"""
Resale Disclosure Package Service

Generates state-compliant resale disclosure packages for unit sales.
Includes financial data, violations, liens, and HOA information.

Sprint 22 - Resale Disclosure Packages
"""

import hashlib
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Dict, Any, Tuple, List

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class ResaleDisclosureService:
    """
    Generate state-compliant resale disclosure packages.

    Revenue opportunity: $200-500 per package
    """

    # State-specific templates
    STATE_TEMPLATES = {
        'CA': 'California HOA Disclosure (Civil Code § 4525)',
        'TX': 'Texas Resale Certificate (Property Code § 209.0041)',
        'FL': 'Florida HOA Disclosure Summary (FS 720.401)',
        'DEFAULT': 'Generic HOA Disclosure Package'
    }

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        """Add custom paragraph styles for disclosure PDFs"""
        self.styles.add(ParagraphStyle(
            name='DisclosureTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=10,
            spaceBefore=15
        ))

        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

    def generate_disclosure_pdf(self, disclosure_obj):
        """
        Generate complete disclosure package PDF.

        Steps:
        1. Gather owner financial data
        2. Check for liens
        3. Get violation history
        4. Pull reserve study summary
        5. Get HOA information
        6. Generate PDF with all sections
        7. Save to storage
        8. Update disclosure record

        Args:
            disclosure_obj: ResaleDisclosure model instance

        Returns:
            Tuple[bool, str, str]: (success, file_url, error_message)
        """
        try:
            # Update status to generating
            disclosure_obj.status = disclosure_obj.STATUS_GENERATING
            disclosure_obj.save(update_fields=['status'])

            # Gather all data
            financial_summary = self.get_owner_financial_summary(disclosure_obj.owner)
            violation_history = self.get_violation_history(disclosure_obj.unit)
            lien_status = self.get_lien_status(disclosure_obj.owner)
            reserve_summary = self.get_reserve_summary(disclosure_obj.tenant)

            # Update financial snapshot
            disclosure_obj.current_balance = financial_summary.get('current_balance', Decimal('0.00'))
            disclosure_obj.monthly_dues = financial_summary.get('monthly_dues', Decimal('0.00'))
            disclosure_obj.special_assessments = financial_summary.get('special_assessments', Decimal('0.00'))
            disclosure_obj.has_lien = lien_status.get('has_lien', False)
            disclosure_obj.has_violations = len(violation_history.get('open_violations', [])) > 0
            disclosure_obj.violation_count = len(violation_history.get('all_violations', []))

            # Generate PDF
            pdf_data = {
                'hoa_name': disclosure_obj.tenant.name if hasattr(disclosure_obj.tenant, 'name') else 'HOA',
                'unit_number': disclosure_obj.unit.unit_number if hasattr(disclosure_obj.unit, 'unit_number') else 'N/A',
                'property_address': getattr(disclosure_obj.unit, 'address', 'N/A'),
                'disclosure_date': date.today(),
                'state': disclosure_obj.state,
                'buyer_name': disclosure_obj.buyer_name,
                'escrow_agent': disclosure_obj.escrow_agent,
                'financial_summary': financial_summary,
                'violation_history': violation_history,
                'lien_status': lien_status,
                'reserve_summary': reserve_summary,
            }

            pdf_buffer = self._generate_pdf(pdf_data, disclosure_obj.state)

            # Calculate file hash
            pdf_content = pdf_buffer.getvalue()
            file_hash = hashlib.sha256(pdf_content).hexdigest()

            # Save PDF to storage
            filename = f"resale_disclosure_{disclosure_obj.id}.pdf"
            file_path = f"disclosures/{disclosure_obj.tenant.id}/{filename}"

            saved_path = default_storage.save(
                file_path,
                ContentFile(pdf_content)
            )

            file_url = default_storage.url(saved_path)

            # Update disclosure record
            disclosure_obj.pdf_url = file_url
            disclosure_obj.pdf_size_bytes = len(pdf_content)
            disclosure_obj.pdf_hash = file_hash
            disclosure_obj.page_count = self._count_pages(pdf_buffer)
            disclosure_obj.status = disclosure_obj.STATUS_READY
            disclosure_obj.generated_at = timezone.now()
            disclosure_obj.save()

            return True, file_url, ""

        except Exception as e:
            # Mark as failed
            disclosure_obj.status = disclosure_obj.STATUS_FAILED
            disclosure_obj.error_message = str(e)
            disclosure_obj.save(update_fields=['status', 'error_message'])

            return False, "", str(e)

    def _generate_pdf(self, data: Dict[str, Any], state: str) -> BytesIO:
        """Generate PDF with state-specific sections"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        story = []

        # 1. Cover Page
        story.extend(self._generate_cover_page(data))
        story.append(PageBreak())

        # 2. Owner Financial Summary
        story.extend(self._generate_financial_section(data['financial_summary']))
        story.append(PageBreak())

        # 3. Lien Disclosure
        story.extend(self._generate_lien_section(data['lien_status']))
        story.append(PageBreak())

        # 4. Violation Disclosure
        story.extend(self._generate_violation_section(data['violation_history']))
        story.append(PageBreak())

        # 5. Reserve Study Summary
        story.extend(self._generate_reserve_section(data['reserve_summary']))
        story.append(PageBreak())

        # 6. HOA Information
        story.extend(self._generate_hoa_info_section(data))
        story.append(PageBreak())

        # 7. Certification Page
        story.extend(self._generate_certification_page(data))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _generate_cover_page(self, data: Dict[str, Any]) -> List:
        """Generate cover page"""
        elements = []

        # Title
        title = Paragraph(
            f"{self.STATE_TEMPLATES.get(data['state'], self.STATE_TEMPLATES['DEFAULT'])}",
            self.styles['DisclosureTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5 * inch))

        # Property information
        property_info = [
            ["HOA Name:", data['hoa_name']],
            ["Unit Number:", data['unit_number']],
            ["Property Address:", data['property_address']],
            ["Disclosure Date:", data['disclosure_date'].strftime('%B %d, %Y')],
            ["Buyer Name:", data['buyer_name'] or 'N/A'],
            ["Escrow Agent:", data['escrow_agent'] or 'N/A'],
        ]

        table = Table(property_info, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 1 * inch))

        # Disclaimer
        disclaimer = Paragraph(
            "This disclosure is provided for informational purposes only. "
            "All information is subject to change and should be independently verified.",
            self.styles['Disclaimer']
        )
        elements.append(disclaimer)

        return elements

    def _generate_financial_section(self, financial_summary: Dict) -> List:
        """Generate owner financial summary section"""
        elements = []

        elements.append(Paragraph("Owner Financial Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        financial_data = [
            ["Item", "Amount"],
            ["Current Balance Owed", f"${financial_summary.get('current_balance', 0):.2f}"],
            ["Monthly Dues", f"${financial_summary.get('monthly_dues', 0):.2f}"],
            ["Special Assessments", f"${financial_summary.get('special_assessments', 0):.2f}"],
        ]

        table = Table(financial_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

        return elements

    def _generate_lien_section(self, lien_status: Dict) -> List:
        """Generate lien disclosure section"""
        elements = []

        elements.append(Paragraph("Lien Disclosure", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        if lien_status.get('has_lien', False):
            lien_text = f"""
            <b>LIEN STATUS: ACTIVE</b><br/>
            Lien Amount: ${lien_status.get('lien_amount', 0):.2f}<br/>
            Filing Date: {lien_status.get('filing_date', 'N/A')}<br/>
            Release Requirements: {lien_status.get('release_requirements', 'Payment in full')}
            """
        else:
            lien_text = "<b>LIEN STATUS: NO ACTIVE LIENS</b><br/>No liens are currently recorded against this property."

        elements.append(Paragraph(lien_text, self.styles['Normal']))

        return elements

    def _generate_violation_section(self, violation_history: Dict) -> List:
        """Generate violation disclosure section"""
        elements = []

        elements.append(Paragraph("Violation Disclosure", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        open_violations = violation_history.get('open_violations', [])

        if open_violations:
            elements.append(Paragraph(f"<b>{len(open_violations)} Open Violation(s)</b>", self.styles['Normal']))

            for violation in open_violations[:5]:  # Show up to 5 violations
                violation_text = f"""
                • {violation.get('description', 'N/A')}<br/>
                  Date: {violation.get('date', 'N/A')} | Fine: ${violation.get('fine_amount', 0):.2f}
                """
                elements.append(Paragraph(violation_text, self.styles['Normal']))
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph("<b>NO OPEN VIOLATIONS</b>", self.styles['Normal']))

        return elements

    def _generate_reserve_section(self, reserve_summary: Dict) -> List:
        """Generate reserve study summary section"""
        elements = []

        elements.append(Paragraph("Reserve Study Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        reserve_data = [
            ["Reserve Fund Balance", f"${reserve_summary.get('fund_balance', 0):,.2f}"],
            ["Funding Percentage", f"{reserve_summary.get('funding_percentage', 0):.1f}%"],
            ["Last Study Date", reserve_summary.get('last_study_date', 'N/A')],
        ]

        table = Table(reserve_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)

        return elements

    def _generate_hoa_info_section(self, data: Dict) -> List:
        """Generate HOA information section"""
        elements = []

        elements.append(Paragraph("HOA Information", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        hoa_info = f"""
        <b>HOA Name:</b> {data['hoa_name']}<br/>
        <b>Management Company:</b> Self-Managed<br/>
        <b>Contact:</b> Board of Directors<br/>
        <b>Meeting Schedule:</b> Monthly
        """

        elements.append(Paragraph(hoa_info, self.styles['Normal']))

        return elements

    def _generate_certification_page(self, data: Dict) -> List:
        """Generate certification page"""
        elements = []

        elements.append(Paragraph("Certification", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.5 * inch))

        certification_text = f"""
        This disclosure package was prepared on {data['disclosure_date'].strftime('%B %d, %Y')}
        for the property located at {data['property_address']}, Unit {data['unit_number']}.
        <br/><br/>
        All information contained herein is accurate to the best of our knowledge as of the date of preparation.
        <br/><br/>
        Prepared by: {data['hoa_name']}
        <br/><br/><br/>
        _________________________________<br/>
        Authorized Signature<br/>
        <br/>
        Date: {data['disclosure_date'].strftime('%B %d, %Y')}
        """

        elements.append(Paragraph(certification_text, self.styles['Normal']))

        return elements

    def _count_pages(self, pdf_buffer: BytesIO) -> int:
        """Count pages in generated PDF"""
        # Simple estimation based on file size
        # More accurate method would parse PDF structure
        file_size = len(pdf_buffer.getvalue())
        estimated_pages = max(1, file_size // 50000)  # Rough estimate
        return min(estimated_pages, 20)  # Max 20 pages

    def get_owner_financial_summary(self, owner):
        """
        Get financial summary for owner.

        Returns:
            Dict with current_balance, monthly_dues, special_assessments
        """
        # TODO: Integrate with actual financial data from Sprint 1-12
        return {
            'current_balance': Decimal('0.00'),
            'monthly_dues': Decimal('250.00'),
            'special_assessments': Decimal('0.00'),
        }

    def get_violation_history(self, unit):
        """
        Get violation history for unit.

        Returns:
            Dict with open_violations and all_violations lists
        """
        # TODO: Integrate with Sprint 15 violation tracking
        return {
            'open_violations': [],
            'all_violations': [],
        }

    def get_lien_status(self, owner):
        """
        Check if owner has lien.

        Returns:
            Dict with has_lien, lien_amount, filing_date, release_requirements
        """
        # TODO: Integrate with lien tracking system
        return {
            'has_lien': False,
            'lien_amount': Decimal('0.00'),
            'filing_date': None,
            'release_requirements': 'N/A',
        }

    def get_reserve_summary(self, tenant):
        """
        Get reserve study summary.

        Returns:
            Dict with fund_balance, funding_percentage, last_study_date
        """
        # TODO: Integrate with Phase 2 reserve study data
        return {
            'fund_balance': Decimal('150000.00'),
            'funding_percentage': 75.0,
            'last_study_date': '2024-01-01',
        }

    def generate_invoice(self, disclosure):
        """
        Generate invoice for disclosure fee.

        Args:
            disclosure: ResaleDisclosure instance

        Returns:
            Invoice instance
        """
        from accounting.models import Invoice, InvoiceLine

        with transaction.atomic():
            # Create invoice
            invoice = Invoice.objects.create(
                tenant=disclosure.tenant,
                owner=disclosure.owner,
                invoice_date=date.today(),
                due_date=date.today(),  # Due immediately
                amount=disclosure.fee_amount,
                status='UNPAID',
                invoice_type='DISCLOSURE_FEE',
            )

            # Create invoice line
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f"Resale Disclosure Package - Unit {disclosure.unit.unit_number}",
                amount=disclosure.fee_amount,
                quantity=1,
            )

            # Link invoice to disclosure
            disclosure.invoice = invoice
            disclosure.save(update_fields=['invoice'])

            return invoice
