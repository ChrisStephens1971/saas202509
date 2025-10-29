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
import { BankReconciliationPage } from './pages/BankReconciliationPage'
import { ReconciliationDetailPage } from './pages/ReconciliationDetailPage'
import { FundsPage } from './pages/FundsPage'
import ReserveStudiesPage from './pages/ReserveStudiesPage'
import CustomReportsPage from './pages/CustomReportsPage'
import DelinquencyDashboardPage from './pages/DelinquencyDashboardPage'
import LateFeeRulesPage from './pages/LateFeeRulesPage'
import CollectionNoticesPage from './pages/CollectionNoticesPage'
import CollectionActionsPage from './pages/CollectionActionsPage'
import TransactionMatchingPage from './pages/TransactionMatchingPage'
import MatchRulesPage from './pages/MatchRulesPage'
import MatchStatisticsPage from './pages/MatchStatisticsPage'
import ViolationsPage from './pages/ViolationsPage'
import BoardPacketsPage from './pages/BoardPacketsPage'

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

          <Route
            path="/reconciliation"
            element={
              <ProtectedRoute>
                <BankReconciliationPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/reconciliation/:id"
            element={
              <ProtectedRoute>
                <ReconciliationDetailPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/funds"
            element={
              <ProtectedRoute>
                <FundsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/reserve-studies"
            element={
              <ProtectedRoute>
                <ReserveStudiesPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <CustomReportsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/delinquency"
            element={
              <ProtectedRoute>
                <DelinquencyDashboardPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/late-fees"
            element={
              <ProtectedRoute>
                <LateFeeRulesPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/collection-notices"
            element={
              <ProtectedRoute>
                <CollectionNoticesPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/collection-actions"
            element={
              <ProtectedRoute>
                <CollectionActionsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/matching"
            element={
              <ProtectedRoute>
                <TransactionMatchingPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/match-rules"
            element={
              <ProtectedRoute>
                <MatchRulesPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/match-statistics"
            element={
              <ProtectedRoute>
                <MatchStatisticsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/violations"
            element={
              <ProtectedRoute>
                <ViolationsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/board-packets"
            element={
              <ProtectedRoute>
                <BoardPacketsPage />
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
