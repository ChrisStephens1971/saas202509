"""
Accounting models for multi-tenant HOA fund accounting system.

CRITICAL ACCOUNTING PRINCIPLES:
1. All money fields use NUMERIC(15,2) - NEVER use FloatField
2. Accounting dates use DATE - NEVER use DateTimeField for transaction dates
3. Financial records are IMMUTABLE - Never UPDATE or DELETE (event sourcing)
4. Every journal entry MUST balance (debits = credits)
5. Each tenant has separate fund structure (operating, reserve, special assessment)
"""

from decimal import Decimal
from datetime import date
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
import uuid


class Fund(models.Model):
    """
    Represents a fund within an HOA (Operating, Reserve, Special Assessment).

    Each fund has its own balance sheet. Funds cannot be mixed without board approval.
    """

    # Fund types
    TYPE_OPERATING = 'OPERATING'
    TYPE_RESERVE = 'RESERVE'
    TYPE_SPECIAL_ASSESSMENT = 'SPECIAL_ASSESSMENT'

    TYPE_CHOICES = [
        (TYPE_OPERATING, 'Operating Fund'),
        (TYPE_RESERVE, 'Reserve Fund'),
        (TYPE_SPECIAL_ASSESSMENT, 'Special Assessment Fund'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,  # Never allow deletion of tenant with funds
        related_name='funds',
        help_text="The HOA (tenant) this fund belongs to"
    )

    name = models.CharField(
        max_length=100,
        help_text="Fund name (e.g., 'Operating Fund', 'Reserve Fund')"
    )

    fund_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type of fund"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of fund purpose"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this fund is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'funds'
        ordering = ['fund_type', 'name']
        unique_together = [['tenant', 'fund_type']]  # One operating, one reserve, etc per tenant
        indexes = [
            models.Index(fields=['tenant', 'fund_type']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class AccountType(models.Model):
    """
    Account types for chart of accounts (Asset, Liability, Equity, Revenue, Expense).

    Each type has a normal balance (debit or credit) which determines how increases/decreases work.
    """

    # Account type codes
    CODE_ASSET = 'ASSET'
    CODE_LIABILITY = 'LIABILITY'
    CODE_EQUITY = 'EQUITY'
    CODE_REVENUE = 'REVENUE'
    CODE_EXPENSE = 'EXPENSE'

    CODE_CHOICES = [
        (CODE_ASSET, 'Asset'),
        (CODE_LIABILITY, 'Liability'),
        (CODE_EQUITY, 'Equity'),
        (CODE_REVENUE, 'Revenue'),
        (CODE_EXPENSE, 'Expense'),
    ]

    # Normal balance (how increases are recorded)
    BALANCE_DEBIT = 'DEBIT'
    BALANCE_CREDIT = 'CREDIT'

    BALANCE_CHOICES = [
        (BALANCE_DEBIT, 'Debit'),
        (BALANCE_CREDIT, 'Credit'),
    ]

    code = models.CharField(
        max_length=20,
        primary_key=True,
        choices=CODE_CHOICES,
        help_text="Account type code"
    )

    name = models.CharField(
        max_length=100,
        help_text="Account type name"
    )

    normal_balance = models.CharField(
        max_length=10,
        choices=BALANCE_CHOICES,
        help_text="Normal balance (Debit or Credit)"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this account type"
    )

    class Meta:
        db_table = 'account_types'
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.normal_balance})"


class Account(models.Model):
    """
    Individual account in the chart of accounts.

    Accounts are organized by fund and account type. Supports hierarchical accounts (parent/child).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='accounts',
        help_text="The HOA (tenant) this account belongs to"
    )

    fund = models.ForeignKey(
        Fund,
        on_delete=models.PROTECT,
        related_name='accounts',
        help_text="The fund this account belongs to"
    )

    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name='accounts',
        help_text="Type of account (Asset, Liability, etc.)"
    )

    account_number = models.CharField(
        max_length=20,
        help_text="Account number (e.g., '1100', '5200')"
    )

    name = models.CharField(
        max_length=200,
        help_text="Account name (e.g., 'Operating Cash', 'Landscaping Expense')"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this account"
    )

    parent_account = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='sub_accounts',
        help_text="Parent account for hierarchical accounts"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this account is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts'
        ordering = ['account_number']
        unique_together = [['tenant', 'fund', 'account_number']]
        indexes = [
            models.Index(fields=['tenant', 'fund']),
            models.Index(fields=['tenant', 'account_type']),
            models.Index(fields=['account_number']),
        ]

    def __str__(self):
        return f"{self.account_number} - {self.name}"

    def clean(self):
        """Validate account belongs to same tenant as fund"""
        if self.fund and self.fund.tenant_id != self.tenant_id:
            raise ValidationError("Account fund must belong to the same tenant")

    def get_balance(self):
        """
        Calculate current balance for this account.

        Returns Decimal (positive for normal balance, negative for opposite).
        """
        from django.db.models import Sum, Q

        # Sum all debits and credits for this account
        lines = JournalEntryLine.objects.filter(account=self)
        debits = lines.aggregate(total=Sum('debit_amount'))['total'] or Decimal('0.00')
        credits = lines.aggregate(total=Sum('credit_amount'))['total'] or Decimal('0.00')

        # Calculate balance based on normal balance
        if self.account_type.normal_balance == AccountType.BALANCE_DEBIT:
            return debits - credits
        else:
            return credits - debits


class JournalEntry(models.Model):
    """
    Journal entry header (immutable).

    Each journal entry contains multiple lines (debits and credits) that must balance.
    Once posted, journal entries CANNOT be modified or deleted (event sourcing).
    """

    # Entry types
    TYPE_MANUAL = 'MANUAL'
    TYPE_INVOICE = 'INVOICE'
    TYPE_PAYMENT = 'PAYMENT'
    TYPE_ADJUSTMENT = 'ADJUSTMENT'
    TYPE_REVERSAL = 'REVERSAL'
    TYPE_TRANSFER = 'TRANSFER'

    TYPE_CHOICES = [
        (TYPE_MANUAL, 'Manual Entry'),
        (TYPE_INVOICE, 'Invoice'),
        (TYPE_PAYMENT, 'Payment'),
        (TYPE_ADJUSTMENT, 'Adjustment'),
        (TYPE_REVERSAL, 'Reversal'),
        (TYPE_TRANSFER, 'Inter-fund Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='journal_entries',
        help_text="The HOA (tenant) this entry belongs to"
    )

    entry_number = models.BigIntegerField(
        help_text="Sequential entry number (auto-generated per tenant)"
    )

    entry_date = models.DateField(
        help_text="Accounting date (DATE not TIMESTAMPTZ - critical for accounting)"
    )

    description = models.TextField(
        help_text="Description of this journal entry"
    )

    entry_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_MANUAL,
        help_text="Type of journal entry"
    )

    reference_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to source document (invoice, payment, etc.)"
    )

    # Immutability and audit trail
    posted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this entry was posted (UTC timestamp)"
    )

    posted_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="User ID who posted this entry"
    )

    reversed_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='reverses',
        help_text="Reversal entry (if this entry was reversed)"
    )

    # Optional: Cryptographic hash chain for tamper detection
    previous_entry_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash of previous entry (cryptographic chain)"
    )

    entry_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash of this entry for tamper detection"
    )

    class Meta:
        db_table = 'journal_entries'
        ordering = ['-entry_date', '-entry_number']
        unique_together = [['tenant', 'entry_number']]
        indexes = [
            models.Index(fields=['tenant', 'entry_date']),
            models.Index(fields=['tenant', 'entry_number']),
            models.Index(fields=['entry_type']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"JE-{self.entry_number} ({self.entry_date})"

    def clean(self):
        """Validate journal entry balances (debits = credits)"""
        if self.pk:  # Only validate if entry has lines
            total_debits, total_credits = self.get_totals()
            if total_debits != total_credits:
                raise ValidationError(
                    f"Journal entry does not balance: "
                    f"Debits ${total_debits} != Credits ${total_credits}"
                )

    def get_totals(self):
        """Calculate total debits and credits for this entry"""
        lines = self.lines.all()
        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)
        return (Decimal(str(total_debits)), Decimal(str(total_credits)))

    def is_balanced(self):
        """Check if this journal entry balances"""
        total_debits, total_credits = self.get_totals()
        return total_debits == total_credits

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Override save to auto-generate entry_number.

        Entry numbers are sequential per tenant.
        """
        if not self.entry_number:
            # Get the last entry number for this tenant
            last_entry = (
                JournalEntry.objects
                .filter(tenant=self.tenant)
                .order_by('-entry_number')
                .first()
            )
            self.entry_number = (last_entry.entry_number + 1) if last_entry else 1

        super().save(*args, **kwargs)


class JournalEntryLine(models.Model):
    """
    Individual line in a journal entry (debit or credit).

    Each line must be EITHER a debit OR a credit (never both).
    Lines are immutable once the journal entry is posted.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,  # Never delete journal entries
        related_name='lines',
        help_text="The journal entry this line belongs to"
    )

    line_number = models.PositiveIntegerField(
        help_text="Line number within this journal entry"
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_lines',
        help_text="The account being debited or credited"
    )

    # CRITICAL: Use DecimalField with max_digits=15, decimal_places=2
    # This maps to NUMERIC(15,2) in PostgreSQL
    debit_amount = models.DecimalField(
        max_digits=settings.ACCOUNTING_SETTINGS['MONEY_MAX_DIGITS'],
        decimal_places=settings.ACCOUNTING_SETTINGS['MONEY_DECIMAL_PLACES'],
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Debit amount (must be 0 if credit is used)"
    )

    credit_amount = models.DecimalField(
        max_digits=settings.ACCOUNTING_SETTINGS['MONEY_MAX_DIGITS'],
        decimal_places=settings.ACCOUNTING_SETTINGS['MONEY_DECIMAL_PLACES'],
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Credit amount (must be 0 if debit is used)"
    )

    description = models.TextField(
        blank=True,
        help_text="Line-specific description (optional)"
    )

    class Meta:
        db_table = 'journal_entry_lines'
        ordering = ['journal_entry', 'line_number']
        unique_together = [['journal_entry', 'line_number']]
        indexes = [
            models.Index(fields=['journal_entry']),
            models.Index(fields=['account']),
        ]
        constraints = [
            # Ensure only debit OR credit (not both)
            models.CheckConstraint(
                check=(
                    models.Q(debit_amount__gt=0, credit_amount=0) |
                    models.Q(credit_amount__gt=0, debit_amount=0)
                ),
                name='debit_or_credit_not_both'
            ),
            # Ensure at least one amount is non-zero
            models.CheckConstraint(
                check=(
                    models.Q(debit_amount__gt=0) |
                    models.Q(credit_amount__gt=0)
                ),
                name='amount_required'
            ),
        ]

    def __str__(self):
        amount = self.debit_amount if self.debit_amount > 0 else self.credit_amount
        side = "DR" if self.debit_amount > 0 else "CR"
        return f"{self.account.account_number} {side} ${amount}"

    def clean(self):
        """Validate journal entry line"""
        # Ensure only debit OR credit (not both)
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError("A line cannot have both debit and credit amounts")

        # Ensure at least one amount is non-zero
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError("A line must have either a debit or credit amount")

        # Validate account belongs to same tenant as journal entry
        if self.account and self.journal_entry:
            if self.account.tenant_id != self.journal_entry.tenant_id:
                raise ValidationError("Account must belong to the same tenant as journal entry")


# ============================================================================
# SPRINT 2: Invoicing & Accounts Receivable Models
# ============================================================================


class Owner(models.Model):
    """
    Represents an HOA unit owner.

    Owners can own multiple units and units can have multiple owners (co-ownership).
    """

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_DELINQUENT = 'delinquent'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_DELINQUENT, 'Delinquent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='owners',
        help_text="The HOA (tenant) this owner belongs to"
    )

    # Personal information
    first_name = models.CharField(max_length=100, help_text="Owner first name")
    last_name = models.CharField(max_length=100, help_text="Owner last name")
    email = models.EmailField(blank=True, help_text="Owner email address")
    phone = models.CharField(max_length=20, blank=True, help_text="Owner phone number")

    # Mailing address
    mailing_address = models.TextField(blank=True, help_text="Mailing address for statements")

    # Status
    is_board_member = models.BooleanField(default=False, help_text="Is this owner a board member?")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text="Owner status"
    )

    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes about this owner")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'owners'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_ar_balance(self):
        """Get total AR balance for this owner"""
        from django.db.models import Sum
        total = Invoice.objects.filter(
            owner=self,
            status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE]
        ).aggregate(total=Sum('amount_due'))['total']
        return total or Decimal('0.00')


class Unit(models.Model):
    """
    Represents a unit/lot in the HOA.

    Units have ownership history tracked through the Ownership model.
    """

    STATUS_OCCUPIED = 'occupied'
    STATUS_VACANT = 'vacant'
    STATUS_RENTED = 'rented'

    STATUS_CHOICES = [
        (STATUS_OCCUPIED, 'Occupied by Owner'),
        (STATUS_VACANT, 'Vacant'),
        (STATUS_RENTED, 'Rented/Leased'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='units',
        help_text="The HOA (tenant) this unit belongs to"
    )

    # Unit identification
    unit_number = models.CharField(
        max_length=20,
        help_text="Unit number (e.g., '123', 'A-5', 'Lot 42')"
    )

    # Property details
    property_address = models.TextField(
        blank=True,
        help_text="Physical address of the unit"
    )

    bedrooms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of bedrooms"
    )

    bathrooms = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Number of bathrooms (e.g., 2.5)"
    )

    square_feet = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Square footage"
    )

    # Assessment information
    monthly_assessment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monthly assessment amount"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OCCUPIED,
        help_text="Unit status"
    )

    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes about this unit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'units'
        ordering = ['unit_number']
        unique_together = [['tenant', 'unit_number']]
        indexes = [
            models.Index(fields=['tenant', 'unit_number']),
            models.Index(fields=['tenant', 'status']),
        ]

    def __str__(self):
        return f"Unit {self.unit_number}"

    def get_current_owners(self):
        """Get list of current owners for this unit"""
        return Owner.objects.filter(
            ownerships__unit=self,
            ownerships__is_current=True
        ).distinct()


class Ownership(models.Model):
    """
    Tracks ownership history for units.

    Supports:
    - Multiple owners per unit (co-ownership)
    - Ownership percentage splits
    - Historical ownership tracking
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='ownerships',
        help_text="The HOA (tenant)"
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.PROTECT,
        related_name='ownerships',
        help_text="The owner"
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='ownerships',
        help_text="The unit"
    )

    # Ownership details
    ownership_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Ownership percentage (usually 100%, but can be split)"
    )

    # Date range
    start_date = models.DateField(help_text="Ownership start date")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Ownership end date (NULL = current owner)"
    )

    is_current = models.BooleanField(
        default=True,
        help_text="Is this the current ownership?"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ownerships'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['tenant', 'owner']),
            models.Index(fields=['tenant', 'unit']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self):
        return f"{self.owner} owns {self.ownership_percentage}% of {self.unit}"

    def clean(self):
        """Validate ownership"""
        # Ensure owner and unit belong to same tenant
        if self.owner and self.owner.tenant_id != self.tenant_id:
            raise ValidationError("Owner must belong to the same tenant")
        if self.unit and self.unit.tenant_id != self.tenant_id:
            raise ValidationError("Unit must belong to the same tenant")

        # If end_date is set, is_current should be False
        if self.end_date and self.is_current:
            raise ValidationError("Ownership with end_date cannot be current")


class Invoice(models.Model):
    """
    Invoice issued to an owner for assessments, late fees, or other charges.

    Each invoice creates a journal entry:
    DR: AR (Asset)
    CR: Revenue (by type)
    """

    # Invoice types
    TYPE_ASSESSMENT = 'ASSESSMENT'
    TYPE_LATE_FEE = 'LATE_FEE'
    TYPE_SPECIAL = 'SPECIAL'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_ASSESSMENT, 'Monthly/Quarterly Assessment'),
        (TYPE_LATE_FEE, 'Late Fee'),
        (TYPE_SPECIAL, 'Special Assessment'),
        (TYPE_OTHER, 'Other Charge'),
    ]

    # Status
    STATUS_DRAFT = 'DRAFT'
    STATUS_ISSUED = 'ISSUED'
    STATUS_PARTIAL = 'PARTIAL'
    STATUS_PAID = 'PAID'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ISSUED, 'Issued'),
        (STATUS_PARTIAL, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="The HOA (tenant)"
    )

    # Invoice identification
    invoice_number = models.CharField(
        max_length=20,
        help_text="Invoice number (auto-generated: INV-00001)"
    )

    # Related entities
    owner = models.ForeignKey(
        Owner,
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="The owner being invoiced"
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="The unit this invoice is for"
    )

    # Dates
    invoice_date = models.DateField(help_text="Invoice date")
    due_date = models.DateField(help_text="Payment due date")

    # Type and status
    invoice_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_ASSESSMENT,
        help_text="Type of invoice"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        help_text="Invoice status"
    )

    # Amounts (NUMERIC(15,2))
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Subtotal before late fees"
    )

    late_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Late fee amount"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount (subtotal + late fee)"
    )

    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount paid so far"
    )

    amount_due = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount still owed (total - paid)"
    )

    # Description
    description = models.TextField(blank=True, help_text="Invoice description")

    # Linked journal entry (auto-created when invoice is issued)
    journal_entry = models.ForeignKey(
        JournalEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="Journal entry created for this invoice"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date', '-invoice_number']
        unique_together = [['tenant', 'invoice_number']]
        indexes = [
            models.Index(fields=['tenant', 'invoice_number']),
            models.Index(fields=['tenant', 'owner']),
            models.Index(fields=['tenant', 'unit']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.owner} - ${self.total_amount}"

    def clean(self):
        """Validate invoice"""
        # Ensure owner and unit belong to same tenant
        if self.owner and self.owner.tenant_id != self.tenant_id:
            raise ValidationError("Owner must belong to the same tenant")
        if self.unit and self.unit.tenant_id != self.tenant_id:
            raise ValidationError("Unit must belong to the same tenant")

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save to auto-generate invoice_number"""
        is_new = self.pk is None
        old_status = None

        if not is_new:
            try:
                old_invoice = Invoice.objects.get(pk=self.pk)
                old_status = old_invoice.status
            except Invoice.DoesNotExist:
                pass

        if not self.invoice_number:
            # Get the last invoice number for this tenant
            last_invoice = (
                Invoice.objects
                .filter(tenant=self.tenant)
                .order_by('-invoice_number')
                .first()
            )
            if last_invoice and last_invoice.invoice_number.startswith('INV-'):
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[1])
                    next_num = last_num + 1
                except (IndexError, ValueError):
                    next_num = 1
            else:
                next_num = 1

            self.invoice_number = f"INV-{next_num:05d}"

        # Calculate total_amount and amount_due
        self.total_amount = self.subtotal + self.late_fee
        self.amount_due = self.total_amount - self.amount_paid

        super().save(*args, **kwargs)

        # Auto-create journal entry when invoice is issued (and doesn't have one yet)
        if self.status == self.STATUS_ISSUED and not self.journal_entry:
            if old_status != self.STATUS_ISSUED or is_new:
                self.create_journal_entry()

    def create_journal_entry(self):
        """
        Create journal entry for invoice:
        DR: Accounts Receivable (1200)
        CR: Revenue accounts (from invoice lines)

        NOTE: Invoice lines must exist before calling this method!
        """
        if self.journal_entry:
            return  # Already has journal entry

        # Check if a journal entry already exists for this invoice
        existing_je = JournalEntry.objects.filter(
            tenant=self.tenant,
            entry_type=JournalEntry.TYPE_INVOICE,
            reference_id=self.id
        ).first()

        if existing_je:
            # Link existing JE and return
            Invoice.objects.filter(pk=self.pk).update(journal_entry=existing_je)
            self.journal_entry = existing_je
            return existing_je

        # Get invoice lines - must exist!
        invoice_lines = self.lines.all()
        if not invoice_lines.exists():
            # Invoice lines don't exist yet, skip journal entry creation
            # It will be created later when lines are added
            return None

        # Get AR account (1200)
        ar_account = Account.objects.filter(
            tenant=self.tenant,
            account_number='1200'
        ).first()

        if not ar_account:
            raise ValidationError("AR account (1200) not found for tenant")

        # Create journal entry
        je = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_date=self.invoice_date,
            description=f"Invoice {self.invoice_number} - {self.owner}",
            entry_type=JournalEntry.TYPE_INVOICE,
            reference_id=self.id
        )

        # Debit line: AR
        JournalEntryLine.objects.create(
            journal_entry=je,
            line_number=1,
            account=ar_account,
            debit_amount=self.total_amount,
            credit_amount=Decimal('0.00'),
            description=f"AR for invoice {self.invoice_number}"
        )

        # Credit lines: Revenue accounts (from invoice lines)
        for idx, line in enumerate(invoice_lines, start=2):
            JournalEntryLine.objects.create(
                journal_entry=je,
                line_number=idx,
                account=line.account,
                debit_amount=Decimal('0.00'),
                credit_amount=line.amount,
                description=line.description
            )

        # Link journal entry to invoice (use queryset update to avoid recursion)
        Invoice.objects.filter(pk=self.pk).update(journal_entry=je)
        self.journal_entry = je

        return je

    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.status in [self.STATUS_PAID, self.STATUS_CANCELLED]:
            return 0
        today = date.today()
        if today > self.due_date:
            return (today - self.due_date).days
        return 0

    @property
    def aging_bucket(self):
        """Get aging bucket for AR aging report"""
        days = self.days_overdue
        if days == 0:
            return 'Current'
        elif days <= 30:
            return '1-30 days'
        elif days <= 60:
            return '31-60 days'
        elif days <= 90:
            return '61-90 days'
        else:
            return '90+ days'

    def calculate_late_fee(self, grace_period_days=5, late_fee_percentage=Decimal('0.05'),
                          minimum_late_fee=Decimal('25.00')):
        """
        Calculate late fee for overdue invoice.

        Args:
            grace_period_days: Number of days after due date before late fee applies (default: 5)
            late_fee_percentage: Late fee as percentage of balance (default: 0.05 = 5%)
            minimum_late_fee: Minimum late fee amount (default: $25.00)

        Returns:
            Decimal: Late fee amount, or 0 if not applicable

        Business Rules:
        - Late fee only applies after grace period
        - Late fee is greater of: percentage of balance or minimum amount
        - Late fee only applies once per invoice
        - Paid/cancelled invoices don't get late fees
        """
        # No late fee if already paid or cancelled
        if self.status in [self.STATUS_PAID, self.STATUS_CANCELLED]:
            return Decimal('0.00')

        # No late fee if already has one
        if self.late_fee > 0:
            return Decimal('0.00')

        # Check if past grace period
        days_overdue = self.days_overdue
        if days_overdue <= grace_period_days:
            return Decimal('0.00')

        # Calculate late fee: greater of percentage or minimum
        percentage_fee = self.amount_due * late_fee_percentage
        late_fee = max(percentage_fee, minimum_late_fee)

        return late_fee.quantize(Decimal('0.01'))

    @transaction.atomic
    def apply_late_fee(self, grace_period_days=5, late_fee_percentage=Decimal('0.05'),
                      minimum_late_fee=Decimal('25.00')):
        """
        Apply late fee to invoice and create journal entry.

        This creates:
        1. Updates invoice.late_fee
        2. Creates InvoiceLine for late fee
        3. Creates journal entry: DR: AR, CR: Late Fee Revenue

        Returns:
            tuple: (late_fee_amount, journal_entry) or (0, None) if not applicable
        """
        late_fee_amount = self.calculate_late_fee(
            grace_period_days=grace_period_days,
            late_fee_percentage=late_fee_percentage,
            minimum_late_fee=minimum_late_fee
        )

        if late_fee_amount == 0:
            return (Decimal('0.00'), None)

        # Get late fee revenue account (4200)
        late_fee_revenue = Account.objects.filter(
            tenant=self.tenant,
            account_number='4200'
        ).first()

        if not late_fee_revenue:
            # Create late fee revenue account if it doesn't exist
            revenue_type = AccountType.objects.get(code='REVENUE')
            operating_fund = Fund.objects.filter(
                tenant=self.tenant,
                fund_type=Fund.TYPE_OPERATING
            ).first()

            late_fee_revenue = Account.objects.create(
                tenant=self.tenant,
                fund=operating_fund,
                account_type=revenue_type,
                account_number='4200',
                name='Late Fee Revenue'
            )

        # Update invoice late fee
        self.late_fee = late_fee_amount
        self.total_amount = self.subtotal + self.late_fee
        self.amount_due = self.total_amount - self.amount_paid

        # Save invoice (use queryset update to avoid triggering save() logic)
        Invoice.objects.filter(pk=self.pk).update(
            late_fee=self.late_fee,
            total_amount=self.total_amount,
            amount_due=self.amount_due
        )

        # Create invoice line for late fee
        last_line = self.lines.order_by('-line_number').first()
        next_line_number = (last_line.line_number + 1) if last_line else 1

        InvoiceLine.objects.create(
            invoice=self,
            line_number=next_line_number,
            description=f"Late fee ({self.days_overdue} days overdue)",
            account=late_fee_revenue,
            amount=late_fee_amount
        )

        # Create journal entry for late fee
        ar_account = Account.objects.filter(
            tenant=self.tenant,
            account_number='1200'
        ).first()

        je = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_date=date.today(),
            description=f"Late fee for {self.invoice_number}",
            entry_type=JournalEntry.TYPE_ADJUSTMENT,
            reference_id=self.id
        )

        # Debit: AR
        JournalEntryLine.objects.create(
            journal_entry=je,
            line_number=1,
            account=ar_account,
            debit_amount=late_fee_amount,
            credit_amount=Decimal('0.00'),
            description=f"Late fee for {self.invoice_number}"
        )

        # Credit: Late Fee Revenue
        JournalEntryLine.objects.create(
            journal_entry=je,
            line_number=2,
            account=late_fee_revenue,
            debit_amount=Decimal('0.00'),
            credit_amount=late_fee_amount,
            description=f"Late fee revenue for {self.invoice_number}"
        )

        return (late_fee_amount, je)

    def generate_pdf(self, output_path=None):
        """
        Generate PDF for this invoice.

        Args:
            output_path: Optional file path to save PDF. If None, returns BytesIO buffer.

        Returns:
            BytesIO buffer or None (if output_path provided)
        """
        from .pdf_generator import generate_invoice_pdf
        return generate_invoice_pdf(self, output_path=output_path)

    def generate_text_invoice(self):
        """
        Generate simple text representation of invoice (no PDF library required).

        Returns:
            str: Formatted text invoice
        """
        from .pdf_generator import generate_invoice_pdf_simple
        return generate_invoice_pdf_simple(self)


class InvoiceLine(models.Model):
    """
    Invoice line items linking to revenue accounts.

    Each line represents a charge on an invoice and specifies which
    revenue account should be credited when the invoice is posted.

    Business rules:
    - Line amounts must sum to invoice subtotal
    - Each line must reference a valid revenue account
    - Lines are immutable once invoice is issued
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this invoice line"
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='lines',
        help_text="Invoice this line belongs to"
    )

    line_number = models.PositiveIntegerField(
        help_text="Line number within the invoice (1, 2, 3...)"
    )

    description = models.TextField(
        help_text="Description of the charge (e.g., 'October 2025 Monthly Assessment')"
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='invoice_lines',
        help_text="Revenue account to credit when invoice is posted"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount for this line item"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoice_lines'
        ordering = ['invoice', 'line_number']
        unique_together = [['invoice', 'line_number']]
        indexes = [
            models.Index(fields=['invoice', 'line_number']),
            models.Index(fields=['account']),
        ]
        verbose_name = "Invoice Line"
        verbose_name_plural = "Invoice Lines"

    def __str__(self):
        return f"Invoice {self.invoice.invoice_number} - Line {self.line_number}: ${self.amount}"


class Payment(models.Model):
    """
    Payment received from an owner.

    Tracks payments and their application to invoices using FIFO logic.
    Creates journal entries when posted (DR: Cash, CR: AR).

    Business rules:
    - Amount = amount_applied + amount_unapplied (always)
    - Payments are applied to oldest invoices first (FIFO)
    - Unapplied amounts create a credit on owner's account
    - Payments are immutable once posted
    """

    # Payment methods
    METHOD_CHECK = 'CHECK'
    METHOD_ACH = 'ACH'
    METHOD_CREDIT_CARD = 'CREDIT_CARD'
    METHOD_DEBIT_CARD = 'DEBIT_CARD'
    METHOD_CASH = 'CASH'
    METHOD_WIRE = 'WIRE'
    METHOD_OTHER = 'OTHER'

    METHOD_CHOICES = [
        (METHOD_CHECK, 'Check'),
        (METHOD_ACH, 'ACH/Bank Transfer'),
        (METHOD_CREDIT_CARD, 'Credit Card'),
        (METHOD_DEBIT_CARD, 'Debit Card'),
        (METHOD_CASH, 'Cash'),
        (METHOD_WIRE, 'Wire Transfer'),
        (METHOD_OTHER, 'Other'),
    ]

    # Payment status
    STATUS_PENDING = 'PENDING'
    STATUS_CLEARED = 'CLEARED'
    STATUS_BOUNCED = 'BOUNCED'
    STATUS_REFUNDED = 'REFUNDED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CLEARED, 'Cleared'),
        (STATUS_BOUNCED, 'Bounced'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this payment"
    )

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='payments',
        help_text="Tenant (HOA) this payment belongs to"
    )

    payment_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Auto-generated payment number (PMT-00001, PMT-00002, etc.)"
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.PROTECT,
        related_name='payments',
        help_text="Owner who made this payment"
    )

    payment_date = models.DateField(
        help_text="Date the payment was received (accounting date)"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default=METHOD_CHECK,
        help_text="Method of payment"
    )

    # Amounts
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total payment amount received"
    )

    amount_applied = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount applied to invoices"
    )

    amount_unapplied = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount not yet applied (credit on account)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CLEARED,
        help_text="Payment status"
    )

    # Metadata
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Check number, transaction ID, confirmation number, etc."
    )

    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this payment"
    )

    # Link to auto-created journal entry
    journal_entry = models.ForeignKey(
        JournalEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='payments',
        help_text="Auto-created journal entry (DR: Cash, CR: AR)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date', '-payment_number']
        indexes = [
            models.Index(fields=['tenant', 'payment_number']),
            models.Index(fields=['owner', 'payment_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name='payment_amount_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(amount_applied__gte=0),
                name='payment_amount_applied_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(amount_unapplied__gte=0),
                name='payment_amount_unapplied_non_negative'
            ),
        ]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.payment_number} - {self.owner} - ${self.amount}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Auto-generate payment number and create journal entry"""
        is_new = self.pk is None

        if not self.payment_number:
            # Get the last payment number for this tenant
            last_payment = Payment.objects.filter(
                tenant=self.tenant
            ).order_by('-payment_number').first()

            if last_payment and last_payment.payment_number:
                try:
                    # Extract number from PMT-00001 format
                    last_number = int(last_payment.payment_number.split('-')[1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1

            self.payment_number = f"PMT-{next_number:05d}"

        # Validate: amount = amount_applied + amount_unapplied
        calculated_total = self.amount_applied + self.amount_unapplied
        if abs(self.amount - calculated_total) > Decimal('0.01'):
            raise ValueError(
                f"Payment amount (${self.amount}) must equal applied (${self.amount_applied}) "
                f"+ unapplied (${self.amount_unapplied})"
            )

        super().save(*args, **kwargs)

        # Auto-create journal entry when payment is cleared (and doesn't have one yet)
        if self.status == self.STATUS_CLEARED and not self.journal_entry and is_new:
            self.create_journal_entry()

    def create_journal_entry(self):
        """
        Create journal entry for payment:
        DR: Cash (1100)
        CR: Accounts Receivable (1200)
        """
        if self.journal_entry:
            return  # Already has journal entry

        # Get Cash account (1100)
        cash_account = Account.objects.filter(
            tenant=self.tenant,
            account_number='1100'
        ).first()

        # Get AR account (1200)
        ar_account = Account.objects.filter(
            tenant=self.tenant,
            account_number='1200'
        ).first()

        if not cash_account:
            raise ValidationError("Cash account (1100) not found for tenant")
        if not ar_account:
            raise ValidationError("AR account (1200) not found for tenant")

        # Create journal entry
        je = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_date=self.payment_date,
            description=f"Payment {self.payment_number} from {self.owner}",
            entry_type=JournalEntry.TYPE_PAYMENT,
            reference_id=self.id
        )

        # Debit line: Cash
        JournalEntryLine.objects.create(
            journal_entry=je,
            line_number=1,
            account=cash_account,
            debit_amount=self.amount,
            credit_amount=Decimal('0.00'),
            description=f"Cash received - {self.payment_method}"
        )

        # Credit line: AR
        JournalEntryLine.objects.create(
            journal_entry=je,
            line_number=2,
            account=ar_account,
            debit_amount=Decimal('0.00'),
            credit_amount=self.amount,
            description=f"AR reduction for payment {self.payment_number}"
        )

        # Link journal entry to payment (use queryset update to avoid recursion)
        Payment.objects.filter(pk=self.pk).update(journal_entry=je)
        self.journal_entry = je

        return je

    def get_applications(self):
        """Get all invoice applications for this payment"""
        return self.applications.all().select_related('invoice')

    @property
    def is_fully_applied(self):
        """Check if payment is fully applied to invoices"""
        return self.amount_unapplied == Decimal('0.00')


class PaymentApplication(models.Model):
    """
    Links a payment to a specific invoice.

    When a payment is received, it's applied to one or more invoices
    using FIFO logic (oldest invoices first).

    Business rules:
    - One payment can be applied to multiple invoices
    - One invoice can receive multiple payment applications
    - Sum of applications for a payment = payment.amount_applied
    - Applications are immutable (create reversal if needed)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this payment application"
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name='applications',
        help_text="Payment being applied"
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payment_applications',
        help_text="Invoice receiving the payment"
    )

    amount_applied = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount of payment applied to this invoice"
    )

    applied_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this application was created"
    )

    notes = models.TextField(
        blank=True,
        help_text="Notes about this application"
    )

    class Meta:
        db_table = 'payment_applications'
        ordering = ['payment', 'applied_at']
        indexes = [
            models.Index(fields=['payment', 'applied_at']),
            models.Index(fields=['invoice', 'applied_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount_applied__gt=0),
                name='payment_application_amount_positive'
            ),
        ]
        verbose_name = "Payment Application"
        verbose_name_plural = "Payment Applications"

    def __str__(self):
        return f"{self.payment.payment_number} → {self.invoice.invoice_number}: ${self.amount_applied}"

    def save(self, *args, **kwargs):
        """Validate application amounts"""
        # Ensure amount doesn't exceed invoice balance
        if self.amount_applied > self.invoice.amount_due:
            raise ValueError(
                f"Cannot apply ${self.amount_applied} to invoice {self.invoice.invoice_number} "
                f"with balance of ${self.invoice.amount_due}"
            )

        super().save(*args, **kwargs)

        # Update invoice amounts
        self.invoice.amount_paid += self.amount_applied
        self.invoice.amount_due = self.invoice.total_amount - self.invoice.amount_paid

        # Update invoice status
        if self.invoice.amount_due == Decimal('0.00'):
            self.invoice.status = Invoice.STATUS_PAID
        elif self.invoice.amount_due < self.invoice.total_amount:
            self.invoice.status = Invoice.STATUS_PARTIAL

        self.invoice.save()


class FundTransfer(models.Model):
    """
    Represents a transfer of funds between two funds (e.g., Operating → Reserve).

    Creates balanced journal entry transferring funds between different fund accounts.
    Common use case: Monthly reserve contributions from operating fund.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.PROTECT,
        related_name='fund_transfers',
        help_text="The HOA (tenant) this transfer belongs to"
    )

    transfer_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique transfer number (e.g., TR-00001)"
    )

    transfer_date = models.DateField(
        help_text="Date of the transfer"
    )

    from_fund = models.ForeignKey(
        'Fund',
        on_delete=models.PROTECT,
        related_name='transfers_out',
        help_text="Source fund (e.g., Operating)"
    )

    to_fund = models.ForeignKey(
        'Fund',
        on_delete=models.PROTECT,
        related_name='transfers_in',
        help_text="Destination fund (e.g., Reserve)"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transfer amount"
    )

    description = models.TextField(
        help_text="Description/memo for the transfer"
    )

    journal_entry = models.OneToOneField(
        'JournalEntry',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='fund_transfer',
        help_text="Journal entry recording this transfer"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this transfer"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fund_transfers'
        ordering = ['-transfer_date', '-transfer_number']
        indexes = [
            models.Index(fields=['tenant', 'transfer_date']),
            models.Index(fields=['from_fund', 'transfer_date']),
            models.Index(fields=['to_fund', 'transfer_date']),
        ]

    def clean(self):
        """Validate transfer"""
        if self.from_fund == self.to_fund:
            raise ValidationError("Cannot transfer funds to the same fund")

        if self.from_fund.tenant != self.to_fund.tenant:
            raise ValidationError("Cannot transfer funds between different tenants")

        if self.amount <= 0:
            raise ValidationError("Transfer amount must be positive")

    def __str__(self):
        return f"{self.transfer_number}: ${self.amount} from {self.from_fund.name} to {self.to_fund.name}"

    @transaction.atomic
    def create_journal_entry(self):
        """
        Create journal entry for fund transfer:

        DR: To Fund Cash (e.g., Reserve Cash - 6100)     $X,XXX
        CR: From Fund Cash (e.g., Operating Cash - 1100)  $X,XXX
        """
        # Get or create next entry number
        last_entry = JournalEntry.objects.filter(tenant=self.tenant).order_by('-entry_number').first()
        next_number = (last_entry.entry_number + 1) if last_entry else 1

        # Create journal entry
        entry = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_number=next_number,
            entry_date=self.transfer_date,
            description=f"Fund Transfer {self.transfer_number}: {self.description}",
            entry_type=JournalEntry.TYPE_TRANSFER,
            reference_id=str(self.id),
            posted_at=timezone.now()
        )

        # Get cash accounts for both funds
        from_cash_account = Account.objects.filter(
            tenant=self.tenant,
            fund=self.from_fund,
            account_number='1100'  # Operating Cash
        ).first()

        to_cash_account = Account.objects.filter(
            tenant=self.tenant,
            fund=self.to_fund,
            account_number='6100'  # Reserve Cash
        ).first()

        if not from_cash_account:
            raise ValueError(f"Cash account not found for {self.from_fund.name}")
        if not to_cash_account:
            raise ValueError(f"Cash account not found for {self.to_fund.name}")

        # Create journal entry lines
        # Line 1: DR: To Fund Cash (increases reserve cash)
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=1,
            account=to_cash_account,
            debit_amount=self.amount,
            credit_amount=Decimal('0.00'),
            description=f"Transfer from {self.from_fund.name}"
        )

        # Line 2: CR: From Fund Cash (decreases operating cash)
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_number=2,
            account=from_cash_account,
            debit_amount=Decimal('0.00'),
            credit_amount=self.amount,
            description=f"Transfer to {self.to_fund.name}"
        )

        # Link journal entry to transfer
        self.journal_entry = entry
        FundTransfer.objects.filter(pk=self.pk).update(journal_entry=entry)

        return entry


class UserTenantMembership(models.Model):
    """
    Represents a user's membership in a tenant with a specific role.

    Enables multi-tenant access control where users can belong to multiple tenants
    with different roles in each tenant.
    """

    # Role choices
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_BOARD = 'board'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_ADMIN, 'Tenant Admin'),
        (ROLE_MANAGER, 'Property Manager'),
        (ROLE_ACCOUNTANT, 'Accountant'),
        (ROLE_BOARD, 'Board Member'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_memberships',
        help_text="The user"
    )

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='user_memberships',
        help_text="The tenant"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="User's role in this tenant"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this membership is active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_tenant_memberships'
        unique_together = [['user', 'tenant']]
        indexes = [
            models.Index(fields=['user', 'tenant']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.get_role_display()})"

    @staticmethod
    def get_role_permissions(role):
        """Return list of permissions for a given role"""
        permissions = {
            UserTenantMembership.ROLE_SUPER_ADMIN: [
                'view_all_tenants', 'create_tenant', 'manage_tenant',
                'create_invoice', 'create_payment', 'create_transfer',
                'view_reports', 'manage_users', 'delete_records'
            ],
            UserTenantMembership.ROLE_ADMIN: [
                'create_invoice', 'create_payment', 'create_transfer',
                'view_reports', 'manage_users', 'send_emails',
                'configure_settings'
            ],
            UserTenantMembership.ROLE_MANAGER: [
                'create_invoice', 'create_payment', 'view_reports',
                'send_emails'
            ],
            UserTenantMembership.ROLE_ACCOUNTANT: [
                'view_reports', 'create_transfer', 'export_data'
            ],
            UserTenantMembership.ROLE_BOARD: [
                'view_reports'
            ],
        }
        return permissions.get(role, [])

    def has_permission(self, permission):
        """Check if this membership has a specific permission"""
        return permission in self.get_role_permissions(self.role)


class AuditLog(models.Model):
    """
    Audit log for tracking all important changes in the system.

    Provides compliance and security tracking for financial transactions.
    """

    # Action types
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_EXPORT = 'EXPORT'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_EXPORT, 'Export'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="The tenant this action belongs to"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text="User who performed the action"
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )

    model_name = models.CharField(
        max_length=100,
        help_text="Name of the model that was changed"
    )

    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the object that was changed"
    )

    changes = models.JSONField(
        default=dict,
        help_text="Before/after values of changed fields"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )

    user_agent = models.TextField(
        blank=True,
        default='',
        help_text="User agent string"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this action occurred"
    )

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.action} {self.model_name} at {self.timestamp}"

    @staticmethod
    def log(tenant, user, action, model_name, object_id=None, changes=None, request=None):
        """Create an audit log entry"""
        ip_address = None
        user_agent = ''

        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return AuditLog.objects.create(
            tenant=tenant,
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent
        )


class Budget(models.Model):
    """
    Annual operating budget for an HOA.
    
    Tracks budgeted amounts by account for fiscal planning and variance analysis.
    """
    
    # Status choices
    STATUS_DRAFT = 'DRAFT'
    STATUS_APPROVED = 'APPROVED'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_CLOSED = 'CLOSED'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CLOSED, 'Closed'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    
    name = models.CharField(
        max_length=200,
        help_text="Budget name (e.g., 'FY 2025 Operating Budget')"
    )
    
    fiscal_year = models.IntegerField(
        help_text="Fiscal year for this budget"
    )
    
    start_date = models.DateField(
        help_text="Budget period start date"
    )
    
    end_date = models.DateField(
        help_text="Budget period end date"
    )
    
    fund = models.ForeignKey(
        Fund,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific fund (null = all funds)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budgets'
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Budget notes and assumptions"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_budgets'
    )
    
    class Meta:
        db_table = 'budgets'
        ordering = ['-fiscal_year', '-start_date']
        indexes = [
            models.Index(fields=['tenant', 'fiscal_year']),
            models.Index(fields=['tenant', 'status']),
        ]
        unique_together = [['tenant', 'fiscal_year', 'fund']]
    
    def __str__(self):
        return f"{self.name} ({self.fiscal_year})"
    
    def get_total_budgeted(self):
        """Calculate total budgeted amount across all lines"""
        return self.lines.aggregate(
            total=models.Sum('budgeted_amount')
        )['total'] or Decimal('0.00')
    
    def get_variance_report(self, as_of_date=None):
        """
        Generate budget vs actual variance report.
        
        Args:
            as_of_date: Date to calculate actuals through (default: today)
        
        Returns:
            dict: Variance report with budget vs actual by account
        """
        from datetime import date
        from django.db.models import Sum, Q
        
        if as_of_date is None:
            as_of_date = date.today()
        
        # Ensure date is within budget period
        if as_of_date < self.start_date:
            as_of_date = self.start_date
        elif as_of_date > self.end_date:
            as_of_date = self.end_date
        
        lines_data = []
        total_budgeted = Decimal('0.00')
        total_actual = Decimal('0.00')
        
        for line in self.lines.select_related('account'):
            # Get actual expenses for this account in the budget period
            journal_lines = JournalEntryLine.objects.filter(
                journal_entry__tenant=self.tenant,
                journal_entry__entry_date__gte=self.start_date,
                journal_entry__entry_date__lte=as_of_date,
                journal_entry__posted_at__isnull=False,
                account=line.account
            )
            
            # For expense accounts, sum debits - credits
            # For revenue accounts, sum credits - debits
            actual_amount = Decimal('0.00')
            for jl in journal_lines:
                if line.account.account_type.code == AccountType.CODE_EXPENSE:
                    actual_amount += jl.debit_amount - jl.credit_amount
                elif line.account.account_type.code == AccountType.CODE_REVENUE:
                    actual_amount += jl.credit_amount - jl.debit_amount
            
            variance = line.budgeted_amount - actual_amount
            variance_pct = (variance / line.budgeted_amount * 100) if line.budgeted_amount != 0 else Decimal('0.00')
            
            # Determine status
            if abs(variance_pct) <= 5:
                status = 'on_track'
            elif variance > 0:
                status = 'favorable'  # Under budget
            else:
                status = 'unfavorable'  # Over budget
            
            lines_data.append({
                'account_number': line.account.account_number,
                'account_name': line.account.name,
                'budgeted': str(line.budgeted_amount),
                'actual': str(actual_amount),
                'variance': str(variance),
                'variance_pct': f"{variance_pct:.1f}",
                'status': status,
                'notes': line.notes
            })
            
            total_budgeted += line.budgeted_amount
            total_actual += actual_amount
        
        total_variance = total_budgeted - total_actual
        total_variance_pct = (total_variance / total_budgeted * 100) if total_budgeted != 0 else Decimal('0.00')
        
        return {
            'budget_id': str(self.id),
            'budget_name': self.name,
            'fiscal_year': self.fiscal_year,
            'period_start': self.start_date.isoformat(),
            'period_end': self.end_date.isoformat(),
            'as_of_date': as_of_date.isoformat(),
            'lines': lines_data,
            'totals': {
                'budgeted': str(total_budgeted),
                'actual': str(total_actual),
                'variance': str(total_variance),
                'variance_pct': f"{total_variance_pct:.1f}"
            }
        }


class BudgetLine(models.Model):
    """
    Individual line item within a budget.
    
    Links a budgeted amount to a specific account.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        help_text="Account this budget line applies to"
    )
    
    budgeted_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Budgeted amount for this account"
    )
    
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Notes and assumptions for this budget line"
    )
    
    class Meta:
        db_table = 'budget_lines'
        ordering = ['account__account_number']
        unique_together = [['budget', 'account']]
    
    def __str__(self):
        return f"{self.budget.name} - {self.account.account_number} ({self.budgeted_amount})"


