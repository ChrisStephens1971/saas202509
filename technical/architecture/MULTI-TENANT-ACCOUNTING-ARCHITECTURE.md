# Multi-Tenant HOA Accounting System - Complete Architecture Guide

**Project:** Communivo HOA Management Platform
**Document Type:** Technical Architecture & Domain Model
**Status:** Foundation Document - Read This First
**Last Updated:** 2025-10-27
**Commitment:** Build it right, no matter the time required

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Pain Points & Value Proposition](#core-pain-points--value-proposition)
3. [Accounting Domain Fundamentals](#accounting-domain-fundamentals)
4. [System Architecture Principles](#system-architecture-principles)
5. [Data Model Design](#data-model-design)
6. [Multi-Tenancy Strategy](#multi-tenancy-strategy)
7. [Security & Compliance](#security--compliance)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Testing Strategy](#testing-strategy)
10. [Common Pitfalls & How to Avoid Them](#common-pitfalls--how-to-avoid-them)
11. [Technical Decisions Log](#technical-decisions-log)

---

## Executive Summary

### What We're Building

A **multi-tenant, fund-based accounting system** specifically designed for Homeowners Associations (HOAs), with these core capabilities:

1. **Fund Accounting** - Separate operating, reserve, and special assessment funds with individual balance sheets
2. **Bank Reconciliation** - Automated payment matching with exception handling for the 5-10% that can't auto-match
3. **AR Aging & Collections** - Delinquency tracking, lien management, certified notice logs, attorney escalation
4. **Multi-Entity Ledger** - Each HOA is a tenant with complete accounting isolation
5. **Immutable Audit Trail** - Event-sourced financial records with cryptographic verification
6. **Reserve Planning** - 5-20 year forecasting for capital projects (roofs, pavement, elevators)

### Why This is Hard

- **Zero tolerance for errors** - Financial data must be 100% accurate
- **Domain complexity** - Requires deep understanding of fund accounting, GAAP, HOA regulations
- **Concurrency challenges** - Multiple users posting transactions simultaneously
- **Performance at scale** - Accounting queries are expensive (SUM, GROUP BY across millions of rows)
- **Regulatory compliance** - Audit requirements, SOC 2, state-specific HOA laws

### Time Commitment

**Realistic Timeline (Solo Founder, Full-Time):**
- Phase 1 (Foundation): 12-16 weeks
- Phase 2 (Operations): 8-12 weeks
- Phase 3 (Polish): 8-12 weeks
- **Total: 28-40 weeks (7-10 months) to production-ready MVP**
- Plus: 6-12 months of bug fixes and edge case handling

**This is a 2-3 year product to get right.**

---

## Core Pain Points & Value Proposition

### Pain Point #1: Fund Accounting (Highest Impact)

**Problem:**
Generic accounting tools (QuickBooks) don't model HOA-specific fund structures:
- **Operating Fund** - Day-to-day expenses (landscaping, utilities, management fees)
- **Reserve Fund** - Long-term capital projects (roof replacement, repaving)
- **Special Assessment Fund** - One-time projects funded by owner contributions
- **Restricted Cash** - Funds that can only be used for specific purposes
- **Community-Level Liabilities** - Shared debt vs individual owner debt

**Why This Matters:**
- Boards need to see: "Do we have enough reserves for the roof replacement?"
- Auditors require fund-level balance sheets (not just one consolidated view)
- State laws mandate minimum reserve funding levels
- Mixing funds = legal liability for board members

**Solution: Multi-Fund General Ledger**

```
Chart of Accounts Structure:
├── Operating Fund
│   ├── Assets
│   │   ├── 1100 - Operating Cash
│   │   ├── 1200 - Accounts Receivable
│   │   └── 1300 - Prepaid Expenses
│   ├── Liabilities
│   │   ├── 2100 - Accounts Payable
│   │   └── 2200 - Deferred Revenue
│   ├── Equity
│   │   └── 3100 - Retained Earnings
│   ├── Revenue
│   │   ├── 4100 - Monthly Dues
│   │   └── 4200 - Late Fees
│   └── Expenses
│       ├── 5100 - Landscaping
│       ├── 5200 - Utilities
│       └── 5300 - Management Fees
│
├── Reserve Fund
│   ├── Assets
│   │   └── 1400 - Reserve Cash
│   ├── Equity
│   │   └── 3200 - Reserve Balance
│   ├── Revenue
│   │   └── 4300 - Reserve Contributions
│   └── Expenses
│       ├── 5400 - Roof Replacement
│       └── 5500 - Pavement Resurfacing
│
└── Special Assessment Fund
    ├── Assets
    │   └── 1500 - Special Assessment Cash
    └── Revenue
        └── 4400 - Special Assessments
```

**Key Features:**
- Each fund maintains its own trial balance (Debits = Credits)
- Inter-fund transfers tracked explicitly
- Board can view: Operating balance, Reserve balance, Special Assessment balance independently
- Auditor can request fund-level or consolidated financial statements

**How It Kills the Pain:**
- GAAP-compliant financial statements on demand
- No more Excel spreadsheets to track reserves
- Board can answer: "Can we afford this project?" in real-time

---

### Pain Point #2: Bank Reconciliation (Critical for Trust)

**Problem:**
Manual reconciliation is the #1 source of distrust between boards and management:
- Bank statement: $10,523.42
- System says: $10,489.17
- Board asks: "Where's the missing $34.25?"
- Staff spends hours finding: It's an outstanding check from 2 months ago

**Why This Matters:**
- Cash discrepancies = accusations of theft or incompetence
- Monthly close can't happen until all accounts reconciled
- Auditors require proof of reconciliation
- Manual process takes 4-8 hours per bank account per month

**Solution: Automated Reconciliation Engine**

**Architecture:**

```
┌─────────────────┐
│  Bank Feed      │ (Plaid API)
│  - Transactions │
│  - Balances     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Auto-Matching Engine               │
│  - Exact match (amount + date)      │
│  - Fuzzy match (amount ±$1, ±3 days)│
│  - Description matching (Stripe ID) │
│  - Pattern learning (ML optional)   │
└────────┬────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌──────────────┐
   │ Matched │   │ Likely  │   │  Exception   │
   │ 90-95%  │   │ Match   │   │  Queue 5-10% │
   │ Auto    │   │ Human   │   │  Human       │
   │         │   │ Review  │   │  Review      │
   └─────────┘   └─────────┘   └──────────────┘
```

**Data Model:**

```sql
CREATE TABLE bank_accounts (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  fund_id UUID NOT NULL, -- Links to specific fund
  account_name TEXT NOT NULL,
  account_number_last4 TEXT NOT NULL,
  routing_number TEXT,
  bank_name TEXT NOT NULL,
  plaid_access_token TEXT ENCRYPTED,
  plaid_account_id TEXT,
  current_balance NUMERIC(15,2),
  available_balance NUMERIC(15,2),
  last_synced_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bank_transactions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  bank_account_id UUID NOT NULL,
  transaction_date DATE NOT NULL,
  posted_date DATE NOT NULL,
  amount NUMERIC(15,2) NOT NULL, -- Negative = debit, Positive = credit
  description TEXT NOT NULL,
  category TEXT, -- From Plaid
  merchant_name TEXT,
  transaction_type TEXT, -- 'deposit', 'withdrawal', 'fee', 'transfer'
  plaid_transaction_id TEXT UNIQUE,
  reconciliation_status TEXT DEFAULT 'unmatched',
    -- 'unmatched', 'matched', 'likely_match', 'manually_matched', 'ignored'
  matched_payment_id UUID,
  matched_by_user_id UUID,
  matched_at TIMESTAMPTZ,
  matching_confidence DECIMAL(3,2), -- 0.00 to 1.00
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE reconciliation_reports (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  bank_account_id UUID NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  opening_balance NUMERIC(15,2) NOT NULL,
  closing_balance NUMERIC(15,2) NOT NULL,
  system_balance NUMERIC(15,2) NOT NULL,
  outstanding_deposits NUMERIC(15,2) DEFAULT 0,
  outstanding_withdrawals NUMERIC(15,2) DEFAULT 0,
  adjustments NUMERIC(15,2) DEFAULT 0,
  reconciled_balance NUMERIC(15,2) NOT NULL,
  difference NUMERIC(15,2) NOT NULL, -- Should be 0.00 when reconciled
  status TEXT DEFAULT 'in_progress', -- 'in_progress', 'reconciled', 'approved'
  reconciled_by_user_id UUID,
  approved_by_user_id UUID,
  reconciled_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**Auto-Matching Algorithm:**

```typescript
interface MatchingRule {
  type: 'exact' | 'fuzzy_amount' | 'fuzzy_date' | 'description' | 'pattern';
  confidence: number; // 0.00 to 1.00
}

async function matchBankTransaction(
  bankTx: BankTransaction,
  pendingPayments: Payment[]
): Promise<MatchResult> {

  // Rule 1: Exact Match (amount + date)
  const exactMatch = pendingPayments.find(p =>
    p.amount === bankTx.amount &&
    p.paymentDate === bankTx.transactionDate
  );
  if (exactMatch) {
    return { payment: exactMatch, confidence: 1.00, rule: 'exact' };
  }

  // Rule 2: Fuzzy Amount Match (within $1.00, date within 3 days)
  const fuzzyMatches = pendingPayments.filter(p =>
    Math.abs(p.amount - bankTx.amount) < 1.00 &&
    Math.abs(daysBetween(p.paymentDate, bankTx.transactionDate)) <= 3
  );
  if (fuzzyMatches.length === 1) {
    return { payment: fuzzyMatches[0], confidence: 0.90, rule: 'fuzzy_amount' };
  }

  // Rule 3: Description Match (Stripe payment ID, check number)
  const descriptionMatch = pendingPayments.find(p =>
    (p.stripePaymentIntentId && bankTx.description.includes(p.stripePaymentIntentId)) ||
    (p.checkNumber && bankTx.description.includes(`CHECK ${p.checkNumber}`))
  );
  if (descriptionMatch) {
    return { payment: descriptionMatch, confidence: 0.95, rule: 'description' };
  }

  // Rule 4: Pattern Learning (Optional - ML model)
  // Train on historical matched transactions
  // Use features: amount, day of month, description patterns, merchant
  const mlMatch = await mlMatchingModel.predict(bankTx, pendingPayments);
  if (mlMatch.confidence > 0.85) {
    return { payment: mlMatch.payment, confidence: mlMatch.confidence, rule: 'ml_pattern' };
  }

  return { payment: null, confidence: 0.00, rule: 'no_match' };
}
```

**Exception Queue UI:**

```
┌────────────────────────────────────────────────────────────────────────┐
│  Unmatched Bank Transactions - December 2025                          │
│  Bank Account: Wells Fargo Operating (****1234)                       │
└────────────────────────────────────────────────────────────────────────┘

Date       │ Description              │ Amount     │ Suggested Match      │ Action
───────────┼──────────────────────────┼────────────┼──────────────────────┼────────
2025-12-15 │ STRIPE PAYMENT pi_3A... │ $250.00    │ Invoice #INV-1234    │ [Match] [Skip]
           │                          │            │ Confidence: 95%      │
───────────┼──────────────────────────┼────────────┼──────────────────────┼────────
2025-12-16 │ CHECK #5678             │ $1,000.00  │ Invoice #INV-1235    │ [Match] [Skip]
           │                          │            │ Confidence: 88%      │
───────────┼──────────────────────────┼────────────┼──────────────────────┼────────
2025-12-17 │ BANK SERVICE FEE        │ -$15.00    │ No match found       │ [Create Expense]
           │                          │            │                      │ [Ignore]
───────────┼──────────────────────────┼────────────┼──────────────────────┼────────
2025-12-18 │ ACH DEPOSIT             │ $500.00    │ 2 possible matches:  │ [Review]
           │ HOMEOWNER JOHN SMITH    │            │ - INV-1236 ($500)    │
           │                          │            │ - INV-1240 ($500)    │
───────────┴──────────────────────────┴────────────┴──────────────────────┴────────

[Approve All High Confidence (>90%)] [Export Unmatched] [Mark Period Complete]
```

**How It Kills the Pain:**
- 90-95% of transactions auto-matched (save 6-8 hours/month per account)
- Exception queue makes human review fast (5-10 minutes instead of hours)
- Real-time cash position (no waiting for month-end reconciliation)
- Audit trail: Who matched what, when, and why

---

### Pain Point #3: AR Aging & Delinquency Management

**Problem:**
Boards ask: "Who's delinquent and by how much?"
Staff answer: "Let me spend 2 hours pulling a report from 3 different systems..."

- No real-time delinquency status
- Late fees applied inconsistently
- No tracking of notice delivery (disputes: "I never got a notice")
- Attorney escalation is manual (board forgets to act)
- Lien eligibility unclear (varies by state law)

**Why This Matters:**
- Delinquent owners = cash flow problems for HOA
- Late enforcement = resentment from paying owners
- Legal liability if process not followed correctly
- Collection rates suffer (industry average: 85-92%, best-in-class: 96%+)

**Solution: Automated AR Aging & Collections Workflow**

**Data Model:**

```sql
CREATE TABLE member_ledgers (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  member_id UUID NOT NULL,
  property_id UUID NOT NULL,
  current_balance NUMERIC(15,2) DEFAULT 0, -- Positive = owed by member
  last_payment_date DATE,
  last_payment_amount NUMERIC(15,2),
  delinquent_since DATE, -- First date balance went past due
  delinquent_amount NUMERIC(15,2) DEFAULT 0,
  days_delinquent INT DEFAULT 0,
  aging_0_30 NUMERIC(15,2) DEFAULT 0, -- Current
  aging_31_60 NUMERIC(15,2) DEFAULT 0,
  aging_61_90 NUMERIC(15,2) DEFAULT 0,
  aging_over_90 NUMERIC(15,2) DEFAULT 0,
  total_late_fees NUMERIC(15,2) DEFAULT 0,
  lien_eligible BOOLEAN DEFAULT false,
  lien_filed_date DATE,
  attorney_escalated_date DATE,
  collection_status TEXT DEFAULT 'current',
    -- 'current', 'late', 'delinquent', 'lien_eligible', 'lien_filed', 'attorney', 'legal'
  last_calculated_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE late_fee_rules (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  grace_period_days INT DEFAULT 10, -- Days after due date before late fee
  fee_type TEXT NOT NULL, -- 'flat', 'percentage', 'tiered'
  flat_amount NUMERIC(10,2), -- If fee_type = 'flat'
  percentage NUMERIC(5,4), -- If fee_type = 'percentage' (e.g., 0.05 = 5%)
  min_amount NUMERIC(10,2), -- Minimum fee (for percentage)
  max_amount NUMERIC(10,2), -- Maximum fee (for percentage)
  apply_monthly BOOLEAN DEFAULT false, -- Recurring late fee each month?
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE delinquency_notices (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  member_id UUID NOT NULL,
  property_id UUID NOT NULL,
  notice_type TEXT NOT NULL,
    -- 'first_notice', 'second_notice', 'final_notice', 'pre_lien', 'lien_notice', 'attorney_demand'
  amount_owed NUMERIC(15,2) NOT NULL,
  days_delinquent INT NOT NULL,
  delivery_method TEXT NOT NULL, -- 'email', 'certified_mail', 'regular_mail', 'hand_delivered'
  sent_date TIMESTAMPTZ NOT NULL,
  delivered_date TIMESTAMPTZ, -- Confirmed delivery (tracking for certified mail)
  tracking_number TEXT, -- USPS tracking for certified mail
  recipient_signature BYTEA, -- Proof of delivery
  email_opened_at TIMESTAMPTZ, -- Email tracking
  template_id UUID,
  content TEXT NOT NULL, -- Full notice content (immutable record)
  pdf_url TEXT,
  created_by_user_id UUID NOT NULL,
  notes TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE lien_records (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  member_id UUID NOT NULL,
  property_id UUID NOT NULL,
  amount NUMERIC(15,2) NOT NULL,
  filing_date DATE NOT NULL,
  filing_location TEXT, -- County recorder office
  filing_reference_number TEXT, -- Official lien number
  attorney_id UUID, -- If attorney handled filing
  release_date DATE,
  release_amount NUMERIC(15,2),
  status TEXT DEFAULT 'filed', -- 'filed', 'released', 'foreclosure_initiated'
  documents JSONB DEFAULT '[]', -- Array of document URLs
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE collection_actions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  member_id UUID NOT NULL,
  action_type TEXT NOT NULL,
    -- 'late_fee_applied', 'notice_sent', 'lien_filed', 'attorney_escalated', 'payment_plan_created'
  action_date DATE NOT NULL,
  performed_by_user_id UUID,
  amount NUMERIC(15,2),
  description TEXT NOT NULL,
  related_entity_id UUID, -- ID of related notice, lien, payment plan, etc.
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**Automated Collections Workflow:**

```
Day 0:   Invoice issued (Due date: Day 10)
Day 10:  Payment due
Day 20:  Grace period ends → Automatic late fee applied
         → First notice sent (email)
Day 35:  Second notice sent (email + certified mail)
Day 60:  Final notice sent (certified mail)
         → Flag as "lien eligible" (if state law allows)
Day 75:  Pre-lien notice sent (required in most states)
Day 90:  Attorney escalation (if no response)
         → Board approval workflow triggered
Day 105: Lien filed (if board approves)
Day 180: Foreclosure initiation (extreme cases)
```

**Key Features:**

1. **Real-Time AR Aging Report**
```sql
-- Generate AR Aging for entire community (runs in <500ms with proper indexes)
SELECT
  p.unit_number,
  m.first_name || ' ' || m.last_name AS owner_name,
  ml.current_balance,
  ml.days_delinquent,
  ml.aging_0_30,
  ml.aging_31_60,
  ml.aging_61_90,
  ml.aging_over_90,
  ml.collection_status,
  ml.last_payment_date
FROM member_ledgers ml
JOIN members m ON ml.member_id = m.id
JOIN properties p ON ml.property_id = p.id
WHERE ml.tenant_id = $1
  AND ml.current_balance > 0
ORDER BY ml.days_delinquent DESC, ml.current_balance DESC;
```

2. **Certified Notice Log (Litigation Protection)**
- Every notice stored with: content, delivery method, timestamp, tracking info
- Certified mail tracking: Delivered date, recipient signature image
- Email tracking: Opened timestamp, IP address
- Proof of delivery for disputes: "You never sent me a notice" → Show signed receipt

3. **Lien Eligibility Calculator**
```typescript
function isLienEligible(
  member: Member,
  ledger: MemberLedger,
  stateRules: StateLienRules
): LienEligibilityResult {

  // State-specific rules (example: California)
  const minimumDelinquentAmount = 1800; // CA requires $1,800 or 12 months
  const minimumDelinquentMonths = 12;
  const requiredNotices = ['first_notice', 'final_notice', 'pre_lien'];

  // Check minimum amount or months
  const meetsAmountThreshold = ledger.delinquentAmount >= minimumDelinquentAmount;
  const meetsMonthsThreshold = ledger.monthsDelinquent >= minimumDelinquentMonths;

  if (!meetsAmountThreshold && !meetsMonthsThreshold) {
    return {
      eligible: false,
      reason: `Must owe $${minimumDelinquentAmount} or be ${minimumDelinquentMonths} months delinquent`
    };
  }

  // Check required notices sent
  const sentNotices = await getNoticesForMember(member.id);
  const missingNotices = requiredNotices.filter(type =>
    !sentNotices.some(n => n.noticeType === type)
  );

  if (missingNotices.length > 0) {
    return {
      eligible: false,
      reason: `Missing required notices: ${missingNotices.join(', ')}`
    };
  }

  // Check notice timing (30 days between notices)
  const daysBetweenNotices = 30;
  for (let i = 1; i < sentNotices.length; i++) {
    const daysSince = daysBetween(sentNotices[i-1].sentDate, sentNotices[i].sentDate);
    if (daysSince < daysBetweenNotices) {
      return {
        eligible: false,
        reason: `Insufficient time between notices (${daysSince} days, need ${daysBetweenNotices})`
      };
    }
  }

  return {
    eligible: true,
    reason: 'Meets all lien requirements',
    nextSteps: ['Send pre-lien notice', 'Obtain board approval', 'File lien with county']
  };
}
```

4. **Board Approval Workflow for Collections**
- Attorney escalation requires board vote (document in system)
- Lien filing requires board resolution (attach PDF of resolution)
- Payment plan agreements require treasurer approval
- Audit trail: Who approved what, when

**How It Kills the Pain:**
- Board gets real-time delinquency dashboard (no waiting for reports)
- Automated notices prevent "forgotten" follow-ups
- Legal protection: Certified delivery proof for every notice
- Collection rates improve (consistent enforcement = owners pay on time)

---

## Accounting Domain Fundamentals

### Double-Entry Bookkeeping (Non-Negotiable)

**Core Principle:** Every financial transaction affects at least two accounts. Debits must equal credits.

```
Example: Owner pays $300 monthly dues

Debit:  Cash (Asset)               $300
Credit: Dues Revenue (Revenue)     $300

This means:
- Cash account increased by $300 (debit increases assets)
- Revenue account increased by $300 (credit increases revenue)
```

**Account Types & Normal Balances:**

| Account Type | Normal Balance | Increase With | Decrease With |
|--------------|----------------|---------------|---------------|
| Asset        | Debit          | Debit         | Credit        |
| Liability    | Credit         | Credit        | Debit         |
| Equity       | Credit         | Credit        | Debit         |
| Revenue      | Credit         | Credit        | Debit         |
| Expense      | Debit          | Debit         | Credit        |

**Data Model for Journal Entries:**

```sql
CREATE TABLE chart_of_accounts (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  fund_id UUID NOT NULL, -- Links to operating, reserve, or special assessment fund
  account_number TEXT NOT NULL, -- 1100, 4200, etc.
  account_name TEXT NOT NULL,
  account_type TEXT NOT NULL, -- 'asset', 'liability', 'equity', 'revenue', 'expense'
  account_subtype TEXT, -- 'cash', 'accounts_receivable', 'dues_revenue', etc.
  parent_account_id UUID, -- For sub-accounts (e.g., 1100-01 under 1100)
  normal_balance TEXT NOT NULL, -- 'debit' or 'credit'
  is_active BOOLEAN DEFAULT true,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(tenant_id, fund_id, account_number)
);

CREATE TABLE journal_entries (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  entry_number TEXT NOT NULL, -- JE-2025-001, JE-2025-002 (sequential)
  entry_date DATE NOT NULL,
  entry_type TEXT NOT NULL,
    -- 'standard', 'adjusting', 'closing', 'reversing', 'system_generated'
  description TEXT NOT NULL,
  reference_type TEXT, -- 'invoice', 'payment', 'bank_transaction', 'manual'
  reference_id UUID, -- ID of related invoice, payment, etc.
  period_id UUID NOT NULL, -- Links to accounting period
  status TEXT DEFAULT 'draft', -- 'draft', 'posted', 'reversed', 'voided'
  posted_at TIMESTAMPTZ,
  posted_by_user_id UUID,
  reversed_by_entry_id UUID, -- If this entry was reversed, link to reversal entry
  total_debits NUMERIC(15,2) NOT NULL,
  total_credits NUMERIC(15,2) NOT NULL,
  is_balanced BOOLEAN GENERATED ALWAYS AS (total_debits = total_credits) STORED,
  created_by_user_id UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(tenant_id, entry_number),
  CONSTRAINT debits_equal_credits CHECK (total_debits = total_credits)
);

CREATE TABLE journal_entry_lines (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  journal_entry_id UUID NOT NULL,
  line_number INT NOT NULL, -- 1, 2, 3... (order within entry)
  account_id UUID NOT NULL,
  fund_id UUID NOT NULL, -- Denormalized for query performance
  debit_amount NUMERIC(15,2) DEFAULT 0 CHECK (debit_amount >= 0),
  credit_amount NUMERIC(15,2) DEFAULT 0 CHECK (credit_amount >= 0),
  description TEXT,
  reference_type TEXT, -- 'invoice_line', 'payment', 'bank_fee', etc.
  reference_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT debit_or_credit CHECK (
    (debit_amount > 0 AND credit_amount = 0) OR
    (credit_amount > 0 AND debit_amount = 0)
  )
);

-- Indexes for performance
CREATE INDEX idx_journal_entries_tenant_date ON journal_entries(tenant_id, entry_date);
CREATE INDEX idx_journal_entries_period ON journal_entries(period_id, status);
CREATE INDEX idx_journal_entry_lines_account ON journal_entry_lines(account_id, journal_entry_id);
CREATE INDEX idx_journal_entry_lines_fund ON journal_entry_lines(fund_id, journal_entry_id);
```

**Example Journal Entry Creation:**

```typescript
async function recordPayment(payment: Payment): Promise<JournalEntry> {
  // Owner pays $300 monthly dues

  const journalEntry = {
    tenantId: payment.tenantId,
    entryNumber: generateEntryNumber(), // JE-2025-001
    entryDate: payment.paymentDate,
    entryType: 'system_generated',
    description: `Payment received: ${payment.description}`,
    referenceType: 'payment',
    referenceId: payment.id,
    periodId: getCurrentPeriodId(payment.paymentDate),
    lines: [
      {
        accountId: getCashAccountId('operating'), // 1100 - Operating Cash
        fundId: getOperatingFundId(),
        debitAmount: 300.00,
        creditAmount: 0.00,
        description: 'Payment received from John Smith'
      },
      {
        accountId: getAccountId('accounts_receivable'), // 1200 - AR
        fundId: getOperatingFundId(),
        debitAmount: 0.00,
        creditAmount: 300.00,
        description: 'Reduce AR for John Smith'
      }
    ]
  };

  // Validation: Debits = Credits
  const totalDebits = journalEntry.lines.reduce((sum, line) => sum + line.debitAmount, 0);
  const totalCredits = journalEntry.lines.reduce((sum, line) => sum + line.creditAmount, 0);

  if (totalDebits !== totalCredits) {
    throw new Error(`Journal entry not balanced: Debits ${totalDebits} != Credits ${totalCredits}`);
  }

  // Insert with transaction to ensure atomicity
  return await db.transaction(async (trx) => {
    const je = await trx.insert('journal_entries', {
      ...journalEntry,
      totalDebits,
      totalCredits,
      status: 'posted',
      postedAt: new Date()
    });

    await trx.insert('journal_entry_lines', journalEntry.lines.map(line => ({
      ...line,
      journalEntryId: je.id
    })));

    return je;
  });
}
```

### Fund Accounting Rules

**Key Principle:** Funds are separate "buckets" of money with their own financial statements.

**Fund Types in HOAs:**

1. **Operating Fund**
   - Purpose: Day-to-day operations
   - Revenue: Monthly dues, late fees, amenity fees
   - Expenses: Landscaping, utilities, insurance, management fees
   - Target Balance: 1-3 months of operating expenses

2. **Reserve Fund**
   - Purpose: Long-term capital projects (roofs, pavement, elevators)
   - Revenue: Monthly reserve contributions (part of dues)
   - Expenses: Only for capital projects (not day-to-day repairs)
   - Target Balance: Per reserve study (actuarial calculation)
   - **Rule:** Cannot transfer from reserves to operating without board approval + owner vote (in most states)

3. **Special Assessment Fund**
   - Purpose: One-time projects funded by owner assessments
   - Revenue: Special assessments (one-time or installment)
   - Expenses: Specific project (e.g., parking lot repaving)
   - **Rule:** Funds must be used for stated purpose only (fiduciary duty)

**Inter-Fund Transfers:**

```typescript
async function transferBetweenFunds(
  fromFund: Fund,
  toFund: Fund,
  amount: number,
  reason: string,
  approvedBy: User
): Promise<JournalEntry> {

  // Validation: Reserve → Operating requires special approval
  if (fromFund.type === 'reserve' && toFund.type === 'operating') {
    if (!approvedBy.hasPermission('approve_reserve_transfer')) {
      throw new Error('Reserve transfers require board approval');
    }
    // Log approval in governance system
    await logGovernanceAction({
      actionType: 'reserve_transfer',
      amount,
      approvedBy: approvedBy.id,
      reason
    });
  }

  // Create journal entry with 4 lines (debit/credit in each fund)
  return await createJournalEntry({
    description: `Inter-fund transfer: ${fromFund.name} → ${toFund.name}`,
    entryType: 'adjusting',
    lines: [
      // Debit "Due from [toFund]" in fromFund
      {
        accountId: getAccountId('due_from_other_funds'),
        fundId: fromFund.id,
        debitAmount: amount,
        creditAmount: 0,
        description: `Transfer to ${toFund.name}`
      },
      // Credit Cash in fromFund
      {
        accountId: getCashAccountId(fromFund.type),
        fundId: fromFund.id,
        debitAmount: 0,
        creditAmount: amount,
        description: `Cash transferred to ${toFund.name}`
      },
      // Debit Cash in toFund
      {
        accountId: getCashAccountId(toFund.type),
        fundId: toFund.id,
        debitAmount: amount,
        creditAmount: 0,
        description: `Cash received from ${fromFund.name}`
      },
      // Credit "Due to [fromFund]" in toFund
      {
        accountId: getAccountId('due_to_other_funds'),
        fundId: toFund.id,
        debitAmount: 0,
        creditAmount: amount,
        description: `Transfer from ${fromFund.name}`
      }
    ]
  });
}
```

### Financial Statements (What Boards & Auditors Need)

**1. Balance Sheet (Per Fund)**
```
Oakwood HOA - Operating Fund
Balance Sheet
As of December 31, 2025

ASSETS
  Current Assets
    Cash                           $45,230.00
    Accounts Receivable            $12,450.00
    Less: Allowance for Doubtful    ($1,200.00)
    Prepaid Insurance               $3,200.00
  Total Current Assets             $59,680.00

TOTAL ASSETS                       $59,680.00

LIABILITIES
  Current Liabilities
    Accounts Payable                $5,420.00
    Deferred Revenue                $2,100.00
  Total Current Liabilities         $7,520.00

EQUITY
  Retained Earnings                $52,160.00

TOTAL LIABILITIES & EQUITY         $59,680.00
```

**2. Income Statement (Per Fund)**
```
Oakwood HOA - Operating Fund
Income Statement
For the Period January 1 - December 31, 2025

REVENUE
  Monthly Dues                    $240,000.00
  Late Fees                         $3,200.00
  Amenity Fees                      $1,800.00
Total Revenue                     $245,000.00

EXPENSES
  Landscaping                      $45,000.00
  Utilities                        $28,000.00
  Insurance                        $18,000.00
  Management Fees                  $24,000.00
  Repairs & Maintenance            $32,000.00
  Legal & Professional             $8,000.00
  Other Expenses                   $12,000.00
Total Expenses                    $167,000.00

NET INCOME                         $78,000.00
```

**3. Cash Flow Statement**
```
Oakwood HOA - Operating Fund
Cash Flow Statement
For the Period January 1 - December 31, 2025

CASH FLOWS FROM OPERATING ACTIVITIES
  Net Income                                    $78,000.00
  Adjustments:
    Increase in Accounts Receivable             ($2,400.00)
    Increase in Accounts Payable                 $1,200.00
    Decrease in Prepaid Insurance                  $400.00
  Net Cash from Operating Activities            $77,200.00

CASH FLOWS FROM INVESTING ACTIVITIES           $0.00

CASH FLOWS FROM FINANCING ACTIVITIES
  Transfer to Reserve Fund                     ($30,000.00)
  Net Cash from Financing Activities           ($30,000.00)

NET CHANGE IN CASH                              $47,200.00
Cash, Beginning of Period                        $8,030.00
Cash, End of Period                             $55,230.00
```

**4. Trial Balance (Validation Report)**
```sql
-- Generate trial balance for a fund
SELECT
  coa.account_number,
  coa.account_name,
  coa.account_type,
  coa.normal_balance,
  SUM(jel.debit_amount) AS total_debits,
  SUM(jel.credit_amount) AS total_credits,
  CASE
    WHEN coa.normal_balance = 'debit'
      THEN SUM(jel.debit_amount) - SUM(jel.credit_amount)
    ELSE SUM(jel.credit_amount) - SUM(jel.debit_amount)
  END AS balance
FROM chart_of_accounts coa
LEFT JOIN journal_entry_lines jel ON coa.id = jel.account_id
LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id
WHERE coa.tenant_id = $1
  AND coa.fund_id = $2
  AND je.status = 'posted'
  AND je.entry_date <= $3 -- As of date
GROUP BY coa.id, coa.account_number, coa.account_name, coa.account_type, coa.normal_balance
ORDER BY coa.account_number;

-- Validation: Total debits MUST equal total credits
SELECT
  SUM(total_debits) AS sum_debits,
  SUM(total_credits) AS sum_credits,
  SUM(total_debits) - SUM(total_credits) AS difference
FROM trial_balance_query;
-- difference MUST be 0.00
```

---

## System Architecture Principles

### Principle #1: Immutability for Financial Records

**Rule:** Never UPDATE or DELETE financial transactions. Only INSERT.

**Why:**
- Audit requirements: Need to reconstruct any point in time
- Legal compliance: Altering financial records = fraud
- Debugging: Can trace every change back to source

**Implementation: Event Sourcing**

```sql
CREATE TABLE ledger_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  event_type TEXT NOT NULL,
    -- 'invoice_created', 'payment_received', 'journal_entry_posted',
    -- 'invoice_voided', 'payment_refunded', 'entry_reversed'
  aggregate_type TEXT NOT NULL, -- 'invoice', 'payment', 'journal_entry'
  aggregate_id UUID NOT NULL, -- ID of invoice, payment, etc.
  event_data JSONB NOT NULL, -- Full snapshot of data at this event
  user_id UUID NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  sequence_number BIGINT NOT NULL, -- Monotonically increasing per aggregate
  previous_hash TEXT, -- Hash of previous event (blockchain-style)
  current_hash TEXT NOT NULL, -- SHA256(previous_hash + event_data + timestamp)
  metadata JSONB DEFAULT '{}',
  UNIQUE(tenant_id, aggregate_id, sequence_number)
);

-- Index for fast event replay
CREATE INDEX idx_ledger_events_aggregate ON ledger_events(aggregate_id, sequence_number);
CREATE INDEX idx_ledger_events_tenant_timestamp ON ledger_events(tenant_id, timestamp);
```

**Example: Voiding an Invoice (Instead of Deleting)**

```typescript
// ❌ WRONG: Delete or update
await db.delete('invoices').where({ id: invoiceId });
await db.update('invoices').set({ status: 'voided' }).where({ id: invoiceId });

// ✅ CORRECT: Create void event + reversal entry
async function voidInvoice(invoiceId: string, reason: string, userId: string) {
  const invoice = await getInvoice(invoiceId);

  // Step 1: Create ledger event
  await createLedgerEvent({
    eventType: 'invoice_voided',
    aggregateType: 'invoice',
    aggregateId: invoiceId,
    eventData: {
      originalInvoice: invoice,
      voidReason: reason,
      voidedAt: new Date()
    },
    userId
  });

  // Step 2: Create reversal journal entry
  const reversalEntry = await createJournalEntry({
    description: `Reversal of Invoice ${invoice.invoiceNumber}: ${reason}`,
    entryType: 'reversing',
    referenceType: 'invoice',
    referenceId: invoiceId,
    lines: [
      // Reverse the original entry
      { accountId: 'accounts_receivable', debitAmount: 0, creditAmount: invoice.totalAmount },
      { accountId: 'dues_revenue', debitAmount: invoice.totalAmount, creditAmount: 0 }
    ]
  });

  // Step 3: Update invoice status (only status field, not amounts)
  // This is the ONLY update allowed
  await db.update('invoices')
    .set({
      status: 'voided',
      voidedAt: new Date(),
      voidedBy: userId,
      reversalEntryId: reversalEntry.id
    })
    .where({ id: invoiceId });

  return { success: true, reversalEntry };
}
```

**Point-in-Time Reconstruction:**

```typescript
// "What was this invoice's status on December 31, 2024?"
async function reconstructInvoiceAtDate(invoiceId: string, asOfDate: Date): Promise<Invoice> {
  const events = await db
    .select('*')
    .from('ledger_events')
    .where({ aggregateId: invoiceId })
    .where('timestamp', '<=', asOfDate)
    .orderBy('sequence_number');

  // Replay events to rebuild state
  let invoice = null;
  for (const event of events) {
    switch (event.eventType) {
      case 'invoice_created':
        invoice = event.eventData;
        break;
      case 'payment_applied':
        invoice.paidAmount += event.eventData.paymentAmount;
        if (invoice.paidAmount >= invoice.totalAmount) {
          invoice.status = 'paid';
        }
        break;
      case 'invoice_voided':
        invoice.status = 'voided';
        break;
    }
  }

  return invoice;
}
```

### Principle #2: Atomic Transactions for Financial Operations

**Rule:** Journal entries must post atomically. Either all lines succeed or all fail.

**Why:**
- Partial journal entry = unbalanced ledger = disaster
- Concurrency: Two users posting entries simultaneously
- System crash: Must recover to consistent state

**Implementation: Database Transactions + Row Locking**

```typescript
async function postJournalEntry(entry: JournalEntryDraft): Promise<JournalEntry> {
  // Validate before starting transaction
  if (!isBalanced(entry)) {
    throw new Error(`Entry not balanced: Debits ${totalDebits} != Credits ${totalCredits}`);
  }

  // Use database transaction for atomicity
  return await db.transaction(async (trx) => {
    // Step 1: Lock accounting period (prevent concurrent close)
    const period = await trx
      .select('*')
      .from('accounting_periods')
      .where({ id: entry.periodId })
      .forUpdate() // Pessimistic lock
      .first();

    if (period.status !== 'OPEN') {
      throw new Error(`Cannot post to ${period.status} period`);
    }

    // Step 2: Insert journal entry header
    const [journalEntry] = await trx
      .insert('journal_entries')
      .values({
        ...entry,
        status: 'posted',
        postedAt: new Date(),
        postedBy: getCurrentUser().id
      })
      .returning('*');

    // Step 3: Insert journal entry lines (all or nothing)
    await trx
      .insert('journal_entry_lines')
      .values(entry.lines.map(line => ({
        ...line,
        journalEntryId: journalEntry.id
      })));

    // Step 4: Update account balances (materialized view for performance)
    for (const line of entry.lines) {
      await trx.raw(`
        INSERT INTO account_balances (account_id, period_id, debit_total, credit_total, balance)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (account_id, period_id) DO UPDATE SET
          debit_total = account_balances.debit_total + EXCLUDED.debit_total,
          credit_total = account_balances.credit_total + EXCLUDED.credit_total,
          balance = account_balances.balance + EXCLUDED.balance,
          last_updated = now()
      `, [
        line.accountId,
        entry.periodId,
        line.debitAmount,
        line.creditAmount,
        calculateBalanceChange(line)
      ]);
    }

    // Step 5: Create audit event
    await trx.insert('ledger_events').values({
      eventType: 'journal_entry_posted',
      aggregateType: 'journal_entry',
      aggregateId: journalEntry.id,
      eventData: journalEntry,
      userId: getCurrentUser().id
    });

    return journalEntry;

    // If ANY step fails, entire transaction rolls back
  });
}
```

### Principle #3: Tenant Isolation (Security Critical)

**Rule:** Tenants must NEVER see or access each other's data. One SQL bug = regulatory catastrophe.

**Strategy: Schema-Per-Tenant + Row-Level Security (Defense in Depth)**

**Why Schema-Per-Tenant:**
- **Best isolation:** Each tenant = separate Postgres schema
- **Performance:** Queries only touch one tenant's tables
- **Compliance:** Easier to prove data separation in audits
- **Backup/Restore:** Can backup one tenant independently
- **Migration:** Can move tenant to different database

**Trade-offs:**
- ❌ Schema migrations slower (must run on each tenant schema)
- ❌ Connection pooling more complex
- ❌ Cross-tenant analytics harder (need to query multiple schemas)
- ✅ But: Security >>> convenience for financial data

**Implementation:**

```sql
-- Master/Control Database Schema
CREATE SCHEMA control;

CREATE TABLE control.tenants (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  schema_name TEXT UNIQUE NOT NULL, -- 'tenant_abc123'
  database_name TEXT NOT NULL, -- For future sharding
  status TEXT DEFAULT 'active', -- 'active', 'suspended', 'archived'
  created_at TIMESTAMPTZ DEFAULT now(),
  settings JSONB DEFAULT '{}'
);

-- Create tenant schema
CREATE FUNCTION control.create_tenant_schema(tenant_id UUID) RETURNS TEXT AS $$
DECLARE
  schema_name TEXT;
BEGIN
  schema_name := 'tenant_' || REPLACE(tenant_id::TEXT, '-', '');

  -- Create isolated schema
  EXECUTE format('CREATE SCHEMA %I', schema_name);

  -- Create all tables in tenant schema
  EXECUTE format('CREATE TABLE %I.chart_of_accounts (...)', schema_name);
  EXECUTE format('CREATE TABLE %I.journal_entries (...)', schema_name);
  -- ... all other tables

  -- Grant access only to tenant-specific role
  EXECUTE format('GRANT USAGE ON SCHEMA %I TO tenant_user', schema_name);

  RETURN schema_name;
END;
$$ LANGUAGE plpgsql;
```

**Application Layer: Tenant Context Enforcement**

```typescript
// Middleware: Extract tenant from request
app.use(async (req, res, next) => {
  // Get tenant from subdomain, header, or JWT
  const tenant = await getTenantFromRequest(req);

  if (!tenant) {
    return res.status(401).json({ error: 'No tenant specified' });
  }

  // Set tenant context for this request
  req.tenant = tenant;
  req.db = getDatabaseConnection(tenant.schemaName);

  next();
});

// Database connection pool per tenant
class TenantDatabasePool {
  private pools: Map<string, Pool> = new Map();

  getConnection(schemaName: string): Pool {
    if (!this.pools.has(schemaName)) {
      this.pools.set(schemaName, new Pool({
        ...dbConfig,
        // Set search_path to tenant schema
        options: `-c search_path=${schemaName},public`
      }));
    }
    return this.pools.get(schemaName);
  }
}

// All queries automatically scoped to tenant schema
async function getInvoices(req: Request) {
  // req.db already scoped to tenant schema
  return await req.db.select('*').from('invoices');
  // Translates to: SELECT * FROM tenant_abc123.invoices
}
```

**Additional Layer: Row-Level Security (Defense in Depth)**

```sql
-- Even within tenant schema, enforce tenant_id
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON invoices
  FOR ALL
  TO tenant_user
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Set tenant context at session level
SET app.current_tenant_id = 'abc-123-def-456';
```

### Principle #4: Optimistic Locking for Concurrency

**Rule:** Two accountants can't close the same period simultaneously.

**Why:**
- Accountant A starts closing December (validates, runs reports)
- Accountant B posts a new entry to December
- Accountant A finishes close
- December is now closed with unvalidated entry = bad

**Implementation: Version Numbers + Optimistic Locking**

```sql
CREATE TABLE accounting_periods (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  period_name TEXT NOT NULL, -- '2025-12', '2025-Q4'
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status TEXT DEFAULT 'OPEN',
    -- 'OPEN' → 'CLOSING' → 'CLOSED' → 'LOCKED'
  version INT DEFAULT 1, -- Incremented on every update
  closed_at TIMESTAMPTZ,
  closed_by_user_id UUID,
  locked_at TIMESTAMPTZ,
  locked_by_user_id UUID,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

```typescript
async function closePeriod(periodId: string, expectedVersion: number): Promise<void> {
  // Step 1: Validation checks
  const validations = await runPeriodCloseValidations(periodId);
  if (!validations.allPassed) {
    throw new Error(`Period close validation failed: ${validations.errors}`);
  }

  // Step 2: Attempt to close with optimistic lock
  const result = await db
    .update('accounting_periods')
    .set({
      status: 'CLOSING',
      version: expectedVersion + 1, // Increment version
      closedAt: new Date(),
      closedBy: getCurrentUser().id
    })
    .where({
      id: periodId,
      version: expectedVersion // Only update if version matches
    })
    .returning('*');

  if (result.length === 0) {
    // Version mismatch = someone else modified this period
    throw new Error('Period was modified by another user. Please refresh and try again.');
  }

  // Step 3: Run close procedures
  await generateClosingEntries(periodId);
  await generateFinancialStatements(periodId);

  // Step 4: Mark as closed
  await db
    .update('accounting_periods')
    .set({
      status: 'CLOSED',
      version: expectedVersion + 2
    })
    .where({ id: periodId });
}
```

---

## Data Model Design

### Core Entities Summary

```
Tenants (HOAs)
├── Funds (Operating, Reserve, Special Assessment)
│   ├── Chart of Accounts (Account hierarchy per fund)
│   └── Accounting Periods (Monthly, Quarterly, Annual)
│
├── Members (Owners, Tenants, Board Members)
│   ├── Properties (Units they own/rent)
│   └── Member Ledgers (AR balance, aging, delinquency status)
│
├── Financial Transactions
│   ├── Journal Entries (All debits/credits)
│   ├── Invoices (Bills to members)
│   ├── Payments (From members)
│   └── Bank Transactions (From bank feeds)
│
├── Collections
│   ├── Late Fee Rules
│   ├── Delinquency Notices (Certified mail tracking)
│   └── Lien Records
│
└── Reconciliation
    ├── Bank Accounts
    ├── Reconciliation Reports
    └── Exception Queue
```

### Entity Relationship Diagram (ERD)

```
┌──────────────┐
│   Tenants    │
└───────┬──────┘
        │
        │ 1:N
        ▼
┌──────────────┐         ┌─────────────────┐
│    Funds     │◄────────┤ Chart of        │
│              │   1:N   │ Accounts        │
└───────┬──────┘         └─────────────────┘
        │
        │ 1:N
        ▼
┌──────────────────┐
│ Accounting       │
│ Periods          │
└──────────────────┘

┌──────────────┐         ┌─────────────────┐
│   Members    │────────►│  Properties     │
│              │   N:M   │                 │
└───────┬──────┘         └─────────────────┘
        │
        │ 1:1
        ▼
┌──────────────────┐
│ Member Ledgers   │
│ (AR balances)    │
└──────────────────┘

┌──────────────────┐         ┌────────────────────┐
│ Journal Entries  │────────►│ Journal Entry      │
│                  │   1:N   │ Lines              │
└──────────────────┘         └────────────────────┘
        ▲
        │ References
        │
┌───────┴──────────┐
│ Invoices         │
│ Payments         │
│ Bank Transactions│
└──────────────────┘
```

### Critical Indexes for Performance

```sql
-- Query: "Show all unpaid invoices for this tenant"
CREATE INDEX idx_invoices_tenant_status_due
  ON invoices(tenant_id, status, due_date)
  WHERE status IN ('SENT', 'OVERDUE');

-- Query: "AR aging report by member"
CREATE INDEX idx_member_ledgers_delinquent
  ON member_ledgers(tenant_id, delinquent_amount)
  WHERE delinquent_amount > 0;

-- Query: "Trial balance for December 2025"
CREATE INDEX idx_journal_entries_period_status
  ON journal_entries(period_id, status)
  WHERE status = 'posted';

-- Query: "Bank transactions needing reconciliation"
CREATE INDEX idx_bank_transactions_unmatched
  ON bank_transactions(tenant_id, bank_account_id, reconciliation_status)
  WHERE reconciliation_status = 'unmatched';

-- Query: "Journal entry lines for account over date range"
CREATE INDEX idx_journal_entry_lines_account_date
  ON journal_entry_lines(account_id)
  INCLUDE (debit_amount, credit_amount, journal_entry_id);

-- Composite index for member payments
CREATE INDEX idx_payments_member_status_date
  ON payments(member_id, status, due_date);
```

---

## Multi-Tenancy Strategy

### Decision: Schema-Per-Tenant (Final Choice)

**Rationale:**
- **Security:** Best isolation, one SQL bug can't leak across tenants
- **Performance:** Queries only touch one tenant's data
- **Compliance:** Easier to prove isolation for SOC 2, GDPR
- **Backup/Restore:** Can backup/restore individual tenants
- **Scale:** Works well up to 500-1000 tenants per database

**Trade-offs:**
- Schema migrations run on each tenant (slower)
- Cross-tenant analytics requires UNION across schemas
- Connection pooling more complex

### Migration Strategy (for growth beyond 1000 tenants)

**Phase 1 (0-500 tenants): Single Database, Schema-Per-Tenant**
```
┌─────────────────────────────┐
│     Primary Database        │
├─────────────────────────────┤
│ Schema: tenant_abc123       │
│ Schema: tenant_def456       │
│ Schema: tenant_ghi789       │
│ ... (up to 500 schemas)     │
└─────────────────────────────┘
```

**Phase 2 (500-2000 tenants): Database-Per-Shard**
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Database: Shard1 │  │ Database: Shard2 │  │ Database: Shard3 │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ tenant_abc123    │  │ tenant_xyz789    │  │ tenant_pqr456    │
│ tenant_def456    │  │ tenant_uvw012    │  │ tenant_stu789    │
│ ... (500 each)   │  │ ... (500 each)   │  │ ... (500 each)   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         ▲                     ▲                     ▲
         └─────────────────────┴─────────────────────┘
                          Router Layer
                (Routes tenant to correct database)
```

**Phase 3 (2000+ tenants): Database-Per-Tenant for Enterprise**
- Large customers (1000+ units) get dedicated database
- Smaller customers stay in sharded multi-tenant databases
- Hybrid approach based on size and compliance needs

---

## Security & Compliance

### Audit Trail Requirements

**What Must Be Audited:**
1. All financial transactions (create, void, reverse)
2. Permission changes (who got access to what)
3. Period close/lock/unlock operations
4. Bank account changes
5. Failed login attempts
6. Data exports (who downloaded financial reports)

**Implementation:**

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  event_type TEXT NOT NULL,
  event_category TEXT NOT NULL, -- 'financial', 'security', 'admin', 'system'
  user_id UUID,
  user_email TEXT,
  user_ip_address INET,
  entity_type TEXT, -- 'invoice', 'payment', 'journal_entry', 'user', etc.
  entity_id UUID,
  action TEXT NOT NULL, -- 'create', 'update', 'delete', 'void', 'export', 'login'
  before_state JSONB, -- State before change
  after_state JSONB, -- State after change
  metadata JSONB DEFAULT '{}',
  timestamp TIMESTAMPTZ DEFAULT now(),
  request_id UUID, -- Trace across multiple operations
  session_id TEXT
);

-- Index for fast audit queries
CREATE INDEX idx_audit_log_tenant_timestamp ON audit_log(tenant_id, timestamp DESC);
CREATE INDEX idx_audit_log_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);

-- Partition by month for performance (old audits rarely queried)
CREATE TABLE audit_log_2025_01 PARTITION OF audit_log
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Encryption Requirements

**Data at Rest:**
- Database encryption: Enable Postgres transparent data encryption (TDE)
- Sensitive fields: `pgcrypto` for PII (SSN, bank accounts)
  ```sql
  CREATE EXTENSION pgcrypto;

  CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY,
    account_number_encrypted BYTEA, -- Encrypted
    account_number_last4 TEXT, -- Plaintext for display
    routing_number_encrypted BYTEA
  );

  -- Encrypt on insert
  INSERT INTO bank_accounts (account_number_encrypted, account_number_last4)
  VALUES (
    pgp_sym_encrypt('1234567890', current_setting('app.encryption_key')),
    '7890'
  );

  -- Decrypt on read (with permission check)
  SELECT pgp_sym_decrypt(account_number_encrypted, current_setting('app.encryption_key'))
  FROM bank_accounts;
  ```

**Data in Transit:**
- Force TLS 1.3 for all database connections
- Force HTTPS for all API requests (no HTTP)

### Access Control (RBAC)

**Roles:**
```typescript
enum Role {
  SUPER_ADMIN = 'super_admin',       // Platform admin (us)
  BOARD_PRESIDENT = 'board_president', // Full access to HOA data
  BOARD_TREASURER = 'board_treasurer', // Financial reports, but can't modify
  PROPERTY_MANAGER = 'property_manager', // Day-to-day operations
  ACCOUNTANT = 'accountant',          // Post entries, run reports
  OWNER = 'owner',                    // View own data only
  TENANT = 'tenant',                  // Limited access
  VENDOR = 'vendor'                   // Work orders only
}

enum Permission {
  // Financial
  VIEW_FINANCIALS = 'financials.view',
  EDIT_JOURNAL_ENTRIES = 'financials.edit_entries',
  CLOSE_PERIOD = 'financials.close_period',
  EXPORT_REPORTS = 'financials.export',

  // Collections
  VIEW_DELINQUENCIES = 'collections.view',
  SEND_NOTICES = 'collections.send_notices',
  FILE_LIENS = 'collections.file_liens',

  // Banking
  VIEW_BANK_ACCOUNTS = 'banking.view',
  RECONCILE_ACCOUNTS = 'banking.reconcile',

  // Admin
  MANAGE_USERS = 'admin.users',
  MANAGE_SETTINGS = 'admin.settings'
}

const rolePermissions: Record<Role, Permission[]> = {
  [Role.BOARD_PRESIDENT]: [
    Permission.VIEW_FINANCIALS,
    Permission.EXPORT_REPORTS,
    Permission.VIEW_DELINQUENCIES,
    Permission.FILE_LIENS,
    Permission.MANAGE_USERS,
    Permission.CLOSE_PERIOD
  ],
  [Role.BOARD_TREASURER]: [
    Permission.VIEW_FINANCIALS,
    Permission.EXPORT_REPORTS,
    Permission.VIEW_DELINQUENCIES
  ],
  [Role.ACCOUNTANT]: [
    Permission.VIEW_FINANCIALS,
    Permission.EDIT_JOURNAL_ENTRIES,
    Permission.RECONCILE_ACCOUNTS,
    Permission.EXPORT_REPORTS
  ],
  [Role.OWNER]: [
    // Can only view own invoices/payments
  ]
};
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-16)

**Week 1-2: Multi-Tenant Infrastructure**
- [ ] Implement schema-per-tenant architecture
- [ ] Build tenant provisioning system
- [ ] Set up connection pooling per tenant
- [ ] Create tenant context middleware

**Week 3-6: Chart of Accounts & Funds**
- [ ] Build fund model (operating, reserve, special assessment)
- [ ] Create chart of accounts hierarchy
- [ ] Implement account types and normal balances
- [ ] Build trial balance query (validate debits = credits)

**Week 7-10: Journal Entry System**
- [ ] Double-entry bookkeeping engine
- [ ] Journal entry creation with validation
- [ ] Automatic entry generation (from invoices, payments)
- [ ] Entry reversal system
- [ ] Event sourcing for immutability

**Week 11-14: Accounting Periods & Locking**
- [ ] Period management (open, close, lock)
- [ ] Period validation checks
- [ ] Prevent posting to closed periods
- [ ] Year-end close procedures

**Week 15-16: Financial Statements (MVP)**
- [ ] Balance sheet per fund
- [ ] Income statement per fund
- [ ] Trial balance report
- [ ] Basic caching for performance

**Milestone: Can track income/expenses for one HOA in one fund with proper double-entry accounting.**

---

### Phase 2: Banking & Reconciliation (Weeks 17-28)

**Week 17-20: Bank Integration**
- [ ] Plaid integration for bank feeds
- [ ] Bank account management
- [ ] Transaction import and deduplication
- [ ] Transaction categorization

**Week 21-24: Auto-Matching Engine**
- [ ] Exact match algorithm
- [ ] Fuzzy matching (amount + date)
- [ ] Description pattern matching
- [ ] Confidence scoring

**Week 25-28: Reconciliation Workflow**
- [ ] Exception queue UI
- [ ] Manual matching interface
- [ ] Reconciliation report generation
- [ ] Outstanding items tracking
- [ ] Approval workflow

**Milestone: 90%+ of bank transactions auto-match. Reconciliation time reduced from hours to minutes.**

---

### Phase 3: AR & Collections (Weeks 29-40)

**Week 29-32: Member Ledgers & AR Aging**
- [ ] Member ledger creation and updates
- [ ] Real-time AR aging calculation
- [ ] Aging buckets (0-30, 31-60, 61-90, 90+)
- [ ] Delinquency status tracking
- [ ] AR aging report with performance optimization

**Week 33-36: Late Fees & Collections Workflow**
- [ ] Late fee rule engine
- [ ] Automatic late fee application
- [ ] Collections workflow state machine
- [ ] Delinquency notice templates
- [ ] Notice delivery tracking (email + certified mail)

**Week 37-40: Lien Management**
- [ ] Lien eligibility calculator (state-specific rules)
- [ ] Lien filing workflow
- [ ] Attorney escalation system
- [ ] Board approval tracking
- [ ] Certified notice log (legal compliance)

**Milestone: Automated collections workflow. Real-time delinquency dashboard. Legal-compliant notice tracking.**

---

## Testing Strategy

### Unit Tests (High Coverage Critical)

**What to Test:**
- Journal entry validation (debits = credits)
- Auto-matching algorithms (precision/recall)
- Late fee calculation (edge cases)
- Account balance calculations
- Period locking logic

**Example Test:**

```typescript
describe('Journal Entry Validation', () => {
  it('should reject unbalanced entries', () => {
    const entry = {
      lines: [
        { accountId: 'cash', debitAmount: 100, creditAmount: 0 },
        { accountId: 'revenue', debitAmount: 0, creditAmount: 99 } // Off by $1
      ]
    };

    expect(() => validateJournalEntry(entry)).toThrow('Entry not balanced');
  });

  it('should accept balanced entries', () => {
    const entry = {
      lines: [
        { accountId: 'cash', debitAmount: 100, creditAmount: 0 },
        { accountId: 'revenue', debitAmount: 0, creditAmount: 100 }
      ]
    };

    expect(() => validateJournalEntry(entry)).not.toThrow();
  });
});
```

### Integration Tests (Critical Paths)

**Scenarios to Test:**
1. **End-to-End Payment Flow**
   - Owner makes payment
   - Payment auto-matches to bank transaction
   - Journal entry created
   - Member ledger updated
   - AR aging recalculated

2. **Period Close Workflow**
   - Post entries to open period
   - Run validation checks
   - Close period (concurrent attempt should fail)
   - Verify entries can't be posted to closed period

3. **Collections Workflow**
   - Invoice becomes past due
   - Late fee automatically applied
   - First notice sent
   - Delinquency escalates
   - Lien eligibility checked

### Load Tests (Performance Validation)

**Critical Queries to Benchmark:**

```bash
# Trial balance (must run in <2 seconds)
ab -n 1000 -c 10 /api/reports/trial-balance?tenantId=abc&periodId=xyz

# AR aging report (must run in <3 seconds)
ab -n 1000 -c 10 /api/reports/ar-aging?tenantId=abc

# Bank transaction matching (must process 1000 transactions in <30 seconds)
ab -n 100 /api/reconciliation/auto-match?tenantId=abc
```

**Performance Targets:**
- Trial balance: <2 seconds (100K transactions)
- AR aging: <3 seconds (500 members)
- Auto-matching: 1000 transactions in <30 seconds
- Period close: <60 seconds (month with 5K transactions)

---

## Common Pitfalls & How to Avoid Them

### Pitfall #1: Floating Point Arithmetic

**Problem:**
```typescript
const total = 0.1 + 0.2; // 0.30000000000000004 (IEEE 754)
```

**Solution:** Use `NUMERIC` type in database, cents in application

```typescript
// Store amounts in cents (integers)
const amountCents = 10050; // $100.50
const displayAmount = (amountCents / 100).toFixed(2); // "100.50"

// Database: NUMERIC(15,2) - exact decimal representation
```

### Pitfall #2: Time Zones

**Problem:** Payment date is Dec 31 in UTC but Jan 1 in California → Wrong accounting period

**Solution:** Store dates as DATE (not TIMESTAMPTZ) for financial records

```sql
-- ✅ CORRECT: Use DATE for accounting dates
CREATE TABLE invoices (
  due_date DATE NOT NULL, -- No timezone ambiguity
  created_at TIMESTAMPTZ DEFAULT now() -- Timestamp for audit
);
```

### Pitfall #3: Cascade Deletes

**Problem:** Deleting a member cascades to delete all their payments → Broken audit trail

**Solution:** No CASCADE on financial tables. Soft deletes only.

```sql
-- ❌ WRONG
CREATE TABLE payments (
  member_id UUID REFERENCES members(id) ON DELETE CASCADE
);

-- ✅ CORRECT
CREATE TABLE payments (
  member_id UUID REFERENCES members(id) ON DELETE RESTRICT,
  is_deleted BOOLEAN DEFAULT false,
  deleted_at TIMESTAMPTZ
);
```

### Pitfall #4: Over-Optimization Too Early

**Problem:** Spending weeks on caching before you have users

**Solution:** Build correct first, optimize later with metrics

```typescript
// Phase 1: Simple, correct
async function getTrialBalance(tenantId, periodId) {
  return await db.query(/* calculate on demand */);
}

// Phase 2 (after performance testing): Add caching
async function getTrialBalance(tenantId, periodId) {
  const cached = await redis.get(`trial_balance:${tenantId}:${periodId}`);
  if (cached) return JSON.parse(cached);

  const result = await db.query(/* calculate */);
  await redis.setex(`trial_balance:${tenantId}:${periodId}`, 300, JSON.stringify(result));
  return result;
}
```

### Pitfall #5: Incomplete Migration Validation

**Problem:** Import 10K invoices, 50 have wrong amounts, customer finds out 6 months later

**Solution:** Parallel running + variance reports

```typescript
// Run old system and new system in parallel for 1 month
// Compare outputs daily
async function validateMigration() {
  const oldSystemTrialBalance = await fetchFromQuickBooks();
  const newSystemTrialBalance = await getTrialBalance();

  const variance = compareTrialBalances(oldSystemTrialBalance, newSystemTrialBalance);

  if (variance.totalDifference > 0.01) {
    await emailAccountingTeam({
      subject: 'Migration Variance Detected',
      variance: variance.accountDifferences
    });
  }
}
```

---

## Technical Decisions Log

| Date | Decision | Rationale | Trade-offs |
|------|----------|-----------|------------|
| 2025-10-27 | Schema-per-tenant | Best security, good performance up to 1000 tenants | Slower migrations, complex connection pooling |
| 2025-10-27 | Event sourcing for financial records | Immutability required for audits, point-in-time reconstruction | Higher storage, more complex queries |
| 2025-10-27 | PostgreSQL over MySQL | Better support for JSONB, RLS, schemas | Team needs to learn Postgres |
| 2025-10-27 | Plaid for bank feeds | Best API, most bank coverage | Cost ($0.25/account/month), US-only initially |
| 2025-10-27 | Optimistic locking for periods | Simpler than distributed locks, works for 99% of cases | Retry logic needed, potential user frustration |
| 2025-10-27 | Materialized views for reports | 100x faster queries, acceptable for 1-hour refresh | Stale data (but acceptable for financial reports) |

---

## Next Steps: Getting Started

### Week 1 Checklist

1. **Set up development environment**
   - [ ] PostgreSQL 15+ with pgcrypto extension
   - [ ] Node.js 20+ or Python 3.11+
   - [ ] Redis for caching (optional for MVP)

2. **Create database structure**
   - [ ] Implement tenant schema creation function
   - [ ] Create first tenant schema manually
   - [ ] Build chart of accounts for HOAs (template)

3. **Build minimal journal entry system**
   - [ ] Journal entry validation (debits = credits)
   - [ ] Insert journal entry with transaction
   - [ ] Query trial balance (validate)

4. **Manual testing**
   - [ ] Create 10 journal entries manually
   - [ ] Generate trial balance
   - [ ] Verify: Sum of debits = Sum of credits

**Success Criteria for Week 1:** Can post a balanced journal entry and generate a trial balance that balances.

---

## Resources & References

### Accounting Education
- **Book:** "Accounting Made Simple" by Mike Piper (start here)
- **Book:** "Fund Accounting" by Leon E. Hay
- **Course:** Coursera "Introduction to Financial Accounting" (Wharton)
- **HOA-Specific:** CAI (Community Associations Institute) accounting guides

### Technical References
- **Event Sourcing:** Martin Fowler - "Event Sourcing Pattern"
- **Multi-Tenancy:** "Multi-Tenant Data Architecture" by Microsoft
- **PostgreSQL RLS:** Official Postgres docs on Row-Level Security
- **Double-Entry:** "Accounting for Computer Scientists" (free online)

### Regulatory Compliance
- **SOC 2:** AICPA Trust Services Criteria
- **GAAP:** FASB Accounting Standards Codification
- **State HOA Laws:** Varies by state (consult attorney)

---

## Glossary of Accounting Terms

- **Chart of Accounts:** List of all accounts used to classify transactions
- **Debit/Credit:** Not "good/bad" - just left/right side of ledger
- **Trial Balance:** Report showing all account balances; debits must equal credits
- **General Ledger:** Complete record of all financial transactions
- **Journal Entry:** Single financial transaction with debits and credits
- **AR (Accounts Receivable):** Money owed TO the HOA by owners
- **AP (Accounts Payable):** Money owed BY the HOA to vendors
- **Fund Accounting:** Separate pools of money with restrictions on use
- **Fiscal Year:** 12-month accounting period (may not match calendar year)
- **Accrual Basis:** Record revenue when earned (not when cash received)

---

**This is your foundation. Build from here. No shortcuts on financial data.**

**Next:** Review this document, ask questions, then start with Week 1 checklist.
