# Late Fee Automation Guide

## Overview

The `assess_late_fees` management command automatically assesses late fees for delinquent accounts based on configured late fee rules.

**Location:** `backend/accounting/management/commands/assess_late_fees.py`

---

## How It Works

### 1. Process Flow

```
For each active tenant:
  ├─ Find all delinquent accounts
  ├─ Check grace period (e.g., 10 days)
  ├─ Get applicable late fee rule
  ├─ Calculate late fee amount
  ├─ Create invoice for late fee
  └─ Update delinquency status
```

### 2. Business Rules

- **Grace Period:** No fees assessed until grace period expires (configurable per rule)
- **Recurring Fees:** If rule is recurring, assesses monthly (30 days between assessments)
- **Non-Recurring Fees:** Assesses only once per delinquency
- **Fee Calculation:** Uses LateFeeRule.calculate_fee() method
  - Flat: Fixed amount
  - Percentage: % of outstanding balance
  - Combined: Flat + percentage with max cap
- **Invoice Creation:** Creates Invoice with TYPE_LATE_FEE and InvoiceLine

### 3. Required Models

The command uses:
- **LateFeeRule** - Rules for calculating late fees
- **DelinquencyStatus** - Tracks delinquent accounts
- **Invoice** - Creates late fee invoices
- **InvoiceLine** - Line items for late fee charges
- **Account** - Revenue account for late fee income (4100)

---

## Command Usage

### Basic Usage

```bash
# Assess late fees for all tenants
python manage.py assess_late_fees

# Dry run (no invoices created)
python manage.py assess_late_fees --dry-run

# Verbose output
python manage.py assess_late_fees --verbose

# Specific tenant only
python manage.py assess_late_fees --tenant-id=<uuid>

# Dry run with verbose output
python manage.py assess_late_fees --dry-run --verbose
```

### Example Output

```
Processing tenant: Sunset Hills HOA (123e4567-e89b-12d3-a456-426614174000)
  Assessed $25.00 late fee for John Smith (Balance: $500.00, Days: 45)
  Assessed $50.00 late fee for Jane Doe (Balance: $1,000.00, Days: 90)
  Skipping Bob Jones: Within grace period (5/10 days)
  Created invoice INV-00123 for $25.00
  Created invoice INV-00124 for $50.00

Successfully assessed late fees for 2 accounts totaling $75.00
```

---

## Scheduling

### Option 1: Cron Job (Linux/Mac)

**Recommended:** Run daily at 1:00 AM

```bash
# Edit crontab
crontab -e

# Add this line:
0 1 * * * cd /var/www/hoaaccounting && /var/www/hoaaccounting/venv/bin/python manage.py assess_late_fees >> /var/log/late_fees.log 2>&1
```

**Explanation:**
- `0 1 * * *` - Run at 1:00 AM every day
- `cd /var/www/hoaaccounting` - Navigate to project directory
- `/var/www/hoaaccounting/venv/bin/python` - Use virtualenv Python
- `>> /var/log/late_fees.log` - Append output to log file
- `2>&1` - Redirect errors to log file

**With email notifications:**

```bash
0 1 * * * cd /var/www/hoaaccounting && /var/www/hoaaccounting/venv/bin/python manage.py assess_late_fees 2>&1 | mail -s "Late Fee Assessment Report" admin@hoa.com
```

### Option 2: Celery Beat (Recommended for Production)

**Step 1: Install Celery**

```bash
pip install celery redis
```

**Step 2: Configure Celery (backend/hoaaccounting/celery.py)**

```python
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoaaccounting.settings')

app = Celery('hoaaccounting')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    'assess-late-fees-daily': {
        'task': 'accounting.tasks.assess_late_fees_task',
        'schedule': crontab(hour=1, minute=0),  # 1:00 AM daily
    },
}
```

**Step 3: Create Celery Task (backend/accounting/tasks.py)**

```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def assess_late_fees_task():
    """Celery task to assess late fees"""
    call_command('assess_late_fees', verbosity=1)
```

**Step 4: Run Celery Worker and Beat**

```bash
# Terminal 1: Worker
celery -A hoaaccounting worker -l info

# Terminal 2: Beat scheduler
celery -A hoaaccounting beat -l info
```

**Production (Docker):**

