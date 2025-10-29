"""
Board Packet PDF Generation Service

Uses ReportLab to generate professional PDF board packets with:
- Cover page with HOA branding
- Table of contents
- Multiple section types (financials, reports, etc.)
- Headers and footers
- Page numbers
"""

from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import List, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class BoardPacketPDFGenerator:
    """Generate PDF board packets from templates and data"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        """Add custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        ))

    def generate_packet(self, packet_data: Dict[str, Any]) -> BytesIO:
        """
        Generate a complete board packet PDF

        Args:
            packet_data: Dictionary containing:
                - meeting_date: date
                - template_name: str
                - sections: List[Dict] with section data
                - hoa_name: str (optional)
                - header_text: str (optional)
                - footer_text: str (optional)

        Returns:
            BytesIO: PDF file in memory
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build PDF content
        story = []

        # Cover page
        story.extend(self._generate_cover_page(packet_data))
        story.append(PageBreak())

        # Table of contents
        story.extend(self._generate_table_of_contents(packet_data['sections']))
        story.append(PageBreak())

        # Generate each section
        for section in packet_data['sections']:
            story.extend(self._generate_section(section))
            story.append(PageBreak())

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _generate_cover_page(self, packet_data: Dict) -> List:
        """Generate cover page"""
        elements = []

        # Title
        hoa_name = packet_data.get('hoa_name', 'Homeowners Association')
        title = Paragraph(f"{hoa_name}<br/>Board Meeting Packet", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.5 * inch))

        # Meeting date
        meeting_date = packet_data.get('meeting_date', date.today())
        date_text = f"Meeting Date: {meeting_date.strftime('%B %d, %Y')}"
        date_para = Paragraph(date_text, self.styles['Heading2'])
        elements.append(date_para)
        elements.append(Spacer(1, 0.3 * inch))

        # Template info
        template = packet_data.get('template_name', 'Standard Board Packet')
        template_para = Paragraph(f"Template: {template}", self.styles['Normal'])
        elements.append(template_para)
        elements.append(Spacer(1, 1 * inch))

        # Footer text
        footer = packet_data.get('footer_text', 'Confidential - For Board Members Only')
        footer_para = Paragraph(f"<i>{footer}</i>", self.styles['Normal'])
        elements.append(footer_para)

        return elements

    def _generate_table_of_contents(self, sections: List[Dict]) -> List:
        """Generate table of contents"""
        elements = []

        # Title
        toc_title = Paragraph("Table of Contents", self.styles['SectionHeader'])
        elements.append(toc_title)
        elements.append(Spacer(1, 0.2 * inch))

        # Build TOC table
        toc_data = [['Section', 'Page']]
        page_num = 3  # Start after cover and TOC

        for section in sections:
            section_title = section.get('title', section['section_type'].replace('_', ' ').title())
            toc_data.append([section_title, str(page_num)])
            page_num += 1

        # Create table
        toc_table = Table(toc_data, colWidths=[5 * inch, 1 * inch])
        toc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(toc_table)
        return elements

    def _generate_section(self, section: Dict) -> List:
        """Generate a section based on type"""
        section_type = section['section_type']

        # Section title
        elements = []
        title = section.get('title', section_type.replace('_', ' ').title())
        title_para = Paragraph(title, self.styles['SectionHeader'])
        elements.append(title_para)
        elements.append(Spacer(1, 0.2 * inch))

        # Generate content based on section type
        if section_type == 'agenda':
            elements.extend(self._generate_agenda(section))
        elif section_type == 'minutes':
            elements.extend(self._generate_minutes(section))
        elif section_type == 'trial_balance':
            elements.extend(self._generate_trial_balance(section))
        elif section_type == 'cash_flow':
            elements.extend(self._generate_cash_flow(section))
        elif section_type == 'ar_aging':
            elements.extend(self._generate_ar_aging(section))
        elif section_type == 'delinquency':
            elements.extend(self._generate_delinquency_report(section))
        elif section_type == 'violations':
            elements.extend(self._generate_violation_summary(section))
        else:
            # Generic section
            content = section.get('content_data', {})
            text = content.get('text', 'No content available for this section.')
            elements.append(Paragraph(text, self.styles['Normal']))

        return elements

    def _generate_agenda(self, section: Dict) -> List:
        """Generate meeting agenda"""
        elements = []
        content = section.get('content_data', {})
        items = content.get('items', [
            'Call to Order',
            'Roll Call',
            'Approval of Minutes',
            'Financial Report',
            'Old Business',
            'New Business',
            'Adjournment'
        ])

        for i, item in enumerate(items, 1):
            para = Paragraph(f"{i}. {item}", self.styles['Normal'])
            elements.append(para)
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _generate_minutes(self, section: Dict) -> List:
        """Generate previous meeting minutes"""
        elements = []
        content = section.get('content_data', {})
        text = content.get('text', 'Previous meeting minutes will be inserted here.')
        para = Paragraph(text, self.styles['Normal'])
        elements.append(para)
        return elements

    def _generate_trial_balance(self, section: Dict) -> List:
        """Generate trial balance report"""
        elements = []
        content = section.get('content_data', {})
        accounts = content.get('accounts', [])

        if not accounts:
            elements.append(Paragraph('No trial balance data available.', self.styles['Normal']))
            return elements

        # Create table
        data = [['Account', 'Debit', 'Credit']]
        total_debit = Decimal('0')
        total_credit = Decimal('0')

        for account in accounts:
            debit = Decimal(account.get('debit', '0'))
            credit = Decimal(account.get('credit', '0'))
            total_debit += debit
            total_credit += credit

            data.append([
                account['name'],
                f"${debit:,.2f}" if debit else '',
                f"${credit:,.2f}" if credit else ''
            ])

        # Add totals
        data.append(['Total', f"${total_debit:,.2f}", f"${total_credit:,.2f}"])

        table = Table(data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        return elements

    def _generate_cash_flow(self, section: Dict) -> List:
        """Generate cash flow statement"""
        elements = []
        content = section.get('content_data', {})

        # Summary paragraph
        beginning = Decimal(content.get('beginning_balance', '0'))
        ending = Decimal(content.get('ending_balance', '0'))
        net_change = ending - beginning

        summary = f"""
        Beginning Balance: ${beginning:,.2f}<br/>
        Ending Balance: ${ending:,.2f}<br/>
        Net Change: ${net_change:,.2f}
        """
        elements.append(Paragraph(summary, self.styles['Normal']))

        return elements

    def _generate_ar_aging(self, section: Dict) -> List:
        """Generate AR aging report"""
        elements = []
        content = section.get('content_data', {})
        aging_data = content.get('aging', [])

        if not aging_data:
            elements.append(Paragraph('No AR aging data available.', self.styles['Normal']))
            return elements

        # Create table
        data = [['Owner', 'Current', '30-60', '60-90', '90+', 'Total']]

        for item in aging_data:
            data.append([
                item['owner'],
                f"${Decimal(item['current']):,.2f}",
                f"${Decimal(item['30_60']):,.2f}",
                f"${Decimal(item['60_90']):,.2f}",
                f"${Decimal(item['90_plus']):,.2f}",
                f"${Decimal(item['total']):,.2f}"
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        return elements

    def _generate_delinquency_report(self, section: Dict) -> List:
        """Generate delinquency summary"""
        elements = []
        content = section.get('content_data', {})

        summary = f"""
        Total Delinquent Accounts: {content.get('total_delinquent', 0)}<br/>
        Total Delinquent Balance: ${Decimal(content.get('total_balance', '0')):,.2f}<br/>
        Accounts 90+ Days: {content.get('accounts_90_plus', 0)}
        """
        elements.append(Paragraph(summary, self.styles['Normal']))

        return elements

    def _generate_violation_summary(self, section: Dict) -> List:
        """Generate violation summary"""
        elements = []
        content = section.get('content_data', {})

        summary = f"""
        Total Violations: {content.get('total_violations', 0)}<br/>
        Open Violations: {content.get('open_violations', 0)}<br/>
        Resolved This Month: {content.get('resolved_this_month', 0)}
        """
        elements.append(Paragraph(summary, self.styles['Normal']))

        return elements
