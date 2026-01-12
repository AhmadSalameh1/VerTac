-- VerTac v0.2.0 Database Schema
-- Live Monitoring Tables

-- Live Streams Table
CREATE TABLE IF NOT EXISTS live_streams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id VARCHAR(255) UNIQUE NOT NULL,
    dataset_id UUID,
    device_name VARCHAR(255) NOT NULL,
    sensor_count INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'registered',
    registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_sample_at TIMESTAMP,
    total_samples INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Live Cycles Table
CREATE TABLE IF NOT EXISTS live_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id VARCHAR(255) UNIQUE NOT NULL,
    stream_id UUID REFERENCES live_streams(id) ON DELETE CASCADE,
    dataset_id UUID,
    cycle_number INTEGER NOT NULL,
    state VARCHAR(50) NOT NULL DEFAULT 'active',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    sample_count INTEGER DEFAULT 0,
    duration_sec FLOAT,
    is_reference BOOLEAN DEFAULT FALSE,
    health_score FLOAT,
    anomaly_flag BOOLEAN DEFAULT FALSE,
    abort_reason VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Live Deviations Table
CREATE TABLE IF NOT EXISTS live_deviations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID REFERENCES live_cycles(id) ON DELETE CASCADE,
    sensor_id VARCHAR(255) NOT NULL,
    sensor_name VARCHAR(255) NOT NULL,
    euclidean_distance FLOAT NOT NULL,
    dtw_distance FLOAT NOT NULL,
    max_deviation FLOAT NOT NULL,
    mean_deviation FLOAT NOT NULL,
    peak_deviation_time TIMESTAMP,
    contribution_rank INTEGER,
    severity VARCHAR(50) NOT NULL DEFAULT 'normal',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Live Alerts Table
CREATE TABLE IF NOT EXISTS live_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID REFERENCES live_cycles(id) ON DELETE CASCADE,
    sensor_id VARCHAR(255),
    sensor_name VARCHAR(255),
    severity VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    alert_type VARCHAR(50) NOT NULL DEFAULT 'deviation',
    euclidean_distance FLOAT,
    dtw_distance FLOAT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_live_streams_stream_id ON live_streams(stream_id);
CREATE INDEX IF NOT EXISTS idx_live_streams_dataset_id ON live_streams(dataset_id);
CREATE INDEX IF NOT EXISTS idx_live_streams_status ON live_streams(status);

CREATE INDEX IF NOT EXISTS idx_live_cycles_cycle_id ON live_cycles(cycle_id);
CREATE INDEX IF NOT EXISTS idx_live_cycles_stream_id ON live_cycles(stream_id);
CREATE INDEX IF NOT EXISTS idx_live_cycles_dataset_id ON live_cycles(dataset_id);
CREATE INDEX IF NOT EXISTS idx_live_cycles_state ON live_cycles(state);
CREATE INDEX IF NOT EXISTS idx_live_cycles_start_time ON live_cycles(start_time);

CREATE INDEX IF NOT EXISTS idx_live_deviations_cycle_id ON live_deviations(cycle_id);
CREATE INDEX IF NOT EXISTS idx_live_deviations_sensor_id ON live_deviations(sensor_id);
CREATE INDEX IF NOT EXISTS idx_live_deviations_severity ON live_deviations(severity);

CREATE INDEX IF NOT EXISTS idx_live_alerts_cycle_id ON live_alerts(cycle_id);
CREATE INDEX IF NOT EXISTS idx_live_alerts_severity ON live_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_live_alerts_acknowledged ON live_alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_live_alerts_created_at ON live_alerts(created_at);

-- Update Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_live_streams_updated_at BEFORE UPDATE ON live_streams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_live_cycles_updated_at BEFORE UPDATE ON live_cycles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant Permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON TABLE live_streams TO vertac;
-- GRANT ALL PRIVILEGES ON TABLE live_cycles TO vertac;
-- GRANT ALL PRIVILEGES ON TABLE live_deviations TO vertac;
-- GRANT ALL PRIVILEGES ON TABLE live_alerts TO vertac;
