import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { dashboardApi, type RevenueVsExpensesResponse } from '../../api/dashboard'

export const RevenueVsExpensesChart: React.FC = () => {
  const [data, setData] = useState<RevenueVsExpensesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await dashboardApi.getRevenueVsExpenses()
      setData(response)
    } catch (err: any) {
      setError('Failed to load chart data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
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

  // Transform data for Recharts
  const chartData = data.months.map((month) => ({
    month: month.month,
    Revenue: parseFloat(month.revenue),
    Expenses: parseFloat(month.expenses),
  }))

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          <p className="text-sm text-green-600">
            Revenue: ${payload[0].value.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
          <p className="text-sm text-red-600">
            Expenses: ${payload[1].value.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
          <p className="text-sm font-medium text-gray-900 mt-1">
            Net: ${(payload[0].value - payload[1].value).toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Revenue vs Expenses (Last 12 Months)
      </h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) =>
              `$${value.toLocaleString('en-US', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}`
            }
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '10px' }} />
          <Line
            type="monotone"
            dataKey="Revenue"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Revenue"
          />
          <Line
            type="monotone"
            dataKey="Expenses"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Expenses"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
