"""
Django management command to generate AR aging report.

Usage:
    python manage.py ar_aging_report --tenant=tenant_sunset_hills
    python manage.py ar_aging_report --tenant=tenant_sunset_hills --export=report.csv

This command:
1. Gets all owners with unpaid invoices
2. Buckets invoices by aging (Current, 1-30, 31-60, 61-90, 90+)
3. Shows balance by aging bucket per owner
4. Optionally exports to CSV
"""

from django.core.management.base import BaseCommand, CommandError
from datetime import date
from decimal import Decimal
import csv

from tenants.models import Tenant
from accounting.models import Invoice, Owner


class Command(BaseCommand):
    help = 'Generate AR aging report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., tenant_sunset_hills)'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Export to CSV file (e.g., ar_aging.csv)'
        )
        parser.add_argument(
            '--show-detail',
            action='store_true',
            help='Show detail (invoices) in addition to summary'
        )

    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        export_file = options.get('export')
        show_detail = options['show_detail']

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{tenant_schema}' does not exist")

        self.stdout.write("=" * 120)
        self.stdout.write(f"AR AGING REPORT - {tenant.name}")
        self.stdout.write(f"As of: {date.today()}")
        self.stdout.write("=" * 120)
        self.stdout.write()

        # Get all owners with unpaid balances
        owners = Owner.objects.filter(tenant=tenant).order_by('last_name', 'first_name')

        # Prepare report data
        report_data = []
        grand_totals = {
            'Current': Decimal('0.00'),
            '1-30 days': Decimal('0.00'),
            '31-60 days': Decimal('0.00'),
            '61-90 days': Decimal('0.00'),
            '90+ days': Decimal('0.00'),
            'Total': Decimal('0.00')
        }

        # Header
        header = f"{'Owner':<30} {'Current':>15} {'1-30 Days':>15} {'31-60 Days':>15} {'61-90 Days':>15} {'90+ Days':>15} {'Total':>15}"
        self.stdout.write(header)
        self.stdout.write("-" * 120)

        for owner in owners:
            # Get unpaid invoices
            unpaid_invoices = Invoice.objects.filter(
                tenant=tenant,
                owner=owner,
                status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL]
            ).order_by('invoice_date')

            if not unpaid_invoices.exists():
                continue  # Skip owners with no balance

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

            # Calculate total for owner
            owner_total = sum(aging.values())

            # Skip if owner has $0 balance
            if owner_total == 0:
                continue

            # Add to grand totals
            for bucket in aging.keys():
                grand_totals[bucket] += aging[bucket]
            grand_totals['Total'] += owner_total

            # Format owner name
            owner_name = f"{owner.last_name}, {owner.first_name}"

            # Print summary line
            line = f"{owner_name:<30} ${aging['Current']:>14,.2f} ${aging['1-30 days']:>14,.2f} ${aging['31-60 days']:>14,.2f} ${aging['61-90 days']:>14,.2f} ${aging['90+ days']:>14,.2f} ${owner_total:>14,.2f}"
            self.stdout.write(line)

            # Store for CSV export
            report_data.append({
                'Owner': owner_name,
                'Current': aging['Current'],
                '1-30 Days': aging['1-30 days'],
                '31-60 Days': aging['31-60 days'],
                '61-90 Days': aging['61-90 days'],
                '90+ Days': aging['90+ days'],
                'Total': owner_total
            })

            # Show detail if requested
            if show_detail:
                for invoice in unpaid_invoices:
                    detail_line = f"    {invoice.invoice_number}  {invoice.invoice_date}  {invoice.due_date}  ${invoice.amount_due:>10,.2f}  {invoice.aging_bucket}"
                    self.stdout.write(detail_line)
                self.stdout.write()

        # Grand totals
        self.stdout.write("-" * 120)
        totals_line = f"{'TOTAL':<30} ${grand_totals['Current']:>14,.2f} ${grand_totals['1-30 days']:>14,.2f} ${grand_totals['31-60 days']:>14,.2f} ${grand_totals['61-90 days']:>14,.2f} ${grand_totals['90+ days']:>14,.2f} ${grand_totals['Total']:>14,.2f}"
        self.stdout.write(totals_line)
        self.stdout.write("=" * 120)
        self.stdout.write()

        # Summary statistics
        total_ar = grand_totals['Total']
        if total_ar > 0:
            current_pct = (grand_totals['Current'] / total_ar * 100) if total_ar > 0 else 0
            days_1_30_pct = (grand_totals['1-30 days'] / total_ar * 100) if total_ar > 0 else 0
            days_31_60_pct = (grand_totals['31-60 days'] / total_ar * 100) if total_ar > 0 else 0
            days_61_90_pct = (grand_totals['61-90 days'] / total_ar * 100) if total_ar > 0 else 0
            days_90_plus_pct = (grand_totals['90+ days'] / total_ar * 100) if total_ar > 0 else 0

            self.stdout.write("AR Aging Breakdown:")
            self.stdout.write(f"  Current:       ${grand_totals['Current']:>12,.2f}  ({current_pct:>5.1f}%)")
            self.stdout.write(f"  1-30 days:     ${grand_totals['1-30 days']:>12,.2f}  ({days_1_30_pct:>5.1f}%)")
            self.stdout.write(f"  31-60 days:    ${grand_totals['31-60 days']:>12,.2f}  ({days_31_60_pct:>5.1f}%)")
            self.stdout.write(f"  61-90 days:    ${grand_totals['61-90 days']:>12,.2f}  ({days_61_90_pct:>5.1f}%)")
            self.stdout.write(f"  90+ days:      ${grand_totals['90+ days']:>12,.2f}  ({days_90_plus_pct:>5.1f}%)")
            self.stdout.write(f"  TOTAL AR:      ${total_ar:>12,.2f}  (100.0%)")
        else:
            self.stdout.write("No outstanding AR balances")

        # Export to CSV if requested
        if export_file:
            with open(export_file, 'w', newline='') as csvfile:
                fieldnames = ['Owner', 'Current', '1-30 Days', '31-60 Days', '61-90 Days', '90+ Days', 'Total']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for row in report_data:
                    writer.writerow(row)

                # Add totals row
                writer.writerow({
                    'Owner': 'TOTAL',
                    'Current': grand_totals['Current'],
                    '1-30 Days': grand_totals['1-30 days'],
                    '31-60 Days': grand_totals['31-60 days'],
                    '61-90 Days': grand_totals['61-90 days'],
                    '90+ Days': grand_totals['90+ days'],
                    'Total': grand_totals['Total']
                })

            self.stdout.write()
            self.stdout.write(self.style.SUCCESS(f"Report exported to: {export_file}"))
