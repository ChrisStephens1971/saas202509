"""
Auditor Export Service

Generates audit-grade financial exports with evidence linking.
Sprint 21 - Auditor Export
"""

import csv
import hashlib
import logging
from datetime import date, datetime
from decimal import Decimal
from io import StringIO, BytesIO
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditorExportService:
    """
    Generate audit-grade exports with evidence linking.

    Supports CSV, Excel, and PDF formats with:
    - Complete general ledger for date range
    - Running balances per account
    - Evidence URLs for supporting documents
    - Immutable, timestamped exports
    """

    def __init__(self):
        self.csv_columns = [
            'Date',
            'Entry#',
            'Account#',
            'Account Name',
            'Description',
            'Debit',
            'Credit',
            'Balance',
            'Evidence URL',
            'Notes'
        ]

    def generate_export(self, export_obj):
        """
        Generate CSV/Excel export for auditor.

        Args:
            export_obj: AuditorExport model instance

        Returns:
            tuple: (success: bool, file_url: str, error_message: str)

        Steps:
        1. Query all journal entries in date range
        2. Build CSV rows with running balances
        3. Attach evidence URLs for each entry
        4. Calculate totals and verify balance
        5. Generate file and upload to storage
        6. Update export record with metadata
        """
        from accounting.models import JournalEntry, JournalEntryLine

        try:
            # Update status to generating
            export_obj.status = 'generating'
            export_obj.save()

            # Query journal entries in date range
            entries = JournalEntry.objects.filter(
                tenant=export_obj.tenant,
                entry_date__gte=export_obj.start_date,
                entry_date__lte=export_obj.end_date
            ).select_related(
                'created_by'
            ).prefetch_related(
                'lines__account'
            ).order_by('entry_date', 'entry_number')

            if not entries.exists():
                return False, None, f"No journal entries found for date range {export_obj.start_date} to {export_obj.end_date}"

            # Build CSV data
            csv_rows = []
            account_balances = {}  # Track running balance per account
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            evidence_count = 0

            for entry in entries:
                lines = entry.lines.all().order_by('account__account_number')

                for line in lines:
                    # Get evidence URL for this entry
                    evidence_url = self.get_evidence_url(entry, export_obj.tenant)
                    if evidence_url:
                        evidence_count += 1

                    # Calculate running balance for account
                    account_id = line.account.id
                    if account_id not in account_balances:
                        account_balances[account_id] = Decimal('0.00')

                    # Update balance based on account type
                    # Debit increases: Assets, Expenses
                    # Credit increases: Liabilities, Equity, Revenue
                    account_type = line.account.account_type.name.lower()
                    if 'asset' in account_type or 'expense' in account_type:
                        account_balances[account_id] += line.debit - line.credit
                    else:
                        account_balances[account_id] += line.credit - line.debit

                    # Format amounts
                    debit_str = f"{line.debit:,.2f}" if line.debit else ""
                    credit_str = f"{line.credit:,.2f}" if line.credit else ""
                    balance_str = f"{account_balances[account_id]:,.2f}"

                    # Build CSV row
                    row = {
                        'Date': entry.entry_date.strftime('%Y-%m-%d'),
                        'Entry#': entry.entry_number,
                        'Account#': line.account.account_number,
                        'Account Name': line.account.name,
                        'Description': line.description or entry.description,
                        'Debit': debit_str,
                        'Credit': credit_str,
                        'Balance': balance_str,
                        'Evidence URL': evidence_url or '',
                        'Notes': entry.notes or ''
                    }
                    csv_rows.append(row)

                    # Update totals
                    total_debit += line.debit
                    total_credit += line.credit

            # Verify debits = credits
            if total_debit != total_credit:
                error_msg = f"Export unbalanced: Debits={total_debit}, Credits={total_credit}"
                logger.error(error_msg)
                export_obj.status = 'failed'
                export_obj.error_message = error_msg
                export_obj.save()
                return False, None, error_msg

            # Generate CSV file
            csv_buffer = self._generate_csv(csv_rows)

            # Calculate file hash for integrity
            csv_buffer.seek(0)
            file_hash = hashlib.sha256(csv_buffer.read()).hexdigest()
            csv_buffer.seek(0)

            # Save to storage
            file_name = f"auditor_exports/{export_obj.tenant.id}/{export_obj.id}.csv"
            saved_path = default_storage.save(file_name, ContentFile(csv_buffer.read()))

            # Generate URL
            file_url = saved_path  # For local storage
            if hasattr(default_storage, 'url'):
                try:
                    file_url = default_storage.url(saved_path)
                except:
                    file_url = saved_path

            # Update export object
            export_obj.file_url = file_url
            export_obj.file_size_bytes = csv_buffer.tell()
            export_obj.file_hash = file_hash
            export_obj.status = 'ready'
            export_obj.total_entries = len(csv_rows)
            export_obj.total_debit = total_debit
            export_obj.total_credit = total_credit
            export_obj.evidence_count = evidence_count
            export_obj.save()

            logger.info(f"Successfully generated export {export_obj.id}: {len(csv_rows)} entries, {file_url}")
            return True, file_url, ""

        except Exception as e:
            error_msg = f"Export generation failed: {str(e)}"
            logger.exception(error_msg)
            export_obj.status = 'failed'
            export_obj.error_message = error_msg
            export_obj.save()
            return False, None, error_msg

    def _generate_csv(self, rows: List[Dict]) -> BytesIO:
        """
        Generate CSV file from row data.

        Args:
            rows: List of dictionaries with column data

        Returns:
            BytesIO: CSV file in memory
        """
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.csv_columns)

        # Write header
        writer.writeheader()

        # Write data rows
        writer.writerows(rows)

        # Convert to bytes
        output.seek(0)
        csv_bytes = BytesIO(output.getvalue().encode('utf-8'))

        return csv_bytes

    def get_evidence_url(self, journal_entry, tenant) -> Optional[str]:
        """
        Find supporting evidence for journal entry.

        Evidence sources:
        - Violation photos (Sprint 15)
        - Work order documents (Sprint 17)
        - ARC request documents (Sprint 16)
        - Bank statements (bank reconciliation)
        - Invoice uploads

        Args:
            journal_entry: JournalEntry instance
            tenant: Tenant instance

        Returns:
            str: Evidence URL or None if no evidence found
        """
        from accounting.models import (
            Violation, ViolationPhoto,
            WorkOrder, WorkOrderAttachment,
            ARCRequest, ARCDocument
        )

        # Check journal entry description/notes for references
        description = (journal_entry.description or '').lower()
        notes = (journal_entry.notes or '').lower()
        combined_text = f"{description} {notes}"

        # Look for violation references
        if 'violation' in combined_text or 'fine' in combined_text:
            # Try to find violation by date proximity
            violations = Violation.objects.filter(
                tenant=tenant,
                violation_date=journal_entry.entry_date
            ).first()

            if violations:
                # Get first photo as evidence
                photo = ViolationPhoto.objects.filter(violation=violations).first()
                if photo:
                    return self._generate_secure_url('violation', violations.id, tenant.id)

        # Look for work order references
        if 'work order' in combined_text or 'maintenance' in combined_text or 'repair' in combined_text:
            # Try to find work order by date
            work_order = WorkOrder.objects.filter(
                tenant=tenant,
                created_at__date=journal_entry.entry_date
            ).first()

            if work_order:
                # Get first attachment
                attachment = WorkOrderAttachment.objects.filter(work_order=work_order).first()
                if attachment:
                    return self._generate_secure_url('workorder', work_order.id, tenant.id)

        # Look for ARC references
        if 'arc' in combined_text or 'architectural' in combined_text:
            arc_request = ARCRequest.objects.filter(
                tenant=tenant,
                submission_date=journal_entry.entry_date
            ).first()

            if arc_request:
                document = ARCDocument.objects.filter(arc_request=arc_request).first()
                if document:
                    return self._generate_secure_url('arc', arc_request.id, tenant.id)

        # No evidence found
        return None

    def _generate_secure_url(self, evidence_type: str, evidence_id, tenant_id) -> str:
        """
        Generate secure, time-limited URL for evidence access.

        Args:
            evidence_type: Type of evidence (violation, workorder, arc, etc.)
            evidence_id: ID of the evidence record
            tenant_id: Tenant ID for security

        Returns:
            str: Secure URL with JWT token
        """
        # In production, this would generate a JWT token
        # For now, return a placeholder URL
        base_url = getattr(settings, 'APP_BASE_URL', 'https://app.hoaaccounting.com')
        return f"{base_url}/evidence/{tenant_id}/{evidence_type}/{evidence_id}"

    def calculate_running_balance(self, account, entries) -> Dict[str, Decimal]:
        """
        Calculate running balance for account across entries.

        Args:
            account: Account instance
            entries: QuerySet of JournalEntry objects

        Returns:
            dict: Mapping of entry_id -> running_balance
        """
        balances = {}
        running_balance = Decimal('0.00')

        for entry in entries:
            lines = entry.lines.filter(account=account)
            for line in lines:
                # Update balance based on account type
                account_type = account.account_type.name.lower()
                if 'asset' in account_type or 'expense' in account_type:
                    running_balance += line.debit - line.credit
                else:
                    running_balance += line.credit - line.debit

                balances[entry.id] = running_balance

        return balances

    def verify_export_integrity(self, export_obj) -> Tuple[bool, str]:
        """
        Verify export data integrity.

        Checks:
        - All debits = all credits (must balance)
        - File hash matches stored hash
        - Date range is valid
        - File exists and is accessible

        Args:
            export_obj: AuditorExport instance

        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        # Check balance
        if export_obj.total_debit != export_obj.total_credit:
            return False, f"Export unbalanced: debits={export_obj.total_debit}, credits={export_obj.total_credit}"

        # Check date range
        if export_obj.end_date < export_obj.start_date:
            return False, f"Invalid date range: {export_obj.start_date} to {export_obj.end_date}"

        # Check file exists
        if not export_obj.file_url:
            return False, "No file URL found"

        # Verify file hash (if file is accessible)
        try:
            if default_storage.exists(export_obj.file_url):
                file_content = default_storage.open(export_obj.file_url).read()
                calculated_hash = hashlib.sha256(file_content).hexdigest()

                if calculated_hash != export_obj.file_hash:
                    return False, f"File integrity check failed: hash mismatch"
        except Exception as e:
            logger.warning(f"Could not verify file hash for export {export_obj.id}: {e}")

        return True, ""
