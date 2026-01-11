import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { listCycles, getCycle, setReferenceCycle, Cycle, CycleDetail } from '../services/api';
import CycleChart from '../components/CycleChart';
import './CycleViewer.css';

const CycleViewer: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [selectedCycle, setSelectedCycle] = useState<CycleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCycles = async (dsId: number) => {
    try {
      setLoading(true);
      const data = await listCycles(dsId);
      setCycles(data);
      if (data.length > 0) {
        loadCycleDetail(data[0].id);
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load cycles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (datasetId) {
      loadCycles(parseInt(datasetId));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  const loadCycleDetail = async (cycleId: number) => {
    try {
      const detail = await getCycle(cycleId, true);
      setSelectedCycle(detail);
    } catch (err: any) {
      setError(err.message || 'Failed to load cycle detail');
    }
  };

  const handleSetReference = async (cycleId: number) => {
    try {
      await setReferenceCycle(cycleId);
      if (datasetId) {
        loadCycles(parseInt(datasetId));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to set reference cycle');
    }
  };

  const referenceCycle = cycles.find((c) => c.is_reference);

  return (
    <div className="cycle-viewer">
      <h1>Cycle Viewer</h1>
      <p className="subtitle">View and compare cycle data</p>

      {loading && <div className="loading">Loading cycles...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && cycles.length === 0 && (
        <div className="empty-state card">
          <p>No cycles found in this dataset</p>
        </div>
      )}

      {!loading && !error && cycles.length > 0 && (
        <div className="cycle-layout">
          <div className="cycle-sidebar card">
            <h3>Cycles ({cycles.length})</h3>
            {referenceCycle && (
              <div className="reference-info">
                <span className="badge success">Reference: Cycle {referenceCycle.cycle_number}</span>
              </div>
            )}
            <div className="cycle-list">
              {cycles.map((cycle) => (
                <div
                  key={cycle.id}
                  className={`cycle-item ${selectedCycle?.id === cycle.id ? 'active' : ''}`}
                  onClick={() => loadCycleDetail(cycle.id)}
                >
                  <div className="cycle-item-header">
                    <span className="cycle-number">Cycle {cycle.cycle_number}</span>
                    {cycle.is_reference && <span className="badge success small">REF</span>}
                    {cycle.is_anomalous && <span className="badge danger small">!</span>}
                  </div>
                  <div className="cycle-item-details">
                    <small>Duration: {cycle.duration.toFixed(2)}s</small>
                    {cycle.anomaly_score && (
                      <small className="anomaly-score">
                        Score: {(cycle.anomaly_score * 100).toFixed(0)}%
                      </small>
                    )}
                  </div>
                  {!cycle.is_reference && (
                    <button
                      className="set-reference-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSetReference(cycle.id);
                      }}
                    >
                      Set as Reference
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="cycle-content">
            {selectedCycle && (
              <>
                <div className="card cycle-info">
                  <h2>Cycle {selectedCycle.cycle_number}</h2>
                  <div className="cycle-stats">
                    <div className="stat">
                      <label>Duration</label>
                      <span className="value">{selectedCycle.duration.toFixed(2)}s</span>
                    </div>
                    <div className="stat">
                      <label>Start Time</label>
                      <span className="value">{selectedCycle.start_time.toFixed(2)}</span>
                    </div>
                    <div className="stat">
                      <label>End Time</label>
                      <span className="value">{selectedCycle.end_time.toFixed(2)}</span>
                    </div>
                    <div className="stat">
                      <label>Status</label>
                      <span className="value">
                        {selectedCycle.is_complete ? (
                          <span className="badge success">Complete</span>
                        ) : (
                          <span className="badge danger">Incomplete</span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3>Sensor Data</h3>
                  {selectedCycle.sensor_data && selectedCycle.sensor_data.length > 0 ? (
                    <CycleChart sensorData={selectedCycle.sensor_data} />
                  ) : (
                    <p>No sensor data available</p>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CycleViewer;
