/**
 * API client for board packet generation
 */

import apiClient from './client';

export interface BoardPacket {
  id: string;
  template: string;
  template_name: string;
  meeting_date: string;
  status: string;
  status_display: string;
  pdf_url: string;
  page_count: number | null;
  generated_at: string | null;
  generated_by: string;
  sent_to: string[];
  sent_at: string | null;
  sections: PacketSection[];
  created_at: string;
}

export interface PacketSection {
  id: string;
  section_type: string;
  section_type_display: string;
  title: string;
  content_url: string;
  order: number;
  page_count: number | null;
}

export interface BoardPacketTemplate {
  id: string;
  name: string;
  description: string;
  sections: string[];
  is_default: boolean;
}

export const getBoardPackets = async (): Promise<BoardPacket[]> => {
  const response = await apiClient.get('/accounting/board-packets/');
  return response.data;
};

export const createBoardPacket = async (data: Partial<BoardPacket>): Promise<BoardPacket> => {
  const response = await apiClient.post('/accounting/board-packets/', data);
  return response.data;
};

export const generatePDF = async (id: string): Promise<any> => {
  const response = await apiClient.post(`/accounting/board-packets/${id}/generate_pdf/`);
  return response.data;
};

export const sendEmail = async (id: string, recipients: string[]): Promise<BoardPacket> => {
  const response = await apiClient.post(`/accounting/board-packets/${id}/send_email/`, { recipients });
  return response.data;
};

export const getTemplates = async (): Promise<BoardPacketTemplate[]> => {
  const response = await apiClient.get('/accounting/board-packet-templates/');
  return response.data;
};
