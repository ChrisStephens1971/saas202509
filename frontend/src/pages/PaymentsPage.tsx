import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { accountingApi } from '../api/accounting'
import type { Owner } from '../types/api'

export function PaymentsPage() {
  const [owners, setOwners] = useState<Owner[]>([])
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    owner: '',
    payment_date: new Date().toISOString().split('T')[0],
    amount: '',
    payment_method: 'CHECK',
    reference_number: '',
    memo: '',
  })

  useEffect(() => {
    loadOwners()
  }, [])

  const loadOwners = async () => {
    try {
      const data = await accountingApi.getOwners()
      setOwners(data)
    } catch (err) {
      console.error(err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setLoading(true)

    try {
      await accountingApi.createPayment(formData)
      setSuccess(true)
      // Reset form
      setFormData({
        ...formData,
        amount: '',
        reference_number: '',
        memo: '',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create payment')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Record Payment</h1>

        <Card className="max-w-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Owner</label>
              <select
                value={formData.owner}
                onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="">Select an owner...</option>
                {owners.map((owner) => (
                  <option key={owner.id} value={owner.id}>
                    {owner.first_name} {owner.last_name} - {owner.owner_number}
                  </option>
                ))}
              </select>
            </div>

            <Input
              type="date"
              label="Payment Date"
              value={formData.payment_date}
              onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
              required
            />

            <Input
              type="number"
              label="Amount"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              placeholder="0.00"
              step="0.01"
              required
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
              <select
                value={formData.payment_method}
                onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="CASH">Cash</option>
                <option value="CHECK">Check</option>
                <option value="ACH">ACH</option>
                <option value="CREDIT_CARD">Credit Card</option>
                <option value="WIRE">Wire Transfer</option>
              </select>
            </div>

            <Input
              type="text"
              label="Check/Reference Number"
              value={formData.reference_number}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
              placeholder="Optional"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Memo</label>
              <textarea
                value={formData.memo}
                onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                rows={3}
                placeholder="Optional notes..."
              />
            </div>

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
                Payment recorded successfully!
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Recording Payment...' : 'Record Payment'}
            </Button>
          </form>
        </Card>
      </div>
    </Layout>
  )
}
