"""
Cycle endpoints
Handles cycle management and visualization
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.cycle import CycleResponse, CycleDetailResponse, CycleSetReferenceRequest
from app.services.cycle_service import CycleService

router = APIRouter()


@router.get("/dataset/{dataset_id}", response_model=List[CycleResponse])
async def list_cycles_for_dataset(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all cycles for a specific dataset
    """
    service = CycleService(db)
    return service.list_cycles_by_dataset(dataset_id, skip, limit)


@router.get("/{cycle_id}", response_model=CycleDetailResponse)
async def get_cycle(
    cycle_id: int,
    include_data: bool = Query(True, description="Include sensor data"),
    db: Session = Depends(get_db)
):
    """
    Get a specific cycle with optional sensor data
    """
    service = CycleService(db)
    cycle = service.get_cycle_detail(cycle_id, include_data)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return cycle


@router.post("/{cycle_id}/set-reference")
async def set_reference_cycle(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Set a cycle as the reference cycle for its dataset
    """
    service = CycleService(db)
    success = service.set_reference_cycle(cycle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return {"message": "Reference cycle set successfully"}


@router.get("/{cycle_id}/sensors")
async def get_cycle_sensors(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Get list of sensors available in a cycle
    """
    service = CycleService(db)
    sensors = service.get_cycle_sensors(cycle_id)
    if sensors is None:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return {"sensors": sensors}
