"""
Cycle service
Handles cycle retrieval and management
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.models import Cycle, Dataset
from app.schemas.cycle import CycleDetailResponse, SensorData


class CycleService:
    """Service for managing cycles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_cycles_by_dataset(
        self,
        dataset_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Cycle]:
        """List all cycles for a dataset"""
        return (
            self.db.query(Cycle)
            .filter(Cycle.dataset_id == dataset_id)
            .order_by(Cycle.cycle_number)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_cycle(self, cycle_id: int) -> Optional[Cycle]:
        """Get a cycle by ID"""
        return self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
    
    def get_cycle_detail(
        self,
        cycle_id: int,
        include_data: bool = True
    ) -> Optional[CycleDetailResponse]:
        """Get cycle with detailed information including sensor data"""
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return None
        
        sensor_data = None
        if include_data:
            sensor_data = self._load_cycle_data(cycle)
        
        return CycleDetailResponse(
            id=cycle.id,
            dataset_id=cycle.dataset_id,
            cycle_number=cycle.cycle_number,
            start_time=cycle.start_time,
            end_time=cycle.end_time,
            duration=cycle.duration,
            is_complete=cycle.is_complete,
            is_reference=cycle.is_reference,
            is_anomalous=cycle.is_anomalous,
            anomaly_score=cycle.anomaly_score,
            cycle_metadata=cycle.cycle_metadata,
            sensor_data=sensor_data
        )
    
    def _load_cycle_data(self, cycle: Cycle) -> List[SensorData]:
        """Load sensor data for a cycle"""
        dataset = cycle.dataset
        
        # Load dataset file
        df = self._load_dataframe(dataset.file_path, dataset.file_format)
        
        # Filter for this cycle
        cycle_df = self._filter_cycle_data(df, cycle.cycle_number)
        
        # Get time column
        time_col = self._find_time_column(cycle_df)
        timestamps = cycle_df[time_col].tolist() if time_col else list(range(len(cycle_df)))
        
        # Extract sensor data
        sensor_data_list = []
        for sensor_name in dataset.sensors:
            if sensor_name in cycle_df.columns:
                sensor_data_list.append(SensorData(
                    sensor_name=sensor_name,
                    timestamps=timestamps,
                    values=cycle_df[sensor_name].tolist(),
                    unit=None  # Could be extracted from metadata
                ))
        
        return sensor_data_list
    
    def _load_dataframe(self, file_path: str, file_format: str) -> pd.DataFrame:
        """Load dataset file"""
        if file_format == 'csv':
            return pd.read_csv(file_path)
        elif file_format in ['xlsx', 'xls']:
            return pd.read_excel(file_path)
        elif file_format == 'parquet':
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    def _filter_cycle_data(self, df: pd.DataFrame, cycle_number: int) -> pd.DataFrame:
        """Filter DataFrame for specific cycle"""
        cycle_col = None
        for col in ['cycle', 'cycle_id', 'cycle_number']:
            if col in df.columns:
                cycle_col = col
                break
        
        if cycle_col:
            return df[df[cycle_col] == cycle_number].copy()
        else:
            # If no cycle column, return entire dataframe (single cycle dataset)
            return df.copy()
    
    def _find_time_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the time column in DataFrame"""
        for col in ['time', 'timestamp']:
            if col in df.columns:
                return col
        return None
    
    def set_reference_cycle(self, cycle_id: int) -> bool:
        """Set a cycle as the reference cycle for its dataset"""
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return False
        
        # Unset any existing reference cycles in this dataset
        self.db.query(Cycle).filter(
            Cycle.dataset_id == cycle.dataset_id,
            Cycle.is_reference == True
        ).update({Cycle.is_reference: False})
        
        # Set this cycle as reference
        cycle.is_reference = True
        self.db.commit()
        
        return True
    
    def get_cycle_sensors(self, cycle_id: int) -> Optional[List[str]]:
        """Get list of sensors for a cycle"""
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return None
        
        return cycle.dataset.sensors
    
    def get_reference_cycle(self, dataset_id: int) -> Optional[Cycle]:
        """Get the reference cycle for a dataset"""
        return (
            self.db.query(Cycle)
            .filter(
                Cycle.dataset_id == dataset_id,
                Cycle.is_reference == True
            )
            .first()
        )
    
    def get_previous_cycle(self, cycle_id: int) -> Optional[Cycle]:
        """Get the cycle immediately preceding the given cycle"""
        cycle = self.get_cycle(cycle_id)
        if not cycle or cycle.cycle_number <= 1:
            return None
        
        return (
            self.db.query(Cycle)
            .filter(
                Cycle.dataset_id == cycle.dataset_id,
                Cycle.cycle_number == cycle.cycle_number - 1
            )
            .first()
        )
