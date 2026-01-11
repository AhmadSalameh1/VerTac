import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  file_format: string;
  file_size: number;
  upload_date: string;
  total_cycles: number;
  sensors?: string[];
}

export interface Cycle {
  id: number;
  dataset_id: number;
  cycle_number: number;
  start_time: number;
  end_time: number;
  duration: number;
  is_complete: boolean;
  is_reference: boolean;
  is_anomalous: boolean;
  anomaly_score?: number;
  created_at: string;
}

export interface SensorData {
  sensor_name: string;
  timestamps: number[];
  values: number[];
  unit?: string;
}

export interface CycleDetail extends Cycle {
  metadata?: any;
  sensor_data?: SensorData[];
}

export interface Deviation {
  sensor_name: string;
  deviation_type: string;
  severity: number;
  compared_to: string;
  time_start?: number;
  time_end?: number;
  details?: any;
}

export interface DeviationAnalysis {
  cycle_id: number;
  has_deviations: boolean;
  deviations_from_reference: Deviation[];
  deviations_from_previous: Deviation[];
  overall_health_score: number;
  recommendations: string[];
}

// Dataset APIs
export const uploadDataset = async (file: File, name?: string, description?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  if (description) formData.append('description', description);

  const response = await api.post('/datasets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const listDatasets = async (): Promise<Dataset[]> => {
  const response = await api.get('/datasets/');
  return response.data;
};

export const getDataset = async (datasetId: number): Promise<Dataset> => {
  const response = await api.get(`/datasets/${datasetId}`);
  return response.data;
};

export const deleteDataset = async (datasetId: number) => {
  const response = await api.delete(`/datasets/${datasetId}`);
  return response.data;
};

// Cycle APIs
export const listCycles = async (datasetId: number): Promise<Cycle[]> => {
  const response = await api.get(`/cycles/dataset/${datasetId}`);
  return response.data;
};

export const getCycle = async (cycleId: number, includeData: boolean = true): Promise<CycleDetail> => {
  const response = await api.get(`/cycles/${cycleId}?include_data=${includeData}`);
  return response.data;
};

export const setReferenceCycle = async (cycleId: number) => {
  const response = await api.post(`/cycles/${cycleId}/set-reference`);
  return response.data;
};

export const getCycleSensors = async (cycleId: number): Promise<string[]> => {
  const response = await api.get(`/cycles/${cycleId}/sensors`);
  return response.data.sensors;
};

// Analysis APIs
export const analyzeCycleDeviations = async (
  cycleId: number,
  compareToReference: boolean = true,
  compareToPrevious: boolean = true
): Promise<DeviationAnalysis> => {
  const response = await api.get(
    `/analysis/cycle/${cycleId}/deviations?compare_to_reference=${compareToReference}&compare_to_previous=${compareToPrevious}`
  );
  return response.data;
};

export const detectDatasetAnomalies = async (datasetId: number, threshold: number = 0.8) => {
  const response = await api.get(`/analysis/dataset/${datasetId}/anomalies?threshold=${threshold}`);
  return response.data;
};

export const analyzeRootCause = async (cycleId: number, timeWindowSeconds?: number) => {
  let url = `/analysis/cycle/${cycleId}/root-cause`;
  if (timeWindowSeconds) {
    url += `?time_window_seconds=${timeWindowSeconds}`;
  }
  const response = await api.get(url);
  return response.data;
};

export default api;
