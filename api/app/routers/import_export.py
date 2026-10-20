import datetime
import io
import json
import logging
import asyncio
import base64
import csv
from decimal import Decimal, InvalidOperation
from typing import Literal, get_args
from collections import OrderedDict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.scheduling import find_conflict, lock_schedule
from app.core.database import get_db
from app.core.config import settings
from app.models import (
    Item,
    Person,
    Preset,
    Quote,
    QuoteItem,
    Reservation,
    User,
    PresetImage,
)
from app.routers.auth import RoleChecker
from app.routers.presets import check_image_refs
from app.schemas.presets import ComponentSchema, MarginSchema
from app.schemas.quotes import QuoteStatus

router = APIRouter(prefix="/import_export", tags=["Import & Export"])

allow_admin_mgr = RoleChecker(["admin", "manager"])

log = logging.getLogger("syntria.import_export")

Entity = Literal["quotes", "items", "reservations", "presets"]


async def _inline_images(db, elements):
    out = []
    for e in elements or []:
        c = e.get("content") if isinstance(e, dict) else None
        if isinstance(c, str) and c.startswith("image:") and c[6:].isdigit():
            img = await db.get(PresetImage, int(c[6:]))
            e = {
                **e,
                "content": (
                    f"data:{img.content_type};base64,{base64.b64encode(img.data).decode()}"
                    if img
                    else None
                ),
            }
        out.append(e)
    return out


class ExportPayload(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=5000)


class CommitAction(BaseModel):
    selected_action: Literal["keep", "update", "new", "ignore"]
    data: dict = Field(default_factory=dict)


class CommitPayload(BaseModel):
    actions: list[CommitAction] = Field(max_length=5000)
    batch_id: str | None = Field(default=None, min_length=8, max_length=64)


# --- CSV formula injection guard: cells starting with these are executed by Excel/LibreOffice ---
_CSV_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(v):
    return "'" + v if isinstance(v, str) and v.startswith(_CSV_TRIGGERS) else v


def _csv_unsafe(v):  # reverses _csv_safe on import so round-trips are lossless
    if isinstance(v, str) and v.startswith("'") and v[1:].startswith(_CSV_TRIGGERS):
        return v[1:]
    return v


def parse_date(val):
    if not val:
        return None
    if isinstance(val, str):
        return datetime.date.fromisoformat(val.split("T")[0])
    return val


def parse_datetime(val):
    if not val:
        return None
    if isinstance(val, str):
        return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
    return val


def _clean_row(entity: str, data: dict) -> dict:
    """Re-validate untrusted commit data with the same rules as the normal API."""
    try:
        if data.get("id") is not None:
            data["id"] = int(data["id"])
        if entity == "items":
            price = Decimal(str(data.get("price")))
            if price <= 0 or price.as_tuple().exponent < -2:
                raise ValueError("price")
            name = str(data.get("name") or "")
            if not 2 <= len(name) <= 100:
                raise ValueError("name")
            if (
                data.get("description") is not None
                and len(str(data["description"])) > 500
            ):
                raise ValueError("description")
            data["price"] = price
            data["is_active"] = _as_bool(data.get("is_active"), True)
            data["is_specific"] = _as_bool(data.get("is_specific"), False)

        elif entity == "quotes":
            if data.get("status", "Draft") not in get_args(QuoteStatus):
                raise ValueError("status")
            items, total = [], Decimal("0.00")
            for itm in data.get("items") or []:
                qty = int(itm.get("quantity", 1))
                unit = Decimal(str(itm.get("unit_price", 0)))
                disc = Decimal(str(itm.get("discount", 0)))
                if qty <= 0 or unit < 0 or disc < 0:
                    raise ValueError("item")
                teeth = itm.get("teeth")
                if qty > 999 or (
                    teeth is not None
                    and (
                        not isinstance(teeth, list)
                        or len(teeth) > 52
                        or any(
                            not isinstance(t, int) or not 11 <= t <= 85 for t in teeth
                        )
                    )
                ):
                    raise ValueError("item")
                total += max(unit * qty - disc, Decimal("0.00"))
                items.append(
                    {**itm, "quantity": qty, "unit_price": unit, "discount": disc}
                )
            data["items"] = items
            data["total_amount"] = total
            data["valid_until"] = parse_date(data.get("valid_until"))

        elif entity == "reservations":
            start = parse_datetime(data.get("reservation_date"))
            if not isinstance(start, datetime.datetime) or start.tzinfo is None:
                raise ValueError("date")
            data["duration_minutes"] = int(data.get("duration_minutes") or 30)
            if not 0 < data["duration_minutes"] <= 1440:
                raise ValueError("duration")
            if (
                data.get("description") is not None
                and len(str(data["description"])) > 500
            ):
                raise ValueError("description")
            staff = data.get("staff")
            if not isinstance(staff, list) or not any(
                isinstance(s, dict) and s.get("id") for s in staff
            ):
                raise ValueError("staff")

        elif entity == "presets":
            data["is_active"] = _as_bool(data.get("is_active"), False)
            if not 1 <= len(str(data.get("name") or "")) <= 100:
                raise ValueError("name")
            elements = data.get("elements") or []
            if len(elements) > 100:
                raise ValueError("elements")
            data["elements"] = [
                ComponentSchema.model_validate(e).model_dump(mode="json")
                for e in elements
            ]
            data["margins"] = MarginSchema.model_validate(
                data.get("margins") or {}
            ).model_dump()
    except (ValueError, TypeError, ArithmeticError, AttributeError):
        raise HTTPException(
            422, f"Invalid {entity} data in import file. Nothing was saved."
        )
    return data


