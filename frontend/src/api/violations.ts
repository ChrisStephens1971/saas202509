/**
 * API client for violation tracking
 */

import apiClient from './apiClient';

export interface Violation {
  id: string;
  owner: string;
  owner_name: string;
  property_address: string;
  violation_type: string;
  severity: string;
  severity_display: string;
  status: string;
  status_display: string;
  reported_date: string;
  first_notice_date: string | null;
  compliance_date: string | null;
  fine_amount: string;
  is_paid: boolean;
  description: string;
  resolution_notes: string;
  photos: ViolationPhoto[];
  notices: ViolationNotice[];
  hearings: ViolationHearing[];
  created_at: string;
}

export interface ViolationPhoto {
  id: string;
  photo_url: string;
  caption: string;
  taken_date: string;
}

export interface ViolationNotice {
  id: string;
  notice_type: string;
  notice_type_display: string;
  sent_date: string;
  cure_deadline: string;
}

export interface ViolationHearing {
  id: string;
  scheduled_date: string;
  scheduled_time: string;
  outcome: string;
  outcome_display: string;
  fine_assessed: string;
}

export const getViolations = async (): Promise<Violation[]> => {
  const response = await apiClient.get('/accounting/violations/');
  return response.data;
};

export const createViolation = async (data: Partial<Violation>): Promise<Violation> => {
  const response = await apiClient.post('/accounting/violations/', data);
  return response.data;
};

export const updateViolation = async (id: string, data: Partial<Violation>): Promise<Violation> => {
  const response = await apiClient.patch(`/accounting/violations/${id}/`, data);
  return response.data;
};
