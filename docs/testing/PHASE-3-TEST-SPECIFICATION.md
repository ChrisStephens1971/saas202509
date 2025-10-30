# Phase 3 Test Specification

**Project:** saas202509 (Development)
**Testing Project:** saas202510 (Dedicated QA/Testing)
**Phase:** 3 - Operational Features
**Document Version:** 1.0
**Date:** October 29, 2025

---

## Overview

This document specifies all tests that should be implemented in **saas202510** (the dedicated testing project) to validate Phase 3 operational features.

**Test Categories:**
1. Backend Model Tests
2. Backend API Tests
3. Backend Service Tests
4. Backend Management Command Tests
5. Frontend Component Tests
6. Frontend Integration Tests
7. End-to-End Tests

**Total Estimated Tests:** 150+ test cases

---

## 1. Backend Model Tests

### 1.1 Violation Model Tests

**File:** `saas202510/backend/tests/models/test_violation.py`

**Test Cases (15 tests):**

```python
class ViolationModelTest(TestCase):
    """Test Violation model functionality"""

    def test_create_violation_with_required_fields(self):
        """Should create violation with all required fields"""
        # Create violation
        # Assert fields are set correctly

    def test_violation_number_auto_generated(self):
        """Should auto-generate unique violation number"""
        # Create violation
        # Assert violation_number format: VIOL-YYYY-###

    def test_default_status_is_open(self):
        """Should default to 'open' status"""
        # Create violation
        # Assert status == 'open'

    def test_cure_deadline_validation(self):
        """Should validate cure_deadline is future date"""
        # Try to create with past cure_deadline
        # Assert ValidationError raised

    def test_status_transition_open_to_escalated(self):
        """Should allow open → escalated transition"""
        # Create violation with status='open'
        # Update to status='escalated'
        # Assert status changed

    def test_status_transition_escalated_to_cured(self):
        """Should allow escalated → cured transition"""
        # Create violation with status='escalated'
        # Update to status='cured' with cured_date
        # Assert status changed and cured_date set

    def test_cannot_cure_without_cured_date(self):
        """Should require cured_date when marking as cured"""
        # Try to set status='cured' without cured_date
        # Assert ValidationError raised

    def test_violation_delete_cascade_to_escalations(self):
        """Should cascade delete to escalations"""
        # Create violation with escalations
        # Delete violation
        # Assert escalations are deleted

    def test_violation_delete_cascade_to_fines(self):
        """Should cascade delete to fines"""
        # Create violation with fines
        # Delete violation
        # Assert fines are deleted

    def test_violation_delete_cascade_to_photos(self):
        """Should cascade delete to photos"""
        # Create violation with photos
        # Delete violation
        # Assert photos are deleted (and files cleaned up)

    def test_violation_str_representation(self):
        """Should return formatted string representation"""
        # Create violation
        # Assert str(violation) == "VIOL-2025-001 - Unit 101"

    def test_tenant_isolation(self):
        """Should isolate violations by tenant"""
        # Create violations for different tenants
        # Query for tenant1
        # Assert only tenant1 violations returned

    def test_severity_choices_validation(self):
        """Should validate severity is one of allowed values"""
        # Try to create with invalid severity
        # Assert ValidationError raised

    def test_overdue_property(self):
        """Should calculate if violation is overdue"""
        # Create violation with past cure_deadline
        # Assert violation.is_overdue == True

    def test_days_overdue_calculation(self):
        """Should calculate days overdue correctly"""
        # Create violation with cure_deadline 7 days ago
        # Assert violation.days_overdue == 7
```

### 1.2 ViolationEscalation Model Tests

**File:** `saas202510/backend/tests/models/test_violation_escalation.py`

**Test Cases (8 tests):**

```python
class ViolationEscalationModelTest(TestCase):
    """Test ViolationEscalation model functionality"""

    def test_create_escalation_with_required_fields(self):
        """Should create escalation with required fields"""

    def test_escalation_step_number_increments(self):
        """Should track escalation step number"""
        # Create violation
        # Create escalation step 1
        # Create escalation step 2
        # Assert step_numbers are 1, 2

    def test_escalation_date_defaults_to_today(self):
        """Should default escalation_date to today"""

    def test_fine_amount_optional(self):
        """Should allow escalation without fine"""

    def test_escalation_ordering(self):
        """Should order by escalation_date desc"""

    def test_multiple_escalations_same_violation(self):
        """Should allow multiple escalations for same violation"""

    def test_escalation_str_representation(self):
        """Should return formatted string"""

    def test_tenant_isolation_via_violation(self):
        """Should inherit tenant isolation from violation"""
```

### 1.3 ViolationFine Model Tests

**File:** `saas202510/backend/tests/models/test_violation_fine.py`

**Test Cases (10 tests):**

```python
class ViolationFineModelTest(TestCase):
    """Test ViolationFine model functionality"""

    def test_create_fine_with_required_fields(self):
        """Should create fine with required fields"""

    def test_fine_amount_positive_validation(self):
        """Should validate fine amount is positive"""

    def test_fine_due_date_after_fine_date(self):
        """Should validate due_date >= fine_date"""

    def test_fine_status_defaults_to_pending(self):
        """Should default status to 'pending'"""

    def test_fine_status_transition_to_posted(self):
        """Should allow pending → posted transition"""

    def test_fine_status_transition_to_paid(self):
        """Should allow posted → paid transition"""

    def test_fine_with_invoice_link(self):
        """Should link fine to invoice"""

    def test_fine_without_invoice(self):
        """Should allow fine without invoice"""

    def test_fine_str_representation(self):
        """Should return formatted string"""

    def test_tenant_isolation_via_violation(self):
        """Should inherit tenant isolation from violation"""
```

