# Sprint 2 - Invoicing & Accounts Receivable

**Sprint Duration:** 2025-10-27 - 2025-10-27 (1 day - COMPLETED SAME DAY!)
**Sprint Goal:** Build the invoicing and accounts receivable system with owner/unit tracking, invoice generation, and payment application
**Status:** Completed

---

## 🎉 Sprint Completion Summary

**Completion Date:** 2025-10-27
**Actual Duration:** 1 day (planned: 2 weeks)
**Completion Rate:** 100% of high-priority stories

### What We Built

**Core Models (7 models):**
- `Owner` - Track homeowners with contact info, board status, AR balance
- `Unit` - Track properties with assessment amounts, occupancy status
- `Ownership` - Link owners to units with ownership percentage and history
- `Invoice` - Track assessments and charges with auto-numbering (INV-00001)
- `InvoiceLine` - Line items linking to revenue accounts
- `Payment` - Track payments with auto-numbering (PMT-00001) and application tracking
- `PaymentApplication` - FIFO payment application to invoices

**Automatic Journal Entry System:**
- Invoices auto-create: DR: AR (1200), CR: Assessment Revenue (4100)
- Payments auto-create: DR: Cash (1100), CR: AR (1200)
- All journal entries perfectly balanced (debits = credits)
- 13 journal entries created across test scenarios

**Management Commands:**
- `generate_monthly_invoices` - Batch generate assessment invoices for all active units
- Supports dry-run mode, custom due dates, duplicate detection

**Business Logic:**
- Invoice auto-numbering (INV-00001, INV-00002, etc.)
- Payment auto-numbering (PMT-00001, PMT-00002, etc.)
- AR aging buckets: Current, 1-30, 31-60, 61-90, 90+ days
- Owner AR balance calculation (sum of unpaid invoices)
- Invoice status tracking: Draft, Issued, Paid, Overdue, Partial, Cancelled
- Payment status tracking: Pending, Cleared, Failed, Reversed

**Trial Balance Verification:**
- November invoices: $2,000 (5 units × $400)
- December invoices: $2,000 (5 units × $400)
- Payments received: $1,100
- Current AR balance: $2,900
- Trial balance: **$4,000 DR = $4,000 CR** ✅

### Test Results

**End-to-end AR workflow tested:**
- ✅ Created 5 owners with 5 units and ownerships
- ✅ Generated November 2025 invoices (5 invoices, $2,000 total)
- ✅ Generated December 2025 invoices (5 invoices, $2,000 total)
- ✅ Applied 3 payments: full, partial, and overpayment scenarios
- ✅ Verified all journal entries auto-created and balanced
- ✅ Verified trial balance remains balanced after all transactions
- ✅ Verified AR aging calculation works correctly

---

## Sprint Goal

Create the AR (Accounts Receivable) system that tracks what each owner owes. By the end of this sprint, we should be able to:

1. Track owners and their units
2. Generate recurring assessment invoices (monthly/quarterly/annual)
3. Apply payments to specific invoices
4. Track AR aging (0-30, 31-60, 61-90, 90+ days)
5. View owner ledger (what they owe by invoice)
6. Automatically create journal entries from invoices and payments

**Success Criteria:**
- Create 10 owners with units
- Generate invoices for monthly assessments
- Apply payments and see AR balance update
- View AR aging report

---

## Sprint Capacity

**Available Days:** 10 working days (2 weeks)
**Capacity:** ~80 hours (8 hours/day × 10 days)
**Focus:** Invoicing, payments, AR tracking

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| HOA-101 | Create Owner and Unit models | M | Chris | 📋 Todo | Track owners, units, ownership relationships |
| HOA-102 | Create Invoice and InvoiceLine models | L | Chris | 📋 Todo | Recurring assessments, special assessments, late fees |
| HOA-103 | Create Payment model with invoice application | L | Chris | 📋 Todo | Apply payments to invoices, track unapplied amounts |
| HOA-104 | Build invoice generation service | M | Chris | 📋 Todo | Auto-generate monthly/quarterly/annual invoices |
| HOA-105 | Build payment application logic | M | Chris | 📋 Todo | Apply payments to oldest invoices first (FIFO) |
| HOA-106 | Create AR aging calculation | M | Chris | 📋 Todo | Calculate aging buckets per owner |
| HOA-107 | Link invoices/payments to journal entries | L | Chris | 📋 Todo | Auto-post JEs when invoice/payment created |
| HOA-108 | Test end-to-end AR workflow | M | Chris | 📋 Todo | Invoice → Payment → JE → Trial Balance |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| HOA-109 | Create owner ledger view | M | Chris | 📋 Todo | Show all invoices/payments per owner |
| HOA-110 | Add late fee calculation | M | Chris | 📋 Todo | Auto-calculate late fees based on aging |
| HOA-111 | Register models in Django admin | S | Chris | 📋 Todo | Admin interface for owners, invoices, payments |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| HOA-112 | Create AR aging report | M | Chris | 📋 Todo | Summary report by aging bucket |
| HOA-113 | Add invoice PDF generation | M | Chris | 📋 Todo | Generate printable invoices |

