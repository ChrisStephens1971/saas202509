"""
Tests for Budget functionality.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from accounting.models import (
    Budget, BudgetLine, Account, AccountType, Fund,
    JournalEntry, JournalEntryLine
)
from tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    return Tenant.objects.create(
        name="Test HOA",
        schema_name="test_hoa",
        domain="test-hoa.localhost"
    )


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def fund(db, tenant):
    """Create an operating fund."""
    return Fund.objects.create(
        tenant=tenant,
        name="Operating Fund",
        fund_type=Fund.TYPE_OPERATING,
        is_active=True
    )


@pytest.fixture
def expense_account_type(db):
    """Create expense account type."""
    return AccountType.objects.create(
        name="Expense",
        normal_balance="DEBIT"
    )


@pytest.fixture
def expense_account(db, tenant, fund, expense_account_type):
    """Create an expense account for testing."""
    return Account.objects.create(
        tenant=tenant,
        account_number="5100",
        name="Landscaping Expense",
        account_type=expense_account_type,
        fund=fund,
        is_active=True
    )


@pytest.fixture
def revenue_account_type(db):
    """Create revenue account type."""
    return AccountType.objects.create(
        name="Revenue",
        normal_balance="CREDIT"
    )


@pytest.fixture
def revenue_account(db, tenant, fund, revenue_account_type):
    """Create a revenue account for testing."""
    return Account.objects.create(
        tenant=tenant,
        account_number="4000",
        name="Assessment Revenue",
        account_type=revenue_account_type,
        fund=fund,
        is_active=True
    )


@pytest.mark.django_db
class TestBudgetModel:
    """Test Budget model functionality."""

    def test_create_budget(self, tenant, user, fund):
        """Test creating a budget."""
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            status=Budget.STATUS_DRAFT,
            created_by=user
        )

        assert budget.id is not None
        assert budget.name == "FY 2025 Operating Budget"
        assert budget.fiscal_year == 2025
        assert budget.status == Budget.STATUS_DRAFT

    def test_budget_lines(self, tenant, user, fund, expense_account):
        """Test adding budget lines to a budget."""
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            created_by=user
        )

        budget_line = BudgetLine.objects.create(
            budget=budget,
            account=expense_account,
            budgeted_amount=Decimal("12000.00"),
            notes="Monthly landscaping service"
        )

        assert budget_line.id is not None
        assert budget_line.budgeted_amount == Decimal("12000.00")
        assert budget.lines.count() == 1

    def test_get_total_budgeted(self, tenant, user, fund, expense_account, revenue_account):
        """Test calculating total budgeted amount."""
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            created_by=user
        )

        BudgetLine.objects.create(
            budget=budget,
            account=expense_account,
            budgeted_amount=Decimal("12000.00")
        )

        BudgetLine.objects.create(
            budget=budget,
            account=revenue_account,
            budgeted_amount=Decimal("50000.00")
        )

        total = budget.get_total_budgeted()
        assert total == Decimal("62000.00")

    def test_budget_approval(self, tenant, user, fund):
        """Test budget approval workflow."""
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            status=Budget.STATUS_DRAFT,
            created_by=user
        )

        # Approve budget
        budget.status = Budget.STATUS_APPROVED
        budget.approved_by = user
        budget.save()

        assert budget.status == Budget.STATUS_APPROVED
        assert budget.approved_by == user
        assert budget.approved_at is not None

    def test_variance_report_expense(self, tenant, user, fund, expense_account):
        """Test variance report calculation for expense accounts."""
        # Create budget
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            created_by=user
        )

        # Add budget line - budgeted $12,000 for landscaping
        BudgetLine.objects.create(
            budget=budget,
            account=expense_account,
            budgeted_amount=Decimal("12000.00")
        )

        # Create journal entry with actual expense of $10,000
        journal_entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_number="JE-2025-001",
            entry_date=date(2025, 6, 15),
            description="Landscaping expense",
            entry_type=JournalEntry.TYPE_STANDARD
        )

        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=expense_account,
            debit_amount=Decimal("10000.00"),
            credit_amount=Decimal("0.00"),
            description="Landscaping service"
        )

        # Get variance report
        report = budget.get_variance_report()

        assert len(report['lines']) == 1
        line = report['lines'][0]
        assert line['budgeted'] == "12000.00"
        assert line['actual'] == "10000.00"
        assert line['variance'] == "2000.00"
        assert line['status'] == 'favorable'  # Under budget is favorable for expenses

    def test_variance_report_revenue(self, tenant, user, fund, revenue_account):
        """Test variance report calculation for revenue accounts."""
        # Create budget
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            created_by=user
        )

        # Add budget line - budgeted $50,000 for revenue
        BudgetLine.objects.create(
            budget=budget,
            account=revenue_account,
            budgeted_amount=Decimal("50000.00")
        )

        # Create journal entry with actual revenue of $55,000
        journal_entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_number="JE-2025-002",
            entry_date=date(2025, 6, 15),
            description="Assessment revenue",
            entry_type=JournalEntry.TYPE_STANDARD
        )

        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=revenue_account,
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("55000.00"),
            description="Monthly assessments"
        )

        # Get variance report
        report = budget.get_variance_report()

        assert len(report['lines']) == 1
        line = report['lines'][0]
        assert line['budgeted'] == "50000.00"
        assert line['actual'] == "55000.00"
        assert line['variance'] == "5000.00"
        assert line['status'] == 'favorable'  # Over budget is favorable for revenue

    def test_unique_constraint(self, tenant, user, fund):
        """Test that only one budget per fiscal year per fund is allowed."""
        Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            created_by=user
        )

        # Try to create duplicate budget for same fiscal year and fund
        with pytest.raises(Exception):  # Should raise IntegrityError
            Budget.objects.create(
                tenant=tenant,
                name="FY 2025 Operating Budget V2",
                fiscal_year=2025,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                fund=fund,
                created_by=user
            )


@pytest.mark.django_db
class TestBudgetLineModel:
    """Test BudgetLine model functionality."""

    def test_unique_account_per_budget(self, tenant, user, fund, expense_account):
        """Test that each account can only appear once per budget."""
        budget = Budget.objects.create(
            tenant=tenant,
            name="FY 2025 Operating Budget",
            fiscal_year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            fund=fund,
            created_by=user
        )

        BudgetLine.objects.create(
            budget=budget,
            account=expense_account,
            budgeted_amount=Decimal("12000.00")
        )

        # Try to add same account again
        with pytest.raises(Exception):  # Should raise IntegrityError
            BudgetLine.objects.create(
                budget=budget,
                account=expense_account,
                budgeted_amount=Decimal("15000.00")
            )
