"""
Django REST Framework API views for accounting endpoints.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from datetime import date
import csv
import io

from tenants.models import Tenant
from .models import (
    Account, Fund, JournalEntry, Owner, Unit, Invoice, Payment,
    PaymentApplication, Budget, BudgetLine
)
from .serializers import (
    AccountSerializer, FundSerializer, OwnerSerializer, UnitSerializer,
    InvoiceSerializer, PaymentSerializer, JournalEntrySerializer,
    ARAgingSerializer, OwnerLedgerTransactionSerializer, DashboardMetricsSerializer,
    BudgetSerializer, BudgetLineSerializer, BudgetCreateSerializer
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
