#!/bin/bash

#################################
# HOA Accounting System - Security Audit Script
# Runs comprehensive security checks and generates reports
#################################

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPORT_DIR="security-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# Counters
VULNERABILITIES_FOUND=0
CRITICAL_ISSUES=0
HIGH_ISSUES=0
MEDIUM_ISSUES=0
LOW_ISSUES=0

# Helper functions
function print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main security audit
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   HOA System - Security Audit           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Create reports directory
mkdir -p $REPORT_DIR
print_info "Reports will be saved to: $REPORT_DIR/"

#################################
# 1. Python Dependency Audit
#################################
print_header "1. PYTHON DEPENDENCY AUDIT (pip-audit)"

cd $BACKEND_DIR

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    print_warning "pip-audit not installed. Installing..."
    pip install pip-audit
fi

print_info "Scanning Python dependencies for known vulnerabilities..."

# Run pip-audit
if pip-audit --format json > ../$REPORT_DIR/pip-audit-${TIMESTAMP}.json 2>&1; then
    print_success "No vulnerabilities found in Python dependencies"
else
    VULN_COUNT=$(jq '.vulnerabilities | length' ../$REPORT_DIR/pip-audit-${TIMESTAMP}.json 2>/dev/null || echo "0")
    if [ "$VULN_COUNT" -gt 0 ]; then
        print_error "Found $VULN_COUNT vulnerable dependencies"
        ((VULNERABILITIES_FOUND += VULN_COUNT))

        # Show summary
        print_info "Vulnerable packages:"
        jq -r '.vulnerabilities[] | "\(.name) \(.installed_version) -> \(.fixed_versions[])"' \
            ../$REPORT_DIR/pip-audit-${TIMESTAMP}.json 2>/dev/null || echo "  (See report for details)"
    else
        print_success "No vulnerabilities found"
    fi
fi

cd ..

#################################
# 2. Python Safety Check
#################################
print_header "2. PYTHON SAFETY CHECK"

cd $BACKEND_DIR

# Check if safety is installed
if ! command -v safety &> /dev/null; then
    print_warning "safety not installed. Installing..."
    pip install safety
fi

print_info "Checking Python dependencies with Safety..."

# Run safety check
if safety check --json > ../$REPORT_DIR/safety-${TIMESTAMP}.json 2>&1; then
    print_success "No known vulnerabilities found"
else
    SAFETY_COUNT=$(jq '. | length' ../$REPORT_DIR/safety-${TIMESTAMP}.json 2>/dev/null || echo "0")
    if [ "$SAFETY_COUNT" -gt 0 ]; then
        print_error "Found $SAFETY_COUNT security issues"
        ((VULNERABILITIES_FOUND += SAFETY_COUNT))
    fi
fi

cd ..

#################################
# 3. Python Static Analysis (Bandit)
#################################
print_header "3. PYTHON STATIC ANALYSIS (Bandit)"

cd $BACKEND_DIR

# Check if bandit is installed
if ! command -v bandit &> /dev/null; then
    print_warning "bandit not installed. Installing..."
    pip install bandit
fi

print_info "Running Bandit security scanner on Python code..."

# Run bandit
bandit -r accounting/ hoaaccounting/ -f json -o ../$REPORT_DIR/bandit-${TIMESTAMP}.json 2>/dev/null || true

# Parse results
if [ -f "../$REPORT_DIR/bandit-${TIMESTAMP}.json" ]; then
    BANDIT_ISSUES=$(jq '.results | length' ../$REPORT_DIR/bandit-${TIMESTAMP}.json 2>/dev/null || echo "0")

    if [ "$BANDIT_ISSUES" -gt 0 ]; then
        print_warning "Found $BANDIT_ISSUES potential security issues"

        # Count by severity
        CRITICAL=$(jq '[.results[] | select(.issue_severity=="CRITICAL")] | length' ../$REPORT_DIR/bandit-${TIMESTAMP}.json 2>/dev/null || echo "0")
        HIGH=$(jq '[.results[] | select(.issue_severity=="HIGH")] | length' ../$REPORT_DIR/bandit-${TIMESTAMP}.json 2>/dev/null || echo "0")
        MEDIUM=$(jq '[.results[] | select(.issue_severity=="MEDIUM")] | length' ../$REPORT_DIR/bandit-${TIMESTAMP}.json 2>/dev/null || echo "0")
        LOW=$(jq '[.results[] | select(.issue_severity=="LOW")] | length' ../$REPORT_DIR/bandit-${TIMESTAMP}.json 2>/dev/null || echo "0")

        print_info "  Critical: $CRITICAL, High: $HIGH, Medium: $MEDIUM, Low: $LOW"

        ((CRITICAL_ISSUES += CRITICAL))
        ((HIGH_ISSUES += HIGH))
        ((MEDIUM_ISSUES += MEDIUM))
        ((LOW_ISSUES += LOW))
    else
        print_success "No security issues found in code"
    fi
