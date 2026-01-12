"""
Edge Connector for VerTac v0.2.0
Lightweight service that reads multi-sensor data and ingests to backend
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import aiohttp
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensorType(str, Enum):
    """Supported sensor types"""
    ANALOG = "analog"
    ACCELEROMETER = "accelerometer"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"


class SensorReading(BaseModel):
    """Single sensor reading"""
    timestamp: str  # ISO8601
    sensor_id: str
    sensor_name: str
    value: float
    unit: str
    quality: float = 1.0  # 0-1, quality score


@dataclass
class SensorConfig:
    """Sensor configuration"""
    sensor_id: str
    name: str
    type: SensorType
    unit: str
    min_value: float = -float('inf')
    max_value: float = float('inf')


class LocalBuffer:
    """SQLite-backed local buffer for offline resilience"""
    
    def __init__(self, db_path: str = "edge_buffer.db", max_samples: int = 10000):
        self.db_path = db_path
        self.max_samples = max_samples
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    sensor_id TEXT,
                    sensor_name TEXT,
                    value REAL,
                    unit TEXT,
                    quality REAL,
                    acked BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_sample(self, reading: SensorReading) -> None:
        """Add sample to buffer"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO samples 
                (timestamp, sensor_id, sensor_name, value, unit, quality)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reading.timestamp,
                reading.sensor_id,
                reading.sensor_name,
                reading.value,
                reading.unit,
                reading.quality
            ))
            conn.commit()
    
    def get_unacked_samples(self, limit: int = 100) -> List[tuple]:
        """Retrieve unacknowledged samples with row IDs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM samples WHERE acked = 0 
                ORDER BY created_at ASC LIMIT ?
            """, (limit,)).fetchall()
            
            return [
                (
                    row['id'],
                    SensorReading(
                        timestamp=row['timestamp'],
                        sensor_id=row['sensor_id'],
                        sensor_name=row['sensor_name'],
                        value=row['value'],
                        unit=row['unit'],
                        quality=row['quality']
                    )
                )
                for row in rows
            ]
    
    def mark_acked(self, sample_ids: List[int]) -> None:
        """Mark samples as acknowledged"""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(sample_ids))
            conn.execute(
                f"UPDATE samples SET acked = 1 WHERE id IN ({placeholders})",
                sample_ids
            )
            conn.commit()
    
    def clear_old_acked(self) -> None:
        """Clean up old acknowledged samples"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM samples 
                WHERE acked = 1 AND created_at < datetime('now', '-7 days')
            """)
            conn.commit()


class SensorSimulator:
    """Simulates sensor readings for testing"""
    
    def __init__(self, sensors: List[SensorConfig], rate_hz: float = 10.0):
        self.sensors = sensors
        self.rate_hz = rate_hz
        self.interval = 1.0 / rate_hz
        self.counter = 0
    
    async def read_sample(self) -> List[SensorReading]:
        """Generate simulated sensor readings"""
        self.counter += 1
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        readings = []
        for sensor in self.sensors:
            if sensor.type == SensorType.ANALOG:
                # Simulate oscillating value
                import math
                value = 50 + 10 * math.sin(self.counter * 0.1)
            elif sensor.type == SensorType.TEMPERATURE:
                # Simulate slowly changing temperature
                import math
                value = 25 + 5 * math.sin(self.counter * 0.01)
            else:
                # Random walk
                import random
                value = 100 + random.gauss(0, 2)
            
            # Clamp to sensor limits
            value = max(sensor.min_value, min(sensor.max_value, value))
            
            readings.append(SensorReading(
                timestamp=timestamp,
                sensor_id=sensor.sensor_id,
                sensor_name=sensor.name,
                value=value,
                unit=sensor.unit,
                quality=0.95 if self.counter % 100 != 0 else 0.7
            ))
        
        return readings


