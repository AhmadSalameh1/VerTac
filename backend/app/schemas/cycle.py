"""
Cycle schemas for API request/response
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class CycleResponse(BaseModel):
    """Schema for cycle list response"""
    id: int
    dataset_id: int
    cycle_number: int
    start_time: float
    end_time: float
    duration: float
    is_complete: bool
    is_reference: bool
    is_anomalous: bool
    anomaly_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SensorData(BaseModel):
    """Schema for sensor time-series data"""
    sensor_name: str
    timestamps: List[float]
    values: List[float]
    unit: Optional[str] = None


class CycleDetailResponse(BaseModel):
    """Schema for detailed cycle information with data"""
    id: int
    dataset_id: int
    cycle_number: int
    start_time: float
    end_time: float
    duration: float
    is_complete: bool
    is_reference: bool
    is_anomalous: bool
    anomaly_score: Optional[float]
    metadata: Optional[Dict[str, Any]]
    sensor_data: Optional[List[SensorData]] = None
    
    class Config:
        from_attributes = True


class CycleSetReferenceRequest(BaseModel):
    """Schema for setting reference cycle"""
    cycle_id: int
