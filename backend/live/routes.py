"""
Live ingestion API routes for v0.2.0
Add these routes to main FastAPI app
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
import uuid
import os

from services.cycle_state_machine import CycleStateMachine, CycleEvent, CycleMetadata
from services.influxdb_manager import InfluxDBManager, SamplePoint
from services.deviation_analyzer import DeviationAnalyzer


# Models
class SensorConfig(BaseModel):
    sensor_id: str
    name: str
    type: str
    unit: str


class RegisterStreamRequest(BaseModel):
    device_name: str
    sensor_count: int
    sensors: List[SensorConfig]


class RegisterStreamResponse(BaseModel):
    stream_id: str
    dataset_id: str
    status: str


class SampleData(BaseModel):
    timestamp: str
    sensor_id: str
    sensor_name: str
    value: float
    unit: str
    quality: float = 1.0


class BatchSamplesRequest(BaseModel):
    stream_id: str
    samples: List[SampleData]


class BatchSamplesResponse(BaseModel):
    ack_id: str
    buffer_status: str
    samples_received: int


# Router
router = APIRouter(tags=["live"])


# In-memory store (replace with database in production)
streams: Dict[str, Dict[str, Any]] = {}
state_machines: Dict[str, CycleStateMachine] = {}
websocket_clients: Dict[str, List[WebSocket]] = {}  # stream_id -> [websockets]


# Initialize services
influxdb_manager = InfluxDBManager(
    url=os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
    token=os.getenv("INFLUXDB_TOKEN", "default-token"),
    org=os.getenv("INFLUXDB_ORG", "vertac"),
    bucket=os.getenv("INFLUXDB_BUCKET", "sensor_readings")
)
deviation_analyzer = DeviationAnalyzer()


@router.post("/register", response_model=RegisterStreamResponse)
async def register_stream(request: RegisterStreamRequest):
    """Register a new sensor stream"""
    try:
        stream_id = str(uuid.uuid4())
        dataset_id = str(uuid.uuid4())
        
        # Create state machine
        fsm = CycleStateMachine(stream_id, dataset_id)
        
        # Setup callbacks
        def on_state_change(**kwargs):
            # Broadcast state change to all connected WebSocket clients
            asyncio.create_task(broadcast_to_stream(
                stream_id,
                {
                    "type": "state_change",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "data": kwargs
                }
            ))
        
        async def on_cycle_complete(cycle: CycleMetadata):
            # Trigger analysis pipeline
            asyncio.create_task(analyze_completed_cycle(cycle))
            
            # Broadcast completion
            await broadcast_to_stream(
                stream_id,
                {
                    "type": "cycle_complete",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "data": {
                        "cycle_id": cycle.cycle_id,
                        "sample_count": cycle.sample_count,
                        "duration_sec": (cycle.end_time - cycle.start_time).total_seconds()
                    }
                }
            )
        
        fsm.on_state_change = on_state_change
        fsm.on_cycle_complete = on_cycle_complete
        
        state_machines[stream_id] = fsm
        
        # Register stream
        streams[stream_id] = {
            "stream_id": stream_id,
            "dataset_id": dataset_id,
            "device_name": request.device_name,
            "sensors": [s.dict() for s in request.sensors],
            "registered_at": datetime.utcnow().isoformat(),
            "sample_count": 0,
            "status": "registered"
        }
        
        # Transition to WAITING_START
        fsm.transition(CycleEvent.REGISTER_STREAM)
        
        return RegisterStreamResponse(
            stream_id=stream_id,
            dataset_id=dataset_id,
            status="registered"
        )
    
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchSamplesResponse)
async def ingest_batch(request: BatchSamplesRequest):
    """Ingest batch of samples"""
    try:
        stream_id = request.stream_id
        
        if stream_id not in streams:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        fsm = state_machines[stream_id]
        stream_info = streams[stream_id]
        
        # Convert to InfluxDB format and store
        samples_to_write = []
        for sample in request.samples:
            # Transition state machine
            fsm.transition(CycleEvent.SAMPLE_RECEIVED)
            
            # Create sample point
            point = SamplePoint(
                timestamp=sample.timestamp,
                sensor_id=sample.sensor_id,
                sensor_name=sample.sensor_name,
                dataset_id=stream_info['dataset_id'],
                cycle_id=fsm.current_cycle.cycle_id if fsm.current_cycle else "unknown",
                stream_id=stream_id,
                value=sample.value,
                quality=sample.quality,
                latency_ms=0  # Would calculate from timestamp
            )
            samples_to_write.append(point)
        
        # Write to InfluxDB
        success = influxdb_manager.write_samples(samples_to_write)
        
        # Update stream stats
        stream_info['sample_count'] += len(request.samples)
        
        # Broadcast samples to WebSocket clients
        await broadcast_to_stream(
            stream_id,
            {
                "type": "samples",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "sample_count": len(request.samples),
                    "samples": [s.dict() for s in request.samples[:5]]  # First 5 for preview
                }
            }
        )
        
        return BatchSamplesResponse(
            ack_id=str(uuid.uuid4()),
            buffer_status="ok",
            samples_received=len(request.samples)
        )
    
    except Exception as e:
        print(f"❌ Batch ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycle/start")
async def start_cycle(stream_id: str, cycle_metadata: Optional[Dict] = Body(None)):
    """Start a new cycle"""
    try:
        if stream_id not in state_machines:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        fsm = state_machines[stream_id]
        fsm.transition(CycleEvent.CYCLE_START, cycle_metadata or {})
        
        return {
            "status": "ok",
            "cycle_id": fsm.current_cycle.cycle_id if fsm.current_cycle else None,
            "state": fsm.state.value
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycle/stop")
async def stop_cycle(stream_id: str):
    """Stop current cycle"""
    try:
        if stream_id not in state_machines:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        fsm = state_machines[stream_id]
        fsm.transition(CycleEvent.CYCLE_STOP)
        
        return {
            "status": "ok",
            "state": fsm.state.value,
            "grace_period_sec": fsm.GRACE_PERIOD_SEC
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{stream_id}/status")
async def get_stream_status(stream_id: str):
    """Get stream and cycle status"""
    try:
        if stream_id not in streams:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        fsm = state_machines[stream_id]
        stream_info = streams[stream_id]
        
        return {
            "stream": stream_info,
            "cycle_status": fsm.get_status()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/stream/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint for live streaming"""
    try:
        if stream_id not in streams:
            await websocket.close(code=1008, reason="Stream not found")
            return
        
        await websocket.accept()
        
        # Add to clients list
        if stream_id not in websocket_clients:
            websocket_clients[stream_id] = []
        websocket_clients[stream_id].append(websocket)
        
        print(f"✅ Client connected to stream {stream_id}")
        
        # Send initial status and recent samples
        fsm = state_machines[stream_id]
        stream_info = streams[stream_id]
        
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "stream_id": stream_id,
                "status": stream_info.get('status'),
                "sample_count": stream_info.get('sample_count', 0),
                "sensors": stream_info.get('sensors', [])
            }
        }))
        
        # Send current cycle status
        await websocket.send_text(json.dumps({
            "type": "state_change",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": fsm.get_status()
        }))
        
        # Keep connection alive
        try:
            while True:
                # Receive messages (heartbeat, control commands)
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                elif data.startswith("cycle_start"):
                    fsm = state_machines[stream_id]
                    fsm.transition(CycleEvent.CYCLE_START)
                
                elif data.startswith("cycle_stop"):
                    fsm = state_machines[stream_id]
                    fsm.transition(CycleEvent.CYCLE_STOP)
        
        except WebSocketDisconnect:
            print(f"❌ Client disconnected from stream {stream_id}")
            websocket_clients[stream_id].remove(websocket)
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


