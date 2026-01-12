# VerTac v0.2.0 Architecture: Real-Time Cycle Monitoring System

## Overview
Version 0.2.0 extends VerTac from batch-only analysis to support live sensor ingestion with real-time monitoring, cycle state management, and unified analysis pipelines for both batch and live data.

---

## System Architecture

### 1. Edge Connector (Edge Layer)
**Purpose**: Lightweight service running near the machine that ingests multi-sensor data

**Components**:
- **Sensor Interface** - Supports multiple input types:
  - PLC (OPC-UA, Modbus)
  - DAQ systems (data acquisition cards)
  - Microcontrollers (serial, MQTT)
  - Simulators (test data generators)
  
- **Local Buffer** - Queue mechanism for reliability:
  - Configurable buffer size (default: 1000 samples/sensor)
  - FIFO persistence to disk if network fails
  - Automatic retry with exponential backoff
  
- **Timestamping** - Precise timing at source:
  - Microsecond-precision timestamps
  - Clock sync with backend
  - Latency tracking
  
- **HTTP/WebSocket Transmitter**:
  - Batches samples (default: 10-sample batches or 1s timeout)
  - HTTP POST for initial handshake and config
  - WebSocket for continuous streaming
  - Compression (gzip) for bandwidth optimization

**Technology**: Python with asyncio, local SQLite buffer, aiohttp for networking

**Deployment**: Raspberry Pi, edge server, or Docker container

---

### 2. Backend Services (Application Layer)

#### 2.1 Ingestion API
**Endpoints**:
```
POST /api/live/register
  - Register new sensor stream
  - Returns stream_id and buffer config
  
POST /api/live/batch
  - Accept batch of timestamped samples
  - Body: {stream_id, samples: [{timestamp, sensor_id, value}, ...]}
  - Response: {ack_id, buffer_status}
  
WebSocket /ws/live/stream/{stream_id}
  - Continuous sample ingestion
  - Auto-reconnection and heartbeat
```

#### 2.2 Time-Series Database
**Technology**: InfluxDB 2.x
- **Measurement**: `sensor_readings`
- **Tags**: dataset_id, cycle_id, stream_id, sensor_name
- **Fields**: value, quality_score, latency_ms
- **Retention**: Raw (7 days), 1-minute aggregates (90 days)
- **Query Language**: Flux

**Storage Model**:
```
measurement: sensor_readings
tags:
  dataset_id: string
  cycle_id: string
  stream_id: string
  sensor_name: string
fields:
  value: float
  quality: float (0-1)
  latency_ms: int
timestamp: nanosecond precision
```

#### 2.3 Cycle State Machine
**States**:
1. **IDLE** - No active cycle
2. **WAITING_START** - Stream registered, awaiting start event
3. **ACTIVE** - Cycle running, samples being collected
4. **STOPPING** - Stop signal received, waiting for grace period
5. **STOPPED** - Cycle complete, ready for analysis
6. **ABORTED** - Abnormal termination detected

**Transitions**:
- IDLE → WAITING_START: Register stream
- WAITING_START → ACTIVE: Receive `cycle_start` event
- ACTIVE → STOPPING: Receive `cycle_stop` event
- STOPPING → STOPPED: Grace period elapsed + no new samples
- ACTIVE → ABORTED: Connection loss > timeout threshold
- STOPPED/ABORTED → IDLE: User acknowledgment

**Events**:
```python
{
  "type": "cycle_start" | "cycle_stop" | "cycle_pause" | "cycle_resume",
  "timestamp": ISO8601,
  "cycle_id": string,
  "metadata": {...}
}
```

#### 2.4 Live Streaming Service
**Technology**: FastAPI WebSocket + Redis Pub/Sub

**Channels**:
- `/live/{dataset_id}/{cycle_id}` - Raw samples stream
- `/events/{dataset_id}` - Cycle state changes
- `/analysis/{dataset_id}/{cycle_id}` - Deviations and alerts

**Message Format**:
```json
{
  "type": "sample" | "state_change" | "deviation" | "alert",
  "timestamp": "2026-01-11T10:30:45.123Z",
  "data": {...}
}
```

#### 2.5 Real-Time Deviation Pipeline
**Triggered**: When cycle transitions to STOPPED or ABORTED

