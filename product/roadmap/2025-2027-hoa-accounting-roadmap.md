# Product Roadmap - Multi-Tenant HOA Accounting System

**Period:** Q4 2025 - Q4 2027 (3-Year Horizon)
**Owner:** Chris Stephens
**Last Updated:** 2025-10-27
**Status:** Draft

---

## Vision & Strategy

### Product Vision

Build the most accurate and trusted fund accounting system for Homeowners Associations, solving the core pain points that legacy systems ignore: proper fund accounting, automated bank reconciliation, and systematic collections workflow. Our system will have zero tolerance for financial errors and provide audit-grade accuracy that boards and auditors can trust.

Target market: Self-managed HOAs and property management companies of all sizes (35-5,000+ units), competing on accounting rigor and automation where competitors focus on operational features only.

### Strategic Themes for 2025-2027

1. **Accounting Foundation First** - Build bulletproof double-entry fund accounting with immutable audit trail before adding operational features
2. **Banking Automation** - Achieve 90%+ auto-match rate on bank transactions to save 8 hours/month per HOA
3. **Collections Workflow** - Automate delinquency tracking with certified notice logging to protect boards from disputes
4. **Operational Excellence** - Add violations, work orders, and ARC workflow to compete with full-service platforms
5. **Retention & Scale** - Build reporting, mobile apps, and self-service features to lock in customers and scale to 500+ tenants

---

## Roadmap Overview

### Now (Q4 2025 - Weeks 1-16)
**Focus:** Phase 1 Foundation - Core accounting engine

| Feature/Initiative | Status | Owner | Target Date | Priority |
|--------------------|--------|-------|-------------|----------|
| Multi-tenant schema architecture | Not Started | Chris | Week 4 | P0 |
| Chart of accounts + fund structure | Not Started | Chris | Week 8 | P0 |
| Journal entry engine (double-entry validation) | Not Started | Chris | Week 12 | P0 |
| Trial balance + basic financial statements | Not Started | Chris | Week 16 | P0 |

**Success Criteria:** Can post balanced journal entries and generate a trial balance that balances

### Next (Q1 2026 - Weeks 17-28)
**Focus:** Phase 1 Continuation - Payments & AR foundation

| Feature/Initiative | Description | Strategic Theme | Target Date | Priority |
|--------------------|-------------|-----------------|-------------|----------|
| Invoice generation + member ledgers | AR aging per owner/unit | Collections Workflow | Week 20 | P0 |
| Payment tracking + application | Apply payments to invoices | Collections Workflow | Week 24 | P0 |
| Accounting periods + locking | Period management + audit trail | Accounting Foundation | Week 28 | P0 |
| Basic owner portal | Login + view balance + make payment | Retention & Scale | Week 28 | P1 |

### Later (Q2-Q3 2026 - Weeks 29-52)
**Focus:** Phase 2 - Banking integration & auto-reconciliation

| Feature/Initiative | Description | Strategic Theme | Estimated Quarter | Priority |
|--------------------|-------------|-----------------|-------------------|----------|
| Plaid integration | Connect 11,000+ banks via API | Banking Automation | Q2 2026 | P0 |
| Auto-matching engine | 90%+ auto-match rate (amount/date/description) | Banking Automation | Q2 2026 | P0 |
| Exception queue UI | Review unmatched transactions | Banking Automation | Q2 2026 | P0 |
| Bank reconciliation workflow | Monthly reconciliation process | Banking Automation | Q2 2026 | P0 |
| Delinquency workflow | Auto-calculate late fees, track status | Collections Workflow | Q3 2026 | P0 |
| Notice tracking system | Certified mail log with USPS tracking | Collections Workflow | Q3 2026 | P0 |

### Future/Backlog (Q4 2026 - Q4 2027)

**Phase 3: Operational Features (Q4 2026 - Q1 2027)**
- Violation tracking with photo evidence
- Architectural Review Committee (ARC) workflow
- Work order system with vendor management
- Reserve planning module (5-20 year forecasting)
- Budget vs actual tracking

**Retention Features (Q2 2027 - Q3 2027)**
- Automated board packet generation (one-click PDF)
- Auditor export (full ledger with evidence links)
- Resale disclosure packages (revenue stream)
- Custom report builder
- Mobile apps (iOS/Android for owners)

**Scaling & Enterprise (Q3 2027 - Q4 2027)**
- API for integrations
- Webhook system for real-time events
- White-label options for management companies
- Advanced analytics and forecasting
- Multi-company consolidation for management firms

---

## Detailed Feature Breakdown

### Multi-Tenant Schema Architecture

**Problem:** Each HOA needs complete data isolation with independent financial systems
**Solution:** Schema-per-tenant in PostgreSQL with automated tenant provisioning
**Impact:** Enables scaling to 500+ HOAs on shared infrastructure while maintaining security
**Effort:** Large (4 weeks)
**Dependencies:** PostgreSQL 15+, tenant management service
**Status:** Not Started
**PRD:** To be created in Sprint 1

