# VerTac v0.2.0 Implementation Guide

## Quick Start

### 1. Backend Integration

Add the live routes to your FastAPI application in `backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from live.routes import router as live_router

app = FastAPI(title="VerTac v0.2.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include live monitoring routes
app.include_router(live_router)

# Your existing routes...
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}
```

### 2. Frontend Integration

#### Add Live Monitoring Page

Create new page in `frontend/src/pages/LiveMonitoring.tsx`:

```typescript
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import LiveMonitoring from '../components/Live/LiveMonitoring';

export default function LiveMonitoringPage() {
  const { streamId } = useParams<{ streamId: string }>();
  
  if (!streamId) {
    return <div>Stream ID not provided</div>;
  }
  
  return <LiveMonitoring streamId={streamId} />;
}
```

#### Update Router

Add to `frontend/src/App.tsx`:

```typescript
import LiveMonitoringPage from './pages/LiveMonitoring';

// In your route definitions:
<Route path="/live/:streamId" element={<LiveMonitoringPage />} />
<Route path="/live/analysis/:cycleId" element={<PostCycleAnalysisPage />} />
```

#### Add Navigation

Update navigation menu to include Live Monitoring link.

### 3. Database Setup

#### PostgreSQL Migrations

Run these in your database:

```sql
-- Live streams table
CREATE TABLE live_streams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_id UUID REFERENCES datasets(id),
  stream_name VARCHAR(255) NOT NULL,
  device_name VARCHAR(255),
  sensor_count INT,
  status VARCHAR(50) DEFAULT 'idle',
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP,
  stopped_at TIMESTAMP
);

-- Live cycles table
CREATE TABLE live_cycles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stream_id UUID REFERENCES live_streams(id) ON DELETE CASCADE,
  cycle_number INT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  sample_count INT DEFAULT 0,
  status VARCHAR(50) DEFAULT 'active',
  is_reference BOOLEAN DEFAULT FALSE,
  health_score FLOAT,
  anomaly_flag BOOLEAN DEFAULT FALSE
);

-- Live deviations table
CREATE TABLE live_deviations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_id UUID REFERENCES live_cycles(id) ON DELETE CASCADE,
  reference_cycle_id UUID REFERENCES live_cycles(id),
  sensor_id VARCHAR(255),
  sensor_name VARCHAR(255),
  euclidean_distance FLOAT,
  dtw_distance FLOAT,
  max_deviation FLOAT,
  mean_deviation FLOAT,
  contribution_rank INT,
  severity VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Live alerts table
CREATE TABLE live_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_id UUID REFERENCES live_cycles(id) ON DELETE CASCADE,
  sensor_id VARCHAR(255),
  sensor_name VARCHAR(255),
  alert_type VARCHAR(50),
  severity VARCHAR(50),
  message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_live_streams_dataset ON live_streams(dataset_id);
CREATE INDEX idx_live_streams_status ON live_streams(status);
CREATE INDEX idx_live_cycles_stream ON live_cycles(stream_id);
CREATE INDEX idx_live_cycles_status ON live_cycles(status);
CREATE INDEX idx_live_deviations_cycle ON live_deviations(cycle_id);
CREATE INDEX idx_live_alerts_cycle ON live_alerts(cycle_id);
```

#### InfluxDB Setup

```bash
# Docker compose example
services:
  influxdb:
    image: influxdb:2.7
    container_name: influxdb
    ports:
      - "8086:8086"
    environment:
      INFLUXDB_DB: vertac
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: admin123
      INFLUXDB_USER: vertac
      INFLUXDB_USER_PASSWORD: vertac123
    volumes:
      - influxdb-storage:/var/lib/influxdb2
    networks:
      - vertac-network

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - vertac-network
```

### 4. Environment Variables

Create `.env` file in backend:

```bash
# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-admin-token-here
INFLUXDB_ORG=vertac
INFLUXDB_BUCKET=sensor_readings

# Redis
REDIS_URL=redis://redis:6379

# Cycle Management
CYCLE_GRACE_PERIOD_SEC=10
SAMPLE_TIMEOUT_SEC=30
```

### 5. Running Edge Connector

```bash
# Install dependencies
cd edge-connector
pip install -r requirements.txt

# Run connector
python connector.py
```

The connector will:
- Register with backend
- Start reading from simulated sensors
- Buffer and retry failed uploads
- Maintain local SQLite cache

## API Endpoints

### Register Stream
```
POST /api/live/register
Content-Type: application/json

{
  "device_name": "Machine-01",
  "sensor_count": 3,
  "sensors": [
    {
      "sensor_id": "uuid",
      "name": "motor_speed",
      "type": "analog",
      "unit": "RPM"
    }
  ]
}

Response:
{
  "stream_id": "uuid",
  "dataset_id": "uuid",
  "status": "registered"
}
```

