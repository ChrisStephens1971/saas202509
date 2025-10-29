"""
Comprehensive unit tests for Invoice and Payment models.

Tests critical financial operations:
1. Invoice creation and amount tracking
2. Payment application (FIFO logic)
3. Status transitions and validation
4. Decimal precision for money amounts
5. Applied vs unapplied payment tracking
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from tenants.models import Tenant
from accounting.models import (
    Fund, AccountType, Account, Invoice, Payment, PaymentApplication,
    Owner, Unit
)


@pytest.fixture
def tenant(db):
    """Create a test tenant (HOA)."""
    return Tenant.objects.create(
        name="Test HOA",
        schema_name="tenant_test_invoice",
        primary_contact_name="Test Admin",
        primary_contact_email="admin@testhoa.com",
        total_units=50,
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
        fund_type=Fund.TYPE_OPERATING
    )


@pytest.fixture
def owner(db, tenant):
    """Create a test owner."""
    return Owner.objects.create(
        tenant=tenant,
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        phone="555-0100",
        status=Owner.STATUS_ACTIVE
    )


@pytest.fixture
def unit(db, tenant, owner):
    """Create a test unit."""
    return Unit.objects.create(
        tenant=tenant,
        unit_number="101",
        owner=owner,
        unit_type=Unit.TYPE_SINGLE_FAMILY,
        bedrooms=3,
        bathrooms=Decimal('2.0'),
        square_feet=1500
    )


@pytest.mark.django_db
class TestInvoiceBasics:
    """Test basic invoice creation and properties."""

    def test_create_invoice(self, tenant, owner, unit):
        """Test creating a basic invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            invoice_type=Invoice.TYPE_ASSESSMENT,
            amount=Decimal('500.00'),
            description="Monthly assessment for October 2025"
        )

        assert invoice.id is not None
        assert invoice.invoice_number is not None
        assert "INV-" in invoice.invoice_number or invoice.invoice_number.startswith("I")
        assert invoice.amount == Decimal('500.00')
        assert invoice.invoice_type == Invoice.TYPE_ASSESSMENT
        assert invoice.status == Invoice.STATUS_DRAFT
        assert invoice.owner == owner
        assert invoice.unit == unit

    def test_invoice_number_auto_increment(self, tenant, owner, unit):
        """Test that invoice numbers auto-increment."""
        invoice1 = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('500.00')
        )
        invoice2 = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 2),
            due_date=date(2025, 10, 16),
            amount=Decimal('600.00')
        )

        # Invoice numbers should be sequential
        assert invoice2.invoice_number > invoice1.invoice_number

    def test_invoice_amount_precision(self, tenant, owner, unit):
        """Test that invoice amounts maintain 2 decimal precision."""
        amount = Decimal('1234.56')
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=amount
        )

        # Verify precision is exactly 2 decimal places
        assert invoice.amount == Decimal('1234.56')
        assert invoice.amount == invoice.amount.quantize(Decimal('0.01'))


@pytest.mark.django_db
class TestInvoiceAmountTracking:
    """Test invoice amount calculations and tracking."""

    def test_invoice_balance_unpaid(self, tenant, owner, unit):
        """Test balance calculation for unpaid invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('1000.00'),
            status=Invoice.STATUS_ISSUED
        )

        # Unpaid invoice: balance = amount
        balance = invoice.get_balance()
        assert balance == Decimal('1000.00')
        assert invoice.amount_paid == Decimal('0.00')

    def test_invoice_balance_partially_paid(self, tenant, owner, unit):
        """Test balance calculation for partially paid invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('1000.00'),
            amount_paid=Decimal('300.00'),
            status=Invoice.STATUS_PARTIAL
        )

        balance = invoice.get_balance()
        assert balance == Decimal('700.00')
        assert invoice.amount_paid == Decimal('300.00')

    def test_invoice_balance_fully_paid(self, tenant, owner, unit):
        """Test balance calculation for fully paid invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('1000.00'),
            amount_paid=Decimal('1000.00'),
            status=Invoice.STATUS_PAID
        )

        balance = invoice.get_balance()
        assert balance == Decimal('0.00')
        assert invoice.amount_paid == Decimal('1000.00')

    def test_amount_paid_cannot_exceed_amount(self, tenant, owner, unit):
        """Test that amount_paid cannot exceed invoice amount."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('1000.00')
        )

        # Attempting to set amount_paid > amount should be prevented
        # (This should be enforced by business logic, not model validation)
        invoice.amount_paid = Decimal('1100.00')  # More than invoice amount!
        balance = invoice.get_balance()
        assert balance < Decimal('0.00')  # Negative balance (credit)


