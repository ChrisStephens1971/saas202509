import { Layout } from '../components/layout/Layout'
import { CashPositionCard } from '../components/dashboard/CashPositionCard'
import { ARAgingCard } from '../components/dashboard/ARAgingCard'
import { ExpensesCard } from '../components/dashboard/ExpensesCard'
import { RevenueCard } from '../components/dashboard/RevenueCard'
import { RevenueVsExpensesChart } from '../components/dashboard/RevenueVsExpensesChart'
import { FundBalancesChart } from '../components/dashboard/FundBalancesChart'
import { RecentActivityList } from '../components/dashboard/RecentActivityList'

export function DashboardPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500">Sunset Hills HOA</p>
        </div>

        {/* Financial Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <CashPositionCard />
          <ARAgingCard />
          <ExpensesCard />
          <RevenueCard />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RevenueVsExpensesChart />
          <FundBalancesChart />
        </div>

        {/* Recent Activity */}
        <RecentActivityList />
      </div>
    </Layout>
  )
}
