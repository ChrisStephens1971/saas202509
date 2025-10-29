# Staging Deployment Guide

## Overview

This guide walks through deploying the HOA Accounting System to a staging environment using Docker.

**Purpose:** Validate MVP in production-like environment before production launch
**Docker Config:** Complete multi-container setup with PostgreSQL, Redis, backend, frontend
**Estimated Time:** 30-45 minutes

---

## Prerequisites

### Required Software
- Docker 20.10+ and Docker Compose 2.0+
- Git
- 2GB+ RAM available
- 10GB+ disk space

### Verify Installation
```bash
docker --version          # Should show 20.10+
docker-compose --version  # Should show 2.0+
git --version
```

---

## Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/ChrisStephens1971/saas202509.git
cd saas202509

# 2. Create environment file
cp .env.production.example .env.production
# Edit .env.production with your values (see Configuration section)

# 3. Build and start services
docker-compose -f docker-compose.production.yml up -d --build

# 4. Run migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# 5. Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

# 6. Verify
open http://localhost        # Frontend
open http://localhost/api/v1/ # Backend API
open http://localhost/admin/  # Admin panel
```

---

## Detailed Deployment Steps

### Step 1: Prepare Environment

**Create `.env.production` from template:**
```bash
cp .env.production.example .env.production
```

**Edit `.env.production` with your values:**

```bash
# Django Settings
SECRET_KEY=your-very-secret-key-here-generate-with-django
DEBUG=False
ALLOWED_HOSTS=staging.yourhoa.com,localhost,127.0.0.1

# Database
POSTGRES_DB=hoaaccounting
POSTGRES_USER=hoauser
POSTGRES_PASSWORD=strong-password-here
DATABASE_URL=postgresql://hoauser:strong-password-here@postgres:5432/hoaaccounting

# Redis
REDIS_URL=redis://redis:6379/0

# Email (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourhoa.com

# AWS S3 (optional for staging, required for production)
USE_S3=False
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
# AWS_STORAGE_BUCKET_NAME=hoa-staging

# Security
CORS_ALLOWED_ORIGINS=http://localhost,https://staging.yourhoa.com
```

**Generate SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 2: Build Docker Images

```bash
# Build all services
docker-compose -f docker-compose.production.yml build

# Verify images created
docker images | grep saas202509
```

**Expected output:**
```
saas202509-backend    latest    ...
saas202509-frontend   latest    ...
postgres              16        ...
redis                 7         ...
```

### Step 3: Start Services

```bash
# Start all services in background
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check service status
docker-compose -f docker-compose.production.yml ps
```

**Expected services:**
```
NAME                STATE    PORTS
postgres            Up       0.0.0.0:5409->5432/tcp
redis               Up       0.0.0.0:6379->6379/tcp
backend             Up       0.0.0.0:8009->8000/tcp
frontend            Up       0.0.0.0:80->80/tcp
```

### Step 4: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
# Follow prompts: username, email, password

# Load initial data (optional)
docker-compose -f docker-compose.production.yml exec backend python manage.py loaddata fixtures/initial_data.json
```

### Step 5: Collect Static Files

```bash
# Collect static files for Django admin
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
```

### Step 6: Verify Deployment

**Frontend:** http://localhost
- Should see HOA Accounting System login page
- No console errors

**Backend API:** http://localhost/api/v1/
- Should see DRF browsable API
- Shows list of endpoints

**Admin Panel:** http://localhost/admin/
- Login with superuser credentials
- Should see Django admin dashboard

**Health Checks:**
```bash
# Backend health
curl http://localhost/api/v1/health/

# Frontend health
curl http://localhost/

# Database connectivity
docker-compose -f docker-compose.production.yml exec backend python manage.py check --database default
```

---

## Post-Deployment Configuration

### 1. Create Tenant (HOA)

```bash
docker-compose -f docker-compose.production.yml exec backend python manage.py shell
```

```python
from tenants.models import Tenant

tenant = Tenant.objects.create(
    name="Test HOA",
    slug="test-hoa",
    is_active=True
)
print(f"Created tenant: {tenant.name} ({tenant.id})")
```

### 2. Create Test Data

```bash
# Run test data script
docker-compose -f docker-compose.production.yml exec backend python manage.py shell < scripts/create_test_data.py
```

### 3. Configure Email (Optional)

Test email sending:
```bash
docker-compose -f docker-compose.production.yml exec backend python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email from HOA System',
    'This is a test email.',
    'noreply@yourhoa.com',
    ['admin@yourhoa.com'],
)
```

---

## Smoke Tests

### Manual Smoke Tests

Run through these critical paths:

**1. Authentication**
- [ ] Login with superuser
- [ ] Logout
- [ ] Login with regular user
- [ ] Token refresh works