fi

cd ..

#################################
# 4. Django Security Check
#################################
print_header "4. DJANGO SECURITY CHECK"

print_info "Running Django security checks..."

# Run Django check with deployment settings
if docker-compose -f docker-compose.production.yml exec -T backend python manage.py check --deploy > $REPORT_DIR/django-check-${TIMESTAMP}.txt 2>&1; then
    print_success "Django security checks passed"
else
    DJANGO_WARNINGS=$(grep -c "WARNING" $REPORT_DIR/django-check-${TIMESTAMP}.txt || echo "0")
    DJANGO_ERRORS=$(grep -c "ERROR" $REPORT_DIR/django-check-${TIMESTAMP}.txt || echo "0")

    if [ "$DJANGO_ERRORS" -gt 0 ]; then
        print_error "Found $DJANGO_ERRORS Django security errors"
        ((CRITICAL_ISSUES += DJANGO_ERRORS))
    fi

    if [ "$DJANGO_WARNINGS" -gt 0 ]; then
        print_warning "Found $DJANGO_WARNINGS Django security warnings"
        ((MEDIUM_ISSUES += DJANGO_WARNINGS))
    fi

    print_info "Check report: $REPORT_DIR/django-check-${TIMESTAMP}.txt"
fi

#################################
# 5. Frontend Dependency Audit (npm)
#################################
print_header "5. FRONTEND DEPENDENCY AUDIT (npm audit)"

cd $FRONTEND_DIR

print_info "Auditing frontend dependencies..."

# Run npm audit
if npm audit --json > ../$REPORT_DIR/npm-audit-${TIMESTAMP}.json 2>&1; then
    print_success "No vulnerabilities found in frontend dependencies"
else
    # Parse npm audit results
    if [ -f "../$REPORT_DIR/npm-audit-${TIMESTAMP}.json" ]; then
        CRITICAL_NPM=$(jq '.metadata.vulnerabilities.critical // 0' ../$REPORT_DIR/npm-audit-${TIMESTAMP}.json 2>/dev/null || echo "0")
        HIGH_NPM=$(jq '.metadata.vulnerabilities.high // 0' ../$REPORT_DIR/npm-audit-${TIMESTAMP}.json 2>/dev/null || echo "0")
        MODERATE_NPM=$(jq '.metadata.vulnerabilities.moderate // 0' ../$REPORT_DIR/npm-audit-${TIMESTAMP}.json 2>/dev/null || echo "0")
        LOW_NPM=$(jq '.metadata.vulnerabilities.low // 0' ../$REPORT_DIR/npm-audit-${TIMESTAMP}.json 2>/dev/null || echo "0")

        TOTAL_NPM=$((CRITICAL_NPM + HIGH_NPM + MODERATE_NPM + LOW_NPM))

        if [ "$TOTAL_NPM" -gt 0 ]; then
            print_warning "Found $TOTAL_NPM vulnerabilities in frontend dependencies"
            print_info "  Critical: $CRITICAL_NPM, High: $HIGH_NPM, Moderate: $MODERATE_NPM, Low: $LOW_NPM"

            ((CRITICAL_ISSUES += CRITICAL_NPM))
            ((HIGH_ISSUES += HIGH_NPM))
            ((MEDIUM_ISSUES += MODERATE_NPM))
            ((LOW_ISSUES += LOW_NPM))
        else
            print_success "No vulnerabilities found"
        fi
    fi
