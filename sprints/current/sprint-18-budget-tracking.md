# Sprint 18 - Budget vs Actual Tracking

**Sprint Duration:** TBD (2 weeks estimated)
**Sprint Goal:** Implement annual budget planning and variance tracking to monitor spending against approved budgets
**Status:** Planning

---

## Sprint Goal

Build a budget management system that enables HOAs to create annual operating budgets, track actual spending in real-time, and generate variance reports. This addresses a critical board need: financial control and accountability. Boards can answer "Are we overspending?" and "Why is landscaping 20% over budget?" with real data.

Key features:
- Annual budget creation by GL account
- Line-item budget per expense category
- Real-time actuals from general ledger
- Variance calculation (actual vs budget)
- Monthly/quarterly/annual reports
- Board approval workflow

---

## Sprint Capacity

**Available Days:** 10 working days
**Capacity:** 60-80 hours
**Commitments/Time Off:** None

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-191 | Backend: Budget models (Budget, BudgetLine, BudgetPeriod) | M | Chris | 📋 Todo | Core data models |
| US-192 | Backend: Budget API endpoints (CRUD) | M | Chris | 📋 Todo | REST API |
| US-193 | Backend: Variance calculation engine | L | Chris | 📋 Todo | Actual vs budget |
| US-194 | Frontend: Budget creation/edit page | L | Chris | 📋 Todo | Line-item input |
| US-195 | Frontend: Budget vs actual report page | M | Chris | 📋 Todo | Variance report |
| US-196 | Backend: Integration with GL for actuals | M | Chris | 📋 Todo | Real-time data |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-197 | Frontend: Budget variance chart (bar chart) | M | Chris | 📋 Todo | Visual variance |
| US-198 | Backend: Budget templates (copy from prior year) | S | Chris | 📋 Todo | Efficiency |
| US-199 | Frontend: Budget approval workflow | S | Chris | 📋 Todo | Board voting |
| US-200 | Email alerts for variance thresholds | S | Chris | 📋 Todo | Overspending alerts |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-201 | Budget forecasting (projected year-end) | M | Chris | 📋 Todo | Trend analysis |
| US-202 | Budget comparison (multi-year) | S | Chris | 📋 Todo | Historical view |
| US-203 | Export budget to Excel | S | Chris | 📋 Todo | Board reporting |

**Story Status Legend:**
- 📋 Todo
- 🏗️ In Progress
- 👀 In Review
- ✅ Done
- ❌ Blocked

---

## Technical Design

### Backend Models

**BudgetPeriod:**
- tenant: FK(Tenant)
- fiscal_year: int (e.g., 2025)
- start_date: DATE (e.g., 2025-01-01)
- end_date: DATE (e.g., 2025-12-31)
- status: str (Draft, Proposed, Approved, Active, Closed)
- total_revenue_budget: Decimal (sum of revenue line items)
- total_expense_budget: Decimal (sum of expense line items)
- approved_by: FK(User) (nullable)
- approved_at: TIMESTAMPTZ (nullable)
- notes: text

**Budget:**
- budget_period: FK(BudgetPeriod)
- fund: FK(Fund) (operating, reserve, special assessment)
- gl_account: FK(GLAccount)
- category: str (Revenue or Expense)
- annual_amount: Decimal (total for year)
- monthly_amount: Decimal (annual / 12, for even distribution)
- notes: text (explanation for this line item)

**BudgetActual (computed view, not stored):**
- budget: FK(Budget)
- period: str (Month, Quarter, or YTD)
- period_date: DATE (end of period)
- budgeted_amount: Decimal (from Budget)
- actual_amount: Decimal (from GL transactions)
- variance_amount: Decimal (actual - budgeted)
- variance_percent: Decimal ((actual - budgeted) / budgeted * 100)

**BudgetAlert:**
- budget: FK(Budget)
- threshold_percent: Decimal (e.g., 10% = alert when variance >10%)
- alert_triggered: bool
- triggered_at: TIMESTAMPTZ (nullable)
- notified_users: JSONB (list of user IDs notified)

### API Endpoints

**Budget Periods:**
- GET /api/budget-periods/ - List all budget periods
- POST /api/budget-periods/ - Create budget period
- GET /api/budget-periods/{id}/ - Get budget period detail
- PUT /api/budget-periods/{id}/ - Update budget period
- POST /api/budget-periods/{id}/approve/ - Approve budget
- POST /api/budget-periods/{id}/activate/ - Activate budget (becomes current)

