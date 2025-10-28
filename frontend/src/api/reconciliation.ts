import client from './client'
import type {
  BankStatement,
  BankTransaction,
  MatchSuggestion,
  ReconciliationReport,
  MatchTransactionRequest,
  CreateFromTransactionRequest,
  JournalEntry,
} from '../types/api'

export const reconciliationApi = {
  // Bank Statements
  uploadStatement: async (
    file: File,
    fundId: string,
    statementDate: string,
    beginningBalance: string,
    endingBalance: string
  ): Promise<{ statement: BankStatement; transactions_created: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('fund', fundId)
    formData.append('statement_date', statementDate)
    formData.append('beginning_balance', beginningBalance)
    formData.append('ending_balance', endingBalance)

    const response = await client.post<{ statement: BankStatement; transactions_created: number }>(
      '/api/v1/accounting/reconciliation/upload-statement/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  getStatements: async (params?: {
    fund?: string
    reconciled?: boolean
  }): Promise<BankStatement[]> => {
    const response = await client.get<BankStatement[]>(
      '/api/v1/accounting/reconciliation/statements/',
      { params }
    )
    return response.data
  },

  getStatementDetail: async (
    id: string
  ): Promise<{ statement: BankStatement; transactions: BankTransaction[] }> => {
    const response = await client.get<{
      statement: BankStatement
      transactions: BankTransaction[]
    }>(`/api/v1/accounting/reconciliation/${id}/statement-detail/`)
    return response.data
  },

  // Transactions
  getUnmatchedTransactions: async (params?: {
    statement?: string
  }): Promise<BankTransaction[]> => {
    const response = await client.get<BankTransaction[]>(
      '/api/v1/accounting/reconciliation/unmatched-transactions/',
      { params }
    )
    return response.data
  },

  // Matching
  suggestMatches: async (
    transactionId: string,
    maxSuggestions: number = 5
  ): Promise<MatchSuggestion[]> => {
    const response = await client.post<MatchSuggestion[]>(
      '/api/v1/accounting/reconciliation/suggest-matches/',
      {
        transaction_id: transactionId,
        max_suggestions: maxSuggestions,
      }
    )
    return response.data
  },

  matchTransaction: async (
    data: MatchTransactionRequest
  ): Promise<{ transaction: BankTransaction; message: string }> => {
    const response = await client.post<{
      transaction: BankTransaction
      message: string
    }>('/api/v1/accounting/reconciliation/match-transaction/', data)
    return response.data
  },

  unmatchTransaction: async (
    transactionId: string
  ): Promise<{ transaction: BankTransaction; message: string }> => {
    const response = await client.post<{
      transaction: BankTransaction
      message: string
    }>('/api/v1/accounting/reconciliation/unmatch-transaction/', {
      transaction_id: transactionId,
    })
    return response.data
  },

  ignoreTransaction: async (
    transactionId: string,
    notes?: string
  ): Promise<{ transaction: BankTransaction; message: string }> => {
    const response = await client.post<{
      transaction: BankTransaction
      message: string
    }>('/api/v1/accounting/reconciliation/ignore-transaction/', {
      transaction_id: transactionId,
      notes: notes || '',
    })
    return response.data
  },

  createFromTransaction: async (
    data: CreateFromTransactionRequest
  ): Promise<{
    entry: JournalEntry
    transaction: BankTransaction
    message: string
  }> => {
    const response = await client.post<{
      entry: JournalEntry
      transaction: BankTransaction
      message: string
    }>('/api/v1/accounting/reconciliation/create-from-transaction/', data)
    return response.data
  },

  // Reporting
  getReconciliationReport: async (
    statementId: string
  ): Promise<ReconciliationReport> => {
    const response = await client.get<ReconciliationReport>(
      `/api/v1/accounting/reconciliation/${statementId}/reconciliation-report/`
    )
    return response.data
  },
}
