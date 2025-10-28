# Sprint 10 - Frontend Enhancement

**Sprint Duration:** 2025-10-28 - 2025-11-08 (2 weeks)
**Sprint Goal:** Build comprehensive frontend UI for budget management, enhance dashboard, and create transaction matching interface
**Status:** 📋 Planning

---

## Sprint Goal

Transform the backend foundation into a production-ready user interface:

1. **Budget Management UI** - Complete React components for budget creation, editing, and variance reporting
2. **Enhanced Dashboard** - Real metrics, charts, and key financial indicators
3. **Transaction Matching UI** - Interface for reviewing and confirming bank transaction matches (prep for Plaid)
4. **UX Improvements** - Polish existing pages, add loading states, error handling, and responsive design

**Success Criteria:**
- Budget CRUD operations functional in UI
- Budget variance report with visual indicators
- Dashboard displays real-time financial metrics
- Transaction matching interface ready for Plaid integration
- All pages responsive and production-quality
- Loading states and error handling throughout

---

## Sprint Capacity

**Available Days:** 10 working days
**Capacity:** 60-80 hours
**Commitments/Time Off:** None planned
**Focus:** Frontend development, UI/UX polish

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1001 | Budget list page with filtering | M | 📋 Todo | Display all budgets, filter by year/fund/status |
| HOA-1002 | Budget creation form | L | 📋 Todo | Multi-step wizard: details → line items → review |
| HOA-1003 | Budget variance report UI | L | 📋 Todo | Table + charts showing budget vs actual |
| HOA-1004 | Dashboard financial summary | M | 📋 Todo | Key metrics: cash position, AR aging, expenses |
| HOA-1005 | Dashboard charts/graphs | M | 📋 Todo | Revenue vs expenses, fund balances over time |
| HOA-1006 | Transaction matching page | L | 📋 Todo | Review queue for bank transactions |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1007 | Budget approval workflow UI | M | 📋 Todo | Review → approve/reject with comments |
| HOA-1008 | Enhanced invoice list page | M | 📋 Todo | Better filters, bulk actions, export |
| HOA-1009 | Payment detail modal | S | 📋 Todo | Show full payment info with ledger entries |
| HOA-1010 | Loading states & skeletons | S | 📋 Todo | Replace spinners with skeleton screens |
| HOA-1011 | Error boundary & error pages | S | 📋 Todo | 404, 500, network error handling |
| HOA-1012 | Responsive design audit | M | 📋 Todo | Test all pages on mobile/tablet |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1013 | Dark mode support | M | 📋 Todo | Theme switcher with persistence |
| HOA-1014 | Keyboard shortcuts | S | 📋 Todo | Power user navigation (?, /, Ctrl+K) |
| HOA-1015 | Export to Excel/PDF | M | 📋 Todo | Export reports and lists |
| HOA-1016 | Dashboard customization | L | 📋 Todo | Drag-drop widgets, save preferences |

---

## Feature 1: Budget Management UI

### Page: Budget List (`/budgets`)

**Components to Create:**
- `frontend/src/pages/BudgetsPage.tsx`
- `frontend/src/components/budgets/BudgetList.tsx`
- `frontend/src/components/budgets/BudgetFilters.tsx`
- `frontend/src/components/budgets/BudgetCard.tsx`

**Features:**
- List all budgets with status badges (Draft, Approved, Active, Closed)
- Filter by: fiscal year, fund, status
- Search by budget name
- Sort by: created date, fiscal year, name
- Quick actions: View, Edit, Delete, Approve
- Create new budget button (prominent CTA)

