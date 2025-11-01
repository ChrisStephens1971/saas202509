"""
Tests for Resale Disclosure functionality

Sprint 22 - Resale Disclosure Packages
Tests: Model, Service, API endpoints
"""

import pytest
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.test import override_settings

from accounting.models import (
    ResaleDisclosure, Unit, Owner, Invoice, InvoiceLine
)
from accounting.services.resale_disclosure_service import ResaleDisclosureService

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
def unit(db, tenant):
    """Create a test unit"""
    return Unit.objects.create(
        tenant=tenant,
        unit_number="101",
        address="123 Main St, Unit 101"
    )


@pytest.fixture
def owner(db, tenant):
    """Create a test owner"""
    return Owner.objects.create(
        tenant=tenant,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-1234"
    )


@pytest.fixture
def resale_disclosure(db, tenant, unit, owner, user):
    """Create a test resale disclosure"""
    return ResaleDisclosure.objects.create(
        tenant=tenant,
        unit=unit,
        owner=owner,
        requested_by=user,
        buyer_name="Jane Smith",
        escrow_agent="Bob Johnson",
        escrow_company="Escrow Co",
        contact_email="buyer@example.com",
        contact_phone="555-5678",
        state="CA"
    )


# ============================================================================
# Model Tests
# ============================================================================

class TestResaleDisclosureModel:
    """Test the ResaleDisclosure model"""

    def test_create_resale_disclosure(self, resale_disclosure):
        """Test creating a resale disclosure"""
        assert resale_disclosure.buyer_name == "Jane Smith"
        assert resale_disclosure.status == ResaleDisclosure.STATUS_REQUESTED
        assert resale_disclosure.state == "CA"
        assert resale_disclosure.fee_amount == Decimal('250.00')

    def test_resale_disclosure_str(self, resale_disclosure):
        """Test string representation"""
        expected = f"Resale Disclosure - {resale_disclosure.unit.unit_number} ({resale_disclosure.requested_at.date()})"
        assert str(resale_disclosure) == expected

    def test_get_state_display_name(self, resale_disclosure):
        """Test state display name method"""
        assert resale_disclosure.get_state_display_name() == "California"

        resale_disclosure.state = "TX"
        assert resale_disclosure.get_state_display_name() == "Texas"

        resale_disclosure.state = "FL"
        assert resale_disclosure.get_state_display_name() == "Florida"

        resale_disclosure.state = "NY"
        assert resale_disclosure.get_state_display_name() == "NY"  # Unknown state returns code

    def test_mark_as_delivered(self, resale_disclosure):
        """Test mark_as_delivered method"""
        resale_disclosure.status = ResaleDisclosure.STATUS_READY
        resale_disclosure.save()

        assert resale_disclosure.delivered_at is None

        resale_disclosure.mark_as_delivered()
        assert resale_disclosure.status == ResaleDisclosure.STATUS_DELIVERED
        assert resale_disclosure.delivered_at is not None

    def test_default_fee_amount(self, resale_disclosure):
        """Test default fee amount is $250"""
        assert resale_disclosure.fee_amount == Decimal('250.00')

    def test_financial_snapshot_fields(self, resale_disclosure):
        """Test financial snapshot fields"""
        resale_disclosure.current_balance = Decimal('500.00')
        resale_disclosure.monthly_dues = Decimal('250.00')
        resale_disclosure.special_assessments = Decimal('1000.00')
        resale_disclosure.has_lien = True
        resale_disclosure.has_violations = True
        resale_disclosure.violation_count = 3
        resale_disclosure.save()

        assert resale_disclosure.current_balance == Decimal('500.00')
        assert resale_disclosure.has_lien is True
        assert resale_disclosure.violation_count == 3


# ============================================================================
# Service Tests
# ============================================================================