**Technical Requirements:**
- Each tenant gets dedicated schema with full chart of accounts
- Row-level security (RLS) as backup defense
- Automated schema migrations
- Tenant provisioning API
- Resource isolation and query performance monitoring

---

### Chart of Accounts + Fund Structure

**Problem:** HOAs use fund accounting (operating/reserve/special assessment), not standard business accounting
**Solution:** Multi-fund general ledger with separate balance sheets per fund
**Impact:** Boards can answer "Can we afford this roof?" by checking reserve fund balance
**Effort:** Large (4 weeks)
**Dependencies:** Multi-tenant architecture
**Status:** Not Started
**PRD:** To be created in Sprint 1

**Fund Types:**
- Operating Fund (day-to-day expenses)
- Reserve Fund (capital projects)
- Special Assessment Fund (one-time projects)

**Account Structure:**
- Assets (1000-1999): Cash, AR, Prepaid
- Liabilities (2000-2999): AP, Deferred revenue
- Equity (3000-3999): Fund balance, retained earnings
- Revenue (4000-4999): Assessments, late fees, interest
- Expenses (5000-5999): By category (landscaping, utilities, insurance, etc.)

---

### Journal Entry Engine

**Problem:** All financial transactions must follow double-entry rules (debits = credits)
**Solution:** Journal entry validation engine with automatic balancing checks
**Impact:** Zero tolerance for financial errors, audit-grade accuracy
**Effort:** Large (4 weeks)
**Dependencies:** Chart of accounts
**Status:** Not Started
**PRD:** To be created in Sprint 2

**Key Features:**
- Immutable journal entries (event sourcing - never UPDATE/DELETE)
- Automatic balancing validation (reject if debits ≠ credits)
- Inter-fund transfer support (with approval workflow)
- Reversal entries (to correct errors without deleting)
- Cryptographic hash chain for tamper detection

---

### Invoice Generation + Member Ledgers

**Problem:** Need to track what each owner owes (AR aging)
**Solution:** Per-unit ledger with aging buckets (0-30, 31-60, 61-90, 90+ days)
**Impact:** Boards can see real-time delinquency status
**Effort:** Medium (3 weeks)
**Dependencies:** Journal entry engine
**Status:** Not Started
**PRD:** To be created in Sprint 3

**Features:**
- Recurring assessment billing (monthly/quarterly/annual)
- Special assessment support (one-time or installment)
- Automatic late fee calculation
- Interest accrual (compound monthly)
- Owner statement generation

---

### Plaid Integration

**Problem:** Manual bank reconciliation takes 8 hours/month per account
**Solution:** Direct bank data ingestion via Plaid API (11,000+ banks)
**Impact:** 95% time reduction (8 hours → 15 minutes)
**Effort:** Medium (3 weeks)
**Dependencies:** Bank account setup, Plaid API credentials
**Status:** Not Started
**PRD:** To be created in Q2 2026

**Technical Details:**
- Daily sync (or real-time if available)
- Transaction deduplication
- Support multiple bank accounts per tenant
- Lockbox remittance file import (fallback for banks without API)
- Map bank accounts to funds (operating checking → operating fund)

---

### Auto-Matching Engine

**Problem:** Matching bank transactions to invoices/payments is manual and error-prone
**Solution:** Multi-rule matching with confidence scoring
**Impact:** 90-95% auto-match rate, only 5-10% need human review
**Effort:** Large (4 weeks)
**Dependencies:** Plaid integration, payment tracking
**Status:** Not Started
**PRD:** To be created in Q2 2026

**Matching Rules:**
1. Exact match (amount + date ±0 days) → 100% confidence
2. Fuzzy match (amount ±$1, date ±3 days) → 95% confidence
3. Description matching (Stripe ID, check number) → 88% confidence
4. Pattern learning (ML-powered, optional) → Variable confidence

**Match Targets:**
- Invoice ID (best)
- Property address (good)
- Owner name (fallback)
- Amount only (last resort)

---

### Delinquency Workflow

**Problem:** Boards don't know who's delinquent or when to escalate
**Solution:** Automated collections workflow with state-specific rules
**Impact:** Consistent enforcement → 96%+ collection rate (vs 85-92% industry average)
**Effort:** Large (4 weeks)
**Dependencies:** Invoice generation, notice tracking
**Status:** Not Started
**PRD:** To be created in Q3 2026

**Workflow:**
```
Day 0:   Invoice issued (Due: Day 10)
Day 10:  Payment due
Day 20:  Grace period ends → Auto-apply late fee → Send first notice (email)
Day 35:  Second notice (email + certified mail)
Day 60:  Final notice (certified mail) → Flag as "lien eligible" (if meets state rules)
Day 75:  Pre-lien notice (required by most states)
Day 90:  Attorney escalation → Board approval workflow triggered
Day 105: Lien filed (if board approves)
Day 180: Foreclosure initiation (last resort)
```

**State-Specific Lien Rules:**
- California: $1,800 OR 12 months delinquent
- Florida: $1,000 OR 90 days delinquent
- Texas: Any amount, 30 days after pre-lien notice

---

## Success Metrics

