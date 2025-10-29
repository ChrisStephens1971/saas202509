"""
Django management command to assess late fees for delinquent accounts.

Run daily via cron: 0 1 * * * python manage.py assess_late_fees
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from tenants.models import Tenant
from accounting.models import (
    DelinquencyStatus, LateFeeRule, Invoice, InvoiceLine, Owner, Account, Unit
)


class Command(BaseCommand):
    help = 'Assess late fees for delinquent accounts past grace period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Process only specific tenant (UUID)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate without creating invoices',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        # Get tenants to process
        if tenant_id:
            tenants = Tenant.objects.filter(id=tenant_id)
            if not tenants.exists():
                self.stdout.write(self.style.ERROR(f'Tenant {tenant_id} not found'))
                return
        else:
            tenants = Tenant.objects.filter(is_active=True)

        total_fees_assessed = 0
        total_accounts_processed = 0

        for tenant in tenants:
            if verbose:
                self.stdout.write(f'\nProcessing tenant: {tenant.name} ({tenant.id})')

            fees_assessed, accounts_processed = self.process_tenant(
                tenant, dry_run, verbose
            )

            total_fees_assessed += fees_assessed
            total_accounts_processed += accounts_processed

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would assess late fees for {total_accounts_processed} accounts '
                    f'totaling ${total_fees_assessed:.2f}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully assessed late fees for {total_accounts_processed} accounts '
                    f'totaling ${total_fees_assessed:.2f}'
                )
            )

    def process_tenant(self, tenant, dry_run, verbose):
        """Process late fee assessment for a single tenant"""
        fees_assessed = Decimal('0.00')
        accounts_processed = 0

        # Find delinquent accounts past grace period
        today = date.today()

        # Get active late fee rules for this tenant
        active_rules = LateFeeRule.objects.filter(
            tenant=tenant,
            is_active=True
        )

        if not active_rules.exists():
            if verbose:
                self.stdout.write(
                    self.style.WARNING(f'  No active late fee rules for {tenant.name}')
                )
            return fees_assessed, accounts_processed

        # Get all delinquent statuses past grace period
        delinquent_statuses = DelinquencyStatus.objects.filter(
            tenant=tenant,
            is_delinquent=True
        ).select_related('owner')

        for status in delinquent_statuses:
            # Check if we've already assessed a late fee recently
            if status.last_late_fee_date:
                # Determine assessment frequency from rule
                rule = self.get_applicable_rule(status, active_rules)
                if rule and rule.is_recurring:
                    # Check if enough time has passed (typically 30 days)
                    days_since_last = (today - status.last_late_fee_date).days
                    if days_since_last < 30:
                        if verbose:
                            self.stdout.write(
                                f'  Skipping {status.owner.full_name}: '
                                f'Last fee {days_since_last} days ago'
                            )
                        continue
                else:
                    # Non-recurring, already assessed
                    if verbose:
                        self.stdout.write(
                            f'  Skipping {status.owner.full_name}: '
                            f'Non-recurring fee already assessed'
                        )
                    continue

            # Check grace period
            grace_days = self.get_grace_days(active_rules)
            if status.days_delinquent < grace_days:
                if verbose:
                    self.stdout.write(
                        f'  Skipping {status.owner.full_name}: '
                        f'Within grace period ({status.days_delinquent}/{grace_days} days)'
                    )
                continue

            # Get applicable late fee rule
            rule = self.get_applicable_rule(status, active_rules)
            if not rule:
                if verbose:
                    self.stdout.write(
                        f'  Skipping {status.owner.full_name}: No applicable rule'
                    )
                continue

            # Calculate late fee
            late_fee = rule.calculate_fee(status.total_balance)

            if late_fee <= Decimal('0.00'):
                if verbose:
                    self.stdout.write(
                        f'  Skipping {status.owner.full_name}: Fee calculated as $0.00'
                    )
                continue

            # Create invoice for late fee
            if not dry_run:
                self.create_late_fee_invoice(
                    tenant=tenant,
                    owner=status.owner,
                    amount=late_fee,
                    rule=rule,
                    delinquency_status=status
                )

                # Update delinquency status
                status.last_late_fee_date = today
                status.last_late_fee_amount = late_fee
                status.save()

            fees_assessed += late_fee
            accounts_processed += 1

            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Assessed ${late_fee:.2f} late fee for {status.owner.full_name} '
                        f'(Balance: ${status.total_balance:.2f}, Days: {status.days_delinquent})'
                    )
                )

        return fees_assessed, accounts_processed

    def get_grace_days(self, rules):
        """Get grace period from rules (use minimum if multiple)"""
        grace_days = [rule.grace_period_days for rule in rules if rule.grace_period_days]
        return min(grace_days) if grace_days else 0

    def get_applicable_rule(self, status, rules):
        """
        Get the applicable late fee rule for this delinquency status.
        Priority: specific balance thresholds, then default rule.
        """
        # For now, use the first active rule
        # In a more sophisticated system, you could have balance tiers, etc.
        return rules.first() if rules.exists() else None

    @transaction.atomic
    def create_late_fee_invoice(self, tenant, owner, amount, rule, delinquency_status):
        """Create an invoice for the late fee"""
        # Get or create late fee income account
        late_fee_account, created = Account.objects.get_or_create(
            tenant=tenant,
            account_type='revenue',
            name='Late Fee Income',
            defaults={
                'account_number': '4100',
                'description': 'Income from late fees assessed on delinquent accounts'
            }
        )

        # Get owner's primary unit (or first unit)
        unit = owner.units.first()
        if not unit:
            # Create a default unit if owner doesn't have one
            unit = Unit.objects.create(
                tenant=tenant,
                unit_number=owner.property_address or 'UNKNOWN',
                owner=owner
            )

        # Create invoice
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=owner,
            unit=unit,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            invoice_type=Invoice.TYPE_LATE_FEE,
            status=Invoice.STATUS_ISSUED,
            description=f'Late Fee - {rule.fee_type_display} (Delinquent {delinquency_status.days_delinquent} days)',
            subtotal=amount,
            total_amount=amount,
            amount_due=amount
        )

        # Create invoice line
        InvoiceLine.objects.create(
            invoice=invoice,
            line_number=1,
            description=f'Late Fee Assessment - Delinquent {delinquency_status.days_delinquent} days',
            account=late_fee_account,
            amount=amount
        )

        self.stdout.write(
            f'  Created invoice {invoice.invoice_number} for ${amount:.2f}'
        )

        return invoice