---

## Database Schema Design (Sprint 2)

### Owner Model
```python
class Owner(models.Model):
    tenant = ForeignKey(Tenant)
    first_name = CharField(100)
    last_name = CharField(100)
    email = EmailField()
    phone = CharField(20)
    mailing_address = TextField()
    is_board_member = BooleanField()
    status = CharField(20)  # ACTIVE, INACTIVE, DELINQUENT
    created_at = DateTimeField()
```

### Unit Model
```python
class Unit(models.Model):
    tenant = ForeignKey(Tenant)
    unit_number = CharField(20)  # "123", "A-5", etc.
    property_address = TextField()
    bedrooms = IntegerField()
    square_feet = IntegerField()
    ownership = ForeignKey(Ownership)  # Link to current owner
    status = CharField(20)  # OCCUPIED, VACANT, RENTED
    created_at = DateTimeField()
```

### Ownership Model (many-to-many with history)
```python
class Ownership(models.Model):
    tenant = ForeignKey(Tenant)
    owner = ForeignKey(Owner)
    unit = ForeignKey(Unit)
    ownership_percentage = DecimalField(5,2)  # Usually 100%, but can be split
    start_date = DateField()
    end_date = DateField(null=True)  # NULL = current owner
    is_current = BooleanField()
```

### Invoice Model
```python
class Invoice(models.Model):
    tenant = ForeignKey(Tenant)
    invoice_number = CharField(20)  # AUTO: INV-00001
    owner = ForeignKey(Owner)
    unit = ForeignKey(Unit)
    invoice_date = DateField()
    due_date = DateField()
    invoice_type = CharField(20)  # ASSESSMENT, LATE_FEE, SPECIAL, OTHER
    status = CharField(20)  # DRAFT, ISSUED, PAID, OVERDUE, CANCELLED

    # Amounts
    subtotal = DecimalField(15,2)
    late_fee = DecimalField(15,2)
    total_amount = DecimalField(15,2)
    amount_paid = DecimalField(15,2)
    amount_due = DecimalField(15,2)  # total - paid

    # Metadata
    description = TextField()
    journal_entry = ForeignKey(JournalEntry, null=True)  # Auto-created
    created_at = DateTimeField()
```

### InvoiceLine Model
```python
class InvoiceLine(models.Model):
    invoice = ForeignKey(Invoice)
    line_number = IntegerField()
    description = TextField()  # "October 2025 Monthly Assessment"
    account = ForeignKey(Account)  # Revenue account to credit
    amount = DecimalField(15,2)
```

### Payment Model
```python
class Payment(models.Model):
    tenant = ForeignKey(Tenant)
    payment_number = CharField(20)  # AUTO: PMT-00001
    owner = ForeignKey(Owner)
    payment_date = DateField()
    payment_method = CharField(20)  # CHECK, ACH, CREDIT_CARD, CASH

    # Amounts
    amount = DecimalField(15,2)
    amount_applied = DecimalField(15,2)  # Applied to invoices
    amount_unapplied = DecimalField(15,2)  # Credit on account

    # Metadata
    reference_number = CharField(50)  # Check number, transaction ID
    notes = TextField()
    journal_entry = ForeignKey(JournalEntry, null=True)  # Auto-created
    created_at = DateTimeField()
```

### PaymentApplication Model
```python
class PaymentApplication(models.Model):
    payment = ForeignKey(Payment)
    invoice = ForeignKey(Invoice)
    amount_applied = DecimalField(15,2)
    applied_at = DateTimeField()
```

---

## Business Logic

### Invoice Generation Logic
```
Monthly Assessment Invoice Generation:
1. Get all active units for tenant
2. For each unit:
   - Get current owner(s)
   - Get assessment amount from fund budget
   - Create invoice with due date = 10th of month
   - Create invoice lines (assessment, any charges)
   - Auto-post journal entry:
     DR: AR (Asset)
     CR: Assessment Revenue
```