class BankStatement(models.Model):
    """
    Imported bank statement for reconciliation.

    Each statement represents a period of bank activity that needs to be reconciled
    against the fund's journal entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='bank_statements'
    )

    fund = models.ForeignKey(
        Fund,
        on_delete=models.PROTECT,
        related_name='bank_statements',
        help_text="Fund this bank statement belongs to"
    )

    statement_date = models.DateField(
        help_text="Statement period ending date"
    )

    beginning_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Beginning balance from bank statement"
    )

    ending_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Ending balance from bank statement"
    )

    file_name = models.CharField(
        max_length=255,
        help_text="Original filename of uploaded statement"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_statements'
    )

    reconciled = models.BooleanField(
        default=False,
        help_text="True if reconciliation is complete"
    )

    reconciled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When reconciliation was completed"
    )

    notes = models.TextField(
        blank=True,
        default='',
        help_text="Reconciliation notes"
    )

    class Meta:
        db_table = 'bank_statements'
        ordering = ['-statement_date']
        unique_together = [['fund', 'statement_date']]

    def __str__(self):
        return f"{self.fund.name} - {self.statement_date}"

    @property
    def matched_count(self):
        """Count of matched transactions"""
        return self.transactions.filter(status='matched').count()

    @property
    def unmatched_count(self):
        """Count of unmatched transactions"""
        return self.transactions.filter(status='unmatched').count()

    @property
    def total_deposits(self):
        """Total deposits (positive amounts)"""
        return self.transactions.filter(
            amount__gt=0,
            status__in=['matched', 'created']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    @property
    def total_withdrawals(self):
        """Total withdrawals (negative amounts)"""
        return self.transactions.filter(
            amount__lt=0,
            status__in=['matched', 'created']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    @property
    def calculated_balance(self):
        """Calculate ending balance: beginning + deposits + withdrawals"""
        return self.beginning_balance + self.total_deposits + self.total_withdrawals


class BankTransaction(models.Model):
    """
    Individual transaction from bank statement.

    Each transaction needs to be matched to a journal entry or have a new entry created.
    """

    STATUS_UNMATCHED = 'unmatched'
    STATUS_MATCHED = 'matched'
    STATUS_IGNORED = 'ignored'
    STATUS_CREATED = 'created'

    STATUS_CHOICES = [
        (STATUS_UNMATCHED, 'Unmatched'),
        (STATUS_MATCHED, 'Matched to Entry'),
        (STATUS_IGNORED, 'Ignored'),
        (STATUS_CREATED, 'Entry Created'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='bank_transactions'
    )

    statement = models.ForeignKey(
        BankStatement,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_date = models.DateField(
        help_text="Date transaction occurred"
    )

    post_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date transaction posted to account"
    )

    description = models.TextField(
        help_text="Transaction description from bank"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Transaction amount (positive=deposit, negative=withdrawal)"
    )

    check_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Check number if applicable"
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Bank reference or confirmation number"
    )

    # Matching fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_UNMATCHED,
        db_index=True
    )

    matched_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_bank_transactions',
        help_text="Journal entry this transaction is matched to"
    )

    match_confidence = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Match confidence score (0-100)"
    )

    notes = models.TextField(
        blank=True,
        default='',
        help_text="Reconciliation notes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_transactions'
        ordering = ['transaction_date', '-amount']
        indexes = [
            models.Index(fields=['status', 'transaction_date']),
            models.Index(fields=['statement', 'status']),
        ]

    def __str__(self):
        return f"{self.transaction_date} - {self.description[:50]} ({self.amount})"

    @property
    def is_deposit(self):
        """True if transaction is a deposit (positive amount)"""
        return self.amount > 0

    @property
    def is_withdrawal(self):
        """True if transaction is a withdrawal (negative amount)"""
        return self.amount < 0


class ReconciliationRule(models.Model):
    """
    Saved rules for automatic transaction matching.

    Rules can be created based on patterns in transaction descriptions
    to automatically suggest or apply matches.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='reconciliation_rules'
    )

    name = models.CharField(
        max_length=255,
        help_text="Descriptive name for this rule"
    )

    description_pattern = models.CharField(
        max_length=255,
        help_text="Pattern to match in transaction description (case-insensitive)"
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        help_text="Account to use when creating entries from matched transactions"
    )

    fund = models.ForeignKey(
        Fund,
        on_delete=models.CASCADE,
        help_text="Fund to use when creating entries"
    )

    amount_min = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum amount to match (optional)"
    )

    amount_max = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum amount to match (optional)"
    )

    active = models.BooleanField(
        default=True,
        help_text="Whether this rule is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reconciliation_rules'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.description_pattern})"

    def matches(self, transaction: BankTransaction) -> bool:
        """
        Check if this rule matches a given transaction.
        """
        # Check description pattern (case-insensitive contains)
        if self.description_pattern.lower() not in transaction.description.lower():
            return False

        # Check amount range if specified
        if self.amount_min is not None and abs(transaction.amount) < self.amount_min:
            return False

        if self.amount_max is not None and abs(transaction.amount) > self.amount_max:
            return False

        return True


# ===========================
# Reserve Planning Models
# ===========================

class ReserveStudy(models.Model):
    """
    Reserve study for capital expenditure forecasting over 5-30 years.

    A reserve study identifies major components (roof, paving, etc.),
    estimates their replacement costs, and creates a funding plan.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='reserve_studies'
    )

    name = models.CharField(
        max_length=255,
        help_text="Study name (e.g., '2025 Reserve Study')"
    )

    study_date = models.DateField(
        default=date.today,
        help_text="Date the study was prepared"
    )

    horizon_years = models.IntegerField(
        default=20,
        validators=[MinValueValidator(5)],
        help_text="Planning horizon in years (typically 5-30)"
    )

    inflation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('3.50'),
        validators=[MinValueValidator(0)],
        help_text="Annual inflation rate as percentage (e.g., 3.50 for 3.5%)"
    )

    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.50'),
        validators=[MinValueValidator(0)],
        help_text="Expected interest rate on reserve funds (e.g., 1.50 for 1.5%)"
    )

    notes = models.TextField(
        blank=True,
        help_text="Study notes or methodology"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reserve_studies'
        ordering = ['-study_date', 'name']
        indexes = [
            models.Index(fields=['tenant', '-study_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.study_date.year})"

    def get_current_reserve_balance(self):
        """Get current balance from reserve fund"""
        try:
            reserve_fund = self.tenant.funds.get(fund_type=Fund.TYPE_RESERVE)
            # Calculate balance from journal entries
            from django.db.models import Sum, Q
            balance = JournalEntryLine.objects.filter(
                journal_entry__fund=reserve_fund
            ).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            return balance
        except Fund.DoesNotExist:
            return Decimal('0.00')


class ReserveComponent(models.Model):
    """
    Individual component in a reserve study (roof, pavement, pool equipment, etc.).

    Each component has a useful life, remaining life, and replacement cost.
    """

    # Component categories
    CATEGORY_ROOFING = 'ROOFING'
    CATEGORY_PAVING = 'PAVING'
    CATEGORY_PAINTING = 'PAINTING'
    CATEGORY_STRUCTURAL = 'STRUCTURAL'
    CATEGORY_HVAC = 'HVAC'
    CATEGORY_PLUMBING = 'PLUMBING'
    CATEGORY_ELECTRICAL = 'ELECTRICAL'
    CATEGORY_POOL = 'POOL'
    CATEGORY_LANDSCAPE = 'LANDSCAPE'
    CATEGORY_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CATEGORY_ROOFING, 'Roofing'),
        (CATEGORY_PAVING, 'Paving / Asphalt'),
        (CATEGORY_PAINTING, 'Painting / Coatings'),
        (CATEGORY_STRUCTURAL, 'Structural / Building'),
        (CATEGORY_HVAC, 'HVAC'),
        (CATEGORY_PLUMBING, 'Plumbing'),
        (CATEGORY_ELECTRICAL, 'Electrical'),
        (CATEGORY_POOL, 'Pool / Spa'),
        (CATEGORY_LANDSCAPE, 'Landscaping'),
        (CATEGORY_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    study = models.ForeignKey(
        ReserveStudy,
        on_delete=models.CASCADE,
        related_name='components'
    )

    name = models.CharField(
        max_length=255,
        help_text="Component name (e.g., 'Asphalt Parking Lot - Section A')"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description and location"
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_OTHER
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Quantity (e.g., square footage, linear feet, unit count)"
    )

    unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement (e.g., 'sq ft', 'linear ft', 'units')"
    )

    useful_life_years = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total useful life in years (e.g., roof = 20 years)"
    )

    remaining_life_years = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Remaining life from study date (e.g., 8 years left)"
    )

    current_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Replacement cost in today's dollars"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reserve_components'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['study', 'category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.remaining_life_years} years remaining)"

    def clean(self):
        """Validate that remaining life <= useful life"""
        if self.remaining_life_years > self.useful_life_years:
            raise ValidationError(
                "Remaining life cannot exceed useful life"
            )

    def get_replacement_year(self):
        """Calculate the year this component needs replacement"""
        return self.study.study_date.year + self.remaining_life_years

    def get_inflated_cost(self):
        """Calculate future cost with inflation"""
        inflation_rate = self.study.inflation_rate / Decimal('100.0')
        years = self.remaining_life_years
        future_value = self.current_cost * (
            (Decimal('1.0') + inflation_rate) ** years
        )
        return future_value.quantize(Decimal('0.01'))


class ReserveScenario(models.Model):
    """
    Funding scenario for a reserve study (baseline, aggressive, minimal, etc.).

    Each scenario has different contribution amounts and produces different
    funding projections.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    study = models.ForeignKey(
        ReserveStudy,
        on_delete=models.CASCADE,
        related_name='scenarios'
    )

    name = models.CharField(
        max_length=255,
        help_text="Scenario name (e.g., 'Baseline', 'Aggressive Funding')"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this scenario"
    )

    monthly_contribution = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly contribution to reserve fund"
    )

    one_time_contribution = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="One-time special assessment (optional)"
    )

    contribution_increase_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Annual % increase in contributions (e.g., 2.0 for 2%)"
    )

    is_baseline = models.BooleanField(
        default=False,
        help_text="Whether this is the recommended baseline scenario"
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reserve_scenarios'
        ordering = ['-is_baseline', 'name']
        indexes = [
            models.Index(fields=['study', '-is_baseline']),
        ]

    def __str__(self):
        return f"{self.name} (${self.monthly_contribution}/mo)"

    def calculate_projection(self):
        """
        Calculate multi-year funding projection for this scenario.

        Returns list of year-by-year projections showing:
        - Beginning balance
        - Contributions
        - Expenditures
        - Interest earned
        - Ending balance
        - Percent funded
        """
        projections = []
        current_balance = self.study.get_current_reserve_balance()

        # Get all components and their replacement years
        components = list(self.study.components.all())
        expenditures_by_year = {}
        for component in components:
            year = component.get_replacement_year()
            if year not in expenditures_by_year:
                expenditures_by_year[year] = Decimal('0.00')
            expenditures_by_year[year] += component.get_inflated_cost()

        # Calculate ideal fully funded balance
        total_future_cost = sum(
            comp.get_inflated_cost() for comp in components
        )

        # Project each year
        current_monthly = self.monthly_contribution
        increase_rate = self.contribution_increase_rate / Decimal('100.0')
        interest_rate = self.study.interest_rate / Decimal('100.0')

        for year_offset in range(self.study.horizon_years + 1):
            year = self.study.study_date.year + year_offset

            beginning_balance = current_balance

            # Add one-time contribution in first year
            contributions = current_monthly * 12
            if year_offset == 0:
                contributions += self.one_time_contribution

            # Subtract expenditures for this year
            expenditures = expenditures_by_year.get(year, Decimal('0.00'))

            # Calculate interest on average balance
            average_balance = beginning_balance + (contributions / 2) - (expenditures / 2)
            interest_earned = (average_balance * interest_rate).quantize(Decimal('0.01'))

            # Calculate ending balance
            ending_balance = beginning_balance + contributions - expenditures + interest_earned

            # Calculate percent funded
            if total_future_cost > 0:
                percent_funded = (ending_balance / total_future_cost * 100).quantize(Decimal('0.01'))
            else:
                percent_funded = Decimal('100.00')

            projections.append({
                'year': year,
                'beginning_balance': beginning_balance,
                'contributions': contributions,
                'expenditures': expenditures,
                'interest_earned': interest_earned,
                'ending_balance': ending_balance,
                'percent_funded': percent_funded,
            })

            # Update for next year
            current_balance = ending_balance
            current_monthly = current_monthly * (Decimal('1.0') + increase_rate)

        return projections


# ===========================
# Advanced Reporting Models
# ===========================

class CustomReport(models.Model):
    """
    User-defined custom reports with saved filters and columns.

    Allows users to create reusable report templates without developer involvement.
    """

    # Report types
    TYPE_GENERAL_LEDGER = 'GENERAL_LEDGER'
    TYPE_TRIAL_BALANCE = 'TRIAL_BALANCE'
    TYPE_INCOME_STATEMENT = 'INCOME_STATEMENT'
    TYPE_BALANCE_SHEET = 'BALANCE_SHEET'
    TYPE_CASH_FLOW = 'CASH_FLOW'
    TYPE_AR_AGING = 'AR_AGING'
    TYPE_OWNER_LEDGER = 'OWNER_LEDGER'
    TYPE_BUDGET_VARIANCE = 'BUDGET_VARIANCE'
    TYPE_RESERVE_FUNDING = 'RESERVE_FUNDING'

    TYPE_CHOICES = [
        (TYPE_GENERAL_LEDGER, 'General Ledger'),
        (TYPE_TRIAL_BALANCE, 'Trial Balance'),
        (TYPE_INCOME_STATEMENT, 'Income Statement'),
        (TYPE_BALANCE_SHEET, 'Balance Sheet'),
        (TYPE_CASH_FLOW, 'Cash Flow Statement'),
        (TYPE_AR_AGING, 'AR Aging Report'),
        (TYPE_OWNER_LEDGER, 'Owner Ledger'),
        (TYPE_BUDGET_VARIANCE, 'Budget Variance'),
        (TYPE_RESERVE_FUNDING, 'Reserve Funding Analysis'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='custom_reports'
    )

    created_by = models.CharField(
        max_length=255,
        blank=True,
        help_text="User who created this report (username or email)"
    )

    name = models.CharField(
        max_length=255,
        help_text="Report name (e.g., 'Monthly AR Aging by Fund')"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of what this report shows"
    )

    report_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Base report type"
    )

    columns = models.JSONField(
        default=list,
        help_text="List of columns to include: ['date', 'account', 'amount', etc.]"
    )

    filters = models.JSONField(
        default=dict,
        help_text="Report filters as JSON: {'fund': 'uuid', 'date_from': '2025-01-01', etc.}"
    )

    sort_by = models.JSONField(
        default=list,
        help_text="Sort order: [{'field': 'date', 'direction': 'desc'}]"
    )

    is_public = models.BooleanField(
        default=False,
        help_text="Whether this report is shared with all users in tenant"
    )

    is_favorite = models.BooleanField(
        default=False,
        help_text="User's favorite reports (shown at top)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_reports'
        ordering = ['-is_favorite', 'name']
        indexes = [
            models.Index(fields=['tenant', 'report_type']),
            models.Index(fields=['tenant', 'created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class ReportExecution(models.Model):
    """
    History of report executions with cached results.

    Stores execution metadata and optionally caches results for quick re-display.
    """

    # Status choices
    STATUS_PENDING = 'PENDING'
    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report = models.ForeignKey(
        CustomReport,
        on_delete=models.CASCADE,
        related_name='executions'
    )

    executed_by = models.CharField(
        max_length=255,
        blank=True,
        help_text="User who executed this report"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    row_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of rows returned"
    )

    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution time in milliseconds"
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed"
    )

    result_cache = models.JSONField(
        null=True,
        blank=True,
        help_text="Cached result data (optional, for fast re-display)"
    )

    parameters = models.JSONField(
        default=dict,
        help_text="Runtime parameters (date ranges, overrides, etc.)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'report_executions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['report', '-started_at']),
            models.Index(fields=['executed_by', '-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.report.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


# ===========================
# Delinquency & Collections Models
# ===========================

class LateFeeRule(models.Model):
    """
    Configurable late fee rules.

    Can be flat fee, percentage, or both. Can be one-time or recurring.
    """

    # Fee type
    TYPE_FLAT = 'FLAT'
    TYPE_PERCENTAGE = 'PERCENTAGE'
    TYPE_BOTH = 'BOTH'

    TYPE_CHOICES = [
        (TYPE_FLAT, 'Flat Fee'),
        (TYPE_PERCENTAGE, 'Percentage of Balance'),
        (TYPE_BOTH, 'Flat + Percentage'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='late_fee_rules'
    )

    name = models.CharField(
        max_length=255,
        help_text="Rule name (e.g., 'Standard Late Fee')"
    )

    grace_period_days = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Days after due date before late fee applies"
    )

    fee_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_FLAT
    )

    flat_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Flat late fee amount"
    )

    percentage_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Percentage of outstanding balance (e.g., 10.00 for 10%)"
    )

    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum late fee amount (optional cap)"
    )

    is_recurring = models.BooleanField(
        default=False,
        help_text="Apply late fee every month while delinquent"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rule is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'late_fee_rules'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    def calculate_fee(self, balance: Decimal) -> Decimal:
        """Calculate late fee for given balance"""
        if self.fee_type == self.TYPE_FLAT:
            fee = self.flat_amount
        elif self.fee_type == self.TYPE_PERCENTAGE:
            fee = balance * (self.percentage_rate / Decimal('100.0'))
        else:  # BOTH
            fee = self.flat_amount + (balance * (self.percentage_rate / Decimal('100.0')))

        # Apply cap if specified
        if self.max_amount is not None:
            fee = min(fee, self.max_amount)

        return fee.quantize(Decimal('0.01'))


class DelinquencyStatus(models.Model):
    """
    Per-owner delinquency status tracking.

    Tracks current balance, aging buckets, and collection stage.
    """

    # Collection stages
    STAGE_CURRENT = 'CURRENT'
    STAGE_0_30 = '0_30_DAYS'
    STAGE_31_60 = '31_60_DAYS'
    STAGE_61_90 = '61_90_DAYS'
    STAGE_90_PLUS = '90_PLUS_DAYS'
    STAGE_ATTORNEY = 'ATTORNEY_REFERRAL'
    STAGE_LIEN = 'LIEN_FILED'
    STAGE_FORECLOSURE = 'FORECLOSURE'

    STAGE_CHOICES = [
        (STAGE_CURRENT, 'Current'),
        (STAGE_0_30, '0-30 Days'),
        (STAGE_31_60, '31-60 Days'),
        (STAGE_61_90, '61-90 Days'),
        (STAGE_90_PLUS, '90+ Days'),
        (STAGE_ATTORNEY, 'Attorney Referral'),
        (STAGE_LIEN, 'Lien Filed'),
        (STAGE_FORECLOSURE, 'Foreclosure'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.OneToOneField(
        Owner,
        on_delete=models.CASCADE,
        related_name='delinquency_status'
    )

    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total outstanding balance"
    )

    balance_0_30 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Balance 0-30 days old"
    )

    balance_31_60 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Balance 31-60 days old"
    )

    balance_61_90 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Balance 61-90 days old"
    )

    balance_90_plus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Balance 90+ days old"
    )

    collection_stage = models.CharField(
        max_length=30,
        choices=STAGE_CHOICES,
        default=STAGE_CURRENT
    )

    days_delinquent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Days since first delinquency"
    )

    last_payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last payment received"
    )

    last_notice_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last collection notice sent"
    )

    is_payment_plan = models.BooleanField(
        default=False,
        help_text="Owner is on approved payment plan"
    )

    notes = models.TextField(
        blank=True,
        help_text="Internal notes about collection status"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delinquency_status'
        verbose_name_plural = 'Delinquency statuses'

    def __str__(self):
        return f"{self.owner.full_name} - {self.get_collection_stage_display()} (${self.current_balance})"

    @property
    def is_delinquent(self):
        """Check if owner is currently delinquent"""
        return self.current_balance > 0


class CollectionNotice(models.Model):
    """
    Collection notices sent to owners.

    Tracks email and certified mail with delivery confirmation.
    """

    # Notice types
    TYPE_FIRST_NOTICE = 'FIRST_NOTICE'
    TYPE_SECOND_NOTICE = 'SECOND_NOTICE'
    TYPE_FINAL_NOTICE = 'FINAL_NOTICE'
    TYPE_PRE_LIEN = 'PRE_LIEN'
    TYPE_LIEN_FILED = 'LIEN_FILED'
    TYPE_ATTORNEY_REFERRAL = 'ATTORNEY_REFERRAL'

    TYPE_CHOICES = [
        (TYPE_FIRST_NOTICE, 'First Notice'),
        (TYPE_SECOND_NOTICE, 'Second Notice'),
        (TYPE_FINAL_NOTICE, 'Final Notice'),
        (TYPE_PRE_LIEN, 'Pre-Lien Notice'),
        (TYPE_LIEN_FILED, 'Lien Filed Notice'),
        (TYPE_ATTORNEY_REFERRAL, 'Attorney Referral'),
    ]

    # Delivery methods
    METHOD_EMAIL = 'EMAIL'
    METHOD_CERTIFIED_MAIL = 'CERTIFIED_MAIL'
    METHOD_REGULAR_MAIL = 'REGULAR_MAIL'

    METHOD_CHOICES = [
        (METHOD_EMAIL, 'Email'),
        (METHOD_CERTIFIED_MAIL, 'Certified Mail'),
        (METHOD_REGULAR_MAIL, 'Regular Mail'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name='collection_notices'
    )

    notice_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    delivery_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES
    )

    sent_date = models.DateField(
        help_text="Date notice was sent"
    )

    balance_at_notice = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Outstanding balance when notice was sent"
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="USPS tracking number for certified mail"
    )

    delivered_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date notice was delivered (for certified mail)"
    )

    returned_undeliverable = models.BooleanField(
        default=False,
        help_text="Notice was returned as undeliverable"
    )

    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this notice"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collection_notices'
        ordering = ['-sent_date']
        indexes = [
            models.Index(fields=['owner', '-sent_date']),
        ]

    def __str__(self):
        return f"{self.get_notice_type_display()} - {self.owner.full_name} ({self.sent_date})"


