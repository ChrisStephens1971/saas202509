import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../ui/Button'
import { Home, FileText, DollarSign, BookOpen, Wallet, LogOut, RefreshCw } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-primary-600">HOA Accounting</span>
              </div>
              <div className="ml-10 flex space-x-4">
                <Link to="/dashboard" className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600">
                  <Home className="w-4 h-4 mr-2" />
                  Dashboard
                </Link>
                <Link to="/invoices" className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600">
                  <FileText className="w-4 h-4 mr-2" />
                  Invoices
                </Link>
                <Link to="/payments" className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600">
                  <DollarSign className="w-4 h-4 mr-2" />
                  Payments
                </Link>
                <Link to="/ledger" className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600">
                  <BookOpen className="w-4 h-4 mr-2" />
                  Ledger
                </Link>
                <Link to="/budgets" className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600">
                  <Wallet className="w-4 h-4 mr-2" />
                  Budgets
                </Link>
                <Link to="/reconciliation" className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reconciliation
                </Link>
              </div>
            </div>
            <div className="flex items-center">
              <Button onClick={handleLogout} variant="secondary" size="sm">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}
