import client from './client'
import type {
  DashboardMetrics,
  Invoice,
  InvoiceDetail,
  Payment,
  CreatePaymentRequest,
  PaginatedResponse,
  Owner,
  LedgerEntry,
} from '../types/api'

export const accountingApi = {
  // Dashboard
  getDashboard: async (): Promise<DashboardMetrics> => {
    const response = await client.get<DashboardMetrics>('/api/v1/accounting/reports/dashboard/')
    return response.data
  },

  // Invoices
  getInvoices: async (params?: {
    status?: string
    page?: number
    search?: string
  }): Promise<PaginatedResponse<Invoice>> => {
    const response = await client.get<PaginatedResponse<Invoice>>(
      '/api/v1/accounting/invoices/',
      { params }
    )
    return response.data
  },

  getInvoice: async (id: string): Promise<InvoiceDetail> => {
    const response = await client.get<InvoiceDetail>(`/api/v1/accounting/invoices/${id}/`)
    return response.data
  },

  // Payments
  getPayments: async (params?: {
    page?: number
    owner?: string
  }): Promise<PaginatedResponse<Payment>> => {
    const response = await client.get<PaginatedResponse<Payment>>(
      '/api/v1/accounting/payments/',
      { params }
    )
    return response.data
  },

  createPayment: async (data: CreatePaymentRequest): Promise<Payment> => {
    const response = await client.post<Payment>('/api/v1/accounting/payments/', data)
    return response.data
  },

  // Owners
  getOwners: async (): Promise<Owner[]> => {
    const response = await client.get<PaginatedResponse<Owner>>('/api/v1/accounting/owners/')
    return response.data.results
  },

  getOwner: async (id: string): Promise<Owner> => {
    const response = await client.get<Owner>(`/api/v1/accounting/owners/${id}/`)
    return response.data
  },

  // Ledger
  getOwnerLedger: async (ownerId: string): Promise<LedgerEntry[]> => {
    const response = await client.get<LedgerEntry[]>(
      `/api/v1/accounting/owners/${ownerId}/ledger/`
    )
    return response.data
  },
}
