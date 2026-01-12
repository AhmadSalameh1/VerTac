import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './LiveMonitoring.css';

interface Sample {
  timestamp: string;
  sensor_id: string;
  sensor_name: string;
  value: number;
  unit: string;
  quality: number;
}

interface CycleStatus {
  stream_id: string;
  state: string;
  cycle_id: string | null;
  cycle_number: number | null;
  start_time: string | null;
  sample_count: number;
  last_sample_time: string | null;
}

interface AlertMessage {
  sensor_id: string;
  sensor_name: string;
  severity: string;
  message: string;
}

export const LiveMonitoring: React.FC<{ streamId?: string }> = ({ streamId: propStreamId }) => {
  const [searchParams] = useSearchParams();
  const [inputStreamId, setInputStreamId] = useState('');
  const streamId = propStreamId || searchParams.get('streamId') || inputStreamId;
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [cycleStatus, setCycleStatus] = useState<CycleStatus | null>(null);
  const [alerts, setAlerts] = useState<AlertMessage[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [currentSensorValues, setCurrentSensorValues] = useState<Record<string, number>>({});
  const [isConnected, setIsConnected] = useState(false);
  const alertScrollRef = useRef<HTMLDivElement>(null);

  const handleSamples = (newSamples: Sample[]) => {
    console.log(`📊 Processing ${newSamples.length} samples`);
    setSamples((prev) => {
      // Keep last 300 samples (5 minutes at 1Hz)
      const combined = [...prev, ...newSamples];
      return combined.slice(-300);
    });

    // Update current values and chart data
    const values: Record<string, number> = {};
    const chartPoint: any = {
      time: new Date().toLocaleTimeString(),
    };

    newSamples.forEach((sample) => {
      values[sample.sensor_name] = sample.value;
      chartPoint[sample.sensor_name] = sample.value;
    });

    setCurrentSensorValues((prev) => ({ ...prev, ...values }));

    setChartData((prev) => {
      const updated = [...prev, chartPoint];
      return updated.slice(-100); // Keep last 100 points on chart
    });
  };

  // WebSocket connection
  useEffect(() => {
    if (!streamId) return;

    const wsUrl = `ws://localhost:8000/api/live/ws/stream/${streamId}`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('✅ Connected to live stream');
      setIsConnected(true);
      // Send initial heartbeat
      websocket.send('ping');
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('📨 Received:', message.type);
        
        switch (message.type) {
          case 'samples':
            if (message.data?.samples) {
              handleSamples(message.data.samples);
            }
            break;
          case 'state_change':
            setCycleStatus(message.data);
            break;
          case 'connection_established':
            console.log('✅ Connection established');
            break;
          case 'alert':
            setAlerts(prev => [...prev, message.data]);
            break;
          case 'pong':
            break;
        }
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    websocket.onclose = () => {
      console.log('❌ Disconnected from live stream');
      setIsConnected(false);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);

    // Heartbeat interval
    const heartbeatInterval = setInterval(() => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send('ping');
      }
    }, 30000);

    return () => {
      clearInterval(heartbeatInterval);
      websocket.close();
    };
  }, [streamId]);

  const handleAnalysisResult = (data: any) => {
    // Display analysis alerts
    if (data.alerts && data.alerts.length > 0) {
      setAlerts(data.alerts);
    }
  };

  const startCycle = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send('cycle_start');
    }
  };

  const stopCycle = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send('cycle_stop');
    }
  };

  const connectionClass = isConnected ? 'connected' : 'disconnected';

  // If no stream ID is set, show input form
  if (!streamId) {
    return (
      <div className="live-monitoring">
        <div className="monitoring-header">
          <h1>🔴 Live Monitoring</h1>
        </div>
        <div className="stream-input-container">
          <h2>Enter Stream ID</h2>
          <p>Enter your live stream ID to start monitoring</p>
          <div className="input-group">
            <input
              type="text"
              placeholder="e.g., 5cb4f558-2c0a-4056-b36a-12d06dae3017"
              value={inputStreamId}
              onChange={(e) => setInputStreamId(e.target.value)}
              className="stream-input"
            />
            <button
              onClick={() => {
                if (inputStreamId.trim()) {
                  window.location.href = `/live?streamId=${inputStreamId}`;
                }
              }}
              className="btn btn-primary"
            >
              Connect
            </button>
          </div>
          <div className="help-text">
            <p><strong>Example Stream ID:</strong> 5cb4f558-2c0a-4056-b36a-12d06dae3017</p>
            <p>Get your stream ID from the edge connector registration output.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="live-monitoring">
      <div className="monitoring-header">
        <h1>🔴 Live Monitoring</h1>
        <div className={`connection-status ${connectionClass}`}>
          <div className="status-indicator"></div>
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Cycle Status Panel */}
      {cycleStatus && (
        <div className="cycle-status-panel">
          <div className="status-info">
            <div className="status-item">
              <span className="label">State:</span>
              <span className={`value state-${cycleStatus.state}`}>
                {cycleStatus.state.toUpperCase()}
              </span>
            </div>
            <div className="status-item">
              <span className="label">Cycle ID:</span>
              <span className="value">{cycleStatus.cycle_id?.substring(0, 8) || 'N/A'}</span>
            </div>
            <div className="status-item">
              <span className="label">Samples:</span>
              <span className="value">{cycleStatus.sample_count}</span>
            </div>
            {cycleStatus.start_time && (
              <div className="status-item">
                <span className="label">Duration:</span>
                <span className="value">
                  {Math.floor(
                    (Date.now() - new Date(cycleStatus.start_time).getTime()) / 1000
                  )}s
                </span>
              </div>
            )}
          </div>

          <div className="cycle-controls">
            <button
              onClick={startCycle}
              disabled={cycleStatus.state === 'active'}
              className="btn btn-start"
            >
              ▶️ Start Cycle
            </button>
            <button
              onClick={stopCycle}
              disabled={cycleStatus.state !== 'active'}
              className="btn btn-stop"
            >
              ⏹️ Stop Cycle
            </button>
          </div>
        </div>
      )}

      {/* Live Chart */}
      <div className="live-chart-container">
        <h2>📊 Real-Time Signals</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              {Object.keys(currentSensorValues).map((sensor, idx) => (
                <Line
                  key={sensor}
                  type="monotone"
                  dataKey={sensor}
                  stroke={`hsl(${(idx * 360) / Object.keys(currentSensorValues).length}, 100%, 50%)`}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-data">Waiting for data...</div>
        )}
      </div>

      {/* Sensor Grid */}
      <div className="sensor-grid">
        <h2>📈 Current Values</h2>
        <div className="grid">
          {Object.entries(currentSensorValues).map(([sensor, value]) => (
            <div key={sensor} className="sensor-card">
              <div className="sensor-name">{sensor}</div>
              <div className="sensor-value">{value.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts */}
      <div className="alerts-container">
        <h2>🚨 Alerts</h2>
        <div className="alerts-list" ref={alertScrollRef}>
          {alerts.length > 0 ? (
            alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`alert alert-${alert.severity}`}
              >
                <span className="alert-sensor">{alert.sensor_name}</span>
                <span className="alert-message">{alert.message}</span>
              </div>
            ))
          ) : (
            <div className="no-alerts">No alerts - system operating normally</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoring;
