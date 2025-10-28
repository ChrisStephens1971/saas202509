// API response types

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
}

export interface TokenRefreshRequest {
  refresh: string
}

export interface TokenRefreshResponse {
  access: string
}

export interface DashboardMetrics {
  total_ar: string
  overdue_ar: string
  current_ar: string
  ar_aging: {
    current: string
    days_30: string
    days_60: string
    days_90: string
    days_over_90: string
  }
  recent_invoices: Invoice[]
  recent_payments: Payment[]
}

export interface InvoiceLine {
  line_number: number
  description: string
  account_number: string
  account_name: string
  amount: string
}

export interface Invoice {
  id: string
  invoice_number: string
  owner: Owner
  invoice_date: string
  due_date: string
  total_amount: string
  balance: string
  status: 'DRAFT' | 'ISSUED' | 'OVERDUE' | 'PAID' | 'VOID'
  description: string
}

export interface InvoiceDetail extends Invoice {
  owner_name: string
  unit_number: string
  invoice_type: string
  subtotal: string
  late_fee: string
  amount_paid: string
  amount_due: string
  days_overdue: number
  aging_bucket: string
  lines: InvoiceLine[]
}

export interface Owner {
  id: string
  first_name: string
  last_name: string
  email: string
  phone: string
  owner_number: string
  ar_balance: string
}

export interface Payment {
  id: string
  payment_number: string
  owner: Owner
  payment_date: string
  amount: string
  payment_method: 'CASH' | 'CHECK' | 'ACH' | 'CREDIT_CARD' | 'WIRE'
  reference_number: string
  memo: string
}

export interface CreatePaymentRequest {
  owner: string
  payment_date: string
  amount: string
  payment_method: string
  reference_number?: string
  memo?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiError {
  detail?: string
  [key: string]: any
}

export interface LedgerEntry {
  date: string
  type: 'invoice' | 'payment'
  reference_number: string
  description: string
  debit: string
  credit: string
  balance: string
}

// Budget types
export interface Fund {
  id: string
  name: string
  fund_type: 'operating' | 'reserve' | 'special_assessment'
  current_balance: string
}

export interface Account {
  id: string
  account_number: string
  account_name: string
  account_type: {
    code: string
    name: string
    normal_balance: 'debit' | 'credit'
  }
  balance: string
}

export interface BudgetLine {
  id?: string
  account: string | Account
  budgeted_amount: string
  notes?: string
}

export interface Budget {
  id: string
  name: string
  fiscal_year: number
  start_date: string
  end_date: string
  fund: string | Fund
  status: 'draft' | 'approved' | 'active' | 'closed'
  approved_by?: string
  approved_at?: string
  notes?: string
  lines?: BudgetLine[]
  total_budgeted?: string
  created_at: string
  updated_at: string
}

export interface CreateBudgetRequest {
  name: string
  fiscal_year: number
  start_date: string
  end_date: string
  fund: string
  status?: 'draft' | 'approved'
  notes?: string
  lines: Array<{
    account: string
    budgeted_amount: string
    notes?: string
  }>
}

export interface VarianceLine {
  account: string
  account_number: string
  account_name: string
  budgeted: string
  actual: string
  variance: string
  variance_pct: string
  status: 'favorable' | 'unfavorable' | 'neutral'
}

export interface BudgetVarianceReport {
  budget_id: string
  budget_name: string
  fiscal_year: number
  period: string
  fund_name: string
  lines: VarianceLine[]
  totals: {
    budgeted: string
    actual: string
    variance: string
    variance_pct: string
  }
}

// Bank Reconciliation Types
export interface BankStatement {
  id: string
  fund: string | Fund
  fund_name?: string
  statement_date: string
  beginning_balance: string
  ending_balance: string
  file_name: string
  uploaded_at: string
  uploaded_by?: string
  uploaded_by_name?: string
  reconciled: boolean
  reconciled_at?: string | null
  notes: string
  matched_count?: number
  unmatched_count?: number
  total_deposits?: string
  total_withdrawals?: string
  calculated_balance?: string
}

export interface BankTransaction {
  id: string
  statement: string
  statement_date?: string
  transaction_date: string
  post_date?: string | null
  description: string
  amount: string
  check_number: string
  reference_number: string
  status: 'unmatched' | 'matched' | 'ignored' | 'created'
  matched_entry?: string | null
  matched_entry_description?: string | null
  match_confidence: number
  notes: string
}

export interface MatchSuggestion {
  journal_entry: JournalEntry
  confidence: number
  reason: string
}

export interface ReconciliationReport {
  statement: BankStatement
  beginning_balance: string
  total_deposits: string
  total_withdrawals: string
  ending_balance: string
  calculated_balance: string
  difference: string
  matched_count: number
  unmatched_count: number
  ignored_count: number
  transactions: BankTransaction[]
}

export interface UploadStatementRequest {
  file: File
  fund: string
  statement_date: string
  beginning_balance: string
  ending_balance: string
}

export interface MatchTransactionRequest {
  transaction_id: string
  entry_id: string
  notes?: string
}

export interface CreateFromTransactionRequest {
  transaction_id: string
  account_id: string
  description?: string
}
