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
