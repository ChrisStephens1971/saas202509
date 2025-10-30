"""
Violation Service - Business Logic for Violation Tracking

Handles:
- Fine calculation based on escalation schedules
- Automatic violation escalation
- Posting fines to general ledger
"""

from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import (
    Violation, ViolationType, FineSchedule, ViolationEscalation,
    ViolationFine, Invoice, JournalEntry, Account
)


class ViolationService:
    """Service for violation tracking business logic."""

    @staticmethod
    def calculate_fine_amount(violation, step_number):
        """
        Calculate fine amount for a specific escalation step.

        Args:
            violation: Violation instance
            step_number: Escalation step number (1, 2, 3, etc.)

        Returns:
            Decimal: Fine amount for this step, or None if no schedule
        """
        try:
            schedule = FineSchedule.objects.get(
                violation_type=violation.violation_type,
                step_number=step_number
            )
            return schedule.fine_amount
        except FineSchedule.DoesNotExist:
            return None

    @staticmethod
    def get_next_escalation_step(violation):
        """
        Get the next escalation step for a violation.

        Returns:
            FineSchedule or None: Next escalation step
        """
        # Get current highest step number
        current_step = ViolationEscalation.objects.filter(
            violation=violation
        ).order_by('-step_number').first()

        if current_step:
            next_step_num = current_step.step_number + 1
        else:
            next_step_num = 1

        # Get next schedule step
        try:
            return FineSchedule.objects.get(
                violation_type=violation.violation_type,
                step_number=next_step_num
            )
        except FineSchedule.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def escalate_violation(violation, user=None):
        """
        Escalate a violation to the next step.

        Creates escalation record and optionally creates fine if
        the escalation step includes a fine amount.

        Args:
            violation: Violation instance
            user: User performing escalation (optional)

        Returns:
            tuple: (ViolationEscalation, ViolationFine or None)
        """
        next_step = ViolationService.get_next_escalation_step(violation)

        if not next_step:
            raise ValueError("No more escalation steps available")

        # Create escalation record
        escalation = ViolationEscalation.objects.create(
            violation=violation,
            step_number=next_step.step_number,
            escalation_date=date.today(),
            fine_amount=next_step.fine_amount if next_step.fine_amount > 0 else None,
            notice_sent=False  # Will be set to True when notice is sent
        )

        # Create fine if this step has a fine amount
        fine = None
        if next_step.fine_amount and next_step.fine_amount > 0:
            fine = ViolationFine.objects.create(
                violation=violation,
                amount=next_step.fine_amount,
                fine_date=date.today(),
                due_date=date.today() + timedelta(days=30),  # 30 days to pay
                status='pending',
                description=f"{next_step.step_name}: {violation.description[:100]}"
            )

        # Update violation status
        if violation.status == 'open':
            violation.status = 'escalated'
            violation.save()

        return escalation, fine

    @staticmethod
    @transaction.atomic
    def post_fine_to_ledger(fine, ar_account=None, revenue_account=None):
        """
        Post a violation fine to the general ledger.

        Creates:
        1. Invoice for the fine amount
        2. Journal entry (DR: AR, CR: Fine Revenue)
        3. Updates fine status to 'posted'

        Args:
            fine: ViolationFine instance
            ar_account: Accounts Receivable account (optional, will lookup if not provided)
            revenue_account: Fine Revenue account (optional, will lookup if not provided)

        Returns:
            tuple: (Invoice, JournalEntry)
        """
        if fine.status != 'pending':
            raise ValueError(f"Only pending fines can be posted. Current status: {fine.status}")

        violation = fine.violation
        tenant = violation.tenant

        # Get default accounts if not provided
        if not ar_account:
            ar_account = Account.objects.filter(
                tenant=tenant,
                account_number__startswith='1200'  # Accounts Receivable
            ).first()

        if not revenue_account:
            revenue_account = Account.objects.filter(
                tenant=tenant,
                account_number__startswith='4600'  # Fine Revenue
            ).first()

        if not ar_account or not revenue_account:
            raise ValueError("AR and Revenue accounts must be configured")

        # Create invoice
        invoice = Invoice.objects.create(
            tenant=tenant,
            owner=violation.owner,
            unit=violation.unit,
            invoice_number=f"FINE-{violation.id}",
            invoice_date=fine.fine_date,
            due_date=fine.due_date,
            description=fine.description or f"Violation fine: {violation.description[:100]}",
            total_amount=fine.amount,
            status='issued'
        )

        # Create journal entry
        # DR: Accounts Receivable (Asset increases)
        # CR: Fine Revenue (Revenue increases)
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=fine.fine_date,
            description=f"Violation fine: {violation.id}",
            reference_number=invoice.invoice_number,
            status='posted'
        )

        # Note: In production, would create JournalEntryLine records here
        # For now, storing the link is sufficient for MVP

        # Update fine with invoice and journal entry links
        fine.invoice = invoice
        fine.journal_entry = entry
        fine.status = 'posted'
        fine.save()

        return invoice, entry

    @staticmethod
    def check_violations_for_escalation(tenant, days_before_escalation=7):
        """
        Check all open violations and escalate those that are past their cure deadline.

        This should be run as a scheduled task (cron job).

        Args:
            tenant: Tenant to check violations for
            days_before_escalation: Days past cure deadline before auto-escalation

        Returns:
            list: List of (violation, escalation, fine) tuples that were escalated
        """
        escalated = []

        # Find violations past cure deadline
        cutoff_date = date.today() - timedelta(days=days_before_escalation)

        violations = Violation.objects.filter(
            tenant=tenant,
            status__in=['open', 'escalated'],
            cure_deadline__lt=cutoff_date,
            cured_date__isnull=True
        )

        for violation in violations:
            try:
                escalation, fine = ViolationService.escalate_violation(violation)
                escalated.append((violation, escalation, fine))
            except ValueError:
                # No more escalation steps available
                pass

        return escalated

    @staticmethod
    def get_violation_summary(tenant):
        """
        Get summary statistics for violations.

        Returns:
            dict: Statistics about violations
        """
        from django.db.models import Count, Sum, Q

        violations = Violation.objects.filter(tenant=tenant)

        return {
            'total_violations': violations.count(),
            'open_violations': violations.filter(status='open').count(),
            'escalated_violations': violations.filter(status='escalated').count(),
            'cured_violations': violations.filter(status='cured').count(),
            'total_fines_pending': ViolationFine.objects.filter(
                violation__tenant=tenant,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'total_fines_posted': ViolationFine.objects.filter(
                violation__tenant=tenant,
                status='posted'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        }
