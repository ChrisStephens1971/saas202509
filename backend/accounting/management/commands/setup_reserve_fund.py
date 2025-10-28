"""
Django management command to set up Reserve Fund chart of accounts.

Usage:
    python manage.py setup_reserve_fund --tenant=tenant_sunset_hills
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal

from tenants.models import Tenant
from accounting.models import Fund, Account, AccountType


class Command(BaseCommand):
    help = 'Set up Reserve Fund chart of accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., tenant_sunset_hills)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant_schema = options['tenant']

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{tenant_schema}' does not exist")

        self.stdout.write("=" * 80)
        self.stdout.write(f"RESERVE FUND SETUP - {tenant.name}")
        self.stdout.write("=" * 80)
        self.stdout.write()

        # Create or get Reserve Fund
        reserve_fund, created = Fund.objects.get_or_create(
            tenant=tenant,
            fund_type=Fund.TYPE_RESERVE,
            defaults={
                'name': 'Reserve Fund',
                'description': 'Long-term capital improvements and replacements'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"[OK] Created Reserve Fund"))
        else:
            self.stdout.write(f"[INFO] Reserve Fund already exists")

        # Get account types
        asset_type = AccountType.objects.get(code='ASSET')
        equity_type = AccountType.objects.get(code='EQUITY')
        revenue_type = AccountType.objects.get(code='REVENUE')
        expense_type = AccountType.objects.get(code='EXPENSE')

        # Define Reserve Fund chart of accounts
        reserve_accounts = [
            # Assets (6000-6999)
            {'number': '6100', 'name': 'Reserve Cash', 'type': asset_type},
            {'number': '6200', 'name': 'Reserve Investments (Money Market)', 'type': asset_type},
            {'number': '6210', 'name': 'Reserve Investments (Certificates of Deposit)', 'type': asset_type},

            # Equity (7000-7999)
            {'number': '7100', 'name': 'Reserve Fund Balance', 'type': equity_type},
            {'number': '7200', 'name': 'Designated Reserves (Roofing)', 'type': equity_type},
            {'number': '7300', 'name': 'Designated Reserves (Pavement)', 'type': equity_type},
            {'number': '7400', 'name': 'Designated Reserves (Painting)', 'type': equity_type},

            # Revenue (8000-8999)
            {'number': '8100', 'name': 'Reserve Contributions (Transfer from Operating)', 'type': revenue_type},
            {'number': '8200', 'name': 'Investment Income (Interest)', 'type': revenue_type},
            {'number': '8300', 'name': 'Investment Income (Dividends)', 'type': revenue_type},

            # Expenses (9000-9999)
            {'number': '9100', 'name': 'Roof Replacement', 'type': expense_type},
            {'number': '9200', 'name': 'Pavement Resurfacing', 'type': expense_type},
            {'number': '9300', 'name': 'Elevator Replacement/Repair', 'type': expense_type},
            {'number': '9400', 'name': 'Pool Resurfacing', 'type': expense_type},
            {'number': '9500', 'name': 'Exterior Painting', 'type': expense_type},
            {'number': '9600', 'name': 'Siding Replacement', 'type': expense_type},
            {'number': '9700', 'name': 'HVAC Replacement', 'type': expense_type},
            {'number': '9800', 'name': 'Landscape Renovation', 'type': expense_type},
            {'number': '9900', 'name': 'Other Capital Projects', 'type': expense_type},
        ]

        self.stdout.write()
        self.stdout.write("Creating Reserve Fund Accounts:")
        self.stdout.write("-" * 80)

        accounts_created = 0
        accounts_existing = 0

        for account_def in reserve_accounts:
            account, created = Account.objects.get_or_create(
                tenant=tenant,
                account_number=account_def['number'],
                defaults={
                    'fund': reserve_fund,
                    'account_type': account_def['type'],
                    'name': account_def['name']
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  [OK] {account.account_number} - {account.name}"))
                accounts_created += 1
            else:
                self.stdout.write(f"  [EXISTS] {account.account_number} - {account.name}")
                accounts_existing += 1

        # Summary
        self.stdout.write()
        self.stdout.write("=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Reserve Fund: {reserve_fund.name}")
        self.stdout.write(f"Accounts created: {accounts_created}")
        self.stdout.write(f"Accounts already existing: {accounts_existing}")
        self.stdout.write(f"Total accounts: {len(reserve_accounts)}")
        self.stdout.write()

        # Show account breakdown
        self.stdout.write("Reserve Fund Chart of Accounts:")
        self.stdout.write(f"  Assets (6000-6999):   {len([a for a in reserve_accounts if a['number'].startswith('6')])} accounts")
        self.stdout.write(f"  Equity (7000-7999):   {len([a for a in reserve_accounts if a['number'].startswith('7')])} accounts")
        self.stdout.write(f"  Revenue (8000-8999):  {len([a for a in reserve_accounts if a['number'].startswith('8')])} accounts")
        self.stdout.write(f"  Expenses (9000-9999): {len([a for a in reserve_accounts if a['number'].startswith('9')])} accounts")
        self.stdout.write()

        self.stdout.write(self.style.SUCCESS("Reserve Fund setup completed!"))
        self.stdout.write()
        self.stdout.write("Next steps:")
        self.stdout.write("  1. Transfer funds from Operating to Reserve: Create manual journal entry")
        self.stdout.write("  2. Record investment purchases: DR 6200/6210, CR 6100")
        self.stdout.write("  3. Record investment income: DR 6100, CR 8200/8300")
        self.stdout.write("  4. Record capital expenditures: DR 9xxx, CR 6100")
