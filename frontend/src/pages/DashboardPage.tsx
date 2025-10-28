import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { Card } from '../components/ui/Card'
import { SkeletonCard, SkeletonTable, SkeletonChart } from '../components/ui/Skeleton'
import { ARAgingChart } from '../components/dashboard/ARAgingChart'
import { accountingApi } from '../api/accounting'
import { formatMoney, formatDate, getStatusColor, getStatusLabel } from '../utils/formatters'
import type { DashboardMetrics } from '../types/api'
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react'

export function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const data = await accountingApi.getDashboard()
      setMetrics(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>

          {/* Skeleton metrics cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>

          {/* Skeleton chart */}
          <SkeletonChart />

          {/* Skeleton tables */}
          <Card>
            <SkeletonTable rows={5} />
          </Card>
          <Card>
            <SkeletonTable rows={5} />
          </Card>
        </div>
      </Layout>
    )
  }

  if (error || !metrics) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error loading dashboard: {error || 'Unknown error'}
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>

        {/* AR Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total AR</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {formatMoney(metrics.total_ar)}
                </p>
              </div>
              <DollarSign className="w-12 h-12 text-primary-600" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overdue</p>
                <p className="text-3xl font-bold text-red-600 mt-2">
                  {formatMoney(metrics.overdue_ar)}
                </p>
              </div>
              <TrendingDown className="w-12 h-12 text-red-600" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Current</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  {formatMoney(metrics.current_ar)}
                </p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-600" />
            </div>
          </Card>
        </div>

        {/* AR Aging Chart */}
        <ARAgingChart data={metrics.ar_aging} />

        {/* Recent Invoices */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Invoices</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {metrics.recent_invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{invoice.invoice_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{invoice.owner.first_name} {invoice.owner.last_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{formatDate(invoice.invoice_date)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{formatMoney(invoice.total_amount)}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
                        {getStatusLabel(invoice.status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Recent Payments */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Payments</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {metrics.recent_payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{payment.payment_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{payment.owner.first_name} {payment.owner.last_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{formatDate(payment.payment_date)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{formatMoney(payment.amount)}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{payment.payment_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Layout>
  )
}