class TestResaleDisclosureService:
    """Test the ResaleDisclosureService"""

    def test_generate_pdf_method(self):
        """Test PDF generation from data"""
        service = ResaleDisclosureService()

        data = {
            'hoa_name': 'Test HOA',
            'unit_number': '101',
            'property_address': '123 Main St, Unit 101',
            'disclosure_date': date.today(),
            'state': 'CA',
            'buyer_name': 'Jane Smith',
            'escrow_agent': 'Bob Johnson',
            'financial_summary': {
                'current_balance': Decimal('0.00'),
                'monthly_dues': Decimal('250.00'),
                'special_assessments': Decimal('0.00'),
            },
            'violation_history': {
                'open_violations': [],
                'all_violations': [],
            },
            'lien_status': {
                'has_lien': False,
                'lien_amount': Decimal('0.00'),
                'filing_date': None,
                'release_requirements': 'N/A',
            },
            'reserve_summary': {
                'fund_balance': Decimal('150000.00'),
                'funding_percentage': 75.0,
                'last_study_date': '2024-01-01',
            },
        }

        pdf_buffer = service._generate_pdf(data, 'CA')
        assert isinstance(pdf_buffer, BytesIO)

        # Read PDF content
        pdf_buffer.seek(0)
        content = pdf_buffer.read()

        # Verify PDF was generated (PDF starts with %PDF)
        assert content[:4] == b'%PDF'

    def test_get_owner_financial_summary(self, owner):
        """Test getting owner financial summary"""
        service = ResaleDisclosureService()

        summary = service.get_owner_financial_summary(owner)

        assert 'current_balance' in summary
        assert 'monthly_dues' in summary
        assert 'special_assessments' in summary
        assert isinstance(summary['current_balance'], Decimal)

    def test_get_violation_history(self, unit):
        """Test getting violation history"""
        service = ResaleDisclosureService()

        history = service.get_violation_history(unit)

        assert 'open_violations' in history
        assert 'all_violations' in history
        assert isinstance(history['open_violations'], list)
        assert isinstance(history['all_violations'], list)

    def test_get_lien_status(self, owner):
        """Test getting lien status"""
        service = ResaleDisclosureService()

        lien_status = service.get_lien_status(owner)

        assert 'has_lien' in lien_status
        assert 'lien_amount' in lien_status
        assert lien_status['has_lien'] is False

    def test_get_reserve_summary(self, tenant):
        """Test getting reserve summary"""
        service = ResaleDisclosureService()

        summary = service.get_reserve_summary(tenant)

        assert 'fund_balance' in summary
        assert 'funding_percentage' in summary
        assert 'last_study_date' in summary

    def test_generate_disclosure_pdf_success(self, resale_disclosure):
        """Test successful disclosure PDF generation"""
        service = ResaleDisclosureService()

        success, file_url, error_message = service.generate_disclosure_pdf(resale_disclosure)

        # Refresh from DB
        resale_disclosure.refresh_from_db()

        assert success is True
        assert file_url is not None
        assert error_message == ""
        assert resale_disclosure.status == ResaleDisclosure.STATUS_READY
        assert resale_disclosure.pdf_url is not None
        assert resale_disclosure.pdf_hash is not None
        assert resale_disclosure.page_count > 0

    def test_generate_disclosure_pdf_already_generated(self, resale_disclosure):
        """Test generating disclosure when already ready"""
        service = ResaleDisclosureService()

        # First generation
        service.generate_disclosure_pdf(resale_disclosure)

        resale_disclosure.refresh_from_db()
        assert resale_disclosure.status == ResaleDisclosure.STATUS_READY

        # Second generation should also succeed (regenerate)
        success, file_url, error_message = service.generate_disclosure_pdf(resale_disclosure)
        assert success is True

    def test_count_pages(self):
        """Test page counting estimation"""
        service = ResaleDisclosureService()

        # Create a small PDF buffer
        small_buffer = BytesIO(b'%PDF-1.4\n' * 100)
        pages = service._count_pages(small_buffer)
        assert pages >= 1

    def test_generate_invoice(self, resale_disclosure):
        """Test invoice generation for disclosure fee"""
        service = ResaleDisclosureService()

        # Generate invoice
        invoice = service.generate_invoice(resale_disclosure)

        assert invoice is not None
        assert isinstance(invoice, Invoice)
        assert invoice.amount == resale_disclosure.fee_amount
        assert invoice.owner == resale_disclosure.owner

        # Check invoice line
        lines = InvoiceLine.objects.filter(invoice=invoice)
        assert lines.count() == 1
        assert lines.first().amount == resale_disclosure.fee_amount

        # Verify disclosure is linked to invoice
        resale_disclosure.refresh_from_db()
        assert resale_disclosure.invoice == invoice


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.django_db
class TestResaleDisclosureIntegration:
    """Integration tests for full disclosure workflow"""

    def test_full_disclosure_workflow(self, resale_disclosure):
        """Test complete disclosure generation workflow"""
        # 1. Create disclosure request
        assert resale_disclosure.status == ResaleDisclosure.STATUS_REQUESTED

        # 2. Generate disclosure
        service = ResaleDisclosureService()
        success, file_url, error_message = service.generate_disclosure_pdf(resale_disclosure)

        assert success is True
        resale_disclosure.refresh_from_db()
        assert resale_disclosure.status == ResaleDisclosure.STATUS_READY

        # 3. Generate invoice
        invoice = service.generate_invoice(resale_disclosure)
        assert invoice.amount == Decimal('250.00')

        # 4. Mark as delivered
        resale_disclosure.mark_as_delivered()
        assert resale_disclosure.status == ResaleDisclosure.STATUS_DELIVERED

    def test_disclosure_pdf_content(self, resale_disclosure):
        """Test PDF disclosure content includes all sections"""
        service = ResaleDisclosureService()
        success, file_url, error_message = service.generate_disclosure_pdf(resale_disclosure)

        assert success is True

        # Verify PDF was generated
        resale_disclosure.refresh_from_db()
        assert resale_disclosure.pdf_url is not None
        assert resale_disclosure.pdf_size_bytes > 0

        # Verify file exists in storage
        if default_storage.exists(resale_disclosure.pdf_url):
            pdf_content = default_storage.open(resale_disclosure.pdf_url).read()

            # Verify PDF structure (basic check)
            assert pdf_content[:4] == b'%PDF'
            assert len(pdf_content) > 1000  # Should be substantial

    def test_multiple_state_templates(self, tenant, unit, owner, user):
        """Test disclosure generation for different states"""
        states = ['CA', 'TX', 'FL']

        for state in states:
            disclosure = ResaleDisclosure.objects.create(
                tenant=tenant,
                unit=unit,
                owner=owner,
                requested_by=user,
                contact_email="buyer@example.com",
                state=state
            )

            service = ResaleDisclosureService()
            success, file_url, error_message = service.generate_disclosure_pdf(disclosure)

            assert success is True
            disclosure.refresh_from_db()
            assert disclosure.status == ResaleDisclosure.STATUS_READY
            assert disclosure.get_state_display_name() in ['California', 'Texas', 'Florida']


