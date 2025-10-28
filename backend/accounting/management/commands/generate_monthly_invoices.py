"""
Django management command to generate monthly assessment invoices for all active units.

Usage:
    python manage.py generate_monthly_invoices --tenant=tenant_sunset_hills --month=2025-11-01

This command:
1. Gets all active units for the tenant
2. For each unit, gets current owner(s)
3. Creates invoice with assessment amount from unit.monthly_assessment
4. Creates invoice line for assessment revenue
5. Auto-creates journal entry (DR: AR, CR: Assessment Revenue)
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import date, datetime, timedelta
from decimal import Decimal

from tenants.models import Tenant
from accounting.models import (
    Unit, Owner, Ownership, Invoice, InvoiceLine, Account
)


class Command(BaseCommand):
    help = 'Generate monthly assessment invoices for all active units'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., tenant_sunset_hills)'
        )
        parser.add_argument(
            '--month',
            type=str,
            required=True,
            help='Invoice month in YYYY-MM-DD format (e.g., 2025-11-01)'
        )
        parser.add_argument(
            '--due-days',
            type=int,
            default=10,
            help='Number of days until due date (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate invoice generation without saving to database'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        month_str = options['month']
        due_days = options['due_days']
        dry_run = options['dry_run']

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{tenant_schema}' does not exist")

        # Parse invoice date
        try:
            invoice_date = datetime.strptime(month_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError(f"Invalid date format: {month_str}. Use YYYY-MM-DD")

        # Calculate due date
        due_date = invoice_date + timedelta(days=due_days)

        # Get assessment revenue account
        assessment_revenue = Account.objects.filter(
            tenant=tenant,
            account_number='4100'
        ).first()

        if not assessment_revenue:
            raise CommandError(f"Assessment Revenue account (4100) not found for tenant {tenant.name}")

        self.stdout.write("=" * 80)
        self.stdout.write(f"MONTHLY INVOICE GENERATION - {tenant.name}")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Invoice Date: {invoice_date}")
        self.stdout.write(f"Due Date: {due_date}")
        self.stdout.write(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        self.stdout.write("")

        # Get all active units
        active_units = Unit.objects.filter(
            tenant=tenant,
            status=Unit.STATUS_OCCUPIED
        ).order_by('unit_number')

        if not active_units.exists():
            self.stdout.write(self.style.WARNING("No active units found"))
            return

        self.stdout.write(f"Found {active_units.count()} active units")
        self.stdout.write("")

        invoices_created = 0
        total_invoiced = Decimal('0.00')
        errors = []

        for unit in active_units:
            try:
                # Get current owner(s)
                current_ownerships = Ownership.objects.filter(
                    tenant=tenant,
                    unit=unit,
                    is_current=True
                )

                if not current_ownerships.exists():
                    errors.append(f"Unit {unit.unit_number}: No current owner")
                    continue

                # For now, handle single owner (most common case)
                # TODO: Handle multiple owners with split invoices
                ownership = current_ownerships.first()
                owner = ownership.owner

                # Check if invoice already exists for this month
                existing_invoice = Invoice.objects.filter(
                    tenant=tenant,
                    owner=owner,
                    unit=unit,
                    invoice_date=invoice_date,
                    invoice_type=Invoice.TYPE_ASSESSMENT
                ).first()

                if existing_invoice:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [SKIP] Unit {unit.unit_number}: Invoice already exists ({existing_invoice.invoice_number})"
                        )
                    )
                    continue

                # Create invoice
                month_name = invoice_date.strftime('%B %Y')

                if not dry_run:
                    invoice = Invoice.objects.create(
                        tenant=tenant,
                        owner=owner,
                        unit=unit,
                        invoice_date=invoice_date,
                        due_date=due_date,
                        invoice_type=Invoice.TYPE_ASSESSMENT,
                        status=Invoice.STATUS_ISSUED,
                        subtotal=unit.monthly_assessment,
                        late_fee=Decimal('0.00'),
                        total_amount=unit.monthly_assessment,
                        amount_paid=Decimal('0.00'),
                        amount_due=unit.monthly_assessment,
                        description=f"{month_name} Monthly Assessment - Unit {unit.unit_number}"
                    )

                    # Create invoice line
                    InvoiceLine.objects.create(
                        invoice=invoice,
                        line_number=1,
                        description=f"{month_name} Monthly Assessment",
                        account=assessment_revenue,
                        amount=unit.monthly_assessment
                    )

                    # Create journal entry
                    invoice.create_journal_entry()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  [OK] Unit {unit.unit_number}: {owner.first_name} {owner.last_name} - "
                            f"${unit.monthly_assessment} (Invoice: {invoice.invoice_number})"
                        )
                    )
                else:
                    self.stdout.write(
                        f"  [DRY RUN] Unit {unit.unit_number}: {owner.first_name} {owner.last_name} - "
                        f"${unit.monthly_assessment}"
                    )

                invoices_created += 1
                total_invoiced += unit.monthly_assessment

            except Exception as e:
                errors.append(f"Unit {unit.unit_number}: {str(e)}")
                continue

        # Summary
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Invoices created: {invoices_created}")
        self.stdout.write(f"Total invoiced: ${total_invoiced:,.2f}")
        self.stdout.write("")

        if errors:
            self.stdout.write(self.style.ERROR("ERRORS:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No invoices were saved to database"))
        else:
            self.stdout.write(self.style.SUCCESS("Invoice generation completed!"))
