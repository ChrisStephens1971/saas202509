"""
Integration Tests for Work Order System Workflow

Tests the complete workflow:
Work Order → Vendor Assignment → Invoice → Journal Entry → GL
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from tenants.models import Tenant
from accounting.models import (
    WorkOrderCategory, Vendor, WorkOrder, WorkOrderInvoice,
    JournalEntry, Account
)
from accounting.services import WorkOrderService

User = get_user_model()


class WorkOrderWorkflowIntegrationTest(TestCase):
    """Test complete work order workflow."""

    def setUp(self):
        """Set up test data."""
        # Create tenant
        self.tenant = Tenant.objects.create(
            schema_name='test_hoa',
            name='Test HOA'
        )

        # Create user
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123'
        )

        # Create GL accounts
        self.expense_account = Account.objects.create(
            tenant=self.tenant,
            account_number='6200',
            name='Repairs & Maintenance',
            account_type='expense'
        )

        self.ap_account = Account.objects.create(
            tenant=self.tenant,
            account_number='2100',
            name='Accounts Payable',
            account_type='liability'
        )

        # Create work order category
        self.category = WorkOrderCategory.objects.create(
            tenant=self.tenant,
            code='HVAC',
            name='HVAC Repairs',
            default_gl_account=self.expense_account
        )

        # Create vendor
        self.vendor = Vendor.objects.create(
            tenant=self.tenant,
            name='ABC Repairs Inc',
            contact_name='Bob Smith',
            email='bob@abcrepairs.com',
            phone='555-1234',
            is_active=True,
            is_preferred=True
        )

    def test_complete_work_order_workflow(self):
        """
        Test complete workflow from work order creation to GL posting.

        Steps:
        1. Create work order
        2. Assign to vendor
        3. Start work
        4. Complete work
        5. Receive invoice
        6. Post invoice to GL
        7. Verify all records
        """
        # Step 1: Create work order
        work_order = WorkOrder.objects.create(
            tenant=self.tenant,
            work_order_number='WO-2025-001',
            title='Replace HVAC Filter',
            description='Annual HVAC filter replacement',
            category=self.category,
            priority='normal',
            status='open',
            estimated_cost=Decimal('150.00'),
            created_by=self.user,
            created_date=date.today()
        )

        self.assertEqual(work_order.status, 'open')

        # Step 2: Assign to vendor
        work_order.assigned_to_vendor = self.vendor
        work_order.status = 'assigned'
        work_order.assigned_date = date.today()
        work_order.save()

        self.assertEqual(work_order.assigned_to_vendor, self.vendor)
        self.assertEqual(work_order.status, 'assigned')

        # Step 3: Start work
        work_order.status = 'in_progress'
        work_order.started_date = date.today()
        work_order.save()

        self.assertEqual(work_order.status, 'in_progress')

        # Step 4: Complete work
        work_order.status = 'completed'
        work_order.completed_date = date.today()
        work_order.actual_cost = Decimal('175.00')  # Slightly over estimate
        work_order.save()

        self.assertEqual(work_order.status, 'completed')

        # Step 5: Receive vendor invoice
        invoice = WorkOrderInvoice.objects.create(
            work_order=work_order,
            vendor=self.vendor,
            invoice_number='INV-12345',
            invoice_date=date.today(),
            amount=Decimal('175.00'),
            description='HVAC filter replacement - completed',
            status='pending'
        )

        self.assertEqual(invoice.status, 'pending')

        # Step 6: Post invoice to GL
        journal_entry = WorkOrderService.post_invoice_to_ledger(
            invoice,
            expense_account=self.expense_account,
            ap_account=self.ap_account
        )

        # Step 7: Verify everything

        # Verify invoice updated
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'posted')
        self.assertEqual(invoice.journal_entry, journal_entry)

        # Verify journal entry created
        self.assertIsNotNone(journal_entry)
        self.assertEqual(journal_entry.status, 'posted')
        self.assertIn('Work Order', journal_entry.description)
        self.assertEqual(journal_entry.reference_number, 'INV-12345')

    def test_cost_variance_calculation(self):
        """Test work order cost variance calculation."""
        work_order = WorkOrder.objects.create(
            tenant=self.tenant,
            work_order_number='WO-2025-002',
            title='Test Work Order',
            category=self.category,
            estimated_cost=Decimal('100.00'),
            actual_cost=Decimal('125.00'),
            status='completed'
        )

        variance = WorkOrderService.calculate_cost_variance(work_order)

        self.assertEqual(variance['estimated_cost'], Decimal('100.00'))
        self.assertEqual(variance['actual_cost'], Decimal('125.00'))
        self.assertEqual(variance['variance'], Decimal('25.00'))
        self.assertEqual(variance['variance_pct'], Decimal('25.00'))
        self.assertEqual(variance['status'], 'over_budget')

    def test_vendor_performance_metrics(self):
        """Test vendor performance calculation."""
        # Create multiple work orders for vendor
        for i in range(3):
            wo = WorkOrder.objects.create(
                tenant=self.tenant,
                work_order_number=f'WO-2025-{i:03d}',
                title=f'Test Work Order {i}',
                category=self.category,
                assigned_to_vendor=self.vendor,
                status='completed',
                started_date=date.today(),
                completed_date=date.today(),
                created_date=date.today()
            )

            WorkOrderInvoice.objects.create(
                work_order=wo,
                vendor=self.vendor,
                invoice_number=f'INV-{i:03d}',
                invoice_date=date.today(),
                amount=Decimal('100.00'),
                status='posted'
            )

        # Get performance metrics
        performance = WorkOrderService.get_vendor_performance(self.vendor)

        self.assertEqual(performance['total_work_orders'], 3)
        self.assertEqual(performance['completed_work_orders'], 3)
        self.assertEqual(performance['completion_rate'], 100.0)
        self.assertEqual(performance['total_amount_paid'], Decimal('300.00'))

    def test_gl_account_assignment(self):
        """Test automatic GL account assignment from category."""
        work_order = WorkOrder.objects.create(
            tenant=self.tenant,
            work_order_number='WO-2025-003',
            title='Test WO',
            category=self.category,
            status='open'
        )

        gl_account = WorkOrderService.assign_gl_account(work_order)

        self.assertEqual(gl_account, self.expense_account)
        self.assertEqual(gl_account.account_number, '6200')

    def test_cannot_post_non_pending_invoice(self):
        """Test that only pending invoices can be posted."""
        work_order = WorkOrder.objects.create(
            tenant=self.tenant,
            work_order_number='WO-2025-004',
            title='Test WO',
            category=self.category,
            status='completed'
        )

        invoice = WorkOrderInvoice.objects.create(
            work_order=work_order,
            vendor=self.vendor,
            invoice_number='INV-999',
            invoice_date=date.today(),
            amount=Decimal('100.00'),
            status='posted'  # Already posted
        )

        with self.assertRaises(ValueError) as context:
            WorkOrderService.post_invoice_to_ledger(invoice)

        self.assertIn('pending', str(context.exception).lower())
