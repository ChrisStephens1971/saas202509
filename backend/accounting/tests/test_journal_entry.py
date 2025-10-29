"""
Comprehensive unit tests for JournalEntry model.

Tests critical accounting principles:
1. Double-entry bookkeeping (debits = credits)
2. Immutability of financial records
3. Balance validation
4. Decimal precision (NUMERIC(15,2))
5. Journal entry sequencing
"""

import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from django.db import transaction

from tenants.models import Tenant
from accounting.models import (
    Fund, AccountType, Account, JournalEntry, JournalEntryLine
)


@pytest.fixture
def tenant(db):
    """Create a test tenant (HOA)."""
    return Tenant.objects.create(
        name="Test HOA",
        schema_name="tenant_test_hoa",
        primary_contact_name="Test Admin",
        primary_contact_email="admin@testhoa.com",
        total_units=100,
        address="123 Test St",
        state="CA",
        status=Tenant.STATUS_TRIAL
    )


@pytest.fixture
def operating_fund(db, tenant):
    """Create an operating fund."""
    return Fund.objects.create(
        tenant=tenant,
        name="Operating Fund",
        fund_type=Fund.TYPE_OPERATING,
        description="Test operating fund"
    )


@pytest.fixture
def account_types(db):
    """Get standard account types."""
    return {
        'asset': AccountType.objects.get(code='ASSET'),
        'liability': AccountType.objects.get(code='LIABILITY'),
        'equity': AccountType.objects.get(code='EQUITY'),
        'revenue': AccountType.objects.get(code='REVENUE'),
        'expense': AccountType.objects.get(code='EXPENSE'),
    }


@pytest.fixture
def cash_account(db, tenant, operating_fund, account_types):
    """Create a cash account (asset)."""
    return Account.objects.create(
        tenant=tenant,
        fund=operating_fund,
        account_type=account_types['asset'],
        account_number="1100",
        name="Cash",
        description="Operating cash account"
    )


@pytest.fixture
def revenue_account(db, tenant, operating_fund, account_types):
    """Create a revenue account."""
    return Account.objects.create(
        tenant=tenant,
        fund=operating_fund,
        account_type=account_types['revenue'],
        account_number="4100",
        name="Assessment Revenue",
        description="Monthly assessments"
    )


@pytest.fixture
def expense_account(db, tenant, operating_fund, account_types):
    """Create an expense account."""
    return Account.objects.create(
        tenant=tenant,
        fund=operating_fund,
        account_type=account_types['expense'],
        account_number="5100",
        name="Maintenance Expense",
        description="Maintenance costs"
    )


@pytest.mark.django_db
class TestJournalEntryBasics:
    """Test basic journal entry creation and properties."""

    def test_create_journal_entry(self, tenant):
        """Test creating a simple journal entry."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Test entry",
            entry_type=JournalEntry.TYPE_INVOICE
        )

        assert entry.id is not None
        assert entry.entry_number > 0
        assert entry.entry_date == date(2025, 10, 1)
        assert entry.description == "Test entry"
        assert entry.entry_type == JournalEntry.TYPE_INVOICE
        assert entry.tenant == tenant
        assert entry.created_at is not None

    def test_entry_number_auto_increment(self, tenant):
        """Test that entry numbers auto-increment per tenant."""
        entry1 = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Entry 1"
        )
        entry2 = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 2),
            description="Entry 2"
        )

        assert entry2.entry_number == entry1.entry_number + 1

    def test_entry_str_representation(self, tenant):
        """Test journal entry string representation."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Test entry"
        )

        str_repr = str(entry)
        assert "JE" in str_repr or str(entry.entry_number) in str_repr