class CollectionAction(models.Model):
    """
    Major collection actions (attorney referral, lien, foreclosure).

    Requires board approval and tracks legal proceedings.
    """

    # Action types
    ACTION_ATTORNEY_REFERRAL = 'ATTORNEY_REFERRAL'
    ACTION_LIEN_FILED = 'LIEN_FILED'
    ACTION_FORECLOSURE = 'FORECLOSURE'
    ACTION_PAYMENT_PLAN = 'PAYMENT_PLAN'
    ACTION_WRITE_OFF = 'WRITE_OFF'

    ACTION_CHOICES = [
        (ACTION_ATTORNEY_REFERRAL, 'Attorney Referral'),
        (ACTION_LIEN_FILED, 'Lien Filed'),
        (ACTION_FORECLOSURE, 'Foreclosure Initiated'),
        (ACTION_PAYMENT_PLAN, 'Payment Plan Approved'),
        (ACTION_WRITE_OFF, 'Bad Debt Write-Off'),
    ]

    # Status
    STATUS_PENDING_APPROVAL = 'PENDING_APPROVAL'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_PENDING_APPROVAL, 'Pending Board Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name='collection_actions'
    )

    action_type = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_APPROVAL
    )

    requested_date = models.DateField(
        help_text="Date action was requested"
    )

    approved_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date approved by board"
    )

    approved_by = models.CharField(
        max_length=255,
        blank=True,
        help_text="Board member who approved"
    )

    completed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date action was completed"
    )

    balance_at_action = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Outstanding balance when action was taken"
    )

    attorney_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Attorney or firm handling case"
    )

    case_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Court case number (for liens/foreclosure)"
    )

    notes = models.TextField(
        blank=True,
        help_text="Details about this action"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collection_actions'
        ordering = ['-requested_date']
        indexes = [
            models.Index(fields=['owner', '-requested_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.owner.full_name} ({self.status})"


# ===========================
# Auto-Matching Engine Models
# ===========================

class AutoMatchRule(models.Model):
    """
    Learned matching patterns for automated transaction matching.

    Rules are created from successful manual matches and improve over time.
    """

    # Rule types
    TYPE_EXACT = 'EXACT'
    TYPE_FUZZY = 'FUZZY'
    TYPE_PATTERN = 'PATTERN'
    TYPE_REFERENCE = 'REFERENCE'
    TYPE_ML = 'ML'

    TYPE_CHOICES = [
        (TYPE_EXACT, 'Exact Match'),
        (TYPE_FUZZY, 'Fuzzy Match'),
        (TYPE_PATTERN, 'Pattern Match'),
        (TYPE_REFERENCE, 'Reference Match'),
        (TYPE_ML, 'ML-Based Match'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='auto_match_rules'
    )

    name = models.CharField(
        max_length=255,
        help_text="Rule name (auto-generated or custom)"
    )

    rule_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    pattern = models.JSONField(
        help_text="Rule pattern as JSON (amount range, date tolerance, description regex, etc.)"
    )

    target_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Target account for matched transactions"
    )

    confidence_score = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MinValueValidator(100)],
        help_text="Confidence score (0-100)"
    )

    match_count = models.IntegerField(
        default=0,
        help_text="Number of successful matches using this rule"
    )

    accuracy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Accuracy rate as percentage (verified matches / total matches)"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rule is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auto_match_rules'
        ordering = ['-confidence_score', '-match_count']
        indexes = [
            models.Index(fields=['tenant', '-confidence_score']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.confidence_score}% confidence)"


class MatchResult(models.Model):
    """
    Cached matching results for bank transactions.

    Stores potential matches with confidence scores for review.
    """

    # Match status
    STATUS_SUGGESTED = 'SUGGESTED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_AUTO_MATCHED = 'AUTO_MATCHED'

    STATUS_CHOICES = [
        (STATUS_SUGGESTED, 'Suggested'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_AUTO_MATCHED, 'Auto-Matched'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    bank_transaction = models.ForeignKey(
        BankTransaction,
        on_delete=models.CASCADE,
        related_name='match_results'
    )

    matched_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='match_results'
    )

    rule_used = models.ForeignKey(
        AutoMatchRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Rule that generated this match"
    )

    confidence_score = models.IntegerField(
        validators=[MinValueValidator(0), MinValueValidator(100)],
        help_text="Match confidence (0-100)"
    )

    match_explanation = models.TextField(
        help_text="Explanation of why this match was suggested"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUGGESTED
    )

    reviewed_by = models.CharField(
        max_length=255,
        blank=True,
        help_text="User who reviewed this match"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'match_results'
        ordering = ['-confidence_score', '-created_at']
        indexes = [
            models.Index(fields=['bank_transaction', '-confidence_score']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Match for {self.bank_transaction} ({self.confidence_score}%)"


class MatchStatistics(models.Model):
    """
    Track overall matching performance metrics.

    Aggregated daily stats for monitoring and improvement.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='match_statistics'
    )

    date = models.DateField(
        help_text="Date for these statistics"
    )

    total_transactions = models.IntegerField(
        default=0,
        help_text="Total bank transactions processed"
    )

    auto_matched = models.IntegerField(
        default=0,
        help_text="Transactions auto-matched with high confidence"
    )

    manually_matched = models.IntegerField(
        default=0,
        help_text="Transactions matched manually"
    )

    unmatched = models.IntegerField(
        default=0,
        help_text="Transactions remaining unmatched"
    )

    auto_match_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Auto-match rate as percentage"
    )

    average_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Average confidence score of matches"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'match_statistics'
        ordering = ['-date']
        unique_together = [['tenant', 'date']]
        indexes = [
            models.Index(fields=['tenant', '-date']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.date} ({self.auto_match_rate}% auto-matched)"


# ===========================
# Violation Tracking Models
# ===========================

class Violation(models.Model):
    """
    HOA violation tracking with photo evidence.

    Tracks violations from report to resolution.
    """

    # Violation statuses
    STATUS_REPORTED = 'REPORTED'
    STATUS_NOTICE_SENT = 'NOTICE_SENT'
    STATUS_PENDING_CURE = 'PENDING_CURE'
    STATUS_CURED = 'CURED'
    STATUS_HEARING_SCHEDULED = 'HEARING_SCHEDULED'
    STATUS_FINED = 'FINED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_REPORTED, 'Reported'),
        (STATUS_NOTICE_SENT, 'Notice Sent'),
        (STATUS_PENDING_CURE, 'Pending Cure'),
        (STATUS_CURED, 'Cured'),
        (STATUS_HEARING_SCHEDULED, 'Hearing Scheduled'),
        (STATUS_FINED, 'Fined'),
        (STATUS_CLOSED, 'Closed'),
    ]

    # Severity levels
    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_CRITICAL = 'CRITICAL'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='violations'
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name='violations'
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='violations'
    )

    violation_type = models.CharField(
        max_length=255,
        help_text="Type of violation (e.g., 'Unpainted Fence', 'Overgrown Lawn')"
    )

    description = models.TextField(
        help_text="Detailed description of violation"
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Specific location on property"
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_REPORTED
    )

    reported_date = models.DateField(
        help_text="Date violation was reported"
    )

    reported_by = models.CharField(
        max_length=255,
        help_text="Who reported the violation"
    )

    cure_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Deadline to cure violation"
    )

    cured_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date violation was cured"
    )

    fine_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fine amount if assessed"
    )

    fine_paid = models.BooleanField(
        default=False,
        help_text="Whether fine has been paid"
    )

    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this violation"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'violations'
        ordering = ['-reported_date']
        indexes = [
            models.Index(fields=['tenant', '-reported_date']),
            models.Index(fields=['owner', '-reported_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.violation_type} - {self.owner.full_name} ({self.status})"


class ViolationPhoto(models.Model):
    """
    Photo evidence for violations.

    Stores URLs/paths to uploaded photos.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    violation = models.ForeignKey(
        Violation,
        on_delete=models.CASCADE,
        related_name='photos'
    )

    photo_url = models.URLField(
        max_length=500,
        help_text="URL to photo (S3, CloudFlare, etc.)"
    )

    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Photo caption or description"
    )

    taken_date = models.DateField(
        help_text="Date photo was taken"
    )

    uploaded_by = models.CharField(
        max_length=255,
        help_text="Who uploaded this photo"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'violation_photos'
        ordering = ['taken_date']

    def __str__(self):
        return f"Photo for {self.violation.violation_type}"


class ViolationNotice(models.Model):
    """
    Notices sent to owners about violations.

    Tracks notice delivery and responses.
    """

    # Notice types
    TYPE_FIRST_NOTICE = 'FIRST_NOTICE'
    TYPE_SECOND_NOTICE = 'SECOND_NOTICE'
    TYPE_FINAL_NOTICE = 'FINAL_NOTICE'
    TYPE_HEARING_NOTICE = 'HEARING_NOTICE'
    TYPE_FINE_NOTICE = 'FINE_NOTICE'

    TYPE_CHOICES = [
        (TYPE_FIRST_NOTICE, 'First Notice'),
        (TYPE_SECOND_NOTICE, 'Second Notice'),
        (TYPE_FINAL_NOTICE, 'Final Notice'),
        (TYPE_HEARING_NOTICE, 'Hearing Notice'),
        (TYPE_FINE_NOTICE, 'Fine Notice'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    violation = models.ForeignKey(
        Violation,
        on_delete=models.CASCADE,
        related_name='notices'
    )

    notice_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    sent_date = models.DateField(
        help_text="Date notice was sent"
    )

    delivery_method = models.CharField(
        max_length=20,
        choices=CollectionNotice.METHOD_CHOICES,
        default=CollectionNotice.METHOD_EMAIL
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tracking number for certified mail"
    )

    delivered_date = models.DateField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'violation_notices'
        ordering = ['-sent_date']

    def __str__(self):
        return f"{self.get_notice_type_display()} for {self.violation}"


class ViolationHearing(models.Model):
    """
    Hearing scheduling and outcomes for violations.

    Board hearings for contested violations.
    """

    # Hearing outcomes
    OUTCOME_PENDING = 'PENDING'
    OUTCOME_UPHELD = 'UPHELD'
    OUTCOME_OVERTURNED = 'OVERTURNED'
    OUTCOME_MODIFIED = 'MODIFIED'
    OUTCOME_POSTPONED = 'POSTPONED'

    OUTCOME_CHOICES = [
        (OUTCOME_PENDING, 'Pending'),
        (OUTCOME_UPHELD, 'Upheld'),
        (OUTCOME_OVERTURNED, 'Overturned'),
        (OUTCOME_MODIFIED, 'Modified'),
        (OUTCOME_POSTPONED, 'Postponed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    violation = models.ForeignKey(
        Violation,
        on_delete=models.CASCADE,
        related_name='hearings'
    )

    scheduled_date = models.DateField(
        help_text="Date hearing is scheduled"
    )

    scheduled_time = models.TimeField(
        help_text="Time of hearing"
    )

    location = models.CharField(
        max_length=255,
        help_text="Hearing location or video conference link"
    )

    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        default=OUTCOME_PENDING
    )

    outcome_notes = models.TextField(
        blank=True,
        help_text="Details of hearing outcome"
    )

    fine_assessed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fine amount assessed at hearing"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'violation_hearings'
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"Hearing for {self.violation} on {self.scheduled_date}"


# ===========================
# Board Packet Generation Models
# ===========================

class BoardPacketTemplate(models.Model):
    """
    Reusable templates for board packet generation.

    Defines which sections to include and their order.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='packet_templates'
    )

    name = models.CharField(
        max_length=255,
        help_text="Template name (e.g., 'Monthly Board Meeting')"
    )

    description = models.TextField(
        blank=True,
        help_text="Template description"
    )

    sections = models.JSONField(
        default=list,
        help_text="List of sections to include: ['agenda', 'financials', 'ar_aging', etc.]"
    )

    section_order = models.JSONField(
        default=list,
        help_text="Order of sections in packet"
    )

    include_cover_page = models.BooleanField(
        default=True,
        help_text="Include auto-generated cover page"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Default template for this tenant"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'board_packet_templates'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class BoardPacket(models.Model):
    """
    Generated board packets with PDF.

    Archives of generated packets for each board meeting.
    """

    # Status
    STATUS_GENERATING = 'GENERATING'
    STATUS_READY = 'READY'
    STATUS_FAILED = 'FAILED'
    STATUS_SENT = 'SENT'

    STATUS_CHOICES = [
        (STATUS_GENERATING, 'Generating'),
        (STATUS_READY, 'Ready'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_SENT, 'Sent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='board_packets'
    )

    template = models.ForeignKey(
        BoardPacketTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packets'
    )

    title = models.CharField(
        max_length=255,
        help_text="Packet title (e.g., 'November 2025 Board Meeting')"
    )

    meeting_date = models.DateField(
        help_text="Date of board meeting"
    )

    generated_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When packet was generated"
    )

    generated_by = models.CharField(
        max_length=255,
        help_text="User who generated the packet"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_GENERATING
    )

    pdf_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL to generated PDF (S3, CloudFlare, etc.)"
    )

    pdf_size_bytes = models.IntegerField(
        null=True,
        blank=True,
        help_text="PDF file size in bytes"
    )

    page_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of pages in PDF"
    )

    generation_time_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken to generate PDF"
    )

    sent_to = models.JSONField(
        default=list,
        help_text="List of email addresses packet was sent to"
    )

    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When packet was emailed to board"
    )

    notes = models.TextField(
        blank=True,
        help_text="Notes about this packet"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'board_packets'
        ordering = ['-meeting_date']
        indexes = [
            models.Index(fields=['tenant', '-meeting_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.meeting_date}"


class PacketSection(models.Model):
    """
    Individual sections within a board packet.

    Tracks which reports/documents are included.
    """

    # Section types
    TYPE_COVER_PAGE = 'COVER_PAGE'
    TYPE_AGENDA = 'AGENDA'
    TYPE_MINUTES = 'MINUTES'
    TYPE_FINANCIAL_SUMMARY = 'FINANCIAL_SUMMARY'
    TYPE_TRIAL_BALANCE = 'TRIAL_BALANCE'
    TYPE_CASH_FLOW = 'CASH_FLOW'
    TYPE_AR_AGING = 'AR_AGING'
    TYPE_DELINQUENCY_REPORT = 'DELINQUENCY_REPORT'
    TYPE_VIOLATION_SUMMARY = 'VIOLATION_SUMMARY'
    TYPE_RESERVE_SUMMARY = 'RESERVE_SUMMARY'
    TYPE_BUDGET_VARIANCE = 'BUDGET_VARIANCE'
    TYPE_CUSTOM_REPORT = 'CUSTOM_REPORT'
    TYPE_ATTACHMENT = 'ATTACHMENT'

    TYPE_CHOICES = [
        (TYPE_COVER_PAGE, 'Cover Page'),
        (TYPE_AGENDA, 'Meeting Agenda'),
        (TYPE_MINUTES, 'Previous Minutes'),
        (TYPE_FINANCIAL_SUMMARY, 'Financial Summary'),
        (TYPE_TRIAL_BALANCE, 'Trial Balance'),
        (TYPE_CASH_FLOW, 'Cash Flow Statement'),
        (TYPE_AR_AGING, 'AR Aging Report'),
        (TYPE_DELINQUENCY_REPORT, 'Delinquency Report'),
        (TYPE_VIOLATION_SUMMARY, 'Violation Summary'),
        (TYPE_RESERVE_SUMMARY, 'Reserve Study Summary'),
        (TYPE_BUDGET_VARIANCE, 'Budget Variance'),
        (TYPE_CUSTOM_REPORT, 'Custom Report'),
        (TYPE_ATTACHMENT, 'Attachment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    packet = models.ForeignKey(
        BoardPacket,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    section_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    title = models.CharField(
        max_length=255,
        help_text="Section title/heading"
    )

    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )

    content_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL to section content (PDF, image, etc.)"
    )

    content_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Embedded content data (for reports generated inline)"
    )

    page_start = models.IntegerField(
        null=True,
        blank=True,
        help_text="Starting page number in final PDF"
    )

    page_end = models.IntegerField(
        null=True,
        blank=True,
        help_text="Ending page number in final PDF"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'packet_sections'
        ordering = ['packet', 'order']
        indexes = [
            models.Index(fields=['packet', 'order']),
        ]

    def __str__(self):
        return f"{self.title} ({self.packet.title})"


# ============================================================================
# PHASE 3: OPERATIONAL FEATURES - Additional Models
# ============================================================================

# ----------------------------------------------------------------------------
# Sprint 15: Violation Tracking - Additional Models
# ----------------------------------------------------------------------------

class ViolationType(models.Model):
    """
    Types/categories of violations (landscaping, parking, noise, etc.).

    Defines violation categories with fine schedules.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='violation_types'
    )

    code = models.CharField(
        max_length=20,
        help_text="Short code (e.g., 'LAND-001', 'PARK-002')"
    )

    name = models.CharField(
        max_length=100,
        help_text="Violation name (e.g., 'Overgrown Lawn')"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of violation"
    )

    category = models.CharField(
        max_length=50,
        help_text="Category (Landscaping, Parking, Noise, Structural, etc.)"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is this violation type active?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'violation_types'
        unique_together = [['tenant', 'code']]
        ordering = ['category', 'code']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.code}: {self.name}"


class FineSchedule(models.Model):
    """
    Fine escalation schedule for violation types.

    Defines steps and fines for each violation type.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    violation_type = models.ForeignKey(
        ViolationType,
        on_delete=models.CASCADE,
        related_name='fine_schedule_steps'
    )

    step_number = models.IntegerField(
        help_text="Step in escalation (1=courtesy, 2=warning, 3=fine, etc.)"
    )

    step_name = models.CharField(
        max_length=50,
        help_text="Step name (Courtesy, Warning, Fine, Continued, Legal)"
    )

    days_after_previous = models.IntegerField(
        default=7,
        help_text="Days after previous step"
    )

    fine_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fine amount for this step"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this step"
    )

    requires_board_approval = models.BooleanField(
        default=False,
        help_text="Does this step require board approval?"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fine_schedules'
        unique_together = [['violation_type', 'step_number']]
        ordering = ['violation_type', 'step_number']

    def __str__(self):
        return f"{self.violation_type.code} - Step {self.step_number}: {self.step_name}"


class ViolationEscalation(models.Model):
    """
    Tracks escalation steps for violations.

    Records each step in the violation escalation process.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    violation = models.ForeignKey(
        Violation,
        on_delete=models.CASCADE,
        related_name='escalations'
    )

    step_number = models.IntegerField(
        help_text="Escalation step number"
    )

    step_name = models.CharField(
        max_length=50,
        help_text="Step name"
    )

    escalated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this step was triggered"
    )

    fine_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fine amount for this step"
    )

    notice_sent = models.BooleanField(
        default=False,
        help_text="Was notice sent?"
    )

    notice_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notice was sent"
    )

    notice_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Email, Certified Mail, Hand Delivered"
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="USPS tracking number for certified mail"
    )

    notes = models.TextField(
        blank=True,
        help_text="Notes about this escalation"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='violation_escalations_created'
    )

    class Meta:
        db_table = 'violation_escalations'
        ordering = ['violation', 'step_number']
        indexes = [
            models.Index(fields=['violation', 'step_number']),
            models.Index(fields=['escalated_at']),
        ]

    def __str__(self):
        return f"Violation {self.violation.id} - Step {self.step_number}"


class ViolationFine(models.Model):
    """
    Fines posted for violations.

    Links violations to invoices and journal entries.
    """

    STATUS_PENDING = 'PENDING'
    STATUS_POSTED = 'POSTED'
    STATUS_PAID = 'PAID'
    STATUS_WAIVED = 'WAIVED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_POSTED, 'Posted'),
        (STATUS_PAID, 'Paid'),
        (STATUS_WAIVED, 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    violation = models.ForeignKey(
        Violation,
        on_delete=models.PROTECT,
        related_name='fines'
    )

    escalation = models.ForeignKey(
        ViolationEscalation,
        on_delete=models.PROTECT,
        related_name='fines',
        null=True,
        blank=True
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='violation_fines',
        null=True,
        blank=True,
        help_text="Link to invoice (AR)"
    )

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name='violation_fines',
        null=True,
        blank=True,
        help_text="Link to GL entry"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Fine amount"
    )

    posted_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date fine was posted to ledger"
    )

    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date fine was paid"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    waived_reason = models.TextField(
        blank=True,
        help_text="Reason fine was waived"
    )

    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='violation_fines_waived',
        null=True,
        blank=True
    )

    waived_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'violation_fines'
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['violation', 'status']),
            models.Index(fields=['posted_date']),
        ]

    def __str__(self):
        return f"Fine ${self.amount} for Violation {self.violation.id}"


