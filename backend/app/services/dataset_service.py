"""
Dataset service
Handles dataset upload, parsing, and cycle extraction
"""

import os
import pandas as pd
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.models import Dataset, Cycle
from app.core.config import settings


class DatasetService:
    """Service for managing datasets"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("./uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def upload_dataset(
        self,
        file: UploadFile,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dataset:
        """Upload and process a dataset file"""
        
        # Validate file format
        file_ext = Path(file.filename).suffix.lower()
        supported_formats = settings.SUPPORTED_FILE_FORMATS.split(',')
        
        if file_ext.lstrip('.') not in supported_formats:
            raise ValueError(f"Unsupported file format. Supported: {supported_formats}")
        
        # Save file
        file_path = self.upload_dir / file.filename
        content = await file.read()
        file_size = len(content)
        
        # Check size limit
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise ValueError(f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Parse dataset
        df = self._load_dataframe(file_path, file_ext)
        sensors = self._extract_sensors(df)
        cycles = self._extract_cycles(df)
        
        # Create dataset record
        dataset = Dataset(
            name=name or file.filename,
            description=description,
            file_path=str(file_path),
            file_format=file_ext.lstrip('.'),
            file_size=file_size,
            total_cycles=len(cycles),
            sensors=sensors
        )
        
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        
        # Create cycle records
        for cycle_data in cycles:
            cycle = Cycle(
                dataset_id=dataset.id,
                cycle_number=cycle_data['cycle_number'],
                start_time=cycle_data['start_time'],
                end_time=cycle_data['end_time'],
                duration=cycle_data['duration'],
                is_complete=cycle_data.get('is_complete', True),
                metadata=cycle_data.get('metadata', {})
            )
            self.db.add(cycle)
        
        self.db.commit()
        
        return dataset
    
    def _load_dataframe(self, file_path: Path, file_ext: str) -> pd.DataFrame:
        """Load dataset into pandas DataFrame"""
        if file_ext == '.csv':
            return pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif file_ext == '.parquet':
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_ext}")
    
    def _extract_sensors(self, df: pd.DataFrame) -> List[str]:
        """Extract sensor column names from DataFrame"""
        # Assume all numeric columns except 'time', 'timestamp', 'cycle' are sensors
        exclude_cols = ['time', 'timestamp', 'cycle', 'cycle_id', 'cycle_number']
        sensors = [
            col for col in df.columns 
            if col.lower() not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]
        return sensors
    
    def _extract_cycles(self, df: pd.DataFrame) -> List[dict]:
        """Extract individual cycles from DataFrame"""
        cycles = []
        
        # Check if there's a cycle column
        cycle_col = None
        for col in ['cycle', 'cycle_id', 'cycle_number']:
            if col in df.columns:
                cycle_col = col
                break
        
        if cycle_col:
            # Split by cycle column
            for cycle_num in df[cycle_col].unique():
                cycle_df = df[df[cycle_col] == cycle_num]
                cycles.append(self._process_cycle(cycle_df, int(cycle_num)))
        else:
            # Treat entire dataset as one cycle
            cycles.append(self._process_cycle(df, 1))
        
        return cycles
    
    def _process_cycle(self, cycle_df: pd.DataFrame, cycle_number: int) -> dict:
        """Process a single cycle DataFrame"""
        # Get time column
        time_col = None
        for col in ['time', 'timestamp']:
            if col in cycle_df.columns:
                time_col = col
                break
        
        if time_col:
            start_time = float(cycle_df[time_col].min())
            end_time = float(cycle_df[time_col].max())
        else:
            # Use row indices as time if no time column
            start_time = 0.0
            end_time = float(len(cycle_df))
        
        duration = end_time - start_time
        
        return {
            'cycle_number': cycle_number,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'is_complete': True,
            'metadata': {}
        }
    
    def list_datasets(self, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """List all datasets"""
        return self.db.query(Dataset).offset(skip).limit(limit).all()
    
    def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get a specific dataset"""
        return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    def delete_dataset(self, dataset_id: int) -> bool:
        """Delete a dataset and its associated files"""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return False
        
        # Delete file
        if os.path.exists(dataset.file_path):
            os.remove(dataset.file_path)
        
        # Delete database record (cascades to cycles)
        self.db.delete(dataset)
        self.db.commit()
        
        return True
