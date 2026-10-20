import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.core.database import get_db
from app.models import User
from app.routers.auth import RoleChecker
from app.models.presets import Preset, PresetImage
from app.schemas.presets import (
    PresetCreate,
    PresetListResponse,
    PresetResponse,
    PresetUpdate,
)

router = APIRouter(prefix="/presets", tags=["Presets"])

allow_read_active = RoleChecker(
    ["admin", "manager", "secretary", "doctor", "employee", "client"]
)
allow_read = RoleChecker(["admin", "manager", "secretary", "doctor"])
allow_write = RoleChecker(["admin", "manager", "secretary"])
allow_delete = RoleChecker(["admin", "manager"])


MAX_IMAGE_BYTES = 2 * 1024 * 1024
_IMG_REF = re.compile(r"^image:(\d{1,10})$")


def _sniff(data: bytes) -> str | None:
    """Never trust the client's content-type; SVG is deliberately not accepted."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def check_image_refs(db, elements) -> None:
    ids = set()
    for e in elements or []:
        m = (
            _IMG_REF.match(str(e.get("content") or ""))
            if e.get("type") == "image"
            else None
        )
        if m:
            ids.add(int(m.group(1)))
    if not ids:
        return
    found = set(
        (
            await db.execute(select(PresetImage.id).where(PresetImage.id.in_(ids)))
        ).scalars()
    )
    if ids - found:
        raise HTTPException(
            422, detail="Preset references an image that does not exist."
        )


async def gc_images(db) -> None:
    """Drop images no preset references, once they are older than 24 h (abandoned uploads)."""
    used = set()
    for els in (await db.execute(select(Preset.elements))).scalars():
        for e in els or []:
            m = (
                _IMG_REF.match(str(e.get("content") or ""))
                if e.get("type") == "image"
                else None
            )
            if m:
                used.add(int(m.group(1)))
    stmt = delete(PresetImage).where(
        PresetImage.created_at < datetime.now(timezone.utc) - timedelta(hours=24)
    )
    if used:
        stmt = stmt.where(PresetImage.id.notin_(used))
    await db.execute(stmt)


@router.post("/", response_model=PresetResponse, status_code=status.HTTP_201_CREATED)
async def create_preset(
    payload: PresetCreate,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_write),
):
    # If the new preset is set to active, deactivate all existing presets
    if payload.is_active:
        await db.execute(update(Preset).values(is_active=False))

    data = payload.model_dump()
    await check_image_refs(db, data["elements"])
    preset = Preset(**data)

    db.add(preset)

    await db.flush()
    await db.refresh(preset)
    await gc_images(db)
    return preset


@router.get("/", response_model=PresetListResponse, status_code=status.HTTP_200_OK)
async def get_presets(
    db: AsyncSession = Depends(get_db, scope="function"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(allow_read),
):
    query = (
        select(Preset)
        .options(defer(Preset.elements), defer(Preset.margins))
        .order_by(Preset.created_at.desc())
    )
    count_query = select(func.count(Preset.id))

    total = (await db.execute(count_query)).scalar_one()
    presets = (await db.execute(query.offset(skip).limit(limit))).scalars().all()

    return {"total": total, "presets": presets}


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_write),
):
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, detail="Image too large (max 2 MB).")
    ctype = _sniff(data)
    if ctype is None:
        raise HTTPException(
            415, detail="Only PNG, JPEG, GIF or WebP images are accepted."
        )
    img = PresetImage(content_type=ctype, data=data)
    db.add(img)
    await db.flush()
    return {"id": img.id, "content": f"image:{img.id}"}


@router.get("/images/{image_id}")
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_read_active),
):
    img = await db.get(PresetImage, image_id)
    if not img:
        raise HTTPException(404, detail="Image not found.")
    return Response(
        content=img.data,
        media_type=img.content_type,
        headers={"Cache-Control": "private, max-age=86400"},  # ids are never reused
    )


@router.get("/active", response_model=PresetResponse, status_code=status.HTTP_200_OK)
async def get_active_preset(
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_read_active),
):
    # Assuming your model has an 'is_active' boolean column
    query = select(Preset).where(Preset.is_active == True)

    preset = (await db.execute(query)).scalar_one_or_none()
    

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active preset found."
        )

    return preset


@router.get(
    "/{preset_id}", response_model=PresetResponse, status_code=status.HTTP_200_OK
)
async def get_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_read),
):
    preset = await db.get(Preset, preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found."
        )
    return preset


@router.patch(
    "/{preset_id}", response_model=PresetResponse, status_code=status.HTTP_200_OK
)
async def update_preset(
    preset_id: int,
    payload: PresetUpdate,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_write),
):
    preset = await db.get(Preset, preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found."
        )

    update_data = payload.model_dump(exclude_unset=True)

    client_version = update_data.pop("version", None)
    if client_version is not None and client_version != preset.version:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This preset was modified by someone else. Reload it and reapply your changes.",
        )
    if "elements" in update_data:
        await check_image_refs(db, update_data["elements"])

    # If updating this preset to active, deactivate all others
    if update_data.get("is_active") is True:
        await db.execute(
            update(Preset).where(Preset.id != preset_id).values(is_active=False)
        )

    for field, value in update_data.items():
        setattr(preset, field, value)

    await db.flush()
    await db.refresh(preset)
    await gc_images(db)
    return preset


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_delete),
):
    preset = await db.get(Preset, preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found."
        )

    await db.delete(preset)
    await db.flush()
    await gc_images(db)
    return None
