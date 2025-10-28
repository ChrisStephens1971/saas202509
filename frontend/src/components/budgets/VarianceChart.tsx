import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { VarianceLine } from '../../types/api'

interface VarianceChartProps {
  data: VarianceLine[]
}

export const VarianceChart: React.FC<VarianceChartProps> = ({ data }) => {
  // Transform data for Recharts
  const chartData = data.map((line) => ({
    name: line.account_number,
    Budgeted: parseFloat(line.budgeted),
    Actual: parseFloat(line.actual),
  }))

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const line = data.find((l) => l.account_number === label)
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">
            {label} - {line?.account_name}
          </p>
          <p className="text-sm text-blue-600">
            Budgeted: ${payload[0].value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className="text-sm text-green-600">
            Actual: ${payload[1].value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          {line && (
            <p className={`text-sm font-medium mt-1 ${
              line.status === 'favorable' ? 'text-green-600' : 'text-red-600'
            }`}>
              Variance: ${parseFloat(line.variance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({line.variance_pct})
            </p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart
        data={chartData}
        margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={100}
          interval={0}
          tick={{ fontSize: 12 }}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(value) =>
            `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
          }
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ paddingTop: '20px' }} />
        <Bar dataKey="Budgeted" fill="#3b82f6" name="Budgeted" />
        <Bar dataKey="Actual" fill="#10b981" name="Actual" />
      </BarChart>
    </ResponsiveContainer>
  )
}