fi

cd ..

#################################
# 6. Environment Variables Check
#################################
print_header "6. ENVIRONMENT VARIABLES CHECK"

print_info "Checking for exposed secrets..."

# Check if .env files are in .gitignore
if grep -q ".env" .gitignore 2>/dev/null; then
    print_success ".env files are in .gitignore"
else
    print_error ".env files are NOT in .gitignore!"
    ((CRITICAL_ISSUES += 1))
fi

# Check for hardcoded secrets in code
print_info "Scanning for hardcoded secrets..."
SECRETS_FOUND=0

# Common secret patterns
grep -r -i "password.*=.*['\"]" backend/ --include="*.py" > $REPORT_DIR/secrets-scan-${TIMESTAMP}.txt 2>/dev/null || true
grep -r -i "secret.*=.*['\"]" backend/ --include="*.py" >> $REPORT_DIR/secrets-scan-${TIMESTAMP}.txt 2>/dev/null || true
grep -r -i "api.*key.*=.*['\"]" backend/ --include="*.py" >> $REPORT_DIR/secrets-scan-${TIMESTAMP}.txt 2>/dev/null || true

if [ -s "$REPORT_DIR/secrets-scan-${TIMESTAMP}.txt" ]; then
    SECRETS_FOUND=$(wc -l < $REPORT_DIR/secrets-scan-${TIMESTAMP}.txt)
    print_warning "Found $SECRETS_FOUND potential hardcoded secrets (review manually)"
    ((HIGH_ISSUES += 1))
else
    print_success "No obvious hardcoded secrets found"
fi

#################################
# 7. HTTPS & Security Headers Check
#################################
print_header "7. SECURITY HEADERS CHECK"

print_info "Checking security headers configuration..."

# Check Django settings for security
SECURE_SETTINGS=$(docker-compose -f docker-compose.production.yml exec -T backend python -c "
from django.conf import settings
checks = {
    'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', False),
    'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
    'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
    'SECURE_HSTS_SECONDS': getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0,
    'SECURE_CONTENT_TYPE_NOSNIFF': getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
    'X_FRAME_OPTIONS': getattr(settings, 'X_FRAME_OPTIONS', None) == 'DENY',
}
for key, value in checks.items():
    print(f'{key}={value}')
" 2>/dev/null)

echo "$SECURE_SETTINGS" > $REPORT_DIR/security-headers-${TIMESTAMP}.txt

INSECURE_SETTINGS=$(echo "$SECURE_SETTINGS" | grep -c "=False" || echo "0")

if [ "$INSECURE_SETTINGS" -gt 0 ]; then
    print_warning "Found $INSECURE_SETTINGS insecure security settings"
    print_info "Check: $REPORT_DIR/security-headers-${TIMESTAMP}.txt"
    ((MEDIUM_ISSUES += INSECURE_SETTINGS))
else
    print_success "Security headers properly configured"
fi

#################################
# 8. Database Security Check
#################################
print_header "8. DATABASE SECURITY CHECK"

print_info "Checking database configuration..."

