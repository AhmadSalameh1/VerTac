"""
Database models for datasets and cycles
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Dataset(Base):
    """Dataset model - represents an imported sensor data file"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    file_format = Column(String, nullable=False)  # csv, xlsx, parquet
    file_size = Column(Integer, nullable=False)  # bytes
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    total_cycles = Column(Integer, default=0)
    sensors = Column(JSON, nullable=True)  # List of sensor names
    
    # Relationships
    cycles = relationship("Cycle", back_populates="dataset", cascade="all, delete-orphan")


class Cycle(Base):
    """Cycle model - represents a single operational cycle"""
    __tablename__ = "cycles"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)  # Sequential number within dataset
    
    # Time information
    start_time = Column(Float, nullable=False)  # Timestamp or relative time
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)  # seconds
    
    # Status
    is_complete = Column(Boolean, default=True)
    is_reference = Column(Boolean, default=False)
    is_anomalous = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    
    # Data storage
    data_path = Column(String, nullable=True)  # Path to stored cycle data
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="cycles")
    deviations = relationship("Deviation", back_populates="cycle", cascade="all, delete-orphan")


class Deviation(Base):
    """Deviation model - represents detected deviations in a cycle"""
    __tablename__ = "deviations"
    
    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    
    # Deviation details
    sensor_name = Column(String, nullable=False)
    deviation_type = Column(String, nullable=False)  # shape, timing, amplitude, overall
    severity = Column(Float, nullable=False)  # 0-1 scale
    
    # Comparison info
    compared_to = Column(String, nullable=False)  # reference, previous
    reference_cycle_id = Column(Integer, nullable=True)
    
    # Time and location
    time_start = Column(Float, nullable=True)
    time_end = Column(Float, nullable=True)
    
    # Additional details
    details = Column(JSON, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cycle = relationship("Cycle", back_populates="deviations")
