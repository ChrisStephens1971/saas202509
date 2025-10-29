# HOA Accounting System - Multi-Tenant SaaS

A comprehensive multi-tenant fund accounting system designed for Homeowners Associations (HOAs) with zero tolerance for financial errors. Built with Django 5.1 + PostgreSQL (backend) and React 18 + TypeScript (frontend).

**Project ID:** saas202509
**Created:** 2025-10-27
**Status:** Development Phase - Backend Complete for Sprints 1-20
**Sprints Completed:** 19 of 20 planned (Sprint 16 skipped)

---

## 🎯 Project Overview

### Purpose
Multi-tenant fund accounting for HOAs with audit-grade accuracy, double-entry bookkeeping, and comprehensive financial reporting.

### Target Market
- Self-managed HOAs (all sizes)
- Property management companies
- Community associations

### Key Requirements
- **Zero tolerance for financial errors** - Audit-grade accuracy
- **Multi-tenant isolation** - Schema-per-tenant PostgreSQL
- **Fund-based accounting** - Operating, Reserve, Special Assessment funds
- **Immutable ledger** - Event-sourced journal entries
- **GAAP compliance** - Proper double-entry bookkeeping

---

## 🏗️ Architecture

### Backend
- **Framework:** Django 5.1 + Django REST Framework
- **Database:** PostgreSQL 16 (schema-per-tenant isolation)
- **Authentication:** JWT (djangorestframework-simplejwt)
- **API Docs:** drf-spectacular (OpenAPI/Swagger)

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS + shadcn/ui components
- **Charts:** Recharts
- **Forms:** React Hook Form + Zod validation
- **Routing:** React Router v6

### Data Architecture
- **NUMERIC(15,2)** for all monetary values (never floats)
- **DATE** for accounting dates (not TIMESTAMPTZ)
- **Immutable records** - INSERT only, never UPDATE/DELETE on financial data
- **Balanced entries** - All journal entries must balance (debits = credits)

---

## 📦 Project Structure

```
saas202509/
├── backend/               # Django + DRF backend
│   ├── accounting/        # Core accounting app
│   ├── tenants/          # Multi-tenant management
│   ├── hoaaccounting/    # Project settings
│   └── requirements.txt
│
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── api/         # API clients
│   │   ├── components/   # React components
│   │   ├── pages/       # Route pages
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Utilities
│   └── package.json
│
├── sprints/             # Sprint plans and progress
│   ├── current/         # Active/recent sprints
│   └── archive/         # Completed sprints
│
├── product/             # Product planning
│   ├── roadmap/         # Product roadmap
│   └── PRDs/           # Requirements docs
│
├── technical/           # Technical docs
│   ├── architecture/    # System design
│   └── api/            # API specifications
│
└── business/           # Business planning
    ├── okrs/           # Objectives & Key Results
    └── goals/          # Milestones
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver 8009
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env  # Edit with your settings

# Start dev server
npm run dev

# Build for production
npm run build
```

### Ports
- **Frontend:** http://localhost:3009
- **Backend:** http://localhost:8009
- **PostgreSQL:** 5409
- **Redis:** 6409 (planned)

---

## ✅ Completed Sprints

### Sprint 1-9: Foundation & Core Features
1. **Accounting Foundation** - Chart of accounts, funds, double-entry bookkeeping
2. **Tenant Management** - Multi-tenant isolation, schema-per-tenant
3. **Owner/Invoice/Payment** - Owner management, invoice generation, payment tracking
4. **Journal Entries** - Immutable ledger, transaction history
5. **Reporting** - AR aging, trial balance, owner ledger
6. **Email Notifications** - Automated invoice/payment emails
7. **Frontend Foundation** - React setup, authentication, layout
8. **Frontend Features** - Invoice/payment UI, owner ledger
9. **Automation & Banking** - Payment import, budget module backend

### Sprint 10: Frontend Enhancement (Completed 2025-10-27)
**Goal:** Build comprehensive budget UI with multi-step wizards and variance reporting

**Delivered:**
- Budget list page with filtering (fiscal year, fund, status)
- 3-step budget creation wizard (Details → Line Items → Review)
- Budget variance report with charts (Budgeted vs Actual)
- Budget approval workflow (Draft → Approved → Active → Closed)
- Recharts integration for data visualization

**Files:** 15 new files, ~1,200 lines of frontend code

### Sprint 11: Dashboard Enhancement (Completed 2025-10-28)
**Goal:** Transform dashboard from static mockup to live data-driven interface