**UI Design:**
```
┌─────────────────────────────────────────────────────────┐
│ Budgets                                    + New Budget │
├─────────────────────────────────────────────────────────┤
│ Filters: [FY 2025 ▼] [All Funds ▼] [All Status ▼]     │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2025 Operating Budget          [Active]            │ │
│ │ FY 2025 | Operating Fund | $150,000 budgeted       │ │
│ │ Actual: $135,000 | Variance: +$15,000 (10%)        │ │
│ │ [View Report] [Edit] [••• More]                     │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2025 Reserve Budget            [Approved]          │ │
│ │ FY 2025 | Reserve Fund | $50,000 budgeted          │ │
│ │ Actual: $48,500 | Variance: +$1,500 (3%)           │ │
│ │ [Activate] [Edit] [••• More]                        │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**API Integration:**
- `GET /api/v1/accounting/budgets/` - Fetch list with filters
- `DELETE /api/v1/accounting/budgets/{id}/` - Delete budget

---

### Page: Budget Creation (`/budgets/new`)

**Components to Create:**
- `frontend/src/pages/BudgetCreatePage.tsx`
- `frontend/src/components/budgets/BudgetWizard.tsx`
- `frontend/src/components/budgets/BudgetDetailsForm.tsx`
- `frontend/src/components/budgets/BudgetLinesForm.tsx`
- `frontend/src/components/budgets/BudgetReview.tsx`

**Multi-Step Wizard:**

**Step 1: Budget Details**
- Name (e.g., "2025 Operating Budget")
- Fiscal Year (2025, 2026, etc.)
- Fund (Operating, Reserve, Special Assessment)
- Date Range (start_date, end_date)
- Notes

**Step 2: Budget Lines**
- Select accounts from chart of accounts
- Enter budgeted amounts for each account
- Add notes per line item
- Show running total
- Copy from previous year's budget (optional)

**Step 3: Review & Submit**
- Summary of budget details
- Table of all budget lines
- Total budgeted amount
- Option to save as Draft or submit for Approval

**UI Design (Step 2 - Budget Lines):**
```
┌─────────────────────────────────────────────────────────┐
│ Create Budget - Step 2 of 3: Budget Lines              │
├─────────────────────────────────────────────────────────┤
│ Budget: 2025 Operating Budget (Operating Fund)         │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Account                    Budgeted     Notes        │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ 5100 - Landscaping        $12,000.00   [✎ Edit]    │ │
│ │ 5200 - Pool Maintenance   $8,500.00    [✎ Edit]    │ │
│ │ 5300 - Insurance          $15,000.00   [✎ Edit]    │ │
│ │ 5400 - Management Fees    $24,000.00   [✎ Edit]    │ │
│ │                                                      │ │
│ │ [+ Add Budget Line]                                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Total Budgeted: $59,500.00                              │
│                                                          │
│ [← Back] [Copy from Previous Year] [Continue →]        │
└─────────────────────────────────────────────────────────┘
```

**API Integration:**
- `GET /api/v1/accounting/accounts/` - Fetch chart of accounts
- `GET /api/v1/accounting/budgets/?fiscal_year={year-1}` - Get previous year for copying
- `POST /api/v1/accounting/budgets/` - Create budget with lines

---

### Page: Budget Variance Report (`/budgets/{id}/variance`)

**Components to Create:**
- `frontend/src/pages/BudgetVariancePage.tsx`
- `frontend/src/components/budgets/VarianceTable.tsx`
- `frontend/src/components/budgets/VarianceChart.tsx`
- `frontend/src/components/budgets/VarianceSummary.tsx`

**Features:**
- Budget header with name, period, fund
- Summary cards: Total Budgeted, Total Actual, Total Variance
- Table of budget lines with variance calculations
- Visual indicators: 🟢 favorable, 🔴 unfavorable
- Variance percentage with color coding
- Filter by account category (Revenue, Expenses)
- Export to Excel/PDF
- Date range filter (YTD, Q1, Q2, Custom)

**UI Design:**
```
┌─────────────────────────────────────────────────────────┐
│ Budget Variance Report                                   │
│ 2025 Operating Budget | Operating Fund                   │
│ Period: 2025-01-01 to 2025-10-28                        │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│ │ Budgeted │ │  Actual  │ │ Variance │                 │
│ │$150,000  │ │ $135,000 │ │ +$15,000 │                 │
│ │          │ │          │ │   10% 🟢 │                 │
│ └──────────┘ └──────────┘ └──────────┘                 │
├─────────────────────────────────────────────────────────┤
│ Account               Budgeted   Actual    Variance     │
├─────────────────────────────────────────────────────────┤
│ 5100 - Landscaping    $12,000   $10,500   +$1,500 🟢   │
│ 5200 - Pool Maint     $8,500    $9,200    -$700 🔴     │
│ 5300 - Insurance      $15,000   $15,000   $0           │
│ 5400 - Mgmt Fees      $24,000   $24,000   $0           │
│ ...                                                      │
├─────────────────────────────────────────────────────────┤
│ [Export] [Print] [Change Date Range]                    │
└─────────────────────────────────────────────────────────┘
```

**API Integration:**
- `GET /api/v1/accounting/budgets/{id}/` - Fetch budget details
- `GET /api/v1/accounting/budgets/{id}/variance-report/?start_date=X&end_date=Y` - Variance data

**Chart Visualization:**
- Bar chart: Budgeted vs Actual by category
- Pie chart: Expense breakdown
- Line chart: Actual expenses over time vs budget trend

---

## Feature 2: Enhanced Dashboard

### Page: Dashboard (`/dashboard`)

**Components to Create:**
- `frontend/src/pages/DashboardPage.tsx` (refactor existing)
- `frontend/src/components/dashboard/FinancialSummary.tsx`
- `frontend/src/components/dashboard/CashPositionCard.tsx`
- `frontend/src/components/dashboard/ARAgingCard.tsx`
- `frontend/src/components/dashboard/ExpensesCard.tsx`
- `frontend/src/components/dashboard/RevenueVsExpensesChart.tsx`
- `frontend/src/components/dashboard/FundBalancesChart.tsx`
- `frontend/src/components/dashboard/RecentActivityList.tsx`

**Key Metrics to Display:**

1. **Cash Position**
   - Total cash across all funds
   - Operating fund balance
   - Reserve fund balance
   - Special assessment balance
   - Trend indicator (↑ or ↓ from last month)

2. **Accounts Receivable**
   - Total AR outstanding
   - Current (0-30 days)
   - 30-60 days
   - 60-90 days
   - 90+ days (critical)

3. **Expenses (MTD/YTD)**
   - Total expenses this month
   - Total expenses year-to-date
   - Top 3 expense categories
   - Budget vs actual indicator

4. **Revenue (MTD/YTD)**
   - Total revenue this month
   - Total revenue year-to-date
   - Assessment collection rate
   - Outstanding assessments

**UI Design:**
```
┌─────────────────────────────────────────────────────────┐
│ Dashboard - Sunset Hills HOA                            │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ Cash     │ │ Total AR │ │ MTD Exp  │ │ MTD Rev  │   │
│ │ $85,500  │ │ $12,300  │ │ $18,500  │ │ $42,000  │   │
│ │ ↑ 5.2%   │ │ 45 days  │ │ ↓ 8%     │ │ ↑ 2%     │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│ ┌────────────────────────┐ ┌─────────────────────────┐ │
│ │ Revenue vs Expenses    │ │ AR Aging                │ │
│ │ [Line Chart]           │ │ [Donut Chart]           │ │
│ │                        │ │ Current: 60%            │ │
│ │                        │ │ 30-60: 25%              │ │
│ │                        │ │ 60-90: 10%              │ │
│ │                        │ │ 90+: 5% 🔴             │ │
│ └────────────────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Recent Activity                                          │
│ • Invoice #1025 created for Unit 42A ($350.00)         │
│ • Payment received from Unit 15B ($350.00)              │
│ • Budget variance report generated                       │
│ • Late fee applied to Unit 8C ($25.00)                  │
└─────────────────────────────────────────────────────────┘
```

**API Endpoints Needed:**
- `GET /api/v1/accounting/dashboard/cash-position/` - Fund balances
- `GET /api/v1/accounting/dashboard/ar-aging/` - AR aging buckets
- `GET /api/v1/accounting/dashboard/expenses/?period=mtd` - Expense summary
- `GET /api/v1/accounting/dashboard/revenue/?period=mtd` - Revenue summary
- `GET /api/v1/accounting/dashboard/recent-activity/` - Last 10 activities

**Chart Library:**
- Install Recharts or Chart.js
- Responsive charts with hover tooltips
- Export chart as PNG

---

## Feature 3: Transaction Matching UI

### Page: Transaction Matching (`/transactions/matching`)

**Components to Create:**
- `frontend/src/pages/TransactionMatchingPage.tsx`
- `frontend/src/components/transactions/MatchingQueue.tsx`
- `frontend/src/components/transactions/TransactionCard.tsx`
- `frontend/src/components/transactions/MatchSuggestions.tsx`
- `frontend/src/components/transactions/ManualMatchModal.tsx`

**Features:**
- List of unmatched bank transactions
- For each transaction, show suggested matches
- Confidence score indicator (High, Medium, Low)
- Quick confirm/reject actions
- Manual match search and selection
- Bulk actions: Confirm all high-confidence matches
- Filter by: date range, amount range, match status

**UI Design:**
```
┌─────────────────────────────────────────────────────────┐
│ Transaction Matching                                     │
│ 15 transactions need review                             │
├─────────────────────────────────────────────────────────┤
│ [Confirm All High Confidence] [Filter ▼]                │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Bank Transaction                                    │ │
│ │ Oct 15, 2025 | $350.00 | ACH from John Smith       │ │
│ │ Operating Account • 4567                            │ │
│ │                                                      │ │
│ │ Suggested Match: 🟢 High Confidence (95%)           │ │
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │ Payment #1025 - Unit 42A (John Smith)          │ │ │
│ │ │ Oct 15, 2025 | $350.00 | Invoice #890          │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ │                                                      │ │
│ │ [✓ Confirm Match] [✗ Reject] [🔍 Search Other]     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Bank Transaction                                    │ │
│ │ Oct 18, 2025 | $125.00 | Check #4892                │ │
│ │ Operating Account • 4567                            │ │
│ │                                                      │ │
│ │ No matches found 🔴                                  │ │
│ │                                                      │ │
│ │ [🔍 Manual Search] [Create New Payment]             │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**API Endpoints (to be created in future sprint):**
- `GET /api/v1/accounting/bank-transactions/unmatched/` - List unmatched
- `GET /api/v1/accounting/bank-transactions/{id}/suggestions/` - Get match suggestions
- `POST /api/v1/accounting/bank-transactions/{id}/match/` - Confirm match
- `POST /api/v1/accounting/bank-transactions/{id}/reject/` - Reject suggestion

