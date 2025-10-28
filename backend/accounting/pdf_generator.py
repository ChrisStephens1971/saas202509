"""
Invoice PDF generation using ReportLab.

Simple, professional invoice PDFs for HOA assessments.
"""

from io import BytesIO
from decimal import Decimal
from datetime import date

# Note: ReportLab may need to be installed: pip install reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_invoice_pdf(invoice, output_path=None):
    """
    Generate PDF for an invoice.

    Args:
        invoice: Invoice model instance
        output_path: Optional file path to save PDF. If None, returns BytesIO buffer.

    Returns:
        BytesIO buffer or None (if output_path provided)

    Raises:
        ImportError: If ReportLab is not installed
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

    # Create buffer or file
    if output_path:
        buffer = open(output_path, 'wb')
    else:
        buffer = BytesIO()

    # Create PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    normal_style = styles['Normal']
    right_align_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    )

    # HOA Header
    hoa_name = invoice.tenant.name
    hoa_address = invoice.tenant.address if hasattr(invoice.tenant, 'address') else ""

    header_data = [
        [Paragraph(hoa_name, title_style), ""],
        [Paragraph(hoa_address, normal_style), ""],
    ]

    header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))

    # Invoice Title
    invoice_title = Paragraph("INVOICE", title_style)
    elements.append(invoice_title)
    elements.append(Spacer(1, 0.2*inch))

    # Invoice details (invoice #, date, due date)
    invoice_info_data = [
        ["Invoice Number:", invoice.invoice_number],
        ["Invoice Date:", invoice.invoice_date.strftime('%B %d, %Y')],
        ["Due Date:", invoice.due_date.strftime('%B %d, %Y')],
        ["Status:", invoice.get_status_display()],
    ]

    invoice_info_table = Table(invoice_info_data, colWidths=[2*inch, 2*inch])
    invoice_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(invoice_info_table)
    elements.append(Spacer(1, 0.3*inch))

    # Bill To section
    bill_to_label = Paragraph("<b>Bill To:</b>", normal_style)
    elements.append(bill_to_label)

    owner_info = f"{invoice.owner.first_name} {invoice.owner.last_name}<br/>"
    if invoice.unit:
        owner_info += f"Unit {invoice.unit.unit_number}<br/>"
    owner_info += invoice.owner.mailing_address.replace('\n', '<br/>')

    bill_to_info = Paragraph(owner_info, normal_style)
    elements.append(bill_to_info)
    elements.append(Spacer(1, 0.3*inch))

    # Invoice lines table
    line_items_data = [
        ["Description", "Amount"]
    ]

    for line in invoice.lines.all().order_by('line_number'):
        line_items_data.append([
            line.description,
            f"${line.amount:,.2f}"
        ])

    # Add subtotal, late fee, total
    line_items_data.append(["", ""])  # Blank row
    line_items_data.append(["Subtotal:", f"${invoice.subtotal:,.2f}"])

    if invoice.late_fee > 0:
        line_items_data.append(["Late Fee:", f"${invoice.late_fee:,.2f}"])

    line_items_data.append(["<b>Total Amount Due:</b>", f"<b>${invoice.total_amount:,.2f}</b>"])

    if invoice.amount_paid > 0:
        line_items_data.append(["Amount Paid:", f"${invoice.amount_paid:,.2f}"])
        line_items_data.append(["<b>Balance Due:</b>", f"<b>${invoice.amount_due:,.2f}</b>"])

    # Convert to Paragraphs for formatting
    formatted_data = []
    for i, row in enumerate(line_items_data):
        if i == 0:  # Header row
            formatted_row = [Paragraph(f"<b>{cell}</b>", normal_style) for cell in row]
        else:
            formatted_row = [Paragraph(str(cell), normal_style if j == 0 else right_align_style) for j, cell in enumerate(row)]
        formatted_data.append(formatted_row)

    line_items_table = Table(formatted_data, colWidths=[4.5*inch, 2*inch])
    line_items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))

    elements.append(line_items_table)
    elements.append(Spacer(1, 0.5*inch))

    # Payment instructions
    payment_instructions = """
    <b>Payment Instructions:</b><br/>
    Please make checks payable to: {hoa_name}<br/>
    Mail payment to: {address}<br/>
    <br/>
    For online payments or questions, please contact:<br/>
    Email: {email}<br/>
    Phone: {phone}
    """.format(
        hoa_name=hoa_name,
        address=hoa_address,
        email=invoice.tenant.primary_contact_email if hasattr(invoice.tenant, 'primary_contact_email') else '',
        phone=invoice.tenant.primary_contact_phone if hasattr(invoice.tenant, 'primary_contact_phone') else ''
    )

    payment_para = Paragraph(payment_instructions, normal_style)
    elements.append(payment_para)

    # Build PDF
    doc.build(elements)

    # Return buffer or close file
    if output_path:
        buffer.close()
        return None
    else:
        buffer.seek(0)
        return buffer


def generate_invoice_pdf_simple(invoice):
    """
    Simple text-based invoice generator (no ReportLab required).
    Returns formatted text representation of invoice.
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"{invoice.tenant.name}".center(80))
    lines.append(f"{invoice.tenant.address if hasattr(invoice.tenant, 'address') else ''}".center(80))
    lines.append("=" * 80)
    lines.append("")
    lines.append("INVOICE".center(80))
    lines.append("")
    lines.append(f"Invoice Number: {invoice.invoice_number}")
    lines.append(f"Invoice Date:   {invoice.invoice_date.strftime('%B %d, %Y')}")
    lines.append(f"Due Date:       {invoice.due_date.strftime('%B %d, %Y')}")
    lines.append(f"Status:         {invoice.get_status_display()}")
    lines.append("")
    lines.append("Bill To:")
    lines.append(f"  {invoice.owner.first_name} {invoice.owner.last_name}")
    if invoice.unit:
        lines.append(f"  Unit {invoice.unit.unit_number}")
    for addr_line in invoice.owner.mailing_address.split('\n'):
        lines.append(f"  {addr_line}")
    lines.append("")
    lines.append("-" * 80)
    lines.append(f"{'Description':<60} {'Amount':>18}")
    lines.append("-" * 80)

    for line in invoice.lines.all().order_by('line_number'):
        lines.append(f"{line.description:<60} ${line.amount:>17,.2f}")

    lines.append("")
    lines.append(f"{'Subtotal:':<60} ${invoice.subtotal:>17,.2f}")

    if invoice.late_fee > 0:
        lines.append(f"{'Late Fee:':<60} ${invoice.late_fee:>17,.2f}")

    lines.append(f"{'TOTAL AMOUNT DUE:':<60} ${invoice.total_amount:>17,.2f}")

    if invoice.amount_paid > 0:
        lines.append(f"{'Amount Paid:':<60} ${invoice.amount_paid:>17,.2f}")
        lines.append(f"{'BALANCE DUE:':<60} ${invoice.amount_due:>17,.2f}")

    lines.append("=" * 80)

    return "\n".join(lines)