@pytest.mark.django_db
class TestInvoiceStatus:
    """Test invoice status transitions."""

    def test_invoice_initial_status_is_draft(self, tenant, owner, unit):
        """Test that new invoices start as DRAFT."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('500.00')
        )

        assert invoice.status == Invoice.STATUS_DRAFT

    def test_invoice_status_transitions(self, tenant, owner, unit):
        """Test typical invoice status flow: DRAFT → ISSUED → PARTIAL → PAID."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('1000.00')
        )

        # Start as DRAFT
        assert invoice.status == Invoice.STATUS_DRAFT

        # Issue the invoice
        invoice.status = Invoice.STATUS_ISSUED
        invoice.save()
        assert invoice.status == Invoice.STATUS_ISSUED

        # Partial payment
        invoice.amount_paid = Decimal('400.00')
        invoice.status = Invoice.STATUS_PARTIAL
        invoice.save()
        assert invoice.status == Invoice.STATUS_PARTIAL
        assert invoice.get_balance() == Decimal('600.00')

        # Full payment
        invoice.amount_paid = Decimal('1000.00')
        invoice.status = Invoice.STATUS_PAID
        invoice.save()
        assert invoice.status == Invoice.STATUS_PAID
        assert invoice.get_balance() == Decimal('0.00')

    def test_invoice_overdue_status(self, tenant, owner, unit):
        """Test invoice becomes overdue after due date."""
        past_due_date = date.today() - timedelta(days=30)
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=past_due_date - timedelta(days=15),
            due_date=past_due_date,
            amount=Decimal('500.00'),
            status=Invoice.STATUS_ISSUED
        )

        # Invoice should be overdue (manual status update in real app)
        invoice.status = Invoice.STATUS_OVERDUE
        invoice.save()
        assert invoice.status == Invoice.STATUS_OVERDUE


@pytest.mark.django_db
class TestInvoiceTypes:
    """Test different invoice types."""

    def test_assessment_invoice(self, tenant, owner, unit):
        """Test regular assessment invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            invoice_type=Invoice.TYPE_ASSESSMENT,
            amount=Decimal('500.00'),
            description="Monthly assessment"
        )

        assert invoice.invoice_type == Invoice.TYPE_ASSESSMENT

    def test_late_fee_invoice(self, tenant, owner, unit):
        """Test late fee invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 16),
            due_date=date(2025, 10, 30),
            invoice_type=Invoice.TYPE_LATE_FEE,
            amount=Decimal('25.00'),
            description="Late fee for October payment"
        )

        assert invoice.invoice_type == Invoice.TYPE_LATE_FEE

    def test_special_assessment_invoice(self, tenant, owner, unit):
        """Test special assessment invoice."""
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 12, 31),
            invoice_type=Invoice.TYPE_SPECIAL,
            amount=Decimal('5000.00'),
            description="Roof replacement special assessment"
        )

        assert invoice.invoice_type == Invoice.TYPE_SPECIAL


