"""
Tests for Board Packet PDF Generation and Email Sending

Sprint 20 - Board Packet Generation
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings

from accounting.models import (
    Tenant, BoardPacketTemplate, BoardPacket, PacketSection
)
from accounting.services.pdf_generator import BoardPacketPDFGenerator

User = get_user_model()


@pytest.fixture
def tenant(db):
    """Create a test tenant"""
    return Tenant.objects.create(
        name="Test HOA",
        domain="testhoa",
        schema_name="testhoa"
    )


@pytest.fixture
def board_packet_template(db, tenant):
    """Create a test board packet template"""
    return BoardPacketTemplate.objects.create(
        tenant=tenant,
        name="Standard Board Packet",
        description="Standard monthly board meeting packet",
        sections=[
            "cover_page",
            "agenda",
            "minutes",
            "trial_balance",
            "cash_flow",
            "ar_aging",
            "delinquency",
            "violations"
        ],
        section_order=["cover_page", "agenda", "minutes", "trial_balance"],
        include_cover_page=True,
        is_default=True
    )


@pytest.fixture
def board_packet(db, tenant, board_packet_template):
    """Create a test board packet"""
    return BoardPacket.objects.create(
        tenant=tenant,
        template=board_packet_template,
        title="November 2025 Board Meeting",
        meeting_date=date(2025, 11, 15),
        status='draft'
    )


@pytest.fixture
def pdf_generator():
    """Create a PDF generator instance"""
    return BoardPacketPDFGenerator()


class TestBoardPacketPDFGenerator:
    """Test the PDF generation service"""

    def test_generate_simple_packet(self, pdf_generator):
        """Test generating a simple board packet PDF"""
        packet_data = {
            'meeting_date': date(2025, 11, 15),
            'template_name': 'Standard Board Packet',
            'hoa_name': 'Test HOA',
            'header_text': 'Monthly Board Meeting',
            'footer_text': 'Confidential',
            'sections': [
                {
                    'section_type': 'agenda',
                    'title': 'Meeting Agenda',
                    'content_data': {
                        'items': [
                            'Call to Order',
                            'Financial Report',
                            'New Business',
                            'Adjournment'
                        ]
                    }
                }
            ]
        }

        # Generate PDF
        pdf_buffer = pdf_generator.generate_packet(packet_data)

        # Verify it's a BytesIO object
        assert isinstance(pdf_buffer, BytesIO)

        # Verify it has content
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        assert len(pdf_content) > 0

        # Verify PDF header
        assert pdf_content[:4] == b'%PDF'

    def test_generate_cover_page(self, pdf_generator):
        """Test cover page generation"""
        packet_data = {
            'hoa_name': 'Test HOA',
            'meeting_date': date(2025, 11, 15),
            'template_name': 'Standard Board Packet',
            'footer_text': 'Confidential'
        }

        elements = pdf_generator._generate_cover_page(packet_data)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_table_of_contents(self, pdf_generator):
        """Test table of contents generation"""
        sections = [
            {'section_type': 'agenda', 'title': 'Meeting Agenda'},
            {'section_type': 'minutes', 'title': 'Previous Minutes'},
            {'section_type': 'trial_balance', 'title': 'Trial Balance'}
        ]

        elements = pdf_generator._generate_table_of_contents(sections)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_trial_balance_section(self, pdf_generator):
        """Test trial balance section generation"""
        section = {
            'section_type': 'trial_balance',
            'title': 'Trial Balance',
            'content_data': {
                'accounts': [
                    {'name': 'Cash', 'debit': '10000.00', 'credit': '0.00'},
                    {'name': 'Accounts Receivable', 'debit': '5000.00', 'credit': '0.00'},
                    {'name': 'Accounts Payable', 'debit': '0.00', 'credit': '3000.00'},
                    {'name': 'Revenue', 'debit': '0.00', 'credit': '12000.00'}
                ]
            }
        }

        elements = pdf_generator._generate_section(section)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_ar_aging_section(self, pdf_generator):
        """Test AR aging section generation"""
        section = {
            'section_type': 'ar_aging',
            'title': 'AR Aging Report',
            'content_data': {
                'aging': [
                    {
                        'owner': 'John Doe',
                        'current': '500.00',
                        '30_60': '200.00',
                        '60_90': '100.00',
                        '90_plus': '50.00',
                        'total': '850.00'
                    },
                    {
                        'owner': 'Jane Smith',
                        'current': '0.00',
                        '30_60': '0.00',
                        '60_90': '300.00',
                        '90_plus': '200.00',
                        'total': '500.00'
                    }
                ]
            }
        }

        elements = pdf_generator._generate_section(section)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_delinquency_section(self, pdf_generator):
        """Test delinquency section generation"""
        section = {
            'section_type': 'delinquency',
            'title': 'Delinquency Report',
            'content_data': {
                'total_delinquent': 12,
                'total_balance': '15000.00',
                'accounts_90_plus': 5
            }
        }

        elements = pdf_generator._generate_section(section)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_violation_section(self, pdf_generator):
        """Test violation section generation"""
        section = {
            'section_type': 'violations',
            'title': 'Violation Summary',
            'content_data': {
                'total_violations': 25,
                'open_violations': 10,
                'resolved_this_month': 5
            }
        }

        elements = pdf_generator._generate_section(section)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_cash_flow_section(self, pdf_generator):
        """Test cash flow section generation"""
        section = {
            'section_type': 'cash_flow',
            'title': 'Cash Flow Statement',
            'content_data': {
                'beginning_balance': '50000.00',
                'ending_balance': '55000.00'
            }
        }

        elements = pdf_generator._generate_section(section)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0


class TestBoardPacketModels:
    """Test board packet models"""

    def test_create_board_packet_template(self, board_packet_template):
        """Test creating a board packet template"""
        assert board_packet_template.name == "Standard Board Packet"
        assert board_packet_template.is_default is True
        assert len(board_packet_template.sections) > 0

    def test_create_board_packet(self, board_packet, board_packet_template):
        """Test creating a board packet"""
        assert board_packet.title == "November 2025 Board Meeting"
        assert board_packet.status == 'draft'
        assert board_packet.template == board_packet_template
        assert board_packet.meeting_date == date(2025, 11, 15)

    def test_board_packet_status_transitions(self, board_packet):
        """Test board packet status transitions"""
        # Initial state
        assert board_packet.status == 'draft'

        # Transition to generating
        board_packet.status = 'generating'
        board_packet.save()
        assert board_packet.status == 'generating'

        # Transition to ready
        board_packet.status = 'ready'
        board_packet.pdf_url = 'http://example.com/packet.pdf'
        board_packet.save()
        assert board_packet.status == 'ready'

        # Transition to sent
        board_packet.status = 'sent'
        board_packet.sent_to = ['board@hoa.com']
        board_packet.save()
        assert board_packet.status == 'sent'

    def test_packet_section_ordering(self, board_packet):
        """Test packet section ordering"""
        # Create sections
        section1 = PacketSection.objects.create(
            packet=board_packet,
            section_type='cover_page',
            title='Cover Page',
            order=1
        )
        section2 = PacketSection.objects.create(
            packet=board_packet,
            section_type='agenda',
            title='Agenda',
            order=2
        )
        section3 = PacketSection.objects.create(
            packet=board_packet,
            section_type='minutes',
            title='Minutes',
            order=3
        )

        # Retrieve sections in order
        sections = board_packet.sections.all().order_by('order')
        assert list(sections) == [section1, section2, section3]


# Integration tests (require more setup)
@pytest.mark.django_db
class TestBoardPacketAPI:
    """Test board packet API endpoints"""

    def test_board_packet_template_list(self, client, tenant, board_packet_template):
        """Test listing board packet templates"""
        # Note: This requires authentication setup
        # response = client.get('/api/v1/accounting/board-packet-templates/')
        # assert response.status_code == 200
        pass

    def test_board_packet_create(self, client, tenant, board_packet_template):
        """Test creating a board packet via API"""
        # Note: This requires authentication setup
        pass

    def test_board_packet_generate_pdf(self, client, board_packet):
        """Test PDF generation via API"""
        # Note: This requires authentication setup
        pass

    def test_board_packet_send_email(self, client, board_packet):
        """Test email sending via API"""
        # Note: This requires authentication setup
        pass
