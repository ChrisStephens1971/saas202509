import client from './client'
import type {
  Budget,
  CreateBudgetRequest,
  BudgetVarianceReport,
  PaginatedResponse,
  Fund,
  Account,
} from '../types/api'

export const budgetsApi = {
  // Budgets
  getBudgets: async (params?: {
    fiscal_year?: number
    fund?: string
    status?: string
    page?: number
  }): Promise<PaginatedResponse<Budget>> => {
    const response = await client.get<PaginatedResponse<Budget>>(
      '/api/v1/accounting/budgets/',
      { params }
    )
    return response.data
  },

  getBudget: async (id: string): Promise<Budget> => {
    const response = await client.get<Budget>(`/api/v1/accounting/budgets/${id}/`)
    return response.data
  },

  createBudget: async (data: CreateBudgetRequest): Promise<Budget> => {
    const response = await client.post<Budget>('/api/v1/accounting/budgets/', data)
    return response.data
  },

  updateBudget: async (id: string, data: Partial<CreateBudgetRequest>): Promise<Budget> => {
    const response = await client.put<Budget>(`/api/v1/accounting/budgets/${id}/`, data)
    return response.data
  },

  deleteBudget: async (id: string): Promise<void> => {
    await client.delete(`/api/v1/accounting/budgets/${id}/`)
  },

  // Budget actions
  approveBudget: async (id: string): Promise<Budget> => {
    const response = await client.post<Budget>(`/api/v1/accounting/budgets/${id}/approve/`)
    return response.data
  },

  activateBudget: async (id: string): Promise<Budget> => {
    const response = await client.post<Budget>(`/api/v1/accounting/budgets/${id}/activate/`)
    return response.data
  },

  // Variance report
  getVarianceReport: async (
    id: string,
    params?: {
      start_date?: string
      end_date?: string
    }
  ): Promise<BudgetVarianceReport> => {
    const response = await client.get<BudgetVarianceReport>(
      `/api/v1/accounting/budgets/${id}/variance-report/`,
      { params }
    )
    return response.data
  },

  // Helper endpoints
  getFunds: async (): Promise<Fund[]> => {
    const response = await client.get<PaginatedResponse<Fund>>('/api/v1/accounting/funds/')
    return response.data.results
  },

  getAccounts: async (params?: {
    account_type?: string
  }): Promise<Account[]> => {
    const response = await client.get<PaginatedResponse<Account>>(
      '/api/v1/accounting/accounts/',
      { params }
    )
    return response.data.results
  },
}
