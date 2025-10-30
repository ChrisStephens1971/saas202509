"""
Integration Tests for Violation Tracking Workflow

Tests the complete workflow:
Violation → Escalation → Fine → Invoice → Journal Entry
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from tenants.models import Tenant
from accounting.models import (
    Owner, Unit, ViolationType, FineSchedule, Violation,
    ViolationEscalation, ViolationFine, Invoice, JournalEntry, Account
)
from accounting.services import ViolationService

User = get_user_model()


class ViolationWorkflowIntegrationTest(TestCase):
    """Test complete violation tracking workflow."""

    def setUp(self):
        """Set up test data."""
        # Create tenant
        self.tenant = Tenant.objects.create(
            schema_name='test_hoa',
            name='Test HOA'
        )

        # Create owner and unit
        self.owner = Owner.objects.create(
            tenant=self.tenant,
            first_name='John',
            last_name='Smith',
            email='john@example.com'
        )

        self.unit = Unit.objects.create(
            tenant=self.tenant,
            unit_number='101',
            owner=self.owner
        )

        # Create violation type
        self.violation_type = ViolationType.objects.create(
            tenant=self.tenant,
            code='LAND-001',
            name='Overgrown Lawn',
            category='landscaping',
            description='Grass exceeds 6 inches'
        )

        # Create fine schedule (3-step escalation)
        FineSchedule.objects.create(
            violation_type=self.violation_type,
            step_number=1,
            step_name='Courtesy Notice',
            days_after_previous=0,
            fine_amount=Decimal('0.00')
        )

        FineSchedule.objects.create(
            violation_type=self.violation_type,
            step_number=2,
            step_name='First Warning',
            days_after_previous=7,
            fine_amount=Decimal('50.00')
        )

        FineSchedule.objects.create(
            violation_type=self.violation_type,
            step_number=3,
            step_name='Second Warning',
            days_after_previous=7,
            fine_amount=Decimal('100.00')
        )

        # Create GL accounts
        self.ar_account = Account.objects.create(
            tenant=self.tenant,
            account_number='1200',
            name='Accounts Receivable',
            account_type='asset'
        )

        self.revenue_account = Account.objects.create(
            tenant=self.tenant,
            account_number='4600',
            name='Fine Revenue',
            account_type='revenue'
        )

    def test_complete_violation_workflow(self):
        """
        Test complete workflow from violation creation to GL posting.

        Steps:
        1. Create violation
        2. Escalate to step 1 (courtesy notice, no fine)
        3. Escalate to step 2 (warning + $50 fine)
        4. Post fine to ledger (creates invoice + journal entry)
        5. Verify all records created correctly
        """
        # Step 1: Create violation
        violation = Violation.objects.create(
            tenant=self.tenant,
            owner=self.owner,
            unit=self.unit,
            violation_type=self.violation_type,
            description='Lawn is 8 inches high',
            reported_date=date.today(),
            cure_deadline=date.today() + timedelta(days=14),
            status='open'
        )

        self.assertEqual(violation.status, 'open')

        # Step 2: First escalation (courtesy notice, no fine)
        escalation1, fine1 = ViolationService.escalate_violation(violation)

        self.assertIsNotNone(escalation1)
        self.assertEqual(escalation1.step_number, 1)
        self.assertIsNone(fine1)  # No fine on courtesy notice
        self.assertEqual(violation.status, 'escalated')

        # Step 3: Second escalation (warning + fine)
        violation.refresh_from_db()
        escalation2, fine2 = ViolationService.escalate_violation(violation)

        self.assertIsNotNone(escalation2)
        self.assertEqual(escalation2.step_number, 2)
        self.assertIsNotNone(fine2)
        self.assertEqual(fine2.amount, Decimal('50.00'))
        self.assertEqual(fine2.status, 'pending')

        # Step 4: Post fine to ledger
        invoice, journal_entry = ViolationService.post_fine_to_ledger(
            fine2,
            ar_account=self.ar_account,
            revenue_account=self.revenue_account
        )

        # Step 5: Verify everything was created correctly

        # Verify fine updated
        fine2.refresh_from_db()
        self.assertEqual(fine2.status, 'posted')
        self.assertEqual(fine2.invoice, invoice)
        self.assertEqual(fine2.journal_entry, journal_entry)

        # Verify invoice created
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.owner, self.owner)
        self.assertEqual(invoice.unit, self.unit)
        self.assertEqual(invoice.total_amount, Decimal('50.00'))
        self.assertEqual(invoice.status, 'issued')

        # Verify journal entry created
        self.assertIsNotNone(journal_entry)
        self.assertEqual(journal_entry.status, 'posted')
        self.assertIn('Violation fine', journal_entry.description)

    def test_fine_calculation(self):
        """Test fine amount calculation for each escalation step."""
        # Step 1: No fine
        amount1 = ViolationService.calculate_fine_amount(
            Violation(violation_type=self.violation_type),
            step_number=1
        )
        self.assertEqual(amount1, Decimal('0.00'))

        # Step 2: $50 fine
        amount2 = ViolationService.calculate_fine_amount(
            Violation(violation_type=self.violation_type),
            step_number=2
        )
        self.assertEqual(amount2, Decimal('50.00'))

        # Step 3: $100 fine
        amount3 = ViolationService.calculate_fine_amount(
            Violation(violation_type=self.violation_type),
            step_number=3
        )
        self.assertEqual(amount3, Decimal('100.00'))

    def test_cannot_post_non_pending_fine(self):
        """Test that only pending fines can be posted."""
        violation = Violation.objects.create(
            tenant=self.tenant,
            owner=self.owner,
            unit=self.unit,
            violation_type=self.violation_type,
            description='Test violation',
            reported_date=date.today(),
            cure_deadline=date.today() + timedelta(days=14),
            status='open'
        )

        fine = ViolationFine.objects.create(
            violation=violation,
            amount=Decimal('50.00'),
            fine_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='posted'  # Already posted
        )

        with self.assertRaises(ValueError) as context:
            ViolationService.post_fine_to_ledger(fine)

        self.assertIn('pending', str(context.exception).lower())