**Budget Lines:**
- GET /api/budgets/?period={id}&fund={id} - List budget lines
- POST /api/budgets/ - Create budget line
- PUT /api/budgets/{id}/ - Update budget line
- DELETE /api/budgets/{id}/ - Delete budget line
- POST /api/budgets/bulk-import/ - Import budget from CSV/Excel
- POST /api/budgets/copy-from-prior-year/ - Copy and inflate

**Variance Reports:**
- GET /api/budget-actuals/?period={id}&date={YYYY-MM-DD} - Get variance report
- GET /api/budget-actuals/monthly/?period={id} - Monthly variance by account
- GET /api/budget-actuals/summary/?period={id} - Summary by category
- GET /api/budget-actuals/alerts/?period={id} - Over-budget alerts

### Frontend Pages

**BudgetPeriodsListPage:**
- List of all budget periods (fiscal years)
- Status badges (Draft, Approved, Active, Closed)
- Create new budget button
- Actions: Edit, Approve, Activate, View report

**BudgetCreateEditPage:**
- Fiscal year selection
- Fund selection (operating, reserve)
- Budget line items table (editable):
  - GL Account (dropdown with search)
  - Account Name (auto-filled)
  - Annual Amount (input)
  - Monthly Amount (calculated, annual / 12)
  - Notes (textarea)
- Add line item button
- Remove line item button
- Total revenue and total expense (calculated)
- Save as draft / Submit for approval buttons

**BudgetVarianceReportPage:**
- Header: Budget period, Fund, As of date
- Table view:
  - GL Account
  - Account Name
  - Budgeted (YTD or monthly)
  - Actual (from GL)
  - Variance ($)
  - Variance (%)
  - Color-coded cells (red if over budget >10%, green if under)
- Grouping by category (Revenue, Expenses by type)
- Total rows (subtotals by category, grand total)
- Filter by: Month, Quarter, YTD
- Export to Excel button

**BudgetVarianceChartPage:**
- Bar chart: Budgeted vs Actual by category
- Line chart: Monthly trend (budget vs actual over time)
- Pie chart: Budget allocation by category
- Filters: Fund, Date range, Category

**BudgetApprovalPage (Board View):**
- Budget summary (total revenue, total expense, net)
- Line item review (all accounts)
- Comments/discussion section
- Approval workflow:
  - Board members vote (approve/reject/abstain)
  - Requires majority approval
  - Approved date and approver recorded

**Components:**
- BudgetLineTable: Editable table with add/remove rows
- VarianceIndicator: Color-coded badge (green/yellow/red)
- BudgetChart: Recharts integration for variance visualization
- ApprovalWorkflow: Multi-step approval UI

---

## Budget Categories

### Revenue Categories

**Operating Fund:**
- 4000: Regular Assessments (monthly dues)
- 4100: Special Assessments (one-time)
- 4200: Late Fees
- 4300: Interest Income
- 4400: Other Income (rentals, amenity fees)
- 4500: Violation Fines

**Reserve Fund:**
- 4600: Reserve Contributions (transfer from operating)
- 4700: Interest Income (reserve savings)
- 4800: Special Assessments (for capital projects)

### Expense Categories

**Operating Fund:**
- 5000: Administrative (office, insurance, legal, audit)
- 5100: Landscaping
- 5200: Repairs & Maintenance
- 5300: Utilities (water, electricity, gas)
- 5350: Pool/Spa Maintenance
- 5400: Security
- 5500: Management Fees
- 5600: Payroll (if HOA has staff)

**Reserve Fund:**
- 6000: Roof Replacement
- 6100: Pavement Resurfacing
- 6200: Building Painting
- 6300: Plumbing Infrastructure
- 6400: Elevator Replacement
- 6500: Pool Equipment

---

## Variance Calculation Logic

### Monthly Variance

```python
budgeted_monthly = budget.annual_amount / 12
actual_monthly = sum(GL transactions for this account in this month)
variance_amount = actual_monthly - budgeted_monthly
variance_percent = (variance_amount / budgeted_monthly) * 100
```

### Year-to-Date (YTD) Variance

```python
months_elapsed = (current_date - budget_period.start_date).months
budgeted_ytd = budget.annual_amount * (months_elapsed / 12)
actual_ytd = sum(GL transactions for this account YTD)
variance_amount = actual_ytd - budgeted_ytd
variance_percent = (variance_amount / budgeted_ytd) * 100
```

### Variance Color Coding

- **Green:** Actual < Budgeted (under budget, good)
- **Yellow:** Variance within ±10% (acceptable)
- **Red:** Actual > Budgeted by >10% (over budget, concern)

