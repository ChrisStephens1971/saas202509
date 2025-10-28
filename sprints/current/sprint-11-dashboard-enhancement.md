# Sprint 11 - Dashboard Enhancement

**Sprint Duration:** 2025-10-28 (1 day sprint)
**Sprint Goal:** Transform dashboard from static mockup to live data-driven interface with real metrics and charts
**Status:** 🏗️ In Progress

---

## Sprint Goal

Build a production-ready dashboard that displays real-time financial metrics from the backend:

1. **Financial Summary Cards** - Cash position, AR aging, expenses, revenue (MTD/YTD)
2. **Revenue vs Expenses Chart** - Line chart showing monthly trends
3. **Fund Balances Chart** - Pie chart showing fund distribution
4. **AR Aging Visualization** - Donut chart with aging buckets
5. **Recent Activity Feed** - Last 10-20 transactions/events

**Success Criteria:**
- Dashboard loads real data from backend APIs
- All metrics update dynamically
- Charts render correctly with actual data
- Loading states implemented
- Error handling for failed requests
- Responsive design on all screen sizes

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1101 | Backend dashboard API endpoints | M | 📋 Todo | 5 endpoints for metrics |
| HOA-1102 | Cash position summary card | S | 📋 Todo | All funds + trend indicator |
| HOA-1103 | AR aging summary card | S | 📋 Todo | Buckets: 0-30, 30-60, 60-90, 90+ |
| HOA-1104 | MTD/YTD expenses card | S | 📋 Todo | Current month + year to date |
| HOA-1105 | MTD/YTD revenue card | S | 📋 Todo | Current month + year to date |
| HOA-1106 | Revenue vs Expenses chart | M | 📋 Todo | Line chart, last 12 months |
| HOA-1107 | Fund balances pie chart | S | 📋 Todo | Operating, Reserve, Special |
| HOA-1108 | AR aging donut chart | S | 📋 Todo | Visual aging breakdown |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1109 | Recent activity feed | M | 📋 Todo | Last 10 events with timestamps |
| HOA-1110 | Dashboard API client | S | 📋 Todo | Frontend API integration |
| HOA-1111 | Loading skeletons | S | 📋 Todo | Skeleton screens for all cards |
| HOA-1112 | Error boundaries | S | 📋 Todo | Graceful error handling |
| HOA-1113 | Responsive grid layout | S | 📋 Todo | Mobile/tablet optimization |

---

## Backend API Implementation

### Dashboard Endpoints to Create

**File:** `backend/accounting/api_views.py`

```python
class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def cash_position(self, request):
        """Get current cash balances across all funds"""
        # Return fund balances with trend data
        pass

    @action(detail=False, methods=['get'])
    def ar_aging(self, request):
        """Get AR aging buckets"""
        # Return: current, 30-60, 60-90, 90+ days
        pass

    @action(detail=False, methods=['get'])
    def expenses(self, request):
        """Get expense summary (MTD/YTD)"""
        # Query params: period=mtd|ytd
        pass

    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue summary (MTD/YTD)"""
        # Query params: period=mtd|ytd
        pass

    @action(detail=False, methods=['get'])
    def revenue_vs_expenses(self, request):
        """Get monthly revenue vs expenses for charting"""
        # Return: last 12 months of data
        pass

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent activity log"""
        # Return: last 10-20 events
        pass
```

### API Response Formats

**Cash Position:**
```json
{
  "total_cash": "85500.00",
  "funds": [
    {
      "name": "Operating Fund",
      "balance": "45000.00",
      "trend": 5.2
    },
    {
      "name": "Reserve Fund",
      "balance": "35000.00",
      "trend": 2.1
    },
    {
      "name": "Special Assessment",
      "balance": "5500.00",
      "trend": -1.5
    }
  ]
}
```

**AR Aging:**
```json
{
  "total_ar": "12300.00",
  "average_days": 45,
  "buckets": {
    "current": {
      "amount": "7380.00",
      "percentage": 60,
      "count": 15
    },
    "days_30_60": {
      "amount": "3075.00",
      "percentage": 25,
      "count": 8
    },
    "days_60_90": {
      "amount": "1230.00",
      "percentage": 10,
      "count": 3
    },
    "days_over_90": {
      "amount": "615.00",
      "percentage": 5,
      "count": 2
    }
  }
}
```

