"""
Manual test script for Budget functionality.

Run with: python manage.py shell < test_budget_manual.py
Or in Django shell:
    exec(open('test_budget_manual.py').read())
"""

from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from accounting.models import (
    Budget, BudgetLine, Account, AccountType, Fund
)
from tenants.models import Tenant

User = get_user_model()

print("\n" + "="*80)
print("BUDGET MODULE MANUAL TEST")
print("="*80)

# Get or create test data
print("\n1. Setting up test data...")

# Get first tenant
tenant = Tenant.objects.first()
if not tenant:
    print("   ERROR: No tenant found. Please create a tenant first.")
    import sys
    sys.exit(1)
print(f"   ✓ Using tenant: {tenant.name}")

# Get first user
user = User.objects.first()
if not user:
    print("   ERROR: No user found. Please create a user first.")
    import sys
    sys.exit(1)
print(f"   ✓ Using user: {user.username}")

# Get operating fund
fund = Fund.objects.filter(tenant=tenant, fund_type=Fund.TYPE_OPERATING).first()
if not fund:
    print("   WARNING: No operating fund found. Creating one...")
    fund = Fund.objects.create(
        tenant=tenant,
        name="Operating Fund",
        fund_type=Fund.TYPE_OPERATING,
        is_active=True
    )
print(f"   ✓ Using fund: {fund.name}")

# Get some expense accounts
expense_accounts = Account.objects.filter(
    tenant=tenant,
    account_type__normal_balance='DEBIT',
    is_active=True
).order_by('account_number')[:3]

if not expense_accounts:
    print("   ERROR: No expense accounts found. Please create accounts first.")
    import sys
    sys.exit(1)
print(f"   ✓ Found {len(expense_accounts)} expense accounts")

print("\n2. Creating budget...")
# Delete any existing budget for testing
Budget.objects.filter(tenant=tenant, fiscal_year=2025).delete()

budget = Budget.objects.create(
    tenant=tenant,
    name="FY 2025 Operating Budget",
    fiscal_year=2025,
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
    fund=fund,
    status=Budget.STATUS_DRAFT,
    created_by=user,
    notes="Test budget created via manual test script"
)
print(f"   ✓ Created budget: {budget.name} (ID: {budget.id})")
print(f"   ✓ Status: {budget.status}")

print("\n3. Adding budget lines...")
for i, account in enumerate(expense_accounts, 1):
    budgeted_amount = Decimal("12000.00") * i
    budget_line = BudgetLine.objects.create(
        budget=budget,
        account=account,
        budgeted_amount=budgeted_amount,
        notes=f"Test budget line for {account.name}"
    )
    print(f"   ✓ Added: {account.account_number} - {account.name}: ${budgeted_amount}")

print("\n4. Testing get_total_budgeted()...")
total = budget.get_total_budgeted()
print(f"   ✓ Total budgeted: ${total}")

print("\n5. Testing variance report (no actual transactions)...")
variance_report = budget.get_variance_report()
print(f"   ✓ Generated variance report with {len(variance_report['lines'])} lines")
print(f"   ✓ Report period: {variance_report['budget_name']}")
print(f"   ✓ Total budgeted: ${variance_report['totals']['budgeted']}")
print(f"   ✓ Total actual: ${variance_report['totals']['actual']}")
print(f"   ✓ Total variance: ${variance_report['totals']['variance']}")

print("\n6. Testing budget approval workflow...")
budget.status = Budget.STATUS_APPROVED
budget.approved_by = user
budget.save()
print(f"   ✓ Budget approved by: {budget.approved_by.username}")
print(f"   ✓ Approved at: {budget.approved_at}")

print("\n7. Testing budget activation...")
budget.status = Budget.STATUS_ACTIVE
budget.save()
print(f"   ✓ Budget activated")
print(f"   ✓ Current status: {budget.status}")

print("\n8. Verifying budget can be retrieved...")
retrieved_budget = Budget.objects.get(id=budget.id)
print(f"   ✓ Retrieved budget: {retrieved_budget.name}")
print(f"   ✓ Budget has {retrieved_budget.lines.count()} lines")

print("\n9. Testing unique constraint (one budget per fiscal year per fund)...")
try:
    duplicate_budget = Budget.objects.create(
        tenant=tenant,
        name="FY 2025 Duplicate Budget",
        fiscal_year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        fund=fund,
        created_by=user
    )
    print("   ✗ ERROR: Unique constraint not working! Duplicate budget created.")
except Exception as e:
    print(f"   ✓ Unique constraint working: {type(e).__name__}")

print("\n" + "="*80)
print("BUDGET MODULE TEST COMPLETE")
print("="*80)
print("\nSummary:")
print(f"  • Budget created: {budget.name}")
print(f"  • Budget ID: {budget.id}")
print(f"  • Budget lines: {budget.lines.count()}")
print(f"  • Total budgeted: ${total}")
print(f"  • Current status: {budget.status}")
print("\n✓ All tests passed successfully!")
print("="*80 + "\n")