**Note:** This feature prepares the UI for Plaid integration in a future sprint. For now, we'll create the components with mock data structure.

---

## Feature 4: UX Improvements

### Loading States

**Replace all loading spinners with skeleton screens:**
- Budget list → Skeleton cards
- Dashboard → Skeleton metric cards + chart placeholders
- Invoice list → Skeleton table rows
- Payment forms → Skeleton form fields

**Library:** Use shadcn/ui Skeleton component

### Error Handling

**Create comprehensive error handling:**
- Network errors → "Unable to connect" message with retry button
- 404 → Custom 404 page with navigation
- 500 → Custom 500 page with "Report Issue" button
- Form validation errors → Inline error messages with red borders
- API errors → Toast notifications with actionable messages

**Components:**
- `frontend/src/components/errors/ErrorBoundary.tsx`
- `frontend/src/pages/NotFoundPage.tsx`
- `frontend/src/pages/ServerErrorPage.tsx`
- `frontend/src/components/common/Toast.tsx`

### Responsive Design

**Test all pages on:**
- Desktop (1920x1080, 1366x768)
- Tablet (iPad: 768x1024)
- Mobile (iPhone: 375x667, 414x896)

**Key Adjustments:**
- Collapse navigation to hamburger menu on mobile
- Stack dashboard cards vertically on mobile
- Make tables horizontally scrollable on mobile
- Adjust chart sizes for smaller screens
- Larger touch targets (48x48px minimum)