**Expenses (MTD/YTD):**
```json
{
  "period": "mtd",
  "total": "18500.00",
  "comparison": {
    "previous_period": "20100.00",
    "change_pct": -8.0
  },
  "top_categories": [
    {
      "category": "Landscaping",
      "amount": "4500.00"
    },
    {
      "category": "Pool Maintenance",
      "amount": "3200.00"
    },
    {
      "category": "Management Fees",
      "amount": "2400.00"
    }
  ]
}
```

**Revenue vs Expenses (12 months):**
```json
{
  "months": [
    {
      "month": "2024-11",
      "revenue": "42000.00",
      "expenses": "18500.00"
    },
    {
      "month": "2024-12",
      "revenue": "42000.00",
      "expenses": "19200.00"
    },
    // ... 10 more months
  ]
}
```

---

## Frontend Components

### Dashboard API Client

**File:** `frontend/src/api/dashboard.ts`

```typescript
export const dashboardApi = {
  getCashPosition: async () => {
    const response = await client.get('/api/v1/accounting/dashboard/cash-position/')
    return response.data
  },

  getARAging: async () => {
    const response = await client.get('/api/v1/accounting/dashboard/ar-aging/')
    return response.data
  },

  getExpenses: async (period: 'mtd' | 'ytd') => {
    const response = await client.get('/api/v1/accounting/dashboard/expenses/', {
      params: { period }
    })
    return response.data
  },

  getRevenue: async (period: 'mtd' | 'ytd') => {
    const response = await client.get('/api/v1/accounting/dashboard/revenue/', {
      params: { period }
    })
    return response.data
  },

  getRevenueVsExpenses: async () => {
    const response = await client.get('/api/v1/accounting/dashboard/revenue-vs-expenses/')
    return response.data
  },

  getRecentActivity: async () => {
    const response = await client.get('/api/v1/accounting/dashboard/recent-activity/')
    return response.data
  }
}
```

### Component Structure

```
frontend/src/components/dashboard/
├── CashPositionCard.tsx       - Total cash + fund breakdown
├── ARAgingCard.tsx            - AR summary + aging buckets
├── ExpensesCard.tsx           - MTD/YTD expenses
├── RevenueCard.tsx            - MTD/YTD revenue
├── RevenueVsExpensesChart.tsx - Line chart (12 months)
├── FundBalancesChart.tsx      - Pie chart
├── ARAgingChart.tsx           - Donut chart (existing)
└── RecentActivityList.tsx     - Event feed
```

---

## UI Design

### Desktop Layout (1920x1080)

