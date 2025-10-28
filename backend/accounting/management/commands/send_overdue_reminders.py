"""
Django management command to send overdue payment reminders.

Usage:
    python manage.py send_overdue_reminders --tenant=tenant_sunset_hills
    python manage.py send_overdue_reminders  # All tenants
"""

from django.core.management.base import BaseCommand, CommandError
from accounting.email_service import EmailService
from tenants.models import Tenant
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send overdue payment reminders for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant schema name (if omitted, processes all tenants)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which invoices would get reminders without sending emails',
        )

    def handle(self, *args, **options):
        # Get tenants
        if options['tenant']:
            try:
                tenants = [Tenant.objects.get(schema_name=options['tenant'])]
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant '{options['tenant']}' not found")
        else:
            tenants = Tenant.objects.all()

        # Process each tenant
        total_sent = 0
        total_failed = 0
        total_no_email = 0

        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name}')

            if options['dry_run']:
                # Dry run: just show what would be sent
                from datetime import date
                from decimal import Decimal
                from accounting.models import Invoice

                overdue_invoices = Invoice.objects.filter(
                    tenant=tenant,
                    due_date__lt=date.today(),
                    balance__gt=Decimal('0.00')
                ).select_related('owner')

                for invoice in overdue_invoices:
                    days_overdue = (date.today() - invoice.due_date).days
                    if invoice.owner.email:
                        self.stdout.write(
                            f'  Would send: {invoice.invoice_number} to {invoice.owner.email} '
                            f'({days_overdue} days overdue, ${invoice.balance})'
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  No email: {invoice.invoice_number} - {invoice.owner} '
                                f'({days_overdue} days overdue, ${invoice.balance})'
                            )
                        )
            else:
                # Actually send reminders
                results = EmailService.send_bulk_overdue_reminders(tenant)

                total_sent += results['sent']
                total_failed += results['failed']
                total_no_email += results['no_email']

                self.stdout.write(
                    f'  Sent: {results["sent"]}, '
                    f'Failed: {results["failed"]}, '
                    f'No email: {results["no_email"]}'
                )

        # Summary
        if not options['dry_run']:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('SUMMARY')
            self.stdout.write('=' * 60)
            self.stdout.write(f'Total reminders sent: {total_sent}')
            self.stdout.write(f'Total failed: {total_failed}')
            self.stdout.write(f'Total without email: {total_no_email}')

            if total_sent > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully sent {total_sent} overdue reminders'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('\nNo overdue reminders sent')
                )
        else:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN: No emails were sent')
            )
