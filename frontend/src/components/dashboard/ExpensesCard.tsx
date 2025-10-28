import React, { useState, useEffect } from 'react'
import { dashboardApi, type ExpenseRevenueResponse } from '../../api/dashboard'
import { formatCurrency } from '../../utils/formatters'
import { TrendingUp, TrendingDown, Receipt } from 'lucide-react'

export const ExpensesCard: React.FC = () => {
  const [data, setData] = useState<ExpenseRevenueResponse | null>(null)
  const [period, setPeriod] = useState<'mtd' | 'ytd'>('mtd')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [period])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await dashboardApi.getExpenses(period)
      setData(response)
    } catch (err: any) {
      setError('Failed to load expenses')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-2/3 mb-4"></div>
        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error || 'No data available'}</p>
        </div>
      </div>
    )
  }

  const changePct = data.comparison.change_pct
  const isIncrease = changePct > 0

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">
          {period === 'mtd' ? 'MTD' : 'YTD'} Expenses
        </h3>
        <Receipt className="w-5 h-5 text-gray-400" />
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-2">
        {formatCurrency(data.total)}
      </p>

      <div className="flex items-center text-sm">
        {isIncrease ? (
          <TrendingUp className="w-4 h-4 text-red-600 mr-1" />
        ) : (
          <TrendingDown className="w-4 h-4 text-green-600 mr-1" />
        )}
        <span
          className={`font-medium ${
            isIncrease ? 'text-red-600' : 'text-green-600'
          }`}
        >
          {isIncrease ? '+' : ''}{changePct.toFixed(1)}%
        </span>
        <span className="text-gray-500 ml-1">vs last {period === 'mtd' ? 'month' : 'year'}</span>
      </div>

      {data.top_categories && data.top_categories.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs font-medium text-gray-500 mb-2">Top Categories</p>
          <div className="space-y-1">
            {data.top_categories.map((cat, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-gray-600 truncate">{cat.category}</span>
                <span className="font-medium text-gray-900 ml-2">
                  {formatCurrency(cat.amount)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => setPeriod('mtd')}
          className={`flex-1 py-1 px-3 text-xs font-medium rounded ${
            period === 'mtd'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          MTD
        </button>
        <button
          onClick={() => setPeriod('ytd')}
          className={`flex-1 py-1 px-3 text-xs font-medium rounded ${
            period === 'ytd'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          YTD
        </button>
      </div>
    </div>
  )
}
