import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { budgetsApi } from '../api/budgets'
import type { CreateBudgetRequest } from '../types/api'
import { BudgetDetailsForm } from '../components/budgets/BudgetDetailsForm'
import { BudgetLinesForm } from '../components/budgets/BudgetLinesForm'
import { BudgetReview } from '../components/budgets/BudgetReview'

type WizardStep = 1 | 2 | 3

interface BudgetFormData {
  name: string
  fiscal_year: number
  start_date: string
  end_date: string
  fund: string
  notes: string
  status: 'draft' | 'approved'
  lines: Array<{
    account: string
    budgeted_amount: string
    notes?: string
  }>
}

export const BudgetCreatePage: React.FC = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<WizardStep>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<BudgetFormData>({
    name: '',
    fiscal_year: new Date().getFullYear(),
    start_date: '',
    end_date: '',
    fund: '',
    notes: '',
    status: 'draft',
    lines: [],
  })

  const updateFormData = (data: Partial<BudgetFormData>) => {
    setFormData((prev) => ({ ...prev, ...data }))
  }

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep((prev) => (prev + 1) as WizardStep)
      window.scrollTo(0, 0)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as WizardStep)
      window.scrollTo(0, 0)
    }
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      setError(null)

      const budgetData: CreateBudgetRequest = {
        name: formData.name,
        fiscal_year: formData.fiscal_year,
        start_date: formData.start_date,
        end_date: formData.end_date,
        fund: formData.fund,
        notes: formData.notes,
        status: formData.status,
        lines: formData.lines,
      }

      await budgetsApi.createBudget(budgetData)
      navigate('/budgets')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create budget')
      setLoading(false)
    }
  }

  const getStepTitle = () => {
    switch (currentStep) {
      case 1:
        return 'Budget Details'
      case 2:
        return 'Budget Lines'
      case 3:
        return 'Review & Submit'
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create Budget</h1>
        <p className="mt-2 text-sm text-gray-600">
          Step {currentStep} of 3: {getStepTitle()}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {[1, 2, 3].map((step) => (
            <div
              key={step}
              className={`flex-1 ${step !== 3 ? 'mr-2' : ''}`}
            >
              <div
                className={`h-2 rounded-full ${
                  step <= currentStep ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-gray-600">
          <span>Details</span>
          <span>Line Items</span>
          <span>Review</span>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {currentStep === 1 && (
          <BudgetDetailsForm
            data={formData}
            onUpdate={updateFormData}
            onNext={handleNext}
            onCancel={() => navigate('/budgets')}
          />
        )}

        {currentStep === 2 && (
          <BudgetLinesForm
            data={formData}
            onUpdate={updateFormData}
            onNext={handleNext}
            onBack={handleBack}
          />
        )}

        {currentStep === 3 && (
          <BudgetReview
            data={formData}
            onSubmit={handleSubmit}
            onBack={handleBack}
            loading={loading}
          />
        )}
      </div>
    </div>
  )
}
