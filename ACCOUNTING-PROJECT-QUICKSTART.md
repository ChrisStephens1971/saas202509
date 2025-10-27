# Accounting Project Quick Start Guide

**Purpose:** Get oriented on the accounting system project in 10 minutes
**Last Updated:** 2025-10-27

---

## 📚 Essential Reading (In Order)

1. **This file** - Overview and decisions (10 minutes)
2. **`product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md`** - What we're building and why (30 minutes)
3. **`technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md`** - How we're building it (2 hours)

---

## 🎯 The Mission

Build a **multi-tenant fund accounting system** for HOAs that solves these pain points:

1. **Fund Accounting** - Separate operating, reserve, and special assessment funds
2. **Bank Reconciliation** - Auto-match 90%+ of transactions
3. **AR/Collections** - Automated delinquency workflow with certified notice tracking

**Non-negotiable:** Financial data must be 100% accurate. Zero tolerance for errors.

---

## ⏱️ Realistic Timeline

- **Phase 1 (Foundation):** 12-16 weeks
- **Phase 2 (Banking):** 8-12 weeks
- **Phase 3 (Collections):** 8-12 weeks
- **Total MVP:** 28-40 weeks (7-10 months)
- **Plus:** 6-12 months of bug fixes and edge cases

**This is a 2-3 year product to get right.**

---

## 🏗️ Architecture Decisions (Already Made)

| Decision | Choice | Why |
|----------|--------|-----|
| **Multi-Tenancy** | Schema-per-tenant | Best security, good performance to 500+ tenants |
| **Database** | PostgreSQL 15+ | JSONB, RLS, schemas, mature |
| **Immutability** | Event sourcing | Required for audits, point-in-time reconstruction |
| **Bank Feeds** | Plaid | Best API, 11,000+ banks, $0.25/account/month |
| **Concurrency** | Optimistic locking | Simpler than distributed locks, works for 99% |
| **Performance** | Materialized views | 100x faster queries, 1-hour refresh acceptable |

---

## 🚀 Week 1 Checklist (Start Here)

### Prerequisites
- [ ] PostgreSQL 15+ installed
- [ ] Node.js 20+ or Python 3.11+
- [ ] Read both architecture documents above

### Tasks
1. [ ] Create first tenant schema manually
2. [ ] Implement chart of accounts for HOAs (use template from architecture doc)
3. [ ] Build journal entry validation (debits = credits check)
4. [ ] Create 10 test journal entries manually
5. [ ] Query trial balance
6. [ ] Verify: Sum of debits = Sum of credits

**Success Criteria:** Can post a balanced journal entry and generate a trial balance that balances.

---

## 🎓 Accounting Concepts You Must Understand

### 1. Double-Entry Bookkeeping
Every transaction has two sides:
```
Owner pays $300 dues:
  Debit:  Cash (Asset)        $300
  Credit: Revenue (Revenue)   $300
```

**Rule:** Debits MUST equal credits. Always.

### 2. Account Types & Normal Balances

| Type | Normal Balance | Increase | Decrease |
|------|----------------|----------|----------|
| Asset | Debit | Debit | Credit |
| Liability | Credit | Credit | Debit |
| Equity | Credit | Credit | Debit |
| Revenue | Credit | Credit | Debit |
| Expense | Debit | Debit | Credit |

### 3. Fund Accounting
HOAs use **fund accounting** (not regular business accounting):

- **Operating Fund:** Day-to-day expenses (landscaping, utilities)
- **Reserve Fund:** Long-term capital projects (roof, pavement)
- **Special Assessment Fund:** One-time projects

Each fund has its own balance sheet. Funds CANNOT be mixed without board approval.

### 4. Trial Balance
Report showing all account balances. Used to verify the books balance.

**Golden Rule:** Total debits MUST equal total credits. If not, there's a bug.

---

## 🔐 Security Principles (Non-Negotiable)

1. **Never UPDATE or DELETE financial records** - Only INSERT (event sourcing)
2. **Schema-per-tenant isolation** - One tenant cannot see another's data
3. **Row-level security as backup** - Defense in depth
4. **Audit everything** - Who did what, when, and why
5. **Encrypt sensitive data** - Bank accounts, routing numbers (pgcrypto)

---

## 🧪 Testing Requirements

