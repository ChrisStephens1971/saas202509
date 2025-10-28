import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { SkeletonTable } from '../components/ui/Skeleton'
import { InvoiceDetailModal } from '../components/invoices/InvoiceDetailModal'
import { accountingApi } from '../api/accounting'
import { formatMoney, formatDate, getStatusColor, getStatusLabel } from '../utils/formatters'
import { exportToCsv } from '../utils/exportToCsv'
import type { Invoice } from '../types/api'
import { Download } from 'lucide-react'

export function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState('ALL')
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  useEffect(() => {
    loadInvoices()
  }, [filter])

  const loadInvoices = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await accountingApi.getInvoices({
        status: filter === 'ALL' ? undefined : filter
      })
      setInvoices(data.results || [])
    } catch (err: any) {
      console.error('Failed to load invoices:', err)
      setError(err.message || 'Failed to load invoices')
      setInvoices([])
    } finally {
      setLoading(false)
    }
  }

  const handleInvoiceClick = (invoiceId: string) => {
    setSelectedInvoiceId(invoiceId)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedInvoiceId(null)
  }

  const handleExportToCsv = () => {
    // Flatten invoice data for CSV export
    const flattenedData = invoices.map(invoice => ({
      invoice_number: invoice.invoice_number,
      owner_name: invoice.owner ? `${invoice.owner.first_name} ${invoice.owner.last_name}` : 'N/A',
      owner_email: invoice.owner?.email || 'N/A',
      invoice_date: formatDate(invoice.invoice_date),
      due_date: formatDate(invoice.due_date),
      total_amount: invoice.total_amount,
      balance: invoice.balance,
      status: getStatusLabel(invoice.status),
    }))

    exportToCsv(
      flattenedData,
      `invoices-${new Date().toISOString().split('T')[0]}.csv`,
      [
        { key: 'invoice_number', header: 'Invoice Number' },
        { key: 'owner_name', header: 'Owner Name' },
        { key: 'owner_email', header: 'Owner Email' },
        { key: 'invoice_date', header: 'Invoice Date' },
        { key: 'due_date', header: 'Due Date' },
        { key: 'total_amount', header: 'Total Amount' },
        { key: 'balance', header: 'Balance' },
        { key: 'status', header: 'Status' },
      ]
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
          <div className="flex gap-4">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="ALL">All Invoices</option>
              <option value="ISSUED">Issued</option>
              <option value="OVERDUE">Overdue</option>
              <option value="PAID">Paid</option>
            </select>
            <Button onClick={handleExportToCsv} disabled={invoices.length === 0}>
              <Download className="w-4 h-4 mr-2" />
              Export to CSV
            </Button>
          </div>
        </div>

        <Card>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}
          {loading ? (
            <SkeletonTable rows={10} />
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice #</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Balance</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {invoices.map((invoice) => (
                    <tr
                      key={invoice.id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => handleInvoiceClick(invoice.id)}
                    >
                      <td className="px-4 py-3 text-sm font-medium text-blue-600">{invoice.invoice_number}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {invoice.owner ? `${invoice.owner.first_name} ${invoice.owner.last_name}` : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatDate(invoice.invoice_date)}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatDate(invoice.due_date)}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{formatMoney(invoice.total_amount)}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900">{formatMoney(invoice.balance)}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
                          {getStatusLabel(invoice.status)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {invoices.length === 0 && (
                <div className="text-center py-8 text-gray-500">No invoices found</div>
              )}
            </div>
          )}
        </Card>
      </div>

      <InvoiceDetailModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        invoiceId={selectedInvoiceId}
      />
    </Layout>
  )
}
