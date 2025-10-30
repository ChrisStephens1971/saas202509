# Cron Job Configuration for Phase 3 Automation

This document describes the scheduled tasks required for Phase 3 production features.

---

## Overview

Phase 3 includes automated tasks that must run on a schedule:

1. **Violation Auto-Escalation** - Daily check for overdue violations
2. **Budget Variance Alerts** - Weekly budget monitoring
3. **Monthly Invoice Generation** - Monthly assessment invoicing (Phase 1)
4. **Late Fee Assessment** - Monthly late fee processing (Phase 1)
5. **Payment Reminders** - Weekly overdue payment reminders (Phase 1)

---

## Cron Job Schedule

### Production Crontab

```bash
# Phase 1 - Monthly Invoicing
# Generate monthly invoices on the 1st of each month at 2:00 AM
0 2 1 * * cd /app && python manage.py generate_monthly_invoices >> /var/log/cron/invoices.log 2>&1

# Phase 1 - Late Fee Assessment
# Assess late fees on the 6th of each month at 3:00 AM (5 days grace period)
0 3 6 * * cd /app && python manage.py assess_late_fees >> /var/log/cron/late_fees.log 2>&1

# Phase 1 - Payment Reminders
# Send overdue payment reminders every Monday at 8:00 AM
0 8 * * 1 cd /app && python manage.py send_overdue_reminders >> /var/log/cron/reminders.log 2>&1

# Phase 3 - Violation Auto-Escalation
# Check for overdue violations daily at 6:00 AM
0 6 * * * cd /app && python manage.py escalate_overdue_violations >> /var/log/cron/violations.log 2>&1

# Phase 3 - Budget Variance Monitoring
# Check budget variances every Monday at 9:00 AM
0 9 * * 1 cd /app && python manage.py check_budget_variances >> /var/log/cron/budgets.log 2>&1
```

### Development Crontab (Windows Task Scheduler)

For Windows development, use Task Scheduler instead of cron:

**Violation Auto-Escalation:**
- Trigger: Daily at 6:00 AM
- Action: `C:\devop\saas202509\backend\venv\Scripts\python.exe manage.py escalate_overdue_violations`
- Start in: `C:\devop\saas202509\backend`

**Budget Variance Monitoring:**
- Trigger: Weekly (Monday) at 9:00 AM
- Action: `C:\devop\saas202509\backend\venv\Scripts\python.exe manage.py check_budget_variances`
- Start in: `C:\devop\saas202509\backend`

---

## Management Commands

### 1. Escalate Overdue Violations

**Command:**
```bash
python manage.py escalate_overdue_violations [options]
```

**Options:**
- `--dry-run` - Show what would be escalated without actually escalating
- `--days-grace N` - Number of grace days after cure deadline (default: 0)

**Examples:**
```bash
# Test mode (see what would happen)
python manage.py escalate_overdue_violations --dry-run

# Live mode with 2-day grace period
python manage.py escalate_overdue_violations --days-grace 2
```

**Process:**
1. Finds violations with status 'open' or 'escalated'
2. Checks if cure_deadline has passed
3. Creates escalation record with fine amount
4. Updates violation status to 'escalated'
5. Sends email notification to owner

**Output:**
```
======================================================================
VIOLATION AUTO-ESCALATION TASK
======================================================================
Run Date: 2025-10-29 06:00:00
Mode: LIVE
Grace Days: 0

Found 3 overdue violation(s)

  → VIOL-2025-001 - Unit 101 - Step 2 - Fine: $100.00 - Overdue by 7 days
    ✓ Escalated and notification sent
  → VIOL-2025-002 - Unit 205 - Step 1 - Fine: $50.00 - Overdue by 3 days
    ✓ Escalated and notification sent
  → VIOL-2025-003 - Unit 312 - Step 3 - Fine: $150.00 - Overdue by 14 days
    ✓ Escalated and notification sent

======================================================================
SUMMARY
======================================================================
Total Overdue: 3
Escalated: 3
```

---

### 2. Check Budget Variances

**Command:**
```bash
python manage.py check_budget_variances [options]
```

**Options:**
- `--budget-id ID` - Check only a specific budget
- `--warning-threshold N` - Warning threshold percentage (default: 20%)
- `--critical-threshold N` - Critical threshold percentage (default: 30%)
- `--dry-run` - Show what would be alerted without sending notifications

**Examples:**
```bash
# Test mode (see what would be alerted)
python manage.py check_budget_variances --dry-run

# Live mode with custom thresholds
python manage.py check_budget_variances --warning-threshold 15 --critical-threshold 25

# Check specific budget only
python manage.py check_budget_variances --budget-id abc123
```

**Process:**
1. Finds all active budgets
2. Calculates actual spend for each line item
3. Compares against budgeted amount
4. Identifies items exceeding warning/critical thresholds
5. Sends email alert to treasurer

**Output:**
```
======================================================================
BUDGET VARIANCE MONITORING
======================================================================
Run Date: 2025-10-29 09:00:00
Mode: LIVE
Warning Threshold: 20.0%
Critical Threshold: 30.0%

Checking 1 active budget(s)

Budget: 2025 Operating Budget
Period: 2025 (2025-01-01 to 2025-12-31)

  ⚠ Landscaping - Budgeted: $12,000.00 - Actual: $14,500.00 - Variance: $2,500.00 (+20.8%) - WARNING
  ⚠ Repairs & Maintenance - Budgeted: $8,000.00 - Actual: $11,200.00 - Variance: $3,200.00 (+40.0%) - CRITICAL

  ✓ Alert notification sent (2 items)

======================================================================
SUMMARY
======================================================================
Budgets Checked: 1
Total Alerts: 2
```

---

## Email Notifications

