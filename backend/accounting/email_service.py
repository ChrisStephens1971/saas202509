"""
Email notification service for HOA accounting system.

Handles sending invoices, payment receipts, and overdue reminders.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending accounting-related emails"""

    @staticmethod
    def send_invoice_email(invoice, recipient_email=None):
        """
        Send invoice to owner via email.

        Args:
            invoice: Invoice model instance
            recipient_email: Override owner's email (optional)
        """
        if not recipient_email:
            recipient_email = invoice.owner.email

        if not recipient_email:
            logger.warning(f"Cannot send invoice {invoice.invoice_number}: Owner has no email address")
            return False

        # Prepare context for email template
        context = {
            'invoice': invoice,
            'owner': invoice.owner,
            'tenant': invoice.tenant,
            'line_items': invoice.lines.all(),
            'total_amount': invoice.total_amount,
            'due_date': invoice.due_date,
        }

        # Render email content
        subject = f"Invoice {invoice.invoice_number} - {invoice.tenant.name}"
        html_content = render_to_string('emails/invoice.html', context)
        text_content = render_to_string('emails/invoice.txt', context)

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_alternative(html_content, "text/html")

        # TODO: Attach PDF invoice
        # pdf_data = generate_invoice_pdf(invoice)
        # email.attach(f'invoice-{invoice.invoice_number}.pdf', pdf_data, 'application/pdf')

        try:
            email.send()
            logger.info(f"Sent invoice {invoice.invoice_number} to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send invoice {invoice.invoice_number}: {str(e)}")
            return False

    @staticmethod
    def send_payment_receipt(payment, recipient_email=None):
        """
        Send payment receipt to owner.

        Args:
            payment: Payment model instance
            recipient_email: Override owner's email (optional)
        """
        if not recipient_email:
            recipient_email = payment.owner.email

        if not recipient_email:
            logger.warning(f"Cannot send payment receipt {payment.payment_number}: Owner has no email")
            return False

        # Prepare context
        context = {
            'payment': payment,
            'owner': payment.owner,
            'tenant': payment.tenant,
            'applications': payment.applications.select_related('invoice'),
            'total_amount': payment.amount,
        }

        # Render email content
        subject = f"Payment Receipt {payment.payment_number} - {payment.tenant.name}"
        html_content = render_to_string('emails/payment_receipt.html', context)
        text_content = render_to_string('emails/payment_receipt.txt', context)

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send()
            logger.info(f"Sent payment receipt {payment.payment_number} to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send payment receipt {payment.payment_number}: {str(e)}")
            return False

    @staticmethod
    def send_overdue_reminder(invoice, recipient_email=None):
        """
        Send overdue reminder for invoice.

        Args:
            invoice: Invoice model instance
            recipient_email: Override owner's email (optional)
        """
        if not recipient_email:
            recipient_email = invoice.owner.email

        if not recipient_email:
            logger.warning(f"Cannot send overdue reminder for {invoice.invoice_number}: Owner has no email")
            return False

        # Calculate days overdue
        from datetime import date
        days_overdue = (date.today() - invoice.due_date).days

        # Prepare context
        context = {
            'invoice': invoice,
            'owner': invoice.owner,
            'tenant': invoice.tenant,
            'days_overdue': days_overdue,
            'total_due': invoice.balance,
        }

        # Render email content
        subject = f"OVERDUE: Invoice {invoice.invoice_number} - {invoice.tenant.name}"
        html_content = render_to_string('emails/overdue_reminder.html', context)
        text_content = render_to_string('emails/overdue_reminder.txt', context)

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send()
            logger.info(f"Sent overdue reminder for {invoice.invoice_number} to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send overdue reminder for {invoice.invoice_number}: {str(e)}")
            return False

    @staticmethod
    def send_bulk_overdue_reminders(tenant):
        """
        Send overdue reminders for all overdue invoices in a tenant.

        Args:
            tenant: Tenant model instance

        Returns:
            dict: Summary of emails sent
        """
        from datetime import date
        from .models import Invoice

        # Get all overdue invoices with balance > 0
        overdue_invoices = Invoice.objects.filter(
            tenant=tenant,
            due_date__lt=date.today(),
            balance__gt=Decimal('0.00')
        ).select_related('owner')

        results = {
            'total': overdue_invoices.count(),
            'sent': 0,
            'failed': 0,
            'no_email': 0,
        }

        for invoice in overdue_invoices:
            if not invoice.owner.email:
                results['no_email'] += 1
                continue

            if EmailService.send_overdue_reminder(invoice):
                results['sent'] += 1
            else:
                results['failed'] += 1

        logger.info(f"Sent {results['sent']}/{results['total']} overdue reminders for {tenant.name}")
        return results
