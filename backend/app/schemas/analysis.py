"""
Analysis schemas for comparison and deviation detection
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DeviationType(str, Enum):
    """Types of deviations that can be detected"""
    SHAPE = "shape"
    TIMING = "timing"
    AMPLITUDE = "amplitude"
    OVERALL = "overall"


class ComparisonRequest(BaseModel):
    """Request schema for cycle comparison"""
    cycle_id: int
    reference_cycle_id: int
    sensors: Optional[List[str]] = None  # If None, compare all sensors


class DeviationDetail(BaseModel):
    """Detailed deviation information"""
    sensor_name: str
    deviation_type: DeviationType
    severity: float = Field(..., ge=0, le=1, description="Deviation severity (0-1)")
    compared_to: str  # "reference" or "previous"
    time_start: Optional[float] = None
    time_end: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class ComparisonResponse(BaseModel):
    """Response schema for cycle comparison"""
    cycle_id: int
    reference_cycle_id: int
    similarity_score: float = Field(..., ge=0, le=1)
    deviations: List[DeviationDetail]
    summary: str


class DeviationAnalysisResponse(BaseModel):
    """Response schema for deviation analysis"""
    cycle_id: int
    has_deviations: bool
    deviations_from_reference: List[DeviationDetail]
    deviations_from_previous: List[DeviationDetail]
    overall_health_score: float = Field(..., ge=0, le=1)
    recommendations: List[str]


class AnomalyDetectionResponse(BaseModel):
    """Response schema for anomaly detection"""
    cycle_id: int
    cycle_number: int
    anomaly_score: float = Field(..., ge=0, le=1)
    is_anomalous: bool
    top_contributing_sensors: List[str]
    description: str


class RootCauseContributor(BaseModel):
    """Individual contributor to root cause"""
    sensor_name: str
    contribution_score: float = Field(..., ge=0, le=1)
    deviation_type: DeviationType
    time_of_deviation: float
    description: str


class RootCauseAnalysisResponse(BaseModel):
    """Response schema for root cause analysis"""
    cycle_id: int
    stop_time: float
    analysis_window_start: float
    analysis_window_end: float
    ranked_contributors: List[RootCauseContributor]
    most_likely_cause: str
    confidence: float = Field(..., ge=0, le=1)
