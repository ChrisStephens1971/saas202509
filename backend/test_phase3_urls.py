#!/usr/bin/env python
"""
Phase 3 URL Configuration Testing Script

Tests that all 16 Phase 3 API endpoints are properly registered
in the URL configuration without requiring database access.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoaaccounting.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver


def get_all_urls(urlpatterns, prefix=''):
    """Recursively get all URL patterns."""
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # Recursively get patterns from included URLConf
            urls.extend(get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
        elif isinstance(pattern, URLPattern):
            urls.append(prefix + str(pattern.pattern))
    return urls


def test_phase3_url_configuration():
    """Test that all Phase 3 endpoints are registered."""

    print("=" * 80)
    print("PHASE 3 URL CONFIGURATION TESTING")
    print("=" * 80)
    print()

    # Expected Phase 3 endpoints
    expected_endpoints = {
        'Sprint 15 - Violation Tracking (4 endpoints)': [
            'violation-types',
            'fine-schedules',
            'violation-escalations',
            'violation-fines',
        ],
        'Sprint 16 - ARC Workflow (6 endpoints)': [
            'arc-request-types',
            'arc-requests',
            'arc-documents',
            'arc-reviews',
            'arc-approvals',
            'arc-completions',
        ],
        'Sprint 17 - Work Order System (6 endpoints)': [
            'work-order-categories',
            'vendors',
            'work-orders',
            'work-order-comments',
            'work-order-attachments',
            'work-order-invoices',
        ],
    }

    # Get all registered URLs
    resolver = get_resolver()
    all_urls = get_all_urls(resolver.url_patterns)

    # Filter for accounting API URLs
    accounting_urls = [url for url in all_urls if 'accounting' in url]

    total_expected = 0
    found_count = 0
    missing_count = 0
    missing_endpoints = []

    for sprint_name, endpoints in expected_endpoints.items():
        print(f"\n{'=' * 80}")
        print(f"{sprint_name}")
        print(f"{'=' * 80}")

        for endpoint in endpoints:
            total_expected += 1

            # Check if endpoint exists in any URL
            found = any(endpoint in url for url in accounting_urls)

            if found:
                status = "[OK] FOUND"
                found_count += 1
            else:
                status = "[!!] MISSING"
                missing_count += 1
                missing_endpoints.append(endpoint)

            print(f"  {status} {endpoint}")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Expected Endpoints: {total_expected}")
    print(f"Found: {found_count} [OK]")
    print(f"Missing: {missing_count} [!!]")
    print(f"Registration Rate: {(found_count/total_expected*100):.1f}%")
    print()

    if missing_count > 0:
        print("Missing Endpoints:")
        for endpoint in missing_endpoints:
            print(f"  - {endpoint}")
        print()

    if missing_count == 0:
        print("SUCCESS: ALL PHASE 3 API ENDPOINTS ARE PROPERLY REGISTERED!")
        print()
        print("Endpoints are accessible at:")
        print("  http://localhost:8009/api/v1/accounting/<endpoint-name>/")
        print()
        print("Example:")
        print("  http://localhost:8009/api/v1/accounting/violation-types/")
        print("  http://localhost:8009/api/v1/accounting/arc-requests/")
        print("  http://localhost:8009/api/v1/accounting/work-orders/")
    else:
        print("WARNING: Some endpoints are missing from URL configuration.")

    print("=" * 80)

    return missing_count == 0


if __name__ == '__main__':
    success = test_phase3_url_configuration()
    sys.exit(0 if success else 1)
