"""
URL configuration for accounting API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    AccountViewSet, OwnerViewSet, InvoiceViewSet, PaymentViewSet,
    BudgetViewSet, BudgetLineViewSet, DashboardViewSet, BankReconciliationViewSet,
    FundViewSet, ReserveStudyViewSet, ReserveComponentViewSet, ReserveScenarioViewSet,
    CustomReportViewSet, ReportExecutionViewSet,
    LateFeeRuleViewSet, DelinquencyStatusViewSet, CollectionNoticeViewSet, CollectionActionViewSet,
    AutoMatchRuleViewSet, MatchResultViewSet, MatchStatisticsViewSet,
    ViolationViewSet, ViolationPhotoViewSet, ViolationNoticeViewSet, ViolationHearingViewSet,
    BoardPacketTemplateViewSet, BoardPacketViewSet, PacketSectionViewSet,
    # Phase 3 Sprint 15: Violation Tracking (New Models)
    ViolationTypeViewSet, FineScheduleViewSet, ViolationEscalationViewSet, ViolationFineViewSet,
    # Phase 3 Sprint 16: ARC Workflow
    ARCRequestTypeViewSet, ARCRequestViewSet, ARCDocumentViewSet, ARCReviewViewSet,
    ARCApprovalViewSet, ARCCompletionViewSet,
    # Phase 3 Sprint 17: Work Orders
    WorkOrderCategoryViewSet, VendorViewSet, WorkOrderViewSet, WorkOrderCommentViewSet,
    WorkOrderAttachmentViewSet, WorkOrderInvoiceViewSet,
    # Phase 4: Retention Features
    AuditorExportViewSet, ResaleDisclosureViewSet,
    ar_aging_report, owner_ledger, dashboard_metrics, trial_balance
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'owners', OwnerViewSet, basename='owner')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'budget-lines', BudgetLineViewSet, basename='budget-line')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'reconciliation', BankReconciliationViewSet, basename='reconciliation')
router.register(r'funds', FundViewSet, basename='fund')
router.register(r'reserve-studies', ReserveStudyViewSet, basename='reserve-study')
router.register(r'reserve-components', ReserveComponentViewSet, basename='reserve-component')
router.register(r'reserve-scenarios', ReserveScenarioViewSet, basename='reserve-scenario')
router.register(r'custom-reports', CustomReportViewSet, basename='custom-report')
router.register(r'report-executions', ReportExecutionViewSet, basename='report-execution')

# Sprint 17: Delinquency & Collections
router.register(r'late-fee-rules', LateFeeRuleViewSet, basename='late-fee-rule')
router.register(r'delinquency-status', DelinquencyStatusViewSet, basename='delinquency-status')
router.register(r'collection-notices', CollectionNoticeViewSet, basename='collection-notice')
router.register(r'collection-actions', CollectionActionViewSet, basename='collection-action')

# Sprint 18: Auto-Matching Engine
router.register(r'auto-match-rules', AutoMatchRuleViewSet, basename='auto-match-rule')
router.register(r'match-results', MatchResultViewSet, basename='match-result')
router.register(r'match-statistics', MatchStatisticsViewSet, basename='match-statistics')

# Sprint 19: Violation Tracking
router.register(r'violations', ViolationViewSet, basename='violation')
router.register(r'violation-photos', ViolationPhotoViewSet, basename='violation-photo')
router.register(r'violation-notices', ViolationNoticeViewSet, basename='violation-notice')
router.register(r'violation-hearings', ViolationHearingViewSet, basename='violation-hearing')

# Sprint 20: Board Packet Generation
router.register(r'board-packet-templates', BoardPacketTemplateViewSet, basename='board-packet-template')
router.register(r'board-packets', BoardPacketViewSet, basename='board-packet')
router.register(r'packet-sections', PacketSectionViewSet, basename='packet-section')

# Phase 4: Retention Features
# Sprint 21: Auditor Export
router.register(r'auditor-exports', AuditorExportViewSet, basename='auditor-export')

# Sprint 22: Resale Disclosure Packages
router.register(r'resale-disclosures', ResaleDisclosureViewSet, basename='resale-disclosure')

# Phase 3 Sprint 15: Violation Tracking (New Models)
router.register(r'violation-types', ViolationTypeViewSet, basename='violation-type')
router.register(r'fine-schedules', FineScheduleViewSet, basename='fine-schedule')
router.register(r'violation-escalations', ViolationEscalationViewSet, basename='violation-escalation')
router.register(r'violation-fines', ViolationFineViewSet, basename='violation-fine')

# Phase 3 Sprint 16: ARC Workflow
router.register(r'arc-request-types', ARCRequestTypeViewSet, basename='arc-request-type')
router.register(r'arc-requests', ARCRequestViewSet, basename='arc-request')
router.register(r'arc-documents', ARCDocumentViewSet, basename='arc-document')
router.register(r'arc-reviews', ARCReviewViewSet, basename='arc-review')
router.register(r'arc-approvals', ARCApprovalViewSet, basename='arc-approval')
router.register(r'arc-completions', ARCCompletionViewSet, basename='arc-completion')

# Phase 3 Sprint 17: Work Order System
router.register(r'work-order-categories', WorkOrderCategoryViewSet, basename='work-order-category')
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'work-orders', WorkOrderViewSet, basename='work-order')
router.register(r'work-order-comments', WorkOrderCommentViewSet, basename='work-order-comment')
router.register(r'work-order-attachments', WorkOrderAttachmentViewSet, basename='work-order-attachment')
router.register(r'work-order-invoices', WorkOrderInvoiceViewSet, basename='work-order-invoice')

# URL patterns
urlpatterns = [
    # ViewSet routes
    path('api/v1/accounting/', include(router.urls)),

    # Custom report endpoints
    path('api/v1/accounting/reports/ar-aging/', ar_aging_report, name='ar-aging-report'),
    path('api/v1/accounting/reports/trial-balance/', trial_balance, name='trial-balance'),
    path('api/v1/accounting/reports/dashboard/', dashboard_metrics, name='dashboard-metrics'),
    path('api/v1/accounting/owners/<uuid:owner_id>/ledger/', owner_ledger, name='owner-ledger'),
]
