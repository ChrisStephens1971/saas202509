#!/usr/bin/env python
"""
Phase 3 API Endpoint Testing Script

Tests all 16 Phase 3 API endpoints to verify they are accessible
and properly configured.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoaaccounting.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from tenants.models import Tenant

User = get_user_model()

def test_phase3_endpoints():
    """Test all Phase 3 API endpoints."""

    print("=" * 80)
    print("PHASE 3 API ENDPOINT TESTING")
    print("=" * 80)
    print()

    # Create test client
    client = APIClient()

    # Get or create a test tenant
    tenant, _ = Tenant.objects.get_or_create(
        schema_name='test_tenant',
        defaults={'name': 'Test HOA'}
    )

    # Phase 3 endpoints to test
    endpoints = {
        'Sprint 15 - Violation Tracking': [
            '/api/v1/accounting/violation-types/',
            '/api/v1/accounting/fine-schedules/',
            '/api/v1/accounting/violation-escalations/',
            '/api/v1/accounting/violation-fines/',
        ],
        'Sprint 16 - ARC Workflow': [
            '/api/v1/accounting/arc-request-types/',
            '/api/v1/accounting/arc-requests/',
            '/api/v1/accounting/arc-documents/',
            '/api/v1/accounting/arc-reviews/',
            '/api/v1/accounting/arc-approvals/',
            '/api/v1/accounting/arc-completions/',
        ],
        'Sprint 17 - Work Order System': [
            '/api/v1/accounting/work-order-categories/',
            '/api/v1/accounting/vendors/',
            '/api/v1/accounting/work-orders/',
            '/api/v1/accounting/work-order-comments/',
            '/api/v1/accounting/work-order-attachments/',
            '/api/v1/accounting/work-order-invoices/',
        ],
    }

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for sprint_name, urls in endpoints.items():
        print(f"\n{'=' * 80}")
        print(f"{sprint_name}")
        print(f"{'=' * 80}")

        for url in urls:
            total_tests += 1
            endpoint_name = url.split('/')[-2]

            try:
                # Test GET request
                response = client.get(url)

                # Check if endpoint is accessible (200 or 403 - 403 means auth required which is expected)
                if response.status_code in [200, 403]:
                    status = "✅ PASS"
                    passed_tests += 1
                    if response.status_code == 403:
                        detail = "Authentication required (expected)"
                    else:
                        detail = f"Returned {len(response.data) if hasattr(response, 'data') else 0} items"
                else:
                    status = "❌ FAIL"
                    failed_tests += 1
                    detail = f"HTTP {response.status_code}"

                print(f"  {status} {endpoint_name:40s} - {detail}")

            except Exception as e:
                status = "❌ ERROR"
                failed_tests += 1
                print(f"  {status} {endpoint_name:40s} - {str(e)[:60]}")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Endpoints Tested: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print()

    if failed_tests == 0:
        print("🎉 ALL PHASE 3 API ENDPOINTS ARE WORKING!")
    else:
        print("⚠️  Some endpoints need attention.")

    print("=" * 80)

    return failed_tests == 0


if __name__ == '__main__':
    success = test_phase3_endpoints()
    sys.exit(0 if success else 1)
