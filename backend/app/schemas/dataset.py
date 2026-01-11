"""
Dataset schemas for API request/response
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class DatasetCreate(BaseModel):
    """Schema for creating a dataset"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    """Schema for dataset response"""
    id: int
    name: str
    description: Optional[str]
    file_format: str
    file_size: int
    upload_date: datetime
    total_cycles: int
    sensors: Optional[List[str]]
    
    class Config:
        from_attributes = True


class DatasetSummary(BaseModel):
    """Brief dataset information"""
    id: int
    name: str
    total_cycles: int
    upload_date: datetime
    
    class Config:
        from_attributes = True
