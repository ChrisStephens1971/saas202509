import React, { useState, useEffect } from 'react'
import { budgetsApi } from '../../api/budgets'
import type { Account } from '../../types/api'
import { Select } from '../ui/Select'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { formatCurrency } from '../../utils/formatters'
import { Trash2, Plus } from 'lucide-react'

interface BudgetLine {
  account: string
  budgeted_amount: string
  notes?: string
}

interface BudgetLinesFormProps {
  data: {
    lines: BudgetLine[]
  }
  onUpdate: (data: any) => void
  onNext: () => void
  onBack: () => void
}

export const BudgetLinesForm: React.FC<BudgetLinesFormProps> = ({
  data,
  onUpdate,
  onNext,
  onBack,
}) => {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [errors, setErrors] = useState<string | null>(null)

  // Current line being edited
  const [selectedAccount, setSelectedAccount] = useState('')
  const [amount, setAmount] = useState('')
  const [notes, setNotes] = useState('')

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const accountsData = await budgetsApi.getAccounts()
      setAccounts(accountsData)
    } catch (err) {
      setErrors('Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const handleAddLine = () => {
    if (!selectedAccount) {
      setErrors('Please select an account')
      return
    }

    if (!amount || parseFloat(amount) <= 0) {
      setErrors('Please enter a valid amount')
      return
    }

    // Check if account already exists
    if (data.lines.some((line) => line.account === selectedAccount)) {
      setErrors('This account has already been added')
      return
    }

    const newLine: BudgetLine = {
      account: selectedAccount,
      budgeted_amount: amount,
      notes: notes || undefined,
    }

    onUpdate({
      lines: [...data.lines, newLine],
    })

    // Reset form
    setSelectedAccount('')
    setAmount('')
    setNotes('')
    setErrors(null)
  }

  const handleRemoveLine = (index: number) => {
    const newLines = data.lines.filter((_, i) => i !== index)
    onUpdate({ lines: newLines })
  }

  const handleNext = () => {
    if (data.lines.length === 0) {
      setErrors('Please add at least one budget line')
      return
    }
    onNext()
  }

  const getTotalBudgeted = () => {
    return data.lines.reduce((sum, line) => {
      return sum + parseFloat(line.budgeted_amount || '0')
    }, 0)
  }

  const getAccountName = (accountId: string) => {
    const account = accounts.find((a) => a.id === accountId)
    return account ? `${account.account_number} - ${account.account_name}` : accountId
  }

  const accountOptions = [
    { value: '', label: 'Select an account' },
    ...accounts.map((account) => ({
      value: account.id,
      label: `${account.account_number} - ${account.account_name}`,
    })),
  ]

  if (loading) {
    return <div className="text-center py-8">Loading accounts...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Budget Lines</h2>
        <p className="text-sm text-gray-600 mb-6">
          Add line items for each account you want to budget for.
        </p>
      </div>

      {/* Add Line Form */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Add Budget Line</h3>

        {errors && (
          <div className="mb-4 text-sm text-red-600">{errors}</div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-12">
          <div className="sm:col-span-6">
            <Select
              value={selectedAccount}
              onChange={(e) => {
                setSelectedAccount(e.target.value)
                setErrors(null)
              }}
              options={accountOptions}
            />
          </div>

          <div className="sm:col-span-3">
            <Input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => {
                setAmount(e.target.value)
                setErrors(null)
              }}
              placeholder="Amount"
            />
          </div>

          <div className="sm:col-span-3">
            <Button
              onClick={handleAddLine}
              className="w-full"
              variant="secondary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Line
            </Button>
          </div>
        </div>

        <div className="mt-3">
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notes (optional)"
          />
        </div>
      </div>

      {/* Budget Lines List */}
      {data.lines.length > 0 ? (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Account
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Budgeted Amount
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Notes
                </th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.lines.map((line, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {getAccountName(line.account)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                    {formatCurrency(line.budgeted_amount)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {line.notes || '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleRemoveLine(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                  Total Budgeted
                </td>
                <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                  {formatCurrency(getTotalBudgeted())}
                </td>
                <td colSpan={2}></td>
              </tr>
            </tfoot>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
          <p className="text-sm text-gray-500">
            No budget lines added yet. Use the form above to add your first line item.
          </p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-6 border-t">
        <Button onClick={onBack} variant="outline">
          ← Back
        </Button>
        <Button onClick={handleNext}>
          Continue to Review →
        </Button>
      </div>
    </div>
  )
}
