import React, { useState, useEffect } from 'react'
import { fundsApi, type CreateFundRequest, type UpdateFundRequest } from '../../api/funds'
import type { Fund } from '../../types/api'
import { Button } from '../ui/Button'
import { X } from 'lucide-react'

interface FundModalProps {
  fund: Fund | null
  onClose: () => void
  onSuccess: () => void
}

export const FundModal: React.FC<FundModalProps> = ({ fund, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    fund_type: 'OPERATING' as 'OPERATING' | 'RESERVE' | 'SPECIAL_ASSESSMENT',
    description: '',
    is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (fund) {
      setFormData({
        name: fund.name,
        fund_type: fund.fund_type as 'OPERATING' | 'RESERVE' | 'SPECIAL_ASSESSMENT',
        description: fund.description || '',
        is_active: fund.is_active,
      })
    }
  }, [fund])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      setLoading(true)
      setError(null)

      if (fund) {
        // Update existing fund
        const updateData: UpdateFundRequest = {
          name: formData.name,
          fund_type: formData.fund_type,
          description: formData.description || undefined,
          is_active: formData.is_active,
        }
        await fundsApi.updateFund(fund.id, updateData)
      } else {
        // Create new fund
        const createData: CreateFundRequest = {
          name: formData.name,
          fund_type: formData.fund_type,
          description: formData.description || undefined,
          is_active: formData.is_active,
        }
        await fundsApi.createFund(createData)
      }

      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.name?.[0] || 'Failed to save fund')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {fund ? 'Edit Fund' : 'Create Fund'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Fund Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={loading}
              />
            </div>

            {/* Fund Type */}
            <div>
              <label htmlFor="fund_type" className="block text-sm font-medium text-gray-700 mb-1">
                Fund Type *
              </label>
              <select
                id="fund_type"
                value={formData.fund_type}
                onChange={(e) => setFormData({
                  ...formData,
                  fund_type: e.target.value as 'OPERATING' | 'RESERVE' | 'SPECIAL_ASSESSMENT'
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={loading}
              >
                <option value="OPERATING">Operating Fund</option>
                <option value="RESERVE">Reserve Fund</option>
                <option value="SPECIAL_ASSESSMENT">Special Assessment Fund</option>
              </select>
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>

            {/* Active Status */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                Active
              </label>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={loading}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                {loading ? 'Saving...' : fund ? 'Update Fund' : 'Create Fund'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