class EdgeConnector:
    """Main edge connector service"""
    
    def __init__(
        self,
        device_name: str,
        sensors: List[SensorConfig],
        backend_url: str = "http://localhost:8000",
        buffer_size: int = 10000,
        batch_size: int = 10,
        flush_interval: float = 1.0,
        retry_max_attempts: int = 5,
        retry_backoff: float = 2.0
    ):
        self.device_name = device_name
        self.sensors = sensors
        self.backend_url = backend_url
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff = retry_backoff
        
        self.buffer = LocalBuffer(max_samples=buffer_size)
        self.simulator = SensorSimulator(sensors)
        
        self.stream_id: Optional[str] = None
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.batch: List[SensorReading] = []
        self.last_flush = datetime.utcnow()
    
    async def register(self) -> bool:
        """Register stream with backend"""
        try:
            async with self.session.post(
                f"{self.backend_url}/api/live/register",
                json={
                    "device_name": self.device_name,
                    "sensor_count": len(self.sensors),
                    "sensors": [
                        {
                            "sensor_id": s.sensor_id,
                            "name": s.name,
                            "type": s.type.value,
                            "unit": s.unit
                        }
                        for s in self.sensors
                    ]
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.stream_id = data.get('stream_id')
                    logger.info(f"✅ Registered stream: {self.stream_id}")
                    return True
                else:
                    logger.error(f"❌ Registration failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return False
    
    async def send_batch(self, readings: List[SensorReading]) -> bool:
        """Send batch of readings to backend"""
        if not self.stream_id:
            return False
        
        retry_count = 0
        backoff = self.retry_backoff
        
        while retry_count < self.retry_max_attempts:
            try:
                async with self.session.post(
                    f"{self.backend_url}/api/live/batch",
                    json={
                        "stream_id": self.stream_id,
                        "samples": [
                            {
                                "timestamp": r.timestamp,
                                "sensor_id": r.sensor_id,
                                "sensor_name": r.sensor_name,
                                "value": r.value,
                                "unit": r.unit,
                                "quality": r.quality
                            }
                            for r in readings
                        ]
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Sent {len(readings)} samples")
                        return True
                    else:
                        logger.warning(f"⚠️  Batch rejected: {resp.status}")
                        return False
            
            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count < self.retry_max_attempts:
                    logger.warning(f"⏳ Timeout, retrying ({retry_count}/{self.retry_max_attempts})")
                    await asyncio.sleep(backoff)
                    backoff *= 2
            except Exception as e:
                retry_count += 1
                if retry_count < self.retry_max_attempts:
                    logger.warning(f"⚠️  Error: {e}, retrying ({retry_count}/{self.retry_max_attempts})")
                    await asyncio.sleep(backoff)
                    backoff *= 2
        
        # If all retries failed, add to buffer
        logger.info(f"📦 Storing {len(readings)} samples in local buffer")
        for reading in readings:
            self.buffer.add_sample(reading)
        
        return False
    
    async def flush_batch(self) -> None:
        """Flush accumulated batch"""
        if self.batch:
            readings_to_send = self.batch.copy()
            self.batch.clear()
            await self.send_batch(readings_to_send)
    
    async def read_loop(self) -> None:
        """Main sensor reading loop"""
        logger.info(f"🚀 Starting sensor read loop...")
        
        while self.running:
            try:
                # Read sensor samples
                readings = await self.simulator.read_sample()
                
                # Add to batch
                self.batch.extend(readings)
                
                # Check if should flush
                now = datetime.utcnow()
                elapsed = (now - self.last_flush).total_seconds()
                
                if len(self.batch) >= self.batch_size or elapsed >= self.flush_interval:
                    await self.flush_batch()
                    self.last_flush = now
                
                # Sleep until next sample
                await asyncio.sleep(self.simulator.interval)
            
            except Exception as e:
                logger.error(f"❌ Read loop error: {e}")
                await asyncio.sleep(1)
    
    async def retry_buffered_samples(self) -> None:
        """Periodically retry buffered samples"""
        while self.running:
            try:
                unacked_with_ids = self.buffer.get_unacked_samples(limit=100)
                if unacked_with_ids:
                    # Extract row IDs and readings
                    row_ids, readings = zip(*unacked_with_ids)
                    logger.info(f"🔄 Retrying {len(readings)} buffered samples...")
                    if await self.send_batch(list(readings)):
                        # Mark as acknowledged using database row IDs
                        self.buffer.mark_acked(list(row_ids))
                
                self.buffer.clear_old_acked()
                await asyncio.sleep(30)  # Retry every 30 seconds
            
            except Exception as e:
                logger.error(f"❌ Retry loop error: {e}")
                await asyncio.sleep(30)
    
    async def start(self) -> None:
        """Start edge connector"""
        self.session = aiohttp.ClientSession()
        self.running = True
        
        # Register with backend
        for attempt in range(3):
            if await self.register():
                break
            logger.warning(f"⏳ Registration attempt {attempt + 1}/3...")
            await asyncio.sleep(5)
        
        # Start read and retry loops
        try:
            await asyncio.gather(
                self.read_loop(),
                self.retry_buffered_samples()
            )
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop edge connector"""
        logger.info("🛑 Stopping edge connector...")
        self.running = False
        
        # Flush remaining batch
        await self.flush_batch()
        
        if self.session:
            await self.session.close()
        
        logger.info("✅ Edge connector stopped")


async def main():
    """Main entry point"""
    # Define sensors
    sensors = [
        SensorConfig(
            sensor_id=str(uuid.uuid4()),
            name="motor_speed",
            type=SensorType.ANALOG,
            unit="RPM",
            min_value=0,
            max_value=3000
        ),
        SensorConfig(
            sensor_id=str(uuid.uuid4()),
            name="vibration",
            type=SensorType.ACCELEROMETER,
            unit="m/s²",
            min_value=0,
            max_value=50
        ),
        SensorConfig(
            sensor_id=str(uuid.uuid4()),
            name="temperature",
            type=SensorType.TEMPERATURE,
            unit="°C",
            min_value=0,
            max_value=100
        ),
    ]
    
    # Create connector
    connector = EdgeConnector(
        device_name="Machine-01",
        sensors=sensors,
        backend_url="http://localhost:8000",
        batch_size=10,
        flush_interval=1.0
    )
    
    # Run
    try:
        await connector.start()
    except KeyboardInterrupt:
        await connector.stop()


if __name__ == "__main__":
    asyncio.run(main())
