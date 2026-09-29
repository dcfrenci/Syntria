import io
import json
import datetime
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Quote, Item, Reservation, Preset, QuoteItem, Person

router = APIRouter(prefix="/import_export", tags=["Import & Export"])

def parse_date(val):
    if not val or pd.isna(val): return None
    if isinstance(val, str):
        try: return datetime.date.fromisoformat(val.split("T")[0])
        except Exception: pass
    return val

def parse_datetime(val):
    if not val or pd.isna(val): return None
    if isinstance(val, str):
        try: return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception: pass
    return val

@router.post("/export/{entity}")
async def export_data(entity: str, payload: dict, db: AsyncSession = Depends(get_db)):
    """Exports structured relationships to a flat CSV by serializing entire nested objects as JSON."""
    ids = payload.get("ids", [])
    if not ids:
        raise HTTPException(400, "No IDs provided for export")

    data = []
    if entity == "quotes":
        # Deep load all nested models for full serialization
        stmt = (
            select(Quote)
            .where(Quote.id.in_(ids))
            .options(
                selectinload(Quote.patient),
                selectinload(Quote.staff),
                selectinload(Quote.quote_items).selectinload(QuoteItem.item)
            )
        )
        for r in (await db.execute(stmt)).scalars().all():
            patient_data = {
                "id": r.patient.id, "first_name": r.patient.first_name, 
                "last_name": r.patient.last_name, "email": r.patient.email, 
                "phone_number": r.patient.phone_number
            } if r.patient else None
            
            staff_data = {
                "id": r.staff.id, "first_name": r.staff.first_name, 
                "last_name": r.staff.last_name, "email": r.staff.email
            } if r.staff else None
            
            items_data = [
                {
                    "item_id": qi.item_id, 
                    "item_name": qi.item.name if qi.item else None,
                    "unit_price": float(qi.unit_price),
                    "quantity": qi.quantity, 
                    "discount": float(qi.discount), 
                    "teeth": qi.teeth
                } for qi in r.quote_items
            ]
            
            data.append({
                "id": r.id, 
                "status": r.status, 
                "total_amount": float(r.total_amount),
                "valid_until": r.valid_until.isoformat() if r.valid_until else None,
                "patient": json.dumps(patient_data) if patient_data else None,
                "staff": json.dumps(staff_data) if staff_data else None,
                "items": json.dumps(items_data)
            })

    elif entity == "items":
        stmt = select(Item).where(Item.id.in_(ids)).options(selectinload(Item.category))
        for r in (await db.execute(stmt)).scalars().all():
            cat_data = {"id": r.category.id, "name": r.category.name} if r.category else None
            data.append({
                "id": r.id, "name": r.name, "description": r.description, 
                "price": float(r.price), "category": json.dumps(cat_data) if cat_data else None, 
                "is_active": r.is_active, "is_specific": r.is_specific
            })

    elif entity == "reservations":
        stmt = (
            select(Reservation)
            .where(Reservation.id.in_(ids))
            .options(selectinload(Reservation.patient), selectinload(Reservation.staff))
        )
        for r in (await db.execute(stmt)).scalars().all():
            patient_data = {
                "id": r.patient.id, "first_name": r.patient.first_name, "last_name": r.patient.last_name
            } if r.patient else None
            
            staff_data = [
                {"id": s.id, "first_name": s.first_name, "last_name": s.last_name} 
                for s in r.staff
            ]

            data.append({
                "id": r.id, 
                "reservation_date": r.reservation_date.isoformat(), 
                "duration_minutes": r.duration_minutes, 
                "description": r.description, 
                "patient": json.dumps(patient_data) if patient_data else None,
                "staff": json.dumps(staff_data)
            })

    elif entity == "presets":
        stmt = select(Preset).where(Preset.id.in_(ids))
        for r in (await db.execute(stmt)).scalars().all():
            data.append({
                "id": r.id, "name": r.name, "is_active": r.is_active, 
                "elements": json.dumps(r.elements), "margins": json.dumps(r.margins)
            })
            
    else:
        raise HTTPException(400, f"Unsupported export entity: {entity}")

    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return Response(content=csv_buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={entity}_export.csv"})


@router.post("/validate/{entity}")
async def validate_import(entity: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Parses a CSV upload and checks the database for conflicts and missing relations from nested objects."""
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
        df = df.where(pd.notnull(df), None) # Convert Pandas NaN to standard Python None
    except Exception as e:
        raise HTTPException(400, f"Failed to parse CSV: {str(e)}")

    rows = df.to_dict(orient="records")
    results = []

    for row in rows:
        row_id = row.get("id")
        status = "ok"
        errors = []

        # Decode full JSON relationships
        if entity == "quotes":
            for col in ["items", "patient", "staff"]:
                if col in row and isinstance(row[col], str):
                    try: row[col] = json.loads(row[col])
                    except: errors.append(f"Invalid JSON format in '{col}' column.")
        elif entity == "items":
            if "category" in row and isinstance(row["category"], str):
                try: row["category"] = json.loads(row["category"])
                except: errors.append("Invalid JSON format in 'category' column.")
        elif entity == "reservations":
            for col in ["patient", "staff"]:
                if col in row and isinstance(row[col], str):
                    try: row[col] = json.loads(row[col])
                    except: errors.append(f"Invalid JSON format in '{col}' column.")
        elif entity == "presets":
            for col in ["elements", "margins"]:
                if col in row and isinstance(row[col], str):
                    try: row[col] = json.loads(row[col])
                    except: errors.append(f"Invalid JSON format in '{col}' column.")

        # Existence validation
        if row_id:
            exists = False
            if entity == "quotes": exists = await db.get(Quote, row_id)
            elif entity == "items": exists = await db.get(Item, row_id)
            elif entity == "reservations": exists = await db.get(Reservation, row_id)
            elif entity == "presets": exists = await db.get(Preset, row_id)
            
            if exists: status = "conflict"
        else:
            errors.append("Missing primary 'id'.")
            status = "error"

        # Relational validation using extracted nested IDs
        if entity == "quotes":
            patient_id = row.get("patient", {}).get("id") if isinstance(row.get("patient"), dict) else None
            staff_id = row.get("staff", {}).get("id") if isinstance(row.get("staff"), dict) else None
            
            if not patient_id or not await db.get(Person, patient_id):
                errors.append(f"Patient ID {patient_id} does not exist.")
            if staff_id and not await db.get(Person, staff_id):
                errors.append(f"Staff ID {staff_id} does not exist.")
                
            items = row.get("items", [])
            if isinstance(items, list):
                for item in items:
                    item_id = item.get("item_id")
                    if not item_id or not await db.get(Item, item_id):
                        errors.append(f"Item ID {item_id} does not exist.")

        elif entity == "reservations":
            patient_id = row.get("patient", {}).get("id") if isinstance(row.get("patient"), dict) else None
            if not patient_id or not await db.get(Person, patient_id):
                errors.append(f"Patient ID {patient_id} does not exist.")
                
            staff_list = row.get("staff", [])
            if isinstance(staff_list, list):
                for s in staff_list:
                    s_id = s.get("id")
                    if not s_id or not await db.get(Person, s_id):
                        errors.append(f"Staff ID {s_id} does not exist.")

        results.append({
            "row_id": row_id,
            "status": "error" if errors else status,
            "errors": errors,
            "data": row
        })

    return results


@router.post("/commit/{entity}")
async def commit_import(entity: str, payload: dict, db: AsyncSession = Depends(get_db)):
    """Executes bulk inserts and updates within a single transaction from serialized nested objects."""
    actions = payload.get("actions", [])
    
    for act in actions:
        action = act.get("selected_action")
        data = act.get("data", {})
        
        if action == "keep" or action == "ignore":
            continue
            
        if action == "new":
            data.pop("id", None) # Let the DB assign a fresh ID

        try:
            if entity == "quotes":
                db_obj = await db.get(Quote, data.get("id")) if action == "update" else Quote()
                
                db_obj.patient_id = data.get("patient", {}).get("id") if isinstance(data.get("patient"), dict) else None
                db_obj.staff_id = data.get("staff", {}).get("id") if isinstance(data.get("staff"), dict) else None
                
                db_obj.status = data.get("status", "Draft")
                db_obj.total_amount = data.get("total_amount", 0)
                db_obj.valid_until = parse_date(data.get("valid_until"))
                
                if action == "new": db.add(db_obj)
                await db.flush()
                
                if "items" in data and isinstance(data["items"], list):
                    if action == "update":
                        await db.execute(delete(QuoteItem).where(QuoteItem.quote_id == db_obj.id))
                    for itm in data["items"]:
                        db.add(QuoteItem(
                            quote_id=db_obj.id, 
                            item_id=itm.get("item_id"), 
                            quantity=itm.get("quantity", 1), 
                            unit_price=itm.get("unit_price", 0),
                            discount=itm.get("discount", 0), 
                            teeth=itm.get("teeth")
                        ))

            elif entity == "items":
                db_obj = await db.get(Item, data.get("id")) if action == "update" else Item()
                db_obj.name = data.get("name")
                db_obj.description = data.get("description")
                db_obj.price = data.get("price")
                db_obj.category_id = data.get("category", {}).get("id") if isinstance(data.get("category"), dict) else None
                db_obj.is_active = data.get("is_active", True)
                db_obj.is_specific = data.get("is_specific", False)
                if action == "new": db.add(db_obj)

            elif entity == "reservations":
                db_obj = await db.get(Reservation, data.get("id")) if action == "update" else Reservation()
                
                db_obj.patient_id = data.get("patient", {}).get("id") if isinstance(data.get("patient"), dict) else None
                db_obj.reservation_date = parse_datetime(data.get("reservation_date"))
                db_obj.duration_minutes = data.get("duration_minutes", 30)
                db_obj.description = data.get("description")
                
                if action == "new": db.add(db_obj)
                await db.flush()
                
                if "staff" in data and isinstance(data["staff"], list):
                    staff_ids = [s.get("id") for s in data["staff"] if s.get("id")]
                    staff_members = (await db.execute(select(Person).where(Person.id.in_(staff_ids)))).scalars().all()
                    db_obj.staff.clear()
                    db_obj.staff.extend(staff_members)

            elif entity == "presets":
                db_obj = await db.get(Preset, data.get("id")) if action == "update" else Preset()
                db_obj.name = data.get("name")
                db_obj.is_active = data.get("is_active", False)
                db_obj.elements = data.get("elements")
                db_obj.margins = data.get("margins")
                if action == "new": db.add(db_obj)

        except Exception as e:
            await db.rollback()
            raise HTTPException(500, f"Transaction aborted due to error on {entity} ID {data.get('id', 'New')}: {str(e)}")

    await db.commit()
    return {"message": f"Successfully processed {len(actions)} records."}