# ----------------------------------------------------------------------------
# Sprint 16: ARC (Architectural Review Committee) Workflow
# ----------------------------------------------------------------------------

class ARCRequestType(models.Model):
    """
    Types of architectural modification requests.

    Defines request categories (paint, fence, landscaping, etc.).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='arc_request_types'
    )

    code = models.CharField(
        max_length=20,
        help_text="Short code (e.g., 'PAINT', 'FENCE')"
    )

    name = models.CharField(
        max_length=100,
        help_text="Request type name"
    )

    description = models.TextField(
        blank=True,
        help_text="Description and guidelines"
    )

    requires_plans = models.BooleanField(
        default=False,
        help_text="Requires architectural plans?"
    )

    requires_contractor = models.BooleanField(
        default=False,
        help_text="Requires contractor information?"
    )

    typical_review_days = models.IntegerField(
        default=30,
        help_text="Typical review time in days"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'arc_request_types'
        unique_together = [['tenant', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code}: {self.name}"


class ARCRequest(models.Model):
    """
    Architectural modification requests from owners.

    Tracks requests from submission through completion.
    """

    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_DENIED = 'DENIED'
    STATUS_APPROVED_WITH_CONDITIONS = 'APPROVED_WITH_CONDITIONS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DENIED, 'Denied'),
        (STATUS_APPROVED_WITH_CONDITIONS, 'Approved with Conditions'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='arc_requests'
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='arc_requests'
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.PROTECT,
        related_name='arc_requests'
    )

    request_type = models.ForeignKey(
        ARCRequestType,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    title = models.CharField(
        max_length=255,
        help_text="Brief title"
    )

    description = models.TextField(
        help_text="Detailed proposal"
    )

    requested_start_date = models.DateField(
        null=True,
        blank=True
    )

    estimated_completion_date = models.DateField(
        null=True,
        blank=True
    )

    contractor_name = models.CharField(
        max_length=100,
        blank=True
    )

    contractor_license = models.CharField(
        max_length=50,
        blank=True
    )

    contractor_phone = models.CharField(
        max_length=20,
        blank=True
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='arc_requests_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'arc_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['unit']),
            models.Index(fields=['owner']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.unit.address}"


class ARCDocument(models.Model):
    """
    Documents attached to ARC requests.

    Plans, specs, photos, contracts, etc.
    """

    DOCUMENT_TYPE_PLAN = 'PLAN'
    DOCUMENT_TYPE_SPEC = 'SPEC'
    DOCUMENT_TYPE_PHOTO = 'PHOTO'
    DOCUMENT_TYPE_CONTRACT = 'CONTRACT'
    DOCUMENT_TYPE_OTHER = 'OTHER'

    DOCUMENT_TYPE_CHOICES = [
        (DOCUMENT_TYPE_PLAN, 'Plan'),
        (DOCUMENT_TYPE_SPEC, 'Specification'),
        (DOCUMENT_TYPE_PHOTO, 'Photo'),
        (DOCUMENT_TYPE_CONTRACT, 'Contract'),
        (DOCUMENT_TYPE_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey(
        ARCRequest,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES
    )

    file_url = models.URLField(
        max_length=500,
        help_text="S3 path or local storage path"
    )

    file_name = models.CharField(
        max_length=255
    )

    file_size = models.IntegerField(
        help_text="File size in bytes"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='arc_documents_uploaded'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'arc_documents'
        ordering = ['request', 'uploaded_at']
        indexes = [
            models.Index(fields=['request']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.document_type})"


class ARCReview(models.Model):
    """
    Committee member reviews for ARC requests.

    Tracks individual review decisions.
    """

    DECISION_APPROVE = 'APPROVE'
    DECISION_DENY = 'DENY'
    DECISION_REQUEST_CHANGES = 'REQUEST_CHANGES'
    DECISION_ABSTAIN = 'ABSTAIN'

    DECISION_CHOICES = [
        (DECISION_APPROVE, 'Approve'),
        (DECISION_DENY, 'Deny'),
        (DECISION_REQUEST_CHANGES, 'Request Changes'),
        (DECISION_ABSTAIN, 'Abstain'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey(
        ARCRequest,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='arc_reviews'
    )

    review_date = models.DateTimeField(auto_now_add=True)

    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES
    )

    comments = models.TextField(
        blank=True,
        help_text="Review comments"
    )

    conditions = models.TextField(
        blank=True,
        help_text="Conditions for approval"
    )

    class Meta:
        db_table = 'arc_reviews'
        ordering = ['request', 'review_date']
        indexes = [
            models.Index(fields=['request']),
            models.Index(fields=['reviewer']),
        ]

    def __str__(self):
        return f"Review by {self.reviewer.username} - {self.decision}"


class ARCApproval(models.Model):
    """
    Final approval for ARC requests.

    Records board decision and conditions.
    """

    DECISION_APPROVED = 'APPROVED'
    DECISION_DENIED = 'DENIED'
    DECISION_APPROVED_WITH_CONDITIONS = 'APPROVED_WITH_CONDITIONS'

    DECISION_CHOICES = [
        (DECISION_APPROVED, 'Approved'),
        (DECISION_DENIED, 'Denied'),
        (DECISION_APPROVED_WITH_CONDITIONS, 'Approved with Conditions'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.OneToOneField(
        ARCRequest,
        on_delete=models.CASCADE,
        related_name='approval'
    )

    final_decision = models.CharField(
        max_length=30,
        choices=DECISION_CHOICES
    )

    decision_date = models.DateField()

    conditions = models.TextField(
        blank=True,
        help_text="Approval conditions"
    )

    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Approval expires if not started"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='arc_approvals'
    )

    board_resolution = models.CharField(
        max_length=50,
        blank=True,
        help_text="Board resolution number"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'arc_approvals'
        indexes = [
            models.Index(fields=['request']),
            models.Index(fields=['decision_date']),
        ]

    def __str__(self):
        return f"{self.final_decision} - {self.request.title}"


class ARCCompletion(models.Model):
    """
    Completion verification for ARC requests.

    Inspector verifies work matches approval.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.OneToOneField(
        ARCRequest,
        on_delete=models.CASCADE,
        related_name='completion'
    )

    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='arc_completions_inspected'
    )

    inspection_date = models.DateField()

    complies_with_approval = models.BooleanField(
        help_text="Does work comply with approval?"
    )

    inspector_notes = models.TextField(
        blank=True
    )

    photo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Completion photo"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'arc_completions'
        indexes = [
            models.Index(fields=['request']),
            models.Index(fields=['inspection_date']),
        ]

    def __str__(self):
        return f"Completion for {self.request.title}"


