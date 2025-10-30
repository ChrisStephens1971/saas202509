"""
Budget Service - Business Logic for Budget Tracking

Handles:
- Budget variance calculation (actual vs budget)
- Monthly/quarterly/annual reporting
- Budget alerts and thresholds
"""

from datetime import date
from decimal import Decimal
from django.db.models import Sum, Q

from ..models import Budget, BudgetLine, JournalEntry, Account


class BudgetService:
    """Service for budget tracking business logic."""

    @staticmethod
    def calculate_variance(budget, as_of_date=None):
        """
        Calculate variance for all budget lines (actual vs budget).

        Args:
            budget: Budget instance
            as_of_date: Date to calculate actuals through (defaults to today)

        Returns:
            list: List of dicts with variance data per budget line
        """
        if not as_of_date:
            as_of_date = date.today()

        budget_lines = budget.budget_lines.all().select_related('account')
        variance_data = []

        for line in budget_lines:
            # Get actual spending from journal entries
            actual = BudgetService.get_actual_spending(
                line.account,
                budget.fiscal_year,
                as_of_date
            )

            # Calculate variance
            variance = actual - line.budgeted_amount
            variance_pct = (variance / line.budgeted_amount * 100) if line.budgeted_amount > 0 else Decimal('0.00')

            # Determine status
            if abs(variance_pct) <= 5:
                status = 'on_target'  # Within 5%
            elif variance_pct > 5:
                status = 'over_budget'  # Spending more than budgeted
            else:
                status = 'under_budget'  # Spending less than budgeted

            variance_data.append({
                'budget_line': line,
                'account': line.account,
                'budgeted_amount': line.budgeted_amount,
                'actual_amount': actual,
                'variance': variance,
                'variance_pct': variance_pct,
                'status': status,
            })

        return variance_data

    @staticmethod
    def get_actual_spending(account, fiscal_year, as_of_date):
        """
        Get actual spending for an account for a fiscal year.

        Args:
            account: Account instance
            fiscal_year: Fiscal year (e.g., 2025)
            as_of_date: Date to calculate through

        Returns:
            Decimal: Total actual spending
        """
        # Calculate date range for fiscal year
        start_date = date(fiscal_year, 1, 1)
        end_date = min(date(fiscal_year, 12, 31), as_of_date)

        # Get journal entries for this account in date range
        # Note: This is simplified - in production, would sum JournalEntryLine amounts
        # For MVP, we're showing the pattern

        # Placeholder calculation - would query JournalEntryLine in production
        # For now, return 0 as MVP doesn't have full GL implementation
        return Decimal('0.00')

    @staticmethod
    def get_monthly_variance(budget, month, year):
        """
        Get variance for a specific month.

        Args:
            budget: Budget instance
            month: Month number (1-12)
            year: Year

        Returns:
            dict: Monthly variance summary
        """
        as_of_date = date(year, month, 1)

        # Get month-to-date actuals
        variance_data = BudgetService.calculate_variance(budget, as_of_date)

        # Summarize
        total_budgeted = sum(item['budgeted_amount'] for item in variance_data)
        total_actual = sum(item['actual_amount'] for item in variance_data)
        total_variance = total_actual - total_budgeted

        return {
            'month': month,
            'year': year,
            'total_budgeted': total_budgeted,
            'total_actual': total_actual,
            'total_variance': total_variance,
            'variance_pct': (total_variance / total_budgeted * 100) if total_budgeted > 0 else Decimal('0.00'),
            'line_items': variance_data,
        }

    @staticmethod
    def get_budget_alerts(budget, threshold_pct=10):
        """
        Get budget lines that exceed variance threshold.

        Args:
            budget: Budget instance
            threshold_pct: Alert threshold percentage (default 10%)

        Returns:
            list: Budget lines exceeding threshold
        """
        variance_data = BudgetService.calculate_variance(budget)

        alerts = []
        for item in variance_data:
            if abs(item['variance_pct']) > threshold_pct:
                alerts.append({
                    'account': item['account'],
                    'budgeted': item['budgeted_amount'],
                    'actual': item['actual_amount'],
                    'variance': item['variance'],
                    'variance_pct': item['variance_pct'],
                    'severity': 'critical' if abs(item['variance_pct']) > 20 else 'warning',
                })

        return alerts

    @staticmethod
    def get_budget_summary(tenant):
        """
        Get summary of all budgets for a tenant.

        Returns:
            dict: Budget summary statistics
        """
        budgets = Budget.objects.filter(tenant=tenant)

        active_budgets = budgets.filter(
            fiscal_year=date.today().year,
            is_approved=True
        )

        return {
            'total_budgets': budgets.count(),
            'active_budgets': active_budgets.count(),
            'current_fiscal_year': date.today().year,
            'budgets': [
                {
                    'id': budget.id,
                    'name': budget.name,
                    'fiscal_year': budget.fiscal_year,
                    'is_approved': budget.is_approved,
                    'total_budgeted': sum(
                        line.budgeted_amount
                        for line in budget.budget_lines.all()
                    ),
                }
                for budget in active_budgets
            ],
        }

    @staticmethod
    def create_budget_from_template(tenant, fiscal_year, template_budget=None, increase_pct=3):
        """
        Create a new budget based on a template or previous year.

        Args:
            tenant: Tenant instance
            fiscal_year: Fiscal year for new budget
            template_budget: Budget to copy from (optional)
            increase_pct: Percentage increase to apply (default 3%)

        Returns:
            Budget: New budget instance
        """
        if not template_budget:
            # Use previous year's budget as template
            template_budget = Budget.objects.filter(
                tenant=tenant,
                fiscal_year=fiscal_year - 1
            ).first()

        if not template_budget:
            raise ValueError("No template budget found")

        # Create new budget
        new_budget = Budget.objects.create(
            tenant=tenant,
            name=f"{fiscal_year} Operating Budget",
            fiscal_year=fiscal_year,
            is_approved=False,
            notes=f"Created from {template_budget.name} with {increase_pct}% increase"
        )

        # Copy budget lines with increase
        multiplier = Decimal('1.0') + (Decimal(str(increase_pct)) / Decimal('100'))

        for line in template_budget.budget_lines.all():
            BudgetLine.objects.create(
                budget=new_budget,
                account=line.account,
                budgeted_amount=line.budgeted_amount * multiplier,
                notes=f"Based on {template_budget.fiscal_year} + {increase_pct}%"
            )

        return new_budget
