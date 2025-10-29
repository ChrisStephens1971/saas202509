# Sprint 14 - Reserve Planning Module

**Sprint Duration:** 2025-10-28 - 2025-10-28
**Sprint Goal:** Implement comprehensive reserve planning with 5-20 year capital expenditure forecasting
**Status:** Active

---

## Sprint Goal

Build a reserve planning module that enables HOAs to forecast capital expenditures over 5-20 year horizons, ensuring adequate funding for major repairs and replacements. This addresses a critical HOA need: boards must plan for expensive items like roof replacements, pavement resurfacing, and building painting without special assessments that anger homeowners.

Key features:
- Reserve study management (component lifecycle planning)
- Multi-year capital expenditure forecasting
- Funding adequacy analysis
- What-if scenario modeling
- Integration with existing reserve fund balances

---

## Sprint Capacity

**Available Days:** 1 day (aggressive sprint)
**Capacity:** 6-8 hours
**Commitments/Time Off:** None

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-141 | Backend: Reserve study models (Component, StudyItem, Scenario) | M | Chris | 📋 Todo | Core data models |
| US-142 | Backend: Reserve planning API endpoints | M | Chris | 📋 Todo | CRUD + forecasting |
| US-143 | Frontend: Reserve studies list page | S | Chris | 📋 Todo | View all studies |
| US-144 | Frontend: Reserve study detail/edit page | L | Chris | 📋 Todo | Component grid |
| US-145 | Backend: Funding adequacy calculations | M | Chris | 📋 Todo | % funded metric |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-146 | Frontend: Funding forecast chart (line chart) | M | Chris | 📋 Todo | Recharts viz |
| US-147 | Backend: Scenario modeling (what-if) | M | Chris | 📋 Todo | Compare scenarios |
| US-148 | Frontend: Export reserve study to PDF | S | Chris | 📋 Todo | Board reporting |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-149 | Industry standard component templates | S | Chris | 📋 Todo | Pre-populated items |
| US-150 | Automatic reserve contribution calculator | M | Chris | 📋 Todo | Suggest monthly amount |

**Story Status Legend:**
- 📋 Todo
- 🏗️ In Progress
- 👀 In Review
- ✅ Done
- ❌ Blocked

---

## Technical Design

### Backend Models

**ReserveStudy:**
- name: str (e.g., "2025 Reserve Study")
- study_date: DATE
- horizon_years: int (5-30)
- inflation_rate: Decimal (e.g., 3.5%)
- current_reserve_balance: Decimal (from fund)
- notes: text

**ReserveComponent:**
- study: FK(ReserveStudy)
- name: str (e.g., "Roof Replacement")
- description: text
- quantity: Decimal (e.g., 12000 sq ft)
- unit: str (e.g., "sq ft")
- useful_life_years: int (e.g., 20)
- remaining_life_years: int (e.g., 8)
- replacement_cost: Decimal (e.g., $120,000)
- inflation_adjusted_cost: Decimal (computed)
- category: str (Roofing, Paving, Painting, Structural, etc.)

**ReserveScenario:**
- study: FK(ReserveStudy)
- name: str (e.g., "Baseline", "Aggressive Funding", "Delayed Maintenance")
- monthly_contribution: Decimal
- one_time_contribution: Decimal (optional)
- notes: text

**FundingProjection (computed view):**
- scenario: FK(ReserveScenario)
- year: int
- beginning_balance: Decimal
- contributions: Decimal
- expenditures: Decimal
- interest_earned: Decimal
- ending_balance: Decimal
- percent_funded: Decimal

### API Endpoints

**Reserve Studies:**
- GET /api/reserve-studies/ - List all studies
- POST /api/reserve-studies/ - Create study
- GET /api/reserve-studies/{id}/ - Get study detail
- PUT /api/reserve-studies/{id}/ - Update study
- DELETE /api/reserve-studies/{id}/ - Delete study

**Reserve Components:**
- GET /api/reserve-components/?study={id} - List components
- POST /api/reserve-components/ - Add component
- PUT /api/reserve-components/{id}/ - Update component
- DELETE /api/reserve-components/{id}/ - Delete component

**Reserve Scenarios:**
- GET /api/reserve-scenarios/?study={id} - List scenarios
- POST /api/reserve-scenarios/ - Create scenario
- GET /api/reserve-scenarios/{id}/projection/ - Get 20-year projection
- GET /api/reserve-scenarios/compare/ - Compare scenarios

**Calculations:**
- GET /api/reserve-studies/{id}/funding-adequacy/ - Percent funded
- GET /api/reserve-studies/{id}/recommended-contribution/ - Calculate needed amount

### Frontend Pages

**ReserveStudiesPage:**
- List all reserve studies
- Filter by year
- Create new study button
- View study details

**ReserveStudyDetailPage:**
- Study metadata (name, date, horizon)
- Component grid (editable table)
- Add component modal
- Scenario tabs
- Funding forecast chart
- Export PDF button

**Components:**
- ReserveComponentGrid: Editable table
- FundingForecastChart: Line chart showing balance over 20 years
- ScenarioComparison: Side-by-side scenario comparison
- ReserveStudyForm: Create/edit study

---

## Technical Debt / Maintenance

- [ ] Ensure reserve fund balance is real-time from accounting system
- [ ] Add input validation for useful life > remaining life
- [ ] Handle inflation rate changes mid-study
- [ ] Add automated alerts when percent funded drops below 30%

---

## Definition of Done

- [x] All models created with migrations
- [x] All API endpoints implemented and tested
- [x] Frontend pages functional with real data
- [x] Reserve calculations accurate (verified with spreadsheet)
- [x] Chart renders correctly
- [x] TypeScript compiles without errors
- [x] Feature demonstrated in UI

---

## Links & References

- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md` (line 70)
- Accounting architecture: `technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md`
- Industry reference: CAI National Reserve Study Standards
- Example study: Washington State Reserve Study Requirements

---
