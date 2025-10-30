"""
Management Command: Escalate Overdue Violations

Automatically escalates violations that are past their cure deadline.

Usage:
    python manage.py escalate_overdue_violations

Schedule:
    Run daily via cron job (e.g., 6:00 AM daily)

Process:
    1. Find all violations with status 'open' or 'escalated'
    2. Check if cure_deadline has passed
    3. Auto-escalate with fine amount from violation type
    4. Send notification to owner
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from accounting.models import Violation, ViolationEscalation
from accounting.services import NotificationService
from datetime import date


class Command(BaseCommand):
    help = 'Escalate violations that are past their cure deadline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be escalated without actually escalating',
        )
        parser.add_argument(
            '--days-grace',
            type=int,
            default=0,
            help='Number of grace days after cure deadline before escalating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        grace_days = options['days_grace']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('VIOLATION AUTO-ESCALATION TASK'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Run Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'Mode: {"DRY RUN" if dry_run else "LIVE"}')
        self.stdout.write(f'Grace Days: {grace_days}')
        self.stdout.write('')

        # Calculate cutoff date (cure deadline must be before this)
        today = date.today()

        # Find overdue violations
        overdue_violations = Violation.objects.filter(
            status__in=['open', 'escalated'],
            cure_deadline__lt=today
        ).select_related('owner', 'unit', 'violation_type', 'tenant')

        if not overdue_violations.exists():
            self.stdout.write(self.style.SUCCESS('✓ No overdue violations found'))
            return

        self.stdout.write(f'Found {overdue_violations.count()} overdue violation(s)')
        self.stdout.write('')

        escalated_count = 0
        error_count = 0

        for violation in overdue_violations:
            days_overdue = (today - violation.cure_deadline).days

            # Apply grace period
            if days_overdue < grace_days:
                self.stdout.write(
                    f'  ⏳ {violation.violation_number} - '
                    f'Overdue by {days_overdue} days (within grace period)'
                )
                continue

            # Check if already escalated recently (prevent duplicate escalations on same day)
            last_escalation = ViolationEscalation.objects.filter(
                violation=violation
            ).order_by('-escalation_date').first()

            if last_escalation and last_escalation.escalation_date == today:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ {violation.violation_number} - '
                        f'Already escalated today, skipping'
                    )
                )
                continue

            # Calculate next escalation step
            current_step = ViolationEscalation.objects.filter(
                violation=violation
            ).count()
            next_step = current_step + 1

            # Get fine amount from violation type (escalate_fine_1, escalate_fine_2, etc.)
            fine_amount = self._get_escalation_fine_amount(violation, next_step)

            self.stdout.write(
                f'  → {violation.violation_number} - '
                f'Unit {violation.unit.unit_number} - '
                f'Step {next_step} - '
                f'Fine: ${fine_amount} - '
                f'Overdue by {days_overdue} days'
            )

            if not dry_run:
                try:
                    with transaction.atomic():
                        # Create escalation
                        escalation = ViolationEscalation.objects.create(
                            violation=violation,
                            step_number=next_step,
                            escalation_date=today,
                            fine_amount=fine_amount,
                            notes='Auto-escalated: Cure deadline passed',
                            created_by='system'
                        )

                        # Update violation status
                        violation.status = 'escalated'
                        violation.save()

                        # Send notification
                        try:
                            NotificationService.notify_violation_escalated(
                                violation=violation,
                                escalation=escalation
                            )
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'    ✓ Escalated and notification sent'
                                )
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    ⚠ Escalated but notification failed: {str(e)}'
                                )
                            )

                        escalated_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'    ✗ Failed to escalate: {str(e)}'
                        )
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('SUMMARY')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Total Overdue: {overdue_violations.count()}')

        if dry_run:
            self.stdout.write(f'Would Escalate: {escalated_count}')
        else:
            self.stdout.write(self.style.SUCCESS(f'Escalated: {escalated_count}'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))

        self.stdout.write('')

    def _get_escalation_fine_amount(self, violation, step_number):
        """
        Get the fine amount for the given escalation step.

        Looks for escalate_fine_1, escalate_fine_2, escalate_fine_3
        on the violation type. Falls back to base fine amount.
        """
        violation_type = violation.violation_type

        # Try to get step-specific fine (escalate_fine_1, escalate_fine_2, etc.)
        fine_field = f'escalate_fine_{step_number}'
        fine_amount = getattr(violation_type, fine_field, None)

        if fine_amount:
            return fine_amount

        # Fall back to base fine amount
        if violation_type.fine_amount:
            return violation_type.fine_amount

        # Default fine if no amount specified
        return 50.00
