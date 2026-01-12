import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './PostCycleAnalysis.css';

interface SensorDeviation {
  sensor_id: string;
  sensor_name: string;
  euclidean_distance: number;
  dtw_distance: number;
  max_deviation: number;
  mean_deviation: number;
  contribution_rank: number;
  severity: string;
}

interface AnalysisAlert {
  sensor_id: string;
  sensor_name: string;
  severity: string;
  message: string;
  euclidean_distance: number;
  dtw_distance: number;
}

interface PostCycleAnalysisProps {
  cycleId?: string;
  analysisResult?: {
    overall_health_score: number;
    anomaly_flag: boolean;
    sensor_deviations: SensorDeviation[];
    top_3_problematic_sensors: Array<[string, number]>;
    alerts: AnalysisAlert[];
  };
}

export const PostCycleAnalysis: React.FC<PostCycleAnalysisProps> = ({
  cycleId: propCycleId,
  analysisResult: propAnalysisResult,
}) => {
  const { cycleId: urlCycleId } = useParams<{ cycleId: string }>();
  const cycleId = propCycleId || urlCycleId;
  const [analysisResult] = useState(propAnalysisResult);
  const [expandedSensor, setExpandedSensor] = useState<string | null>(null);

  // If no analysis result, show loading or error
  if (!analysisResult) {
    return (
      <div className="post-cycle-analysis">
        <h1>📊 Post-Cycle Analysis</h1>
        <div className="loading-message">
          <p>Analysis results not available yet.</p>
          <p>Cycle ID: {cycleId || 'Not specified'}</p>
        </div>
      </div>
    );
  }

  const healthColor = (score: number) => {
    if (score >= 90) return '#28a745'; // Green
    if (score >= 70) return '#ffc107'; // Yellow
    return '#dc3545'; // Red
  };

  const getRiskLevel = (score: number) => {
    if (score >= 90) return 'HEALTHY';
    if (score >= 70) return 'WARNING';
    return 'CRITICAL';
  };

  const chartData = analysisResult.sensor_deviations.map((d) => ({
    name: d.sensor_name,
    'Euclidean Distance': d.euclidean_distance,
    'DTW Distance': d.dtw_distance / 10, // Scale for visibility
    'Contribution Rank': d.contribution_rank,
  }));

  return (
    <div className="post-cycle-analysis">
      <div className="analysis-header">
        <h1>📊 Post-Cycle Analysis Report</h1>
        <p className="cycle-id">Cycle ID: {cycleId?.substring(0, 8)}</p>
      </div>

      {/* Health Score Card */}
      <div className="health-score-card">
        <div className="score-gauge">
          <svg viewBox="0 0 200 200" className="gauge-svg">
            <circle cx="100" cy="100" r="90" className="gauge-background" />
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke={healthColor(analysisResult.overall_health_score)}
              strokeWidth="20"
              strokeDasharray={`${(analysisResult.overall_health_score / 100) * 2 * Math.PI * 80} 999`}
              className="gauge-progress"
            />
            <text
              x="100"
              y="110"
              textAnchor="middle"
              fontSize="48"
              fontWeight="bold"
              fill={healthColor(analysisResult.overall_health_score)}
            >
              {analysisResult.overall_health_score.toFixed(0)}
            </text>
            <text
              x="100"
              y="140"
              textAnchor="middle"
              fontSize="14"
              fill="#666"
            >
              Health Score
            </text>
          </svg>
        </div>

        <div className="score-details">
          <div className="detail-item">
            <span className="label">Status:</span>
            <span
              className="badge"
              style={{ background: healthColor(analysisResult.overall_health_score), color: 'white' }}
            >
              {getRiskLevel(analysisResult.overall_health_score)}
            </span>
          </div>
          <div className="detail-item">
            <span className="label">Anomaly Detected:</span>
            <span className={analysisResult.anomaly_flag ? 'badge danger' : 'badge success'}>
              {analysisResult.anomaly_flag ? '⚠️ YES' : '✅ NO'}
            </span>
          </div>
          <div className="detail-item">
            <span className="label">Sensors Analyzed:</span>
            <span className="value">{analysisResult.sensor_deviations.length}</span>
          </div>
        </div>
      </div>

      {/* Top 3 Problematic Sensors */}
      <div className="top-sensors-section">
        <h2>🔴 Top Problematic Sensors</h2>
        <div className="sensors-ranking">
          {analysisResult.top_3_problematic_sensors.map((sensor, idx) => (
            <div key={idx} className={`ranking-item rank-${idx + 1}`}>
              <div className="rank-badge">#{idx + 1}</div>
              <div className="rank-info">
                <div className="sensor-name">{sensor[0]}</div>
                <div className="deviation-score">Score: {sensor[1].toFixed(4)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Deviation Chart */}
      <div className="charts-section">
        <h2>📈 Sensor Deviations</h2>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Euclidean Distance" fill="#667eea" />
              <Bar dataKey="DTW Distance" fill="#f093fb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Sensor Analysis */}
      <div className="detailed-sensors-section">
        <h2>🔍 Detailed Sensor Analysis</h2>
        <div className="sensors-list">
          {analysisResult.sensor_deviations.map((sensor) => (
            <div
              key={sensor.sensor_id}
              className={`sensor-detail-card ${sensor.severity}`}
            >
              <div
                className="sensor-header"
                onClick={() =>
                  setExpandedSensor(
                    expandedSensor === sensor.sensor_id ? null : sensor.sensor_id
                  )
                }
              >
                <div className="header-left">
                  <span className={`severity-badge ${sensor.severity}`}>
                    {sensor.severity.toUpperCase()}
                  </span>
                  <span className="sensor-name">{sensor.sensor_name}</span>
                  <span className="rank-badge">Rank #{sensor.contribution_rank}</span>
                </div>
                <div className="toggle-arrow">
                  {expandedSensor === sensor.sensor_id ? '▼' : '▶'}
                </div>
              </div>

              {expandedSensor === sensor.sensor_id && (
                <div className="sensor-details">
                  <div className="detail-grid">
                    <div className="detail">
                      <span className="label">Euclidean Distance:</span>
                      <span className="value">{sensor.euclidean_distance.toFixed(4)}</span>
                    </div>
                    <div className="detail">
                      <span className="label">DTW Distance:</span>
                      <span className="value">{sensor.dtw_distance.toFixed(4)}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Max Deviation:</span>
                      <span className="value">{sensor.max_deviation.toFixed(4)}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Mean Deviation:</span>
                      <span className="value">{sensor.mean_deviation.toFixed(4)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Alerts Summary */}
      {analysisResult.alerts.length > 0 && (
        <div className="alerts-summary">
          <h2>🚨 Alert Summary</h2>
          <div className="alerts-list">
            {analysisResult.alerts.map((alert, idx) => (
              <div key={idx} className={`alert-card ${alert.severity}`}>
                <div className="alert-icon">
                  {alert.severity === 'critical' ? '🔴' : '🟡'}
                </div>
                <div className="alert-content">
                  <div className="alert-title">{alert.message}</div>
                  <div className="alert-details">
                    <span className="detail">Sensor: {alert.sensor_name}</span>
                    <span className="detail">
                      Distance: {alert.euclidean_distance.toFixed(4)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="recommendations">
        <h2>💡 Recommendations</h2>
        <ul>
          {analysisResult.overall_health_score < 70 && (
            <>
              <li>⚠️ Cycle shows anomalies. Review sensor data carefully.</li>
              <li>📊 Check the top 3 problematic sensors for maintenance needs.</li>
              <li>🔧 Consider calibration or replacement of problematic sensors.</li>
            </>
          )}
          {analysisResult.overall_health_score >= 70 && analysisResult.overall_health_score < 90 && (
            <>
              <li>⚡ Some sensors show warning-level deviations.</li>
              <li>📍 Monitor the identified sensors in upcoming cycles.</li>
              <li>🛠️ Plan preventive maintenance for flagged sensors.</li>
            </>
          )}
          {analysisResult.overall_health_score >= 90 && (
            <>
              <li>✅ Cycle completed successfully with no significant issues.</li>
              <li>📈 System performance is within normal parameters.</li>
              <li>👍 Continue normal operation monitoring.</li>
            </>
          )}
        </ul>
      </div>

      {/* Export Options */}
      <div className="export-section">
        <h2>📥 Export Options</h2>
        <div className="export-buttons">
          <button className="btn btn-export">📄 Export as PDF</button>
          <button className="btn btn-export">📊 Export as CSV</button>
          <button className="btn btn-export">💾 Save to Database</button>
        </div>
      </div>
    </div>
  );
};

export default PostCycleAnalysis;