**Process**:
1. **Data Collection**:
   - Retrieve completed cycle samples from InfluxDB
   - Retrieve reference cycle samples (user-selected or auto-detected)
   - Retrieve previous cycle samples (immediate predecessor)

2. **Signal Processing**:
   - Normalization against reference
   - Smoothing (Savitzky-Golay filter)
   - Feature extraction (FFT, statistical moments)

3. **Deviation Computation**:
   - Euclidean distance per sensor
   - Dynamic Time Warping (DTW) distance
   - Frequency-domain differences

4. **Anomaly Scoring**:
   - Per-sensor deviation scores
   - Overall cycle health score (0-100)
   - Comparison to historical baseline

5. **Ranking and Alerts**:
   - Rank sensors by contribution to anomaly
   - Generate alerts if scores exceed thresholds
   - Categorize: normal, warning, critical

6. **Storage**:
   - Save deviation results to PostgreSQL
   - Emit WebSocket alerts to connected clients
   - Update cycle status with analysis results

---

### 3. Frontend Application (Presentation Layer)

#### 3.1 Live Monitoring View
**Components**:
- **Signal Chart** - Real-time line charts (5-30s window)
  - Multiple series (one per sensor)
  - Auto-scroll with zoom/pan
  - Legend with min/max/avg displays
  
- **Cycle Status Panel**:
  - Current cycle ID, start time, elapsed time
  - State indicator (ACTIVE, STOPPING, etc.)
  - Sample count and data rate (samples/sec)
  
- **Sensor Grid**:
  - Current values for all sensors
  - Real-time min/max/avg
  - Quality indicator
  
- **Alerts Ticker**:
  - Live warning/critical alerts
  - Color-coded by severity
  - Timestamp and affected sensor

#### 3.2 Post-Cycle Analysis View
**Displays**:
- Completed cycle waveforms (all sensors)
- Deviation heatmap (sensors × time)
- Sensor contribution ranking (bar chart)
- Comparison overlay (completed vs reference cycle)
- Alert summary with root cause hints

#### 3.3 Stop Analysis View
**For Abnormal Stops**:
- Timeline of last 30 seconds before stop
- Last sample values per sensor
- Quality degradation indicators
- Hypothesis for stop cause (connection loss, sensor fault, etc.)

#### 3.4 Unified Data Management
**Backend Integration**:
- Load live data via WebSocket + HTTP
- Query historical batch data alongside live
- Unified reference cycle picker (batch or live)
- Export live cycle as batch dataset

---

## Data Flow

### Batch Workflow (v0.1.0 - Unchanged)
```
CSV Upload → Backend Parse → PostgreSQL → Analysis Page
```

### Live Workflow (v0.2.0 - New)
```
Sensor → Edge Connector → Ingestion API → InfluxDB
                                    ↓
                            WebSocket Stream
                                    ↓
                          Frontend (Live View)
                                    ↓
              [Cycle Complete/Abnormal Stop]
                                    ↓
                    Deviation Pipeline (Batch-like)
                                    ↓
                      PostgreSQL (Results) + Alerts
                                    ↓
              Frontend (Post-Cycle Analysis View)
```

---

## Database Schema Additions

### PostgreSQL (New Tables)

#### `live_streams`
```sql
CREATE TABLE live_streams (
  id UUID PRIMARY KEY,
  dataset_id UUID REFERENCES datasets(id),
  stream_name VARCHAR(255),
  sensor_count INT,
  status VARCHAR(50), -- IDLE, ACTIVE, STOPPED, ABORTED
  registered_at TIMESTAMP,
  started_at TIMESTAMP,
  stopped_at TIMESTAMP
);
```

#### `live_cycles`
```sql
CREATE TABLE live_cycles (
  id UUID PRIMARY KEY,
  stream_id UUID REFERENCES live_streams(id),
  cycle_number INT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  sample_count INT,
  status VARCHAR(50), -- ACTIVE, STOPPED, ABORTED
  is_reference BOOLEAN DEFAULT FALSE,
  health_score FLOAT,
  anomaly_flag BOOLEAN DEFAULT FALSE
);
```

