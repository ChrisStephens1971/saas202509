import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { budgetsApi } from '../api/budgets'
import type { Budget, BudgetVarianceReport } from '../types/api'
import { Button } from '../components/ui/Button'
import { Skeleton } from '../components/ui/Skeleton'
import { formatCurrency } from '../utils/formatters'
import { VarianceChart } from '../components/budgets/VarianceChart'
import { ArrowLeft, Download, TrendingUp, TrendingDown } from 'lucide-react'

export const BudgetVariancePage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [budget, setBudget] = useState<Budget | null>(null)
  const [report, setReport] = useState<BudgetVarianceReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      loadData(id)
    }
  }, [id])

  const loadData = async (budgetId: string) => {
    try {
      setLoading(true)
      setError(null)

      const [budgetData, reportData] = await Promise.all([
        budgetsApi.getBudget(budgetId),
        budgetsApi.getVarianceReport(budgetId),
      ])

      setBudget(budgetData)
      setReport(reportData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load variance report')
    } finally {
      setLoading(false)
    }
  }

  const getVarianceIcon = (status: string) => {
    if (status === 'favorable') {
      return <TrendingUp className="w-4 h-4 text-green-600" />
    } else if (status === 'unfavorable') {
      return <TrendingDown className="w-4 h-4 text-red-600" />
    }
    return null
  }

  const getVarianceColor = (status: string) => {
    if (status === 'favorable') {
      return 'text-green-600'
    } else if (status === 'unfavorable') {
      return 'text-red-600'
    }
    return 'text-gray-600'
  }

  if (loading) {
    return (
      <Layout>
        <Skeleton className="h-8 w-64 mb-4" />
        <Skeleton className="h-64 w-full mb-4" />
        <Skeleton className="h-96 w-full" />
      </Layout>
    )
  }

  if (error || !budget || !report) {
    return (
      <Layout>
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error || 'Failed to load report'}</p>
        </div>
        <Button onClick={() => navigate('/budgets')} className="mt-4">
          Back to Budgets
        </Button>
      </Layout>
    )
  }

  return (
    <Layout>
      {/* Header */}
      <div className="mb-6">
        <Button
          onClick={() => navigate('/budgets')}
          variant="outline"
          size="sm"
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Budgets
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{report.budget_name}</h1>
            <p className="mt-1 text-sm text-gray-500">
              Variance Report | {report.fund_name} | {report.period}
            </p>
          </div>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-6 mb-8 sm:grid-cols-3">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Budgeted</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {formatCurrency(report.totals.budgeted)}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Actual Spent</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {formatCurrency(report.totals.actual)}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Variance</h3>
          <div className="mt-2 flex items-center">
            <p className={`text-3xl font-bold ${
              parseFloat(report.totals.variance) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(report.totals.variance)}
            </p>
            <span className={`ml-2 text-lg font-medium ${
              parseFloat(report.totals.variance) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              ({report.totals.variance_pct})
            </span>
          </div>
        </div>
      </div>

      {/* Chart */}
      {report.lines.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Budget vs Actual Comparison
          </h2>
          <VarianceChart data={report.lines} />
        </div>
      )}

      {/* Variance Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Detailed Variance Analysis</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Budgeted
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actual
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Variance
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % Variance
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {report.lines.map((line, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {line.account_number} - {line.account_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {formatCurrency(line.budgeted)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {formatCurrency(line.actual)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${getVarianceColor(line.status)}`}>
                    {formatCurrency(line.variance)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${getVarianceColor(line.status)}`}>
                    {line.variance_pct}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <div className="flex items-center justify-center">
                      {getVarianceIcon(line.status)}
                      <span className={`ml-1 ${getVarianceColor(line.status)}`}>
                        {line.status.charAt(0).toUpperCase() + line.status.slice(1)}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr className="font-bold">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  Total
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {formatCurrency(report.totals.budgeted)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {formatCurrency(report.totals.actual)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${
                  parseFloat(report.totals.variance) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(report.totals.variance)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${
                  parseFloat(report.totals.variance) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {report.totals.variance_pct}
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center space-x-8 text-sm">
        <div className="flex items-center">
          <TrendingUp className="w-4 h-4 text-green-600 mr-2" />
          <span className="text-gray-600">Favorable - Under budget</span>
        </div>
        <div className="flex items-center">
          <TrendingDown className="w-4 h-4 text-red-600 mr-2" />
          <span className="text-gray-600">Unfavorable - Over budget</span>
        </div>
      </div>
    </Layout>
  )
}
