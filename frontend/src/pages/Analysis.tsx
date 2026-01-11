import React, { useState, useEffect } from 'react';
import { listDatasets, listCycles, analyzeCycleDeviations, Dataset, Cycle, DeviationAnalysis } from '../services/api';
import './Analysis.css';

const Analysis: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [selectedCycle, setSelectedCycle] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<DeviationAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  useEffect(() => {
    if (selectedDataset) {
      loadCycles(selectedDataset);
    } else {
      setCycles([]);
      setSelectedCycle(null);
    }
  }, [selectedDataset]);

  const loadDatasets = async () => {
    try {
      const data = await listDatasets();
      setDatasets(data);
    } catch (err) {
      console.error('Failed to load datasets:', err);
    }
  };

  const loadCycles = async (datasetId: number) => {
    try {
      const data = await listCycles(datasetId);
      setCycles(data);
    } catch (err) {
      console.error('Failed to load cycles:', err);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedCycle) {
      setError('Please select a cycle');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await analyzeCycleDeviations(selectedCycle, true, true);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: number): string => {
    if (severity > 0.7) return '#dc2626';
    if (severity > 0.4) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="analysis-page">
      <h1>Cycle Analysis</h1>
      <p className="subtitle">Analyze deviations and detect anomalies</p>

      <div className="card">
        <h2>Select Cycle for Analysis</h2>
        <div className="analysis-form">
          <div className="form-group">
            <label>Dataset</label>
            <select
              value={selectedDataset || ''}
              onChange={(e) => setSelectedDataset(parseInt(e.target.value))}
            >
              <option value="">Select a dataset...</option>
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.total_cycles} cycles)
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Cycle</label>
            <select
              value={selectedCycle || ''}
              onChange={(e) => setSelectedCycle(parseInt(e.target.value))}
              disabled={!selectedDataset}
            >
              <option value="">Select a cycle...</option>
              {cycles.map((cycle) => (
                <option key={cycle.id} value={cycle.id}>
                  Cycle {cycle.cycle_number}
                  {cycle.is_reference && ' (Reference)'}
                  {cycle.is_anomalous && ' ⚠️'}
                </option>
              ))}
            </select>
          </div>
          <button className="primary" onClick={handleAnalyze} disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {analysis && (
        <>
          <div className="card">
            <h2>Overall Health</h2>
            <div className="health-score-container">
              <div className="health-score-circle">
                <svg viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke={getSeverityColor(1 - analysis.overall_health_score)}
                    strokeWidth="8"
                    strokeDasharray={`${analysis.overall_health_score * 251.2} 251.2`}
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className="health-score-value">
                  {(analysis.overall_health_score * 100).toFixed(0)}%
                </div>
              </div>
              <div className="health-details">
                <h3>Health Score</h3>
                <p>
                  {analysis.has_deviations
                    ? `${
                        analysis.deviations_from_reference.length +
                        analysis.deviations_from_previous.length
                      } deviation(s) detected`
                    : 'No deviations detected'}
                </p>
              </div>
            </div>
          </div>

          {analysis.deviations_from_reference.length > 0 && (
            <div className="card">
              <h2>Deviations from Reference</h2>
              <div className="deviations-list">
                {analysis.deviations_from_reference.map((dev, idx) => (
                  <div key={idx} className="deviation-item">
                    <div className="deviation-header">
                      <span className="sensor-name">{dev.sensor_name}</span>
                      <span className="badge" style={{ backgroundColor: getSeverityColor(dev.severity) + '20', color: getSeverityColor(dev.severity) }}>
                        {dev.deviation_type}
                      </span>
                    </div>
                    <div className="severity-bar">
                      <div
                        className="severity-fill"
                        style={{
                          width: `${dev.severity * 100}%`,
                          backgroundColor: getSeverityColor(dev.severity),
                        }}
                      />
                    </div>
                    <div className="deviation-severity">
                      Severity: {(dev.severity * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.deviations_from_previous.length > 0 && (
            <div className="card">
              <h2>Deviations from Previous Cycle</h2>
              <div className="deviations-list">
                {analysis.deviations_from_previous.map((dev, idx) => (
                  <div key={idx} className="deviation-item">
                    <div className="deviation-header">
                      <span className="sensor-name">{dev.sensor_name}</span>
                      <span className="badge" style={{ backgroundColor: getSeverityColor(dev.severity) + '20', color: getSeverityColor(dev.severity) }}>
                        {dev.deviation_type}
                      </span>
                    </div>
                    <div className="severity-bar">
                      <div
                        className="severity-fill"
                        style={{
                          width: `${dev.severity * 100}%`,
                          backgroundColor: getSeverityColor(dev.severity),
                        }}
                      />
                    </div>
                    <div className="deviation-severity">
                      Severity: {(dev.severity * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.recommendations.length > 0 && (
            <div className="card">
              <h2>Recommendations</h2>
              <ul className="recommendations-list">
                {analysis.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Analysis;
