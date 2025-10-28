import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { budgetsApi } from '../api/budgets'
import type { Budget, Fund } from '../types/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Select } from '../components/ui/Select'
import { Skeleton } from '../components/ui/Skeleton'
import { formatCurrency, formatDate } from '../utils/formatters'

export const BudgetsPage: React.FC = () => {
  const navigate = useNavigate()
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [funds, setFunds] = useState<Fund[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [fiscalYear, setFiscalYear] = useState<string>('all')
  const [fundFilter, setFundFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [fiscalYear, fundFilter, statusFilter])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load funds for filter dropdown
      if (funds.length === 0) {
        const fundsData = await budgetsApi.getFunds()
        setFunds(fundsData)
      }

      // Load budgets with filters
      const params: any = {}
      if (fiscalYear !== 'all') params.fiscal_year = parseInt(fiscalYear)
      if (fundFilter !== 'all') params.fund = fundFilter
      if (statusFilter !== 'all') params.status = statusFilter

      const response = await budgetsApi.getBudgets(params)
      setBudgets(response.results)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load budgets')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this budget?')) return

    try {
      await budgetsApi.deleteBudget(id)
      await loadData()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete budget')
    }
  }

  const handleApprove = async (id: string) => {
    try {
      await budgetsApi.approveBudget(id)
      await loadData()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve budget')
    }
  }

  const handleActivate = async (id: string) => {
    try {
      await budgetsApi.activateBudget(id)
      await loadData()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to activate budget')
    }
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success'
      case 'approved':
        return 'info'
      case 'draft':
        return 'warning'
      case 'closed':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStatusLabel = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1)
  }

  // Generate fiscal year options (current year ± 5 years)
  const currentYear = new Date().getFullYear()
  const fiscalYearOptions = [
    { value: 'all', label: 'All Years' },
    ...Array.from({ length: 11 }, (_, i) => {
      const year = currentYear - 5 + i
      return { value: year.toString(), label: `FY ${year}` }
    }),
  ]

  const fundOptions = [
    { value: 'all', label: 'All Funds' },
    ...funds.map((fund) => ({
      value: fund.id,
      label: fund.name,
    })),
  ]

  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'draft', label: 'Draft' },
    { value: 'approved', label: 'Approved' },
    { value: 'active', label: 'Active' },
    { value: 'closed', label: 'Closed' },
  ]

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Budgets</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage annual budgets and track variances
          </p>
        </div>
        <Button
          onClick={() => navigate('/budgets/new')}
          className="bg-blue-600 hover:bg-blue-700"
        >
          + New Budget
        </Button>
      </div>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Select
          value={fiscalYear}
          onChange={(e) => setFiscalYear(e.target.value)}
          options={fiscalYearOptions}
        />
        <Select
          value={fundFilter}
          onChange={(e) => setFundFilter(e.target.value)}
          options={fundOptions}
        />
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          options={statusOptions}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Budget List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : budgets.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900">No budgets found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new budget.
          </p>
          <Button
            onClick={() => navigate('/budgets/new')}
            className="mt-4 bg-blue-600 hover:bg-blue-700"
          >
            Create Budget
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {budgets.map((budget) => (
            <div
              key={budget.id}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {budget.name}
                    </h3>
                    <Badge variant={getStatusVariant(budget.status)}>
                      {getStatusLabel(budget.status)}
                    </Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm text-gray-600 sm:grid-cols-4">
                    <div>
                      <span className="font-medium">Fiscal Year:</span> {budget.fiscal_year}
                    </div>
                    <div>
                      <span className="font-medium">Fund:</span>{' '}
                      {typeof budget.fund === 'object' ? budget.fund.name : 'N/A'}
                    </div>
                    <div>
                      <span className="font-medium">Period:</span>{' '}
                      {formatDate(budget.start_date)} - {formatDate(budget.end_date)}
                    </div>
                    <div>
                      <span className="font-medium">Total:</span>{' '}
                      {budget.total_budgeted
                        ? formatCurrency(budget.total_budgeted)
                        : 'N/A'}
                    </div>
                  </div>
                  {budget.notes && (
                    <p className="mt-2 text-sm text-gray-500">{budget.notes}</p>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 flex gap-2">
                <Button
                  onClick={() => navigate(`/budgets/${budget.id}/variance`)}
                  variant="outline"
                  size="sm"
                >
                  View Report
                </Button>
                <Button
                  onClick={() => navigate(`/budgets/${budget.id}/edit`)}
                  variant="outline"
                  size="sm"
                >
                  Edit
                </Button>
                {budget.status === 'draft' && (
                  <Button
                    onClick={() => handleApprove(budget.id)}
                    variant="outline"
                    size="sm"
                    className="text-blue-600 hover:text-blue-700"
                  >
                    Approve
                  </Button>
                )}
                {budget.status === 'approved' && (
                  <Button
                    onClick={() => handleActivate(budget.id)}
                    variant="outline"
                    size="sm"
                    className="text-green-600 hover:text-green-700"
                  >
                    Activate
                  </Button>
                )}
                {budget.status === 'draft' && (
                  <Button
                    onClick={() => handleDelete(budget.id)}
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700"
                  >
                    Delete
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