```yaml
# docker-compose.production.yml
celery-worker:
  build: ./backend
  command: celery -A hoaaccounting worker -l info
  depends_on:
    - redis
    - postgres

celery-beat:
  build: ./backend
  command: celery -A hoaaccounting beat -l info
  depends_on:
    - redis
```

### Option 3: Windows Task Scheduler

**Step 1: Create batch file (assess_late_fees.bat)**

```batch
@echo off
cd C:\var\www\hoaaccounting
C:\var\www\hoaaccounting\venv\Scripts\python.exe manage.py assess_late_fees >> C:\logs\late_fees.log 2>&1
```

**Step 2: Schedule in Task Scheduler**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Assess Late Fees"
4. Trigger: Daily at 1:00 AM
5. Action: Start a Program
6. Program: `C:\var\www\hoaaccounting\assess_late_fees.bat`
7. Finish

---

## Monitoring and Logging

### 1. Log Output

Add logging to settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/late_fees.log',
        },
    },
    'loggers': {
        'accounting.management.commands.assess_late_fees': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### 2. Email Notifications

Send email report after assessment:

```python
# In assess_late_fees.py
from django.core.mail import send_mail

# After processing all tenants
if not dry_run:
    send_mail(
        subject=f'Late Fee Assessment Complete - {total_accounts_processed} accounts',
        message=f'Assessed ${total_fees_assessed:.2f} in late fees',
        from_email='noreply@hoa.com',
        recipient_list=['admin@hoa.com'],
    )
```

### 3. Database Tracking

Track assessment history:

```python
# Optional: Create AssessmentLog model
class LateFeeAssessmentLog(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    run_date = models.DateTimeField(auto_now_add=True)
    accounts_processed = models.IntegerField()
    total_fees_assessed = models.DecimalField(max_digits=15, decimal_places=2)
    invoices_created = models.IntegerField()
```

---

## Testing

### 1. Dry Run First

Always test with --dry-run before running in production:

```bash
python manage.py assess_late_fees --dry-run --verbose
```

### 2. Test with Single Tenant

```bash
python manage.py assess_late_fees --tenant-id=<uuid> --verbose
```

### 3. Verify Results

After running:
- Check invoices created (Invoice.objects.filter(invoice_type='LATE_FEE'))
- Check delinquency status updated (last_late_fee_date)
- Verify amounts calculated correctly

---

## Troubleshooting

### No Late Fees Assessed

**Check:**
1. Are there active LateFeeRule records?
   ```python
   LateFeeRule.objects.filter(is_active=True)
   ```
2. Are accounts past grace period?
   ```python
   DelinquencyStatus.objects.filter(is_delinquent=True, days_delinquent__gte=10)
   ```
3. Has a fee already been assessed recently?
   ```python
   DelinquencyStatus.objects.filter(last_late_fee_date__isnull=False)
   ```

### Errors During Invoice Creation

**Check:**
1. Do owners have units assigned?
2. Does late fee income account exist?
3. Are invoice numbers being generated correctly?

### Run Command Manually

```bash
python manage.py assess_late_fees --verbose
```

---

## Best Practices

### 1. Configuration

- Set appropriate grace periods (10-15 days typical)
- Test fee calculations before activating rules
- Consider max fee caps to prevent excessive charges

### 2. Scheduling

- Run during off-peak hours (1-3 AM)
- Send email notifications to admins
- Log all assessments for audit trail

### 3. Monitoring

- Review logs daily
- Monitor invoice creation
- Track false positives (fees assessed incorrectly)

### 4. Communication

- Notify owners before first late fee
- Include late fee policy in HOA bylaws
- Provide grace period before assessment

---

## Production Checklist

Before deploying to production:

- [ ] LateFeeRule configured for each tenant
- [ ] Grace periods set appropriately
- [ ] Cron job or Celery scheduled
- [ ] Logging configured and tested
- [ ] Email notifications working
- [ ] Dry run tested successfully
- [ ] Database backups automated
- [ ] Late fee policy documented
- [ ] Owner communication sent
- [ ] Monitoring dashboard created

---

## Support

For issues or questions:
- Check logs: `/var/log/django/late_fees.log`
- Run with --verbose for debugging
- Test with --dry-run first
- Contact: admin@hoa.com

---

**Last Updated:** 2025-10-29
**Version:** 1.0
**Command:** `accounting/management/commands/assess_late_fees.py`
