"""
Django management command to onboard a new HOA tenant.

This command sets up everything needed for a new tenant:
1. Create tenant record
2. Create tenant admin user
3. Set up default fund structure (Operating + Reserve)
4. Create chart of accounts
5. Assign admin user to tenant with admin role

Usage:
    python manage.py onboard_tenant \
        --name="Sunset Hills HOA" \
        --schema="tenant_sunset_hills_2" \
        --admin-email="admin@sunsethills.com" \
        --admin-name="John Smith"
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from tenants.models import Tenant
from accounting.models import (
    Fund, Account, AccountType, UserTenantMembership
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Onboard a new HOA tenant with complete setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Tenant name (e.g., "Sunset Hills HOA")',
        )
        parser.add_argument(
            '--schema',
            type=str,
            required=True,
            help='Tenant schema name (e.g., "tenant_sunset_hills")',
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            required=True,
            help='Admin user email',
        )
        parser.add_argument(
            '--admin-name',
            type=str,
            required=True,
            help='Admin user full name (e.g., "John Smith")',
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            help='Admin username (defaults to email)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without creating anything',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant_name = options['name']
        schema_name = options['schema']
        admin_email = options['admin_email']
        admin_name = options['admin_name']
        admin_username = options.get('admin_username') or admin_email
        dry_run = options['dry_run']

        self.stdout.write('=' * 80)
        self.stdout.write('TENANT ONBOARDING')
        self.stdout.write('=' * 80)
        self.stdout.write(f'Tenant Name: {tenant_name}')
        self.stdout.write(f'Schema Name: {schema_name}')
        self.stdout.write(f'Admin Email: {admin_email}')
        self.stdout.write(f'Admin Name: {admin_name}')
        self.stdout.write(f'Mode: {"DRY RUN" if dry_run else "LIVE"}')
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')
            self.stdout.write('Would create:')
            self.stdout.write(f'  1. Tenant: {tenant_name} ({schema_name})')
            self.stdout.write(f'  2. Admin user: {admin_name} ({admin_email})')
            self.stdout.write('  3. Operating Fund')
            self.stdout.write('  4. Reserve Fund')
            self.stdout.write('  5. Chart of Accounts (15+ accounts)')
            self.stdout.write(f'  6. User-Tenant membership (Admin role)')
            return

        # 1. Create tenant
        self.stdout.write('Step 1: Creating tenant...')
        if Tenant.objects.filter(schema_name=schema_name).exists():
            raise CommandError(f'Tenant with schema "{schema_name}" already exists')

        tenant = Tenant.objects.create(
            name=tenant_name,
            schema_name=schema_name,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created tenant: {tenant.name}'))

        # 2. Create admin user
        self.stdout.write('\nStep 2: Creating admin user...')
        first_name, last_name = self._parse_name(admin_name)

        user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': False,
                'is_active': True,
            }
        )

        if created:
            # Set temporary password
            temp_password = User.objects.make_random_password(length=12)
            user.set_password(temp_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created user: {user.username}'))
            self.stdout.write(self.style.WARNING(f'  ⚠ Temporary password: {temp_password}'))
            self.stdout.write(self.style.WARNING('    (Send this to the admin securely)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Using existing user: {user.username}'))

        # 3. Create default funds
        self.stdout.write('\nStep 3: Creating default funds...')

        operating_fund = Fund.objects.create(
            tenant=tenant,
            name='Operating Fund',
            fund_type=Fund.TYPE_OPERATING,
            description='Primary operating fund for day-to-day expenses',
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {operating_fund.name}'))

        reserve_fund = Fund.objects.create(
            tenant=tenant,
            name='Reserve Fund',
            fund_type=Fund.TYPE_RESERVE,
            description='Capital reserve fund for major repairs and replacements',
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {reserve_fund.name}'))

        # 4. Create chart of accounts
        self.stdout.write('\nStep 4: Creating chart of accounts...')
        accounts_created = self._create_chart_of_accounts(tenant, operating_fund, reserve_fund)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(accounts_created)} accounts'))

        # 5. Create user-tenant membership
        self.stdout.write('\nStep 5: Creating admin membership...')
        membership = UserTenantMembership.objects.create(
            user=user,
            tenant=tenant,
            role=UserTenantMembership.ROLE_ADMIN,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Assigned {user.username} as Tenant Admin'))

        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('ONBOARDING COMPLETE')
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS(f'Tenant "{tenant.name}" is ready to use!'))
        self.stdout.write('')
        self.stdout.write('Created:')
        self.stdout.write(f'  - Tenant: {tenant.name}')
        self.stdout.write(f'  - Admin: {user.email}')
        self.stdout.write(f'  - Funds: 2 (Operating + Reserve)')
        self.stdout.write(f'  - Accounts: {len(accounts_created)}')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Send admin credentials securely')
        self.stdout.write('  2. Configure units and owners')
        self.stdout.write('  3. Set up monthly assessment amounts')
        self.stdout.write('  4. Configure email settings')

    def _parse_name(self, full_name):
        """Parse full name into first and last name"""
        parts = full_name.strip().split(' ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return parts[0], ''

    def _create_chart_of_accounts(self, tenant, operating_fund, reserve_fund):
        """Create default HOA chart of accounts"""
        accounts = []

        # Asset accounts (1000-1999)
        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='1100',
            name='Operating Cash',
            account_type=AccountType.ASSET,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='1200',
            name='Accounts Receivable',
            account_type=AccountType.ASSET,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=reserve_fund,
            account_number='6100',
            name='Reserve Cash',
            account_type=AccountType.ASSET,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        # Liability accounts (2000-2999)
        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='2100',
            name='Accounts Payable',
            account_type=AccountType.LIABILITY,
            normal_balance=Account.CREDIT,
            is_active=True
        ))

        # Equity accounts (3000-3999)
        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='3100',
            name='Fund Balance',
            account_type=AccountType.EQUITY,
            normal_balance=Account.CREDIT,
            is_active=True
        ))

        # Revenue accounts (4000-4999)
        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='4100',
            name='Assessment Revenue',
            account_type=AccountType.REVENUE,
            normal_balance=Account.CREDIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='4200',
            name='Late Fee Revenue',
            account_type=AccountType.REVENUE,
            normal_balance=Account.CREDIT,
            is_active=True
        ))

        # Expense accounts (5000-5999)
        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='5100',
            name='Landscape Maintenance',
            account_type=AccountType.EXPENSE,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='5200',
            name='Utilities',
            account_type=AccountType.EXPENSE,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='5300',
            name='Insurance',
            account_type=AccountType.EXPENSE,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='5400',
            name='Management Fees',
            account_type=AccountType.EXPENSE,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        accounts.append(Account.objects.create(
            tenant=tenant,
            fund=operating_fund,
            account_number='5500',
            name='Repairs and Maintenance',
            account_type=AccountType.EXPENSE,
            normal_balance=Account.DEBIT,
            is_active=True
        ))

        return accounts
