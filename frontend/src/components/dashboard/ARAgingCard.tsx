import React, { useState, useEffect } from 'react'
import { dashboardApi, type ARAgingResponse } from '../../api/dashboard'
import { formatCurrency } from '../../utils/formatters'
import { Clock, AlertTriangle } from 'lucide-react'

export const ARAgingCard: React.FC = () => {
  const [data, setData] = useState<ARAgingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await dashboardApi.getARAging()
      setData(response)
    } catch (err: any) {
      setError('Failed to load AR aging')
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

  const hasOverdue = data.buckets.days_over_90.percentage > 0

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">Accounts Receivable</h3>
        {hasOverdue ? (
          <AlertTriangle className="w-5 h-5 text-red-500" />
        ) : (
          <Clock className="w-5 h-5 text-gray-400" />
        )}
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-1">
        {formatCurrency(data.total_ar)}
      </p>
      <p className="text-sm text-gray-500 mb-4">
        Avg. {data.average_days} days outstanding
      </p>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Current (0-30)</span>
          <div className="flex items-center">
            <span className="font-medium text-gray-900 mr-2">
              {formatCurrency(data.buckets.current.amount)}
            </span>
            <span className="text-gray-500">
              {data.buckets.current.percentage}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">30-60 days</span>
          <div className="flex items-center">
            <span className="font-medium text-gray-900 mr-2">
              {formatCurrency(data.buckets.days_30_60.amount)}
            </span>
            <span className="text-gray-500">
              {data.buckets.days_30_60.percentage}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">60-90 days</span>
          <div className="flex items-center">
            <span className="font-medium text-orange-600 mr-2">
              {formatCurrency(data.buckets.days_60_90.amount)}
            </span>
            <span className="text-orange-600">
              {data.buckets.days_60_90.percentage}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">90+ days</span>
          <div className="flex items-center">
            <span className="font-medium text-red-600 mr-2">
              {formatCurrency(data.buckets.days_over_90.amount)}
            </span>
            <span className="text-red-600">
              {data.buckets.days_over_90.percentage}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
