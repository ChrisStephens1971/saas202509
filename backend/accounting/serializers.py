"""
Django REST Framework serializers for accounting API.
"""

from rest_framework import serializers
from decimal import Decimal
from .models import (
    Account, Fund, JournalEntry, JournalEntryLine,
    Owner, Unit, Ownership, Invoice, InvoiceLine, Payment, PaymentApplication,
    Budget, BudgetLine, BankStatement, BankTransaction, ReconciliationRule,
    ReserveStudy, ReserveComponent, ReserveScenario,
    CustomReport, ReportExecution,
    LateFeeRule, DelinquencyStatus, CollectionNotice, CollectionAction,
    AutoMatchRule, MatchResult, MatchStatistics,
    Violation, ViolationPhoto, ViolationNotice, ViolationHearing,
    BoardPacketTemplate, BoardPacket, PacketSection,
    # Phase 3: Violation Tracking
    ViolationType, FineSchedule, ViolationEscalation, ViolationFine,
    # Phase 3: ARC Workflow
    ARCRequestType, ARCRequest, ARCDocument, ARCReview, ARCApproval, ARCCompletion,
    # Phase 3: Work Orders
    WorkOrderCategory, Vendor, WorkOrder, WorkOrderComment, WorkOrderAttachment, WorkOrderInvoice,
    # Phase 4: Retention Features
    AuditorExport
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


class BankStatementSerializer(serializers.ModelSerializer):
    """Serializer for BankStatement model."""
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    matched_count = serializers.IntegerField(read_only=True)
    unmatched_count = serializers.SerializerMethodField()
    total_deposits = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_withdrawals = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    calculated_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = BankStatement
        fields = [
            'id', 'fund', 'fund_name', 'statement_date',
            'beginning_balance', 'ending_balance', 'file_name',
            'uploaded_at', 'uploaded_by', 'uploaded_by_name',
            'reconciled', 'reconciled_at', 'notes',
            'matched_count', 'unmatched_count',
            'total_deposits', 'total_withdrawals', 'calculated_balance'
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by', 'reconciled_at']

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None

    def get_unmatched_count(self, obj):
        return obj.transactions.filter(status=BankTransaction.STATUS_UNMATCHED).count()


class BankTransactionSerializer(serializers.ModelSerializer):
    """Serializer for BankTransaction model."""
    statement_date = serializers.DateField(source='statement.statement_date', read_only=True)
    matched_entry_description = serializers.SerializerMethodField()

    class Meta:
        model = BankTransaction
        fields = [
            'id', 'statement', 'statement_date', 'transaction_date', 'post_date',
            'description', 'amount', 'check_number', 'reference_number',
            'status', 'matched_entry', 'matched_entry_description',
            'match_confidence', 'notes'
        ]
        read_only_fields = ['id']

    def get_matched_entry_description(self, obj):
        if obj.matched_entry:
            return obj.matched_entry.description
        return None


class ReconciliationRuleSerializer(serializers.ModelSerializer):
    """Serializer for ReconciliationRule model."""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = ReconciliationRule
        fields = [
            'id', 'name', 'description_pattern',
            'account', 'account_number', 'account_name',
            'fund', 'fund_name',
            'amount_min', 'amount_max', 'active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MatchSuggestionSerializer(serializers.Serializer):
    """Serializer for match suggestions."""
    journal_entry = JournalEntrySerializer(read_only=True)
    confidence = serializers.IntegerField()
    reason = serializers.CharField()


class ReconciliationReportSerializer(serializers.Serializer):
    """Serializer for reconciliation report."""
    statement = BankStatementSerializer(read_only=True)
    beginning_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_deposits = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_withdrawals = serializers.DecimalField(max_digits=15, decimal_places=2)
    ending_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    calculated_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    difference = serializers.DecimalField(max_digits=15, decimal_places=2)
    matched_count = serializers.IntegerField()
    unmatched_count = serializers.IntegerField()
    ignored_count = serializers.IntegerField()
    transactions = BankTransactionSerializer(many=True, read_only=True)


# ===========================
# Reserve Planning Serializers
# ===========================

class ReserveComponentSerializer(serializers.ModelSerializer):
    """Serializer for ReserveComponent model."""
    inflated_cost = serializers.SerializerMethodField()
    replacement_year = serializers.SerializerMethodField()

    class Meta:
        model = ReserveComponent
        fields = [
            'id', 'study', 'name', 'description', 'category',
            'quantity', 'unit', 'useful_life_years', 'remaining_life_years',
            'current_cost', 'inflated_cost', 'replacement_year',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_inflated_cost(self, obj):
        return str(obj.get_inflated_cost())

    def get_replacement_year(self, obj):
        return obj.get_replacement_year()


class ReserveScenarioSerializer(serializers.ModelSerializer):
    """Serializer for ReserveScenario model."""

    class Meta:
        model = ReserveScenario
        fields = [
            'id', 'study', 'name', 'description',
            'monthly_contribution', 'one_time_contribution',
            'contribution_increase_rate', 'is_baseline', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReserveStudySerializer(serializers.ModelSerializer):
    """Serializer for ReserveStudy model."""
    components = ReserveComponentSerializer(many=True, read_only=True)
    scenarios = ReserveScenarioSerializer(many=True, read_only=True)
    current_reserve_balance = serializers.SerializerMethodField()

    class Meta:
        model = ReserveStudy
        fields = [
            'id', 'name', 'study_date', 'horizon_years',
            'inflation_rate', 'interest_rate', 'notes',
            'components', 'scenarios', 'current_reserve_balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_current_reserve_balance(self, obj):
        return str(obj.get_current_reserve_balance())


class FundingProjectionSerializer(serializers.Serializer):
    """Serializer for funding projections."""
    year = serializers.IntegerField()
    beginning_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    contributions = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenditures = serializers.DecimalField(max_digits=15, decimal_places=2)
    interest_earned = serializers.DecimalField(max_digits=15, decimal_places=2)
    ending_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    percent_funded = serializers.DecimalField(max_digits=5, decimal_places=2)


# ===========================
# Advanced Reporting Serializers
# ===========================

class CustomReportSerializer(serializers.ModelSerializer):
    """Serializer for CustomReport model."""
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    execution_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomReport
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'columns', 'filters', 'sort_by', 'is_public', 'is_favorite',
            'created_by', 'execution_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_execution_count(self, obj):
        return obj.executions.count()


class ReportExecutionSerializer(serializers.ModelSerializer):
    """Serializer for ReportExecution model."""
    report_name = serializers.CharField(source='report.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ReportExecution
        fields = [
            'id', 'report', 'report_name', 'executed_by', 'status', 'status_display',
            'started_at', 'completed_at', 'row_count', 'execution_time_ms',
            'error_message', 'result_cache', 'parameters', 'created_at'
        ]
        read_only_fields = ['id', 'started_at', 'created_at']


# ===========================
# Delinquency & Collections Serializers
# ===========================

class LateFeeRuleSerializer(serializers.ModelSerializer):
    """Serializer for LateFeeRule model."""
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)

    class Meta:
        model = LateFeeRule
        fields = [
            'id', 'name', 'grace_period_days', 'fee_type', 'fee_type_display',
            'flat_amount', 'percentage_rate', 'max_amount', 'is_recurring',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DelinquencyStatusSerializer(serializers.ModelSerializer):
    """Serializer for DelinquencyStatus model."""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    stage_display = serializers.CharField(source='get_collection_stage_display', read_only=True)

    class Meta:
        model = DelinquencyStatus
        fields = [
            'id', 'owner', 'owner_name', 'current_balance',
            'balance_0_30', 'balance_31_60', 'balance_61_90', 'balance_90_plus',
            'collection_stage', 'stage_display', 'days_delinquent',
            'last_payment_date', 'last_notice_date', 'is_payment_plan',
            'notes', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class CollectionNoticeSerializer(serializers.ModelSerializer):
    """Serializer for CollectionNotice model."""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    notice_type_display = serializers.CharField(source='get_notice_type_display', read_only=True)
    method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)

    class Meta:
        model = CollectionNotice
        fields = [
            'id', 'owner', 'owner_name', 'notice_type', 'notice_type_display',
            'delivery_method', 'method_display', 'sent_date', 'balance_at_notice',
            'tracking_number', 'delivered_date', 'returned_undeliverable',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CollectionActionSerializer(serializers.ModelSerializer):
    """Serializer for CollectionAction model."""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CollectionAction
        fields = [
            'id', 'owner', 'owner_name', 'action_type', 'action_type_display',
            'status', 'status_display', 'requested_date', 'approved_date',
            'approved_by', 'completed_date', 'balance_at_action',
            'attorney_name', 'case_number', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===========================
# Auto-Matching Engine Serializers
# ===========================

class AutoMatchRuleSerializer(serializers.ModelSerializer):
    """Serializer for AutoMatchRule model."""
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)

    class Meta:
        model = AutoMatchRule
        fields = [
            'id', 'tenant', 'rule_type', 'rule_type_display', 'pattern',
            'confidence_score', 'times_used', 'times_correct',
            'accuracy_rate', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'times_used', 'times_correct', 'accuracy_rate', 'created_at', 'updated_at']


class MatchResultSerializer(serializers.ModelSerializer):
    """Serializer for MatchResult model."""
    bank_transaction_description = serializers.CharField(source='bank_transaction.description', read_only=True)
    matched_entry_reference = serializers.CharField(source='matched_entry.reference', read_only=True)

    class Meta:
        model = MatchResult
        fields = [
            'id', 'tenant', 'bank_transaction', 'bank_transaction_description',
            'matched_entry', 'matched_entry_reference', 'confidence_score',
            'match_explanation', 'matched_by_rule', 'was_accepted',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MatchStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for MatchStatistics model."""

    class Meta:
        model = MatchStatistics
        fields = [
            'id', 'tenant', 'period_start', 'period_end',
            'total_transactions', 'auto_matched', 'manually_matched',
            'unmatched', 'auto_match_rate', 'average_confidence',
            'false_positive_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ===========================
# Violation Tracking Serializers
# ===========================

class ViolationPhotoSerializer(serializers.ModelSerializer):
    """Serializer for ViolationPhoto model."""

    class Meta:
        model = ViolationPhoto
        fields = [
            'id', 'violation', 'photo_url', 'caption',
            'taken_date', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']


class ViolationNoticeSerializer(serializers.ModelSerializer):
    """Serializer for ViolationNotice model."""
    notice_type_display = serializers.CharField(source='get_notice_type_display', read_only=True)
    method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)

    class Meta:
        model = ViolationNotice
        fields = [
            'id', 'violation', 'notice_type', 'notice_type_display',
            'delivery_method', 'method_display', 'sent_date',
            'tracking_number', 'delivered_date', 'cure_deadline',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ViolationHearingSerializer(serializers.ModelSerializer):
    """Serializer for ViolationHearing model."""
    outcome_display = serializers.CharField(source='get_outcome_display', read_only=True)

    class Meta:
        model = ViolationHearing
        fields = [
            'id', 'violation', 'scheduled_date', 'scheduled_time',
            'location', 'attendees', 'outcome', 'outcome_display',
            'fine_assessed', 'compliance_deadline', 'hearing_notes',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ViolationSerializer(serializers.ModelSerializer):
    """Serializer for Violation model."""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    property_address = serializers.CharField(source='owner.property_address', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    photos = ViolationPhotoSerializer(many=True, read_only=True, source='violationphoto_set')
    notices = ViolationNoticeSerializer(many=True, read_only=True, source='violationnotice_set')
    hearings = ViolationHearingSerializer(many=True, read_only=True, source='violationhearing_set')

    class Meta:
        model = Violation
        fields = [
            'id', 'tenant', 'owner', 'owner_name', 'property_address',
            'violation_type', 'severity', 'severity_display',
            'status', 'status_display', 'reported_date',
            'first_notice_date', 'compliance_date', 'fine_amount',
            'is_paid', 'description', 'resolution_notes',
            'photos', 'notices', 'hearings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===========================
# Board Packet Generation Serializers
# ===========================

class PacketSectionSerializer(serializers.ModelSerializer):
    """Serializer for PacketSection model."""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)

    class Meta:
        model = PacketSection
        fields = [
            'id', 'packet', 'section_type', 'section_type_display',
            'title', 'content_url', 'content_data', 'order',
            'page_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BoardPacketSerializer(serializers.ModelSerializer):
    """Serializer for BoardPacket model."""
    template_name = serializers.CharField(source='template.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sections = PacketSectionSerializer(many=True, read_only=True, source='packetsection_set')

    class Meta:
        model = BoardPacket
        fields = [
            'id', 'tenant', 'template', 'template_name',
            'meeting_date', 'status', 'status_display',
            'pdf_url', 'page_count', 'generated_at',
            'generated_by', 'sent_to', 'sent_at',
            'sections', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'created_at', 'updated_at']


class BoardPacketTemplateSerializer(serializers.ModelSerializer):
    """Serializer for BoardPacketTemplate model."""

    class Meta:
        model = BoardPacketTemplate
        fields = [
            'id', 'tenant', 'name', 'description',
            'sections', 'section_order',
            'include_cover_page', 'cover_page_template',
            'header_text', 'footer_text',
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# PHASE 3: OPERATIONAL FEATURES - API Serializers
# ============================================================================

# ----------------------------------------------------------------------------
# Sprint 15: Violation Tracking Serializers
# ----------------------------------------------------------------------------

class ViolationTypeSerializer(serializers.ModelSerializer):
    """Serializer for ViolationType model."""

    class Meta:
        model = ViolationType
        fields = [
            'id', 'tenant', 'code', 'name', 'description',
            'category', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FineScheduleSerializer(serializers.ModelSerializer):
    """Serializer for FineSchedule model."""
    violation_type_code = serializers.CharField(source='violation_type.code', read_only=True)
    violation_type_name = serializers.CharField(source='violation_type.name', read_only=True)

    class Meta:
        model = FineSchedule
        fields = [
            'id', 'violation_type', 'violation_type_code', 'violation_type_name',
            'step_number', 'step_name', 'days_after_previous',
            'fine_amount', 'description', 'requires_board_approval',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ViolationEscalationSerializer(serializers.ModelSerializer):
    """Serializer for ViolationEscalation model."""
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ViolationEscalation
        fields = [
            'id', 'violation', 'step_number', 'step_name',
            'escalated_at', 'fine_amount', 'notice_sent',
            'notice_sent_at', 'notice_method', 'tracking_number',
            'notes', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'escalated_at']

    def get_created_by_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}" if obj.created_by else None


class ViolationFineSerializer(serializers.ModelSerializer):
    """Serializer for ViolationFine model."""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    waived_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ViolationFine
        fields = [
            'id', 'violation', 'escalation', 'invoice', 'invoice_number',
            'journal_entry', 'amount', 'posted_date', 'paid_date',
            'status', 'waived_reason', 'waived_by', 'waived_by_name',
            'waived_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_waived_by_name(self, obj):
        return f"{obj.waived_by.first_name} {obj.waived_by.last_name}" if obj.waived_by else None


# Enhanced Violation serializer with Phase 3 relationships
class ViolationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Violation model with Phase 3 relationships."""
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)
    owner_name = serializers.SerializerMethodField()
    violation_type_name = serializers.CharField(source='violation_type.name', read_only=True)
    photos = ViolationPhotoSerializer(many=True, read_only=True)
    notices = ViolationNoticeSerializer(many=True, read_only=True)
    escalations = ViolationEscalationSerializer(many=True, read_only=True)
    fines = ViolationFineSerializer(many=True, read_only=True)

    class Meta:
        model = Violation
        fields = [
            'id', 'tenant', 'unit', 'unit_number', 'owner', 'owner_name',
            'violation_type', 'violation_type_name', 'status',
            'discovered_date', 'due_date', 'cured_date',
            'first_notice_date', 'compliance_date',
            'description', 'resolution_notes',
            'photos', 'notices', 'escalations', 'fines',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}" if obj.owner else None


# ----------------------------------------------------------------------------
# Sprint 16: ARC Workflow Serializers
# ----------------------------------------------------------------------------

class ARCRequestTypeSerializer(serializers.ModelSerializer):
    """Serializer for ARCRequestType model."""

    class Meta:
        model = ARCRequestType
        fields = [
            'id', 'tenant', 'code', 'name', 'description',
            'requires_plans', 'requires_contractor',
            'typical_review_days', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ARCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for ARCDocument model."""
    uploaded_by_name = serializers.SerializerMethodField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = ARCDocument
        fields = [
            'id', 'request', 'document_type', 'document_type_display',
            'file_url', 'file_name', 'file_size',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']

    def get_uploaded_by_name(self, obj):
        return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}" if obj.uploaded_by else None


class ARCReviewSerializer(serializers.ModelSerializer):
    """Serializer for ARCReview model."""
    reviewer_name = serializers.SerializerMethodField()
    decision_display = serializers.CharField(source='get_decision_display', read_only=True)

    class Meta:
        model = ARCReview
        fields = [
            'id', 'request', 'reviewer', 'reviewer_name',
            'review_date', 'decision', 'decision_display',
            'comments', 'conditions'
        ]
        read_only_fields = ['id', 'review_date']

    def get_reviewer_name(self, obj):
        return f"{obj.reviewer.first_name} {obj.reviewer.last_name}" if obj.reviewer else None


class ARCApprovalSerializer(serializers.ModelSerializer):
    """Serializer for ARCApproval model."""
    approved_by_name = serializers.SerializerMethodField()
    final_decision_display = serializers.CharField(source='get_final_decision_display', read_only=True)

    class Meta:
        model = ARCApproval
        fields = [
            'id', 'request', 'final_decision', 'final_decision_display',
            'decision_date', 'conditions', 'expiration_date',
            'approved_by', 'approved_by_name', 'board_resolution',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_approved_by_name(self, obj):
        return f"{obj.approved_by.first_name} {obj.approved_by.last_name}" if obj.approved_by else None


class ARCCompletionSerializer(serializers.ModelSerializer):
    """Serializer for ARCCompletion model."""
    inspected_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ARCCompletion
        fields = [
            'id', 'request', 'inspected_by', 'inspected_by_name',
            'inspection_date', 'complies_with_approval',
            'inspector_notes', 'photo_url', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_inspected_by_name(self, obj):
        return f"{obj.inspected_by.first_name} {obj.inspected_by.last_name}" if obj.inspected_by else None


class ARCRequestSerializer(serializers.ModelSerializer):
    """Serializer for ARCRequest model - List view."""
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)
    owner_name = serializers.SerializerMethodField()
    request_type_name = serializers.CharField(source='request_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ARCRequest
        fields = [
            'id', 'tenant', 'unit', 'unit_number', 'owner', 'owner_name',
            'request_type', 'request_type_name', 'status', 'status_display',
            'title', 'description', 'requested_start_date',
            'estimated_completion_date', 'contractor_name',
            'submitted_at', 'reviewed_at', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}" if obj.owner else None


class ARCRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for ARCRequest model with all relationships."""
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)
    owner_name = serializers.SerializerMethodField()
    request_type_name = serializers.CharField(source='request_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents = ARCDocumentSerializer(many=True, read_only=True)
    reviews = ARCReviewSerializer(many=True, read_only=True)
    approval = ARCApprovalSerializer(read_only=True)
    completion = ARCCompletionSerializer(read_only=True)

    class Meta:
        model = ARCRequest
        fields = [
            'id', 'tenant', 'unit', 'unit_number', 'owner', 'owner_name',
            'request_type', 'request_type_name', 'status', 'status_display',
            'title', 'description', 'requested_start_date',
            'estimated_completion_date', 'contractor_name',
            'contractor_license', 'contractor_phone',
            'submitted_at', 'reviewed_at', 'completed_at',
            'documents', 'reviews', 'approval', 'completion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}" if obj.owner else None


# ----------------------------------------------------------------------------
# Sprint 17: Work Order System Serializers
# ----------------------------------------------------------------------------

class WorkOrderCategorySerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderCategory model."""
    default_gl_account_name = serializers.CharField(source='default_gl_account.name', read_only=True)

    class Meta:
        model = WorkOrderCategory
        fields = [
            'id', 'tenant', 'code', 'name', 'description',
            'default_gl_account', 'default_gl_account_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model."""

    class Meta:
        model = Vendor
        fields = [
            'id', 'tenant', 'name', 'contact_name', 'phone',
            'email', 'address', 'tax_id', 'license_number',
            'insurance_expiration', 'payment_terms', 'specialty',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkOrderCommentSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderComment model."""
    commented_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderComment
        fields = [
            'id', 'work_order', 'comment', 'commented_by',
            'commented_by_name', 'commented_at', 'is_internal'
        ]
        read_only_fields = ['id', 'commented_at']

    def get_commented_by_name(self, obj):
        return f"{obj.commented_by.first_name} {obj.commented_by.last_name}" if obj.commented_by else None


class WorkOrderAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderAttachment model."""
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderAttachment
        fields = [
            'id', 'work_order', 'file_url', 'file_name',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']

    def get_uploaded_by_name(self, obj):
        return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}" if obj.uploaded_by else None


class WorkOrderInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderInvoice model."""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = WorkOrderInvoice
        fields = [
            'id', 'work_order', 'vendor', 'vendor_name',
            'invoice_number', 'invoice_date', 'amount',
            'payment_status', 'payment_status_display',
            'journal_entry', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_approved_by_name(self, obj):
        return f"{obj.approved_by.first_name} {obj.approved_by.last_name}" if obj.approved_by else None


class WorkOrderSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrder model - List view."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='assigned_to_vendor.name', read_only=True)
    assigned_staff_name = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'tenant', 'work_order_number', 'category', 'category_name',
            'title', 'description', 'priority', 'priority_display',
            'status', 'status_display', 'location', 'unit', 'unit_number',
            'requested_by', 'assigned_to_vendor', 'vendor_name',
            'assigned_to_staff', 'assigned_staff_name',
            'estimated_cost', 'actual_cost', 'gl_account', 'fund',
            'requested_date', 'scheduled_date', 'completed_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_assigned_staff_name(self, obj):
        return f"{obj.assigned_to_staff.first_name} {obj.assigned_to_staff.last_name}" if obj.assigned_to_staff else None


class WorkOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for WorkOrder model with all relationships."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='assigned_to_vendor.name', read_only=True)
    assigned_staff_name = serializers.SerializerMethodField()
    requested_by_name = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)
    gl_account_name = serializers.CharField(source='gl_account.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    comments = WorkOrderCommentSerializer(many=True, read_only=True)
    attachments = WorkOrderAttachmentSerializer(many=True, read_only=True)
    invoices = WorkOrderInvoiceSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'tenant', 'work_order_number', 'category', 'category_name',
            'title', 'description', 'priority', 'priority_display',
            'status', 'status_display', 'location', 'unit', 'unit_number',
            'requested_by', 'requested_by_name',
            'assigned_to_vendor', 'vendor_name',
            'assigned_to_staff', 'assigned_staff_name',
            'estimated_cost', 'actual_cost',
            'gl_account', 'gl_account_name', 'fund', 'fund_name',
            'requested_date', 'scheduled_date', 'completed_date',
            'comments', 'attachments', 'invoices',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_assigned_staff_name(self, obj):
        return f"{obj.assigned_to_staff.first_name} {obj.assigned_to_staff.last_name}" if obj.assigned_to_staff else None

    def get_requested_by_name(self, obj):
        return f"{obj.requested_by.first_name} {obj.requested_by.last_name}" if obj.requested_by else None


# ============================================================================
# PHASE 4: RETENTION FEATURES - Serializers
# ============================================================================

# ----------------------------------------------------------------------------
# Sprint 21: Auditor Export
# ----------------------------------------------------------------------------

class AuditorExportSerializer(serializers.ModelSerializer):
    """
    Serializer for auditor exports.

    Includes computed fields for evidence percentage and balance status.
    """
    generated_by_name = serializers.SerializerMethodField()
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    evidence_percentage = serializers.ReadOnlyField()
    is_balanced = serializers.SerializerMethodField()

    class Meta:
        model = AuditorExport
        fields = [
            'id', 'tenant', 'title', 'start_date', 'end_date',
            'format', 'format_display',
            'include_evidence', 'include_balances', 'include_owner_data',
            'file_url', 'file_size_bytes', 'file_hash',
            'generated_at', 'generated_by', 'generated_by_name',
            'status', 'status_display',
            'downloaded_count', 'last_downloaded_at',
            'total_entries', 'total_debit', 'total_credit',
            'evidence_count', 'evidence_percentage',
            'is_balanced', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_url', 'file_size_bytes', 'file_hash',
            'generated_at', 'generated_by', 'status',
            'downloaded_count', 'last_downloaded_at',
            'total_entries', 'total_debit', 'total_credit',
            'evidence_count', 'error_message',
            'created_at', 'updated_at'
        ]

    def get_generated_by_name(self, obj):
        """Get full name of user who generated export"""
        if obj.generated_by:
            return f"{obj.generated_by.first_name} {obj.generated_by.last_name}"
        return None

    def get_is_balanced(self, obj):
        """Check if export debits equal credits"""
        return obj.is_balanced()