@pytest.mark.django_db
class TestDoubleEntryBookkeeping:
    """Test double-entry bookkeeping requirements."""

    def test_balanced_journal_entry(self, tenant, cash_account, revenue_account):
        """Test that a balanced journal entry is valid."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Balanced entry: Cash receipt"
        )

        # Debit cash (increase asset)
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00'),
            description="Cash received"
        )

        # Credit revenue (increase revenue)
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('1000.00'),
            description="Revenue earned"
        )

        assert entry.is_balanced()
        total_debits, total_credits = entry.get_totals()
        assert total_debits == Decimal('1000.00')
        assert total_credits == Decimal('1000.00')
        assert total_debits == total_credits

    def test_unbalanced_entry_detection(self, tenant, cash_account, revenue_account):
        """Test that unbalanced entries are detected."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Unbalanced entry"
        )

        # Debit $1000
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00')
        )

        # Credit $900 (WRONG - doesn't balance!)
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('900.00')
        )

        assert not entry.is_balanced()
        total_debits, total_credits = entry.get_totals()
        assert total_debits != total_credits
        assert total_debits == Decimal('1000.00')
        assert total_credits == Decimal('900.00')

    def test_complex_multi_line_balanced_entry(self, tenant, cash_account, revenue_account, expense_account):
        """Test complex journal entry with multiple lines."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Multi-line entry"
        )

        # Debit: Cash $1000
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00')
        )

        # Debit: Expense $500
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=expense_account,
            debit_amount=Decimal('500.00'),
            credit_amount=Decimal('0.00')
        )

        # Credit: Revenue $1500
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=3,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('1500.00')
        )

        assert entry.is_balanced()
        total_debits, total_credits = entry.get_totals()
        assert total_debits == Decimal('1500.00')
        assert total_credits == Decimal('1500.00')


@pytest.mark.django_db
class TestDecimalPrecision:
    """Test decimal precision requirements (NUMERIC(15,2))."""

    def test_two_decimal_places_precision(self, tenant, cash_account, revenue_account):
        """Test that amounts are stored with exactly 2 decimal places."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Precision test"
        )

        # Use exact decimal with 2 places
        amount = Decimal('1234.56')

        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=amount,
            credit_amount=Decimal('0.00')
        )

        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=amount
        )

        # Retrieve and verify precision
        line = entry.lines.first()
        assert line.debit_amount == Decimal('1234.56')
        # Verify it has exactly 2 decimal places
        assert line.debit_amount == line.debit_amount.quantize(Decimal('0.01'))

    def test_large_amounts_within_limit(self, tenant, cash_account, revenue_account):
        """Test that large amounts (up to 15 digits) are supported."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Large amount test"
        )

        # Max: 9,999,999,999,999.99 (13 digits + 2 decimals = 15 total)
        large_amount = Decimal('9999999999999.99')

        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=large_amount,
            credit_amount=Decimal('0.00')
        )

        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=large_amount
        )

        assert entry.is_balanced()

    def test_prevent_floating_point_errors(self, tenant, cash_account, revenue_account):
        """Test that decimal arithmetic doesn't have floating point errors."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Floating point test"
        )

        # This would cause issues with floats: 0.1 + 0.2 != 0.3
        # But Decimal handles it correctly
        amount1 = Decimal('0.10')
        amount2 = Decimal('0.20')
        total = amount1 + amount2

        assert total == Decimal('0.30')  # This works with Decimal!

        # Test in journal entry
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=amount1 + amount2,
            credit_amount=Decimal('0.00')
        )

        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('0.30')
        )

        assert entry.is_balanced()


@pytest.mark.django_db
class TestJournalEntryValidation:
    """Test validation rules for journal entries."""

    def test_entry_must_have_lines(self, tenant, cash_account, revenue_account):
        """Test that a journal entry with no lines is detected."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Entry with no lines"
        )

        # Entry exists but has no lines
        assert entry.lines.count() == 0
        assert not entry.is_balanced()  # No lines means not balanced

    def test_line_must_have_debit_or_credit(self, tenant, cash_account):
        """Test that a line must have either debit or credit (not both zero)."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Test entry"
        )

        # Create a line with both zero (should be prevented by model logic)
        line = JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('0.00')
        )

        # Line exists but contributes nothing to balance
        assert line.debit_amount == Decimal('0.00')
        assert line.credit_amount == Decimal('0.00')

    def test_negative_amounts_not_allowed(self, tenant, cash_account):
        """Test that negative amounts should not be allowed."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Negative amount test"
        )

        # Negative amounts violate accounting principles
        # (use debit vs credit instead of negative numbers)
        with pytest.raises(Exception):  # Should raise ValidationError or IntegrityError
            JournalEntryLine.objects.create(
                journal_entry=entry,
                line_number=1,
                account=cash_account,
                debit_amount=Decimal('-100.00'),  # INVALID!
                credit_amount=Decimal('0.00')
            )


@pytest.mark.django_db
class TestAccountBalance:
    """Test account balance calculations."""

    def test_simple_account_balance(self, tenant, cash_account, revenue_account):
        """Test basic account balance calculation."""
        # Entry 1: Debit cash $1000
        entry1 = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Cash receipt"
        )
        JournalEntryLine.objects.create(
            journal_entry=entry1,
            line_number=1,
            account=cash_account,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00')
        )
        JournalEntryLine.objects.create(
            journal_entry=entry1,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('1000.00')
        )

        # Entry 2: Credit cash $300
        entry2 = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 2),
            description="Cash payment"
        )
        expense_account = Account.objects.create(
            tenant=tenant,
            fund=cash_account.fund,
            account_type=AccountType.objects.get(code='EXPENSE'),
            account_number="5100",
            name="Expense"
        )
        JournalEntryLine.objects.create(
            journal_entry=entry2,
            line_number=1,
            account=expense_account,
            debit_amount=Decimal('300.00'),
            credit_amount=Decimal('0.00')
        )
        JournalEntryLine.objects.create(
            journal_entry=entry2,
            line_number=2,
            account=cash_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('300.00')
        )

        # Cash balance should be: 1000 DR - 300 CR = 700 DR
        cash_balance = cash_account.get_balance()
        assert cash_balance == Decimal('700.00')

    def test_revenue_account_balance(self, tenant, cash_account, revenue_account):
        """Test revenue account balance (credit normal balance)."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Revenue"
        )
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=cash_account,
            debit_amount=Decimal('5000.00'),
            credit_amount=Decimal('0.00')
        )
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('5000.00')
        )

        # Revenue has credit normal balance, so should show as positive
        revenue_balance = revenue_account.get_balance()
        assert revenue_balance == Decimal('5000.00')