### 1.4 ARCRequest Model Tests

**File:** `saas202510/backend/tests/models/test_arc_request.py`

**Test Cases (12 tests):**

```python
class ARCRequestModelTest(TestCase):
    """Test ARCRequest model functionality"""

    def test_create_arc_request_with_required_fields(self):
        """Should create ARC request with required fields"""

    def test_request_number_auto_generated(self):
        """Should auto-generate request number: ARC-YYYY-###"""

    def test_default_status_is_draft(self):
        """Should default to 'draft' status"""

    def test_status_transition_draft_to_submitted(self):
        """Should allow draft → submitted transition"""

    def test_status_transition_submitted_to_under_review(self):
        """Should allow submitted → under_review transition"""

    def test_status_transition_under_review_to_approved(self):
        """Should allow under_review → approved transition"""

    def test_status_transition_under_review_to_denied(self):
        """Should allow under_review → denied transition"""

    def test_cannot_approve_without_approval_date(self):
        """Should require approval_date when approving"""

    def test_cannot_deny_without_denial_reason(self):
        """Should require denial_reason when denying"""

    def test_conditional_approval_with_conditions(self):
        """Should store conditions for conditional approval"""

    def test_arc_request_str_representation(self):
        """Should return formatted string"""

    def test_tenant_isolation(self):
        """Should isolate requests by tenant"""
```

### 1.5 WorkOrder Model Tests

**File:** `saas202510/backend/tests/models/test_work_order.py`

**Test Cases (15 tests):**

```python
class WorkOrderModelTest(TestCase):
    """Test WorkOrder model functionality"""

    def test_create_work_order_with_required_fields(self):
        """Should create work order with required fields"""

    def test_work_order_number_auto_generated(self):
        """Should auto-generate work order number: WO-YYYY-###"""

    def test_default_status_is_draft(self):
        """Should default to 'draft' status"""

    def test_priority_defaults_to_medium(self):
        """Should default priority to 'medium'"""

    def test_status_workflow_draft_to_pending(self):
        """Should allow draft → pending transition"""

    def test_status_workflow_pending_to_assigned(self):
        """Should allow pending → assigned transition"""

    def test_status_workflow_assigned_to_in_progress(self):
        """Should allow assigned → in_progress transition"""

    def test_status_workflow_in_progress_to_completed(self):
        """Should allow in_progress → completed transition"""

    def test_cannot_complete_without_actual_cost(self):
        """Should require actual_cost when completing"""

    def test_cost_variance_calculation(self):
        """Should calculate cost variance correctly"""
        # estimated_cost = 500, actual_cost = 650
        # Assert variance = 150, variance_pct = 30%

    def test_work_order_location_unit(self):
        """Should support unit-specific work orders"""

    def test_work_order_location_common_area(self):
        """Should support common area work orders"""

    def test_vendor_assignment_optional(self):
        """Should allow work order without vendor"""

    def test_work_order_str_representation(self):
        """Should return formatted string"""

    def test_tenant_isolation(self):
        """Should isolate work orders by tenant"""
```

### 1.6 Budget Model Tests

**File:** `saas202510/backend/tests/models/test_budget.py`

**Test Cases (10 tests):**

```python
class BudgetModelTest(TestCase):
    """Test Budget model functionality"""

    def test_create_budget_with_required_fields(self):
        """Should create budget with required fields"""

    def test_budget_date_range_validation(self):
        """Should validate end_date >= start_date"""

    def test_budget_status_defaults_to_draft(self):
        """Should default status to 'draft'"""

    def test_budget_status_transition_to_active(self):
        """Should allow draft → active transition"""

    def test_only_one_active_budget_per_fiscal_year(self):
        """Should enforce one active budget per fiscal year per tenant"""

    def test_budget_total_amount_calculation(self):
        """Should calculate total from line items"""

    def test_budget_with_line_items(self):
        """Should support multiple line items"""

    def test_budget_line_item_cascade_delete(self):
        """Should cascade delete line items"""

    def test_budget_str_representation(self):
        """Should return formatted string"""

    def test_tenant_isolation(self):
        """Should isolate budgets by tenant"""
```

**Total Model Tests:** 80+ test cases

---

## 2. Backend API Tests

### 2.1 Violations API Tests

**File:** `saas202510/backend/tests/api/test_violations_api.py`

**Test Cases (20 tests):**

