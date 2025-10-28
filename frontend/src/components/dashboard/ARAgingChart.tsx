import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card } from '../ui/Card'
import { formatMoney } from '../../utils/formatters'

interface ARAgingChartProps {
  data: {
    current: string
    days_30: string
    days_60: string
    days_90: string
    days_over_90: string
  }
}

export function ARAgingChart({ data }: ARAgingChartProps) {
  const chartData = [
    {
      name: 'Current',
      amount: parseFloat(data.current),
    },
    {
      name: '30-60 Days',
      amount: parseFloat(data.days_30),
    },
    {
      name: '60-90 Days',
      amount: parseFloat(data.days_60),
    },
    {
      name: '90+ Days',
      amount: parseFloat(data.days_over_90),
    },
  ]

  return (
    <Card>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">AR Aging</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            formatter={(value: number) => formatMoney(value)}
            contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
          />
          <Legend />
          <Bar dataKey="amount" fill="#3b82f6" name="Amount" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}