# ----------------------------------------------------------------------------
# Sprint 17: Work Order System with Vendor Management
# ----------------------------------------------------------------------------

class WorkOrderCategory(models.Model):
    """
    Work order categories (landscaping, pool, HVAC, etc.).

    Maps categories to GL accounts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='work_order_categories'
    )

    code = models.CharField(
        max_length=20,
        help_text="Short code (e.g., 'LAND', 'POOL')"
    )

    name = models.CharField(
        max_length=100,
        help_text="Category name"
    )

    description = models.TextField(
        blank=True
    )

    default_gl_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='work_order_categories',
        null=True,
        blank=True,
        help_text="Default GL expense account"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_order_categories'
        unique_together = [['tenant', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code}: {self.name}"


class Vendor(models.Model):
    """
    Vendor directory for work orders.

    Tracks contractors, service providers, and suppliers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='vendors'
    )

    name = models.CharField(
        max_length=200,
        help_text="Company name"
    )

    contact_name = models.CharField(
        max_length=100,
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    tax_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="EIN for 1099 reporting"
    )

    license_number = models.CharField(
        max_length=50,
        blank=True
    )

    insurance_expiration = models.DateField(
        null=True,
        blank=True
    )

    payment_terms = models.CharField(
        max_length=50,
        default='Net 30',
        help_text="Payment terms"
    )

    specialty = models.CharField(
        max_length=100,
        blank=True,
        help_text="Vendor specialty/category"
    )

    is_active = models.BooleanField(
        default=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendors'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['specialty']),
        ]

    def __str__(self):
        return self.name