```python
class ViolationsAPITest(APITestCase):
    """Test Violations API endpoints"""

    def test_create_violation_authenticated(self):
        """Should create violation when authenticated"""
        # POST /api/v1/accounting/violations/
        # Assert 201 Created

    def test_create_violation_unauthenticated(self):
        """Should reject unauthenticated requests"""
        # POST without auth
        # Assert 401 Unauthorized

    def test_create_violation_missing_required_fields(self):
        """Should validate required fields"""
        # POST with missing fields
        # Assert 400 Bad Request with field errors

    def test_create_violation_invalid_severity(self):
        """Should validate severity choices"""
        # POST with invalid severity
        # Assert 400 Bad Request

    def test_list_violations_paginated(self):
        """Should return paginated list of violations"""
        # GET /api/v1/accounting/violations/
        # Assert pagination metadata

    def test_list_violations_filtered_by_status(self):
        """Should filter violations by status"""
        # GET /api/v1/accounting/violations/?status=open
        # Assert only open violations returned

    def test_list_violations_filtered_by_unit(self):
        """Should filter violations by unit"""
        # GET /api/v1/accounting/violations/?unit=uuid
        # Assert only unit violations returned

    def test_list_violations_tenant_isolation(self):
        """Should only return current tenant's violations"""
        # Create violations for different tenants
        # GET as tenant1
        # Assert only tenant1 violations returned

    def test_get_violation_by_id(self):
        """Should retrieve single violation"""
        # GET /api/v1/accounting/violations/:id/
        # Assert violation details returned

    def test_get_violation_not_found(self):
        """Should return 404 for non-existent violation"""
        # GET with invalid ID
        # Assert 404 Not Found

    def test_update_violation(self):
        """Should update violation fields"""
        # PUT /api/v1/accounting/violations/:id/
        # Assert fields updated

    def test_update_violation_cannot_change_owner(self):
        """Should prevent changing owner after creation"""
        # PUT with different owner_id
        # Assert 400 Bad Request

    def test_delete_violation(self):
        """Should delete violation"""
        # DELETE /api/v1/accounting/violations/:id/
        # Assert 204 No Content

    def test_escalate_violation_endpoint(self):
        """Should escalate violation via endpoint"""
        # POST /api/v1/accounting/violations/:id/escalate/
        # Assert escalation created
        # Assert notification sent

    def test_escalate_violation_with_fine(self):
        """Should escalate with fine amount"""
        # POST with fine_amount
        # Assert escalation has fine_amount

    def test_mark_violation_cured(self):
        """Should mark violation as cured"""
        # POST /api/v1/accounting/violations/:id/mark-cured/
        # Assert status changed to 'cured'
        # Assert cured_date set

    def test_cannot_escalate_already_cured(self):
        """Should prevent escalating cured violation"""
        # Mark as cured
        # Try to escalate
        # Assert 400 Bad Request

    def test_violation_photos_endpoint(self):
        """Should list photos for violation"""
        # GET /api/v1/accounting/violation-photos/?violation=uuid
        # Assert photos returned

    def test_violation_escalations_endpoint(self):
        """Should list escalations for violation"""
        # GET /api/v1/accounting/violation-escalations/?violation=uuid
        # Assert escalations returned in order

    def test_violation_fines_endpoint(self):
        """Should list fines for violation"""
        # GET /api/v1/accounting/violation-fines/?violation=uuid
        # Assert fines returned
```

### 2.2 ARC Requests API Tests

**File:** `saas202510/backend/tests/api/test_arc_requests_api.py`

**Test Cases (18 tests):**

```python
class ARCRequestsAPITest(APITestCase):
    """Test ARC Requests API endpoints"""

    def test_create_arc_request(self):
        """Should create ARC request"""

    def test_create_arc_request_with_deposit_requirement(self):
        """Should handle deposit requirement"""

    def test_list_arc_requests_filtered_by_status(self):
        """Should filter by status"""

    def test_list_arc_requests_tenant_isolation(self):
        """Should isolate by tenant"""

    def test_get_arc_request_by_id(self):
        """Should retrieve single request"""

    def test_update_arc_request(self):
        """Should update request fields"""

    def test_approve_arc_request(self):
        """Should approve request"""

    def test_approve_with_conditions(self):
        """Should approve with conditions"""

    def test_deny_arc_request(self):
        """Should deny request with reason"""

    def test_request_changes(self):
        """Should request changes"""

    def test_cannot_approve_draft_request(self):
        """Should validate status before approval"""

    def test_arc_documents_endpoint(self):
        """Should list documents for request"""

    def test_arc_reviews_endpoint(self):
        """Should list reviews for request"""

    def test_withdraw_arc_request(self):
        """Should allow owner to withdraw"""

    def test_cannot_modify_after_approval(self):
        """Should prevent modification after approval"""

    def test_arc_request_status_workflow(self):
        """Should follow correct status workflow"""

    def test_notification_on_submission(self):
        """Should notify committee on submission"""

    def test_notification_on_status_change(self):
        """Should notify owner on status change"""
```

### 2.3 Work Orders API Tests

**File:** `saas202510/backend/tests/api/test_work_orders_api.py`

**Test Cases (18 tests):**

```python
class WorkOrdersAPITest(APITestCase):
    """Test Work Orders API endpoints"""

    def test_create_work_order(self):
        """Should create work order"""

    def test_create_work_order_with_unit(self):
        """Should create unit-specific work order"""

    def test_create_work_order_common_area(self):
        """Should create common area work order"""

    def test_list_work_orders_filtered_by_priority(self):
        """Should filter by priority"""

    def test_list_work_orders_filtered_by_status(self):
        """Should filter by status"""

    def test_list_work_orders_tenant_isolation(self):
        """Should isolate by tenant"""

    def test_get_work_order_by_id(self):
        """Should retrieve single work order"""

    def test_update_work_order(self):
        """Should update work order fields"""

    def test_update_status_endpoint(self):
        """Should update status via endpoint"""

    def test_add_comment_endpoint(self):
        """Should add comment"""

    def test_add_internal_comment(self):
        """Should support internal comments"""

    def test_complete_work_order(self):
        """Should complete work order"""

    def test_complete_requires_actual_cost(self):
        """Should require actual_cost to complete"""

    def test_cost_variance_in_response(self):
        """Should include cost variance in response"""

    def test_assign_vendor(self):
        """Should assign vendor to work order"""

    def test_notification_on_vendor_assignment(self):
        """Should notify vendor on assignment"""

    def test_notification_on_completion(self):
        """Should notify manager on completion"""

    def test_work_order_status_workflow(self):
        """Should follow correct status workflow"""
```

