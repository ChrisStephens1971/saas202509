"""
Test script for HOA accounting system.

This script tests the core accounting functionality:
1. Create a tenant (HOA)
2. Create funds (operating, reserve)
3. Create accounts in chart of accounts
4. Post a balanced journal entry
5. Verify trial balance
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoaaccounting.settings')
django.setup()

from tenants.models import Tenant
from accounting.models import Fund, AccountType, Account, JournalEntry, JournalEntryLine


def test_accounting_system():
    print("=" * 80)
    print("HOA ACCOUNTING SYSTEM TEST")
    print("=" * 80)
    print()

    # Step 1: Create a test tenant
    print("Step 1: Creating test tenant...")
    tenant = Tenant.objects.create(
        name="Sunset Hills HOA",
        schema_name="tenant_sunset_hills",
        primary_contact_name="John Smith",
        primary_contact_email="john@sunsethills.com",
        total_units=125,
        address="123 Main St, Anytown, CA 90210",
        state="CA",
        status=Tenant.STATUS_TRIAL
    )
    print(f"[OK] Created tenant: {tenant.name} (ID: {tenant.id})")
    print(f"  Schema: {tenant.schema_name}")
    print(f"  Total units: {tenant.total_units}")
    print()

    # Step 2: Create funds
    print("Step 2: Creating funds...")
    operating_fund = Fund.objects.create(
        tenant=tenant,
        name="Operating Fund",
        fund_type=Fund.TYPE_OPERATING,
        description="Day-to-day operations and expenses"
    )
    print(f"[OK] Created {operating_fund.name}")

    reserve_fund = Fund.objects.create(
        tenant=tenant,
        name="Reserve Fund",
        fund_type=Fund.TYPE_RESERVE,
        description="Capital projects and replacements"
    )
    print(f"[OK] Created {reserve_fund.name}")
    print()

    # Step 3: Create accounts
    print("Step 3: Creating chart of accounts...")

    # Get account types
    asset_type = AccountType.objects.get(code='ASSET')
    revenue_type = AccountType.objects.get(code='REVENUE')
    expense_type = AccountType.objects.get(code='EXPENSE')

    # Operating Fund accounts
    cash_account = Account.objects.create(
        tenant=tenant,
        fund=operating_fund,
        account_type=asset_type,
        account_number="1100",
        name="Operating Cash",
        description="Main operating checking account"
    )
    print(f"[OK] Created {cash_account.account_number} - {cash_account.name}")

    assessment_revenue = Account.objects.create(
        tenant=tenant,
        fund=operating_fund,
        account_type=revenue_type,
        account_number="4100",
        name="Assessment Revenue",
        description="Monthly/quarterly/annual assessments"
    )
    print(f"[OK] Created {assessment_revenue.account_number} - {assessment_revenue.name}")

    landscaping_expense = Account.objects.create(
        tenant=tenant,
        fund=operating_fund,
        account_type=expense_type,
        account_number="5100",
        name="Landscaping Expense",
        description="Lawn care, tree trimming, etc."
    )
    print(f"[OK] Created {landscaping_expense.account_number} - {landscaping_expense.name}")
    print()

    # Step 4: Create a balanced journal entry
    print("Step 4: Creating balanced journal entry...")
    print("Transaction: Receive $50,000 in monthly assessments")

    journal_entry = JournalEntry.objects.create(
        tenant=tenant,
        entry_date=date(2025, 10, 1),
        description="October 2025 monthly assessments received",
        entry_type=JournalEntry.TYPE_INVOICE
    )
    print(f"[OK] Created Journal Entry #{journal_entry.entry_number}")
    print(f"  Date: {journal_entry.entry_date}")
    print(f"  Description: {journal_entry.description}")
    print()

    # Add journal entry lines
    print("  Adding journal entry lines:")

    # Debit: Cash (increase asset)
    debit_line = JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=1,
        account=cash_account,
        debit_amount=Decimal('50000.00'),
        credit_amount=Decimal('0.00'),
        description="Cash received from assessments"
    )
    print(f"    Line 1: DR {cash_account.account_number} ${debit_line.debit_amount}")

    # Credit: Assessment Revenue (increase revenue)
    credit_line = JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=2,
        account=assessment_revenue,
        debit_amount=Decimal('0.00'),
        credit_amount=Decimal('50000.00'),
        description="Revenue from monthly assessments"
    )
    print(f"    Line 2: CR {assessment_revenue.account_number} ${credit_line.credit_amount}")
    print()

    # Step 5: Verify journal entry balances
    print("Step 5: Verifying journal entry...")
    total_debits, total_credits = journal_entry.get_totals()
    is_balanced = journal_entry.is_balanced()

    print(f"  Total Debits:  ${total_debits}")
    print(f"  Total Credits: ${total_credits}")
    print(f"  Is Balanced:   {is_balanced}")

    if is_balanced:
        print("  [OK] Journal entry is balanced!")
    else:
        print("  [ERROR] ERROR: Journal entry is NOT balanced!")
        return False
    print()

    # Step 6: Create another journal entry (expense payment)
    print("Step 6: Creating expense payment journal entry...")
    print("Transaction: Pay $2,500 for landscaping services")

    payment_entry = JournalEntry.objects.create(
        tenant=tenant,
        entry_date=date(2025, 10, 15),
        description="October landscaping payment",
        entry_type=JournalEntry.TYPE_PAYMENT
    )
    print(f"[OK] Created Journal Entry #{payment_entry.entry_number}")

    # Debit: Landscaping Expense (increase expense)
    JournalEntryLine.objects.create(
        journal_entry=payment_entry,
        line_number=1,
        account=landscaping_expense,
        debit_amount=Decimal('2500.00'),
        credit_amount=Decimal('0.00'),
        description="Landscaping services for October"
    )
    print(f"    Line 1: DR {landscaping_expense.account_number} $2,500.00")

    # Credit: Cash (decrease asset)
    JournalEntryLine.objects.create(
        journal_entry=payment_entry,
        line_number=2,
        account=cash_account,
        debit_amount=Decimal('0.00'),
        credit_amount=Decimal('2500.00'),
        description="Payment for landscaping"
    )
    print(f"    Line 2: CR {cash_account.account_number} $2,500.00")
    print()

    # Verify second entry
    total_debits2, total_credits2 = payment_entry.get_totals()
    print(f"  Total Debits:  ${total_debits2}")
    print(f"  Total Credits: ${total_credits2}")
    print(f"  Is Balanced:   {payment_entry.is_balanced()}")
    print()

    # Step 7: Calculate account balances
    print("Step 7: Calculating account balances...")
    print()
    print("TRIAL BALANCE - Sunset Hills HOA - Operating Fund")
    print("-" * 80)
    print(f"{'Account':<40} {'Debit':>15} {'Credit':>15}")
    print("-" * 80)

    # Get all accounts for this tenant's operating fund
    accounts = Account.objects.filter(tenant=tenant, fund=operating_fund).order_by('account_number')

    total_trial_debits = Decimal('0.00')
    total_trial_credits = Decimal('0.00')

    for account in accounts:
        balance = account.get_balance()

        # Format for trial balance (normal balance side)
        if account.account_type.normal_balance == 'DEBIT':
            if balance >= 0:
                debit_amt = balance
                credit_amt = Decimal('0.00')
            else:
                debit_amt = Decimal('0.00')
                credit_amt = abs(balance)
        else:  # CREDIT normal balance
            if balance >= 0:
                debit_amt = Decimal('0.00')
                credit_amt = balance
            else:
                debit_amt = abs(balance)
                credit_amt = Decimal('0.00')

        total_trial_debits += debit_amt
        total_trial_credits += credit_amt

        account_name = f"{account.account_number} {account.name}"
        debit_str = f"${debit_amt:,.2f}" if debit_amt > 0 else ""
        credit_str = f"${credit_amt:,.2f}" if credit_amt > 0 else ""

        print(f"{account_name:<40} {debit_str:>15} {credit_str:>15}")

    print("-" * 80)
    print(f"{'TOTALS':<40} ${total_trial_debits:>14,.2f} ${total_trial_credits:>14,.2f}")
    print("=" * 80)

    # Verify trial balance
    print()
    if total_trial_debits == total_trial_credits:
        print("[OK] TRIAL BALANCE IS BALANCED!")
        print(f"  Total Debits = Total Credits = ${total_trial_debits:,.2f}")
    else:
        print("[ERROR] ERROR: TRIAL BALANCE DOES NOT BALANCE!")
        print(f"  Difference: ${abs(total_trial_debits - total_trial_credits):,.2f}")
        return False

    print()
    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Created tenant: {tenant.name}")
    print(f"  - Created {Fund.objects.filter(tenant=tenant).count()} funds")
    print(f"  - Created {Account.objects.filter(tenant=tenant).count()} accounts")
    print(f"  - Posted {JournalEntry.objects.filter(tenant=tenant).count()} journal entries")
    print(f"  - Created {JournalEntryLine.objects.filter(journal_entry__tenant=tenant).count()} journal entry lines")
    print(f"  - Trial balance is BALANCED: ${total_trial_debits:,.2f}")
    print()
    print("Next steps:")
    print("  1. Create Django superuser: python manage.py createsuperuser")
    print("  2. Run development server: python manage.py runserver 8009")
    print("  3. Access admin: http://localhost:8009/admin/")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_accounting_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
