import React, { useState, useEffect } from 'react'
import { dashboardApi, type RecentActivityResponse } from '../../api/dashboard'
import { formatCurrency, formatDate } from '../../utils/formatters'
import { FileText, DollarSign, Clock } from 'lucide-react'

export const RecentActivityList: React.FC = () => {
  const [data, setData] = useState<RecentActivityResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await dashboardApi.getRecentActivity(10)
      setData(response)
    } catch (err: any) {
      setError('Failed to load recent activity')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getActivityIcon = (type: string) => {
    if (type === 'invoice') {
      return <FileText className="w-5 h-5 text-blue-500" />
    } else if (type === 'payment') {
      return <DollarSign className="w-5 h-5 text-green-500" />
    }
    return <Clock className="w-5 h-5 text-gray-400" />
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
              <div className="flex-1">
                <div className="h-3 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-2 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
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
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>

      {data.activities.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-8">No recent activity</p>
      ) : (
        <div className="space-y-4">
          {data.activities.map((activity, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">{getActivityIcon(activity.type)}</div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {activity.description}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatDate(activity.timestamp)}
                </p>
              </div>

              <div className="flex-shrink-0">
                <span
                  className={`text-sm font-medium ${
                    activity.type === 'payment' ? 'text-green-600' : 'text-gray-900'
                  }`}
                >
                  {formatCurrency(activity.amount)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={loadData}
        className="mt-4 w-full py-2 px-4 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
      >
        Refresh
      </button>
    </div>
  )
}
