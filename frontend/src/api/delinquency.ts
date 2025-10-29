/**
 * API client for delinquency and collections management
 */

import apiClient from './apiClient';

// ===========================
// Types
// ===========================

export interface LateFeeRule {
  id: string;
  name: string;
  grace_period_days: number;
  fee_type: 'flat' | 'percentage' | 'both';
  fee_type_display: string;
  flat_amount: string;
  percentage_rate: string;
  max_amount: string | null;
  is_recurring: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DelinquencyStatus {
  id: string;
  owner: string;
  owner_name: string;
  current_balance: string;
  balance_0_30: string;
  balance_31_60: string;
  balance_61_90: string;
  balance_90_plus: string;
  collection_stage: string;
  stage_display: string;
  days_delinquent: number;
  last_payment_date: string | null;
  last_notice_date: string | null;
  is_payment_plan: boolean;
  notes: string;
  updated_at: string;
}

export interface CollectionNotice {
  id: string;
  owner: string;
  owner_name: string;
  notice_type: string;
  notice_type_display: string;
  delivery_method: string;
  method_display: string;
  sent_date: string;
  balance_at_notice: string;
  tracking_number: string;
  delivered_date: string | null;
  returned_undeliverable: boolean;
  notes: string;
  created_at: string;
}

export interface CollectionAction {
  id: string;
  owner: string;
  owner_name: string;
  action_type: string;
  action_type_display: string;
  status: string;
  status_display: string;
  requested_date: string;
  approved_date: string | null;
  approved_by: string;
  completed_date: string | null;
  balance_at_action: string;
  attorney_name: string;
  case_number: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface DelinquencySummary {
  total_delinquent: number;
  total_balance: string;
  by_stage: Record<string, { count: number; balance: string }>;
}

// ===========================
// API Functions
// ===========================

// Late Fee Rules
export const getLateFeeRules = async (): Promise<LateFeeRule[]> => {
  const response = await apiClient.get('/accounting/late-fee-rules/');
  return response.data;
};

export const createLateFeeRule = async (data: Partial<LateFeeRule>): Promise<LateFeeRule> => {
  const response = await apiClient.post('/accounting/late-fee-rules/', data);
  return response.data;
};

export const updateLateFeeRule = async (id: string, data: Partial<LateFeeRule>): Promise<LateFeeRule> => {
  const response = await apiClient.patch(`/accounting/late-fee-rules/${id}/`, data);
  return response.data;
};

export const deleteLateFeeRule = async (id: string): Promise<void> => {
  await apiClient.delete(`/accounting/late-fee-rules/${id}/`);
};

export const calculateLateFee = async (ruleId: string, balance: string): Promise<{ fee: string }> => {
  const response = await apiClient.post(`/accounting/late-fee-rules/${ruleId}/calculate_fee/`, { balance });
  return response.data;
};

// Delinquency Status
export const getDelinquencyStatuses = async (): Promise<DelinquencyStatus[]> => {
  const response = await apiClient.get('/accounting/delinquency-status/');
  return response.data;
};

export const getDelinquencyStatus = async (id: string): Promise<DelinquencyStatus> => {
  const response = await apiClient.get(`/accounting/delinquency-status/${id}/`);
  return response.data;
};

export const updateDelinquencyStatus = async (id: string, data: Partial<DelinquencyStatus>): Promise<DelinquencyStatus> => {
  const response = await apiClient.patch(`/accounting/delinquency-status/${id}/`, data);
  return response.data;
};

export const getDelinquencySummary = async (): Promise<DelinquencySummary> => {
  const response = await apiClient.get('/accounting/delinquency-status/summary/');
  return response.data;
};

// Collection Notices
export const getCollectionNotices = async (): Promise<CollectionNotice[]> => {
  const response = await apiClient.get('/accounting/collection-notices/');
  return response.data;
};

export const createCollectionNotice = async (data: Partial<CollectionNotice>): Promise<CollectionNotice> => {
  const response = await apiClient.post('/accounting/collection-notices/', data);
  return response.data;
};

export const updateCollectionNotice = async (id: string, data: Partial<CollectionNotice>): Promise<CollectionNotice> => {
  const response = await apiClient.patch(`/accounting/collection-notices/${id}/`, data);
  return response.data;
};

// Collection Actions
export const getCollectionActions = async (): Promise<CollectionAction[]> => {
  const response = await apiClient.get('/accounting/collection-actions/');
  return response.data;
};

export const createCollectionAction = async (data: Partial<CollectionAction>): Promise<CollectionAction> => {
  const response = await apiClient.post('/accounting/collection-actions/', data);
  return response.data;
};

export const approveCollectionAction = async (id: string, approvedBy: string): Promise<CollectionAction> => {
  const response = await apiClient.post(`/accounting/collection-actions/${id}/approve/`, { approved_by: approvedBy });
  return response.data;
};

export const updateCollectionAction = async (id: string, data: Partial<CollectionAction>): Promise<CollectionAction> => {
  const response = await apiClient.patch(`/accounting/collection-actions/${id}/`, data);
  return response.data;
};