# ============================================================================
# Performance Tests
# ============================================================================

class TestResaleDisclosurePerformance:
    """Test disclosure performance"""

    def test_pdf_generation_performance(self, resale_disclosure):
        """Test PDF generation completes in reasonable time"""
        import time

        service = ResaleDisclosureService()

        start_time = time.time()
        success, file_url, error_message = service.generate_disclosure_pdf(resale_disclosure)
        elapsed_time = time.time() - start_time

        assert success is True
        assert elapsed_time < 10.0  # Should complete in < 10 seconds
        print(f"\n[PERFORMANCE] Generated disclosure PDF in {elapsed_time:.2f}s")

    def test_multiple_disclosure_generation(self, tenant, unit, owner, user):
        """Test generating multiple disclosures"""
        import time

        service = ResaleDisclosureService()
        disclosures = []

        # Create 5 disclosure requests
        for i in range(5):
            disclosure = ResaleDisclosure.objects.create(
                tenant=tenant,
                unit=unit,
                owner=owner,
                requested_by=user,
                buyer_name=f"Buyer {i}",
                contact_email=f"buyer{i}@example.com",
                state="CA"
            )
            disclosures.append(disclosure)

        # Generate all disclosures
        start_time = time.time()
        for disclosure in disclosures:
            success, file_url, error_message = service.generate_disclosure_pdf(disclosure)
            assert success is True

        elapsed_time = time.time() - start_time

        assert elapsed_time < 30.0  # 5 disclosures should complete in < 30 seconds
        print(f"\n[PERFORMANCE] Generated {len(disclosures)} disclosure PDFs in {elapsed_time:.2f}s ({elapsed_time/len(disclosures):.2f}s average)")


if __name__ == '__main__':
    # Run tests with: python -m pytest accounting/tests/test_resale_disclosure.py -v -s
    pytest.main([__file__, '-v', '-s'])
