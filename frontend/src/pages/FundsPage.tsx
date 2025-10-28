import React, { useState, useEffect } from 'react'
import { Layout } from '../components/layout/Layout'
import { fundsApi } from '../api/funds'
import type { Fund } from '../types/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Select } from '../components/ui/Select'
import { Skeleton } from '../components/ui/Skeleton'
import { formatDate } from '../utils/formatters'
import { FundModal } from '../components/funds/FundModal'
import { Wallet, Plus, Edit, Trash2 } from 'lucide-react'

export const FundsPage: React.FC = () => {
  const [funds, setFunds] = useState<Fund[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [fundTypeFilter, setFundTypeFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingFund, setEditingFund] = useState<Fund | null>(null)

  useEffect(() => {
    loadData()
  }, [fundTypeFilter, statusFilter])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = {}
      if (fundTypeFilter !== 'all') params.fund_type = fundTypeFilter
      if (statusFilter !== 'all') params.is_active = statusFilter === 'active'

      const response = await fundsApi.getFunds(params)
      setFunds(response.results)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load funds')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingFund(null)
    setIsModalOpen(true)
  }

  const handleEdit = (fund: Fund) => {
    setEditingFund(fund)
    setIsModalOpen(true)
  }

  const handleDelete = async (fund: Fund) => {
    if (!confirm(`Are you sure you want to delete "${fund.name}"?`)) return

    try {
      await fundsApi.deleteFund(fund.id)
      await loadData()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete fund')
    }
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setEditingFund(null)
  }

  const handleModalSuccess = () => {
    handleModalClose()
    loadData()
  }

  const getFundTypeLabel = (fundType: string) => {
    switch (fundType) {
      case 'OPERATING':
        return 'Operating Fund'
      case 'RESERVE':
        return 'Reserve Fund'
      case 'SPECIAL_ASSESSMENT':
        return 'Special Assessment'
      default:
        return fundType
    }
  }

  const getFundTypeVariant = (fundType: string): 'success' | 'info' | 'warning' => {
    switch (fundType) {
      case 'OPERATING':
        return 'success'
      case 'RESERVE':
        return 'info'
      case 'SPECIAL_ASSESSMENT':
        return 'warning'
      default:
        return 'info'
    }
  }

  const fundTypeOptions = [
    { value: 'all', label: 'All Types' },
    { value: 'OPERATING', label: 'Operating Fund' },
    { value: 'RESERVE', label: 'Reserve Fund' },
    { value: 'SPECIAL_ASSESSMENT', label: 'Special Assessment' },
  ]

  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
  ]

  return (
    <Layout>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Funds</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage operating, reserve, and special assessment funds
          </p>
        </div>
        <Button
          onClick={handleCreate}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Fund
        </Button>
      </div>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Select
          value={fundTypeFilter}
          onChange={(e) => setFundTypeFilter(e.target.value)}
          options={fundTypeOptions}
        />
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          options={statusOptions}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Fund List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : funds.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <Wallet className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No funds found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first fund.
          </p>
          <Button
            onClick={handleCreate}
            className="mt-4 bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Fund
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {funds.map((fund) => (
            <div
              key={fund.id}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {fund.name}
                    </h3>
                    <Badge variant={getFundTypeVariant(fund.fund_type)}>
                      {getFundTypeLabel(fund.fund_type)}
                    </Badge>
                    {fund.is_active ? (
                      <Badge variant="success">Active</Badge>
                    ) : (
                      <Badge variant="secondary">Inactive</Badge>
                    )}
                  </div>
                  {fund.description && (
                    <p className="mt-2 text-sm text-gray-600">{fund.description}</p>
                  )}
                  <p className="mt-2 text-xs text-gray-500">
                    Created {formatDate(fund.created_at)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleEdit(fund)}
                    variant="outline"
                    size="sm"
                  >
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  {!fund.is_active && (
                    <Button
                      onClick={() => handleDelete(fund)}
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <FundModal
          fund={editingFund}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </Layout>
  )
}