### Ingest Batch Samples
```
POST /api/live/batch
Content-Type: application/json

{
  "stream_id": "uuid",
  "samples": [
    {
      "timestamp": "2026-01-11T10:30:45.123Z",
      "sensor_id": "uuid",
      "sensor_name": "motor_speed",
      "value": 1500.5,
      "unit": "RPM",
      "quality": 0.95
    }
  ]
}

Response:
{
  "ack_id": "uuid",
  "buffer_status": "ok",
  "samples_received": 10
}
```

### Start Cycle
```
POST /api/live/cycle/start?stream_id=uuid
Content-Type: application/json

{
  "metadata": {
    "operator": "John Doe",
    "comments": "Normal run"
  }
}

Response:
{
  "status": "ok",
  "cycle_id": "uuid",
  "state": "active"
}
```

### WebSocket Connection
```
WebSocket /api/live/ws/stream/{stream_id}

Messages received:
{
  "type": "samples" | "state_change" | "analysis_result" | "pong",
  "timestamp": "2026-01-11T10:30:45.123Z",
  "data": {...}
}

Commands sent:
"ping"
"cycle_start"
"cycle_stop"
```

## Deployment Checklist

### Development
- [ ] InfluxDB running locally
- [ ] Redis running
- [ ] Edge connector running
- [ ] Backend updated with live routes
- [ ] Frontend components imported and routed
- [ ] Database migrations applied

### Staging
- [ ] Docker containers for all services
- [ ] docker-compose.yml created
- [ ] Environment variables configured
- [ ] Load testing with 100+ sensors
- [ ] Connection retry logic verified
- [ ] Deviation pipeline tested

### Production
- [ ] InfluxDB with persistent storage
- [ ] Backup strategy for databases
- [ ] Monitoring and alerting setup
- [ ] SSL/TLS for WebSockets
- [ ] Rate limiting on APIs
- [ ] Horizontal scaling for WebSocket servers
- [ ] Data retention policies

## Testing

### Unit Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Integration Tests

```bash
# Full stack test
python tests/integration/test_end_to_end.py
```

### Load Testing

```bash
# 1000 samples/sec for 10 minutes
locust -f tests/load/locustfile.py --headless \
  -u 100 -r 10 -t 10m \
  --host=http://localhost:8000
```

## Troubleshooting

### Edge Connector Won't Connect
```bash
# Check backend URL
curl http://localhost:8000/api/health

# Check logs
tail -f edge_connector.log
```

### High Latency in WebSocket
```
- Check network connectivity
- Reduce batch size in edge connector
- Scale up Redis
- Add WebSocket server load balancer
```

### InfluxDB Write Failures
```bash
# Check InfluxDB status
influx health

# Check bucket exists
influx bucket list --org vertac

# Verify token
influx auth list
```

### Analysis Pipeline Too Slow
```
- Profile with Python profiler
- Optimize signal processing filters
- Parallelize sensor comparisons
- Cache reference cycles
```

## Performance Optimization

### Edge Connector
- Batch size: 10-50 samples (trade-off latency vs overhead)
- Flush interval: 0.5-2.0 seconds
- Buffer size: 1000-10000 samples

### Backend
- InfluxDB thread pool: 10-20
- WebSocket connections per server: 10000+
- Redis memory limit: 2GB+

### Frontend
- Keep only last 300 samples in memory
- Virtualize long lists
- Debounce WebSocket message handlers
- Use memoization for chart data

## Monitoring Queries

### Sample Throughput
```flux
from(bucket: "sensor_readings")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensor_readings")
  |> group(columns: ["stream_id"])
  |> count()
```

### Latest Cycle Status
```sql
SELECT stream_id, state, sample_count, start_time
FROM live_cycles
WHERE end_time IS NULL
ORDER BY start_time DESC;
```

### Failed Alerts
```sql
SELECT COUNT(*) as critical_count
FROM live_alerts
WHERE severity = 'critical'
  AND created_at > now() - interval '24 hours';
```

## Next Steps

1. **Custom Sensor Integrations**
   - Implement OPC-UA client in edge connector
   - Add Modbus TCP support
   - MQTT subscriber support

2. **Advanced Analytics**
   - Machine learning anomaly detection
   - Predictive maintenance models
   - Pattern recognition in deviations

3. **Data Export**
   - Export to Parquet for data science
   - Integration with data lakes
   - Real-time Kafka streaming

4. **Mobile Support**
   - React Native app for iOS/Android
   - Push notifications for critical alerts
   - Offline mode with sync

## Support and Updates

For issues or feature requests:
- GitHub Issues: [VerTac Issues]
- Email: support@vertac.io
- Slack: #vertac-support

Version: 0.2.0
Last Updated: January 11, 2026
