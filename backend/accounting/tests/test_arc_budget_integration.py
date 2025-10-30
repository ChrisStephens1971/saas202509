"""
Integration Tests for ARC Workflow and Budget Tracking

Tests:
- ARC Request approval workflow
- Budget variance calculation
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from tenants.models import Tenant
from accounting.models import (
    Owner, Unit, ARCRequestType, ARCRequest, ARCReview, ARCApproval,
    Budget, BudgetLine, Account
)
from accounting.services import BudgetService

User = get_user_model()


class ARCWorkflowIntegrationTest(TestCase):
    """Test ARC request approval workflow."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            schema_name='test_hoa',
            name='Test HOA'
        )

        self.owner = Owner.objects.create(
            tenant=self.tenant,
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com'
        )

        self.unit = Unit.objects.create(
            tenant=self.tenant,
            unit_number='201',
            owner=self.owner
        )

        self.request_type = ARCRequestType.objects.create(
            tenant=self.tenant,
            code='PAINT',
            name='Exterior Paint',
            requires_plans=False,
            requires_contractor=True
        )

        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com'
        )

        self.approver = User.objects.create_user(
            username='approver',
            email='approver@example.com'
        )

    def test_complete_arc_approval_workflow(self):
        """
        Test complete ARC workflow from submission to approval.

        Steps:
        1. Owner submits request (draft)
        2. Request is submitted for review
        3. Committee member reviews
        4. Final approval is issued
        5. Verify status transitions
        """
        # Step 1: Create draft request
        arc_request = ARCRequest.objects.create(
            tenant=self.tenant,
            unit=self.unit,
            owner=self.owner,
            request_type=self.request_type,
            project_description='Repaint front door from white to blue',
            status='draft',
            submitted_by=self.owner.user if hasattr(self.owner, 'user') else None
        )

        self.assertEqual(arc_request.status, 'draft')

        # Step 2: Submit for review
        arc_request.status = 'submitted'
        arc_request.submission_date = date.today()
        arc_request.save()

        self.assertEqual(arc_request.status, 'submitted')

        # Step 3: Assign to reviewer
        arc_request.assigned_to = self.reviewer
        arc_request.status = 'under_review'
        arc_request.save()

        # Committee member reviews
        review = ARCReview.objects.create(
            request=arc_request,
            reviewer=self.reviewer,
            review_date=date.today(),
            decision='approved',
            comments='Blue color is within approved palette. Approved.'
        )

        self.assertEqual(review.decision, 'approved')

        # Step 4: Final approval
        approval = ARCApproval.objects.create(
            request=arc_request,
            final_decision='approved',
            approval_date=date.today(),
            approved_by=self.approver,
            conditions='Must use Benjamin Moore paint. Submit completion photos.'
        )

        # Update request status
        arc_request.status = 'approved'
        arc_request.save()

        # Verify final state
        arc_request.refresh_from_db()
        self.assertEqual(arc_request.status, 'approved')
        self.assertIsNotNone(arc_request.approval)
        self.assertEqual(arc_request.approval.final_decision, 'approved')

    def test_conditional_approval(self):
        """Test ARC request with conditional approval."""
        arc_request = ARCRequest.objects.create(
            tenant=self.tenant,
            unit=self.unit,
            owner=self.owner,
            request_type=self.request_type,
            project_description='Install solar panels',
            status='submitted',
            submission_date=date.today()
        )

        approval = ARCApproval.objects.create(
            request=arc_request,
            final_decision='conditional',
            approval_date=date.today(),
            approved_by=self.approver,
            conditions='Must be installed by licensed contractor. Must submit warranty documentation.',
            expiration_date=date.today().replace(year=date.today().year + 1)
        )

        arc_request.status = 'conditional_approval'
        arc_request.save()

        self.assertEqual(arc_request.status, 'conditional_approval')
        self.assertIsNotNone(approval.conditions)
        self.assertIsNotNone(approval.expiration_date)


class BudgetTrackingIntegrationTest(TestCase):
    """Test budget variance calculation and tracking."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            schema_name='test_hoa',
            name='Test HOA'
        )

        # Create GL accounts
        self.maintenance_account = Account.objects.create(
            tenant=self.tenant,
            account_number='6200',
            name='Repairs & Maintenance',
            account_type='expense'
        )

        self.utilities_account = Account.objects.create(
            tenant=self.tenant,
            account_number='6300',
            name='Utilities',
            account_type='expense'
        )

        # Create budget
        self.budget = Budget.objects.create(
            tenant=self.tenant,
            name='2025 Operating Budget',
            fiscal_year=2025,
            is_approved=True
        )

        # Create budget lines
        BudgetLine.objects.create(
            budget=self.budget,
            account=self.maintenance_account,
            budgeted_amount=Decimal('12000.00'),
            notes='Monthly: $1,000'
        )

        BudgetLine.objects.create(
            budget=self.budget,
            account=self.utilities_account,
            budgeted_amount=Decimal('6000.00'),
            notes='Monthly: $500'
        )

    def test_variance_calculation(self):
        """Test budget variance calculation."""
        variance_data = BudgetService.calculate_variance(self.budget)

        self.assertEqual(len(variance_data), 2)

        # Check structure of variance data
        for item in variance_data:
            self.assertIn('budget_line', item)
            self.assertIn('account', item)
            self.assertIn('budgeted_amount', item)
            self.assertIn('actual_amount', item)
            self.assertIn('variance', item)
            self.assertIn('variance_pct', item)
            self.assertIn('status', item)

        # Verify budgeted amounts
        maintenance_item = next(i for i in variance_data if i['account'] == self.maintenance_account)
        self.assertEqual(maintenance_item['budgeted_amount'], Decimal('12000.00'))

    def test_budget_creation_from_template(self):
        """Test creating a new budget from previous year template."""
        # Create 2026 budget based on 2025
        new_budget = BudgetService.create_budget_from_template(
            tenant=self.tenant,
            fiscal_year=2026,
            template_budget=self.budget,
            increase_pct=3  # 3% increase
        )

        self.assertEqual(new_budget.fiscal_year, 2026)
        self.assertEqual(new_budget.budget_lines.count(), 2)

        # Verify amounts increased by 3%
        maintenance_line = new_budget.budget_lines.get(account=self.maintenance_account)
        expected_amount = Decimal('12000.00') * Decimal('1.03')
        self.assertEqual(maintenance_line.budgeted_amount, expected_amount)

    def test_budget_alerts(self):
        """Test budget alert generation for variances over threshold."""
        # This test would work better with actual spending data
        # For now, verify the function works
        alerts = BudgetService.get_budget_alerts(
            self.budget,
            threshold_pct=10
        )

        # Should return a list (empty in this case as no actual spending)
        self.assertIsInstance(alerts, list)

    def test_budget_summary(self):
        """Test budget summary statistics."""
        summary = BudgetService.get_budget_summary(self.tenant)

        self.assertEqual(summary['total_budgets'], 1)
        self.assertEqual(summary['active_budgets'], 1)
        self.assertEqual(summary['current_fiscal_year'], date.today().year)
        self.assertEqual(len(summary['budgets']), 1)

        budget_info = summary['budgets'][0]
        self.assertEqual(budget_info['fiscal_year'], 2025)
        self.assertTrue(budget_info['is_approved'])
        self.assertEqual(budget_info['total_budgeted'], Decimal('18000.00'))
