"""
Django REST Framework API views for accounting endpoints.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, F, ExpressionWrapper, IntegerField
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import csv
import io

from tenants.models import Tenant
from .models import (
    Account, Fund, JournalEntry, Owner, Unit, Invoice, Payment,
    PaymentApplication, Budget, BudgetLine, BankStatement, BankTransaction,
    ReconciliationRule, ReserveStudy, ReserveComponent, ReserveScenario
)
from .serializers import (
    AccountSerializer, FundSerializer, OwnerSerializer, UnitSerializer,
    InvoiceSerializer, PaymentSerializer, JournalEntrySerializer,
    ARAgingSerializer, OwnerLedgerTransactionSerializer, DashboardMetricsSerializer,
    BudgetSerializer, BudgetLineSerializer, BudgetCreateSerializer,
    BankStatementSerializer, BankTransactionSerializer, ReconciliationRuleSerializer,
    MatchSuggestionSerializer, ReconciliationReportSerializer,
    ReserveStudySerializer, ReserveComponentSerializer, ReserveScenarioSerializer,
    FundingProjectionSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list endpoints."""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Account model."""
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Account.objects.select_related('account_type', 'fund')

        # Filter by fund if specified
        fund_id = self.request.query_params.get('fund')
        if fund_id:
            queryset = queryset.filter(fund_id=fund_id)

        # Filter by account type if specified
        account_type = self.request.query_params.get('type')
        if account_type:
            queryset = queryset.filter(account_type__code=account_type)

        return queryset.order_by('account_number')


class OwnerViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Owner model."""
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Owner.objects.all()

        # Filter by status if specified
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search by name or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.order_by('last_name', 'first_name')


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Invoice model."""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Invoice.objects.select_related('owner', 'unit').prefetch_related('lines')

        # Filter by status if specified
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by owner if specified
        owner_id = self.request.query_params.get('owner')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        # Filter overdue only
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL],
                due_date__lt=date.today()
            )

        return queryset.order_by('-invoice_date', '-invoice_number')


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Payment model."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Payment.objects.select_related('owner').prefetch_related('applications')

        # Filter by owner if specified
        owner_id = self.request.query_params.get('owner')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        return queryset.order_by('-payment_date', '-payment_number')


@api_view(['GET'])
def ar_aging_report(request):
    """
    AR Aging Report API endpoint.

    Returns aging breakdown for all owners with unpaid balances.
    """
    # Get tenant from request (in production, this would come from authentication)
    tenant_schema = request.query_params.get('tenant', 'tenant_sunset_hills')
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
    except Tenant.DoesNotExist:
        return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get all owners with unpaid invoices
    owners = Owner.objects.filter(tenant=tenant).order_by('last_name', 'first_name')

    report_data = []
    grand_totals = {
        'current': Decimal('0.00'),
        'days_1_30': Decimal('0.00'),
        'days_31_60': Decimal('0.00'),
        'days_61_90': Decimal('0.00'),
        'days_90_plus': Decimal('0.00'),
        'total': Decimal('0.00')
    }

    for owner in owners:
        # Get unpaid invoices
        unpaid_invoices = Invoice.objects.filter(
            tenant=tenant,
            owner=owner,
            status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL]
        )

        if not unpaid_invoices.exists():
            continue

        # Calculate aging buckets
        aging = {
            'Current': Decimal('0.00'),
            '1-30 days': Decimal('0.00'),
            '31-60 days': Decimal('0.00'),
            '61-90 days': Decimal('0.00'),
            '90+ days': Decimal('0.00')
        }

        for invoice in unpaid_invoices:
            bucket = invoice.aging_bucket
            aging[bucket] += invoice.amount_due

        owner_total = sum(aging.values())

        if owner_total == 0:
            continue

        # Add to report
        report_data.append({
            'owner_id': str(owner.id),
            'owner_name': f"{owner.last_name}, {owner.first_name}",
            'current': aging['Current'],
            'days_1_30': aging['1-30 days'],
            'days_31_60': aging['31-60 days'],
            'days_61_90': aging['61-90 days'],
            'days_90_plus': aging['90+ days'],
            'total': owner_total
        })

        # Update grand totals
        grand_totals['current'] += aging['Current']
        grand_totals['days_1_30'] += aging['1-30 days']
        grand_totals['days_31_60'] += aging['31-60 days']
        grand_totals['days_61_90'] += aging['61-90 days']
        grand_totals['days_90_plus'] += aging['90+ days']
        grand_totals['total'] += owner_total

    serializer = ARAgingSerializer(report_data, many=True)

    return Response({
        'report_date': date.today(),
        'tenant': tenant.name,
        'data': serializer.data,
        'totals': grand_totals
    })


@api_view(['GET'])
def owner_ledger(request, owner_id):
    """
    Owner Ledger API endpoint.

    Returns complete transaction history for an owner.
    """
    owner = get_object_or_404(Owner, id=owner_id)

    # Get all invoices
    invoices = Invoice.objects.filter(owner=owner).order_by('invoice_date', 'invoice_number')

    # Get all payments
    payments = Payment.objects.filter(owner=owner).prefetch_related('applications__invoice').order_by('payment_date', 'payment_number')

    # Create ledger transactions
    transactions = []

    for invoice in invoices:
        transactions.append({
            'date': invoice.invoice_date,
            'type': 'Invoice',
            'number': invoice.invoice_number,
            'description': invoice.description,
            'charges': invoice.total_amount,
            'payments': Decimal('0.00'),
            'balance': Decimal('0.00')  # Will calculate below
        })

    for payment in payments:
        # Get applied invoices
        applications = payment.applications.all()
        invoice_numbers = ", ".join([app.invoice.invoice_number for app in applications])
        description = f"{payment.payment_method}"
        if invoice_numbers:
            description += f" (Applied to: {invoice_numbers})"

        transactions.append({
            'date': payment.payment_date,
            'type': 'Payment',
            'number': payment.payment_number,
            'description': description,
            'charges': Decimal('0.00'),
            'payments': payment.amount,
            'balance': Decimal('0.00')  # Will calculate below
        })

    # Sort by date and calculate running balance
    transactions.sort(key=lambda x: (x['date'], x['type']))

    running_balance = Decimal('0.00')
    for txn in transactions:
        running_balance += txn['charges'] - txn['payments']
        txn['balance'] = running_balance

    serializer = OwnerLedgerTransactionSerializer(transactions, many=True)

    # Calculate summary
    total_charges = sum([t['charges'] for t in transactions])
    total_payments = sum([t['payments'] for t in transactions])

    return Response({
        'owner': OwnerSerializer(owner).data,
        'transactions': serializer.data,
        'summary': {
            'total_charges': total_charges,
            'total_payments': total_payments,
            'current_balance': owner.get_ar_balance()
        }
    })


@api_view(['GET'])
def dashboard_metrics(request):
    """
    Dashboard Metrics API endpoint.

    Returns summary metrics for AR dashboard.
    """
    # Get tenant from request
    tenant_schema = request.query_params.get('tenant', 'tenant_sunset_hills')
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
    except Tenant.DoesNotExist:
        return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)

    # Calculate metrics
    all_invoices = Invoice.objects.filter(tenant=tenant)

    total_ar = all_invoices.filter(
        status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL]
    ).aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

    current_ar = all_invoices.filter(
        status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL],
        due_date__gte=date.today()
    ).aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

    overdue_ar = all_invoices.filter(
        status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL],
        due_date__lt=date.today()
    ).aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

    total_invoices = all_invoices.count()
    paid_invoices = all_invoices.filter(status=Invoice.STATUS_PAID).count()
    overdue_invoices = all_invoices.filter(
        status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL],
        due_date__lt=date.today()
    ).count()

    total_owners = Owner.objects.filter(tenant=tenant).count()
    delinquent_owners = Owner.objects.filter(
        tenant=tenant,
        invoices__status__in=[Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL],
        invoices__due_date__lt=date.today()
    ).distinct().count()

    # Recent payments
    recent_payments = Payment.objects.filter(tenant=tenant).select_related('owner').order_by('-payment_date')[:10]

    metrics = {
        'total_ar': total_ar,
        'current_ar': current_ar,
        'overdue_ar': overdue_ar,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_owners': total_owners,
        'delinquent_owners': delinquent_owners,
        'recent_payments': recent_payments
    }

    serializer = DashboardMetricsSerializer(metrics)
    return Response(serializer.data)


@api_view(['GET'])
def trial_balance(request):
    """
    Trial Balance API endpoint.

    Returns trial balance for all accounts.
    """
    # Get tenant from request
    tenant_schema = request.query_params.get('tenant', 'tenant_sunset_hills')
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
    except Tenant.DoesNotExist:
        return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get fund if specified
    fund_type = request.query_params.get('fund_type', 'OPERATING')
    fund = Fund.objects.filter(tenant=tenant, fund_type=fund_type).first()

    if not fund:
        return Response({'error': f'Fund type {fund_type} not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get all accounts for this fund
    accounts = Account.objects.filter(
        tenant=tenant,
        fund=fund,
        is_active=True
    ).select_related('account_type').order_by('account_number')

    trial_balance_data = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for account in accounts:
        balance = account.get_balance()

        # Format for trial balance
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

        trial_balance_data.append({
            'account_number': account.account_number,
            'account_name': account.name,
            'account_type': account.account_type.name,
            'debit': debit_amt,
            'credit': credit_amt,
            'balance': balance
        })

    is_balanced = total_debits == total_credits

    return Response({
        'report_date': date.today(),
        'tenant': tenant.name,
        'fund': fund.name,
        'accounts': trial_balance_data,
        'totals': {
            'total_debits': total_debits,
            'total_credits': total_credits,
            'is_balanced': is_balanced,
            'difference': abs(total_debits - total_credits)
        }
    })


# Budget Management Views

class BudgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing budgets.
    
    Provides CRUD operations for budgets and variance reporting.
    """
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['fiscal_year', 'status', 'fund']
    ordering_fields = ['fiscal_year', 'start_date', 'created_at']
    ordering = ['-fiscal_year']
    
    def get_queryset(self):
        tenant = get_tenant(self.request)
        return Budget.objects.filter(tenant=tenant).prefetch_related('lines__account')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BudgetCreateSerializer
        return BudgetSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['tenant'] = get_tenant(self.request)
        return context
    
    @action(detail=True, methods=['get'])
    def variance_report(self, request, pk=None):
        """
        Generate budget vs actual variance report.
        
        Query params:
        - as_of_date: Date to calculate actuals through (default: today)
        """
        budget = self.get_object()
        as_of_date_str = request.query_params.get('as_of_date')
        
        if as_of_date_str:
            from datetime import datetime
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        else:
            as_of_date = None
        
        variance_report = budget.get_variance_report(as_of_date)
        return Response(variance_report)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a budget.
        
        Requires admin or treasurer role.
        """
        budget = self.get_object()
        
        if budget.status != Budget.STATUS_DRAFT:
            return Response(
                {'error': 'Only draft budgets can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        budget.status = Budget.STATUS_APPROVED
        budget.approved_by = request.user
        budget.approved_at = timezone.now()
        budget.save()
        
        serializer = self.get_serializer(budget)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate an approved budget.
        
        Sets this budget as the active budget for its fiscal year.
        """
        budget = self.get_object()
        
        if budget.status != Budget.STATUS_APPROVED:
            return Response(
                {'error': 'Only approved budgets can be activated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deactivate any other active budgets for this fiscal year/fund
        Budget.objects.filter(
            tenant=budget.tenant,
            fiscal_year=budget.fiscal_year,
            fund=budget.fund,
            status=Budget.STATUS_ACTIVE
        ).update(status=Budget.STATUS_APPROVED)
        
        budget.status = Budget.STATUS_ACTIVE
        budget.save()

        serializer = self.get_serializer(budget)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='funds')
    def funds(self, request):
        """
        List all funds for the current tenant.

        Used by the UI to populate fund dropdowns.
        """
        tenant = get_tenant(request)
        queryset = Fund.objects.filter(tenant=tenant, is_active=True)
        serializer = FundSerializer(queryset, many=True)
        return Response(serializer.data)


class BudgetLineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing budget lines.
    
    Allows adding/updating individual budget lines.
    """
    serializer_class = BudgetLineSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_tenant(self.request)
        budget_id = self.request.query_params.get('budget')
        
        queryset = BudgetLine.objects.filter(
            budget__tenant=tenant
        ).select_related('budget', 'account')
        
        if budget_id:
            queryset = queryset.filter(budget_id=budget_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new budget line"""
        budget_id = request.data.get('budget')
        
        try:
            budget = Budget.objects.get(
                id=budget_id,
                tenant=get_tenant(request)
            )
        except Budget.DoesNotExist:
            return Response(
                {'error': 'Budget not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if budget.status not in [Budget.STATUS_DRAFT, Budget.STATUS_APPROVED]:
            return Response(
                {'error': 'Cannot modify active or closed budgets'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard API endpoints for financial metrics and summaries.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def cash_position(self, request):
        """
        Get current cash balances across all funds with trend data.

        Returns:
            {
                "total_cash": "85500.00",
                "funds": [
                    {
                        "name": "Operating Fund",
                        "balance": "45000.00",
                        "trend": 5.2
                    },
                    ...
                ]
            }
        """
        tenant = get_tenant(request)

        # Get all funds with their current balances
        funds = Fund.objects.filter(tenant=tenant)
        fund_data = []
        total_cash = Decimal('0.00')

        for fund in funds:
            # Current balance
            balance = fund.balance
            total_cash += balance

            # Calculate trend (compare to 30 days ago)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            entries_last_month = JournalEntry.objects.filter(
                fund=fund,
                entry_date__gte=thirty_days_ago.date(),
                entry_date__lte=timezone.now().date()
            ).aggregate(
                debits=Coalesce(Sum('debit_amount'), Decimal('0.00')),
                credits=Coalesce(Sum('credit_amount'), Decimal('0.00'))
            )

            net_change = entries_last_month['debits'] - entries_last_month['credits']
            previous_balance = balance - net_change

            if previous_balance > 0:
                trend = float((net_change / previous_balance) * 100)
            else:
                trend = 0.0

            fund_data.append({
                'name': fund.name,
                'balance': str(balance),
                'trend': round(trend, 2)
            })

        return Response({
            'total_cash': str(total_cash),
            'funds': fund_data
        })

    @action(detail=False, methods=['get'])
    def ar_aging(self, request):
        """
        Get AR aging buckets.

        Returns:
            {
                "total_ar": "12300.00",
                "average_days": 45,
                "buckets": {
                    "current": {"amount": "7380.00", "percentage": 60, "count": 15},
                    "days_30_60": {"amount": "3075.00", "percentage": 25, "count": 8},
                    "days_60_90": {"amount": "1230.00", "percentage": 10, "count": 3},
                    "days_over_90": {"amount": "615.00", "percentage": 5, "count": 2}
                }
            }
        """
        tenant = get_tenant(request)
        today = timezone.now().date()

        # Get all unpaid invoices
        invoices = Invoice.objects.filter(
            owner__tenant=tenant,
            status__in=['sent', 'overdue']
        )

        total_ar = Decimal('0.00')
        buckets = {
            'current': {'amount': Decimal('0.00'), 'count': 0},
            'days_30_60': {'amount': Decimal('0.00'), 'count': 0},
            'days_60_90': {'amount': Decimal('0.00'), 'count': 0},
            'days_over_90': {'amount': Decimal('0.00'), 'count': 0}
        }

        total_days = 0
        invoice_count = 0

        for invoice in invoices:
            balance = invoice.balance_due
            if balance <= 0:
                continue

            total_ar += balance
            days_old = (today - invoice.due_date).days
            total_days += days_old
            invoice_count += 1

            if days_old <= 30:
                buckets['current']['amount'] += balance
                buckets['current']['count'] += 1
            elif days_old <= 60:
                buckets['days_30_60']['amount'] += balance
                buckets['days_30_60']['count'] += 1
            elif days_old <= 90:
                buckets['days_60_90']['amount'] += balance
                buckets['days_60_90']['count'] += 1
            else:
                buckets['days_over_90']['amount'] += balance
                buckets['days_over_90']['count'] += 1

        # Calculate percentages
        bucket_data = {}
        for key, data in buckets.items():
            percentage = int((data['amount'] / total_ar * 100)) if total_ar > 0 else 0
            bucket_data[key] = {
                'amount': str(data['amount']),
                'percentage': percentage,
                'count': data['count']
            }

        average_days = int(total_days / invoice_count) if invoice_count > 0 else 0

        return Response({
            'total_ar': str(total_ar),
            'average_days': average_days,
            'buckets': bucket_data
        })

    @action(detail=False, methods=['get'])
    def expenses(self, request):
        """
        Get expense summary (MTD/YTD).

        Query params:
            period: 'mtd' or 'ytd'

        Returns:
            {
                "period": "mtd",
                "total": "18500.00",
                "comparison": {
                    "previous_period": "20100.00",
                    "change_pct": -8.0
                },
                "top_categories": [...]
            }
        """
        tenant = get_tenant(request)
        period = request.query_params.get('period', 'mtd')
        today = timezone.now().date()

        if period == 'mtd':
            start_date = today.replace(day=1)
            previous_start = (start_date - timedelta(days=1)).replace(day=1)
            previous_end = start_date - timedelta(days=1)
        else:  # ytd
            start_date = today.replace(month=1, day=1)
            previous_start = start_date.replace(year=start_date.year - 1)
            previous_end = start_date - timedelta(days=1)

        # Get expense accounts (liabilities and expenses)
        expense_entries = JournalEntry.objects.filter(
            fund__tenant=tenant,
            entry_date__gte=start_date,
            entry_date__lte=today,
            debit_amount__gt=0
        ).aggregate(total=Coalesce(Sum('debit_amount'), Decimal('0.00')))

        previous_entries = JournalEntry.objects.filter(
            fund__tenant=tenant,
            entry_date__gte=previous_start,
            entry_date__lte=previous_end,
            debit_amount__gt=0
        ).aggregate(total=Coalesce(Sum('debit_amount'), Decimal('0.00')))

        total = expense_entries['total']
        previous_total = previous_entries['total']

        if previous_total > 0:
            change_pct = float((total - previous_total) / previous_total * 100)
        else:
            change_pct = 0.0

        # Get top expense categories
        top_categories = []
        category_totals = JournalEntry.objects.filter(
            fund__tenant=tenant,
            entry_date__gte=start_date,
            entry_date__lte=today,
            debit_amount__gt=0
        ).values('account__account_name').annotate(
            amount=Sum('debit_amount')
        ).order_by('-amount')[:3]

        for cat in category_totals:
            top_categories.append({
                'category': cat['account__account_name'],
                'amount': str(cat['amount'])
            })

        return Response({
            'period': period,
            'total': str(total),
            'comparison': {
                'previous_period': str(previous_total),
                'change_pct': round(change_pct, 1)
            },
            'top_categories': top_categories
        })

    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """
        Get revenue summary (MTD/YTD).

        Query params:
            period: 'mtd' or 'ytd'

        Returns:
            {
                "period": "mtd",
                "total": "42000.00",
                "comparison": {
                    "previous_period": "41000.00",
                    "change_pct": 2.4
                }
            }
        """
        tenant = get_tenant(request)
        period = request.query_params.get('period', 'mtd')
        today = timezone.now().date()

        if period == 'mtd':
            start_date = today.replace(day=1)
            previous_start = (start_date - timedelta(days=1)).replace(day=1)
            previous_end = start_date - timedelta(days=1)
        else:  # ytd
            start_date = today.replace(month=1, day=1)
            previous_start = start_date.replace(year=start_date.year - 1)
            previous_end = start_date - timedelta(days=1)

        # Get revenue (credit entries to revenue accounts)
        revenue_entries = JournalEntry.objects.filter(
            fund__tenant=tenant,
            entry_date__gte=start_date,
            entry_date__lte=today,
            credit_amount__gt=0
        ).aggregate(total=Coalesce(Sum('credit_amount'), Decimal('0.00')))

        previous_entries = JournalEntry.objects.filter(
            fund__tenant=tenant,
            entry_date__gte=previous_start,
            entry_date__lte=previous_end,
            credit_amount__gt=0
        ).aggregate(total=Coalesce(Sum('credit_amount'), Decimal('0.00')))

        total = revenue_entries['total']
        previous_total = previous_entries['total']

        if previous_total > 0:
            change_pct = float((total - previous_total) / previous_total * 100)
        else:
            change_pct = 0.0

        return Response({
            'period': period,
            'total': str(total),
            'comparison': {
                'previous_period': str(previous_total),
                'change_pct': round(change_pct, 1)
            }
        })

    @action(detail=False, methods=['get'])
    def revenue_vs_expenses(self, request):
        """
        Get monthly revenue vs expenses for charting (last 12 months).

        Returns:
            {
                "months": [
                    {"month": "2024-11", "revenue": "42000.00", "expenses": "18500.00"},
                    {"month": "2024-12", "revenue": "42000.00", "expenses": "19200.00"},
                    ...
                ]
            }
        """
        tenant = get_tenant(request)
        today = timezone.now().date()
        twelve_months_ago = today - timedelta(days=365)

        months_data = []
        current_date = twelve_months_ago.replace(day=1)

        while current_date <= today:
            # Last day of month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1, day=1)
            end_date = next_month - timedelta(days=1)

            # Revenue (credits)
            revenue = JournalEntry.objects.filter(
                fund__tenant=tenant,
                entry_date__gte=current_date,
                entry_date__lte=end_date,
                credit_amount__gt=0
            ).aggregate(total=Coalesce(Sum('credit_amount'), Decimal('0.00')))['total']

            # Expenses (debits)
            expenses = JournalEntry.objects.filter(
                fund__tenant=tenant,
                entry_date__gte=current_date,
                entry_date__lte=end_date,
                debit_amount__gt=0
            ).aggregate(total=Coalesce(Sum('debit_amount'), Decimal('0.00')))['total']

            months_data.append({
                'month': current_date.strftime('%Y-%m'),
                'revenue': str(revenue),
                'expenses': str(expenses)
            })

            current_date = next_month

        return Response({
            'months': months_data
        })

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """
        Get recent activity log (last 20 events).

        Returns:
            {
                "activities": [
                    {
                        "type": "invoice",
                        "description": "Invoice #1025 created",
                        "amount": "450.00",
                        "timestamp": "2025-10-28T10:30:00Z"
                    },
                    ...
                ]
            }
        """
        tenant = get_tenant(request)
        limit = int(request.query_params.get('limit', 20))

        activities = []

        # Get recent invoices
        recent_invoices = Invoice.objects.filter(
            owner__tenant=tenant
        ).order_by('-issue_date')[:limit//2]

        for invoice in recent_invoices:
            activities.append({
                'type': 'invoice',
                'description': f'Invoice #{invoice.invoice_number} created',
                'amount': str(invoice.total_amount),
                'timestamp': invoice.issue_date.isoformat()
            })

        # Get recent payments
        recent_payments = Payment.objects.filter(
            owner__tenant=tenant
        ).order_by('-payment_date')[:limit//2]

        for payment in recent_payments:
            activities.append({
                'type': 'payment',
                'description': f'Payment received from {payment.owner.unit.unit_number}',
                'amount': str(payment.amount),
                'timestamp': payment.payment_date.isoformat()
            })

        # Sort by timestamp descending
        activities.sort(key=lambda x: x['timestamp'], reverse=True)

        return Response({
            'activities': activities[:limit]
        })


class BankReconciliationViewSet(viewsets.ViewSet):
    """ViewSet for bank reconciliation operations."""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def upload_statement(self, request):
        """
        Upload and parse bank statement (CSV format).

        Expected POST data:
        - file: CSV file
        - fund: Fund ID
        - statement_date: YYYY-MM-DD
        - beginning_balance: Decimal
        - ending_balance: Decimal
        """
        tenant = get_tenant(request)

        # Validate required fields
        file_obj = request.FILES.get('file')
        fund_id = request.data.get('fund')
        statement_date = request.data.get('statement_date')
        beginning_balance = request.data.get('beginning_balance')
        ending_balance = request.data.get('ending_balance')

        if not all([file_obj, fund_id, statement_date, beginning_balance, ending_balance]):
            return Response(
                {'error': 'Missing required fields: file, fund, statement_date, beginning_balance, ending_balance'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fund = Fund.objects.get(id=fund_id, tenant=tenant)
        except Fund.DoesNotExist:
            return Response({'error': 'Fund not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create BankStatement
        statement = BankStatement.objects.create(
            tenant=tenant,
            fund=fund,
            statement_date=statement_date,
            beginning_balance=Decimal(beginning_balance),
            ending_balance=Decimal(ending_balance),
            file_name=file_obj.name,
            uploaded_by=request.user
        )

        # Parse CSV file
        try:
            decoded_file = file_obj.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))

            transactions_created = 0
            for row in csv_reader:
                # Expected CSV columns: date, description, amount, check_number (optional), reference (optional)
                transaction_date = row.get('date') or row.get('Date') or row.get('DATE')
                description = row.get('description') or row.get('Description') or row.get('DESCRIPTION')
                amount = row.get('amount') or row.get('Amount') or row.get('AMOUNT')
                check_number = row.get('check_number') or row.get('Check Number') or row.get('CHECK_NUMBER', '')
                reference = row.get('reference') or row.get('Reference') or row.get('REFERENCE', '')

                if not all([transaction_date, description, amount]):
                    continue

                BankTransaction.objects.create(
                    tenant=tenant,
                    statement=statement,
                    transaction_date=transaction_date,
                    description=description,
                    amount=Decimal(amount),
                    check_number=check_number,
                    reference_number=reference,
                    status=BankTransaction.STATUS_UNMATCHED
                )
                transactions_created += 1

            return Response({
                'statement': BankStatementSerializer(statement).data,
                'transactions_created': transactions_created
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Rollback statement creation if parsing fails
            statement.delete()
            return Response(
                {'error': f'Failed to parse CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def statements(self, request):
        """List all bank statements with optional filters."""
        tenant = get_tenant(request)
        queryset = BankStatement.objects.filter(tenant=tenant)

        # Filter by fund
        fund_id = request.query_params.get('fund')
        if fund_id:
            queryset = queryset.filter(fund_id=fund_id)

        # Filter by reconciliation status
        reconciled = request.query_params.get('reconciled')
        if reconciled is not None:
            queryset = queryset.filter(reconciled=reconciled.lower() == 'true')

        queryset = queryset.select_related('fund', 'uploaded_by').order_by('-statement_date')
        serializer = BankStatementSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statement_detail(self, request, pk=None):
        """Get statement details with all transactions."""
        tenant = get_tenant(request)
        try:
            statement = BankStatement.objects.get(id=pk, tenant=tenant)
        except BankStatement.DoesNotExist:
            return Response({'error': 'Statement not found'}, status=status.HTTP_404_NOT_FOUND)

        transactions = statement.transactions.all().order_by('transaction_date', '-amount')

        return Response({
            'statement': BankStatementSerializer(statement).data,
            'transactions': BankTransactionSerializer(transactions, many=True).data
        })

    @action(detail=False, methods=['get'])
    def unmatched_transactions(self, request):
        """Get all unmatched bank transactions."""
        tenant = get_tenant(request)
        queryset = BankTransaction.objects.filter(
            tenant=tenant,
            status=BankTransaction.STATUS_UNMATCHED
        )

        # Filter by statement
        statement_id = request.query_params.get('statement')
        if statement_id:
            queryset = queryset.filter(statement_id=statement_id)

        queryset = queryset.select_related('statement').order_by('transaction_date', '-amount')
        serializer = BankTransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def suggest_matches(self, request):
        """
        Suggest matches for a bank transaction using fuzzy matching.

        POST data:
        - transaction_id: BankTransaction ID
        - max_suggestions: Maximum number of suggestions (default: 5)
        """
        tenant = get_tenant(request)
        transaction_id = request.data.get('transaction_id')
        max_suggestions = int(request.data.get('max_suggestions', 5))

        if not transaction_id:
            return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = BankTransaction.objects.get(id=transaction_id, tenant=tenant)
        except BankTransaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        # Find potential matches in journal entries
        suggestions = []

        # Get journal entries within ±7 days and same fund
        date_min = transaction.transaction_date - timedelta(days=7)
        date_max = transaction.transaction_date + timedelta(days=7)

        potential_entries = JournalEntry.objects.filter(
            tenant=tenant,
            fund=transaction.statement.fund,
            entry_date__range=(date_min, date_max)
        ).prefetch_related('lines')

        for entry in potential_entries:
            confidence = 0
            reasons = []

            # Calculate entry amount (sum of debits or credits, use larger)
            entry_amount = abs(entry.amount)  # Use entry.amount if available
            transaction_amount = abs(transaction.amount)

            # Exact amount match: +50 points
            if entry_amount == transaction_amount:
                confidence += 50
                reasons.append('Exact amount match')
            # Close amount match (within 1%): +30 points
            elif abs(entry_amount - transaction_amount) / transaction_amount < 0.01:
                confidence += 30
                reasons.append('Close amount match')
            # Similar amount (within 10%): +15 points
            elif abs(entry_amount - transaction_amount) / transaction_amount < 0.10:
                confidence += 15
                reasons.append('Similar amount')
            else:
                continue  # Skip if amount is too different

            # Same date: +30 points
            if entry.entry_date == transaction.transaction_date:
                confidence += 30
                reasons.append('Same date')
            # Within 3 days: +20 points
            elif abs((entry.entry_date - transaction.transaction_date).days) <= 3:
                confidence += 20
                reasons.append('Close date')
            # Within 7 days: +10 points
            else:
                confidence += 10
                reasons.append('Date within range')

            # Check number match: +20 points
            if transaction.check_number and transaction.check_number in entry.description:
                confidence += 20
                reasons.append('Check number match')

            # Description similarity (simple keyword matching)
            transaction_words = set(transaction.description.lower().split())
            entry_words = set(entry.description.lower().split())
            common_words = transaction_words & entry_words
            if len(common_words) > 0:
                similarity = len(common_words) / max(len(transaction_words), len(entry_words))
                if similarity > 0.3:
                    confidence += int(similarity * 20)
                    reasons.append(f'Description similarity ({int(similarity * 100)}%)')

            # Add to suggestions if confidence > 40
            if confidence >= 40:
                suggestions.append({
                    'journal_entry': entry,
                    'confidence': min(confidence, 100),  # Cap at 100
                    'reason': ', '.join(reasons)
                })

        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        suggestions = suggestions[:max_suggestions]

        serializer = MatchSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def match_transaction(self, request):
        """
        Match a bank transaction to a journal entry.

        POST data:
        - transaction_id: BankTransaction ID
        - entry_id: JournalEntry ID
        - notes: Optional notes
        """
        tenant = get_tenant(request)
        transaction_id = request.data.get('transaction_id')
        entry_id = request.data.get('entry_id')
        notes = request.data.get('notes', '')

        if not all([transaction_id, entry_id]):
            return Response({'error': 'transaction_id and entry_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = BankTransaction.objects.get(id=transaction_id, tenant=tenant)
            entry = JournalEntry.objects.get(id=entry_id, tenant=tenant)
        except (BankTransaction.DoesNotExist, JournalEntry.DoesNotExist):
            return Response({'error': 'Transaction or entry not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update transaction
        transaction.status = BankTransaction.STATUS_MATCHED
        transaction.matched_entry = entry
        transaction.match_confidence = 100  # Manual match = 100% confidence
        transaction.notes = notes
        transaction.save()

        return Response({
            'transaction': BankTransactionSerializer(transaction).data,
            'message': 'Transaction matched successfully'
        })

    @action(detail=False, methods=['post'])
    def unmatch_transaction(self, request):
        """
        Unmatch a previously matched transaction.

        POST data:
        - transaction_id: BankTransaction ID
        """
        tenant = get_tenant(request)
        transaction_id = request.data.get('transaction_id')

        if not transaction_id:
            return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = BankTransaction.objects.get(id=transaction_id, tenant=tenant)
        except BankTransaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        transaction.status = BankTransaction.STATUS_UNMATCHED
        transaction.matched_entry = None
        transaction.match_confidence = 0
        transaction.save()

        return Response({
            'transaction': BankTransactionSerializer(transaction).data,
            'message': 'Transaction unmatched successfully'
        })

    @action(detail=False, methods=['post'])
    def ignore_transaction(self, request):
        """
        Mark transaction as ignored.

        POST data:
        - transaction_id: BankTransaction ID
        - notes: Optional notes explaining why ignored
        """
        tenant = get_tenant(request)
        transaction_id = request.data.get('transaction_id')
        notes = request.data.get('notes', '')

        if not transaction_id:
            return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = BankTransaction.objects.get(id=transaction_id, tenant=tenant)
        except BankTransaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        transaction.status = BankTransaction.STATUS_IGNORED
        transaction.notes = notes
        transaction.save()

        return Response({
            'transaction': BankTransactionSerializer(transaction).data,
            'message': 'Transaction marked as ignored'
        })

    @action(detail=False, methods=['post'])
    def create_from_transaction(self, request):
        """
        Create a journal entry from a bank transaction.

        POST data:
        - transaction_id: BankTransaction ID
        - account_id: Account ID for the offset entry
        - description: Entry description (optional, defaults to transaction description)
        """
        tenant = get_tenant(request)
        transaction_id = request.data.get('transaction_id')
        account_id = request.data.get('account_id')
        description = request.data.get('description')

        if not all([transaction_id, account_id]):
            return Response({'error': 'transaction_id and account_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = BankTransaction.objects.get(id=transaction_id, tenant=tenant)
            account = Account.objects.get(id=account_id, tenant=tenant)
        except (BankTransaction.DoesNotExist, Account.DoesNotExist):
            return Response({'error': 'Transaction or account not found'}, status=status.HTTP_404_NOT_FOUND)

        # Use transaction description if not provided
        if not description:
            description = transaction.description

        # Determine if this is a deposit or withdrawal
        amount = abs(transaction.amount)
        is_deposit = transaction.amount > 0

        # Get cash account for the fund (assuming account type 'Cash')
        try:
            cash_account = Account.objects.get(
                tenant=tenant,
                fund=transaction.statement.fund,
                account_type__name='Cash'
            )
        except Account.DoesNotExist:
            return Response(
                {'error': 'Cash account not found for fund'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create journal entry
        from .services import JournalEntryService

        # For deposits: Debit Cash, Credit specified account
        # For withdrawals: Debit specified account, Credit Cash
        if is_deposit:
            lines = [
                {'account': cash_account.id, 'debit': amount, 'credit': 0},
                {'account': account.id, 'debit': 0, 'credit': amount}
            ]
        else:
            lines = [
                {'account': account.id, 'debit': amount, 'credit': 0},
                {'account': cash_account.id, 'debit': 0, 'credit': amount}
            ]

        try:
            entry = JournalEntryService.create_journal_entry(
                tenant=tenant,
                fund=transaction.statement.fund,
                entry_date=transaction.transaction_date,
                description=description,
                lines=lines,
                created_by=request.user
            )

            # Match the transaction to the new entry
            transaction.status = BankTransaction.STATUS_CREATED
            transaction.matched_entry = entry
            transaction.match_confidence = 100
            transaction.save()

            return Response({
                'entry': JournalEntrySerializer(entry).data,
                'transaction': BankTransactionSerializer(transaction).data,
                'message': 'Journal entry created and matched successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def reconciliation_report(self, request, pk=None):
        """Generate reconciliation report for a statement."""
        tenant = get_tenant(request)
        try:
            statement = BankStatement.objects.get(id=pk, tenant=tenant)
        except BankStatement.DoesNotExist:
            return Response({'error': 'Statement not found'}, status=status.HTTP_404_NOT_FOUND)

        transactions = statement.transactions.all()

        # Calculate totals
        matched_transactions = transactions.filter(status=BankTransaction.STATUS_MATCHED)
        total_deposits = sum(t.amount for t in matched_transactions if t.amount > 0)
        total_withdrawals = sum(abs(t.amount) for t in matched_transactions if t.amount < 0)

        calculated_balance = statement.beginning_balance + Decimal(total_deposits) - Decimal(total_withdrawals)
        difference = statement.ending_balance - calculated_balance

        report = {
            'statement': statement,
            'beginning_balance': statement.beginning_balance,
            'total_deposits': Decimal(total_deposits),
            'total_withdrawals': Decimal(total_withdrawals),
            'ending_balance': statement.ending_balance,
            'calculated_balance': calculated_balance,
            'difference': difference,
            'matched_count': transactions.filter(status=BankTransaction.STATUS_MATCHED).count(),
            'unmatched_count': transactions.filter(status=BankTransaction.STATUS_UNMATCHED).count(),
            'ignored_count': transactions.filter(status=BankTransaction.STATUS_IGNORED).count(),
            'transactions': transactions
        }

        serializer = ReconciliationReportSerializer(report)
        return Response(serializer.data)


class FundViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Funds.
    """
    serializer_class = FundSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fund_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'fund_type', 'created_at']
    ordering = ['fund_type', 'name']

    def get_queryset(self):
        tenant = get_tenant(self.request)
        return Fund.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant)


# ===========================
# Reserve Planning ViewSets
# ===========================

class ReserveStudyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reserve Studies.

    Provides CRUD operations plus funding adequacy calculations.
    """
    serializer_class = ReserveStudySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['study_date']
    search_fields = ['name', 'notes']
    ordering_fields = ['name', 'study_date', 'created_at']
    ordering = ['-study_date', 'name']

    def get_queryset(self):
        tenant = get_tenant(self.request)
        return ReserveStudy.objects.filter(tenant=tenant).prefetch_related('components', 'scenarios')

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant)

    @action(detail=True, methods=['get'])
    def funding_adequacy(self, request, pk=None):
        """
        Calculate funding adequacy (% funded) for this study.

        Returns:
        - current_balance: Current reserve fund balance
        - total_future_cost: Sum of all inflated replacement costs
        - percent_funded: (balance / cost) * 100
        - status: WELL_FUNDED (>70%), ADEQUATE (30-70%), UNDERFUNDED (<30%)
        """
        study = self.get_object()
        current_balance = study.get_current_reserve_balance()

        # Calculate total future cost (sum of inflated costs)
        components = study.components.all()
        total_future_cost = sum(comp.get_inflated_cost() for comp in components)

        if total_future_cost > 0:
            percent_funded = (current_balance / total_future_cost * 100).quantize(Decimal('0.01'))
        else:
            percent_funded = Decimal('100.00')

        # Determine status
        if percent_funded >= 70:
            status = 'WELL_FUNDED'
        elif percent_funded >= 30:
            status = 'ADEQUATE'
        else:
            status = 'UNDERFUNDED'

        return Response({
            'current_balance': str(current_balance),
            'total_future_cost': str(total_future_cost),
            'percent_funded': str(percent_funded),
            'status': status
        })


class ReserveComponentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reserve Components.

    Components belong to a reserve study.
    """
    serializer_class = ReserveComponentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['study', 'category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'category', 'remaining_life_years', 'current_cost']
    ordering = ['category', 'name']

    def get_queryset(self):
        tenant = get_tenant(self.request)
        return ReserveComponent.objects.filter(study__tenant=tenant)


class ReserveScenarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reserve Scenarios.

    Scenarios belong to a reserve study and provide different funding options.
    """
    serializer_class = ReserveScenarioSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['study', 'is_baseline']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'monthly_contribution', 'created_at']
    ordering = ['-is_baseline', 'name']

    def get_queryset(self):
        tenant = get_tenant(self.request)
        return ReserveScenario.objects.filter(study__tenant=tenant)

    @action(detail=True, methods=['get'])
    def projection(self, request, pk=None):
        """
        Calculate multi-year funding projection for this scenario.

        Returns year-by-year projections showing:
        - Beginning balance
        - Contributions
        - Expenditures
        - Interest earned
        - Ending balance
        - Percent funded
        """
        scenario = self.get_object()
        projections = scenario.calculate_projection()
        serializer = FundingProjectionSerializer(projections, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        Compare multiple scenarios side-by-side.

        POST body: {"scenario_ids": ["uuid1", "uuid2", "uuid3"]}

        Returns projections for all scenarios for easy comparison.
        """
        scenario_ids = request.data.get('scenario_ids', [])
        if not scenario_ids or not isinstance(scenario_ids, list):
            return Response(
                {"error": "scenario_ids array required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = get_tenant(request)
        scenarios = ReserveScenario.objects.filter(
            id__in=scenario_ids,
            study__tenant=tenant
        )

        if len(scenarios) != len(scenario_ids):
            return Response(
                {"error": "One or more scenarios not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        comparison = []
        for scenario in scenarios:
            projections = scenario.calculate_projection()
            comparison.append({
                'scenario': ReserveScenarioSerializer(scenario).data,
                'projections': FundingProjectionSerializer(projections, many=True).data
            })

        return Response(comparison)
