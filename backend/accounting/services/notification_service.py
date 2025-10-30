"""
Notification Service - Email Notifications for Phase 3

Handles email notifications for:
- Violation escalations
- ARC request status changes
- Work order assignments and completions
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class NotificationService:
    """Service for sending email notifications."""

    @staticmethod
    def send_email(subject, html_content, recipient_list, from_email=None):
        """
        Send an email notification.

        Args:
            subject: Email subject
            html_content: HTML email content
            recipient_list: List of recipient email addresses
            from_email: Sender email (optional, uses default)

        Returns:
            int: Number of emails sent
        """
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        plain_message = strip_tags(html_content)

        return send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_content,
            fail_silently=False,
        )

    # ===========================
    # Violation Notifications
    # ===========================

    @staticmethod
    def notify_violation_created(violation):
        """
        Notify owner when a violation is created.

        Args:
            violation: Violation instance
        """
        subject = f"Notice of Violation - {violation.violation_type.name}"

        html_content = f"""
        <html>
        <body>
            <h2>Notice of Violation</h2>
            <p>Dear {violation.owner.first_name} {violation.owner.last_name},</p>

            <p>A violation has been reported for your property at <strong>Unit {violation.unit.unit_number}</strong>.</p>

            <h3>Violation Details:</h3>
            <ul>
                <li><strong>Type:</strong> {violation.violation_type.name}</li>
                <li><strong>Description:</strong> {violation.description}</li>
                <li><strong>Reported Date:</strong> {violation.reported_date}</li>
                <li><strong>Cure Deadline:</strong> {violation.cure_deadline}</li>
            </ul>

            <p>Please address this violation by the cure deadline to avoid further action.</p>

            <p>If you have any questions, please contact the property management office.</p>

            <p>Thank you,<br>
            {violation.tenant.name} Management</p>
        </body>
        </html>
        """

        return NotificationService.send_email(
            subject=subject,
            html_content=html_content,
            recipient_list=[violation.owner.email]
        )

    @staticmethod
    def notify_violation_escalated(violation, escalation):
        """
        Notify owner when a violation is escalated.

        Args:
            violation: Violation instance
            escalation: ViolationEscalation instance
        """
        subject = f"Violation Escalated - {violation.violation_type.name}"

        fine_info = ""
        if escalation.fine_amount and escalation.fine_amount > 0:
            fine_info = f"<p><strong>Fine Amount: ${escalation.fine_amount}</strong></p>"

        html_content = f"""
        <html>
        <body>
            <h2>Violation Escalation Notice</h2>
            <p>Dear {violation.owner.first_name} {violation.owner.last_name},</p>

            <p>The violation at <strong>Unit {violation.unit.unit_number}</strong> has been escalated.</p>

            <h3>Violation Details:</h3>
            <ul>
                <li><strong>Type:</strong> {violation.violation_type.name}</li>
                <li><strong>Description:</strong> {violation.description}</li>
                <li><strong>Escalation Step:</strong> {escalation.step_number}</li>
                <li><strong>Escalation Date:</strong> {escalation.escalation_date}</li>
            </ul>

            {fine_info}

            <p><strong>Action Required:</strong> Please address this violation immediately to avoid further fines.</p>

            <p>Thank you,<br>
            {violation.tenant.name} Management</p>
        </body>
        </html>
        """

        return NotificationService.send_email(
            subject=subject,
            html_content=html_content,
            recipient_list=[violation.owner.email]
        )

    @staticmethod
    def notify_fine_posted(fine):
        """
        Notify owner when a fine is posted to their ledger.

        Args:
            fine: ViolationFine instance
        """
        violation = fine.violation
        subject = f"Fine Posted to Account - ${fine.amount}"

        html_content = f"""
        <html>
        <body>
            <h2>Fine Posted to Your Account</h2>
            <p>Dear {violation.owner.first_name} {violation.owner.last_name},</p>

            <p>A fine has been posted to your account for the violation at <strong>Unit {violation.unit.unit_number}</strong>.</p>

            <h3>Fine Details:</h3>
            <ul>
                <li><strong>Amount:</strong> ${fine.amount}</li>
                <li><strong>Fine Date:</strong> {fine.fine_date}</li>
                <li><strong>Due Date:</strong> {fine.due_date}</li>
                <li><strong>Invoice Number:</strong> {fine.invoice.invoice_number if fine.invoice else 'Pending'}</li>
            </ul>

            <h3>Violation:</h3>
            <ul>
                <li><strong>Type:</strong> {violation.violation_type.name}</li>
                <li><strong>Description:</strong> {violation.description}</li>
            </ul>

            <p>Please remit payment by the due date to avoid additional penalties.</p>

            <p>Thank you,<br>
            {violation.tenant.name} Management</p>
        </body>
        </html>
        """

        return NotificationService.send_email(
            subject=subject,
            html_content=html_content,
            recipient_list=[violation.owner.email]
        )

    # ===========================
    # ARC Request Notifications
    # ===========================

    @staticmethod
    def notify_arc_submitted(arc_request):
        """
        Notify committee when an ARC request is submitted.

        Args:
            arc_request: ARCRequest instance
        """
        subject = f"New ARC Request Submitted - Unit {arc_request.unit.unit_number}"

        html_content = f"""
        <html>
        <body>
            <h2>New ARC Request</h2>
            <p>A new architectural review request has been submitted.</p>

            <h3>Request Details:</h3>
            <ul>
                <li><strong>Request Number:</strong> {arc_request.request_number}</li>
                <li><strong>Unit:</strong> {arc_request.unit.unit_number}</li>
                <li><strong>Owner:</strong> {arc_request.owner.first_name} {arc_request.owner.last_name}</li>
                <li><strong>Type:</strong> {arc_request.request_type.name}</li>
                <li><strong>Submission Date:</strong> {arc_request.submission_date}</li>
            </ul>

            <h3>Project Description:</h3>
            <p>{arc_request.project_description}</p>

            <p>Please log in to review this request.</p>

            <p>Thank you,<br>
            {arc_request.tenant.name} System</p>
        </body>
        </html>
        """

        # Get committee members (would need a CommitteeMember model in production)
        # For now, send to tenant admin email
        recipient_list = [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else []

        if recipient_list:
            return NotificationService.send_email(
                subject=subject,
                html_content=html_content,
                recipient_list=recipient_list
            )
        return 0

    @staticmethod
    def notify_arc_status_change(arc_request, old_status, new_status):
        """
        Notify owner when ARC request status changes.

        Args:
            arc_request: ARCRequest instance
            old_status: Previous status
            new_status: New status
        """
        status_messages = {
            'approved': 'Your request has been <strong>APPROVED</strong>!',
            'denied': 'Your request has been <strong>DENIED</strong>.',
            'conditional_approval': 'Your request has been <strong>CONDITIONALLY APPROVED</strong>.',
            'under_review': 'Your request is now <strong>UNDER REVIEW</strong>.',
        }

        subject = f"ARC Request {new_status.replace('_', ' ').title()} - {arc_request.request_number}"

        status_message = status_messages.get(new_status, f'Status updated to {new_status}')

        html_content = f"""
        <html>
        <body>
            <h2>ARC Request Status Update</h2>
            <p>Dear {arc_request.owner.first_name} {arc_request.owner.last_name},</p>

            <p>{status_message}</p>

            <h3>Request Details:</h3>
            <ul>
                <li><strong>Request Number:</strong> {arc_request.request_number}</li>
                <li><strong>Unit:</strong> {arc_request.unit.unit_number}</li>
                <li><strong>Type:</strong> {arc_request.request_type.name}</li>
                <li><strong>Project:</strong> {arc_request.project_description}</li>
            </ul>

            <p>Please log in to view full details and any conditions or comments.</p>

            <p>Thank you,<br>
            {arc_request.tenant.name} Architectural Review Committee</p>
        </body>
        </html>
        """

        return NotificationService.send_email(
            subject=subject,
            html_content=html_content,
            recipient_list=[arc_request.owner.email]
        )

    # ===========================
    # Work Order Notifications
    # ===========================

    @staticmethod
    def notify_work_order_assigned(work_order):
        """
        Notify vendor when a work order is assigned to them.

        Args:
            work_order: WorkOrder instance
        """
        if not work_order.assigned_to_vendor:
            return 0

        vendor = work_order.assigned_to_vendor
        subject = f"Work Order Assigned - {work_order.work_order_number}"

        html_content = f"""
        <html>
        <body>
            <h2>New Work Order Assignment</h2>
            <p>Dear {vendor.contact_name},</p>

            <p>A new work order has been assigned to {vendor.name}.</p>

            <h3>Work Order Details:</h3>
            <ul>
                <li><strong>Work Order #:</strong> {work_order.work_order_number}</li>
                <li><strong>Title:</strong> {work_order.title}</li>
                <li><strong>Category:</strong> {work_order.category.name if work_order.category else 'N/A'}</li>
                <li><strong>Priority:</strong> {work_order.get_priority_display()}</li>
                <li><strong>Estimated Cost:</strong> ${work_order.estimated_cost or 'TBD'}</li>
                <li><strong>Created:</strong> {work_order.created_date}</li>
            </ul>

            <h3>Description:</h3>
            <p>{work_order.description}</p>

            <p>Please contact us to schedule this work.</p>

            <p>Thank you,<br>
            {work_order.tenant.name} Management</p>
        </body>
        </html>
        """

        return NotificationService.send_email(
            subject=subject,
            html_content=html_content,
            recipient_list=[vendor.email]
        )

    @staticmethod
    def notify_work_order_completed(work_order):
        """
        Notify property manager when a work order is completed.

        Args:
            work_order: WorkOrder instance
        """
        subject = f"Work Order Completed - {work_order.work_order_number}"

        actual_cost = work_order.actual_cost or work_order.estimated_cost or 0
        variance = ""
        if work_order.estimated_cost and work_order.actual_cost:
            diff = work_order.actual_cost - work_order.estimated_cost
            if diff > 0:
                variance = f"<p><strong>Note:</strong> Actual cost was ${diff} over estimate.</p>"
            elif diff < 0:
                variance = f"<p><strong>Note:</strong> Actual cost was ${abs(diff)} under estimate.</p>"

        html_content = f"""
        <html>
        <body>
            <h2>Work Order Completed</h2>

            <h3>Work Order Details:</h3>
            <ul>
                <li><strong>Work Order #:</strong> {work_order.work_order_number}</li>
                <li><strong>Title:</strong> {work_order.title}</li>
                <li><strong>Vendor:</strong> {work_order.assigned_to_vendor.name if work_order.assigned_to_vendor else 'N/A'}</li>
                <li><strong>Estimated Cost:</strong> ${work_order.estimated_cost or 'N/A'}</li>
                <li><strong>Actual Cost:</strong> ${actual_cost}</li>
                <li><strong>Completed:</strong> {work_order.completed_date}</li>
            </ul>

            {variance}

            <p>Please review and close this work order.</p>

            <p>Thank you,<br>
            {work_order.tenant.name} System</p>
        </body>
        </html>
        """

        # Send to property manager (would need proper user lookup in production)
        recipient_list = [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else []

        if recipient_list:
            return NotificationService.send_email(
                subject=subject,
                html_content=html_content,
                recipient_list=recipient_list
            )
        return 0

    # ===========================
    # Budget Alerts
    # ===========================

    @staticmethod
    def notify_budget_alert(budget, alert_items):
        """
        Notify treasurer when budget variance exceeds threshold.

        Args:
            budget: Budget instance
            alert_items: List of budget line items exceeding threshold
        """
        subject = f"Budget Alert - {budget.name}"

        alert_rows = ""
        for item in alert_items:
            alert_rows += f"""
            <tr>
                <td>{item['account'].name}</td>
                <td>${item['budgeted']}</td>
                <td>${item['actual']}</td>
                <td>${item['variance']}</td>
                <td>{item['variance_pct']:.1f}%</td>
                <td><span style="color: {'red' if item['severity'] == 'critical' else 'orange'}">
                    {item['severity'].upper()}
                </span></td>
            </tr>
            """

        html_content = f"""
        <html>
        <body>
            <h2>Budget Variance Alert</h2>
            <p>The following budget lines have exceeded variance thresholds:</p>

            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>Account</th>
                        <th>Budgeted</th>
                        <th>Actual</th>
                        <th>Variance</th>
                        <th>Variance %</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>
                    {alert_rows}
                </tbody>
            </table>

            <p>Please review spending in these categories.</p>

            <p>Thank you,<br>
            {budget.tenant.name} System</p>
        </body>
        </html>
        """

        # Send to treasurer (would need proper user lookup in production)
        recipient_list = [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else []

        if recipient_list:
            return NotificationService.send_email(
                subject=subject,
                html_content=html_content,
                recipient_list=recipient_list
            )
        return 0
