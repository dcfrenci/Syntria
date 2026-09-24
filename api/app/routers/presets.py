from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.presets import Preset
from app.schemas.presets import (
    PresetCreate,
    PresetListResponse,
    PresetResponse,
    PresetUpdate,
)

router = APIRouter(prefix="/presets", tags=["Presets"])

@router.post("/", response_model=PresetResponse, status_code=status.HTTP_201_CREATED)
async def create_preset(payload: PresetCreate, db: AsyncSession = Depends(get_db)):
    # If the new preset is set to active, deactivate all existing presets
    if payload.is_active:
        await db.execute(update(Preset).values(is_active=False))
        
    preset = Preset(**payload.model_dump())
    db.add(preset)
    
    await db.flush()
    await db.refresh(preset)
    return preset

@router.get("/", response_model=PresetListResponse, status_code=status.HTTP_200_OK)
async def get_presets(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    query = select(Preset).order_by(Preset.created_at.desc())
    count_query = select(func.count(Preset.id))
    
    total = (await db.execute(count_query)).scalar_one()
    presets = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    
    return {"total": total, "presets": presets}

@router.get("/{preset_id}", response_model=PresetResponse, status_code=status.HTTP_200_OK)
async def get_preset(preset_id: int, db: AsyncSession = Depends(get_db)):
    preset = await db.get(Preset, preset_id)
    if not preset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found.")
    return preset

@router.patch("/{preset_id}", response_model=PresetResponse, status_code=status.HTTP_200_OK)
async def update_preset(preset_id: int, payload: PresetUpdate, db: AsyncSession = Depends(get_db)):
    preset = await db.get(Preset, preset_id)
    if not preset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found.")
        
    update_data = payload.model_dump(exclude_unset=True)
    
    # If updating this preset to active, deactivate all others
    if update_data.get("is_active") is True:
        await db.execute(update(Preset).where(Preset.id != preset_id).values(is_active=False))

    for field, value in update_data.items():
        setattr(preset, field, value)
        
    await db.flush()
    await db.refresh(preset)
    return preset

@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(preset_id: int, db: AsyncSession = Depends(get_db)):
    preset = await db.get(Preset, preset_id)
    if not preset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found.")
        
    await db.delete(preset)
    return None