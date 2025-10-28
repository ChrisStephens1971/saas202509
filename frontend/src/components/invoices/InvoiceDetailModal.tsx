import { useEffect, useState } from 'react'
import { Modal } from '../ui/Modal'
import { accountingApi } from '../../api/accounting'
import { formatMoney, formatDate, getStatusColor, getStatusLabel } from '../../utils/formatters'
import type { InvoiceDetail } from '../../types/api'

interface InvoiceDetailModalProps {
  isOpen: boolean
  onClose: () => void
  invoiceId: string | null
}

export function InvoiceDetailModal({ isOpen, onClose, invoiceId }: InvoiceDetailModalProps) {
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && invoiceId) {
      loadInvoice()
    }
  }, [isOpen, invoiceId])

  const loadInvoice = async () => {
    if (!invoiceId) return

    setLoading(true)
    setError(null)
    try {
      const data = await accountingApi.getInvoice(invoiceId)
      setInvoice(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load invoice')
    } finally {
      setLoading(false)
    }
  }

  const renderContent = () => {
    if (loading) {
      return <div className="text-center py-8 text-gray-500">Loading invoice details...</div>
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )
    }

    if (!invoice) {
      return null
    }

    return (
      <div className="space-y-6">
        {/* Invoice Header */}
        <div className="grid grid-cols-2 gap-4 pb-4 border-b border-gray-200">
          <div>
            <p className="text-sm text-gray-600">Invoice Number</p>
            <p className="text-lg font-semibold text-gray-900">{invoice.invoice_number}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(invoice.status)}`}>
              {getStatusLabel(invoice.status)}
            </span>
          </div>
          <div>
            <p className="text-sm text-gray-600">Owner</p>
            <p className="text-base font-medium text-gray-900">{invoice.owner_name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Unit</p>
            <p className="text-base font-medium text-gray-900">{invoice.unit_number}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Invoice Date</p>
            <p className="text-base text-gray-900">{formatDate(invoice.invoice_date)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Due Date</p>
            <p className="text-base text-gray-900">{formatDate(invoice.due_date)}</p>
          </div>
          {invoice.days_overdue > 0 && (
            <div className="col-span-2">
              <p className="text-sm text-gray-600">Days Overdue</p>
              <p className="text-base font-semibold text-red-600">{invoice.days_overdue} days</p>
            </div>
          )}
        </div>

        {/* Invoice Lines */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Invoice Items</h3>
          <div className="overflow-hidden border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoice.lines.map((line) => (
                  <tr key={line.line_number}>
                    <td className="px-4 py-3 text-sm text-gray-900">{line.description}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {line.account_number} - {line.account_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                      {formatMoney(line.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Totals */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Subtotal:</span>
            <span className="text-gray-900 font-medium">{formatMoney(invoice.subtotal)}</span>
          </div>
          {parseFloat(invoice.late_fee) > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Late Fee:</span>
              <span className="text-red-600 font-medium">{formatMoney(invoice.late_fee)}</span>
            </div>
          )}
          <div className="flex justify-between text-base pt-2 border-t border-gray-200">
            <span className="text-gray-900 font-semibold">Total Amount:</span>
            <span className="text-gray-900 font-bold">{formatMoney(invoice.total_amount)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Amount Paid:</span>
            <span className="text-green-600 font-medium">{formatMoney(invoice.amount_paid)}</span>
          </div>
          <div className="flex justify-between text-lg pt-2 border-t border-gray-200">
            <span className="text-gray-900 font-bold">Balance Due:</span>
            <span className={`font-bold ${parseFloat(invoice.amount_due) > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatMoney(invoice.amount_due)}
            </span>
          </div>
        </div>

        {/* Description */}
        {invoice.description && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Notes</h3>
            <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">{invoice.description}</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Invoice Details">
      {renderContent()}
    </Modal>
  )
}
