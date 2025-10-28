/**
 * Dashboard API client for financial metrics and summaries.
 */

import client from './client'

export interface CashPositionResponse {
  total_cash: string
  funds: Array<{
    name: string
    balance: string
    trend: number
  }>
}

export interface ARAgingResponse {
  total_ar: string
  average_days: number
  buckets: {
    current: {
      amount: string
      percentage: number
      count: number
    }
    days_30_60: {
      amount: string
      percentage: number
      count: number
    }
    days_60_90: {
      amount: string
      percentage: number
      count: number
    }
    days_over_90: {
      amount: string
      percentage: number
      count: number
    }
  }
}

export interface ExpenseRevenueResponse {
  period: 'mtd' | 'ytd'
  total: string
  comparison: {
    previous_period: string
    change_pct: number
  }
  top_categories?: Array<{
    category: string
    amount: string
  }>
}

export interface RevenueVsExpensesResponse {
  months: Array<{
    month: string
    revenue: string
    expenses: string
  }>
}

export interface RecentActivityResponse {
  activities: Array<{
    type: 'invoice' | 'payment'
    description: string
    amount: string
    timestamp: string
  }>
}

export const dashboardApi = {
  /**
   * Get current cash balances across all funds with trend data.
   */
  getCashPosition: async (): Promise<CashPositionResponse> => {
    const response = await client.get<CashPositionResponse>(
      '/api/v1/accounting/dashboard/cash-position/'
    )
    return response.data
  },

  /**
   * Get AR aging buckets.
   */
  getARAging: async (): Promise<ARAgingResponse> => {
    const response = await client.get<ARAgingResponse>(
      '/api/v1/accounting/dashboard/ar-aging/'
    )
    return response.data
  },

  /**
   * Get expense summary (MTD/YTD).
   */
  getExpenses: async (period: 'mtd' | 'ytd' = 'mtd'): Promise<ExpenseRevenueResponse> => {
    const response = await client.get<ExpenseRevenueResponse>(
      '/api/v1/accounting/dashboard/expenses/',
      { params: { period } }
    )
    return response.data
  },

  /**
   * Get revenue summary (MTD/YTD).
   */
  getRevenue: async (period: 'mtd' | 'ytd' = 'mtd'): Promise<ExpenseRevenueResponse> => {
    const response = await client.get<ExpenseRevenueResponse>(
      '/api/v1/accounting/dashboard/revenue/',
      { params: { period } }
    )
    return response.data
  },

  /**
   * Get monthly revenue vs expenses for charting (last 12 months).
   */
  getRevenueVsExpenses: async (): Promise<RevenueVsExpensesResponse> => {
    const response = await client.get<RevenueVsExpensesResponse>(
      '/api/v1/accounting/dashboard/revenue-vs-expenses/'
    )
    return response.data
  },

  /**
   * Get recent activity log (last 20 events).
   */
  getRecentActivity: async (limit: number = 20): Promise<RecentActivityResponse> => {
    const response = await client.get<RecentActivityResponse>(
      '/api/v1/accounting/dashboard/recent-activity/',
      { params: { limit } }
    )
    return response.data
  },
}
