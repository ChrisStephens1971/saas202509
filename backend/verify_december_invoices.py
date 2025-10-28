"""
Verify December 2025 invoices and trial balance
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoaaccounting.settings')
django.setup()

from decimal import Decimal
from tenants.models import Tenant
from accounting.models import (
    Account, JournalEntry, JournalEntryLine, Invoice, Fund
)

def main():
    print("=" * 80)
    print("DECEMBER 2025 INVOICE VERIFICATION")
    print("=" * 80)
    print()

    tenant = Tenant.objects.get(schema_name="tenant_sunset_hills")

    # Get December invoices
    december_invoices = Invoice.objects.filter(
        tenant=tenant,
        invoice_date__month=12,
        invoice_date__year=2025
    ).order_by('invoice_number')

    print(f"December 2025 Invoices: {december_invoices.count()}")
    print("-" * 80)

    total_dec_invoiced = Decimal('0.00')
    for inv in december_invoices:
        has_je = "YES" if inv.journal_entry else "NO"
        print(f"  {inv.invoice_number}: {inv.owner.first_name} {inv.owner.last_name:<15} "
              f"${inv.total_amount:>8.2f}  JE: {has_je}")
        total_dec_invoiced += inv.total_amount

    print(f"\nTotal December invoiced: ${total_dec_invoiced:,.2f}")
    print()

    # Get all journal entries
    je_count = JournalEntry.objects.filter(tenant=tenant).count()
    print(f"Total journal entries: {je_count}")

    # Recent journal entries
    recent_jes = JournalEntry.objects.filter(tenant=tenant).order_by('-entry_number')[:5]
    print("\nRecent Journal Entries:")
    print("-" * 80)
    for je in recent_jes:
        debits, credits = je.get_totals()
        balanced = "OK" if je.is_balanced else "!!"
        print(f"  JE-{je.entry_number:03d} [{balanced}] {je.entry_type:<12} ${debits:>8.2f} DR / ${credits:>8.2f} CR")
    print()

    # Trial Balance
    operating_fund = Fund.objects.filter(
        tenant=tenant,
        fund_type=Fund.TYPE_OPERATING
    ).first()

    accounts = Account.objects.filter(
        tenant=tenant,
        fund=operating_fund
    ).order_by('account_number')

    print("TRIAL BALANCE")
    print("-" * 80)
    print(f"{'Account':<40} {'Debit':>15} {'Credit':>15}")
    print("-" * 80)

    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for account in accounts:
        balance = account.get_balance()

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

        total_debits += debit_amt
        total_credits += credit_amt

        account_name = f"{account.account_number} {account.name}"
        debit_str = f"${debit_amt:,.2f}" if debit_amt > 0 else ""
        credit_str = f"${credit_amt:,.2f}" if credit_amt > 0 else ""

        print(f"{account_name:<40} {debit_str:>15} {credit_str:>15}")

    print("-" * 80)
    print(f"{'TOTALS':<40} ${total_debits:>14,.2f} ${total_credits:>14,.2f}")
    print("=" * 80)
    print()

    if total_debits == total_credits:
        print("[OK] TRIAL BALANCE IS BALANCED!")
        print(f"  Total Debits = Total Credits = ${total_debits:,.2f}")
    else:
        print("[ERROR] TRIAL BALANCE DOES NOT BALANCE!")
        print(f"  Difference: ${abs(total_debits - total_credits):,.2f}")

    print()

if __name__ == "__main__":
    main()
