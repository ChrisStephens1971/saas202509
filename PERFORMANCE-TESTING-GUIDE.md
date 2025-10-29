# Performance Testing & Optimization Guide

## Overview

This guide covers performance testing, benchmarking, and optimization for the HOA Accounting System.

**Goals:**
- Dashboard load time < 2 seconds
- Report generation < 5 seconds
- Bank reconciliation (500 transactions) < 10 seconds
- Support 100 concurrent users

---

## Performance Testing Tools

### 1. Locust (Load Testing)

**Install:**
```bash
pip install locust==2.31.8
```

**Create `locustfile.py`:**
```python
from locust import HttpUser, task, between
import random

class HOAUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    token = None

    def on_start(self):
        """Login and get JWT token"""
        response = self.client.post("/api/v1/token/", json={
            "username": "testuser",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json()["access"]
            self.client.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)  # Weight 5 - most common action
    def view_dashboard(self):
        """View dashboard"""
        self.client.get("/api/v1/dashboard/metrics/")

    @task(3)
    def list_invoices(self):
        """List invoices"""
        self.client.get("/api/v1/invoices/")

    @task(3)
    def list_owners(self):
        """List owners"""
        self.client.get("/api/v1/owners/")

    @task(2)
    def view_budget(self):
        """View budget"""
        self.client.get("/api/v1/budgets/")

    @task(1)
    def generate_report(self):
        """Generate AR aging report"""
        self.client.get("/api/v1/owners/ar-aging/")

    @task(1)
    def view_delinquency(self):
        """View delinquency dashboard"""
        self.client.get("/api/v1/delinquency-status/summary/")
```

**Run load test:**
```bash
# Start Locust web interface
locust -f locustfile.py --host=http://localhost:8009

# Open browser to http://localhost:8089
# Set users: 100, spawn rate: 10

# Or run headless
locust -f locustfile.py --host=http://localhost:8009 --users 100 --spawn-rate 10 --run-time 5m --headless
```

### 2. Django Debug Toolbar

**Install:**
```bash
pip install django-debug-toolbar==4.4.6
```

**Configure (`settings.py`):**
```python
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ...
]

INTERNAL_IPS = ['127.0.0.1']
```

**Add to URLs:**
```python
from django.urls import path, include

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

**Usage:**
- Toolbar appears on all pages
- Shows SQL queries, cache hits, template rendering time
- Identifies N+1 query problems

### 3. Apache Bench (Quick Tests)

**Install:** Usually pre-installed on Linux/Mac

**Test endpoint:**
```bash
# 1000 requests, 10 concurrent
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8009/api/v1/invoices/

# With JSON payload
ab -n 1000 -c 10 -T "application/json" -p post_data.json http://localhost:8009/api/v1/invoices/
```

---

## Performance Metrics

### Key Metrics to Track

1. **Response Time**
   - P50 (median): < 200ms
   - P95: < 500ms
   - P99: < 1000ms

2. **Throughput**
   - Requests per second: > 100 RPS
   - Concurrent users: 100+

3. **Database**
   - Query time: < 50ms per query
   - Connection pool usage: < 80%
   - Slow queries: 0

4. **Memory**
   - Backend: < 512MB per worker
   - Frontend: < 100MB static files
   - Redis: < 256MB

5. **CPU**
   - Average usage: < 50%
   - Peak usage: < 80%

---

## Optimization Strategies

### 1. Database Optimization

**Add Indexes:**
```python
# models.py
class Invoice(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'owner']),
            models.Index(fields=['tenant', 'due_date']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['invoice_date', 'status']),
        ]
```

**Use select_related and prefetch_related:**
```python
# Before (N+1 queries)
invoices = Invoice.objects.filter(tenant=tenant)
for invoice in invoices:
    print(invoice.owner.full_name)  # Hits DB each time!

# After (2 queries)
invoices = Invoice.objects.filter(tenant=tenant).select_related('owner')
for invoice in invoices:
    print(invoice.owner.full_name)  # No extra query!
```

**Optimize complex queries:**
```python
# Before
owners_with_balance = []
for owner in Owner.objects.all():
    balance = owner.calculate_balance()  # Expensive!
    if balance > 0:
        owners_with_balance.append(owner)

# After (single query)
from django.db.models import Sum

owners_with_balance = Owner.objects.annotate(
    total_owed=Sum('invoices__amount_due')
).filter(total_owed__gt=0)
```

**Database Connection Pooling:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### 2. Caching with Redis

**Install:**
```bash
pip install django-redis==5.4.0
```

**Configure:**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

**Cache expensive queries:**
```python
from django.core.cache import cache

def get_dashboard_metrics(tenant):
    cache_key = f'dashboard_metrics_{tenant.id}'
    metrics = cache.get(cache_key)

    if metrics is None:
        # Expensive calculation
        metrics = calculate_metrics(tenant)
        cache.set(cache_key, metrics, 300)  # Cache for 5 minutes

    return metrics
```

**Cache API responses:**
```python
from django.views.decorators.cache import cache_page