# Check if SSL is enabled for database
DB_SSL=$(docker-compose -f docker-compose.production.yml exec -T backend python -c "
from django.conf import settings
db = settings.DATABASES['default']
print(db.get('OPTIONS', {}).get('sslmode', 'none'))
" 2>/dev/null || echo "unknown")

if [[ "$DB_SSL" == "require" ]] || [[ "$DB_SSL" == "verify-full" ]]; then
    print_success "Database SSL is enabled"
else
    print_warning "Database SSL is not enabled (recommend 'require' or 'verify-full')"
    ((MEDIUM_ISSUES += 1))
fi

#################################
# 9. File Permissions Check
#################################
print_header "9. FILE PERMISSIONS CHECK"

print_info "Checking file permissions..."

# Check for world-writable files
WRITABLE_FILES=$(find . -type f -perm -002 2>/dev/null | wc -l)

if [ "$WRITABLE_FILES" -gt 0 ]; then
    print_warning "Found $WRITABLE_FILES world-writable files"
    find . -type f -perm -002 2>/dev/null > $REPORT_DIR/writable-files-${TIMESTAMP}.txt
    ((LOW_ISSUES += 1))
else
    print_success "No world-writable files found"
fi

#################################
# 10. Generate Summary Report
#################################
print_header "10. GENERATING SUMMARY REPORT"

SUMMARY_FILE="$REPORT_DIR/security-audit-summary-${TIMESTAMP}.txt"

cat > $SUMMARY_FILE <<EOF
HOA Accounting System - Security Audit Summary
===============================================

Date: $(date)
Timestamp: $TIMESTAMP

FINDINGS SUMMARY
================

Total Vulnerabilities Found: $VULNERABILITIES_FOUND

Issues by Severity:
  Critical: $CRITICAL_ISSUES
  High:     $HIGH_ISSUES
  Medium:   $MEDIUM_ISSUES
  Low:      $LOW_ISSUES

AUDIT SECTIONS
==============

1. Python Dependencies (pip-audit)
   - Report: pip-audit-${TIMESTAMP}.json

2. Python Safety Check
   - Report: safety-${TIMESTAMP}.json

3. Python Static Analysis (Bandit)
   - Report: bandit-${TIMESTAMP}.json

4. Django Security Check
   - Report: django-check-${TIMESTAMP}.txt

5. Frontend Dependencies (npm audit)
   - Report: npm-audit-${TIMESTAMP}.json

6. Environment Variables
   - Report: secrets-scan-${TIMESTAMP}.txt

7. Security Headers
   - Report: security-headers-${TIMESTAMP}.txt

8. Database Security
   - SSL Mode: $DB_SSL

9. File Permissions
   - World-writable files: $WRITABLE_FILES

RECOMMENDATIONS
===============

EOF

# Add recommendations based on findings
if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    echo "❌ CRITICAL: Address all critical issues immediately before production!" >> $SUMMARY_FILE
fi

if [ "$HIGH_ISSUES" -gt 0 ]; then
    echo "⚠️  HIGH: Fix high-severity issues as soon as possible" >> $SUMMARY_FILE
fi

if [ "$VULNERABILITIES_FOUND" -gt 0 ]; then
    echo "📦 Update vulnerable dependencies using 'pip install --upgrade' or 'npm update'" >> $SUMMARY_FILE
fi

if [[ "$DB_SSL" != "require" ]] && [[ "$DB_SSL" != "verify-full" ]]; then
    echo "🔒 Enable SSL for database connections in production" >> $SUMMARY_FILE
fi

echo "" >> $SUMMARY_FILE
echo "For detailed remediation steps, consult SECURITY-AUDIT-GUIDE.md" >> $SUMMARY_FILE

print_success "Summary report generated: $SUMMARY_FILE"

#################################
# Display Summary
#################################
print_header "SECURITY AUDIT COMPLETE"

echo ""
cat $SUMMARY_FILE
echo ""

# Final status
TOTAL_ISSUES=$((CRITICAL_ISSUES + HIGH_ISSUES + MEDIUM_ISSUES + LOW_ISSUES))

if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    print_error "CRITICAL ISSUES FOUND! Address immediately before production."
    echo ""
    echo "Next steps:"
    echo "  1. Review: $SUMMARY_FILE"
    echo "  2. Fix critical issues"
    echo "  3. Update dependencies"
    echo "  4. Re-run this audit"
    exit 1
elif [ "$HIGH_ISSUES" -gt 0 ]; then
    print_warning "High-severity issues found. Recommend fixing before production."
    echo ""
    echo "Next steps:"
    echo "  1. Review: $SUMMARY_FILE"
    echo "  2. Fix high-severity issues"
    echo "  3. Update dependencies"
    echo "  4. Re-run this audit"
    exit 1
elif [ "$TOTAL_ISSUES" -gt 0 ]; then
    print_warning "Medium/Low issues found. Consider fixing before production."
    echo ""
    echo -e "${GREEN}System is production-ready with minor improvements recommended${NC}"
    exit 0
else
    print_success "No security issues found! System is secure."
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ SECURITY AUDIT PASSED! ✅            ║${NC}"
    echo -e "${GREEN}║  System is production-ready               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    exit 0
fi