_JSON_COLS = {
    "quotes": ("items", "patient", "staff"),
    "items": ("category",),
    "reservations": ("patient", "staff"),
    "presets": ("elements", "margins"),
}
_MODELS = {
    "quotes": Quote,
    "items": Item,
    "reservations": Reservation,
    "presets": Preset,
}


def _parse_csv(contents: bytes) -> list[dict]:
    csv.field_size_limit(
        8_000_000
    )  # default 128 KB would reject presets with embedded images
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
    rows: list[dict] = []
    for raw in reader:
        if len(rows) >= 5000:
            raise ValueError("too many rows")
        raw.pop(None, None)  # extra cells beyond the header
        rows.append({k: _csv_unsafe(v if v != "" else None) for k, v in raw.items()})
    return rows


def _as_bool(v, default: bool) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("true", "1"):
        return True
    if s in ("false", "0"):
        return False
    raise ValueError("bool")


def _to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: _csv_safe(v) for k, v in r.items()})
    return buf.getvalue()


def _as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


async def _existing(db, model, ids) -> set[int]:
    ids = {i for i in map(_as_int, ids) if i is not None}
    if not ids:
        return set()
    return set((await db.execute(select(model.id).where(model.id.in_(ids)))).scalars())


async def _visible_persons(db, ids, actor) -> set[int]:
    found = await _existing(db, Person, ids)
    if actor.role.name.lower() != "admin":
        admin_id = (
            await db.execute(
                select(Person.id).where(Person.email == settings.ADMIN_EMAIL)
            )
        ).scalar_one_or_none()
        found.discard(admin_id)
    return found


def _collect_refs(row: dict, person_ids: set, item_ids: set) -> None:
    p, s = row.get("patient"), row.get("staff")
    if isinstance(p, dict):
        person_ids.add(p.get("id"))
    if isinstance(s, dict):
        person_ids.add(s.get("id"))
    elif isinstance(s, list):
        person_ids.update(x.get("id") for x in s if isinstance(x, dict))
    if isinstance(row.get("items"), list):
        item_ids.update(i.get("item_id") for i in row["items"] if isinstance(i, dict))