### Alert Thresholds

**Configurable per account:**
- Default: 10% variance triggers alert
- Critical accounts (e.g., insurance): 5% variance
- Flexible accounts (e.g., repairs): 20% variance

**Alert actions:**
- Email to treasurer and board president
- Dashboard notification
- Highlight in variance report

---

## Integration Requirements

### GL Integration (US-196)

Budget actuals come from general ledger transactions:

```sql
SELECT
  gl_account_id,
  SUM(debit_amount - credit_amount) as actual_amount
FROM journal_entry_lines
WHERE
  journal_entry.posted_date BETWEEN '2025-01-01' AND '2025-03-31'
  AND fund_id = {operating_fund_id}
GROUP BY gl_account_id
```

**Refresh frequency:**
- Real-time (no caching) for treasurer view
- Daily cache for board reports
- Monthly snapshot for historical comparison

### Board Approval Workflow

**Steps:**
1. Treasurer creates draft budget
2. Submit for review (status = Proposed)
3. Board discusses at meeting
4. Board votes (each member records vote)
5. If approved (majority): Status = Approved
6. Treasurer activates budget (status = Active)
7. Budget becomes current fiscal year budget

**Voting record:**
- Each board member's vote stored
- Date and time of approval
- Meeting minutes reference (optional)

### Owner Communication

**Budget summary in owner portal:**
- Total dues amount (what owners pay)
- How dues are allocated (% to operating, % to reserve)
- Major budget categories (where the money goes)
- Year-over-year comparison (dues history)

**Transparency:**
- Approved budget published to owner portal
- Variance reports available to owners (optional, board decides)
- Builds trust ("This is where your money goes")

---

## Technical Debt / Maintenance

- [ ] Add budget amendments (mid-year changes with board approval)
- [ ] Implement rolling forecasts (project year-end based on trends)
- [ ] Add budget vs actual drill-down (click category → see transactions)
- [ ] Consider multi-year budget planning (3-year projection)

---

## Definition of Done

- [ ] All models created with migrations
- [ ] All API endpoints implemented and tested
- [ ] Frontend pages functional with real data
- [ ] Budget creation working (line-item entry)
- [ ] Variance calculation accurate (tested against spreadsheet)
- [ ] GL integration pulling actual amounts correctly
- [ ] Variance report displaying correctly with color coding
- [ ] Chart visualization working (Recharts)
- [ ] TypeScript compiles without errors
- [ ] Feature demonstrated in UI

---

## Links & References

- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md` (Phase 3)
- Pain Point: `product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md` (Pain Point #4)
- Accounting architecture: `technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md`
- GL accounts: Reference existing chart of accounts

---

## Success Metrics

**MVP Success Criteria:**
- 100% of pilot HOAs create annual budget
- Budget vs actual report generated monthly
- Board reports "better spending visibility" in feedback
- 80% of board members view variance report monthly
- At least 3 over-budget alerts triggered and acted upon

---

## Notes

**Budget Planning Best Practices:**
1. **Start with prior year actuals:** Use last year's spending as baseline
2. **Inflate for inflation:** Add 3-5% for inflation
3. **Add known increases:** Insurance premiums, management fee increases
4. **Reserve contributions:** Transfer 10-30% of assessments to reserves
5. **Contingency:** Budget 5-10% contingency for unexpected expenses

**Common Budget Mistakes:**
- Underestimating insurance (often increases 10-20% annually)
- Forgetting utilities increases
- Not budgeting for legal fees (lawsuits happen)
- Ignoring deferred maintenance (will catch up eventually)
- No contingency (Murphy's Law applies to HOAs)

**Typical HOA Operating Budget:**
- Landscaping: 25-35% of budget
- Insurance: 15-20%
- Management fees: 10-15%
- Utilities: 10-15%
- Repairs & maintenance: 10-15%
- Pool/spa: 5-10% (if applicable)
- Administrative: 5-10%
- Reserve contributions: 10-30%

**Future Enhancements (Post-Sprint):**
- Budget scenario modeling ("What if dues increase 5%?")
- Automatic dues calculation (to balance budget)
- Multi-year trending (compare current year to last 3 years)
- Budget vs actual drill-down (click account → see all transactions)
- Seasonal budgeting (some expenses higher in certain months)

**Integration with Reserve Planning:**
- Reserve contributions budgeted in operating fund
- Reserve expenses budgeted in reserve fund
- Ensure consistency between reserve study and budget
- Link reserve planning module (Sprint 14) to budget system
