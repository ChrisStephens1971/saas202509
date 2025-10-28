import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { Card } from '../components/ui/Card'
import { accountingApi } from '../api/accounting'
import { formatMoney, formatDate } from '../utils/formatters'
import type { Owner, LedgerEntry } from '../types/api'

export function OwnerLedgerPage() {
  const [owners, setOwners] = useState<Owner[]>([])
  const [selectedOwnerId, setSelectedOwnerId] = useState<string>('')
  const [ledger, setLedger] = useState<LedgerEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadOwners()
  }, [])

  useEffect(() => {
    if (selectedOwnerId) {
      loadLedger()
    }
  }, [selectedOwnerId])

  const loadOwners = async () => {
    try {
      const data = await accountingApi.getOwners()
      setOwners(data)
    } catch (err: any) {
      console.error('Failed to load owners:', err)
    }
  }

  const loadLedger = async () => {
    if (!selectedOwnerId) return

    setLoading(true)
    setError(null)
    try {
      const data = await accountingApi.getOwnerLedger(selectedOwnerId)
      setLedger(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load ledger')
    } finally {
      setLoading(false)
    }
  }

  const selectedOwner = owners.find((o) => o.id === selectedOwnerId)

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Owner Ledger</h1>
        </div>

        {/* Owner Selection */}
        <Card>
          <div className="space-y-4">
            <div>
              <label htmlFor="owner-select" className="block text-sm font-medium text-gray-700 mb-2">
                Select Owner
              </label>
              <select
                id="owner-select"
                value={selectedOwnerId}
                onChange={(e) => setSelectedOwnerId(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">-- Select an owner --</option>
                {owners.map((owner) => (
                  <option key={owner.id} value={owner.id}>
                    {owner.first_name} {owner.last_name} ({owner.owner_number})
                  </option>
                ))}
              </select>
            </div>

            {selectedOwner && (
              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <p className="text-sm text-gray-600">Email</p>
                  <p className="text-base font-medium text-gray-900">{selectedOwner.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Phone</p>
                  <p className="text-base font-medium text-gray-900">{selectedOwner.phone || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">AR Balance</p>
                  <p className={`text-base font-bold ${parseFloat(selectedOwner.ar_balance) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {formatMoney(selectedOwner.ar_balance)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Ledger */}
        {selectedOwnerId && (
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Transaction History</h2>

            {loading && (
              <div className="text-center py-8 text-gray-500">Loading ledger...</div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {!loading && !error && ledger.length === 0 && (
              <div className="text-center py-8 text-gray-500">No transactions found</div>
            )}

            {!loading && !error && ledger.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reference</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debit</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Credit</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {ledger.map((entry, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-700">{formatDate(entry.date)}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            entry.type === 'invoice'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {entry.type === 'invoice' ? 'Invoice' : 'Payment'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{entry.reference_number}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">{entry.description}</td>
                        <td className="px-4 py-3 text-sm text-right text-red-600 font-medium">
                          {parseFloat(entry.debit) > 0 ? formatMoney(entry.debit) : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                          {parseFloat(entry.credit) > 0 ? formatMoney(entry.credit) : '—'}
                        </td>
                        <td className={`px-4 py-3 text-sm text-right font-bold ${
                          parseFloat(entry.balance) > 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {formatMoney(entry.balance)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}
      </div>
    </Layout>
  )
}
