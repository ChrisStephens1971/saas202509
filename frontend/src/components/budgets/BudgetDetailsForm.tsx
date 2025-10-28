import React, { useState, useEffect } from 'react'
import { budgetsApi } from '../../api/budgets'
import type { Fund } from '../../types/api'
import { Input } from '../ui/Input'
import { Select } from '../ui/Select'
import { Button } from '../ui/Button'

interface BudgetDetailsFormProps {
  data: {
    name: string
    fiscal_year: number
    start_date: string
    end_date: string
    fund: string
    notes: string
  }
  onUpdate: (data: any) => void
  onNext: () => void
  onCancel: () => void
}

export const BudgetDetailsForm: React.FC<BudgetDetailsFormProps> = ({
  data,
  onUpdate,
  onNext,
  onCancel,
}) => {
  const [funds, setFunds] = useState<Fund[]>([])
  const [loading, setLoading] = useState(true)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    loadFunds()
  }, [])

  const loadFunds = async () => {
    try {
      const fundsData = await budgetsApi.getFunds()
      setFunds(fundsData)
    } catch (err) {
      console.error('Failed to load funds:', err)
    } finally {
      setLoading(false)
    }
  }

  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!data.name.trim()) {
      newErrors.name = 'Budget name is required'
    }

    if (!data.fiscal_year) {
      newErrors.fiscal_year = 'Fiscal year is required'
    }

    if (!data.start_date) {
      newErrors.start_date = 'Start date is required'
    }

    if (!data.end_date) {
      newErrors.end_date = 'End date is required'
    }

    if (data.start_date && data.end_date && data.start_date >= data.end_date) {
      newErrors.end_date = 'End date must be after start date'
    }

    if (!data.fund) {
      newErrors.fund = 'Fund is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validate()) {
      onNext()
    }
  }

  const handleChange = (field: string, value: any) => {
    onUpdate({ [field]: value })
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  // Generate fiscal year options
  const currentYear = new Date().getFullYear()
  const fiscalYearOptions = Array.from({ length: 11 }, (_, i) => {
    const year = currentYear - 5 + i
    return { value: year.toString(), label: year.toString() }
  })

  const fundOptions = [
    { value: '', label: 'Select a fund' },
    ...funds.map((fund) => ({
      value: fund.id,
      label: fund.name,
    })),
  ]

  if (loading) {
    return <div className="text-center py-8">Loading funds...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Budget Details
        </h2>
        <p className="text-sm text-gray-600 mb-6">
          Enter the basic information for your budget.
        </p>
      </div>

      <Input
        label="Budget Name *"
        value={data.name}
        onChange={(e) => handleChange('name', e.target.value)}
        error={errors.name}
        placeholder="e.g., 2025 Operating Budget"
      />

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <Select
          label="Fiscal Year *"
          value={data.fiscal_year.toString()}
          onChange={(e) => handleChange('fiscal_year', parseInt(e.target.value))}
          options={fiscalYearOptions}
          error={errors.fiscal_year}
        />

        <Select
          label="Fund *"
          value={data.fund}
          onChange={(e) => handleChange('fund', e.target.value)}
          options={fundOptions}
          error={errors.fund}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <Input
          label="Start Date *"
          type="date"
          value={data.start_date}
          onChange={(e) => handleChange('start_date', e.target.value)}
          error={errors.start_date}
        />

        <Input
          label="End Date *"
          type="date"
          value={data.end_date}
          onChange={(e) => handleChange('end_date', e.target.value)}
          error={errors.end_date}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={data.notes}
          onChange={(e) => handleChange('notes', e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Add any notes or comments about this budget..."
        />
      </div>

      <div className="flex justify-between pt-6 border-t">
        <Button onClick={onCancel} variant="outline">
          Cancel
        </Button>
        <Button onClick={handleNext}>
          Continue to Line Items →
        </Button>
      </div>
    </div>
  )
}