### 2.4 Budgets API Tests

**File:** `saas202510/backend/tests/api/test_budgets_api.py`

**Test Cases (12 tests):**

```python
class BudgetsAPITest(APITestCase):
    """Test Budgets API endpoints"""

    def test_create_budget(self):
        """Should create budget"""

    def test_create_budget_with_line_items(self):
        """Should create with nested line items"""

    def test_list_budgets_filtered_by_fiscal_year(self):
        """Should filter by fiscal year"""

    def test_list_budgets_tenant_isolation(self):
        """Should isolate by tenant"""

    def test_get_budget_by_id(self):
        """Should retrieve single budget"""

    def test_update_budget(self):
        """Should update budget fields"""

    def test_update_line_items(self):
        """Should update line items"""

    def test_variance_report_endpoint(self):
        """Should generate variance report"""

    def test_variance_calculation_accuracy(self):
        """Should calculate variances correctly"""

    def test_activate_budget(self):
        """Should activate budget"""

    def test_only_one_active_budget_per_year(self):
        """Should enforce one active budget"""

    def test_budget_total_calculation(self):
        """Should calculate total from line items"""
```

**Total API Tests:** 68+ test cases

---

## 3. Backend Service Tests

### 3.1 NotificationService Tests

**File:** `saas202510/backend/tests/services/test_notification_service.py`

**Test Cases (15 tests):**

```python
class NotificationServiceTest(TestCase):
    """Test NotificationService functionality"""

    def test_send_email_basic(self):
        """Should send email with HTML content"""

    def test_send_email_generates_plain_text(self):
        """Should auto-generate plain text from HTML"""

    def test_notify_violation_created(self):
        """Should send violation created notification"""

    def test_notify_violation_escalated(self):
        """Should send escalation notification"""

    def test_notify_violation_escalated_with_fine(self):
        """Should include fine amount in notification"""

    def test_notify_fine_posted(self):
        """Should send fine posted notification"""

    def test_notify_arc_submitted(self):
        """Should send ARC submission notification to committee"""

    def test_notify_arc_status_change_approved(self):
        """Should send approval notification to owner"""

    def test_notify_arc_status_change_denied(self):
        """Should send denial notification to owner"""

    def test_notify_work_order_assigned(self):
        """Should send assignment notification to vendor"""

    def test_notify_work_order_completed(self):
        """Should send completion notification to manager"""

    def test_notify_budget_alert(self):
        """Should send budget variance alert"""

    def test_notification_includes_tenant_branding(self):
        """Should include tenant name in emails"""

    def test_notification_error_handling(self):
        """Should handle email send failures gracefully"""

    def test_notification_rate_limiting(self):
        """Should respect rate limits"""
```

### 3.2 FileUploadService Tests

**File:** `saas202510/backend/tests/services/test_file_upload_service.py`

**Test Cases (18 tests):**

```python
class FileUploadServiceTest(TestCase):
    """Test FileUploadService functionality"""

    def test_generate_filename(self):
        """Should generate unique filename"""

    def test_filename_includes_timestamp(self):
        """Should include timestamp in filename"""

    def test_filename_preserves_extension(self):
        """Should preserve original file extension"""

    def test_validate_file_size_within_limit(self):
        """Should accept files within size limit"""

    def test_validate_file_size_exceeds_limit(self):
        """Should reject files exceeding size limit"""

    def test_validate_file_extension_allowed(self):
        """Should accept allowed file extensions"""

    def test_validate_file_extension_not_allowed(self):
        """Should reject disallowed file extensions"""

    def test_upload_file_to_storage(self):
        """Should upload file to storage backend"""

    def test_upload_file_returns_url(self):
        """Should return file URL after upload"""

    def test_upload_violation_photo(self):
        """Should upload to violations folder"""

    def test_upload_arc_document_plans(self):
        """Should upload to arc-requests/plans folder"""

    def test_upload_arc_document_photos(self):
        """Should upload to arc-requests/photos folder"""

    def test_upload_work_order_attachment(self):
        """Should upload to work-orders folder"""

    def test_delete_file(self):
        """Should delete file from storage"""

    def test_get_file_info(self):
        """Should retrieve file information"""

    def test_file_upload_error_handling(self):
        """Should handle upload failures"""

    def test_storage_backend_abstraction(self):
        """Should work with both S3 and local storage"""

    def test_file_cleanup_on_model_delete(self):
        """Should clean up files when model is deleted"""
```

### 3.3 ViolationService Tests

**File:** `saas202510/backend/tests/services/test_violation_service.py`

**Test Cases (10 tests):**

