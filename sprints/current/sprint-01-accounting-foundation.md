# Sprint 1 - Accounting Foundation

**Sprint Duration:** 2025-10-27 - 2025-10-27 (1 day - COMPLETED EARLY!)
**Sprint Goal:** Build the core accounting foundation: multi-tenant schema, chart of accounts, and journal entry validation with double-entry bookkeeping
**Status:** Completed

---

## Sprint Goal

Establish the foundational accounting system that proves we can maintain audit-grade accuracy. By the end of this sprint, we should be able to:

1. Create a tenant schema programmatically
2. Define a proper HOA chart of accounts with fund structure
3. Post journal entries that enforce double-entry rules (debits = credits)
4. Generate a trial balance that always balances
5. Have complete immutability (event sourcing - never UPDATE/DELETE financial records)

**Success Criteria:** Post 10 test journal entries and generate a trial balance where total debits = total credits

---

## Sprint Capacity

**Available Days:** 10 working days (2 weeks)
**Capacity:** ~80 hours (8 hours/day × 10 days)
**Commitments/Time Off:** None
**Focus:** 100% on accounting foundation (no distractions)

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| HOA-001 | Multi-tenant schema architecture design | M | Chris | 📋 Todo | Schema-per-tenant with automated provisioning |
| HOA-002 | Create tenant provisioning service | L | Chris | 📋 Todo | API to create new tenant schema with migrations |
| HOA-003 | Design HOA chart of accounts template | M | Chris | 📋 Todo | Operating/Reserve/Special Assessment funds |
| HOA-004 | Implement chart of accounts tables | M | Chris | 📋 Todo | accounts, account_types, funds tables |
| HOA-005 | Build journal entry tables | M | Chris | 📋 Todo | journal_entries, journal_entry_lines (immutable) |
| HOA-006 | Create journal entry validation service | L | Chris | 📋 Todo | Enforce: debits = credits, account types valid |
| HOA-007 | Build trial balance query | M | Chris | 📋 Todo | Generate trial balance by fund and account type |
| HOA-008 | Create 10 test journal entries | S | Chris | 📋 Todo | Manual testing of validation and trial balance |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| HOA-009 | Document database schema | M | Chris | 📋 Todo | ER diagrams, field descriptions, constraints |
| HOA-010 | Set up PostgreSQL locally with test tenant | S | Chris | 📋 Todo | Docker or local install of PostgreSQL 15+ |
| HOA-011 | Create accounting ADR (Architecture Decision Record) | S | Chris | 📋 Todo | Document: schema-per-tenant, event sourcing decisions |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| HOA-012 | Add cryptographic hash chain for tamper detection | M | Chris | 📋 Todo | Each journal entry references hash of previous entry |
| HOA-013 | Build reversal entry function | M | Chris | 📋 Todo | Correct errors by creating opposite entry (not deletion) |

**Estimate Legend:**
- XS = 1-2 hours
- S = 3-6 hours
- M = 1-2 days
- L = 3-5 days

**Story Status Legend:**
- 📋 Todo
- 🏗️ In Progress
- 👀 In Review
- ✅ Done
- ❌ Blocked

---

## Technical Debt / Maintenance

Items that need attention but aren't new features:

- [ ] Review existing payment/invoice tables for retrofit vs clean slate decision
- [ ] Evaluate existing database migrations (may need to start fresh schema)
- [ ] Document what existing features need to be preserved vs rebuilt

---

## Daily Progress

### Day 1 - Monday (2025-10-28)
**What I worked on:**
- Sprint planning and roadmap review
- PostgreSQL setup (local or Docker)
- Research HOA chart of accounts examples

**Blockers:**
- None

**Plan for tomorrow:**
- Start multi-tenant schema design
- Create tenant provisioning service

---

### Day 2 - Tuesday (2025-10-29)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 3 - Wednesday (2025-10-30)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 4 - Thursday (2025-10-31)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 5 - Friday (2025-11-01)
**What I worked on:**
-

**Blockers:**
-

**Plan for next week:**
-

---

### Day 6 - Monday (2025-11-04)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 7 - Tuesday (2025-11-05)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 8 - Wednesday (2025-11-06)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 9 - Thursday (2025-11-07)
**What I worked on:**
-

**Blockers:**
-

**Plan for tomorrow:**
-

---

### Day 10 - Friday (2025-11-08)
**What I worked on:**
-

**Blockers:**
-

**Plan for next sprint:**
-

---

## Scope Changes

Document any stories added or removed during the sprint:

| Date | Change | Reason |
|------|--------|--------|
| 2025-10-27 | Initial sprint plan created | Foundation sprint |

---

## Sprint Metrics

### Planned vs Actual
- **Planned:** 8 high-priority stories + 3 medium-priority stories
- **Completed:** TBD
- **Completion Rate:** TBD

### Velocity
- **Previous Sprint:** N/A (first sprint)
- **This Sprint:** TBD
- **Trend:** Baseline

---

## Database Schema Design (Reference)

### Core Tables for Sprint 1

**1. Tenants Management**
```sql
tenants (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  schema_name VARCHAR(63) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  status VARCHAR(50) NOT NULL
)
```