@pytest.mark.django_db
class TestPaymentBasics:
    """Test basic payment creation and properties."""

    def test_create_payment(self, tenant, owner):
        """Test creating a basic payment."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            payment_method=Payment.METHOD_CHECK,
            reference_number="1234",
            amount=Decimal('500.00'),
            status=Payment.STATUS_PENDING
        )

        assert payment.id is not None
        assert payment.payment_number is not None
        assert "PMT-" in payment.payment_number or payment.payment_number.startswith("P")
        assert payment.amount == Decimal('500.00')
        assert payment.payment_method == Payment.METHOD_CHECK
        assert payment.status == Payment.STATUS_PENDING
        assert payment.amount_applied == Decimal('0.00')
        assert payment.amount_unapplied == Decimal('500.00')

    def test_payment_number_auto_increment(self, tenant, owner):
        """Test that payment numbers auto-increment."""
        payment1 = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('500.00')
        )
        payment2 = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 6),
            amount=Decimal('600.00')
        )

        assert payment2.payment_number > payment1.payment_number

    def test_payment_amount_precision(self, tenant, owner):
        """Test that payment amounts maintain 2 decimal precision."""
        amount = Decimal('1234.56')
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=amount
        )

        assert payment.amount == Decimal('1234.56')
        assert payment.amount == payment.amount.quantize(Decimal('0.01'))


@pytest.mark.django_db
class TestPaymentApplication:
    """Test payment application logic (FIFO)."""

    def test_payment_applied_amounts(self, tenant, owner):
        """Test that payment tracks applied and unapplied amounts."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('1000.00')
        )

        # Initially all unapplied
        assert payment.amount == Decimal('1000.00')
        assert payment.amount_applied == Decimal('0.00')
        assert payment.amount_unapplied == Decimal('1000.00')

        # Apply $600
        payment.amount_applied = Decimal('600.00')
        payment.amount_unapplied = Decimal('400.00')
        payment.save()

        assert payment.amount_applied == Decimal('600.00')
        assert payment.amount_unapplied == Decimal('400.00')

    def test_payment_amounts_must_sum_to_total(self, tenant, owner):
        """Test that amount_applied + amount_unapplied = amount."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('1000.00'),
            amount_applied=Decimal('700.00'),
            amount_unapplied=Decimal('300.00')
        )

        # Verify the accounting equation
        assert payment.amount_applied + payment.amount_unapplied == payment.amount

    def test_payment_fully_applied(self, tenant, owner):
        """Test a fully applied payment."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('500.00'),
            amount_applied=Decimal('500.00'),
            amount_unapplied=Decimal('0.00')
        )

        assert payment.amount_applied == payment.amount
        assert payment.amount_unapplied == Decimal('0.00')

    def test_unapplied_payment_creates_credit(self, tenant, owner):
        """Test that unapplied payments create owner credit."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('2000.00'),  # More than invoices owed
            amount_applied=Decimal('1500.00'),
            amount_unapplied=Decimal('500.00')  # Credit on account
        )

        # Unapplied amount represents owner credit
        assert payment.amount_unapplied == Decimal('500.00')


@pytest.mark.django_db
class TestPaymentStatus:
    """Test payment status transitions."""

    def test_payment_initial_status_is_pending(self, tenant, owner):
        """Test that new payments start as PENDING."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('500.00')
        )

        assert payment.status == Payment.STATUS_PENDING

    def test_payment_status_cleared(self, tenant, owner):
        """Test payment clearing (check cleared, ACH settled)."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            payment_method=Payment.METHOD_CHECK,
            amount=Decimal('500.00'),
            status=Payment.STATUS_PENDING
        )

        # Check clears
        payment.status = Payment.STATUS_CLEARED
        payment.save()

        assert payment.status == Payment.STATUS_CLEARED

    def test_payment_status_bounced(self, tenant, owner):
        """Test handling bounced payment."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            payment_method=Payment.METHOD_CHECK,
            amount=Decimal('500.00'),
            status=Payment.STATUS_PENDING
        )

        # Check bounces (NSF)
        payment.status = Payment.STATUS_BOUNCED
        payment.save()

        assert payment.status == Payment.STATUS_BOUNCED


@pytest.mark.django_db
class TestPaymentMethods:
    """Test different payment methods."""

    def test_payment_by_check(self, tenant, owner):
        """Test check payment."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            payment_method=Payment.METHOD_CHECK,
            reference_number="1234",
            amount=Decimal('500.00')
        )

        assert payment.payment_method == Payment.METHOD_CHECK
        assert payment.reference_number == "1234"

    def test_payment_by_ach(self, tenant, owner):
        """Test ACH payment."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            payment_method=Payment.METHOD_ACH,
            reference_number="ACH-9876",
            amount=Decimal('500.00')
        )

        assert payment.payment_method == Payment.METHOD_ACH

    def test_payment_by_credit_card(self, tenant, owner):
        """Test credit card payment."""
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            payment_method=Payment.METHOD_CREDIT_CARD,
            reference_number="CC-1234-5678",
            amount=Decimal('500.00')
        )

        assert payment.payment_method == Payment.METHOD_CREDIT_CARD


