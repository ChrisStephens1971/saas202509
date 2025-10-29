# S3 File Storage Configuration Guide

## Overview

This guide explains how to migrate from local file storage to AWS S3 for:
- Violation photos
- Board packet PDFs

**Current Setup:** Local file storage (media/ directory)
**Production Recommendation:** AWS S3 with CloudFront CDN

---

## Why Use S3?

### Benefits
- **Scalability:** Unlimited storage capacity
- **Reliability:** 99.999999999% (11 9's) durability
- **Cost-effective:** Pay only for what you use
- **Performance:** Global content delivery with CloudFront
- **Security:** Fine-grained access control
- **Backup:** Automatic versioning and lifecycle policies

### Cost Estimates
- **S3 Storage:** $0.023/GB/month (first 50TB)
- **S3 Requests:** $0.0004 per 1,000 GET requests
- **CloudFront:** $0.085/GB (first 10TB)
- **Typical HOA (1,000 units):** $5-20/month

---

## Setup Instructions

### 1. Install Required Packages

```bash
pip install boto3 django-storages
```

Add to `requirements.txt`:
```
boto3==1.35.0
django-storages==1.14.4
```

### 2. Create S3 Bucket

**Via AWS Console:**
1. Go to AWS S3 Console
2. Click "Create bucket"
3. Bucket name: `hoa-accounting-prod` (must be globally unique)
4. Region: `us-east-1` (or your preferred region)
5. Block Public Access: Keep enabled (we'll use signed URLs)
6. Versioning: Enable (recommended for PDFs)
7. Encryption: Enable server-side encryption
8. Create bucket

**Via AWS CLI:**
```bash
aws s3 mb s3://hoa-accounting-prod --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket hoa-accounting-prod \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket hoa-accounting-prod \
  --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

### 3. Configure IAM User

**Create IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::hoa-accounting-prod/*",
        "arn:aws:s3:::hoa-accounting-prod"
      ]
    }
  ]
}
```

**Create IAM User:**
1. IAM Console → Users → Add User
2. User name: `hoa-accounting-app`
3. Attach policy created above
4. Save Access Key ID and Secret Access Key

### 4. Configure Django Settings

**Update `settings.py`:**

```python
# Storage Configuration
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='hoa-accounting-prod')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    # S3 Object Parameters
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 day
    }

    # S3 File Storage Settings
    AWS_S3_FILE_OVERWRITE = False  # Don't overwrite files with same name
    AWS_DEFAULT_ACL = None  # Use bucket's ACL
    AWS_S3_VERIFY = True

    # Use S3 for media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Local file storage (development)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
```

### 5. Update Environment Variables

**Add to `.env.production`:**
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_STORAGE_BUCKET_NAME=hoa-accounting-prod
AWS_S3_REGION_NAME=us-east-1
```

**Security Note:** Never commit credentials to Git!

### 6. Configure CORS (for Browser Uploads)

**S3 Bucket → Permissions → CORS:**
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "POST", "PUT"],
    "AllowedOrigins": [
      "https://yourhoadomain.com",
      "http://localhost:3009"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

### 7. Test S3 Integration

```bash
# Set USE_S3=True in .env
USE_S3=True

# Run Django shell
python manage.py shell

# Test file upload
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Upload test file
content = ContentFile(b"Test content")
path = default_storage.save('test.txt', content)
print(f"Saved to: {path}")

# Get URL
url = default_storage.url(path)
print(f"URL: {url}")

# Delete test file
default_storage.delete(path)
```

---

## CloudFront CDN Setup (Optional)

### Benefits
- Faster global delivery
- HTTPS by default
- Custom domain support
- Cost-effective for frequent access

### Setup Steps

1. **Create CloudFront Distribution:**
   - Origin: S3 bucket
   - Viewer Protocol Policy: Redirect HTTP to HTTPS
   - Allowed HTTP Methods: GET, HEAD, OPTIONS, PUT, POST, DELETE
   - Compress Objects: Yes
   - Price Class: Use Only US, Canada and Europe (or adjust)

2. **Update Django Settings:**
```python
AWS_S3_CUSTOM_DOMAIN = 'd111111abcdef8.cloudfront.net'  # Your CloudFront domain
# Or use custom domain:
# AWS_S3_CUSTOM_DOMAIN = 'cdn.yourhoa.com'
```

3. **Configure Custom Domain (Optional):**
   - Add CNAME record: `cdn.yourhoa.com → d111111abcdef8.cloudfront.net`
   - Request SSL certificate in AWS Certificate Manager
   - Attach certificate to CloudFront distribution

---

## Migration from Local to S3

### Option 1: Fresh Start (New Deployment)
- Just enable S3 before launching
- All new uploads go directly to S3

### Option 2: Migrate Existing Files

**Script to migrate existing files:**

```python
# migrate_to_s3.py
import os
import boto3
from django.core.files.storage import default_storage
from pathlib import Path

def migrate_media_to_s3():
    """Migrate all files from local media/ to S3"""
    media_root = Path('media')
    s3_client = boto3.client('s3')
    bucket = 'hoa-accounting-prod'

    for file_path in media_root.rglob('*'):
        if file_path.is_file():
            # Get relative path
            relative_path = file_path.relative_to(media_root)
            s3_key = str(relative_path).replace('\\', '/')

            # Upload to S3
            with open(file_path, 'rb') as f:
                s3_client.upload_fileobj(
                    f,
                    bucket,
                    s3_key,
                    ExtraArgs={'ServerSideEncryption': 'AES256'}
                )

            print(f'Uploaded: {s3_key}')

# Run migration
migrate_media_to_s3()
```

**Run migration:**
```bash
python manage.py shell < migrate_to_s3.py
```

---

## Signed URLs (Private Access)

For sensitive files (board packets), use signed URLs:

**Update `api_views.py`:**
```python
from storages.backends.s3boto3 import S3Boto3Storage

@action(detail=True, methods=['get'])
def download_pdf(self, request, pk=None):
    """Generate signed URL for secure PDF download"""
    packet = self.get_object()

    if settings.USE_S3:
        # Generate signed URL (expires in 1 hour)
        storage = S3Boto3Storage()
        url = storage.url(packet.pdf_url, expire=3600)
    else:
        # Local file
        url = packet.pdf_url

    return Response({'download_url': url})
```

---

## Backup and Lifecycle Policies

### Enable Versioning
```bash
aws s3api put-bucket-versioning \
  --bucket hoa-accounting-prod \
  --versioning-configuration Status=Enabled
```

### Lifecycle Rules

**Delete old versions after 90 days:**
```json
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

**Apply lifecycle:**
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket hoa-accounting-prod \
  --lifecycle-configuration file://lifecycle.json
```

---

## Monitoring and Costs

### CloudWatch Metrics
- Number of Objects
- Bucket Size Bytes
- All Requests
- Data Transfer

### Cost Optimization Tips
1. Use Intelligent-Tiering for automatic cost optimization
2. Enable CloudFront to reduce S3 GET requests
3. Set lifecycle policies to archive old files to Glacier
4. Use S3 Select to reduce data transfer
5. Compress files before uploading

---

## Troubleshooting

### 403 Forbidden
- Check IAM permissions
- Verify bucket policy
- Ensure AWS credentials are correct

### CORS Errors
- Configure CORS on S3 bucket
- Verify allowed origins
- Check request headers

### Slow Uploads
- Use multipart uploads for large files (>100MB)
- Enable transfer acceleration
- Use CloudFront for distribution

### Connection Timeout
- Check security group rules
- Verify VPC endpoints (if using)
- Increase timeout in boto3 config

---

## Production Checklist

- [ ] S3 bucket created and configured
- [ ] IAM user created with proper permissions
- [ ] django-storages and boto3 installed
- [ ] Environment variables set
- [ ] CORS configured
- [ ] Versioning enabled
- [ ] Encryption enabled
- [ ] Lifecycle policies configured
- [ ] CloudFront distribution created (optional)
- [ ] Custom domain configured (optional)
- [ ] Backup strategy in place
- [ ] Monitoring enabled
- [ ] Cost alerts configured
- [ ] Migration tested in staging
- [ ] Documentation updated

---

## References

- [django-storages documentation](https://django-storages.readthedocs.io/)
- [AWS S3 documentation](https://docs.aws.amazon.com/s3/)
- [boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [CloudFront documentation](https://docs.aws.amazon.com/cloudfront/)

---

**Last Updated:** 2025-10-29
**Version:** 1.0