### Violation Escalation Email

**To:** Owner email address
**Subject:** Violation Escalated - [Violation Type]
**Content:**
- Violation details
- Escalation step number
- Fine amount (if applicable)
- Action required

**Example:**
```
Violation Escalation Notice

Dear John Smith,

The violation at Unit 101 has been escalated.

Violation Details:
- Type: Unapproved Exterior Modification
- Description: Unauthorized fence installation
- Escalation Step: 2
- Escalation Date: October 29, 2025

Fine Amount: $100.00

Action Required: Please address this violation immediately to avoid further fines.

Thank you,
Sunset Ridge HOA Management
```

### Budget Variance Alert Email

**To:** Treasurer/Board email addresses
**Subject:** Budget Alert - [Budget Name]
**Content:**
- List of budget lines exceeding thresholds
- Budgeted vs actual amounts
- Variance percentages
- Severity levels

**Example:**
```
Budget Variance Alert

The following budget lines have exceeded variance thresholds:

Account              Budgeted      Actual        Variance     Variance %  Severity
Landscaping          $12,000.00    $14,500.00    $2,500.00    +20.8%      WARNING
Repairs & Maintenance $8,000.00    $11,200.00    $3,200.00    +40.0%      CRITICAL

Please review spending in these categories.

Thank you,
Sunset Ridge HOA System
```

---

## Logging

All scheduled tasks log to `/var/log/cron/` in production:

- `violations.log` - Violation escalation output
- `budgets.log` - Budget variance monitoring output
- `invoices.log` - Monthly invoice generation
- `late_fees.log` - Late fee assessment
- `reminders.log` - Payment reminders

**Log Rotation:**
Configure logrotate to prevent log files from growing too large:

```bash
# /etc/logrotate.d/hoa-cron
/var/log/cron/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

---

## Monitoring

### Health Checks

Create a monitoring script to verify scheduled tasks are running:

```bash
#!/bin/bash
# check_cron_health.sh

# Check last run timestamps
VIOLATIONS_LOG="/var/log/cron/violations.log"
BUDGETS_LOG="/var/log/cron/budgets.log"

# Violations should run daily
if [ ! -f "$VIOLATIONS_LOG" ]; then
    echo "ERROR: Violations log not found"
    exit 1
fi

LAST_RUN=$(grep "Run Date:" "$VIOLATIONS_LOG" | tail -1 | awk '{print $3, $4}')
echo "Violations last run: $LAST_RUN"

# Budget checks should run weekly
if [ ! -f "$BUDGETS_LOG" ]; then
    echo "ERROR: Budget log not found"
    exit 1
fi

LAST_RUN=$(grep "Run Date:" "$BUDGETS_LOG" | tail -1 | awk '{print $3, $4}')
echo "Budget check last run: $LAST_RUN"
```

### Alerts

Set up monitoring alerts (e.g., via Sentry, DataDog, or custom scripts):

1. **Failed Executions** - Alert if management command exits with error code
2. **Stale Logs** - Alert if log files haven't been updated in expected timeframe
3. **Email Failures** - Alert if notifications fail to send

---

## Testing

### Manual Testing

Test scheduled tasks manually before deploying to production:

```bash
# Test violation escalation (dry run)
python manage.py escalate_overdue_violations --dry-run

# Test budget variance checks (dry run)
python manage.py check_budget_variances --dry-run

# Test with custom parameters
python manage.py escalate_overdue_violations --days-grace 2 --dry-run
python manage.py check_budget_variances --warning-threshold 15 --dry-run
```

### Automated Testing

Create integration tests for management commands:

```python
# tests/test_scheduled_tasks.py

from django.core.management import call_command
from django.test import TestCase
from accounting.models import Violation, Budget

class ScheduledTaskTests(TestCase):
    def test_escalate_overdue_violations_dry_run(self):
        """Test violation escalation in dry-run mode"""
        call_command('escalate_overdue_violations', '--dry-run')
        # Verify no escalations were created

    def test_check_budget_variances_dry_run(self):
        """Test budget variance checks in dry-run mode"""
        call_command('check_budget_variances', '--dry-run')
        # Verify no notifications were sent
```

---

## Deployment Checklist

Before deploying scheduled tasks to production:

- [ ] Test all management commands with `--dry-run`
- [ ] Verify email notifications are working
- [ ] Configure cron jobs with correct schedule
- [ ] Set up log rotation
- [ ] Configure monitoring and alerts
- [ ] Test with production-like data volumes
- [ ] Document emergency procedures (how to disable/re-enable)
- [ ] Set up backup notification channels (Slack, SMS)

---

## Emergency Procedures

### Disable Scheduled Task

If a scheduled task is causing issues:

```bash
# Comment out the cron job
crontab -e
# Add # at the beginning of the line

# Or temporarily rename the management command
mv escalate_overdue_violations.py escalate_overdue_violations.py.disabled
```

### Manual Execution

Run scheduled tasks manually if needed:

```bash
# Escalate violations manually
python manage.py escalate_overdue_violations

# Check budget variances manually
python manage.py check_budget_variances
```

---

## Future Enhancements

Potential improvements for Phase 4+:

1. **Celery Integration** - Replace cron jobs with Celery periodic tasks for better monitoring
2. **Admin Dashboard** - Web UI to view scheduled task history and manually trigger
3. **Custom Thresholds** - Per-budget variance thresholds instead of global
4. **Escalation Rules** - Configurable escalation schedules per violation type
5. **Notification Preferences** - Allow owners to choose notification delivery method
6. **Task Queue** - Async processing for large numbers of violations/budgets

---

**Document Version:** 1.0
**Last Updated:** 2025-10-29
**Phase:** 3 (Operational Features)
