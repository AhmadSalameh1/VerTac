import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listDatasets, uploadDataset, deleteDataset, Dataset } from '../services/api';
import './DatasetList.css';

const DatasetList: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const navigate = useNavigate();

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

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const file = formData.get('file') as File;
    const name = formData.get('name') as string;
    const description = formData.get('description') as string;

    if (!file) {
      setError('Please select a file');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      await uploadDataset(file, name || undefined, description || undefined);
      setShowUploadForm(false);
      loadDatasets();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      await deleteDataset(id);
      loadDatasets();
    } catch (err: any) {
      setError(err.message || 'Failed to delete dataset');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="dataset-list-page">
      <div className="page-header">
        <div>
          <h1>Datasets</h1>
          <p className="subtitle">Manage your uploaded sensor datasets</p>
        </div>
        <button className="primary" onClick={() => setShowUploadForm(!showUploadForm)}>
          {showUploadForm ? 'Cancel' : '+ Upload Dataset'}
        </button>
      </div>

      {showUploadForm && (
        <div className="card upload-form">
          <h2>Upload New Dataset</h2>
          <form onSubmit={handleUpload}>
            <div className="form-group">
              <label>Dataset Name (optional)</label>
              <input type="text" name="name" placeholder="My Dataset" />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <textarea name="description" rows={3} placeholder="Description of this dataset..." />
            </div>
            <div className="form-group">
              <label>
                File <span className="required">*</span>
              </label>
              <input
                type="file"
                name="file"
                accept=".csv,.xlsx,.xls,.parquet"
                required
              />
              <small>Supported formats: CSV, Excel, Parquet</small>
            </div>
            {error && <div className="error">{error}</div>}
            <div className="form-actions">
              <button type="submit" className="primary" disabled={uploading}>
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => setShowUploadForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading && <div className="loading">Loading datasets...</div>}
        {!loading && error && !showUploadForm && <div className="error">{error}</div>}
        {!loading && !error && datasets.length === 0 && (
          <div className="empty-state">
            <p>No datasets uploaded yet</p>
            <p>Upload your first dataset to get started with cycle analysis</p>
          </div>
        )}
        {!loading && !error && datasets.length > 0 && (
          <div className="dataset-table">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Cycles</th>
                  <th>Format</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>
                      <div className="dataset-name">
                        <strong>{dataset.name}</strong>
                        {dataset.description && (
                          <small className="dataset-description">{dataset.description}</small>
                        )}
                      </div>
                    </td>
                    <td>{dataset.total_cycles}</td>
                    <td>
                      <span className="badge info">{dataset.file_format.toUpperCase()}</span>
                    </td>
                    <td>{formatFileSize(dataset.file_size)}</td>
                    <td>{new Date(dataset.upload_date).toLocaleDateString()}</td>
                    <td>
                      <div className="action-buttons-inline">
                        <button
                          className="primary small"
                          onClick={() => navigate(`/cycles/${dataset.id}`)}
                        >
                          View Cycles
                        </button>
                        <button
                          className="danger small"
                          onClick={() => handleDelete(dataset.id, dataset.name)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DatasetList;
