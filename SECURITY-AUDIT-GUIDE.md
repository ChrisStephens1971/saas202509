# Security Audit & Hardening Guide

## Overview

Comprehensive security checklist and hardening guide for the HOA Accounting System.

**Security Goals:**
- Protect sensitive financial data
- Prevent unauthorized access
- Comply with data protection regulations
- Pass security audit requirements

---

## Quick Security Checklist

### Critical (Must Do Before Production)
- [ ] HTTPS/TLS enabled with valid certificate
- [ ] SECRET_KEY rotated and never committed to Git
- [ ] DEBUG=False in production
- [ ] Strong database passwords
- [ ] Rate limiting enabled
- [ ] CSRF protection verified
- [ ] SQL injection protection (using Django ORM)
- [ ] XSS protection (React default escaping)
- [ ] Dependency audit completed
- [ ] Secure headers configured

### Important (Highly Recommended)
- [ ] Two-factor authentication
- [ ] IP whitelist for admin panel
- [ ] Regular security updates
- [ ] Automated backups
- [ ] Security logging and monitoring
- [ ] Penetration testing completed

### Nice to Have (Additional Protection)
- [ ] Web Application Firewall (WAF)
- [ ] DDoS protection (CloudFlare)
- [ ] Security audit by third party
- [ ] Bug bounty program
- [ ] Security training for team

---

## 1. Dependency Security

### pip-audit (Python)

**Install:**
```bash
pip install pip-audit
```

**Run audit:**
```bash
cd backend
pip-audit

# With fix suggestions
pip-audit --fix

# Generate report
pip-audit --format json > security-audit.json
```

**Example output:**
```
Found 2 known vulnerabilities in 1 package
Name    Version  ID               Fix Versions
------  -------  ---------------  ------------
pillow  9.0.0    GHSA-xxx-yyy-zzz 9.3.0
```

**Fix vulnerabilities:**
```bash
pip install --upgrade pillow==11.0.0
pip freeze > requirements.txt
```

### npm audit (Frontend)

**Run audit:**
```bash
cd frontend
npm audit

# Auto-fix (be careful!)
npm audit fix

# Force major version updates
npm audit fix --force
```

### Automate Security Checks

**GitHub Actions (`.github/workflows/security.yml`):**
```yaml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Security Audit
        run: |
          cd backend
          pip install pip-audit
          pip-audit

      - name: JavaScript Security Audit
        run: |
          cd frontend
          npm audit
```

---

## 2. Code Security Scanning

### Bandit (Python Static Analysis)

**Install:**
```bash
pip install bandit
```

**Run scan:**
```bash
cd backend
bandit -r accounting/ hoaaccounting/

# Generate report
bandit -r accounting/ -f json -o security-report.json

# Exclude false positives
bandit -r accounting/ --skip B101,B601
```

**Common issues to fix:**
- Hardcoded passwords
- Use of `exec()` or `eval()`
- Weak cryptography
- SQL injection risks
- Insecure file permissions

**Example fix:**
```python
# Bad
password = "admin123"  # B105: hardcoded password

# Good
password = os.environ.get('ADMIN_PASSWORD')
```

### Safety (Known Vulnerabilities)

**Install:**
```bash
pip install safety
```

**Check dependencies:**
```bash
safety check --file requirements.txt

# Generate JSON report
safety check --json --output security-report.json
```

---

## 3. Django Security Settings

### Production Settings (`settings.py`)

**Critical settings:**
```python
# Never True in production!
DEBUG = False

# Strong secret key
SECRET_KEY = env('SECRET_KEY')  # From environment, never in code

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Restrict hosts
ALLOWED_HOSTS = ['yourhoadomain.com', 'www.yourhoadomain.com']

# CORS (be specific!)
CORS_ALLOWED_ORIGINS = [
    'https://yourhoadomain.com',
    'https://www.yourhoadomain.com',
]

# Cookie security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

### Check Django Security

```bash
python manage.py check --deploy
```

**Fix all warnings!**

---

## 4. Rate Limiting

### django-ratelimit

**Install:**
```bash
pip install django-ratelimit
```

**Apply to sensitive endpoints:**
```python
from django_ratelimit.decorators import ratelimit

class AuthViewSet(viewsets.ViewSet):
    @ratelimit(key='ip', rate='5/m', method='POST')
    def login(self, request):
        # Only 5 login attempts per minute per IP
        # ...
```

**Rate limit configuration:**
```python
# Login: 5 attempts per minute
@ratelimit(key='ip', rate='5/m')

# Password reset: 3 per hour
@ratelimit(key='user', rate='3/h')

# API: 100 requests per minute
@ratelimit(key='user', rate='100/m')

# File uploads: 10 per hour
@ratelimit(key='ip', rate='10/h')
```

---

## 5. Authentication & Authorization

### Strong Passwords

**Configure password validators:**
```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Minimum 12 characters
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### Two-Factor Authentication (Optional)

**Install django-otp:**
```bash
pip install django-otp qrcode
```

**Configure:**
```python
INSTALLED_APPS = [
    # ...
    'django_otp',
    'django_otp.plugins.otp_totp',
]

MIDDLEWARE = [
    # ...
    'django_otp.middleware.OTPMiddleware',
]
```

### JWT Token Security

**Configure SimpleJWT:**
```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Short-lived
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,  # Rotate on refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old tokens
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

---

## 6. Input Validation

### Never Trust User Input

**Django Forms validation:**
```python
class InvoiceForm(forms.ModelForm):
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        if amount > Decimal('1000000'):
            raise ValidationError("Amount exceeds maximum")
        return amount
