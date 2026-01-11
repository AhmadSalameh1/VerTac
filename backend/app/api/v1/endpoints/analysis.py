"""
Analysis endpoints
Handles cycle comparison and deviation analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.analysis import (
    ComparisonRequest,
    ComparisonResponse,
    DeviationAnalysisResponse,
    AnomalyDetectionResponse
)
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/compare", response_model=ComparisonResponse)
async def compare_cycles(
    request: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare two cycles and identify deviations
    """
    service = AnalysisService(db)
    try:
        result = service.compare_cycles(
            request.cycle_id,
            request.reference_cycle_id,
            request.sensors
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cycle/{cycle_id}/deviations", response_model=DeviationAnalysisResponse)
async def analyze_cycle_deviations(
    cycle_id: int,
    compare_to_reference: bool = Query(True, description="Compare to reference cycle"),
    compare_to_previous: bool = Query(True, description="Compare to previous cycle"),
    db: Session = Depends(get_db)
):
    """
    Analyze deviations for a specific cycle
    """
    service = AnalysisService(db)
    try:
        result = service.analyze_deviations(
            cycle_id,
            compare_to_reference,
            compare_to_previous
        )
        if not result:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dataset/{dataset_id}/anomalies", response_model=List[AnomalyDetectionResponse])
async def detect_dataset_anomalies(
    dataset_id: int,
    threshold: float = Query(0.8, description="Anomaly detection threshold (0-1)"),
    db: Session = Depends(get_db)
):
    """
    Detect anomalous cycles in a dataset
    """
    service = AnalysisService(db)
    try:
        result = service.detect_anomalies(dataset_id, threshold)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cycle/{cycle_id}/root-cause")
async def analyze_root_cause(
    cycle_id: int,
    time_window_seconds: Optional[float] = Query(
        None, 
        description="Time window before stop to analyze (seconds)"
    ),
    db: Session = Depends(get_db)
):
    """
    Analyze root cause for abnormal cycle termination
    Traces and ranks sensor deviations leading up to the stop
    """
    service = AnalysisService(db)
    try:
        result = service.analyze_root_cause(cycle_id, time_window_seconds)
        if not result:
            raise HTTPException(status_code=404, detail="Cycle not found or not abnormal")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
