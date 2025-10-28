"""
Test late fee calculation and application.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoaaccounting.settings')
django.setup()

from tenants.models import Tenant
from accounting.models import Invoice, Owner, Unit

def main():
    print("=" * 80)
    print("LATE FEE CALCULATION TEST")
    print("=" * 80)
    print()

    tenant = Tenant.objects.get(schema_name="tenant_sunset_hills")

    # Get Bob Williams' November invoice (partial payment, should be overdue)
    bob = Owner.objects.get(tenant=tenant, email="bob@example.com")
    november_invoice = Invoice.objects.filter(
        tenant=tenant,
        owner=bob,
        invoice_date__month=11,
        invoice_date__year=2025
    ).first()

    if not november_invoice:
        print("[ERROR] Bob's November invoice not found")
        return

    print(f"Testing invoice: {november_invoice.invoice_number}")
    print(f"  Owner: {november_invoice.owner.first_name} {november_invoice.owner.last_name}")
    print(f"  Due date: {november_invoice.due_date}")
    print(f"  Amount due: ${november_invoice.amount_due}")
    print(f"  Days overdue: {november_invoice.days_overdue}")
    print(f"  Current late fee: ${november_invoice.late_fee}")
    print()

    # Calculate late fee with different grace periods
    print("Late Fee Calculations:")
    print("-" * 80)

    # Scenario 1: 5-day grace period (default)
    late_fee_5 = november_invoice.calculate_late_fee(grace_period_days=5)
    print(f"  5-day grace period: ${late_fee_5}")

    # Scenario 2: 10-day grace period
    late_fee_10 = november_invoice.calculate_late_fee(grace_period_days=10)
    print(f"  10-day grace period: ${late_fee_10}")

    # Scenario 3: 0-day grace period (immediate late fee)
    late_fee_0 = november_invoice.calculate_late_fee(grace_period_days=0)
    print(f"  0-day grace period: ${late_fee_0}")
    print()

    # Check if invoice is past grace period
    if november_invoice.days_overdue > 5:
        print("[INFO] Invoice is past 5-day grace period")
        print(f"  Calculated late fee: ${late_fee_5}")
        print()

        # Show what would happen if we apply the late fee
        print("If late fee is applied:")
        print(f"  Current total: ${november_invoice.total_amount}")
        print(f"  New total: ${november_invoice.total_amount + late_fee_5}")
        print(f"  Current amount due: ${november_invoice.amount_due}")
        print(f"  New amount due: ${november_invoice.amount_due + late_fee_5}")
        print()

        # Ask if user wants to apply
        response = input("Apply late fee to this invoice? (yes/no): ")
        if response.lower() == 'yes':
            print()
            print("Applying late fee...")
            late_fee_amount, je = november_invoice.apply_late_fee(grace_period_days=5)

            print(f"  [OK] Late fee applied: ${late_fee_amount}")
            if je:
                print(f"  [OK] Journal entry created: JE-{je.entry_number}")
                debits, credits = je.get_totals()
                print(f"  [OK] Journal entry balanced: ${debits} DR = ${credits} CR")

            # Refresh and show updated invoice
            november_invoice.refresh_from_db()
            print()
            print("Updated Invoice:")
            print(f"  Total amount: ${november_invoice.total_amount}")
            print(f"  Late fee: ${november_invoice.late_fee}")
            print(f"  Amount due: ${november_invoice.amount_due}")
        else:
            print("[INFO] Late fee not applied")
    else:
        print(f"[INFO] Invoice is NOT past 5-day grace period (only {november_invoice.days_overdue} days overdue)")
        print("[INFO] Late fee would be: $0.00")

    print()

if __name__ == "__main__":
    main()
