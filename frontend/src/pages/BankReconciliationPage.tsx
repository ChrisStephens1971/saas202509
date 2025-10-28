import React, { useState, useEffect } from 'react'
import { Layout } from '../components/layout/Layout'
import { reconciliationApi } from '../api/reconciliation'
import { budgetsApi } from '../api/budgets'
import type { BankStatement, Fund } from '../types/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Select } from '../components/ui/Select'
import { Skeleton } from '../components/ui/Skeleton'
import { formatCurrency, formatDate } from '../utils/formatters'
import { FileUp } from 'lucide-react'

export const BankReconciliationPage: React.FC = () => {
  const [statements, setStatements] = useState<BankStatement[]>([])
  const [funds, setFunds] = useState<Fund[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Upload state
  const [showUpload, setShowUpload] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadFund, setUploadFund] = useState('')
  const [uploadDate, setUploadDate] = useState('')
  const [uploadBeginning, setUploadBeginning] = useState('')
  const [uploadEnding, setUploadEnding] = useState('')
  const [uploading, setUploading] = useState(false)

  // Filter
  const [fundFilter, setFundFilter] = useState<string>('all')
  const [reconciledFilter, setReconciledFilter] = useState<string>('all')

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load funds for filter dropdown
      if (funds.length === 0) {
        try {
          const fundsData = await budgetsApi.getFunds()
          setFunds(fundsData)
        } catch (fundErr) {
          console.error('Failed to load funds:', fundErr)
          // Continue even if funds fail to load
        }
      }

      // Load statements with filters
      const params: any = {}
      if (fundFilter !== 'all') params.fund = fundFilter
      if (reconciledFilter !== 'all') {
        params.reconciled = reconciledFilter === 'reconciled'
      }

      const statementsData = await reconciliationApi.getStatements(params)
      setStatements(statementsData)
    } catch (err: any) {
      console.error('Failed to load statements:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load statements')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [fundFilter, reconciledFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async () => {
    if (!uploadFile || !uploadFund || !uploadDate || !uploadBeginning || !uploadEnding) {
      alert('Please fill in all fields')
      return
    }

    try {
      setUploading(true)
      await reconciliationApi.uploadStatement(
        uploadFile,
        uploadFund,
        uploadDate,
        uploadBeginning,
        uploadEnding
      )

      // Reset form
      setUploadFile(null)
      setUploadFund('')
      setUploadDate('')
      setUploadBeginning('')
      setUploadEnding('')
      setShowUpload(false)

      // Reload data
      await loadData()
    } catch (err: any) {
      console.error('Upload failed:', err)
      alert(err.response?.data?.error || err.message || 'Failed to upload statement')
    } finally {
      setUploading(false)
    }
  }

  const getStatusBadge = (statement: BankStatement) => {
    if (statement.reconciled) {
      return <Badge variant="success">Reconciled</Badge>
    }

    const unmatchedCount = statement.unmatched_count || 0
    if (unmatchedCount === 0) {
      return <Badge variant="success">All Matched</Badge>
    }

    return <Badge variant="warning">{unmatchedCount} Unmatched</Badge>
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {error && (
          <div className="mb-6">
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Bank Reconciliation</h1>
          <p className="text-gray-600 mt-2">
            Upload bank statements and match transactions to journal entries
          </p>
        </div>

        {/* Actions */}
        <div className="mb-6 flex items-center gap-4">
          <Button
            onClick={() => setShowUpload(!showUpload)}
            className="flex items-center gap-2"
          >
            <FileUp size={18} />
            Upload Statement
          </Button>

          {/* Filters */}
          <Select
            value={fundFilter}
            onChange={(e) => setFundFilter(e.target.value)}
            className="w-48"
          >
            <option value="all">All Funds</option>
            {funds.map((fund) => (
              <option key={fund.id} value={fund.id}>
                {fund.name}
              </option>
            ))}
          </Select>

          <Select
            value={reconciledFilter}
            onChange={(e) => setReconciledFilter(e.target.value)}
            className="w-48"
          >
            <option value="all">All Statements</option>
            <option value="reconciled">Reconciled</option>
            <option value="unreconciled">Unreconciled</option>
          </Select>
        </div>

        {/* Upload Form */}
        {showUpload && (
          <div className="mb-6 bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Upload Bank Statement</h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fund
                </label>
                <Select
                  value={uploadFund}
                  onChange={(e) => setUploadFund(e.target.value)}
                  required
                >
                  <option value="">Select fund...</option>
                  {funds.map((fund) => (
                    <option key={fund.id} value={fund.id}>
                      {fund.name}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Statement Date
                </label>
                <input
                  type="date"
                  value={uploadDate}
                  onChange={(e) => setUploadDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Beginning Balance
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={uploadBeginning}
                  onChange={(e) => setUploadBeginning(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="0.00"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ending Balance
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={uploadEnding}
                  onChange={(e) => setUploadEnding(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="0.00"
                  required
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CSV File
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Expected columns: date, description, amount, check_number (optional), reference (optional)
                </p>
              </div>
            </div>

            <div className="mt-4 flex gap-3">
              <Button onClick={handleUpload} disabled={uploading}>
                {uploading ? 'Uploading...' : 'Upload & Parse'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowUpload(false)}
                disabled={uploading}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Statements List */}
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
        ) : statements.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <FileUp className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No bank statements</h3>
            <p className="mt-1 text-sm text-gray-500">
              Upload your first bank statement to get started.
            </p>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Statement Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fund
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Beginning
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ending
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {statements.map((statement) => (
                  <tr key={statement.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatDate(statement.statement_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {statement.fund_name || (typeof statement.fund === 'object' ? statement.fund.name : statement.fund)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(statement.beginning_balance)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(statement.ending_balance)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(statement)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(statement.uploaded_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.location.href = `/reconciliation/${statement.id}`}
                      >
                        {statement.reconciled ? 'View' : 'Reconcile'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