@router.post("/export/{entity}")
async def export_data(
    entity: Entity,
    payload: ExportPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin_mgr),
):
    """Exports structured relationships to a flat CSV by serializing entire nested objects as JSON."""
    ids = payload.ids

    log.info("export entity=%s count=%d user=%s", entity, len(ids), current_user.id)

    if not ids:
        raise HTTPException(400, "No IDs provided for export")

    data = []
    is_admin = current_user.role.name.lower() == "admin"
    admin_p = Person.email == settings.ADMIN_EMAIL
    if entity == "quotes":
        # Deep load all nested models for full serialization
        stmt = (
            select(Quote)
            .where(Quote.id.in_(ids))
            .options(
                selectinload(Quote.patient),
                selectinload(Quote.staff),
                selectinload(Quote.quote_items).selectinload(QuoteItem.item),
            )
        )
        if not is_admin:
            stmt = stmt.where(~Quote.patient.has(admin_p))
        for r in (await db.execute(stmt)).scalars().all():
            patient_data = (
                {
                    "id": r.patient.id,
                    "first_name": r.patient.first_name,
                    "last_name": r.patient.last_name,
                    "email": r.patient.email,
                    "phone_number": r.patient.phone_number,
                }
                if r.patient
                else None
            )

            staff_data = (
                {
                    "id": r.staff.id,
                    "first_name": r.staff.first_name,
                    "last_name": r.staff.last_name,
                    "email": r.staff.email,
                }
                if r.staff
                else None
            )

            items_data = [
                {
                    "item_id": qi.item_id,
                    "item_name": qi.item.name if qi.item else None,
                    "unit_price": float(qi.unit_price),
                    "quantity": qi.quantity,
                    "discount": float(qi.discount),
                    "teeth": qi.teeth,
                }
                for qi in r.quote_items
            ]

            data.append(
                {
                    "id": r.id,
                    "status": r.status,
                    "total_amount": float(r.total_amount),
                    "valid_until": r.valid_until.isoformat() if r.valid_until else None,
                    "patient": json.dumps(patient_data) if patient_data else None,
                    "staff": json.dumps(staff_data) if staff_data else None,
                    "items": json.dumps(items_data),
                }
            )

    elif entity == "items":
        stmt = select(Item).where(Item.id.in_(ids)).options(selectinload(Item.category))
        for r in (await db.execute(stmt)).scalars().all():
            cat_data = (
                {"id": r.category.id, "name": r.category.name} if r.category else None
            )
            data.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "price": float(r.price),
                    "category": json.dumps(cat_data) if cat_data else None,
                    "is_active": r.is_active,
                    "is_specific": r.is_specific,
                }
            )

    elif entity == "reservations":
        stmt = (
            select(Reservation)
            .where(Reservation.id.in_(ids))
            .options(selectinload(Reservation.patient), selectinload(Reservation.staff))
        )
        if not is_admin:
            stmt = stmt.where(
                ~Reservation.patient.has(admin_p), ~Reservation.staff.any(admin_p)
            )
        for r in (await db.execute(stmt)).scalars().all():
            patient_data = (
                {
                    "id": r.patient.id,
                    "first_name": r.patient.first_name,
                    "last_name": r.patient.last_name,
                }
                if r.patient
                else None
            )

            staff_data = [
                {"id": s.id, "first_name": s.first_name, "last_name": s.last_name}
                for s in r.staff
            ]

            data.append(
                {
                    "id": r.id,
                    "reservation_date": r.reservation_date.isoformat(),
                    "duration_minutes": r.duration_minutes,
                    "description": r.description,
                    "patient": json.dumps(patient_data) if patient_data else None,
                    "staff": json.dumps(staff_data),
                }
            )

    elif entity == "presets":
        stmt = select(Preset).where(Preset.id.in_(ids))
        for r in (await db.execute(stmt)).scalars().all():
            data.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "is_active": r.is_active,
                    "elements": json.dumps(await _inline_images(db, r.elements)),
                    "margins": json.dumps(r.margins),
                }
            )

    else:
        raise HTTPException(400, f"Unsupported export entity: {entity}")

    return Response(
        content=_to_csv(data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}_export.csv"},
    )