```python
class ViolationServiceTest(TestCase):
    """Test ViolationService business logic"""

    def test_calculate_next_escalation_step(self):
        """Should calculate next escalation step correctly"""

    def test_get_fine_amount_for_escalation_step_1(self):
        """Should get fine amount for step 1"""

    def test_get_fine_amount_for_escalation_step_2(self):
        """Should get fine amount for step 2"""

    def test_get_fine_amount_fallback(self):
        """Should fall back to base fine amount"""

    def test_auto_escalate_violation(self):
        """Should auto-escalate violation"""

    def test_post_fine_to_ledger(self):
        """Should post fine to owner ledger"""

    def test_create_fine_invoice(self):
        """Should create invoice for fine"""

    def test_cannot_escalate_cured_violation(self):
        """Should prevent escalating cured violation"""

    def test_escalation_triggers_notification(self):
        """Should trigger notification on escalation"""

    def test_status_workflow_validation(self):
        """Should validate status transitions"""
```

### 3.4 BudgetService Tests

**File:** `saas202510/backend/tests/services/test_budget_service.py`

**Test Cases (12 tests):**

```python
class BudgetServiceTest(TestCase):
    """Test BudgetService business logic"""

    def test_calculate_actual_spend_for_expense(self):
        """Should sum debits for expense accounts"""

    def test_calculate_actual_spend_for_revenue(self):
        """Should sum credits for revenue accounts"""

    def test_calculate_variance_amount(self):
        """Should calculate variance amount"""

    def test_calculate_variance_percentage(self):
        """Should calculate variance percentage"""

    def test_identify_variances_above_threshold(self):
        """Should identify items exceeding threshold"""

    def test_variance_severity_warning(self):
        """Should classify 20-30% as warning"""

    def test_variance_severity_critical(self):
        """Should classify >30% as critical"""

    def test_ytd_spend_calculation(self):
        """Should calculate YTD spend"""

    def test_budget_analysis_report(self):
        """Should generate analysis report"""

    def test_variance_triggers_notification(self):
        """Should trigger notification for variances"""

    def test_budget_date_range_filtering(self):
        """Should only include entries within budget period"""

    def test_tenant_isolation_in_calculations(self):
        """Should isolate calculations by tenant"""
```

**Total Service Tests:** 55+ test cases

---

## 4. Backend Management Command Tests

### 4.1 Escalate Overdue Violations Command Tests

**File:** `saas202510/backend/tests/commands/test_escalate_overdue_violations.py`

**Test Cases (12 tests):**

```python
class EscalateOverdueViolationsCommandTest(TestCase):
    """Test escalate_overdue_violations management command"""

    def test_command_dry_run_mode(self):
        """Should show what would be escalated without escalating"""
        # Run with --dry-run
        # Assert no escalations created

    def test_command_identifies_overdue_violations(self):
        """Should find violations past cure deadline"""
        # Create overdue violation
        # Run command
        # Assert violation identified

    def test_command_escalates_overdue_violations(self):
        """Should create escalation records"""
        # Create overdue violation
        # Run command
        # Assert escalation created

    def test_command_applies_grace_period(self):
        """Should respect grace period"""
        # Create violation 1 day overdue
        # Run with --days-grace 2
        # Assert not escalated

    def test_command_sends_notifications(self):
        """Should send email notifications"""
        # Create overdue violation
        # Run command
        # Assert notification sent

    def test_command_updates_violation_status(self):
        """Should update violation status to escalated"""

    def test_command_skips_already_escalated_today(self):
        """Should prevent duplicate escalations on same day"""

    def test_command_handles_multiple_violations(self):
        """Should process multiple violations"""

    def test_command_error_handling(self):
        """Should handle errors gracefully"""

    def test_command_output_formatting(self):
        """Should output formatted summary"""

    def test_command_tenant_isolation(self):
        """Should process violations for all tenants"""

    def test_command_performance_with_large_dataset(self):
        """Should perform efficiently with many violations"""
```

### 4.2 Check Budget Variances Command Tests

**File:** `saas202510/backend/tests/commands/test_check_budget_variances.py`

**Test Cases (12 tests):**

```python
class CheckBudgetVariancesCommandTest(TestCase):
    """Test check_budget_variances management command"""

    def test_command_dry_run_mode(self):
        """Should show what would be alerted without sending"""

    def test_command_identifies_variance_warnings(self):
        """Should identify items exceeding warning threshold"""

    def test_command_identifies_variance_criticals(self):
        """Should identify items exceeding critical threshold"""

    def test_command_custom_thresholds(self):
        """Should accept custom threshold parameters"""

    def test_command_sends_alert_notifications(self):
        """Should send email alerts"""

    def test_command_processes_all_active_budgets(self):
        """Should check all active budgets"""

    def test_command_specific_budget_only(self):
        """Should process specific budget with --budget-id"""

    def test_command_calculates_variances_correctly(self):
        """Should calculate accurate variance amounts"""

    def test_command_groups_by_severity(self):
        """Should group alerts by severity level"""

    def test_command_output_formatting(self):
        """Should output formatted summary"""

    def test_command_tenant_isolation(self):
        """Should process budgets for all tenants"""

    def test_command_performance_with_large_dataset(self):
        """Should perform efficiently with many line items"""
```

**Total Management Command Tests:** 24+ test cases

---

## 5. Frontend Component Tests

### 5.1 CreateViolationPage Tests

**File:** `saas202510/frontend/tests/pages/violations/CreateViolationPage.test.tsx`

**Test Cases (12 tests):**