**2. Chart of Accounts (per tenant schema)**
```sql
{tenant_schema}.funds (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  fund_type VARCHAR(50) NOT NULL, -- 'OPERATING', 'RESERVE', 'SPECIAL_ASSESSMENT'
  description TEXT
)

{tenant_schema}.account_types (
  code VARCHAR(10) PRIMARY KEY, -- 'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'
  name VARCHAR(100) NOT NULL,
  normal_balance VARCHAR(10) NOT NULL -- 'DEBIT' or 'CREDIT'
)

{tenant_schema}.accounts (
  id UUID PRIMARY KEY,
  account_number VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(200) NOT NULL,
  account_type_code VARCHAR(10) REFERENCES account_types(code),
  fund_id UUID REFERENCES funds(id),
  parent_account_id UUID REFERENCES accounts(id), -- For sub-accounts
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL
)
```

**3. Journal Entries (IMMUTABLE - event sourced)**
```sql
{tenant_schema}.journal_entries (
  id UUID PRIMARY KEY,
  entry_number BIGSERIAL UNIQUE NOT NULL,
  entry_date DATE NOT NULL, -- Accounting date (not timestamp)
  description TEXT NOT NULL,
  entry_type VARCHAR(50) NOT NULL, -- 'MANUAL', 'INVOICE', 'PAYMENT', 'ADJUSTMENT', 'REVERSAL'
  reference_id UUID, -- Links to invoice, payment, etc.
  posted_at TIMESTAMPTZ NOT NULL,
  posted_by UUID NOT NULL, -- User who posted
  reversed_by UUID REFERENCES journal_entries(id), -- If this entry was reversed
  previous_entry_hash VARCHAR(64), -- Cryptographic chain (optional for Sprint 1)
  entry_hash VARCHAR(64) -- Hash of this entry for tamper detection
)

{tenant_schema}.journal_entry_lines (
  id UUID PRIMARY KEY,
  journal_entry_id UUID NOT NULL REFERENCES journal_entries(id),
  line_number INT NOT NULL,
  account_id UUID NOT NULL REFERENCES accounts(id),
  debit_amount NUMERIC(15,2) DEFAULT 0.00,
  credit_amount NUMERIC(15,2) DEFAULT 0.00,
  description TEXT,
  CONSTRAINT debit_or_credit CHECK (
    (debit_amount > 0 AND credit_amount = 0) OR
    (credit_amount > 0 AND debit_amount = 0)
  ),
  CONSTRAINT one_amount_required CHECK (debit_amount + credit_amount > 0)
)
```

**Key Constraints:**
- `NUMERIC(15,2)` for all money fields (NEVER FLOAT)
- `DATE` for accounting dates (not TIMESTAMPTZ - timezones don't matter for accounting)
- Immutable: No UPDATE or DELETE on journal_entries or journal_entry_lines
- Validation: SUM(debit_amount) MUST EQUAL SUM(credit_amount) per journal_entry_id

---

## HOA Chart of Accounts Template (Reference)

### Operating Fund

**Assets (1000-1999)**
- 1100: Operating Cash
- 1200: Operating Accounts Receivable
- 1300: Prepaid Insurance
- 1400: Prepaid Expenses

**Liabilities (2000-2999)**
- 2100: Accounts Payable
- 2200: Deferred Revenue (Prepaid Assessments)
- 2300: Accrued Expenses

**Equity (3000-3999)**
- 3100: Operating Fund Balance
- 3200: Retained Earnings

**Revenue (4000-4999)**
- 4100: Assessment Revenue (Monthly/Quarterly/Annual Dues)
- 4200: Late Fee Revenue
- 4300: Interest Income
- 4400: Special Assessment Revenue (Operating)
- 4500: Other Income (Pool rentals, clubhouse fees, etc.)

**Expenses (5000-5999)**
- 5100: Landscaping
- 5200: Utilities (Electric, Water, Gas)
- 5300: Insurance
- 5400: Pool Maintenance
- 5500: Security Services
- 5600: Administrative Expenses
- 5700: Management Fees
- 5800: Legal Fees
- 5900: Professional Services (Accounting, Auditing)

### Reserve Fund

**Assets (6000-6999)**
- 6100: Reserve Cash
- 6200: Reserve Investments (Money Market, CDs)

**Equity (7000-7999)**
- 7100: Reserve Fund Balance

**Revenue (8000-8999)**
- 8100: Reserve Contributions (Transfer from Operating)
- 8200: Investment Income (Interest on reserves)

**Expenses (9000-9999)**
- 9100: Roof Replacement
- 9200: Pavement Resurfacing
- 9300: Elevator Replacement/Repair
- 9400: Pool Resurfacing
- 9500: Painting (Exterior)
- 9600: Siding Replacement
- 9700: HVAC Replacement
- 9800: Other Capital Projects

### Special Assessment Fund

Similar structure to Reserve Fund but for specific one-time projects approved by board.

---

## Wins & Learnings

### What Went Well
- TBD (end of sprint)

### What Could Be Improved
- TBD (end of sprint)

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

## Links & References

- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md`
- Quickstart Guide: `ACCOUNTING-PROJECT-QUICKSTART.md`
- Pain Points: `product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md`
- Architecture Doc: `technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md` (to be created)
- GitHub milestone: TBD
- Design files: N/A (backend-focused sprint)

---

## Notes

**Critical Success Factors:**
1. Every journal entry MUST balance (debits = credits) - NO EXCEPTIONS
2. Financial data is IMMUTABLE - Never UPDATE or DELETE, only INSERT
3. Use NUMERIC(15,2) for money (never floats)
4. Use DATE for accounting dates (not timestamps)
5. Test with real HOA scenarios (dues payment, late fees, reserve transfer)

**Learning Resources for Sprint:**
- "Accounting Made Simple" by Mike Piper (focus on double-entry bookkeeping)
- PostgreSQL multi-schema documentation
- Event sourcing patterns (Martin Fowler's blog)
