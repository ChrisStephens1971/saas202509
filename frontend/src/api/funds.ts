import apiClient from './client'
import type { Fund } from '../types/api'

export interface CreateFundRequest {
  name: string
  fund_type: 'OPERATING' | 'RESERVE' | 'SPECIAL_ASSESSMENT'
  description?: string
  is_active?: boolean
}

export interface UpdateFundRequest {
  name?: string
  fund_type?: 'OPERATING' | 'RESERVE' | 'SPECIAL_ASSESSMENT'
  description?: string
  is_active?: boolean
}

export interface FundsListResponse {
  count: number
  results: Fund[]
}

export const fundsApi = {
  /**
   * List all funds with optional filters
   */
  async getFunds(params?: {
    fund_type?: string
    is_active?: boolean
    search?: string
    ordering?: string
  }): Promise<FundsListResponse> {
    const response = await apiClient.get('/api/v1/accounting/funds/', { params })
    return response.data
  },

  /**
   * Get a single fund by ID
   */
  async getFund(id: string): Promise<Fund> {
    const response = await apiClient.get(`/api/v1/accounting/funds/${id}/`)
    return response.data
  },

  /**
   * Create a new fund
   */
  async createFund(data: CreateFundRequest): Promise<Fund> {
    const response = await apiClient.post('/api/v1/accounting/funds/', data)
    return response.data
  },

  /**
   * Update an existing fund
   */
  async updateFund(id: string, data: UpdateFundRequest): Promise<Fund> {
    const response = await apiClient.patch(`/api/v1/accounting/funds/${id}/`, data)
    return response.data
  },

  /**
   * Delete a fund
   */
  async deleteFund(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/accounting/funds/${id}/`)
  },
}