```typescript
describe('CreateViolationPage', () => {
  test('renders form with all fields', () => {
    // Render component
    // Assert all form fields present
  });

  test('loads owner options from API', async () => {
    // Mock API response
    // Render component
    // Assert owner dropdown populated
  });

  test('loads unit options from API', async () => {
    // Mock API response
    // Assert unit dropdown populated
  });

  test('loads violation type options from API', async () => {
    // Mock API response
    // Assert violation type dropdown populated
  });

  test('validates required fields on submit', async () => {
    // Submit empty form
    // Assert validation errors displayed
  });

  test('sets default cure deadline to 14 days from now', () => {
    // Render component
    // Assert cure_deadline field has correct default
  });

  test('handles file upload', async () => {
    // Select files
    // Assert file count displayed
  });

  test('submits form with valid data', async () => {
    // Fill form
    // Submit
    // Assert API called with correct data
  });

  test('navigates to violation detail on success', async () => {
    // Submit form
    // Assert navigation occurred
  });

  test('displays error message on API failure', async () => {
    // Mock API error
    // Submit form
    // Assert error message displayed
  });

  test('disables submit button while submitting', async () => {
    // Start submit
    // Assert button disabled
  });

  test('navigates back on cancel', async () => {
    // Click cancel
    // Assert navigation occurred
  });
});
```

### 5.2 ViolationDetailPage Tests

**File:** `saas202510/frontend/tests/pages/violations/ViolationDetailPage.test.tsx`

**Test Cases (15 tests):**

```typescript
describe('ViolationDetailPage', () => {
  test('renders violation details', async () => {
    // Mock API response
    // Render component
    // Assert details displayed
  });

  test('renders escalation history', async () => {
    // Mock violation with escalations
    // Assert escalation timeline displayed
  });

  test('renders fines table', async () => {
    // Mock violation with fines
    // Assert fines table displayed
  });

  test('renders photo gallery', async () => {
    // Mock violation with photos
    // Assert photos displayed
  });

  test('shows escalate button for open violations', () => {
    // Mock open violation
    // Assert escalate button visible
  });

  test('hides escalate button for cured violations', () => {
    // Mock cured violation
    // Assert escalate button hidden
  });

  test('opens escalate modal on button click', async () => {
    // Click escalate button
    // Assert modal opened
  });

  test('submits escalation with fine amount', async () => {
    // Open modal
    // Fill form
    // Submit
    // Assert API called
  });

  test('opens mark as cured modal', async () => {
    // Click mark as cured button
    // Assert modal opened
  });

  test('submits cure with date and notes', async () => {
    // Fill cure form
    // Submit
    // Assert API called
  });

  test('opens add fine modal', async () => {
    // Click add fine button
    // Assert modal opened
  });

  test('displays severity badge with correct color', () => {
    // Mock critical violation
    // Assert badge color is red
  });

  test('displays status badge with correct color', () => {
    // Mock escalated violation
    // Assert badge color is orange
  });

  test('refetches data after successful action', async () => {
    // Submit escalation
    // Assert data refetched
  });

  test('navigates back to list', async () => {
    // Click back button
    // Assert navigation occurred
  });
});
```

### 5.3 WorkOrderDetailPage Tests

**File:** `saas202510/frontend/tests/pages/workorders/WorkOrderDetailPage.test.tsx`

**Test Cases (15 tests):**

```typescript
describe('WorkOrderDetailPage', () => {
  test('renders work order details', async () => {});
  test('renders vendor information', async () => {});
  test('renders cost tracking with variance', async () => {});
  test('renders comments timeline', async () => {});
  test('renders attachments gallery', async () => {});
  test('shows update status button', async () => {});
  test('opens update status modal', async () => {});
  test('submits status update', async () => {});
  test('opens add comment modal', async () => {});
  test('submits comment with type', async () => {});
  test('supports internal comments', async () => {});
  test('opens complete modal', async () => {});
  test('requires actual cost to complete', async () => {});
  test('displays priority badge with correct color', async () => {});
  test('displays status badge with correct color', async () => {});
});
```

### 5.4 ARCRequestDetailPage Tests

**File:** `saas202510/frontend/tests/pages/arc/ARCRequestDetailPage.test.tsx`

**Test Cases (15 tests):**

```typescript
describe('ARCRequestDetailPage', () => {
  test('renders request details', async () => {});
  test('renders review history', async () => {});
  test('renders grouped documents', async () => {});
  test('shows approve button for submitted requests', async () => {});
  test('hides approve button for approved requests', async () => {});
  test('opens approve modal', async () => {});
  test('submits approval with conditions', async () => {});
  test('submits unconditional approval', async () => {});
  test('opens deny modal', async () => {});
  test('requires denial reason', async () => {});
  test('submits denial with reason', async () => {});
  test('opens request changes modal', async () => {});
  test('submits requested changes', async () => {});
  test('displays status badge with correct color', async () => {});
  test('displays deposit requirement notice', async () => {});
});
```

**Total Frontend Component Tests:** 57+ test cases

---

## 6. Frontend Integration Tests

### 6.1 Violation Workflow Integration Tests

**File:** `saas202510/frontend/tests/integration/violation_workflow.test.tsx`

**Test Cases (8 tests):**