@router.post("/validate/{entity}")
async def validate_import(
    entity: Entity,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_admin_mgr),
):
    contents = await file.read(5_000_001)
    if len(contents) > 5_000_000:
        raise HTTPException(413, "CSV too large (max 5 MB)")
    try:
        rows = await asyncio.to_thread(_parse_csv, contents)
    except Exception:
        raise HTTPException(400, "Failed to parse CSV (max 5000 rows).")

    # pass 1: decode nested JSON columns
    row_errors: list[list[str]] = []
    for row in rows:
        errs = []
        for col in _JSON_COLS[entity]:
            if isinstance(row.get(col), str):
                try:
                    row[col] = json.loads(row[col])
                except ValueError:
                    errs.append(f"Invalid JSON format in '{col}' column.")
        row_errors.append(errs)

    # pass 2: one query per table instead of one per row
    person_ids, item_ids = set(), set()
    for row in rows:
        _collect_refs(row, person_ids, item_ids)
    found = await _existing(db, _MODELS[entity], (r.get("id") for r in rows))
    ok_persons = await _visible_persons(db, person_ids, current_user)
    ok_items = await _existing(db, Item, item_ids)

    results = []
    for row, errors in zip(rows, row_errors):
        row_id, status = row.get("id"), "ok"
        if row_id is None:
            errors.append("Missing primary 'id'.")
            status = "error"
        elif _as_int(row_id) in found:
            status = "conflict"

        if entity in ("quotes", "reservations"):
            p = row.get("patient")
            pid = p.get("id") if isinstance(p, dict) else None
            if _as_int(pid) not in ok_persons:
                errors.append(f"Patient ID {pid} does not exist.")
        if entity == "quotes":
            s = row.get("staff")
            sid = s.get("id") if isinstance(s, dict) else None
            if sid and _as_int(sid) not in ok_persons:
                errors.append(f"Staff ID {sid} does not exist.")
            for it in row.get("items") or []:
                iid = it.get("item_id") if isinstance(it, dict) else None
                if _as_int(iid) not in ok_items:
                    errors.append(f"Item ID {iid} does not exist.")
        elif entity == "reservations":
            for s in row.get("staff") or []:
                sid = s.get("id") if isinstance(s, dict) else None
                if _as_int(sid) not in ok_persons:
                    errors.append(f"Staff ID {sid} does not exist.")

        results.append(
            {
                "row_id": row_id,
                "status": "error" if errors else status,
                "errors": errors,
                "data": row,
            }
        )
    return results


