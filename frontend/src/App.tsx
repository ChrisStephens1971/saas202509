import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { InvoicesPage } from './pages/InvoicesPage'
import { PaymentsPage } from './pages/PaymentsPage'
import { OwnerLedgerPage } from './pages/OwnerLedgerPage'
import { BudgetsPage } from './pages/BudgetsPage'
import { BudgetCreatePage } from './pages/BudgetCreatePage'
import { BudgetVariancePage } from './pages/BudgetVariancePage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/invoices"
            element={
              <ProtectedRoute>
                <InvoicesPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/payments"
            element={
              <ProtectedRoute>
                <PaymentsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/ledger"
            element={
              <ProtectedRoute>
                <OwnerLedgerPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/budgets"
            element={
              <ProtectedRoute>
                <BudgetsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/budgets/new"
            element={
              <ProtectedRoute>
                <BudgetCreatePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/budgets/:id/variance"
            element={
              <ProtectedRoute>
                <BudgetVariancePage />
              </ProtectedRoute>
            }
          />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
