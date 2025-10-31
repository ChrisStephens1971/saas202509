/**
 * API client for Auditor Exports
 * Sprint 21 - Auditor Export
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8009/api/v1';

export interface AuditorExport {
  id: string;
  tenant: string;
  title: string;
  start_date: string;
  end_date: string;
  format: 'csv' | 'excel' | 'pdf';
  format_display: string;
  include_evidence: boolean;
  include_balances: boolean;
  include_owner_data: boolean;
  file_url?: string;
  file_size_bytes: number;
  file_hash?: string;
  generated_at: string;
  generated_by: string;
  generated_by_name?: string;
  status: 'generating' | 'ready' | 'failed';
  status_display: string;
  downloaded_count: number;
  last_downloaded_at?: string;
  total_entries: number;
  total_debit: string;
  total_credit: string;
  evidence_count: number;
  evidence_percentage: number;
  is_balanced: boolean;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAuditorExportRequest {
  title: string;
  start_date: string;
  end_date: string;
  format?: 'csv' | 'excel' | 'pdf';
  include_evidence?: boolean;
  include_balances?: boolean;
  include_owner_data?: boolean;
}

export interface GenerateExportResponse {
  status: 'success' | 'error';
  message: string;
  export: AuditorExport;
}

export interface VerifyIntegrityResponse {
  status: 'valid' | 'invalid';
  message: string;
  details?: {
    total_entries: number;
    total_debit: string;
    total_credit: string;
    balanced: boolean;
    file_hash: string;
    evidence_percentage: number;
  };
  error?: string;
}

/**
 * Get all auditor exports for the tenant
 */
export const getAuditorExports = async (): Promise<AuditorExport[]> => {
  const response = await axios.get(`${API_BASE_URL}/accounting/auditor-exports/`);
  return response.data;
};

/**
 * Get a single auditor export by ID
 */
export const getAuditorExport = async (id: string): Promise<AuditorExport> => {
  const response = await axios.get(`${API_BASE_URL}/accounting/auditor-exports/${id}/`);
  return response.data;
};

/**
 * Create a new auditor export
 */
export const createAuditorExport = async (
  data: CreateAuditorExportRequest
): Promise<AuditorExport> => {
  const response = await axios.post(`${API_BASE_URL}/accounting/auditor-exports/`, data);
  return response.data;
};

/**
 * Update an existing auditor export
 */
export const updateAuditorExport = async (
  id: string,
  data: Partial<CreateAuditorExportRequest>
): Promise<AuditorExport> => {
  const response = await axios.put(`${API_BASE_URL}/accounting/auditor-exports/${id}/`, data);
  return response.data;
};

/**
 * Delete an auditor export
 */
export const deleteAuditorExport = async (id: string): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/accounting/auditor-exports/${id}/`);
};

/**
 * Generate export file (CSV/Excel/PDF)
 */
export const generateExport = async (id: string): Promise<GenerateExportResponse> => {
  const response = await axios.post(
    `${API_BASE_URL}/accounting/auditor-exports/${id}/generate/`
  );
  return response.data;
};

/**
 * Download generated export file
 */
export const downloadExport = async (id: string, filename?: string): Promise<void> => {
  const response = await axios.get(
    `${API_BASE_URL}/accounting/auditor-exports/${id}/download/`,
    {
      responseType: 'blob',
    }
  );

  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename || 'auditor_export.csv');
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Verify export file integrity
 */
export const verifyIntegrity = async (id: string): Promise<VerifyIntegrityResponse> => {
  const response = await axios.get(
    `${API_BASE_URL}/accounting/auditor-exports/${id}/verify_integrity/`
  );
  return response.data;
};
