"""
Simple tests for Board Packet PDF Generation

Tests the PDF generation service without requiring full Django models.
Sprint 20 - Board Packet Generation
"""

from datetime import date
from io import BytesIO

from accounting.services.pdf_generator import BoardPacketPDFGenerator


class TestBoardPacketPDFGenerator:
    """Test the PDF generation service"""

    def test_generate_simple_packet(self):
        """Test generating a simple board packet PDF"""
        generator = BoardPacketPDFGenerator()

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
        pdf_buffer = generator.generate_packet(packet_data)

        # Verify it's a BytesIO object
        assert isinstance(pdf_buffer, BytesIO)

        # Verify it has content
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        assert len(pdf_content) > 0

        # Verify PDF header
        assert pdf_content[:4] == b'%PDF'

        print(f"[OK] PDF generated successfully ({len(pdf_content)} bytes)")

    def test_generate_with_multiple_sections(self):
        """Test generating packet with multiple section types"""
        generator = BoardPacketPDFGenerator()

        packet_data = {
            'meeting_date': date(2025, 11, 15),
            'template_name': 'Full Board Packet',
            'hoa_name': 'Sunset Hills HOA',
            'sections': [
                {
                    'section_type': 'agenda',
                    'title': 'Meeting Agenda',
                    'content_data': {'items': ['Call to Order', 'Adjournment']}
                },
                {
                    'section_type': 'trial_balance',
                    'title': 'Trial Balance',
                    'content_data': {
                        'accounts': [
                            {'name': 'Cash', 'debit': '10000.00', 'credit': '0.00'},
                            {'name': 'Revenue', 'debit': '0.00', 'credit': '10000.00'}
                        ]
                    }
                },
                {
                    'section_type': 'ar_aging',
                    'title': 'AR Aging Report',
                    'content_data': {
                        'aging': [
                            {
                                'owner': 'John Doe',
                                'current': '500.00',
                                '30_60': '200.00',
                                '60_90': '0.00',
                                '90_plus': '0.00',
                                'total': '700.00'
                            }
                        ]
                    }
                },
                {
                    'section_type': 'violations',
                    'title': 'Violation Summary',
                    'content_data': {
                        'total_violations': 25,
                        'open_violations': 10,
                        'resolved_this_month': 5
                    }
                }
            ]
        }

        # Generate PDF
        pdf_buffer = generator.generate_packet(packet_data)

        # Verify
        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        assert len(pdf_content) > 0
        assert pdf_content[:4] == b'%PDF'

        print(f"[OK] Multi-section PDF generated successfully ({len(pdf_content)} bytes)")

    def test_generate_cover_page(self):
        """Test cover page generation"""
        generator = BoardPacketPDFGenerator()

        packet_data = {
            'hoa_name': 'Test HOA',
            'meeting_date': date(2025, 11, 15),
            'template_name': 'Standard Board Packet',
            'footer_text': 'Confidential'
        }

        elements = generator._generate_cover_page(packet_data)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

        print(f"[OK] Cover page generated with {len(elements)} elements")

    def test_generate_table_of_contents(self):
        """Test table of contents generation"""
        generator = BoardPacketPDFGenerator()

        sections = [
            {'section_type': 'agenda', 'title': 'Meeting Agenda'},
            {'section_type': 'minutes', 'title': 'Previous Minutes'},
            {'section_type': 'trial_balance', 'title': 'Trial Balance'}
        ]

        elements = generator._generate_table_of_contents(sections)

        # Should return a list of elements
        assert isinstance(elements, list)
        assert len(elements) > 0

        print(f"[OK] Table of contents generated with {len(sections)} sections")

    def test_all_section_types(self):
        """Test that all section types can be generated"""
        generator = BoardPacketPDFGenerator()

        section_types = [
            ('agenda', {'items': ['Item 1', 'Item 2']}),
            ('minutes', {'text': 'Previous meeting minutes'}),
            ('trial_balance', {'accounts': [{'name': 'Cash', 'debit': '1000.00', 'credit': '0.00'}]}),
            ('cash_flow', {'beginning_balance': '5000.00', 'ending_balance': '5500.00'}),
            ('ar_aging', {'aging': [{'owner': 'Test', 'current': '100.00', '30_60': '0.00', '60_90': '0.00', '90_plus': '0.00', 'total': '100.00'}]}),
            ('delinquency', {'total_delinquent': 5, 'total_balance': '1000.00', 'accounts_90_plus': 2}),
            ('violations', {'total_violations': 10, 'open_violations': 3, 'resolved_this_month': 2})
        ]

        for section_type, content_data in section_types:
            section = {
                'section_type': section_type,
                'title': section_type.replace('_', ' ').title(),
                'content_data': content_data
            }

            elements = generator._generate_section(section)
            assert isinstance(elements, list)
            assert len(elements) > 0
            print(f"  [OK] {section_type} section generated")

        print(f"[OK] All {len(section_types)} section types generated successfully")


if __name__ == '__main__':
    # Run tests manually for quick verification
    test = TestBoardPacketPDFGenerator()

    print("\nRunning Board Packet PDF Generator Tests...")
    print("=" * 60)

    try:
        print("\n1. Testing simple packet generation...")
        test.test_generate_simple_packet()

        print("\n2. Testing multi-section packet...")
        test.test_generate_with_multiple_sections()

        print("\n3. Testing cover page...")
        test.test_generate_cover_page()

        print("\n4. Testing table of contents...")
        test.test_generate_table_of_contents()

        print("\n5. Testing all section types...")
        test.test_all_section_types()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