### Unit Tests (80%+ coverage)
- Journal entry validation
- Account balance calculations
- Auto-matching algorithms
- Late fee calculations

### Integration Tests (Critical paths)
- End-to-end payment flow
- Period close workflow
- Collections workflow

### Load Tests (Performance targets)
- Trial balance: <2 seconds (100K transactions)
- AR aging: <3 seconds (500 members)
- Auto-matching: 1000 transactions in <30 seconds

---

## ⚠️ Common Mistakes to Avoid

1. **Floating point arithmetic** → Use NUMERIC(15,2) in DB, cents in code
2. **Time zones** → Use DATE (not TIMESTAMPTZ) for accounting dates
3. **Cascade deletes** → Use ON DELETE RESTRICT + soft deletes
4. **Premature optimization** → Build correct first, optimize with metrics later
5. **Incomplete migrations** → Always run parallel (old system + new system) for 1 month

---

## 📖 Learning Resources

### Accounting Basics
- **Book:** "Accounting Made Simple" by Mike Piper (START HERE)
- **Book:** "Fund Accounting" by Leon E. Hay
- **Online:** "Accounting for Computer Scientists" (free)

### Technical Patterns
- **Event Sourcing:** Martin Fowler's blog
- **Multi-Tenancy:** Microsoft's "Multi-Tenant Data Architecture"
- **PostgreSQL RLS:** Official Postgres documentation

---

## 🎯 Next Steps After Week 1

Once you have basic journal entries working:

1. **Week 2-6:** Build chart of accounts + fund structure
2. **Week 7-10:** Automatic journal entry generation (from invoices/payments)
3. **Week 11-14:** Accounting periods + locking
4. **Week 15-16:** Financial statements (balance sheet, income statement)

Then move to Phase 2 (Banking & Reconciliation).

---

## 💬 Key Questions to Answer Early

Before diving deep, answer these:

1. **Target Market:**
   - Self-managed HOAs or property management companies?
   - Small (<100 units), mid-size (100-500), or large (500+)?

2. **Build vs Buy:**
   - Build accounting from scratch or integrate QuickBooks/Xero?
   - Build Plaid integration or use aggregator?

3. **Go-to-Market:**
   - How will you get first 10 customers?
   - Pilot program? Referrals? Direct sales?

---

## 📊 Current Project Status

**What's Built:**
- ✅ User authentication (Clerk)
- ✅ Basic payment tracking (Stripe integration)
- ✅ Invoice management (basic)
- ✅ Work orders system
- ✅ Document storage
- ✅ Announcements

**What's Missing (Critical):**
- ❌ Multi-fund general ledger
- ❌ Double-entry bookkeeping
- ❌ Bank reconciliation (only have Stripe, not bank feeds)
- ❌ AR aging / collections workflow
- ❌ Fund accounting (no separation of operating vs reserve)
- ❌ Immutable audit trail

**Decision:** Your current build focused on operational features (Phase 2) but is missing the accounting foundation (Phase 1). You need to either:

A) **Pivot:** Build accounting foundation now (recommended based on pain points)
B) **Continue:** Finish operational features, integrate QuickBooks for accounting
C) **Hybrid:** Retrofit fund accounting under existing payment tables (technical debt)

---

## 🔄 Current Project vs Accounting Requirements

### Current Schema Analysis

**What you have:**
- `payments` table - Basic payment tracking
- `invoices` table - Basic invoice tracking
- `subscriptions` table - Recurring billing

**What's missing for accounting:**
- `chart_of_accounts` - No account structure
- `journal_entries` - No double-entry system
- `journal_entry_lines` - No debits/credits
- `funds` - No fund separation
- `accounting_periods` - No period management
- `bank_accounts` - No bank account tracking
- `bank_transactions` - No bank feed integration
- `member_ledgers` - No AR aging tracking
- `delinquency_notices` - No notice tracking
- `lien_records` - No lien management

**Assessment:** ~10% of required accounting system is built.

---

## 🎬 Ready to Start?

1. Read the two architecture documents (links at top)
2. Complete Week 1 checklist
3. Report back: "Trial balance works" or "Stuck on X"
4. Then we'll tackle Week 2-6 together

**Remember:** Building accounting software is hard. Take your time. Get it right. Financial data has zero tolerance for errors.

---

**Questions? Start with Week 1 and let me know what you hit.**
