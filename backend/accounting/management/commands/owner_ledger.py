"""
Django management command to generate owner ledger report.

Usage:
    python manage.py owner_ledger --tenant=tenant_sunset_hills --owner=alice@example.com
    python manage.py owner_ledger --tenant=tenant_sunset_hills --owner-id=<uuid>

This command:
1. Gets all invoices and payments for an owner
2. Shows chronological transaction history
3. Calculates running balance
4. Shows current balance
"""

from django.core.management.base import BaseCommand, CommandError
from datetime import date as today_date
from decimal import Decimal

from tenants.models import Tenant
from accounting.models import Invoice, Payment, PaymentApplication, Owner


class Command(BaseCommand):
    help = 'Generate owner ledger report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., tenant_sunset_hills)'
        )
        parser.add_argument(
            '--owner',
            type=str,
            help='Owner email address'
        )
        parser.add_argument(
            '--owner-id',
            type=str,
            help='Owner UUID'
        )

    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        owner_email = options.get('owner')
        owner_id = options.get('owner_id')

        if not owner_email and not owner_id:
            raise CommandError("Must provide either --owner or --owner-id")

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{tenant_schema}' does not exist")

        # Get owner
        if owner_email:
            try:
                owner = Owner.objects.get(tenant=tenant, email=owner_email)
            except Owner.DoesNotExist:
                raise CommandError(f"Owner with email '{owner_email}' not found")
        else:
            try:
                owner = Owner.objects.get(tenant=tenant, id=owner_id)
            except Owner.DoesNotExist:
                raise CommandError(f"Owner with ID '{owner_id}' not found")

        # Get owner's unit(s)
        from accounting.models import Ownership
        ownerships = Ownership.objects.filter(tenant=tenant, owner=owner, is_current=True)
        units = [ownership.unit for ownership in ownerships]

        self.stdout.write("=" * 120)
        self.stdout.write(f"OWNER LEDGER - {owner.first_name} {owner.last_name}")
        self.stdout.write(f"Email: {owner.email}")
        self.stdout.write(f"Phone: {owner.phone}")
        if units:
            unit_numbers = ", ".join([unit.unit_number for unit in units])
            self.stdout.write(f"Unit(s): {unit_numbers}")
        self.stdout.write(f"As of: {today_date.today()}")
        self.stdout.write("=" * 120)
        self.stdout.write()

        # Get all invoices
        invoices = Invoice.objects.filter(
            tenant=tenant,
            owner=owner
        ).order_by('invoice_date', 'invoice_number')

        # Get all payments
        payments = Payment.objects.filter(
            tenant=tenant,
            owner=owner
        ).order_by('payment_date', 'payment_number')

        # Create ledger transactions list
        transactions = []

        # Add invoices
        for invoice in invoices:
            transactions.append({
                'date': invoice.invoice_date,
                'type': 'Invoice',
                'number': invoice.invoice_number,
                'description': invoice.description,
                'charges': invoice.total_amount,
                'payments': Decimal('0.00'),
                'reference': invoice
            })

        # Add payments
        for payment in payments:
            # Get applied invoices
            applications = PaymentApplication.objects.filter(payment=payment)
            invoice_numbers = ", ".join([app.invoice.invoice_number for app in applications])
            description = f"{payment.payment_method}"
            if invoice_numbers:
                description += f" (Applied to: {invoice_numbers})"
            if payment.reference_number:
                description += f" - Ref: {payment.reference_number}"

            transactions.append({
                'date': payment.payment_date,
                'type': 'Payment',
                'number': payment.payment_number,
                'description': description,
                'charges': Decimal('0.00'),
                'payments': payment.amount,
                'reference': payment
            })

        # Sort by date
        transactions.sort(key=lambda x: (x['date'], x['type']))

        # Print ledger
        header = f"{'Date':<12} {'Type':<10} {'Number':<12} {'Description':<40} {'Charges':>15} {'Payments':>15} {'Balance':>15}"
        self.stdout.write(header)
        self.stdout.write("-" * 120)

        running_balance = Decimal('0.00')
        total_charges = Decimal('0.00')
        total_payments = Decimal('0.00')

        for txn in transactions:
            running_balance += txn['charges'] - txn['payments']
            total_charges += txn['charges']
            total_payments += txn['payments']

            charges_str = f"${txn['charges']:,.2f}" if txn['charges'] > 0 else ""
            payments_str = f"${txn['payments']:,.2f}" if txn['payments'] > 0 else ""

            line = f"{txn['date'].strftime('%Y-%m-%d'):<12} {txn['type']:<10} {txn['number']:<12} {txn['description'][:40]:<40} {charges_str:>15} {payments_str:>15} ${running_balance:>14,.2f}"
            self.stdout.write(line)

        # Totals
        self.stdout.write("-" * 120)
        totals_line = f"{'TOTAL':<76} ${total_charges:>14,.2f} ${total_payments:>14,.2f} ${running_balance:>14,.2f}"
        self.stdout.write(totals_line)
        self.stdout.write("=" * 120)
        self.stdout.write()

        # Summary
        current_balance = owner.get_ar_balance()
        self.stdout.write("Account Summary:")
        self.stdout.write(f"  Total Charges:    ${total_charges:>12,.2f}")
        self.stdout.write(f"  Total Payments:   ${total_payments:>12,.2f}")
        self.stdout.write(f"  Current Balance:  ${current_balance:>12,.2f}")
        self.stdout.write()

        # Show unapplied credit if exists
        unapplied_payments = payments.filter(amount_unapplied__gt=0)
        if unapplied_payments.exists():
            self.stdout.write("Unapplied Credits:")
            for payment in unapplied_payments:
                self.stdout.write(f"  {payment.payment_number}: ${payment.amount_unapplied:,.2f}")
            self.stdout.write()

        # Show aging breakdown if there's a balance
        if current_balance > 0:
            unpaid_invoices = Invoice.objects.filter(
                tenant=tenant,
                owner=owner,
                status__in=[Invoice.STATUS_ISSUED, Invoice.STATUS_OVERDUE, Invoice.STATUS_PARTIAL]
            )

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

            self.stdout.write("Aging Breakdown:")
            for bucket, amount in aging.items():
                if amount > 0:
                    self.stdout.write(f"  {bucket:<12} ${amount:>10,.2f}")
            self.stdout.write()

        # Account status
        if current_balance == 0:
            self.stdout.write(self.style.SUCCESS("Account Status: PAID IN FULL"))
        elif current_balance < 0:
            self.stdout.write(self.style.SUCCESS(f"Account Status: CREDIT BALANCE (${abs(current_balance):,.2f})"))
        else:
            # Check if overdue (use due_date comparison instead of days_overdue property)
            overdue_invoices = unpaid_invoices.filter(due_date__lt=today_date.today()) if current_balance > 0 else []
            if overdue_invoices.exists():
                # Calculate days overdue for the oldest invoice
                oldest_days = max([(today_date.today() - inv.due_date).days for inv in overdue_invoices])
                self.stdout.write(self.style.ERROR(f"Account Status: OVERDUE ({oldest_days} days)"))
            else:
                self.stdout.write(self.style.WARNING(f"Account Status: BALANCE DUE"))