class DashboardViewSet(viewsets.ViewSet):
    @action(detail=False)
    @cache_page(60 * 5)  # Cache for 5 minutes
    def metrics(self, request):
        # ...
        return Response(metrics)
```

### 3. Pagination

**Always paginate lists:**
```python
# api_views.py
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

class InvoiceViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
```

### 4. Frontend Optimization

**Code splitting:**
```typescript
// App.tsx
import { lazy, Suspense } from 'react'

const InvoicesPage = lazy(() => import('./pages/InvoicesPage'))
const PaymentsPage = lazy(() => import('./pages/PaymentsPage'))

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/payments" element={<PaymentsPage />} />
      </Routes>
    </Suspense>
  )
}
```

**Image optimization:**
```typescript
// Lazy load images
<img loading="lazy" src={photo.url} alt={photo.caption} />

// Use proper image formats
// Convert to WebP with Pillow on backend
```

**Bundle optimization:**
```bash
# Analyze bundle size
npm run build
npx vite-bundle-visualizer

# Optimize
- Remove unused dependencies
- Use tree-shaking
- Compress images
```

### 5. API Response Optimization

**Only return needed fields:**
```python
class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'owner', 'total_amount', 'due_date']
        # Don't include heavy fields like journal_entry unless needed
```

**Use bulk operations:**
```python
# Before (N queries)
for owner in owners:
    Invoice.objects.create(owner=owner, ...)

# After (1 query)
Invoice.objects.bulk_create([
    Invoice(owner=owner, ...) for owner in owners
])
```

---

## Performance Testing Checklist

### Pre-Test Setup
- [ ] Load test data (1,000 owners, 10,000 invoices, 50,000 transactions)
- [ ] Configure production-like environment
- [ ] Enable query logging
- [ ] Set up monitoring (CPU, memory, disk I/O)

### Tests to Run
- [ ] Single user baseline (response times)
- [ ] Ramp-up test (1 → 100 users over 5 minutes)
- [ ] Sustained load (100 users for 30 minutes)
- [ ] Spike test (sudden jump to 200 users)
- [ ] Stress test (find breaking point)

### Scenarios
- [ ] Dashboard load
- [ ] Invoice list pagination
- [ ] Payment processing
- [ ] Bank reconciliation (500 transactions)
- [ ] Report generation (AR aging, delinquency)
- [ ] Budget vs actual comparison
- [ ] PDF generation for board packet
- [ ] File upload (violation photos)

### Analysis
- [ ] Identify slow endpoints (> 1 second)
- [ ] Find N+1 query problems
- [ ] Check cache hit rates
- [ ] Review database query plans
- [ ] Monitor memory usage patterns
- [ ] Check for memory leaks
- [ ] Review error rates

---

## Optimization Priority

### Critical (Do First)
1. Add database indexes
2. Use select_related/prefetch_related
3. Implement pagination
4. Cache expensive queries
5. Fix N+1 queries

### Important (Do Second)
1. Redis caching for dashboard
2. Code splitting (frontend)
3. Image optimization
4. API response field filtering
5. Database connection pooling

### Nice to Have (Do Later)
1. CDN for static files
2. HTTP/2 and compression
3. Database read replicas
4. Async task processing (Celery)
5. Query result caching

---

## Monitoring in Production

### Tools

**Backend Monitoring:**
- New Relic or DataDog (APM)
- Sentry (error tracking)
- Prometheus + Grafana (metrics)

**Database:**
- pg_stat_statements (slow queries)
- pgBadger (log analysis)

**Frontend:**
- Google Analytics (page load times)
- Lighthouse CI (performance scores)

### Alerts
- Response time > 1 second (warning)
- Response time > 3 seconds (critical)
- Error rate > 1% (critical)
- CPU usage > 80% (warning)
- Memory usage > 90% (critical)
- Disk space < 10% (critical)

---

## Performance Budget

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Dashboard load | < 1s | < 2s | > 3s |
| Invoice list | < 500ms | < 1s | > 2s |
| Report generation | < 3s | < 5s | > 10s |
| Bank reconciliation | < 5s | < 10s | > 20s |
| PDF generation | < 3s | < 5s | > 10s |
| API endpoint (avg) | < 200ms | < 500ms | > 1s |

---

## Troubleshooting Slow Performance

### Slow Database Queries

```sql
-- Find slow queries (PostgreSQL)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM invoices WHERE tenant_id = '...';
```

### High Memory Usage

```bash
# Check Django memory usage
docker stats

# Profile memory
pip install memory_profiler
python -m memory_profiler manage.py runserver
```

### N+1 Queries

```python
# Use Django Debug Toolbar
# Or enable query logging
import logging
logger = logging.getLogger('django.db.backends')
logger.setLevel(logging.DEBUG)
```

---

## References

- [Locust Documentation](https://docs.locust.io/)
- [Django Performance Tips](https://docs.djangoproject.com/en/5.1/topics/performance/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [React Performance](https://react.dev/learn/render-and-commit#optimizing-performance)

---

**Last Updated:** 2025-10-29
**Version:** 1.0