### Accessibility

**WCAG 2.1 AA Compliance:**
- All interactive elements keyboard accessible
- Focus indicators visible
- Color contrast ratio ≥ 4.5:1
- Alt text for all images
- ARIA labels for icon buttons
- Form labels properly associated

---

## Technical Architecture

### Frontend Stack

**Core:**
- React 18.2+ with TypeScript
- Vite for build tooling
- React Router v6 for routing

**UI Components:**
- Tailwind CSS for styling
- shadcn/ui for component library
- Radix UI primitives (headless components)

**Charts:**
- Recharts (recommended) or Chart.js
- Responsive and accessible

**State Management:**
- React Context for global state (auth, tenant)
- React Query (TanStack Query) for server state
- Zustand for complex client state (optional)

**Forms:**
- React Hook Form for form management
- Zod for schema validation

**API Client:**
- Axios with interceptors for auth tokens
- Request/response logging in dev mode

### Project Structure

```
frontend/src/
├── components/
│   ├── budgets/
│   │   ├── BudgetList.tsx
│   │   ├── BudgetCard.tsx
│   │   ├── BudgetWizard.tsx
│   │   ├── BudgetDetailsForm.tsx
│   │   ├── BudgetLinesForm.tsx
│   │   ├── BudgetReview.tsx
│   │   ├── VarianceTable.tsx
│   │   └── VarianceChart.tsx
│   ├── dashboard/
│   │   ├── FinancialSummary.tsx
│   │   ├── CashPositionCard.tsx
│   │   ├── ARAgingCard.tsx
│   │   ├── ExpensesCard.tsx
│   │   ├── RevenueVsExpensesChart.tsx
│   │   └── FundBalancesChart.tsx
│   ├── transactions/
│   │   ├── MatchingQueue.tsx
│   │   ├── TransactionCard.tsx
│   │   └── MatchSuggestions.tsx
│   ├── common/
│   │   ├── Skeleton.tsx
│   │   ├── Toast.tsx
│   │   └── ErrorMessage.tsx
│   └── errors/
│       └── ErrorBoundary.tsx
├── pages/
│   ├── DashboardPage.tsx
│   ├── BudgetsPage.tsx
│   ├── BudgetCreatePage.tsx
│   ├── BudgetVariancePage.tsx
│   ├── TransactionMatchingPage.tsx
│   ├── NotFoundPage.tsx
│   └── ServerErrorPage.tsx
├── api/
│   ├── client.ts (Axios instance)
│   ├── budgets.ts
│   ├── dashboard.ts
│   └── transactions.ts
├── hooks/
│   ├── useBudgets.ts
│   ├── useDashboard.ts
│   └── useTransactions.ts
├── types/
│   ├── budget.ts
│   ├── dashboard.ts
│   └── transaction.ts
└── utils/
    ├── formatters.ts (currency, date)
    └── validators.ts
```