class WorkOrder(models.Model):
    """
    Work orders for maintenance and repairs.

    Tracks requests from creation through completion.
    """

    PRIORITY_EMERGENCY = 'EMERGENCY'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_LOW = 'LOW'

    PRIORITY_CHOICES = [
        (PRIORITY_EMERGENCY, 'Emergency'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_LOW, 'Low'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_OPEN = 'OPEN'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='work_orders'
    )

    work_order_number = models.CharField(
        max_length=50,
        help_text="Auto-generated number (e.g., WO-2025-001)"
    )

    category = models.ForeignKey(
        WorkOrderCategory,
        on_delete=models.PROTECT,
        related_name='work_orders'
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    location = models.CharField(
        max_length=255,
        help_text="Unit number or common area"
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='work_orders',
        null=True,
        blank=True
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='work_orders_requested'
    )

    assigned_to_vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='work_orders',
        null=True,
        blank=True
    )

    assigned_to_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='work_orders_assigned',
        null=True,
        blank=True
    )

    estimated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    actual_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    gl_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='work_orders',
        null=True,
        blank=True,
        help_text="GL expense account"
    )

    fund = models.ForeignKey(
        Fund,
        on_delete=models.PROTECT,
        related_name='work_orders',
        null=True,
        blank=True
    )

    requested_date = models.DateField()

    scheduled_date = models.DateField(
        null=True,
        blank=True
    )

    completed_date = models.DateField(
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='work_orders_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_orders'
        unique_together = [['tenant', 'work_order_number']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['assigned_to_vendor']),
            models.Index(fields=['requested_date']),
        ]

    def __str__(self):
        return f"{self.work_order_number}: {self.title}"


