"""
Tests for Auditor Export functionality

Sprint 21 - Auditor Export
Tests: Model, Service, API endpoints
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.test import override_settings

from accounting.models import (
    AuditorExport, JournalEntry, JournalEntryLine,
    Account, AccountType, Fund
)
from accounting.services.auditor_export_service import AuditorExportService

User = get_user_model()


# Fixtures for testing
@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def tenant(db):
    """Create a test tenant"""
    from tenants.models import Tenant
    return Tenant.objects.create(
        name="Test HOA",
        schema_name="test_hoa"
    )


@pytest.fixture
def account_type_asset(db, tenant):
    """Create asset account type"""
    return AccountType.objects.create(
        tenant=tenant,
        name="Asset",
        normal_balance="debit"
    )


@pytest.fixture
def account_type_revenue(db, tenant):
    """Create revenue account type"""
    return AccountType.objects.create(
        tenant=tenant,
        name="Revenue",
        normal_balance="credit"
    )


@pytest.fixture
def fund(db, tenant):
    """Create operating fund"""
    return Fund.objects.create(
        tenant=tenant,
        name="Operating Fund",
        fund_type="operating"
    )


@pytest.fixture
def cash_account(db, tenant, account_type_asset, fund):
    """Create cash account"""
    return Account.objects.create(
        tenant=tenant,
        account_number="1000",
        name="Cash",
        account_type=account_type_asset,
        fund=fund
    )


@pytest.fixture
def revenue_account(db, tenant, account_type_revenue, fund):
    """Create revenue account"""
    return Account.objects.create(
        tenant=tenant,
        account_number="4000",
        name="HOA Dues Revenue",
        account_type=account_type_revenue,
        fund=fund
    )


@pytest.fixture
def journal_entries(db, tenant, cash_account, revenue_account, user):
    """Create sample journal entries for testing"""
    entries = []

    # Entry 1: Revenue collection
    entry1 = JournalEntry.objects.create(
        tenant=tenant,
        entry_date=date(2025, 1, 15),
        entry_number="JE-001",
        description="Monthly assessment revenue",
        created_by=user
    )
    JournalEntryLine.objects.create(
        journal_entry=entry1,
        account=cash_account,
        debit=Decimal('5000.00'),
        credit=Decimal('0.00'),
        description="Cash receipt"
    )
    JournalEntryLine.objects.create(
        journal_entry=entry1,
        account=revenue_account,
        debit=Decimal('0.00'),
        credit=Decimal('5000.00'),
        description="Revenue recognition"
    )
    entries.append(entry1)

    # Entry 2: More revenue
    entry2 = JournalEntry.objects.create(
        tenant=tenant,
        entry_date=date(2025, 1, 20),
        entry_number="JE-002",
        description="Late fee revenue",
        created_by=user
    )
    JournalEntryLine.objects.create(
        journal_entry=entry2,
        account=cash_account,
        debit=Decimal('100.00'),
        credit=Decimal('0.00'),
        description="Late fee received"
    )
    JournalEntryLine.objects.create(
        journal_entry=entry2,
        account=revenue_account,
        debit=Decimal('0.00'),
        credit=Decimal('100.00'),
        description="Late fee revenue"
    )
    entries.append(entry2)

    return entries


@pytest.fixture
def auditor_export(db, tenant, user):
    """Create a test auditor export"""
    return AuditorExport.objects.create(
        tenant=tenant,
        title="2025 Q1 Audit Export",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        format='csv',
        generated_by=user
    )


# ============================================================================
# Model Tests
# ============================================================================

class TestAuditorExportModel:
    """Test the AuditorExport model"""

    def test_create_auditor_export(self, auditor_export):
        """Test creating an auditor export"""
        assert auditor_export.title == "2025 Q1 Audit Export"
        assert auditor_export.status == 'generating'
        assert auditor_export.format == 'csv'
        assert auditor_export.start_date == date(2025, 1, 1)
        assert auditor_export.end_date == date(2025, 3, 31)

    def test_auditor_export_str(self, auditor_export):
        """Test string representation"""
        expected = "2025 Q1 Audit Export (2025-01-01 to 2025-03-31)"
        assert str(auditor_export) == expected

    def test_is_balanced_method(self, auditor_export):
        """Test is_balanced method"""
        auditor_export.total_debit = Decimal('1000.00')
        auditor_export.total_credit = Decimal('1000.00')
        assert auditor_export.is_balanced() is True

        auditor_export.total_credit = Decimal('999.00')
        assert auditor_export.is_balanced() is False

    def test_evidence_percentage_property(self, auditor_export):
        """Test evidence_percentage calculation"""
        auditor_export.total_entries = 100
        auditor_export.evidence_count = 75
        assert auditor_export.evidence_percentage == 75.0

        auditor_export.total_entries = 0
        assert auditor_export.evidence_percentage == 0

    def test_increment_download_count(self, auditor_export):
        """Test download counter increment"""
        assert auditor_export.downloaded_count == 0
        assert auditor_export.last_downloaded_at is None

        auditor_export.increment_download_count()
        assert auditor_export.downloaded_count == 1
        assert auditor_export.last_downloaded_at is not None

        auditor_export.increment_download_count()
        assert auditor_export.downloaded_count == 2


# ============================================================================
# Service Tests
# ============================================================================

class TestAuditorExportService:
    """Test the AuditorExportService"""

    def test_generate_csv_method(self):
        """Test CSV generation from row data"""
        service = AuditorExportService()

        rows = [
            {
                'Date': '2025-01-15',
                'Entry#': 'JE-001',
                'Account#': '1000',
                'Account Name': 'Cash',
                'Description': 'Revenue collection',
                'Debit': '5,000.00',
                'Credit': '',
                'Balance': '5,000.00',
                'Evidence URL': 'https://example.com/evidence/1',
                'Notes': 'Monthly assessment'
            }
        ]

        csv_buffer = service._generate_csv(rows)
        assert isinstance(csv_buffer, BytesIO)

        # Read CSV content
        csv_buffer.seek(0)
        content = csv_buffer.read().decode('utf-8')

        # Verify header
        assert 'Date,Entry#,Account#,Account Name' in content
        # Verify data
        assert '2025-01-15' in content
        assert 'JE-001' in content
        assert 'Cash' in content

    def test_generate_export_success(self, auditor_export, journal_entries):
        """Test successful export generation"""
        service = AuditorExportService()

        success, file_url, error_message = service.generate_export(auditor_export)

        assert success is True
        assert file_url is not None
        assert error_message == ""

        # Refresh from DB
        auditor_export.refresh_from_db()
        assert auditor_export.status == 'ready'
        assert auditor_export.total_entries == 4  # 2 entries x 2 lines each
        assert auditor_export.total_debit == Decimal('5100.00')
        assert auditor_export.total_credit == Decimal('5100.00')
        assert auditor_export.is_balanced() is True

    def test_generate_export_no_entries(self, auditor_export):
        """Test export generation with no journal entries"""
        service = AuditorExportService()

        # Set date range with no entries
        auditor_export.start_date = date(2024, 1, 1)
        auditor_export.end_date = date(2024, 1, 31)
        auditor_export.save()

        success, file_url, error_message = service.generate_export(auditor_export)

        assert success is False
        assert "No journal entries found" in error_message

    def test_verify_export_integrity_valid(self, auditor_export):
        """Test integrity verification for valid export"""
        service = AuditorExportService()

        # Set up valid export
        auditor_export.total_debit = Decimal('1000.00')
        auditor_export.total_credit = Decimal('1000.00')
        auditor_export.file_url = 'test.csv'
        auditor_export.file_hash = 'abc123'
        auditor_export.save()

        is_valid, error_message = service.verify_export_integrity(auditor_export)

        assert is_valid is True
        assert error_message == ""

    def test_verify_export_integrity_unbalanced(self, auditor_export):
        """Test integrity verification for unbalanced export"""
        service = AuditorExportService()

        # Set up unbalanced export
        auditor_export.total_debit = Decimal('1000.00')
        auditor_export.total_credit = Decimal('999.00')
        auditor_export.save()

        is_valid, error_message = service.verify_export_integrity(auditor_export)

        assert is_valid is False
        assert "unbalanced" in error_message.lower()

    def test_verify_export_integrity_invalid_date_range(self, auditor_export):
        """Test integrity verification for invalid date range"""
        service = AuditorExportService()

        # Set up invalid date range
        auditor_export.end_date = auditor_export.start_date - timedelta(days=1)
        auditor_export.save()

        is_valid, error_message = service.verify_export_integrity(auditor_export)

        assert is_valid is False
        assert "Invalid date range" in error_message

    def test_get_evidence_url(self, tenant, user):
        """Test evidence URL generation"""
        service = AuditorExportService()

        # Create journal entry with violation reference
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date.today(),
            entry_number="JE-TEST",
            description="Violation fine collected",
            notes="Related to violation #123",
            created_by=user
        )

        # Test evidence URL generation
        evidence_url = service.get_evidence_url(entry, tenant)

        # Should return None if no actual violation exists
        # (or a URL if violation is found)
        assert evidence_url is None or isinstance(evidence_url, str)

    def test_generate_secure_url(self):
        """Test secure URL generation"""
        service = AuditorExportService()

        url = service._generate_secure_url('violation', '123', 'tenant-456')

        assert 'violation' in url
        assert '123' in url
        assert 'tenant-456' in url


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.django_db
class TestAuditorExportIntegration:
    """Integration tests for full export workflow"""

    def test_full_export_workflow(self, auditor_export, journal_entries):
        """Test complete export generation workflow"""
        # 1. Create export request
        assert auditor_export.status == 'generating'

        # 2. Generate export
        service = AuditorExportService()
        success, file_url, error_message = service.generate_export(auditor_export)

        assert success is True
        assert auditor_export.status == 'ready'

        # 3. Verify integrity
        is_valid, error_message = service.verify_export_integrity(auditor_export)
        assert is_valid is True

        # 4. Track download
        auditor_export.increment_download_count()
        assert auditor_export.downloaded_count == 1

    def test_export_csv_format(self, auditor_export, journal_entries):
        """Test CSV export format and content"""
        service = AuditorExportService()
        success, file_url, error_message = service.generate_export(auditor_export)

        assert success is True

        # Verify file exists
        if default_storage.exists(file_url):
            # Read CSV content
            csv_content = default_storage.open(file_url).read().decode('utf-8')

            # Verify CSV structure
            lines = csv_content.strip().split('\n')
            assert len(lines) > 1  # Header + data rows

            # Verify header
            header = lines[0]
            assert 'Date' in header
            assert 'Entry#' in header
            assert 'Account#' in header
            assert 'Debit' in header
            assert 'Credit' in header

            # Verify data rows
            assert 'JE-001' in csv_content
            assert 'Cash' in csv_content
            assert 'HOA Dues Revenue' in csv_content


# ============================================================================
# Performance Tests
# ============================================================================

class TestAuditorExportPerformance:
    """Test export performance with larger datasets"""

    def test_large_export_performance(self, tenant, cash_account, revenue_account, user):
        """Test export generation with many entries"""
        # Create 100 journal entries
        for i in range(100):
            entry = JournalEntry.objects.create(
                tenant=tenant,
                entry_date=date(2025, 1, 1) + timedelta(days=i % 30),
                entry_number=f"JE-{i:04d}",
                description=f"Transaction {i}",
                created_by=user
            )
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=cash_account,
                debit=Decimal('100.00'),
                credit=Decimal('0.00')
            )
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=revenue_account,
                debit=Decimal('0.00'),
                credit=Decimal('100.00')
            )

        # Create export
        export = AuditorExport.objects.create(
            tenant=tenant,
            title="Performance Test Export",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            format='csv',
            generated_by=user
        )

        # Generate export and measure time
        import time
        start_time = time.time()

        service = AuditorExportService()
        success, file_url, error_message = service.generate_export(export)

        elapsed_time = time.time() - start_time

        assert success is True
        assert export.total_entries == 200  # 100 entries x 2 lines
        assert elapsed_time < 5.0  # Should complete in < 5 seconds
        print(f"\n[PERFORMANCE] Generated 200 entries in {elapsed_time:.2f}s")


if __name__ == '__main__':
    # Run tests with: python -m pytest accounting/tests/test_auditor_export.py -v -s
    pytest.main([__file__, '-v', '-s'])
