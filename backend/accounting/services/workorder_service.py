"""
Work Order Service - Business Logic for Work Order Management

Handles:
- Work order cost tracking
- Vendor performance metrics
- Automatic GL account assignment
- Invoice matching
"""

from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Avg, Q

from ..models import (
    WorkOrder, WorkOrderCategory, Vendor, WorkOrderInvoice,
    JournalEntry, Account
)


class WorkOrderService:
    """Service for work order business logic."""

    @staticmethod
    def assign_gl_account(work_order):
        """
        Automatically assign GL account based on work order category.

        Args:
            work_order: WorkOrder instance

        Returns:
            Account: GL account to use for expenses
        """
        if work_order.category and work_order.category.default_gl_account:
            return work_order.category.default_gl_account

        # Fallback: Use generic repairs & maintenance account
        return Account.objects.filter(
            tenant=work_order.tenant,
            account_number__startswith='6200'  # Repairs & Maintenance
        ).first()

    @staticmethod
    def calculate_cost_variance(work_order):
        """
        Calculate variance between estimated and actual costs.

        Args:
            work_order: WorkOrder instance

        Returns:
            dict: Cost variance data
        """
        estimated = work_order.estimated_cost or Decimal('0.00')
        actual = work_order.actual_cost or Decimal('0.00')

        variance = actual - estimated
        variance_pct = (variance / estimated * 100) if estimated > 0 else Decimal('0.00')

        return {
            'estimated_cost': estimated,
            'actual_cost': actual,
            'variance': variance,
            'variance_pct': variance_pct,
            'status': 'over_budget' if variance > 0 else 'under_budget' if variance < 0 else 'on_budget',
        }

    @staticmethod
    @transaction.atomic
    def post_invoice_to_ledger(work_order_invoice, expense_account=None, ap_account=None):
        """
        Post work order invoice to general ledger.

        Creates journal entry: DR: Expense Account, CR: Accounts Payable

        Args:
            work_order_invoice: WorkOrderInvoice instance
            expense_account: Expense account (optional, will use work order's GL account)
            ap_account: Accounts Payable account (optional, will lookup)

        Returns:
            JournalEntry: Created journal entry
        """
        if work_order_invoice.status != 'pending':
            raise ValueError(f"Only pending invoices can be posted. Current status: {work_order_invoice.status}")

        work_order = work_order_invoice.work_order
        tenant = work_order.tenant

        # Get expense account
        if not expense_account:
            expense_account = work_order.gl_account or WorkOrderService.assign_gl_account(work_order)

        # Get AP account
        if not ap_account:
            ap_account = Account.objects.filter(
                tenant=tenant,
                account_number__startswith='2100'  # Accounts Payable
            ).first()

        if not expense_account or not ap_account:
            raise ValueError("Expense and AP accounts must be configured")

        # Create journal entry
        # DR: Expense Account (Expense increases)
        # CR: Accounts Payable (Liability increases)
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=work_order_invoice.invoice_date,
            description=f"Work Order: {work_order.work_order_number}",
            reference_number=work_order_invoice.invoice_number,
            status='posted'
        )

        # Note: In production, would create JournalEntryLine records here

        # Update invoice
        work_order_invoice.journal_entry = entry
        work_order_invoice.status = 'posted'
        work_order_invoice.save()

        # Update work order actual cost
        if work_order.status == 'completed':
            work_order.actual_cost = work_order_invoice.amount
            work_order.save()

        return entry

    @staticmethod
    def get_vendor_performance(vendor, start_date=None, end_date=None):
        """
        Calculate vendor performance metrics.

        Args:
            vendor: Vendor instance
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            dict: Performance metrics
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)  # Last year

        work_orders = WorkOrder.objects.filter(
            assigned_to_vendor=vendor,
            created_date__gte=start_date,
            created_date__lte=end_date
        )

        completed = work_orders.filter(status='completed')

        # Calculate average completion time
        completion_times = []
        for wo in completed:
            if wo.started_date and wo.completed_date:
                days = (wo.completed_date - wo.started_date).days
                completion_times.append(days)

        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

        # Calculate cost metrics
        total_invoiced = WorkOrderInvoice.objects.filter(
            work_order__in=work_orders,
            vendor=vendor
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return {
            'vendor': vendor,
            'total_work_orders': work_orders.count(),
            'completed_work_orders': completed.count(),
            'completion_rate': (completed.count() / work_orders.count() * 100) if work_orders.count() > 0 else 0,
            'avg_completion_days': avg_completion_time,
            'total_amount_paid': total_invoiced,
        }

    @staticmethod
    def get_category_spending(tenant, fiscal_year=None):
        """
        Get spending breakdown by work order category.

        Args:
            tenant: Tenant instance
            fiscal_year: Fiscal year to analyze (optional, defaults to current)

        Returns:
            list: Spending by category
        """
        if not fiscal_year:
            fiscal_year = date.today().year

        start_date = date(fiscal_year, 1, 1)
        end_date = date(fiscal_year, 12, 31)

        categories = WorkOrderCategory.objects.filter(tenant=tenant)

        spending_data = []
        for category in categories:
            work_orders = WorkOrder.objects.filter(
                tenant=tenant,
                category=category,
                created_date__gte=start_date,
                created_date__lte=end_date
            )

            total_spent = WorkOrderInvoice.objects.filter(
                work_order__in=work_orders
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            spending_data.append({
                'category': category,
                'work_order_count': work_orders.count(),
                'total_spent': total_spent,
            })

        # Sort by spending descending
        spending_data.sort(key=lambda x: x['total_spent'], reverse=True)

        return spending_data

    @staticmethod
    def get_work_order_summary(tenant):
        """
        Get summary statistics for work orders.

        Returns:
            dict: Work order statistics
        """
        work_orders = WorkOrder.objects.filter(tenant=tenant)

        return {
            'total_work_orders': work_orders.count(),
            'open': work_orders.filter(status='open').count(),
            'assigned': work_orders.filter(status='assigned').count(),
            'in_progress': work_orders.filter(status='in_progress').count(),
            'completed': work_orders.filter(status='completed').count(),
            'closed': work_orders.filter(status='closed').count(),
            'total_estimated_cost': work_orders.aggregate(
                total=Sum('estimated_cost')
            )['total'] or Decimal('0.00'),
            'total_actual_cost': work_orders.aggregate(
                total=Sum('actual_cost')
            )['total'] or Decimal('0.00'),
        }

    @staticmethod
    def auto_assign_vendor(work_order):
        """
        Automatically suggest a vendor based on category and performance.

        Args:
            work_order: WorkOrder instance

        Returns:
            Vendor or None: Suggested vendor
        """
        # Get vendors who handle this category
        # (In production, would have a many-to-many relationship)
        # For MVP, return preferred vendors

        vendors = Vendor.objects.filter(
            tenant=work_order.tenant,
            is_active=True,
            is_preferred=True
        )

        if not vendors.exists():
            return None

        # Simple algorithm: Return first preferred vendor
        # In production, would rank by:
        # - Performance metrics
        # - Current workload
        # - Specialty match
        # - Cost history

        return vendors.first()