class WorkOrderComment(models.Model):
    """
    Comments on work orders.

    Tracks communication about work orders.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    comment = models.TextField()

    commented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='work_order_comments'
    )

    commented_at = models.DateTimeField(auto_now_add=True)

    is_internal = models.BooleanField(
        default=False,
        help_text="Visible to staff only?"
    )

    class Meta:
        db_table = 'work_order_comments'
        ordering = ['work_order', 'commented_at']
        indexes = [
            models.Index(fields=['work_order', 'commented_at']),
        ]

    def __str__(self):
        return f"Comment on {self.work_order.work_order_number}"


class WorkOrderAttachment(models.Model):
    """
    File attachments for work orders.

    Photos, documents, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file_url = models.URLField(
        max_length=500
    )

    file_name = models.CharField(
        max_length=255
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='work_order_attachments_uploaded'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'work_order_attachments'
        ordering = ['work_order', 'uploaded_at']
        indexes = [
            models.Index(fields=['work_order']),
        ]

    def __str__(self):
        return f"{self.file_name}"


class WorkOrderInvoice(models.Model):
    """
    Vendor invoices for work orders.

    Links work orders to invoices and GL entries.
    """

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_PAID = 'PAID'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PAID, 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.PROTECT,
        related_name='invoices'
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='invoices'
    )

    invoice_number = models.CharField(
        max_length=100
    )

    invoice_date = models.DateField()

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    payment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name='work_order_invoices',
        null=True,
        blank=True
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='work_order_invoices_approved',
        null=True,
        blank=True
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_order_invoices'
        unique_together = [['vendor', 'invoice_number']]
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['work_order']),
            models.Index(fields=['vendor']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.vendor.name}"
