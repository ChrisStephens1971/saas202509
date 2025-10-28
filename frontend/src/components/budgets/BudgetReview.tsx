import React, { useState, useEffect } from 'react'
import { budgetsApi } from '../../api/budgets'
import type { Fund, Account } from '../../types/api'
import { Button } from '../ui/Button'
import { formatCurrency, formatDate } from '../../utils/formatters'
import { CheckCircle } from 'lucide-react'

interface BudgetReviewProps {
  data: {
    name: string
    fiscal_year: number
    start_date: string
    end_date: string
    fund: string
    notes: string
    status: 'draft' | 'approved'
    lines: Array<{
      account: string
      budgeted_amount: string
      notes?: string
    }>
  }
  onSubmit: () => void
  onBack: () => void
  loading: boolean
}

export const BudgetReview: React.FC<BudgetReviewProps> = ({
  data,
  onSubmit,
  onBack,
  loading,
}) => {
  const [funds, setFunds] = useState<Fund[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loadingData, setLoadingData] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [fundsData, accountsData] = await Promise.all([
        budgetsApi.getFunds(),
        budgetsApi.getAccounts(),
      ])
      setFunds(fundsData)
      setAccounts(accountsData)
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoadingData(false)
    }
  }

  const getFundName = () => {
    const fund = funds.find((f) => f.id === data.fund)
    return fund ? fund.name : 'Unknown Fund'
  }

  const getAccountName = (accountId: string) => {
    const account = accounts.find((a) => a.id === accountId)
    return account
      ? `${account.account_number} - ${account.account_name}`
      : accountId
  }

  const getTotalBudgeted = () => {
    return data.lines.reduce((sum, line) => {
      return sum + parseFloat(line.budgeted_amount || '0')
    }, 0)
  }

  if (loadingData) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Review & Submit
        </h2>
        <p className="text-sm text-gray-600 mb-6">
          Please review all budget details before submitting.
        </p>
      </div>

      {/* Budget Details Summary */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Budget Details</h3>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Budget Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{data.name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Fiscal Year</dt>
            <dd className="mt-1 text-sm text-gray-900">{data.fiscal_year}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Fund</dt>
            <dd className="mt-1 text-sm text-gray-900">{getFundName()}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Budget Period</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {formatDate(data.start_date)} - {formatDate(data.end_date)}
            </dd>
          </div>
          {data.notes && (
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-gray-500">Notes</dt>
              <dd className="mt-1 text-sm text-gray-900">{data.notes}</dd>
            </div>
          )}
        </dl>
      </div>

      {/* Budget Lines Summary */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Budget Lines ({data.lines.length} items)
        </h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Account
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Budgeted Amount
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Notes
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.lines.map((line, index) => (
                <tr key={index}>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {getAccountName(line.account)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                    {formatCurrency(line.budgeted_amount)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {line.notes || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                  Total Budgeted
                </td>
                <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right text-lg">
                  {formatCurrency(getTotalBudgeted())}
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Confirmation Message */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <div className="flex">
          <CheckCircle className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-900">
              Ready to submit
            </h4>
            <p className="mt-1 text-sm text-blue-700">
              This budget will be saved as a draft. You can activate it later from the
              budget list page.
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-6 border-t">
        <Button onClick={onBack} variant="outline" disabled={loading}>
          ← Back
        </Button>
        <Button onClick={onSubmit} disabled={loading}>
          {loading ? 'Creating Budget...' : 'Create Budget'}
        </Button>
      </div>
    </div>
  )
}