#### `live_deviations`
```sql
CREATE TABLE live_deviations (
  id UUID PRIMARY KEY,
  cycle_id UUID REFERENCES live_cycles(id),
  reference_cycle_id UUID REFERENCES live_cycles(id),
  sensor_id UUID REFERENCES sensors(id),
  euclidean_distance FLOAT,
  dtw_distance FLOAT,
  contribution_rank INT,
  severity VARCHAR(50) -- normal, warning, critical
);
```

#### `live_alerts`
```sql
CREATE TABLE live_alerts (
  id UUID PRIMARY KEY,
  cycle_id UUID REFERENCES live_cycles(id),
  sensor_id UUID REFERENCES sensors(id),
  alert_type VARCHAR(50), -- threshold_exceeded, anomaly_detected, etc.
  severity VARCHAR(50),
  message TEXT,
  created_at TIMESTAMP
);
```

### InfluxDB
- Already described in "Time-Series Database" section above

---

## Implementation Phases

### Phase 1: Infrastructure Setup
- [ ] InfluxDB Docker container setup
- [ ] Database schema and migrations
- [ ] WebSocket server implementation
- [ ] Redis pub/sub setup

### Phase 2: Edge Connector
- [ ] Sensor interface abstraction
- [ ] Local buffer implementation
- [ ] HTTP/WebSocket transmitter
- [ ] Simulator for testing

### Phase 3: Backend Services
- [ ] Ingestion API endpoints
- [ ] Cycle state machine
- [ ] Live streaming service
- [ ] Real-time deviation pipeline

### Phase 4: Frontend
- [ ] Live monitoring components
- [ ] Post-cycle analysis views
- [ ] WebSocket integration
- [ ] Unified data management

### Phase 5: Testing & Release
- [ ] End-to-end integration tests
- [ ] Load testing (1000s of samples/sec)
- [ ] Documentation and deployment guide
- [ ] v0.2.0 release

---

## Configuration

### Edge Connector (config.yaml)
```yaml
edge:
  device_name: "Machine-01"
  sensors:
    - name: "motor_speed"
      type: "analog"
      unit: "RPM"
    - name: "vibration"
      type: "accelerometer"
      unit: "m/s²"
  
  buffer:
    max_samples: 1000
    flush_interval_sec: 1
    batch_size: 10
  
  connection:
    backend_url: "http://backend:8000"
    ws_url: "ws://backend:8000"
    retry_max_attempts: 5
    retry_backoff_sec: 2
```

### Backend (.env)
```
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=<token>
INFLUXDB_ORG=vertac
INFLUXDB_BUCKET=sensor_readings

REDIS_URL=redis://redis:6379

DATABASE_URL=postgresql://user:pass@postgres:5432/vertac

CYCLE_GRACE_PERIOD_SEC=10
SAMPLE_TIMEOUT_SEC=30
```

---

## Key Technologies

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Edge Connector | Python + asyncio | Lightweight, easy deployment |
| Time-Series DB | InfluxDB 2.x | Optimized for metrics, high write throughput |
| Cycle State Machine | Python dataclasses + enums | Clean, type-safe implementation |
| WebSocket | FastAPI WebSocket | Integrated with existing backend |
| Live Streaming | Redis Pub/Sub | Horizontal scalability, decoupling |
| Signal Processing | SciPy, NumPy | Established DSP libraries |
| Frontend Charts | Chart.js or Plotly | Real-time performance, existing use |

---

## Success Criteria for v0.2.0

✅ Edge connector ingests 1000+ samples/sec per sensor  
✅ Backend stores with <100ms latency  
✅ Live view updates at 10+ FPS  
✅ Cycle state machine handles all edge cases (reconnection, pause/resume, abnormal stops)  
✅ Deviation pipeline completes within 5 seconds of cycle stop  
✅ Alert generation is accurate (no false positives on healthy cycles)  
✅ Frontend unifies batch and live data seamlessly  
✅ Full backward compatibility with v0.1.0 batch workflow  

---

## Rollback and Compatibility

- v0.2.0 is **additive only** - v0.1.0 batch workflow unchanged
- Live data stored in new InfluxDB (separate from PostgreSQL batch data)
- WebSocket optional - frontend works without it
- Can disable live features via feature flags if needed