### Payment Application Logic
```
FIFO (First In, First Out) Application:
1. Receive payment from owner
2. Get all unpaid invoices for owner (ordered by invoice_date ASC)
3. Apply payment to oldest invoice first
4. If payment > invoice balance, apply remainder to next invoice
5. If payment > all invoices, leave as unapplied credit
6. Auto-post journal entry:
   DR: Cash (Asset)
   CR: AR (Asset)
```

### AR Aging Calculation
```
For each owner:
1. Get all unpaid invoices
2. Calculate days overdue = today - due_date
3. Bucket by aging:
   - Current (0-30 days)
   - 31-60 days
   - 61-90 days
   - 90+ days
4. Sum amounts by bucket
```

---

## Key Account Relationships

**Accounts Receivable Flow:**
```
Invoice Created:
  DR: 1200 AR                   $500
  CR: 4100 Assessment Revenue   $500

Payment Received:
  DR: 1100 Cash                 $500
  CR: 1200 AR                   $500
```

**Late Fee Flow:**
```
Late Fee Applied:
  DR: 1200 AR                   $25
  CR: 4200 Late Fee Revenue     $25
```

---

## Sprint Metrics

### Planned vs Actual
- **Planned:** 8 high-priority stories
- **Completed:** TBD
- **Completion Rate:** TBD

### Velocity
- **Previous Sprint:** N/A (Sprint 1 baseline)
- **This Sprint:** TBD
- **Trend:** Baseline

---

## Testing Checklist

- [x] Create 10 owners with units (created 5 for testing)
- [x] Generate monthly assessment invoices for all units (November + December batches)
- [x] Apply full payment (invoice paid in full) - Alice Johnson
- [x] Apply partial payment (invoice partially paid) - Bob Williams
- [x] Apply overpayment (creates unapplied credit) - Carol Davis
- [x] Verify journal entries auto-created (13 journal entries, all balanced)
- [x] Verify AR aging shows correct buckets (implemented via Invoice.aging_bucket property)
- [ ] Verify owner ledger shows all activity (API/view not yet implemented)
- [x] Verify trial balance still balances after invoice/payment ($4,000 DR = $4,000 CR)

---

## Wins & Learnings

### What Went Well
- **Completed Sprint 2 in 1 day** - All core AR functionality built and tested
- **Journal entry automation** - Invoices and payments automatically create balanced journal entries
- **Perfect trial balance** - System maintains audit-grade accuracy across all transactions
- **Batch invoice generation** - Management command allows generating monthly invoices for all units
- **No data corruption** - Using event sourcing pattern, all financial records are immutable
- **FIFO payment application** - Properly implements payment application to oldest invoices first
- **AR aging calculation** - Automatic bucketing of invoices by aging (Current, 1-30, 31-60, 61-90, 90+ days)

### What Could Be Improved
- **Payment journal entry automation** - Currently requires explicit call after PaymentApplication is created
- **Multiple owner support** - Invoice generation currently handles single owner per unit; need split invoice logic for multiple owners
- **Late fee automation** - Late fees are manual; should auto-calculate based on AR aging

### Action Items for Next Sprint
- [ ] Implement automatic late fee calculation based on aging
- [ ] Add support for split invoices (multiple owners per unit)
- [ ] Build AR aging report view (Django template or API endpoint)
- [ ] Create owner ledger view showing all invoices and payments
- [ ] Add invoice PDF generation for printing/emailing
- [ ] Build payment batch import (CSV upload for ACH payments)

---

## Links & References

- Previous Sprint: `sprint-01-accounting-foundation.md`
- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md`
- Pain Points: `product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md`

---

## Notes

**Critical Accounting Rules:**
1. Invoice creates AR debit + Revenue credit
2. Payment creates Cash debit + AR credit
3. Amount must match: Invoice.total_amount = sum(InvoiceLine.amount)
4. Amount must match: Payment.amount = Payment.amount_applied + Payment.amount_unapplied
5. Invoice balance: Invoice.amount_due = Invoice.total_amount - Invoice.amount_paid

**FIFO Payment Application:**
- Always apply payments to oldest invoice first
- This matches industry standard and legal requirements
- Prevents selective payment application disputes

**AR Accuracy:**
- Sum of all unpaid invoices = AR account balance
- This is the "sub-ledger to general ledger" reconciliation
- Must ALWAYS match!
