# HOA Accounting System - Production Deployment Guide

Complete guide for deploying the HOA Accounting System to production using Docker.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Quick Start](#quick-start)
- [Detailed Deployment Steps](#detailed-deployment-steps)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## Prerequisites

### Required
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Domain name** with DNS configured
- **SSL certificate** (Let's Encrypt recommended)
- **Server** with minimum:
  - 2 CPU cores
  - 4GB RAM
  - 20GB disk space
  - Ubuntu 22.04 LTS or similar

### Optional but Recommended
- **Sentry** account for error tracking
- **AWS S3** or similar for file storage
- **Backup** solution configured

---

## Pre-Deployment Checklist

### 1. Test Suite
```bash
# Run tests in QA project (saas202510)
cd /path/to/saas202510
pytest tests/test_bank_reconciliation.py -v

# Expected: 18 tests passed ✅
```

### 2. Environment Configuration
```bash
# Copy and configure environment file
cp .env.production.example .env.production

# Edit .env.production with your values
nano .env.production
```

**Critical settings to update:**
- `DJANGO_SECRET_KEY` - Generate with: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `POSTGRES_PASSWORD` - Strong password (16+ chars)
- `ALLOWED_HOSTS` - Your domain(s)
- `CORS_ALLOWED_ORIGINS` - Your frontend URL(s)
- `EMAIL_*` - Email service credentials

### 3. Database Backup
```bash
# If migrating from existing database
pg_dump hoaaccounting > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. DNS Configuration
Ensure DNS records point to your server:
```
A     yourdomain.com          -> YOUR_SERVER_IP
A     www.yourdomain.com      -> YOUR_SERVER_IP
A     api.yourdomain.com      -> YOUR_SERVER_IP
```

---

## Quick Start

For experienced users who just want to deploy:

```bash
# 1. Clone repository
git clone https://github.com/ChrisStephens1971/saas202509.git
cd saas202509

# 2. Configure environment
cp .env.production.example .env.production
# Edit .env.production

# 3. Build and start
docker-compose -f docker-compose.production.yml up -d --build

# 4. Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

# 5. Verify
curl http://localhost:8009/api/v1/accounting/accounts/
curl http://localhost:3009/
```

---

## Detailed Deployment Steps

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2: SSL Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot -y

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Step 3: Application Deployment

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/ChrisStephens1971/saas202509.git
sudo chown -R $USER:$USER saas202509
cd saas202509

# Configure environment
cp .env.production.example .env.production

# IMPORTANT: Edit these values
nano .env.production

# Build images (this takes 5-10 minutes)
docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f
```

### Step 4: Database Initialization

```bash
# Wait for database to be healthy
docker-compose -f docker-compose.production.yml exec postgres pg_isready

# Run migrations (should auto-run, but verify)
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
# Enter: admin / your-email@domain.com / strong-password

# Collect static files (should auto-run, but verify)
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### Step 5: Verify Deployment

```bash
# Check all containers are running
docker-compose -f docker-compose.production.yml ps

# Expected output:
# hoa-postgres    running    5409/tcp
# hoa-backend     running    8009/tcp
# hoa-frontend    running    3009/tcp
# hoa-redis       running    6409/tcp

# Test backend API
curl http://localhost:8009/api/v1/accounting/accounts/

# Test frontend
curl http://localhost:3009/

# Check container health
docker-compose -f docker-compose.production.yml exec backend python manage.py check
```

---

## Post-Deployment

### 1. Configure Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/hoaaccounting

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3009;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8009;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/saas202509/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /opt/saas202509/media/;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/hoaaccounting /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Setup Automatic Backups

```bash
# Create backup script
cat > /opt/backup-hoa.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose -f /opt/saas202509/docker-compose.production.yml exec -T postgres \
    pg_dump -U hoaadmin hoaaccounting > "$BACKUP_DIR/db_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_$DATE.sql"

# Keep last 30 days
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.gz"
EOF

chmod +x /opt/backup-hoa.sh

# Add to crontab (daily at 2am)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-hoa.sh") | crontab -
```

### 3. Setup Monitoring

```bash
# Install monitoring tools
docker run -d \
  --name=cadvisor \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --publish=8080:8080 \
  gcr.io/cadvisor/cadvisor:latest

# View metrics at http://your-server:8080
```

---

## Monitoring & Maintenance

### Daily Checks

```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Check logs for errors
docker-compose -f docker-compose.production.yml logs --tail=100

# Check disk space
df -h

# Check database connections
docker-compose -f docker-compose.production.yml exec postgres \
    psql -U hoaadmin -d hoaaccounting -c "SELECT count(*) FROM pg_stat_activity;"
```

### Weekly Maintenance

```bash
# Update images (if needed)
docker-compose -f docker-compose.production.yml pull

# Restart services
docker-compose -f docker-compose.production.yml restart

# Clean up old images
docker system prune -a --volumes -f

# Verify backups
ls -lh /opt/backups/
```

### Performance Monitoring

```bash
# Database stats
docker-compose -f docker-compose.production.yml exec backend python manage.py dbshell
\d+ bank_statements
\d+ bank_transactions

# API response times
docker-compose -f docker-compose.production.yml logs backend | grep "GET /api"

# Resource usage
docker stats
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml logs frontend

# Check environment variables
docker-compose -f docker-compose.production.yml config

# Rebuild from scratch
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up -d --build
```

### Database Connection Issues

```bash
# Test database connection
docker-compose -f docker-compose.production.yml exec postgres \
    psql -U hoaadmin -d hoaaccounting -c "SELECT 1;"

# Check credentials in .env.production
cat .env.production | grep POSTGRES

# Restart database
docker-compose -f docker-compose.production.yml restart postgres
```

### Frontend Not Loading

```bash
# Check Nginx logs
docker-compose -f docker-compose.production.yml logs frontend

# Verify build
docker-compose -f docker-compose.production.yml exec frontend ls /usr/share/nginx/html

# Check network
curl http://localhost:3009/health
```

### Performance Issues

```bash
# Check resources
docker stats

# Scale backend workers
docker-compose -f docker-compose.production.yml up -d --scale backend=3

# Check database performance
docker-compose -f docker-compose.production.yml exec postgres \
    psql -U hoaadmin -d hoaaccounting -c "
    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    LIMIT 10;"
```

---

## Security

### Best Practices

1. **Never commit** `.env.production` to git
2. **Use strong passwords** (16+ characters, mixed case, numbers, symbols)
3. **Enable firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **Regular updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose -f docker-compose.production.yml pull
   ```
5. **Monitor logs** for suspicious activity
6. **Backup regularly** (automated script provided above)

### Security Headers

Already configured in `nginx.conf`:
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- HSTS enabled

### Database Security

```bash
# Restrict database access
docker-compose -f docker-compose.production.yml exec postgres \
    psql -U hoaadmin -d hoaaccounting -c "
    REVOKE ALL ON SCHEMA public FROM PUBLIC;
    GRANT ALL ON SCHEMA public TO hoaadmin;"
```

---

## Updating the Application

### Zero-Downtime Deployment

```bash
# Pull latest code
cd /opt/saas202509
git pull origin master

# Build new images
docker-compose -f docker-compose.production.yml build

# Run migrations (if needed)
docker-compose -f docker-compose.production.yml run --rm backend python manage.py migrate

# Rolling update
docker-compose -f docker-compose.production.yml up -d

# Verify
docker-compose -f docker-compose.production.yml ps
```

---

## Support & Resources

- **Documentation**: `README.md`
- **Architecture**: `technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md`
- **Sprint Plans**: `sprints/current/`
- **GitHub**: https://github.com/ChrisStephens1971/saas202509
- **Issues**: https://github.com/ChrisStephens1971/saas202509/issues

---

## Production Checklist

Before going live, ensure:

- [ ] All tests passing (18/18 in saas202510)
- [ ] `.env.production` configured with production values
- [ ] SSL certificates installed and working
- [ ] Database backups automated
- [ ] Monitoring setup (logs, metrics)
- [ ] Firewall configured
- [ ] DNS records configured
- [ ] Domain pointing to server
- [ ] Nginx reverse proxy configured
- [ ] Superuser account created
- [ ] Email notifications working
- [ ] CORS configured for your domain
- [ ] Security headers enabled
- [ ] Automated updates scheduled

---

**Deployment complete! Your HOA Accounting System is production-ready.** 🚀
