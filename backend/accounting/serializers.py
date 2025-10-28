"""
Django REST Framework serializers for accounting API.
"""

from rest_framework import serializers
from decimal import Decimal
from .models import (
    Account, Fund, JournalEntry, JournalEntryLine,
    Owner, Unit, Ownership, Invoice, InvoiceLine, Payment, PaymentApplication,
    Budget, BudgetLine
)


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model."""
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'name', 'description',
            'account_type_name', 'fund_name', 'is_active', 'balance'
        ]

    def get_balance(self, obj):
        return str(obj.get_balance())


class FundSerializer(serializers.ModelSerializer):
    """Serializer for Fund model."""
    class Meta:
        model = Fund
        fields = ['id', 'name', 'fund_type', 'description', 'is_active']


class OwnerSerializer(serializers.ModelSerializer):
    """Serializer for Owner model."""
    ar_balance = serializers.SerializerMethodField()

    class Meta:
        model = Owner
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'mailing_address', 'is_board_member', 'status', 'ar_balance'
        ]

    def get_ar_balance(self, obj):
        return str(obj.get_ar_balance())


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for Unit model."""
    current_owners = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            'id', 'unit_number', 'property_address', 'bedrooms',
            'bathrooms', 'square_feet', 'monthly_assessment',
            'status', 'current_owners'
        ]

    def get_current_owners(self, obj):
        owners = obj.get_current_owners()
        return [f"{o.first_name} {o.last_name}" for o in owners]


class InvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceLine model."""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ['line_number', 'description', 'account_number', 'account_name', 'amount']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    owner_name = serializers.SerializerMethodField()
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    aging_bucket = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'owner_name', 'unit_number',
            'invoice_date', 'due_date', 'invoice_type', 'status',
            'subtotal', 'late_fee', 'total_amount', 'amount_paid',
            'amount_due', 'description', 'days_overdue', 'aging_bucket', 'lines'
        ]

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"


class PaymentApplicationSerializer(serializers.ModelSerializer):
    """Serializer for PaymentApplication model."""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)

    class Meta:
        model = PaymentApplication
        fields = ['invoice_number', 'amount_applied', 'applied_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    owner_name = serializers.SerializerMethodField()
    applications = PaymentApplicationSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'owner_name', 'payment_date',
            'payment_method', 'amount', 'amount_applied', 'amount_unapplied',
            'status', 'reference_number', 'applications'
        ]

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"


class JournalEntryLineSerializer(serializers.ModelSerializer):
    """Serializer for JournalEntryLine model."""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = [
            'line_number', 'account_number', 'account_name',
            'debit_amount', 'credit_amount', 'description'
        ]


class JournalEntrySerializer(serializers.ModelSerializer):
    """Serializer for JournalEntry model."""
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'entry_number', 'entry_date', 'description',
            'entry_type', 'posted_at', 'is_balanced', 'lines'
        ]


# Special serializers for reports

class ARAgingSerializer(serializers.Serializer):
    """Serializer for AR Aging report data."""
    owner_id = serializers.UUIDField()
    owner_name = serializers.CharField()
    current = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_1_30 = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_31_60 = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_61_90 = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_90_plus = serializers.DecimalField(max_digits=15, decimal_places=2)
    total = serializers.DecimalField(max_digits=15, decimal_places=2)


class OwnerLedgerTransactionSerializer(serializers.Serializer):
    """Serializer for owner ledger transactions."""
    date = serializers.DateField()
    type = serializers.CharField()
    number = serializers.CharField()
    description = serializers.CharField()
    charges = serializers.DecimalField(max_digits=15, decimal_places=2)
    payments = serializers.DecimalField(max_digits=15, decimal_places=2)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)


class DashboardMetricsSerializer(serializers.Serializer):
    """Serializer for dashboard metrics."""
    total_ar = serializers.DecimalField(max_digits=15, decimal_places=2)
    current_ar = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_ar = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    total_owners = serializers.IntegerField()
    delinquent_owners = serializers.IntegerField()
    recent_payments = PaymentSerializer(many=True)


class BudgetLineSerializer(serializers.ModelSerializer):
    """Serializer for BudgetLine model."""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    
    class Meta:
        model = BudgetLine
        fields = [
            'id', 'account', 'account_number', 'account_name',
            'budgeted_amount', 'notes'
        ]


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model."""
    lines = BudgetLineSerializer(many=True, read_only=True)
    total_budgeted = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'fiscal_year', 'start_date', 'end_date',
            'fund', 'status', 'approved_by', 'approved_by_name',
            'approved_at', 'notes', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'lines', 'total_budgeted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_at']
    
    def get_total_budgeted(self, obj):
        return str(obj.get_total_budgeted())
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class BudgetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating budgets with lines."""
    lines = BudgetLineSerializer(many=True)
    
    class Meta:
        model = Budget
        fields = [
            'name', 'fiscal_year', 'start_date', 'end_date',
            'fund', 'notes', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        
        # Set tenant and created_by from context
        validated_data['tenant'] = self.context['tenant']
        validated_data['created_by'] = self.context['request'].user
        
        # Create budget
        budget = Budget.objects.create(**validated_data)
        
        # Create budget lines
        for line_data in lines_data:
            BudgetLine.objects.create(budget=budget, **line_data)
        
        return budget
