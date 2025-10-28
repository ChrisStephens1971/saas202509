import React, { useState, useEffect } from 'react'
import { dashboardApi, type CashPositionResponse } from '../../api/dashboard'
import { formatCurrency } from '../../utils/formatters'
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react'

export const CashPositionCard: React.FC = () => {
  const [data, setData] = useState<CashPositionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await dashboardApi.getCashPosition()
      setData(response)
    } catch (err: any) {
      setError('Failed to load cash position')
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
        <div className="space-y-2">
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded"></div>
        </div>
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

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">Total Cash Position</h3>
        <DollarSign className="w-5 h-5 text-gray-400" />
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-4">
        {formatCurrency(data.total_cash)}
      </p>

      <div className="space-y-3">
        {data.funds.map((fund, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-700">{fund.name}</p>
              <p className="text-xs text-gray-500">
                {formatCurrency(fund.balance)}
              </p>
            </div>
            <div className="flex items-center">
              {fund.trend >= 0 ? (
                <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
              )}
              <span
                className={`text-sm font-medium ${
                  fund.trend >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {fund.trend >= 0 ? '+' : ''}{fund.trend.toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