```typescript
describe('Violation Workflow Integration', () => {
  test('complete flow: create violation', async () => {
    // Navigate to create page
    // Fill form
    // Submit
    // Assert redirected to detail page
  });

  test('complete flow: escalate violation', async () => {
    // Navigate to detail page
    // Click escalate
    // Fill modal
    // Submit
    // Assert escalation appears in history
  });

  test('complete flow: mark as cured', async () => {
    // Navigate to detail page
    // Click mark as cured
    // Fill modal
    // Submit
    // Assert status changed to cured
  });

  test('complete flow: add fine', async () => {
    // Navigate to detail page
    // Click add fine
    // Fill modal
    // Submit
    // Assert fine appears in table
  });

  test('complete flow: upload photos', async () => {
    // Navigate to create page
    // Select photo files
    // Submit form
    // Navigate to detail page
    // Assert photos displayed
  });

  test('form validation errors prevent submission', async () => {
    // Fill partial form
    // Submit
    // Assert validation errors
    // Assert not submitted
  });

  test('optimistic updates on escalation', async () => {
    // Mock slow API
    // Submit escalation
    // Assert UI updates optimistically
  });

  test('error recovery on failed submission', async () => {
    // Mock API error
    // Submit form
    // Assert error message
    // Fix error
    // Retry
    // Assert success
  });
});
```

### 6.2 ARC Request Workflow Integration Tests

**File:** `saas202510/frontend/tests/integration/arc_request_workflow.test.tsx`

**Test Cases (8 tests):**

```typescript
describe('ARC Request Workflow Integration', () => {
  test('complete flow: submit request', async () => {});
  test('complete flow: upload multiple documents', async () => {});
  test('complete flow: approve request', async () => {});
  test('complete flow: approve with conditions', async () => {});
  test('complete flow: deny request', async () => {});
  test('complete flow: request changes', async () => {});
  test('document upload progress tracking', async () => {});
  test('validation prevents incomplete submission', async () => {});
});
```

### 6.3 Work Order Workflow Integration Tests

**File:** `saas202510/frontend/tests/integration/work_order_workflow.test.tsx`

**Test Cases (8 tests):**

```typescript
describe('Work Order Workflow Integration', () => {
  test('complete flow: create work order', async () => {});
  test('complete flow: assign vendor', async () => {});
  test('complete flow: update status', async () => {});
  test('complete flow: add comments', async () => {});
  test('complete flow: complete work order', async () => {});
  test('cost variance calculation and display', async () => {});
  test('conditional unit field based on location type', async () => {});
  test('validation prevents incomplete submission', async () => {});
});
```

**Total Integration Tests:** 24+ test cases

---

## 7. End-to-End Tests

### 7.1 Violation E2E Tests

**File:** `saas202510/e2e/tests/violations.spec.ts`

**Test Cases (6 tests):**

```typescript
describe('Violations E2E', () => {
  test('property manager creates violation', async ({ page }) => {
    // Login as property manager
    // Navigate to violations
    // Click create
    // Fill form
    // Upload photo
    // Submit
    // Verify violation created
    // Verify owner receives email
  });

  test('violation auto-escalates after deadline', async ({ page }) => {
    // Create violation with past deadline
    // Run escalation command
    // Verify escalation created
    // Verify owner receives email
  });

  test('violation marked as cured', async ({ page }) => {
    // Navigate to violation
    // Click mark as cured
    // Fill form
    // Submit
    // Verify status changed
  });

  test('fine posted to owner ledger', async ({ page }) => {
    // Create violation
    // Escalate with fine
    // Verify fine appears on owner ledger
    // Verify invoice created
  });

  test('violation lifecycle: open → escalated → cured', async ({ page }) => {
    // Create violation
    // Wait for deadline
    // Escalate
    // Mark as cured
    // Verify complete workflow
  });

  test('violation search and filtering', async ({ page }) => {
    // Create multiple violations
    // Filter by status
    // Filter by unit
    // Search by description
    // Verify correct results
  });
});
```

### 7.2 ARC Request E2E Tests

**File:** `saas202510/e2e/tests/arc_requests.spec.ts`

**Test Cases (6 tests):**

```typescript
describe('ARC Requests E2E', () => {
  test('owner submits ARC request', async ({ page }) => {
    // Login as owner
    // Navigate to ARC requests
    // Click submit
    // Fill form
    // Upload documents
    // Submit
    // Verify request submitted
    // Verify committee receives email
  });

  test('committee reviews and approves request', async ({ page }) => {
    // Login as committee member
    // Navigate to pending requests
    // Click request
    // Review documents
    // Click approve
    // Add conditions
    // Submit
    // Verify owner receives email
  });

  test('committee denies request', async ({ page }) => {
    // Login as committee member
    // Navigate to request
    // Click deny
    // Enter reason
    // Submit
    // Verify owner receives email
  });

  test('committee requests changes', async ({ page }) => {
    // Navigate to request
    // Click request changes
    // Enter requested changes
    // Submit
    // Verify owner notified
  });

  test('deposit requirement displayed', async ({ page }) => {
    // Create request for type with deposit
    // Verify deposit notice shown
  });

  test('document gallery organized by type', async ({ page }) => {
    // Submit request with multiple document types
    // Navigate to detail page
    // Verify documents grouped by type
  });
});
```

### 7.3 Work Order E2E Tests

**File:** `saas202510/e2e/tests/work_orders.spec.ts`

**Test Cases (6 tests):**

```typescript
describe('Work Orders E2E', () => {
  test('manager creates work order', async ({ page }) => {});
  test('vendor assigned to work order', async ({ page }) => {});
  test('work order status progression', async ({ page }) => {});
  test('work order completed with cost variance', async ({ page }) => {});
  test('comments timeline tracking', async ({ page }) => {});
  test('attachments uploaded and displayed', async ({ page }) => {});
});
```