---

## Dependencies to Install

```bash
cd frontend

# Charts
npm install recharts

# Forms & Validation
npm install react-hook-form zod @hookform/resolvers

# Date handling
npm install date-fns

# State management (if needed)
npm install @tanstack/react-query zustand

# Additional shadcn/ui components
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add select
npx shadcn-ui@latest add calendar
npx shadcn-ui@latest add form
```

---

## Backend API Endpoints Needed

Most budget endpoints already exist from Sprint 9. Need to add dashboard endpoints:

**New Endpoints to Create:**
```python
# In backend/accounting/api_views.py

class DashboardViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def cash_position(self, request):
        # Return fund balances
        pass

    @action(detail=False, methods=['get'])
    def ar_aging(self, request):
        # Return AR aging buckets
        pass

    @action(detail=False, methods=['get'])
    def expenses(self, request):
        # Return expense summary (MTD/YTD)
        pass

    @action(detail=False, methods=['get'])
    def revenue(self, request):
        # Return revenue summary (MTD/YTD)
        pass

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        # Return last 10-20 activities
        pass
```

**Routes:**
```python
# In backend/accounting/urls.py
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
```

---

## Testing Strategy

### Unit Tests
- Component tests with React Testing Library
- Test user interactions (clicks, form submissions)
- Test conditional rendering
- Test error states

### Integration Tests
- API integration tests with MSW (Mock Service Worker)
- Test complete user flows
- Test error handling and retries

### E2E Tests (Future)
- Playwright or Cypress
- Critical user journeys:
  - Create budget → Add lines → Submit
  - View variance report → Export
  - Match bank transaction → Confirm

### Manual Testing Checklist
- [ ] Budget wizard completes successfully
- [ ] Variance report displays correct calculations
- [ ] Dashboard metrics match backend data
- [ ] All pages responsive on mobile/tablet
- [ ] Loading states appear during data fetching
- [ ] Error messages display appropriately
- [ ] Form validation works correctly
- [ ] Navigation works across all pages

---

## Scope Changes

*Document any stories added or removed during the sprint*

| Date | Change | Reason |
|------|--------|--------|
| - | - | - |

---

## Daily Progress

### Day 1 - [Date]
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 2 - [Date]
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 3 - [Date]
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

## Sprint Metrics

### Planned vs Actual
- **Planned:** 16 stories (6 high + 6 medium + 4 low)
- **Completed:** TBD
- **Completion Rate:** TBD

### Velocity
- **Previous Sprint (9):** 4 stories completed in 1 day
- **This Sprint:** TBD
- **Trend:** TBD

---

## Wins & Learnings

### What Went Well
- TBD

### What Could Be Improved
- TBD

### Action Items for Next Sprint
- [ ] TBD

---

## Sprint Review Notes

**What We Shipped:**
- TBD

**Demo Notes:**
- TBD

**Feedback Received:**
- TBD

---

## Next Steps (Sprint 11)

Potential priorities for Sprint 11:
1. Plaid integration (if API credentials obtained)
2. Reserve planning module
3. Email notification preferences UI
4. Advanced reporting features
5. Multi-tenant admin panel
6. Mobile-specific optimizations

---

## Links & References

- **Related Sprints:**
  - Sprint 9: Automation and Banking (backend budget module)
  - Sprint 7: Frontend Dashboard (initial dashboard setup)
  - Sprint 8: Frontend Enhancements (auth and navigation)

- **Documentation:**
  - Budget API: `backend/accounting/api_views.py` (lines 16,000-19,358)
  - Budget Models: `backend/accounting/models.py` (Budget, BudgetLine)
  - shadcn/ui Docs: https://ui.shadcn.com/

- **Design References:**
  - TBD (if using Figma/Sketch mockups)

---

**Sprint 10 Status:** 📋 Planning
**Estimated Completion:** 2025-11-08