async def broadcast_to_stream(stream_id: str, message: Dict):
    """Broadcast message to all connected clients for a stream"""
    try:
        if stream_id not in websocket_clients:
            return
        
        disconnected = []
        for websocket in websocket_clients[stream_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            websocket_clients[stream_id].remove(ws)
    
    except Exception as e:
        print(f"⚠️  Broadcast error: {e}")


async def analyze_completed_cycle(cycle: CycleMetadata):
    """Analyze a completed cycle"""
    try:
        print(f"🔬 Analyzing cycle {cycle.cycle_id}...")
        
        # Query samples from InfluxDB
        completed_samples = influxdb_manager.query_cycle_samples(cycle.cycle_id)
        
        # Get reference cycle (using previous or first cycle in dataset)
        # In production, would query database for reference
        reference_cycle_id = str(uuid.uuid4())  # Placeholder
        reference_samples = influxdb_manager.query_cycle_samples(reference_cycle_id)
        
        # Run analysis
        if completed_samples and reference_samples:
            result = deviation_analyzer.analyze_cycle(
                cycle_id=cycle.cycle_id,
                completed_samples=completed_samples,
                reference_samples=reference_samples,
                reference_cycle_id=reference_cycle_id,
                comparison_type="reference"
            )
            
            # Save results to database
            print(f"✅ Analysis complete: {result.overall_health_score:.1f}")
            
            # Broadcast results
            await broadcast_to_stream(
                cycle.stream_id,
                {
                    "type": "analysis_result",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "data": {
                        "cycle_id": cycle.cycle_id,
                        "health_score": result.overall_health_score,
                        "anomaly_flag": result.anomaly_flag,
                        "alerts": result.alerts,
                        "top_3_sensors": result.top_3_problematic_sensors
                    }
                }
            )
    
    except Exception as e:
        print(f"❌ Analysis error: {e}")


# Include this router in your main FastAPI app:
# app.include_router(router)