```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard - Sunset Hills HOA                   [Date Filter] │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ Cash     │ │ Total AR │ │ MTD Exp  │ │ MTD Rev  │       │
│ │ $85,500  │ │ $12,300  │ │ $18,500  │ │ $42,000  │       │
│ │ ↑ 5.2%   │ │ 45 days  │ │ ↓ 8%     │ │ ↑ 2%     │       │
│ │ Operating│ │ Current  │ │ vs Last  │ │ vs Last  │       │
│ │ Reserve  │ │ 30-60    │ │ Month    │ │ Month    │       │
│ │ Special  │ │ 60-90    │ │          │ │          │       │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────────────────┐ ┌─────────────────────────┐     │
│ │ Revenue vs Expenses    │ │ Fund Balances           │     │
│ │ [Line Chart]           │ │ [Pie Chart]             │     │
│ │ • Revenue line         │ │ • Operating: 52.6%      │     │
│ │ • Expenses line        │ │ • Reserve: 40.9%        │     │
│ │ • Last 12 months       │ │ • Special: 6.5%         │     │
│ └────────────────────────┘ └─────────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────────────────┐ ┌─────────────────────────┐     │
│ │ AR Aging               │ │ Recent Activity         │     │
│ │ [Donut Chart]          │ │ • Invoice #1025 created │     │
│ │ • Current: 60%         │ │ • Payment received 15B  │     │
│ │ • 30-60: 25%           │ │ • Budget report gen     │     │
│ │ • 60-90: 10%           │ │ • Late fee applied 8C   │     │
│ │ • 90+: 5% 🔴          │ │ • Invoice #1024 paid    │     │
│ └────────────────────────┘ └─────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout (375x667)

```
┌──────────────────┐
│ Dashboard        │
│ [Date: Oct 2025] │
├──────────────────┤
│ Cash: $85,500    │
│ ↑ 5.2%           │
├──────────────────┤
│ AR: $12,300      │
│ 45 days avg      │
├──────────────────┤
│ Expenses: $18,500│
│ ↓ 8% MTD         │
├──────────────────┤
│ Revenue: $42,000 │
│ ↑ 2% MTD         │
├──────────────────┤
│ [Revenue Chart]  │
│ [Fund Pie Chart] │
│ [AR Donut Chart] │
├──────────────────┤
│ Recent Activity  │
│ • Invoice #1025  │
│ • Payment 15B    │
│ • ...            │
└──────────────────┘
```

---

## Testing Plan

### Backend API Tests

1. **Test cash position endpoint**
   - Verify fund balances sum correctly
   - Test trend calculation
   - Test with no transactions

2. **Test AR aging endpoint**
   - Verify aging buckets calculated correctly
   - Test with overdue invoices
   - Test percentage calculations

3. **Test expense/revenue endpoints**
   - Verify MTD vs YTD calculations
   - Test period filtering
   - Test comparison calculations

4. **Test revenue vs expenses endpoint**
   - Verify monthly grouping
   - Test 12-month window
   - Test with sparse data

### Frontend Integration Tests

1. **Test dashboard loading states**
   - Verify skeletons display while loading
   - Test concurrent API calls
   - Test individual card failures

2. **Test chart rendering**
   - Verify charts render with real data
   - Test responsive behavior
   - Test empty data states

3. **Test error handling**
   - Verify error messages display
   - Test retry functionality
   - Test partial failures

### Manual Testing Checklist

- [ ] Dashboard loads within 3 seconds
- [ ] All metrics display real backend data
- [ ] Charts render correctly
- [ ] Clicking cards navigates to detail pages
- [ ] Refresh button reloads data
- [ ] Mobile layout works correctly
- [ ] Loading skeletons appear
- [ ] Error states handle gracefully

---

## Performance Considerations

### Backend Optimization

- Cache dashboard metrics for 5 minutes
- Use database indexes on frequently queried fields
- Limit recent activity to last 20 items
- Use select_related/prefetch_related for related queries

### Frontend Optimization

- Use React Query for caching and refetching
- Lazy load charts (code splitting)
- Debounce refresh requests
- Implement optimistic UI updates

---

## Dependencies

### Backend
- No new dependencies required
- Uses existing Django/DRF/PostgreSQL stack

### Frontend
- `recharts` - Already installed (Sprint 10)
- `@tanstack/react-query` - Already installed (Sprint 10)
- `date-fns` - Already installed (Sprint 10)

---

## Sprint Metrics

**Planned:**
- 13 stories (8 high + 5 medium)
- ~600 lines of backend code
- ~800 lines of frontend code
- 6 API endpoints
- 8 React components

**Timeline:**
- Backend API: 2-3 hours
- Frontend components: 3-4 hours
- Integration & testing: 1-2 hours
- **Total: 1 day sprint**

---

## Next Steps (Sprint 12)

Potential priorities for Sprint 12:
1. Transaction Matching UI (manual bank reconciliation)
2. Reserve Planning module (5-20 year forecasting)
3. Advanced reporting (custom report builder)
4. Email notification preferences UI
5. Mobile app foundation (React Native)
6. Multi-tenant admin panel

---

## Links & References

- **Related Sprints:**
  - Sprint 9: Automation and Banking (backend budget module)
  - Sprint 10: Frontend Enhancement (budget UI)
  - Sprint 7: Frontend Dashboard (initial mockup)

- **Documentation:**
  - Dashboard API: `backend/accounting/api_views.py`
  - Recharts docs: https://recharts.org/

---

**Sprint 11 Status:** 🏗️ In Progress
**Started:** 2025-10-28
**Target Completion:** 2025-10-28 (same day)
