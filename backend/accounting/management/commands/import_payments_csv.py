"""
Django management command to import payments from CSV file.

CSV Format:
date,owner_email,amount,reference,method
2025-11-15,alice@example.com,400.00,ACH-2025-11-15-001,ACH
2025-11-15,bob@example.com,400.00,ACH-2025-11-15-002,ACH

Usage:
    python manage.py import_payments_csv --tenant=tenant_sunset_hills --file=payments.csv
    python manage.py import_payments_csv --tenant=tenant_sunset_hills --file=payments.csv --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import datetime
from decimal import Decimal
import csv

from tenants.models import Tenant
from accounting.models import Owner, Payment, Invoice, PaymentApplication


class Command(BaseCommand):
    help = 'Import payments from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., tenant_sunset_hills)'
        )
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to CSV file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database'
        )
        parser.add_argument(
            '--auto-apply',
            action='store_true',
            default=True,
            help='Automatically apply payments to oldest invoices (FIFO)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        file_path = options['file']
        dry_run = options['dry_run']
        auto_apply = options['auto_apply']

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{tenant_schema}' does not exist")

        self.stdout.write("=" * 80)
        self.stdout.write(f"PAYMENT CSV IMPORT - {tenant.name}")
        self.stdout.write("=" * 80)
        self.stdout.write(f"File: {file_path}")
        self.stdout.write(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        self.stdout.write(f"Auto-apply: {'Yes' if auto_apply else 'No'}")
        self.stdout.write("")

        # Read CSV file
        try:
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate headers
                required_headers = ['date', 'owner_email', 'amount', 'reference', 'method']
                if not all(header in reader.fieldnames for header in required_headers):
                    raise CommandError(
                        f"CSV file must have headers: {', '.join(required_headers)}\n"
                        f"Found: {', '.join(reader.fieldnames)}"
                    )

                payments_created = 0
                payments_failed = 0
                total_amount = Decimal('0.00')
                errors = []

                for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header row
                    try:
                        # Parse row
                        payment_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                        owner_email = row['owner_email'].strip()
                        amount = Decimal(row['amount'])
                        reference = row['reference'].strip()
                        method = row['method'].strip().upper()

                        # Validate payment method
                        valid_methods = [Payment.METHOD_CHECK, Payment.METHOD_ACH, Payment.METHOD_CREDIT_CARD, Payment.METHOD_CASH]
                        if method not in valid_methods:
                            errors.append(f"Row {row_num}: Invalid payment method '{method}'. Must be one of: {', '.join(valid_methods)}")
                            payments_failed += 1
                            continue

                        # Find owner
                        try:
                            owner = Owner.objects.get(tenant=tenant, email=owner_email)
                        except Owner.DoesNotExist:
                            errors.append(f"Row {row_num}: Owner with email '{owner_email}' not found")
                            payments_failed += 1
                            continue

                        if dry_run:
                            self.stdout.write(
                                f"  [DRY RUN] Row {row_num}: {owner.first_name} {owner.last_name} - ${amount} ({method})"
                            )
                            payments_created += 1
                            total_amount += amount
                            continue

                        # Create payment
                        payment = Payment.objects.create(
                            tenant=tenant,
                            owner=owner,
                            payment_date=payment_date,
                            payment_method=method,
                            amount=amount,
                            amount_applied=Decimal('0.00'),
                            amount_unapplied=amount,
                            status=Payment.STATUS_CLEARED,
                            reference_number=reference
                        )

                        # Auto-apply to invoices if enabled
                        if auto_apply:
                            # Get unpaid invoices (FIFO - oldest first)
                            unpaid_invoices = Invoice.objects.filter(
                                tenant=tenant,
                                owner=owner,
                                status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL]
                            ).order_by('invoice_date', 'invoice_number')

                            remaining_amount = amount
                            for invoice in unpaid_invoices:
                                if remaining_amount <= 0:
                                    break

                                # Calculate amount to apply to this invoice
                                amount_to_apply = min(remaining_amount, invoice.amount_due)

                                # Create payment application
                                PaymentApplication.objects.create(
                                    payment=payment,
                                    invoice=invoice,
                                    amount_applied=amount_to_apply
                                )

                                # Update invoice
                                invoice.amount_paid += amount_to_apply
                                invoice.amount_due = invoice.total_amount - invoice.amount_paid

                                if invoice.amount_due == 0:
                                    invoice.status = Invoice.STATUS_PAID
                                elif invoice.amount_paid > 0:
                                    invoice.status = Invoice.STATUS_PARTIAL

                                invoice.save()

                                # Update remaining amount
                                remaining_amount -= amount_to_apply

                            # Update payment amounts
                            payment.amount_applied = amount - remaining_amount
                            payment.amount_unapplied = remaining_amount
                            Payment.objects.filter(pk=payment.pk).update(
                                amount_applied=payment.amount_applied,
                                amount_unapplied=payment.amount_unapplied
                            )

                        # Create journal entry
                        payment.create_journal_entry()

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [OK] Row {row_num}: {payment.payment_number} - {owner.first_name} {owner.last_name} - ${amount} ({method})"
                            )
                        )
                        payments_created += 1
                        total_amount += amount

                    except ValueError as e:
                        errors.append(f"Row {row_num}: Invalid data format - {str(e)}")
                        payments_failed += 1
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        payments_failed += 1

        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error reading CSV file: {str(e)}")

        # Summary
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Payments created: {payments_created}")
        self.stdout.write(f"Payments failed: {payments_failed}")
        self.stdout.write(f"Total amount: ${total_amount:,.2f}")
        self.stdout.write("")

        if errors:
            self.stdout.write(self.style.ERROR("ERRORS:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No payments were saved to database"))
        else:
            self.stdout.write(self.style.SUCCESS("Payment import completed!"))