**2. Invoicing**
- [ ] Create invoice for owner
- [ ] View invoice list
- [ ] View invoice detail
- [ ] Record payment
- [ ] Verify ledger updated

**3. Bank Reconciliation**
- [ ] Import bank statement (CSV)
- [ ] View unmatched transactions
- [ ] Auto-match suggestions work
- [ ] Manually match transaction
- [ ] View reconciliation report

**4. Budgeting**
- [ ] Create budget for year
- [ ] Add budget lines
- [ ] View budget vs actual
- [ ] Export budget report

**5. Delinquency**
- [ ] View delinquency dashboard
- [ ] Configure late fee rule
- [ ] Manually assess late fee
- [ ] View collection notices

**6. Violations**
- [ ] Report new violation
- [ ] Upload photo evidence
- [ ] View violations list
- [ ] Filter by severity/status

**7. Board Packets**
- [ ] Create packet template
- [ ] Generate board packet
- [ ] Generate PDF
- [ ] Email to recipients (test mode)

### Automated Smoke Tests

Create `smoke_tests.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost/api/v1"
TOKEN=""

echo "Running Smoke Tests..."

# 1. Health Check
echo "1. Health Check..."
curl -f $BASE_URL/health/ || exit 1

# 2. Authentication
echo "2. Testing Authentication..."
RESPONSE=$(curl -s -X POST $BASE_URL/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo $RESPONSE | jq -r '.access')
if [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  exit 1
fi
echo "✅ Authentication successful"

# 3. Test Endpoints
echo "3. Testing API Endpoints..."

# Owners endpoint
curl -f -H "Authorization: Bearer $TOKEN" $BASE_URL/owners/ || exit 1
echo "✅ Owners endpoint working"

# Invoices endpoint
curl -f -H "Authorization: Bearer $TOKEN" $BASE_URL/invoices/ || exit 1
echo "✅ Invoices endpoint working"

# Payments endpoint
curl -f -H "Authorization: Bearer $TOKEN" $BASE_URL/payments/ || exit 1
echo "✅ Payments endpoint working"

echo ""
echo "🎉 All smoke tests passed!"
```

**Run automated tests:**
```bash
chmod +x smoke_tests.sh
./smoke_tests.sh
```

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml logs frontend
docker-compose -f docker-compose.production.yml logs postgres
```

**Common issues:**
- Port already in use → Change ports in docker-compose.yml
- Database connection failed → Check DATABASE_URL in .env.production
- Permission denied → Run with sudo (Linux) or check Docker Desktop settings

### Database Errors

**Reset database:**
```bash
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
```

### Frontend 404 Errors

**Rebuild frontend:**
```bash
docker-compose -f docker-compose.production.yml build frontend
docker-compose -f docker-compose.production.yml up -d frontend
```

### Static Files Missing

**Collect static files:**
```bash
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
```

---

## Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 backend
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Image sizes
docker images
```

### Database Backups

```bash
# Backup database
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U hoauser hoaaccounting > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20251029.sql | docker-compose -f docker-compose.production.yml exec -T postgres psql -U hoauser hoaaccounting
```

---

## Cleanup

### Stop Services

```bash
# Stop containers
docker-compose -f docker-compose.production.yml stop

# Stop and remove containers
docker-compose -f docker-compose.production.yml down

# Remove containers and volumes (⚠️ deletes all data)
docker-compose -f docker-compose.production.yml down -v
```

### Rebuild Everything

```bash
# Clean rebuild
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

---

## Staging Checklist

Before marking staging deployment as complete:

- [ ] All Docker services running
- [ ] Database migrations applied
- [ ] Superuser account created
- [ ] Test tenant created
- [ ] Test data loaded
- [ ] Frontend accessible and loads correctly
- [ ] Backend API accessible
- [ ] Admin panel accessible
- [ ] Email sending configured and tested
- [ ] All manual smoke tests passed
- [ ] Automated smoke tests passed
- [ ] No errors in logs
- [ ] Resource usage acceptable (<2GB RAM)
- [ ] Database backups configured
- [ ] Monitoring in place
- [ ] Documentation reviewed

---

## Next Steps

After staging validation:
1. Run full test suite (saas202510)
2. Performance testing with load
3. Security audit
4. User documentation
5. Production deployment planning

---

## Support

**Logs Location:** Run `docker-compose logs` to view
**Issue Reporting:** GitHub Issues at https://github.com/ChrisStephens1971/saas202509/issues
**Emergency Stop:** `docker-compose -f docker-compose.production.yml down`

---

**Last Updated:** 2025-10-29
**Version:** 1.0
**Docker Compose:** docker-compose.production.yml
