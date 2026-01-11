import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listDatasets, Dataset } from '../services/api';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await listDatasets();
      setDatasets(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const totalCycles = datasets.reduce((sum, ds) => sum + ds.total_cycles, 0);
  const anomalousCycles = 0; // Would need to fetch from backend

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      <p className="subtitle">Monitor your factory cycles and detect anomalies</p>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{datasets.length}</div>
          <div className="stat-label">Total Datasets</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalCycles}</div>
          <div className="stat-label">Total Cycles</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{anomalousCycles}</div>
          <div className="stat-label">Anomalous Cycles</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {datasets.length > 0 ? Math.round((1 - anomalousCycles / totalCycles) * 100) : 0}%
          </div>
          <div className="stat-label">Health Score</div>
        </div>
      </div>

      <div className="card">
        <h2>Recent Datasets</h2>
        {loading && <div className="loading">Loading...</div>}
        {error && <div className="error">{error}</div>}
        {!loading && !error && datasets.length === 0 && (
          <div className="empty-state">
            <p>No datasets uploaded yet</p>
            <Link to="/datasets">
              <button className="primary">Upload Dataset</button>
            </Link>
          </div>
        )}
        {!loading && !error && datasets.length > 0 && (
          <div className="dataset-list">
            {datasets.slice(0, 5).map((dataset) => (
              <Link to={`/cycles/${dataset.id}`} key={dataset.id} className="dataset-item">
                <div>
                  <h3>{dataset.name}</h3>
                  <p className="dataset-meta">
                    {dataset.total_cycles} cycles • {dataset.file_format.toUpperCase()} •{' '}
                    {new Date(dataset.upload_date).toLocaleDateString()}
                  </p>
                </div>
                <span className="arrow">→</span>
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="quick-actions card">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <Link to="/datasets">
            <button className="primary">Upload Dataset</button>
          </Link>
          <Link to="/analysis">
            <button className="secondary">View Analysis</button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