### 7.4 Budget Monitoring E2E Tests

**File:** `saas202510/e2e/tests/budgets.spec.ts`

**Test Cases (4 tests):**

```typescript
describe('Budgets E2E', () => {
  test('budget created with line items', async ({ page }) => {});
  test('spending tracked against budget', async ({ page }) => {});
  test('variance alert triggered', async ({ page }) => {});
  test('budget report generated', async ({ page }) => {});
});
```

**Total E2E Tests:** 22+ test cases

---

## Test Execution Summary

### Total Test Count: 150+ tests

1. **Backend Model Tests:** 80+ tests
2. **Backend API Tests:** 68+ tests
3. **Backend Service Tests:** 55+ tests
4. **Backend Management Command Tests:** 24+ tests
5. **Frontend Component Tests:** 57+ tests
6. **Frontend Integration Tests:** 24+ tests
7. **End-to-End Tests:** 22+ tests

---

## Test Implementation Priority

### Phase 1: Critical Path Tests (Week 1)
**Priority: HIGH**

1. Violation Model Tests (15 tests)
2. Violations API Tests (20 tests)
3. ViolationService Tests (10 tests)
4. Escalate Command Tests (12 tests)
5. CreateViolationPage Tests (12 tests)
6. ViolationDetailPage Tests (15 tests)

**Total: 84 tests covering core violation workflow**

### Phase 2: ARC & Work Orders (Week 2)
**Priority: HIGH**

1. ARCRequest Model Tests (12 tests)
2. WorkOrder Model Tests (15 tests)
3. ARC API Tests (18 tests)
4. Work Orders API Tests (18 tests)
5. ARCRequestDetailPage Tests (15 tests)
6. WorkOrderDetailPage Tests (15 tests)

**Total: 93 tests covering ARC and work order features**

### Phase 3: Services & Automation (Week 3)
**Priority: MEDIUM**

1. NotificationService Tests (15 tests)
2. FileUploadService Tests (18 tests)
3. BudgetService Tests (12 tests)
4. Budget Command Tests (12 tests)
5. Integration Tests (24 tests)

**Total: 81 tests covering services and automation**

### Phase 4: E2E & Edge Cases (Week 4)
**Priority: MEDIUM**

1. Violation E2E Tests (6 tests)
2. ARC E2E Tests (6 tests)
3. Work Order E2E Tests (6 tests)
4. Budget E2E Tests (4 tests)
5. Edge case tests for all features

**Total: 22+ E2E tests**

---

## Test Data Fixtures

Create fixtures in `saas202510/backend/fixtures/`:

1. **test_tenants.json** - Test tenant data
2. **test_owners.json** - Test owner data
3. **test_units.json** - Test unit data
4. **test_violation_types.json** - Violation type configurations
5. **test_arc_request_types.json** - ARC request type configurations
6. **test_work_order_categories.json** - Work order categories
7. **test_vendors.json** - Vendor data
8. **test_budgets.json** - Sample budgets with line items

---

## CI/CD Integration

### GitHub Actions Workflow

**File:** `saas202510/.github/workflows/test.yml`

```yaml
name: Phase 3 Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run backend tests
        run: |
          python manage.py test --parallel

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Run frontend tests
        run: npm test -- --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Playwright
        run: npx playwright install
      - name: Run E2E tests
        run: npm run test:e2e
```

---

## Test Coverage Goals

### Backend Coverage Targets
- **Models:** 95%+ line coverage
- **APIs:** 90%+ line coverage
- **Services:** 95%+ line coverage
- **Management Commands:** 85%+ line coverage

### Frontend Coverage Targets
- **Components:** 80%+ line coverage
- **Integration:** 70%+ line coverage
- **E2E:** Critical paths covered

### Overall Target
- **Minimum:** 85% overall code coverage
- **Goal:** 90%+ overall code coverage

---

## Documentation

All tests should include:

1. **Descriptive test names** - Clear what is being tested
2. **AAA pattern** - Arrange, Act, Assert structure
3. **Comments for complex logic** - Explain non-obvious test setup
4. **Assertions with messages** - Clear failure messages

**Example:**
```python
def test_violation_auto_escalates_after_deadline(self):
    """
    Should automatically escalate violation when cure deadline passes.

    Scenario:
    1. Create violation with cure_deadline 7 days ago
    2. Run escalation command
    3. Assert escalation created with step_number=1
    4. Assert violation status changed to 'escalated'
    5. Assert owner receives email notification
    """
    # Arrange
    violation = create_violation(cure_deadline=date.today() - timedelta(days=7))

    # Act
    call_command('escalate_overdue_violations')

    # Assert
    violation.refresh_from_db()
    self.assertEqual(violation.status, 'escalated')
    self.assertEqual(violation.escalations.count(), 1)
    self.assertEqual(len(mail.outbox), 1)
```

---

## Next Steps

**To implement these tests in saas202510:**

1. Set up testing project structure
2. Install testing dependencies (pytest, pytest-django, playwright)
3. Create test data fixtures
4. Implement tests in priority order (Phase 1-4)
5. Set up CI/CD pipeline
6. Monitor coverage and add tests for gaps
7. Document test results and any bugs found

**Estimated Timeline:** 4 weeks for full test implementation

---

**Document Version:** 1.0
**Date:** October 29, 2025
**Status:** Ready for Implementation in saas202510
**Total Test Cases:** 150+