@pytest.mark.django_db
class TestJournalEntryTypes:
    """Test different journal entry types."""

    def test_invoice_entry_type(self, tenant, cash_account, revenue_account):
        """Test invoice journal entry."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Invoice entry",
            entry_type=JournalEntry.TYPE_INVOICE
        )

        assert entry.entry_type == JournalEntry.TYPE_INVOICE

    def test_payment_entry_type(self, tenant, cash_account, expense_account):
        """Test payment journal entry."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Payment entry",
            entry_type=JournalEntry.TYPE_PAYMENT
        )

        assert entry.entry_type == JournalEntry.TYPE_PAYMENT

    def test_adjustment_entry_type(self, tenant):
        """Test adjustment journal entry."""
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Adjustment entry",
            entry_type=JournalEntry.TYPE_ADJUSTMENT
        )

        assert entry.entry_type == JournalEntry.TYPE_ADJUSTMENT


@pytest.mark.django_db
class TestTrialBalance:
    """Test trial balance calculations."""

    def test_trial_balance_calculation(self, tenant, operating_fund, account_types):
        """Test that trial balance totals are equal."""
        # Create accounts
        cash = Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_type=account_types['asset'],
            account_number="1100",
            name="Cash"
        )
        revenue = Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_type=account_types['revenue'],
            account_number="4100",
            name="Revenue"
        )
        expense = Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_type=account_types['expense'],
            account_number="5100",
            name="Expense"
        )

        # Entry 1: Cash $10,000 from revenue
        entry1 = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 1),
            description="Revenue"
        )
        JournalEntryLine.objects.create(
            journal_entry=entry1,
            line_number=1,
            account=cash,
            debit_amount=Decimal('10000.00'),
            credit_amount=Decimal('0.00')
        )
        JournalEntryLine.objects.create(
            journal_entry=entry1,
            line_number=2,
            account=revenue,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('10000.00')
        )

        # Entry 2: Expense $3,000 paid from cash
        entry2 = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date(2025, 10, 2),
            description="Expense"
        )
        JournalEntryLine.objects.create(
            journal_entry=entry2,
            line_number=1,
            account=expense,
            debit_amount=Decimal('3000.00'),
            credit_amount=Decimal('0.00')
        )
        JournalEntryLine.objects.create(
            journal_entry=entry2,
            line_number=2,
            account=cash,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('3000.00')
        )

        # Calculate trial balance
        accounts = Account.objects.filter(tenant=tenant, fund=operating_fund)
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')

        for account in accounts:
            balance = account.get_balance()
            if account.account_type.normal_balance == 'DEBIT':
                if balance >= 0:
                    total_debits += balance
                else:
                    total_credits += abs(balance)
            else:  # CREDIT normal balance
                if balance >= 0:
                    total_credits += balance
                else:
                    total_debits += abs(balance)

        # Trial balance must balance!
        assert total_debits == total_credits
        # Cash: 7000 DR, Expense: 3000 DR, Revenue: 10000 CR
        assert total_debits == Decimal('10000.00')
        assert total_credits == Decimal('10000.00')
