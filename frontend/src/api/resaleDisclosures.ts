/**
 * API client for Resale Disclosure Packages
 * Sprint 22 - Resale Disclosure Packages
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8009/api/v1';

export interface ResaleDisclosure {
  id: string;
  tenant: string;
  unit: string;
  unit_number: string;
  owner: string;
  owner_name: string;
  requested_by: string;
  requested_by_name: string;
  requested_at: string;
  buyer_name: string;
  escrow_agent: string;
  escrow_company: string;
  contact_email: string;
  contact_phone: string;
  state: string;
  state_display_name: string;
  template_version: string;
  status: 'requested' | 'generating' | 'ready' | 'delivered' | 'failed';
  status_display: string;
  pdf_url?: string;
  pdf_size_bytes: number;
  pdf_hash?: string;
  page_count: number;
  generated_at?: string;
  delivered_at?: string;
  current_balance: string;
  monthly_dues: string;
  special_assessments: string;
  has_lien: boolean;
  has_violations: boolean;
  violation_count: number;
  fee_amount: string;
  invoice?: string;
  payment_status: string;
  notes?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateResaleDisclosureRequest {
  unit: string;
  owner: string;
  buyer_name?: string;
  escrow_agent?: string;
  escrow_company?: string;
  contact_email: string;
  contact_phone?: string;
  state: string;
  notes?: string;
}

export interface GenerateDisclosureResponse {
  status: 'success' | 'error';
  message: string;
  disclosure: ResaleDisclosure;
}

export interface DeliverDisclosureRequest {
  email_addresses?: string[];
  message?: string;
}

/**
 * Get all resale disclosures for the tenant
 */
export const getResaleDisclosures = async (): Promise<ResaleDisclosure[]> => {
  const response = await axios.get(`${API_BASE_URL}/accounting/resale-disclosures/`);
  return response.data;
};

/**
 * Get a single resale disclosure by ID
 */
export const getResaleDisclosure = async (id: string): Promise<ResaleDisclosure> => {
  const response = await axios.get(`${API_BASE_URL}/accounting/resale-disclosures/${id}/`);
  return response.data;
};

/**
 * Create a new resale disclosure request
 */
export const createResaleDisclosure = async (
  data: CreateResaleDisclosureRequest
): Promise<ResaleDisclosure> => {
  const response = await axios.post(`${API_BASE_URL}/accounting/resale-disclosures/`, data);
  return response.data;
};

/**
 * Update an existing resale disclosure
 */
export const updateResaleDisclosure = async (
  id: string,
  data: Partial<CreateResaleDisclosureRequest>
): Promise<ResaleDisclosure> => {
  const response = await axios.put(`${API_BASE_URL}/accounting/resale-disclosures/${id}/`, data);
  return response.data;
};

/**
 * Delete a resale disclosure
 */
export const deleteResaleDisclosure = async (id: string): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/accounting/resale-disclosures/${id}/`);
};

/**
 * Generate disclosure PDF package
 */
export const generateDisclosure = async (id: string): Promise<GenerateDisclosureResponse> => {
  const response = await axios.post(
    `${API_BASE_URL}/accounting/resale-disclosures/${id}/generate/`
  );
  return response.data;
};

/**
 * Download generated disclosure PDF
 */
export const downloadDisclosure = async (id: string, filename?: string): Promise<void> => {
  const response = await axios.get(
    `${API_BASE_URL}/accounting/resale-disclosures/${id}/download/`,
    {
      responseType: 'blob',
    }
  );

  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename || 'resale_disclosure.pdf');
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Mark disclosure as delivered and send email
 */
export const deliverDisclosure = async (
  id: string,
  data: DeliverDisclosureRequest
): Promise<GenerateDisclosureResponse> => {
  const response = await axios.post(
    `${API_BASE_URL}/accounting/resale-disclosures/${id}/deliver/`,
    data
  );
  return response.data;
};

/**
 * Create invoice for disclosure fee
 */
export const billDisclosure = async (id: string): Promise<any> => {
  const response = await axios.post(
    `${API_BASE_URL}/accounting/resale-disclosures/${id}/bill/`
  );
  return response.data;
};