**Delivered:**
- **Backend:** 6 API endpoints for dashboard metrics
  - Cash position with fund balances and trends
  - AR aging with buckets (current, 30-60, 60-90, 90+ days)
  - MTD/YTD expenses with top categories
  - MTD/YTD revenue with period comparisons
  - 12-month revenue vs expenses for charting
  - Recent activity feed (last 20 events)

- **Frontend:** 7 dashboard components
  - CashPositionCard (total cash + fund breakdown)
  - ARAgingCard (aging buckets with visual indicators)
  - ExpensesCard (MTD/YTD toggle)
  - RevenueCard (MTD/YTD toggle)
  - RevenueVsExpensesChart (line chart)
  - FundBalancesChart (pie chart)
  - RecentActivityList (activity feed)

**Files:** 12 files changed, 1,867 insertions, 170 deletions

### Sprint 12: Bank Reconciliation (Completed 2025-10-28) ✅ Production Ready
**Goal:** Implement manual bank reconciliation with CSV import and transaction matching

**Delivered:**
- **Backend:** 3 models + 10 API endpoints
  - BankStatement, BankTransaction, ReconciliationRule models
  - CSV parsing with case-insensitive column support
  - Fuzzy matching algorithm (confidence scoring: amount 50pts, date 30pts, check# 20pts, description 20pts)
  - Match/unmatch/ignore/create_entry operations
  - Reconciliation report generation

- **Frontend:** 2 pages + navigation
  - BankReconciliationPage (statement list, upload form, filtering)
  - ReconciliationDetailPage (transaction matching interface)
  - AI-powered match suggestions with confidence scores & reasoning
  - Real-time status updates (matched/unmatched/ignored counters)

- **Testing:** 18 comprehensive tests (all passing ✅)
  - test_bank_reconciliation.py (541 lines in saas202510)
  - BankStatement model validation & calculations
  - BankTransaction status transitions
  - CSV parsing with various formats
  - Fuzzy matching algorithm accuracy
  - Financial accuracy with property-based tests (Hypothesis)
  - Complete reconciliation workflow

- **Production Configuration:**
  - Docker multi-stage builds (Dockerfile.backend, Dockerfile.frontend)
  - docker-compose.production.yml with PostgreSQL, Redis, Gunicorn, Nginx
  - .env.production.example with all settings
  - nginx.conf with optimization, caching, security headers
  - DEPLOYMENT.md - 400+ line comprehensive deployment guide
  - Automated backup scripts included
  - Monitoring setup with cAdvisor
  - Zero-downtime deployment strategy

**Files:** 20 files changed, 2,430 insertions, 9 deletions

**Status:** ✅ **PRODUCTION READY** - Tested, documented, and ready to deploy

### Sprint 13: Funds Management UI + Navigation Overhaul (Completed 2025-10-28)
**Goal:** Complete frontend CRUD interface for fund management and improve navigation UX

**Delivered:**
- **Sidebar Navigation:** Converted horizontal top nav to fixed vertical left sidebar
  - 256px fixed width with proper spacing
  - Icons for all navigation items (lucide-react)
  - Logout button positioned at bottom
  - Hover effects and active states

- **Funds Management Feature:**
  - **Backend:** FundViewSet with full CRUD operations
    - Tenant-scoped queries with filtering (type, active status)
    - Search by name and description
    - API endpoint: `/api/v1/accounting/funds/`

  - **Frontend:** Complete UI (3 new files, 513 lines)
    - FundsPage with card-based list view
    - Filter dropdowns (fund type, status)
    - FundModal for create/edit operations
    - Color-coded badges (Operating=green, Reserve=blue, Special Assessment=yellow)
    - Empty state, loading skeletons, error handling

  - **Routing & Navigation:**
    - Added `/funds` route with ProtectedRoute wrapper
    - Added "Funds" link to sidebar (with Building2 icon)

- **Bug Fixes:** 6 TypeScript compilation errors resolved
  - Updated Fund type with missing fields (description, is_active, created_at)
  - Added missing JournalEntry interface
  - Fixed apiClient import (default vs named export)
  - Added 'secondary' variant to Badge component
  - Removed unused imports and variables
  - Fixed Fund object rendering in BankReconciliationPage

**Files:** 9 files changed, 513 insertions, 20 deletions

**Documentation:** Session notes in `docs/session-notes/2025-10-28-funds-feature.md`

### Sprint 14: Reserve Planning Module (Completed 2025-10-29)
**Goal:** Enable long-term capital expenditure planning with 5-30 year forecasting

**Delivered:**
- **Backend:** 3 models + API endpoints (backend/accounting/models.py lines 2611-2960)
  - ReserveStudy: Multi-year studies with inflation/interest rates
  - ReserveComponent: Individual components (roof, pavement, HVAC, etc.)
  - ReserveScenario: Funding scenarios with multi-year projections
  - Custom actions: funding_adequacy, projection, compare

- **Frontend:** Complete UI (2 new files, ~400 lines)
  - ReserveStudiesPage.tsx - Reserve planning interface
  - api/reserves.ts - API client for reserve operations

**Key Features:**
- 5-30 year horizon forecasting with inflation modeling
- Component useful life tracking
- Funding adequacy calculations (% funded)
- Scenario comparison (optimistic/pessimistic/realistic)

**Files:** 8 files changed, models + migrations + serializers + ViewSets + frontend

### Sprint 15: Advanced Reporting (Completed 2025-10-29)
**Goal:** User-defined custom reports with saved filters and CSV export

**Delivered:**
- **Backend:** 2 models + API endpoints (backend/accounting/models.py lines 2963-3150)
  - CustomReport: User-defined reports with configurable filters/columns
  - ReportExecution: Execution history with cached results
  - Custom actions: execute (run report), export_csv

- **Frontend:** Complete UI (2 new files, ~450 lines)
  - CustomReportsPage.tsx - Report builder interface
  - api/reports.ts - API client for report operations

**Supported Report Types (9):**
1. Trial Balance
2. General Ledger
3. AR Aging
4. Cash Flow Statement
5. Budget vs Actual
6. Owner Ledger
7. Collection Report
8. Violation Report
9. Reserve Funding

**Key Features:**
- Configurable columns and filters
- Result caching for performance
- CSV export functionality
- Execution time tracking

**Files:** 8 files changed, models + migrations + serializers + ViewSets + frontend

### Sprint 17: Delinquency Workflow (Completed 2025-10-29)
**Goal:** Automated collections workflow with 8-stage tracking

**Delivered:**
- **Backend:** 4 models + API endpoints (backend/accounting/models.py lines 3153-3592)
  - LateFeeRule: Configurable late fees (flat/percentage/combined)
  - DelinquencyStatus: Per-owner tracking with aging buckets
  - CollectionNotice: Notice history with USPS tracking
  - CollectionAction: Major actions requiring board approval
  - Custom actions: calculate_fee, summary, approve

**Collection Stages:** Current → 1st Notice → 2nd Notice → Final → Pre-Legal → Legal → Lien → Foreclosure

**Key Features:**
- Configurable late fee rules with grace periods
- Automatic aging bucket calculations (0-30, 31-60, 61-90, 90+ days)
- USPS delivery tracking for certified mail
- Board approval workflow for legal actions
- Attorney and case number tracking

**Files:** 6 files changed, models + migrations + serializers + ViewSets + URL routes

### Sprint 18: Auto-Matching Engine (Completed 2025-10-29)
**Goal:** Intelligent bank transaction matching (90%+ match rate target)

**Delivered:**
- **Backend:** 3 models + API endpoints (backend/accounting/models.py lines 3595-3837)
  - AutoMatchRule: Learned matching patterns
  - MatchResult: Cached match results with confidence scores
  - MatchStatistics: Performance tracking (auto-match rate, accuracy)
  - Custom action: accept (accept match and update rule accuracy)

**Matching Algorithms (5):**
1. Exact Match (100%) - Amount + Date ±0 days
2. Fuzzy Match (95%) - Amount ±$1 + Date ±3 days
3. Reference Match (90%) - Check#, Invoice#, Stripe ID
4. Pattern Match (85%) - Description patterns
5. ML Match (variable) - Learn from historical matches

**Key Features:**
- Multi-rule matching engine with confidence scoring
- Pattern learning from accepted matches
- Accuracy tracking per rule (times_used, times_correct)
- False positive rate monitoring
- Auto-match rate statistics

**Files:** 6 files changed, models + migrations + serializers + ViewSets + URL routes

### Sprint 19: Violation Tracking System (Completed 2025-10-29)
**Goal:** Track HOA violations with photo evidence and compliance workflow

**Delivered:**
- **Backend:** 4 models + API endpoints (backend/accounting/models.py lines 3840-4170)
  - Violation: Core violation tracking (7 status stages, 4 severity levels)
  - ViolationPhoto: Photo evidence storage
  - ViolationNotice: Notice workflow with delivery tracking
  - ViolationHearing: Hearing scheduling and outcomes
  - Custom action: summary (violation statistics by severity/status)

**Violation Workflow:** Reported → Notice Sent → Cure Period → Hearing → Fine Assessed → Resolved

**Severity Levels:** Minor (aesthetic) → Moderate (policy) → Major (structural) → Critical (safety)

**Key Features:**
- Photo evidence with captions and timestamps
- Multi-stage notice workflow with USPS tracking
- Hearing scheduling with attendees and outcomes
- Fine assessment and payment tracking
- Historical violation tracking per property

**Files:** 6 files changed, models + migrations + serializers + ViewSets + URL routes

### Sprint 20: Board Packet Generation (Completed 2025-10-29)
**Goal:** Generate comprehensive board packets with one click

**Delivered:**
- **Backend:** 3 models + API endpoints (backend/accounting/models.py lines 4173-4444)
  - BoardPacketTemplate: Reusable packet templates
  - BoardPacket: Generated packets with PDF and email tracking
  - PacketSection: Individual sections within packets
  - Custom actions: generate_pdf, send_email (placeholders for future implementation)

**Section Types (13):** Cover Page, Agenda, Minutes, Financial Summary, Trial Balance, Cash Flow, Budget Variance, AR Aging, Delinquency, Violation Summary, Reserve Study, Bank Reconciliation, Attachments

**Key Features:**
- Reusable templates with configurable sections
- Dynamic section ordering
- Status tracking (draft, generating, ready, sent)
- Email distribution to board members
- Meeting date association
- Page count tracking

**Files:** 6 files changed, models + migrations + serializers + ViewSets + URL routes

**Note:** PDF generation and email sending are placeholder implementations requiring library integration (ReportLab/WeasyPrint + SendGrid/SMTP)

---

## 🎯 Roadmap

### ⏸️ Skipped Sprint
- **Sprint 16:** Plaid Integration (11,000+ bank connections) - Intentionally skipped per project requirements

### 🔮 Future Enhancements
**Sprint 14-20 Frontend (Partially Complete):**
- ✅ Sprint 14: ReserveStudiesPage.tsx (complete)
- ✅ Sprint 15: CustomReportsPage.tsx (complete)
- ⏸️ Sprint 17: Delinquency dashboard UI (pending)
- ⏸️ Sprint 18: Transaction matching UI (pending)
- ⏸️ Sprint 19: Violation tracking UI (pending)
- ⏸️ Sprint 20: Board packet builder UI (pending)

### Future Features
- Mobile app (React Native)
- Multi-tenant admin panel
- Advanced analytics dashboard
- Document management (contracts, invoices)
- Owner portal (self-service)

---

## 🧪 Testing

### QA Project
**Location:** C:\devop\saas202510
**Purpose:** Dedicated QA/testing infrastructure for zero-tolerance financial accuracy

**Testing Strategy:**
- Backend unit tests (pytest)
- Frontend component tests (Vitest)
- Integration tests (Playwright)
- Property-based tests for financial calculations
- Manual testing checklist per sprint

**After implementing features in saas202509, tests should be added in saas202510**

---

## 📊 Project Metrics

### Code Stats (as of Sprint 20)
- **Backend:** ~10,000 lines (Python)
  - Models: 4,444 lines (18 models added in Sprints 14-20)
  - Serializers: ~700 lines (18 serializers added)
  - ViewSets: ~2,160 lines (18 ViewSets added)
  - Migrations: 14 files
- **Frontend:** ~10,000 lines (TypeScript/TSX)
  - Pages: ~15 major pages
  - Components: ~30 reusable components
- **Total:** ~20,000 lines of production code
- **Tests:** In development (saas202510)

### Progress
- **Sprints Completed:** 19 of 20 (Sprint 16 skipped)
- **Backend:** ✅ Complete for all sprints
- **Frontend:** 🟡 Partial (Sprints 1-15 complete, 17-20 pending)
- **Testing:** ⏸️ Pending in saas202510
- **Timeline:** Backend MVP complete, frontend enhancements ongoing

---

## 🔗 Related Documentation

### Essential Reading
- **ACCOUNTING-PROJECT-QUICKSTART.md** - Week 1 guide (START HERE)
- **SPRINT-14-20-COMPLETION-REPORT.md** - Comprehensive report on Sprints 14-20 (NEW)
- **product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md** - 10 pain points & requirements
- **technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md** - Complete architecture

### Planning Documents
- Product roadmap: `product/roadmap/`
- Sprint plans: `sprints/current/`
- OKRs: `business/okrs/`

### Technical Specs
- Architecture decisions: `technical/adr/`
- API specifications: `technical/api/`
- Database schema: `backend/accounting/models.py`

---

## 🤝 Development Workflow

### Sprint Cadence
- **Sprint Duration:** 1-2 days (aggressive timeline)
- **Planning:** Sprint plan created at start
- **Development:** Feature implementation with testing
- **Review:** Code committed to GitHub
- **Retrospective:** Learnings documented

### Git Workflow
```bash
# Work on feature
git add .
git commit -m "feat: description"

# Push to GitHub
git push origin master
```

### Commit Message Format
```
feat: add dashboard API endpoints
fix: correct AR aging calculation
docs: update Sprint 11 plan
test: add budget validation tests
```

---

## 🚀 Production Deployment

### Quick Deploy (5 Commands)

```bash
git clone https://github.com/ChrisStephens1971/saas202509.git
cd saas202509
cp .env.production.example .env.production
# Edit .env.production with your production values
docker-compose -f docker-compose.production.yml up -d --build
```

### Full Deployment Guide

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for comprehensive deployment instructions including:
- ✅ Pre-deployment checklist with test verification
- ✅ SSL setup with Let's Encrypt
- ✅ Nginx reverse proxy configuration
- ✅ Automated backup scripts
- ✅ Monitoring setup (cAdvisor)
- ✅ Troubleshooting guide
- ✅ Security best practices
- ✅ Zero-downtime updates

### Infrastructure

**Docker Services:**
- **PostgreSQL 16** - Multi-tenant database with health checks
- **Redis 7** - Caching and sessions
- **Django + Gunicorn** - Backend API (4 workers)
- **React + Nginx** - Frontend SPA with optimization

**Production Features:**
- Multi-stage Docker builds
- Health checks for all services
- Automated database migrations
- Static file optimization
- Gzip compression
- Security headers (HSTS, X-Frame-Options, etc.)
- Volume persistence
- Zero-downtime deployment

### Testing

**Test Suite (saas202510):**
```bash
# Run comprehensive test suite
pytest tests/test_bank_reconciliation.py -v

# Result: 18 tests passed ✅
```

**Test Coverage:**
- BankStatement model validation
- BankTransaction operations
- CSV parsing (multiple formats)
- Fuzzy matching algorithm
- Financial accuracy (property-based)
- Complete reconciliation workflows

---

## 📝 Development Notes

### Key Principles
- **Financial accuracy first** - Never compromise on precision
- **Tenant isolation** - Strict schema-per-tenant separation
- **Immutable records** - Financial data is append-only
- **Audit trail** - Complete transaction history
- **GAAP compliance** - Proper accounting practices

### Special Considerations
- All monetary calculations use `Decimal` type
- Date comparisons use `DATE` not `TIMESTAMPTZ`
- Journal entries must always balance (debits = credits)
- Never UPDATE or DELETE financial records
- Always validate fund balances after transactions

---

## 🔧 Tech Stack Details

### Backend Dependencies
- Django 5.1
- djangorestframework
- djangorestframework-simplejwt
- drf-spectacular
- psycopg[binary]
- django-filter
- pytest (testing)

### Frontend Dependencies
- React 18
- TypeScript 5
- Vite 5
- Tailwind CSS 3
- React Router 6
- React Hook Form
- Zod
- Recharts
- Lucide Icons

---

## 📈 Project Timeline

- **2025-10-27:** Project created (Sprint 1-9 foundation complete)
- **2025-10-27:** Sprint 10 complete (Budget UI)
- **2025-10-28:** Sprint 11 complete (Dashboard Enhancement)
- **2025-10-29+:** Continuing development

**Estimated MVP:** Q2 2026
**Estimated Beta:** Q3 2026

---

## 📞 Project Info

**GitHub:** https://github.com/ChrisStephens1971/saas202509
**Linear:** https://linear.app/verdaio-saas-projects/project/accounting-b81e6c2bcbce
**Template Type:** Enterprise
**Team:** Solo founder

---

## 🎉 Acknowledgments

**Created with:** Claude Code (claude.ai/code)

**Inspired by:**
- Modern HOA accounting challenges
- Double-entry bookkeeping principles
- Multi-tenant SaaS best practices
- Event-sourcing patterns

---

**Built for audit-grade accuracy. Zero tolerance for financial errors.** 🎯