```

**DRF Serializer validation:**
```python
class InvoiceSerializer(serializers.ModelSerializer):
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
```

### File Upload Security

**Validate file types:**
```python
def validate_image(file):
    # Check file extension
    ext = file.name.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'heic']:
        raise ValidationError("Invalid file type")

    # Validate content type
    if file.content_type not in ['image/jpeg', 'image/png', 'image/heic']:
        raise ValidationError("Invalid content type")

    # Verify it's actually an image
    try:
        from PIL import Image
        image = Image.open(file)
        image.verify()
    except Exception:
        raise ValidationError("File is not a valid image")
```

---

## 7. Database Security

### Connection Security

**Use SSL for database connections:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL
        }
    }
}
```

### Prevent SQL Injection

**Always use Django ORM:**
```python
# Bad (SQL injection vulnerable)
query = f"SELECT * FROM invoices WHERE owner = '{owner_name}'"
cursor.execute(query)

# Good (parameterized)
Invoice.objects.filter(owner__full_name=owner_name)
```

**If raw SQL is necessary:**
```python
# Use parameterized queries
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM invoices WHERE owner_id = %s", [owner_id])
```

### Database User Permissions

**Principle of least privilege:**
```sql
-- Application user (limited permissions)
CREATE USER hoaapp WITH PASSWORD 'strong_password';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO hoaapp;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO hoaapp;
-- No DELETE or DROP permissions!

-- Admin user (for migrations only)
CREATE USER hoaadmin WITH PASSWORD 'even_stronger_password';
GRANT ALL PRIVILEGES ON DATABASE hoaaccounting TO hoaadmin;
```

---

## 8. API Security

### Secure Headers

**Install django-cors-headers:**
```bash
pip install django-cors-headers
```

**Configure:**
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
]

CORS_ALLOW_CREDENTIALS = True

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### API Rate Limiting

**Per-user limits:**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',
        'user': '1000/hour'
    }
}
```

---

## 9. Secrets Management

### Environment Variables

**Never commit secrets:**
```bash
# .gitignore
.env
.env.production
*.key
*.pem
secrets/
```

**Use environment variables:**
```python
# settings.py
import environ

env = environ.Env()
environ.Env.read_env('.env')

SECRET_KEY = env('SECRET_KEY')
DATABASE_PASSWORD = env('DATABASE_PASSWORD')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
```

### AWS Secrets Manager (Production)

**Store sensitive values in AWS:**
```python
import boto3
import json

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client('secretsmanager', region_name='us-east-1')
    secret = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret['SecretString'])

# settings.py
if ENV == 'production':
    secrets = get_secret('hoaaccounting/production')
    SECRET_KEY = secrets['SECRET_KEY']
    DATABASE_PASSWORD = secrets['DATABASE_PASSWORD']
```

---

## 10. Logging & Monitoring

### Security Event Logging

**Configure logging:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'security': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/security.log',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

**Log important events:**
```python
import logging
security_logger = logging.getLogger('django.security')

# Login attempts
security_logger.warning(f'Failed login attempt for user {username} from IP {ip}')

# Permission denials
security_logger.warning(f'Unauthorized access attempt by user {user} to {resource}')

# Data modifications
security_logger.info(f'User {user} modified invoice {invoice_id}')
```

### Monitoring with Sentry

**Install:**
```bash
pip install sentry-sdk
```

**Configure:**
```python
import sentry_sdk

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    traces_sample_rate=0.1,
    environment=env('ENVIRONMENT'),
)
```

---

## 11. Regular Maintenance

### Security Update Schedule

**Weekly:**
- Check for dependency updates
- Review security advisories
- Monitor security logs

**Monthly:**
- Full dependency audit
- Review access logs
- Rotate secrets (if policy requires)
- Backup verification

**Quarterly:**
- Penetration testing
- Security training
- Policy review
- Incident response drill

---

## 12. Incident Response

### Security Incident Checklist

**If breach suspected:**
1. [ ] Isolate affected systems
2. [ ] Preserve evidence
3. [ ] Notify stakeholders
4. [ ] Change all credentials
5. [ ] Review logs for scope
6. [ ] Patch vulnerabilities
7. [ ] Document incident
8. [ ] Notify authorities (if required)
9. [ ] Conduct post-mortem
10. [ ] Update security policies

---

## Security Tools Summary

| Tool | Purpose | Command |
|------|---------|---------|
| pip-audit | Python dependencies | `pip-audit` |
| safety | Known vulnerabilities | `safety check` |
| bandit | Code security scan | `bandit -r .` |
| npm audit | Frontend dependencies | `npm audit` |
| Django check | Django security | `python manage.py check --deploy` |

---

## Compliance Considerations

### GDPR (if applicable)
- [ ] Data encryption at rest and in transit
- [ ] User data export capability
- [ ] Right to be forgotten (data deletion)
- [ ] Consent management
- [ ] Privacy policy

### HIPAA (if handling health data)
- [ ] Encrypted storage
- [ ] Access audit logs
- [ ] User authentication
- [ ] Data backup and recovery

### SOC 2 (for SaaS)
- [ ] Access controls
- [ ] Audit logging
- [ ] Vulnerability management
- [ ] Incident response plan

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Guide](https://docs.djangoproject.com/en/5.1/topics/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Last Updated:** 2025-10-29
**Version:** 1.0
**Compliance:** GDPR-ready, SOC 2-ready
