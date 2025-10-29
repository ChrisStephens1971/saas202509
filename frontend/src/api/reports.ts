import axios from 'axios';

const API_BASE_URL = 'http://localhost:8009/api/v1/accounting';

// Get auth token from localStorage
const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Type definitions
export interface CustomReport {
  id: string;
  name: string;
  description: string;
  report_type: string;
  report_type_display: string;
  columns: string[];
  filters: Record<string, any>;
  sort_by: Array<{ field: string; direction: string }>;
  is_public: boolean;
  is_favorite: boolean;
  created_by: string;
  execution_count: number;
  created_at: string;
  updated_at: string;
}

export interface ReportExecution {
  id: string;
  report: string;
  report_name: string;
  executed_by: string;
  status: string;
  status_display: string;
  started_at: string;
  completed_at: string | null;
  row_count: number | null;
  execution_time_ms: number | null;
  error_message: string;
  result_cache: any;
  parameters: Record<string, any>;
  created_at: string;
}

export interface ReportExecutionResult {
  execution_id: string;
  status: string;
  row_count: number;
  execution_time_ms: number;
  data: any[];
}

// Custom Reports API
export const customReportsApi = {
  list: async (): Promise<CustomReport[]> => {
    const response = await axios.get(`${API_BASE_URL}/custom-reports/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  get: async (id: string): Promise<CustomReport> => {
    const response = await axios.get(`${API_BASE_URL}/custom-reports/${id}/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  create: async (data: Partial<CustomReport>): Promise<CustomReport> => {
    const response = await axios.post(`${API_BASE_URL}/custom-reports/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  update: async (id: string, data: Partial<CustomReport>): Promise<CustomReport> => {
    const response = await axios.put(`${API_BASE_URL}/custom-reports/${id}/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/custom-reports/${id}/`, {
      headers: getAuthHeader(),
    });
  },

  execute: async (id: string, parameters: Record<string, any>): Promise<ReportExecutionResult> => {
    const response = await axios.post(
      `${API_BASE_URL}/custom-reports/${id}/execute/`,
      { parameters },
      { headers: getAuthHeader() }
    );
    return response.data;
  },

  exportCSV: async (id: string): Promise<string> => {
    const response = await axios.get(`${API_BASE_URL}/custom-reports/${id}/export_csv/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },
};

// Report Executions API
export const reportExecutionsApi = {
  list: async (reportId?: string): Promise<ReportExecution[]> => {
    const params = reportId ? { report: reportId } : {};
    const response = await axios.get(`${API_BASE_URL}/report-executions/`, {
      headers: getAuthHeader(),
      params,
    });
    return response.data;
  },

  get: async (id: string): Promise<ReportExecution> => {
    const response = await axios.get(`${API_BASE_URL}/report-executions/${id}/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },
};
