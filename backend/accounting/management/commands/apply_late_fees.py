"""
Django management command to apply late fees to overdue invoices.

Usage:
    python manage.py apply_late_fees --tenant=tenant_sunset_hills

This command:
1. Finds all overdue invoices past grace period
2. Calculates and applies late fees
3. Creates journal entries for late fees
4. Reports results

Run this nightly via cron to automatically apply late fees.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import date
from decimal import Decimal

from tenants.models import Tenant
from accounting.models import Invoice


class Command(BaseCommand):
    help = 'Apply late fees to overdue invoices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., tenant_sunset_hills)'
        )
        parser.add_argument(
            '--grace-period',
            type=int,
            default=5,
            help='Grace period in days before late fee applies (default: 5)'
        )
        parser.add_argument(
            '--late-fee-percentage',
            type=float,
            default=0.05,
            help='Late fee as percentage of balance (default: 0.05 = 5%%)'
        )
        parser.add_argument(
            '--minimum-late-fee',
            type=float,
            default=25.00,
            help='Minimum late fee amount (default: $25.00)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate late fee application without saving to database'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        grace_period = options['grace_period']
        late_fee_percentage = Decimal(str(options['late_fee_percentage']))
        minimum_late_fee = Decimal(str(options['minimum_late_fee']))
        dry_run = options['dry_run']

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{tenant_schema}' does not exist")

        self.stdout.write("=" * 80)
        self.stdout.write(f"LATE FEE APPLICATION - {tenant.name}")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Date: {date.today()}")
        self.stdout.write(f"Grace Period: {grace_period} days")
        self.stdout.write(f"Late Fee: {late_fee_percentage * 100}% (min ${minimum_late_fee})")
        self.stdout.write(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        self.stdout.write("")

        # Get overdue invoices without late fees
        overdue_invoices = Invoice.objects.filter(
            tenant=tenant,
            status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL],
            late_fee=Decimal('0.00')
        ).order_by('due_date', 'invoice_number')

        if not overdue_invoices.exists():
            self.stdout.write(self.style.WARNING("No overdue invoices found"))
            return

        self.stdout.write(f"Found {overdue_invoices.count()} invoices to check")
        self.stdout.write("")

        late_fees_applied = 0
        total_late_fees = Decimal('0.00')
        errors = []

        for invoice in overdue_invoices:
            try:
                # Calculate late fee
                late_fee_amount = invoice.calculate_late_fee(
                    grace_period_days=grace_period,
                    late_fee_percentage=late_fee_percentage,
                    minimum_late_fee=minimum_late_fee
                )

                if late_fee_amount == 0:
                    # Not past grace period or already has late fee
                    continue

                if dry_run:
                    self.stdout.write(
                        f"  [DRY RUN] {invoice.invoice_number}: {invoice.owner.first_name} {invoice.owner.last_name} - "
                        f"${late_fee_amount} late fee (overdue {invoice.days_overdue} days)"
                    )
                else:
                    # Apply late fee
                    late_fee_amount, je = invoice.apply_late_fee(
                        grace_period_days=grace_period,
                        late_fee_percentage=late_fee_percentage,
                        minimum_late_fee=minimum_late_fee
                    )

                    if late_fee_amount > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [OK] {invoice.invoice_number}: {invoice.owner.first_name} {invoice.owner.last_name} - "
                                f"${late_fee_amount} late fee applied (overdue {invoice.days_overdue} days)"
                            )
                        )

                late_fees_applied += 1
                total_late_fees += late_fee_amount

            except Exception as e:
                errors.append(f"Invoice {invoice.invoice_number}: {str(e)}")
                continue

        # Summary
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Late fees applied: {late_fees_applied}")
        self.stdout.write(f"Total late fees: ${total_late_fees:,.2f}")
        self.stdout.write("")

        if errors:
            self.stdout.write(self.style.ERROR("ERRORS:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No late fees were saved to database"))
        else:
            self.stdout.write(self.style.SUCCESS("Late fee application completed!"))
