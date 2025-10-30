"""
Management Command: Check Budget Variances

Monitors budget line items for variance thresholds and sends alerts.

Usage:
    python manage.py check_budget_variances

Schedule:
    Run weekly or monthly via cron job (e.g., Monday 8:00 AM)

Process:
    1. Find all active budgets
    2. Calculate actual spend for each line item
    3. Compare against budgeted amount
    4. Alert if variance exceeds thresholds (20% warning, 30% critical)
    5. Send email notification to treasurer
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Q
from accounting.models import Budget, BudgetLineItem, JournalEntry
from accounting.services import NotificationService
from decimal import Decimal


class Command(BaseCommand):
    help = 'Check budget variances and send alerts for items exceeding thresholds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--budget-id',
            type=str,
            help='Check only a specific budget (by ID)',
        )
        parser.add_argument(
            '--warning-threshold',
            type=float,
            default=20.0,
            help='Warning threshold percentage (default: 20%)',
        )
        parser.add_argument(
            '--critical-threshold',
            type=float,
            default=30.0,
            help='Critical threshold percentage (default: 30%)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be alerted without sending notifications',
        )

    def handle(self, *args, **options):
        budget_id = options.get('budget_id')
        warning_threshold = Decimal(str(options['warning_threshold']))
        critical_threshold = Decimal(str(options['critical_threshold']))
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('BUDGET VARIANCE MONITORING'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Run Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'Mode: {"DRY RUN" if dry_run else "LIVE"}')
        self.stdout.write(f'Warning Threshold: {warning_threshold}%')
        self.stdout.write(f'Critical Threshold: {critical_threshold}%')
        self.stdout.write('')

        # Find active budgets
        budgets = Budget.objects.filter(status='active').select_related('tenant')

        if budget_id:
            budgets = budgets.filter(id=budget_id)

        if not budgets.exists():
            self.stdout.write(self.style.SUCCESS('✓ No active budgets found'))
            return

        self.stdout.write(f'Checking {budgets.count()} active budget(s)')
        self.stdout.write('')

        total_alerts = 0

        for budget in budgets:
            self.stdout.write(self.style.SUCCESS(f'Budget: {budget.name}'))
            self.stdout.write(f'Period: {budget.fiscal_year} ({budget.start_date} to {budget.end_date})')
            self.stdout.write('')

            # Get all line items for this budget
            line_items = BudgetLineItem.objects.filter(
                budget=budget
            ).select_related('account')

            alert_items = []

            for item in line_items:
                # Calculate actual spend for this account during budget period
                actual_spend = self._calculate_actual_spend(
                    budget=budget,
                    account=item.account
                )

                # Calculate variance
                budgeted = item.amount
                variance = actual_spend - budgeted
                variance_pct = (variance / budgeted * 100) if budgeted > 0 else 0

                # Determine severity
                severity = None
                if abs(variance_pct) >= critical_threshold:
                    severity = 'critical'
                elif abs(variance_pct) >= warning_threshold:
                    severity = 'warning'

                if severity:
                    alert_items.append({
                        'account': item.account,
                        'budgeted': budgeted,
                        'actual': actual_spend,
                        'variance': variance,
                        'variance_pct': variance_pct,
                        'severity': severity,
                    })

                    # Display alert
                    color = self.style.ERROR if severity == 'critical' else self.style.WARNING
                    self.stdout.write(
                        color(
                            f'  ⚠ {item.account.name} - '
                            f'Budgeted: ${budgeted:,.2f} - '
                            f'Actual: ${actual_spend:,.2f} - '
                            f'Variance: ${variance:,.2f} ({variance_pct:+.1f}%) - '
                            f'{severity.upper()}'
                        )
                    )

            # Send notification if there are alerts
            if alert_items:
                total_alerts += len(alert_items)
                self.stdout.write('')

                if not dry_run:
                    try:
                        NotificationService.notify_budget_alert(
                            budget=budget,
                            alert_items=alert_items
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Alert notification sent ({len(alert_items)} items)'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Failed to send notification: {str(e)}'
                            )
                        )
                else:
                    self.stdout.write(
                        f'  → Would send alert for {len(alert_items)} item(s)'
                    )
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ No variances exceeding thresholds'))

            self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('SUMMARY')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Budgets Checked: {budgets.count()}')
        self.stdout.write(f'Total Alerts: {total_alerts}')
        self.stdout.write('')

    def _calculate_actual_spend(self, budget, account):
        """
        Calculate actual spending for an account during the budget period.

        Sums all debit journal entries for expense accounts
        within the budget's date range.
        """
        entries = JournalEntry.objects.filter(
            account=account,
            entry_date__gte=budget.start_date,
            entry_date__lte=budget.end_date,
            tenant=budget.tenant
        )

        # For expense accounts, sum debits (increases)
        # For other accounts, adjust logic as needed
        if account.account_type in ['expense', 'cost_of_goods_sold']:
            actual = entries.aggregate(
                total=Sum('debit_amount')
            )['total'] or Decimal('0.00')
        else:
            # For revenue/income accounts, sum credits
            actual = entries.aggregate(
                total=Sum('credit_amount')
            )['total'] or Decimal('0.00')

        return actual