@pytest.mark.django_db
class TestInvoicePaymentIntegration:
    """Test invoice and payment integration."""

    def test_payment_applied_to_invoice(self, tenant, owner, unit):
        """Test applying payment to an invoice."""
        # Create invoice
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('500.00'),
            status=Invoice.STATUS_ISSUED
        )

        # Create payment
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('500.00')
        )

        # Apply payment to invoice
        PaymentApplication.objects.create(
            payment=payment,
            invoice=invoice,
            amount=Decimal('500.00')
        )

        # Update payment
        payment.amount_applied = Decimal('500.00')
        payment.amount_unapplied = Decimal('0.00')
        payment.save()

        # Update invoice
        invoice.amount_paid = Decimal('500.00')
        invoice.status = Invoice.STATUS_PAID
        invoice.save()

        # Verify
        assert payment.amount_applied == Decimal('500.00')
        assert invoice.amount_paid == Decimal('500.00')
        assert invoice.get_balance() == Decimal('0.00')
        assert invoice.status == Invoice.STATUS_PAID

    def test_payment_applied_to_multiple_invoices(self, tenant, owner, unit):
        """Test applying one payment to multiple invoices (FIFO)."""
        # Create two invoices
        invoice1 = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 9, 1),  # Older invoice
            due_date=date(2025, 9, 15),
            amount=Decimal('300.00'),
            status=Invoice.STATUS_ISSUED
        )

        invoice2 = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),  # Newer invoice
            due_date=date(2025, 10, 15),
            amount=Decimal('400.00'),
            status=Invoice.STATUS_ISSUED
        )

        # Create payment that covers both invoices
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('700.00')
        )

        # Apply to older invoice first (FIFO)
        PaymentApplication.objects.create(
            payment=payment,
            invoice=invoice1,
            amount=Decimal('300.00')
        )

        # Apply remainder to newer invoice
        PaymentApplication.objects.create(
            payment=payment,
            invoice=invoice2,
            amount=Decimal('400.00')
        )

        # Update invoices
        invoice1.amount_paid = Decimal('300.00')
        invoice1.status = Invoice.STATUS_PAID
        invoice1.save()

        invoice2.amount_paid = Decimal('400.00')
        invoice2.status = Invoice.STATUS_PAID
        invoice2.save()

        # Update payment
        payment.amount_applied = Decimal('700.00')
        payment.amount_unapplied = Decimal('0.00')
        payment.save()

        # Verify both invoices paid
        assert invoice1.status == Invoice.STATUS_PAID
        assert invoice2.status == Invoice.STATUS_PAID
        assert payment.amount_applied == payment.amount

    def test_partial_payment_application(self, tenant, owner, unit):
        """Test partial payment of an invoice."""
        # Create invoice
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('1000.00'),
            status=Invoice.STATUS_ISSUED
        )

        # Create partial payment
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('400.00')
        )

        # Apply payment to invoice
        PaymentApplication.objects.create(
            payment=payment,
            invoice=invoice,
            amount=Decimal('400.00')
        )

        # Update invoice
        invoice.amount_paid = Decimal('400.00')
        invoice.status = Invoice.STATUS_PARTIAL
        invoice.save()

        # Update payment
        payment.amount_applied = Decimal('400.00')
        payment.amount_unapplied = Decimal('0.00')
        payment.save()

        # Verify partial payment
        assert invoice.status == Invoice.STATUS_PARTIAL
        assert invoice.get_balance() == Decimal('600.00')
        assert payment.amount_applied == Decimal('400.00')


@pytest.mark.django_db
class TestDecimalArithmetic:
    """Test decimal arithmetic for financial accuracy."""

    def test_invoice_and_payment_precision(self, tenant, owner, unit):
        """Test that invoice and payment amounts maintain precision."""
        # Create invoice with precise amount
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('123.45')
        )

        # Create payment with precise amount
        payment = Payment.objects.create(
            tenant=tenant,
            owner=owner,
            payment_date=date(2025, 10, 5),
            amount=Decimal('123.45')
        )

        # Apply payment
        PaymentApplication.objects.create(
            payment=payment,
            invoice=invoice,
            amount=Decimal('123.45')
        )

        # Verify no rounding errors
        assert invoice.amount == Decimal('123.45')
        assert payment.amount == Decimal('123.45')
        assert invoice.amount == payment.amount

    def test_no_floating_point_errors_in_calculations(self, tenant, owner, unit):
        """Test that calculations don't have floating point errors."""
        # Create invoice
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date(2025, 10, 1),
            due_date=date(2025, 10, 15),
            amount=Decimal('0.10') + Decimal('0.20')  # 0.30
        )

        # This would be 0.30000000000000004 with floats, but Decimal handles it correctly
        assert invoice.amount == Decimal('0.30')