async def _do_commit(
    entity: Entity,
    payload: CommitPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin_mgr),
):
    """Executes bulk inserts and updates within a single transaction from serialized nested objects."""
    actions = payload.actions

    person_ids, item_ids = set(), set()
    for act in actions:
        if act.selected_action in ("new", "update"):
            _collect_refs(act.data, person_ids, item_ids)
    ok_persons = await _visible_persons(db, person_ids, current_user)
    ok_items = await _existing(db, Item, item_ids)

    if entity == "reservations":
        await lock_schedule(db)

    for act in actions:
        action = act.selected_action
        data = act.data

        if action == "keep" or action == "ignore":
            continue

        if action == "new":
            data.pop("id", None)  # Let the DB assign a fresh ID

        data = _clean_row(entity, data)

        if action == "update":
            target_id = _as_int(data.get("id"))
            if target_id is None or await db.get(_MODELS[entity], target_id) is None:
                raise HTTPException(
                    422, f"{entity} id {data.get('id')} not found. Nothing was saved."
                )
            if entity == "quotes" and current_user.role.name.lower() != "admin":
                q = await db.get(Quote, target_id)
                if q.patient and q.patient.email == settings.ADMIN_EMAIL:
                    raise HTTPException(404, "Quote not found. Nothing was saved.")

        refs_p, refs_i = set(), set()
        _collect_refs(data, refs_p, refs_i)
        refs_p.discard(None)
        refs_i.discard(None)
        if {_as_int(i) for i in refs_p} - ok_persons or {
            _as_int(i) for i in refs_i
        } - ok_items:
            raise HTTPException(
                422, "Import references records that do not exist. Nothing was saved."
            )

        if entity == "reservations":
            p = data.get("patient")
            staff_ids = [
                s["id"]
                for s in data.get("staff") or []
                if isinstance(s, dict) and s.get("id")
            ]
            msg = await find_conflict(
                db,
                parse_datetime(data["reservation_date"]),
                int(data.get("duration_minutes", 30)),
                p.get("id") if isinstance(p, dict) else None,
                staff_ids,
                exclude_id=data.get("id") if action == "update" else None,
            )
            if msg:
                raise HTTPException(
                    409, f"Reservation conflict: {msg} Nothing was saved."
                )

        try:
            if entity == "quotes":
                db_obj = (
                    await db.get(Quote, data.get("id"))
                    if action == "update"
                    else Quote()
                )

                db_obj.patient_id = (
                    data.get("patient", {}).get("id")
                    if isinstance(data.get("patient"), dict)
                    else None
                )
                db_obj.staff_id = (
                    data.get("staff", {}).get("id")
                    if isinstance(data.get("staff"), dict)
                    else None
                )

                db_obj.status = data.get("status", "Draft")
                db_obj.total_amount = data.get("total_amount", 0)
                db_obj.valid_until = parse_date(data.get("valid_until"))

                if action == "new":
                    db.add(db_obj)
                await db.flush()

                if "items" in data and isinstance(data["items"], list):
                    if action == "update":
                        await db.execute(
                            delete(QuoteItem).where(QuoteItem.quote_id == db_obj.id)
                        )
                    for itm in data["items"]:
                        db.add(
                            QuoteItem(
                                quote_id=db_obj.id,
                                item_id=itm.get("item_id"),
                                quantity=itm.get("quantity", 1),
                                unit_price=itm.get("unit_price", 0),
                                discount=itm.get("discount", 0),
                                teeth=itm.get("teeth"),
                            )
                        )

            elif entity == "items":
                db_obj = (
                    await db.get(Item, data.get("id")) if action == "update" else Item()
                )
                db_obj.name = data.get("name")
                db_obj.description = data.get("description")
                db_obj.price = data.get("price")
                db_obj.category_id = (
                    data.get("category", {}).get("id")
                    if isinstance(data.get("category"), dict)
                    else None
                )
                db_obj.is_active = data.get("is_active", True)
                db_obj.is_specific = data.get("is_specific", False)
                if action == "new":
                    db.add(db_obj)

            elif entity == "reservations":
                db_obj = (
                    await db.get(Reservation, data.get("id"))
                    if action == "update"
                    else Reservation()
                )

                db_obj.patient_id = (
                    data.get("patient", {}).get("id")
                    if isinstance(data.get("patient"), dict)
                    else None
                )
                db_obj.reservation_date = parse_datetime(data.get("reservation_date"))
                db_obj.duration_minutes = data.get("duration_minutes", 30)
                db_obj.description = data.get("description")

                if action == "new":
                    db.add(db_obj)
                await db.flush()

                if "staff" in data and isinstance(data["staff"], list):
                    staff_ids = [s.get("id") for s in data["staff"] if s.get("id")]
                    staff_members = (
                        (
                            await db.execute(
                                select(Person).where(Person.id.in_(staff_ids))
                            )
                        )
                        .scalars()
                        .all()
                    )
                    db_obj.staff.clear()
                    db_obj.staff.extend(staff_members)

            elif entity == "presets":
                await check_image_refs(db, data.get("elements"))
                if data.get("is_active", False):
                    q = update(Preset).values(is_active=False)
                    if action == "update":
                        q = q.where(Preset.id != data.get("id"))
                    await db.execute(q)
                db_obj = (
                    await db.get(Preset, data.get("id"))
                    if action == "update"
                    else Preset()
                )
                db_obj.name = data.get("name")
                db_obj.is_active = data.get("is_active", False)
                db_obj.elements = data.get("elements")
                db_obj.margins = data.get("margins")
                if action == "new":
                    db.add(db_obj)
                await db.flush()

        except Exception:
            await db.rollback()
            log.exception("import commit failed for %s", entity)
            raise HTTPException(
                500, f"Import aborted on a {entity} record. Nothing was saved."
            )

    await db.commit()
    return {"message": f"Successfully processed {len(actions)} records."}


# In-memory, like the login throttle: valid because the API runs a single worker.
_batches: "OrderedDict[str, None]" = OrderedDict()


@router.post("/commit/{entity}")
async def commit_import(
    entity: Entity,
    payload: CommitPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin_mgr),
):
    key = f"{current_user.id}:{payload.batch_id}" if payload.batch_id else None
    if key:
        if key in _batches:
            raise HTTPException(409, "This import batch was already submitted.")
        _batches[key] = None
        while len(_batches) > 200:
            _batches.popitem(last=False)
    try:
        return await _do_commit(entity, payload, db, current_user)
    except BaseException:
        if key:
            _batches.pop(key, None)  # failed and rolled back: allow a retry
        raise