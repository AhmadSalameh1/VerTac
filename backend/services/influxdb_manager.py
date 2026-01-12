"""
InfluxDB client and utilities for time-series data
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from pydantic import BaseModel


class SamplePoint(BaseModel):
    """Time-series sample point"""
    timestamp: str
    sensor_id: str
    sensor_name: str
    dataset_id: str
    cycle_id: str
    stream_id: str
    value: float
    quality: float = 1.0
    latency_ms: int = 0


class InfluxDBManager:
    """Manage InfluxDB operations"""
    
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str = "sensor_readings"
    ):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_type=SYNCHRONOUS)
        self.query_api = self.client.query_api()
    
    def write_samples(self, samples: List[SamplePoint]) -> bool:
        """Write samples to InfluxDB"""
        try:
            points = []
            for sample in samples:
                point = {
                    "measurement": "sensor_readings",
                    "tags": {
                        "dataset_id": sample.dataset_id,
                        "cycle_id": sample.cycle_id,
                        "stream_id": sample.stream_id,
                        "sensor_id": sample.sensor_id,
                        "sensor_name": sample.sensor_name,
                    },
                    "fields": {
                        "value": sample.value,
                        "quality": sample.quality,
                        "latency_ms": sample.latency_ms,
                    },
                    "time": sample.timestamp,
                }
                points.append(point)
            
            self.write_api.write(bucket=self.bucket, org=self.org, records=points)
            return True
        except Exception as e:
            print(f"❌ Write error: {e}")
            return False
    
    def query_cycle_samples(
        self,
        cycle_id: str,
        sensor_ids: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Query samples for a cycle"""
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -7d)
                |> filter(fn: (r) => r["_measurement"] == "sensor_readings")
                |> filter(fn: (r) => r["cycle_id"] == "{cycle_id}")
            '''
            
            if sensor_ids:
                sensor_filter = ' or '.join([f'r["sensor_id"] == "{sid}"' for sid in sensor_ids])
                query += f'|> filter(fn: (r) => {sensor_filter})'
            
            query += '|> sort(columns: ["_time"])'
            
            result = self.query_api.query(query=query)
            
            samples_by_sensor = {}
            for table in result:
                for record in table.records:
                    sensor_id = record.tags.get("sensor_id", "unknown")
                    if sensor_id not in samples_by_sensor:
                        samples_by_sensor[sensor_id] = []
                    
                    samples_by_sensor[sensor_id].append({
                        "timestamp": record.get_time().isoformat(),
                        "value": record.get_value(),
                        "quality": record.values.get("quality", 1.0),
                    })
            
            return samples_by_sensor
        except Exception as e:
            print(f"❌ Query error: {e}")
            return {}
    
    def query_cycle_stats(
        self,
        cycle_id: str,
        sensor_id: str
    ) -> Dict[str, float]:
        """Get statistics for a sensor in a cycle"""
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -7d)
                |> filter(fn: (r) => r["_measurement"] == "sensor_readings")
                |> filter(fn: (r) => r["cycle_id"] == "{cycle_id}")
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                
            stats = {
                "mean": mean(column: "_value"),
                "min": min(column: "_value"),
                "max": max(column: "_value"),
                "stddev": stdDev(column: "_value"),
            }
            '''
            
            result = self.query_api.query(query=query)
            
            stats = {}
            if result:
                for table in result:
                    for record in table.records:
                        field_name = record.values.get("result", "")
                        stats[field_name] = record.get_value()
            
            return stats
        except Exception as e:
            print(f"❌ Stats query error: {e}")
            return {}
    
    def close(self):
        """Close connection"""
        self.client.close()


# Example usage
if __name__ == "__main__":
    manager = InfluxDBManager(
        url="http://localhost:8086",
        token="your-token",
        org="vertac",
        bucket="sensor_readings"
    )
    
    # Write sample
    samples = [
        SamplePoint(
            timestamp="2026-01-11T10:30:45.123Z",
            sensor_id="sensor-1",
            sensor_name="motor_speed",
            dataset_id="dataset-1",
            cycle_id="cycle-1",
            stream_id="stream-1",
            value=1500.5,
            quality=0.95,
            latency_ms=50
        )
    ]
    
    manager.write_samples(samples)
    print("✅ Sample written")
    
    manager.close()