### Phase 1 Targets (Q4 2025 - Q1 2026)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Trial balance accuracy | 0% | 100% | 🟡 Not Started |
| Pilot HOAs | 0 | 3-5 | 🟡 Not Started |
| Journal entries posted | 0 | 1,000+ | 🟡 Not Started |
| Financial statements generated | 0 | 10+ | 🟡 Not Started |

### Phase 2 Targets (Q2-Q3 2026)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| AR auto-match rate | 0% | 90%+ | 🟡 Not Started |
| Reconciliation time savings | 0% | 80% reduction | 🟡 Not Started |
| Beta HOAs | 0 | 10+ | 🟡 Not Started |
| Owner portal adoption | 0% | 60%+ | 🟡 Not Started |

### Phase 3 Targets (Q4 2026 - Q2 2027)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Active HOAs | 0 | 25+ | 🟡 Not Started |
| Total units managed | 0 | 5,000+ | 🟡 Not Started |
| Monthly recurring revenue | $0 | $10K+ | 🟡 Not Started |
| Churn rate | N/A | <5% annual | 🟡 Not Started |
| NPS | N/A | 50+ | 🟡 Not Started |

---

## Resource Allocation

### Team Capacity
- **Engineering:** Solo founder (Chris) - 40 hours/week
- **Design:** DIY / use component libraries (Tailwind, shadcn/ui)
- **Product:** Solo founder

### Effort Distribution
- 70% - New features (accounting foundation is priority)
- 15% - Technical debt / Architecture
- 10% - Bug fixes / Maintenance
- 5% - Research / Learning (accounting domain knowledge)

### Realistic Timeline
- **Phase 1:** 40-50 weeks (solo founder, learning curve)
- **Phase 2:** 20-30 weeks (faster, architecture proven)
- **Phase 3:** 20-30 weeks (operational features simpler than accounting)
- **Total to MVP:** 80-110 weeks (18-24 months realistically)
- **Plus:** 6-12 months of bug fixes and edge cases

**This is a 2-3 year product to get right.**

---

## Risks and Dependencies

| Risk/Dependency | Impact | Mitigation | Owner |
|-----------------|--------|------------|-------|
| Accounting domain complexity | High | Study "Accounting Made Simple", consult with CPAs | Chris |
| Multi-tenancy performance at scale | High | Materialized views, query optimization, load testing | Chris |
| Plaid API costs ($0.25/account/month) | Medium | Pass costs to customers, build fallback CSV import | Chris |
| State-specific lien rules | Medium | Start with 3 states (CA, FL, TX), expand later | Chris |
| User adoption (boards resist new tools) | High | Pilot program with 3-5 friendly HOAs, iterate on UX | Chris |
| Audit compliance (GAAP, SOC 2) | Medium | Event sourcing, immutable records, consult auditor | Chris |
| Data migration complexity | High | Build validation tools, parallel period running | Chris |

---

## What We're NOT Doing

It's important to be explicit about what we're deprioritizing:

- ❌ **Mobile-first design** - Web-first for boards/treasurers (mobile comes in Phase 3 for owners)
- ❌ **AI/ML features** - Manual matching is fine for MVP, ML can come later
- ❌ **QuickBooks integration** - Build our own accounting, don't depend on QB
- ❌ **Marketplace for vendors** - Focus on accounting, not vendor sourcing
- ❌ **Community social features** - Not a social network, it's a financial system
- ❌ **Property management features** - No lease management, rent roll, tenant screening
- ❌ **International support** - US-only for MVP (state-specific rules complex enough)
- ❌ **White-label** - Standard branding for MVP, white-label is Phase 3+ for enterprise

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-27 | Build custom accounting instead of integrating QuickBooks | Fund accounting not well-supported in QB, need full control for audit trail |
| 2025-10-27 | Schema-per-tenant over row-level security only | Better security, acceptable performance to 500+ tenants, simpler queries |
| 2025-10-27 | Plaid for bank feeds | Best API, 11,000+ banks, reasonable cost ($0.25/account/month) |
| 2025-10-27 | PostgreSQL over MySQL/MongoDB | JSONB for flexibility, schemas for multi-tenancy, RLS for security |
| 2025-10-27 | Event sourcing for financial records | Immutable audit trail, point-in-time reconstruction, required for compliance |
| 2025-10-27 | Target both self-managed and property management companies | Don't limit market, design for scale (35 to 5,000+ units) |
| 2025-10-27 | 3-phase approach (Accounting → Banking → Collections) | Build foundation first, banking automation is differentiator, collections locks in retention |

---

## Feedback and Questions

**Open Questions:**
1. Which 3-5 HOAs will be our pilot customers? (Need friendly boards willing to test)
2. Do we need a CPA advisor for accounting design? (Probably yes)
3. Should we build payment processing (ACH/credit card) or integrate Stripe? (Integrate Stripe for MVP)
4. Which states to support first? (CA, FL, TX = 40% of US HOAs)

---

## Revision History

| Date | Changes | Updated By |
|------|---------|------------|
| 2025-10-27 | Initial 3-year roadmap based on pain points analysis | Chris Stephens |
