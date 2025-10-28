import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { reconciliationApi } from '../api/reconciliation'
import type { BankStatement, BankTransaction, MatchSuggestion } from '../types/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Skeleton } from '../components/ui/Skeleton'
import { formatCurrency, formatDate } from '../utils/formatters'
import { ArrowLeft, XCircle, Sparkles } from 'lucide-react'

export const ReconciliationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [statement, setStatement] = useState<BankStatement | null>(null)
  const [transactions, setTransactions] = useState<BankTransaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Suggestion state
  const [selectedTransaction, setSelectedTransaction] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<MatchSuggestion[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)

  useEffect(() => {
    if (id) {
      loadData()
    }
  }, [id])

  const loadData = async () => {
    if (!id) return

    try {
      setLoading(true)
      setError(null)

      const data = await reconciliationApi.getStatementDetail(id)
      setStatement(data.statement)
      setTransactions(data.transactions)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load statement')
    } finally {
      setLoading(false)
    }
  }

  const handleGetSuggestions = async (transactionId: string) => {
    try {
      setLoadingSuggestions(true)
      setSelectedTransaction(transactionId)
      const suggestionsData = await reconciliationApi.suggestMatches(transactionId, 5)
      setSuggestions(suggestionsData)
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to get suggestions')
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const handleMatch = async (transactionId: string, entryId: string) => {
    try {
      await reconciliationApi.matchTransaction({
        transaction_id: transactionId,
        entry_id: entryId,
      })
      await loadData()
      setSelectedTransaction(null)
      setSuggestions([])
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to match transaction')
    }
  }

  const handleUnmatch = async (transactionId: string) => {
    if (!confirm('Unmatch this transaction?')) return

    try {
      await reconciliationApi.unmatchTransaction(transactionId)
      await loadData()
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to unmatch transaction')
    }
  }

  const handleIgnore = async (transactionId: string) => {
    const notes = prompt('Optional notes for ignoring this transaction:')
    if (notes === null) return // User cancelled

    try {
      await reconciliationApi.ignoreTransaction(transactionId, notes)
      await loadData()
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to ignore transaction')
    }
  }

  const getStatusBadge = (transaction: BankTransaction) => {
    switch (transaction.status) {
      case 'matched':
        return <Badge variant="success">Matched</Badge>
      case 'created':
        return <Badge variant="success">Created</Badge>
      case 'ignored':
        return <Badge variant="secondary">Ignored</Badge>
      case 'unmatched':
      default:
        return <Badge variant="warning">Unmatched</Badge>
    }
  }

  const getAmountColor = (amount: string) => {
    const num = parseFloat(amount)
    return num >= 0 ? 'text-green-600' : 'text-red-600'
  }

  if (loading) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-12 w-64 mb-6" />
          <Skeleton className="h-96" />
        </div>
      </Layout>
    )
  }

  if (error || !statement) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto">
          <Button variant="outline" onClick={() => navigate('/reconciliation')} className="mb-4">
            <ArrowLeft size={16} className="mr-2" />
            Back to Statements
          </Button>
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error || 'Statement not found'}
          </div>
        </div>
      </Layout>
    )
  }

  const matchedCount = transactions.filter((t) => t.status === 'matched' || t.status === 'created').length
  const unmatchedCount = transactions.filter((t) => t.status === 'unmatched').length

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <Button variant="outline" onClick={() => navigate('/reconciliation')} className="mb-4">
          <ArrowLeft size={16} className="mr-2" />
          Back to Statements
        </Button>

        <div className="mb-6 bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Bank Statement - {formatDate(statement.statement_date)}
              </h1>
              <p className="text-gray-600 mt-1">
                {statement.fund_name} • Uploaded {formatDate(statement.uploaded_at)}
              </p>
            </div>
            <div className="text-right">
              {statement.reconciled ? (
                <Badge variant="success" className="text-base px-4 py-2">
                  Reconciled
                </Badge>
              ) : (
                <Badge variant="warning" className="text-base px-4 py-2">
                  In Progress
                </Badge>
              )}
            </div>
          </div>

        <div className="grid grid-cols-4 gap-6 mt-6">
          <div>
            <p className="text-sm text-gray-500">Beginning Balance</p>
            <p className="text-lg font-semibold">{formatCurrency(statement.beginning_balance)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Ending Balance</p>
            <p className="text-lg font-semibold">{formatCurrency(statement.ending_balance)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Matched</p>
            <p className="text-lg font-semibold text-green-600">{matchedCount}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Unmatched</p>
            <p className="text-lg font-semibold text-yellow-600">{unmatchedCount}</p>
          </div>
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold">Transactions ({transactions.length})</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {transactions.map((transaction) => (
            <div key={transaction.id} className="p-6 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {getStatusBadge(transaction)}
                    <span className="text-sm text-gray-500">
                      {formatDate(transaction.transaction_date)}
                    </span>
                    {transaction.check_number && (
                      <span className="text-sm text-gray-500">
                        Check #{transaction.check_number}
                      </span>
                    )}
                  </div>

                  <p className="text-base font-medium text-gray-900 mb-1">
                    {transaction.description}
                  </p>

                  {transaction.matched_entry_description && (
                    <p className="text-sm text-gray-500">
                      Matched to: {transaction.matched_entry_description}
                      {transaction.match_confidence > 0 && (
                        <span className="ml-2 text-xs text-gray-400">
                          ({transaction.match_confidence}% confidence)
                        </span>
                      )}
                    </p>
                  )}

                  {transaction.notes && (
                    <p className="text-sm text-gray-500 mt-1 italic">
                      Note: {transaction.notes}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-4">
                  <p className={`text-lg font-semibold ${getAmountColor(transaction.amount)}`}>
                    {formatCurrency(transaction.amount)}
                  </p>

                  <div className="flex gap-2">
                    {transaction.status === 'unmatched' && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleGetSuggestions(transaction.id)}
                        >
                          <Sparkles size={14} className="mr-1" />
                          Suggest
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleIgnore(transaction.id)}
                        >
                          <XCircle size={14} className="mr-1" />
                          Ignore
                        </Button>
                      </>
                    )}
                    {(transaction.status === 'matched' || transaction.status === 'created') && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleUnmatch(transaction.id)}
                      >
                        Unmatch
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {/* Suggestions */}
              {selectedTransaction === transaction.id && (
                <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  {loadingSuggestions ? (
                    <p className="text-sm text-gray-600">Loading suggestions...</p>
                  ) : suggestions.length === 0 ? (
                    <p className="text-sm text-gray-600">No matching journal entries found</p>
                  ) : (
                    <div>
                      <p className="text-sm font-medium text-gray-900 mb-3">
                        Suggested Matches ({suggestions.length})
                      </p>
                      <div className="space-y-2">
                        {suggestions.map((suggestion, idx) => (
                          <div
                            key={idx}
                            className="flex justify-between items-center bg-white p-3 rounded border border-gray-200"
                          >
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                {suggestion.journal_entry.description}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                {formatDate(suggestion.journal_entry.entry_date)} •{' '}
                                {formatCurrency(suggestion.journal_entry.amount)} •{' '}
                                {suggestion.confidence}% confidence
                              </p>
                              <p className="text-xs text-blue-600 mt-1">{suggestion.reason}</p>
                            </div>
                            <Button
                              size="sm"
                              onClick={() => handleMatch(transaction.id, suggestion.journal_entry.id)}
                            >
                              Match
                            </Button>
                          </div>
                        ))}
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-3"
                        onClick={() => {
                          setSelectedTransaction(null)
                          setSuggestions([])
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
    </Layout>
  )
}
 
