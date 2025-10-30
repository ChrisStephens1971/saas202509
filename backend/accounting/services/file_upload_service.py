"""
File Upload Service - S3 and Local Storage Support

Handles file uploads for:
- Violation photos
- ARC request documents (plans, specs, photos, contracts)
- Work order attachments
"""

import os
import uuid
import mimetypes
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class FileUploadService:
    """Service for handling file uploads with S3/local storage."""

    # Allowed file extensions by category
    ALLOWED_IMAGES = ['.jpg', '.jpeg', '.png', '.gif', '.heic']
    ALLOWED_DOCUMENTS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
    ALLOWED_ALL = ALLOWED_IMAGES + ALLOWED_DOCUMENTS

    # Maximum file sizes (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DOCUMENT_SIZE = 25 * 1024 * 1024  # 25MB

    @staticmethod
    def generate_filename(original_filename, prefix=''):
        """
        Generate a unique filename for upload.

        Args:
            original_filename: Original file name
            prefix: Optional prefix for the filename

        Returns:
            str: Unique filename
        """
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        # Generate unique ID
        unique_id = uuid.uuid4().hex[:12]

        # Create timestamp
        timestamp = datetime.now().strftime('%Y%m%d')

        # Build filename
        if prefix:
            filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
        else:
            filename = f"{timestamp}_{unique_id}{ext}"

        return filename

    @staticmethod
    def validate_file(file, allowed_extensions=None, max_size=None):
        """
        Validate uploaded file.

        Args:
            file: Uploaded file object
            allowed_extensions: List of allowed extensions (default: all)
            max_size: Maximum file size in bytes

        Returns:
            tuple: (is_valid, error_message)
        """
        if not allowed_extensions:
            allowed_extensions = FileUploadService.ALLOWED_ALL

        if not max_size:
            max_size = FileUploadService.MAX_DOCUMENT_SIZE

        # Check file size
        if hasattr(file, 'size') and file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {max_mb}MB"

        # Check file extension
        _, ext = os.path.splitext(file.name)
        ext = ext.lower()

        if ext not in allowed_extensions:
            return False, f"File type {ext} not allowed. Allowed types: {', '.join(allowed_extensions)}"

        return True, None

    @staticmethod
    def upload_file(file, folder, filename=None, allowed_extensions=None, max_size=None):
        """
        Upload file to storage (S3 or local).

        Args:
            file: Uploaded file object
            folder: Folder path (e.g., 'violations', 'arc-documents')
            filename: Optional custom filename (will generate if not provided)
            allowed_extensions: List of allowed extensions
            max_size: Maximum file size

        Returns:
            tuple: (success, file_url_or_error_message, file_size)
        """
        # Validate file
        is_valid, error = FileUploadService.validate_file(
            file,
            allowed_extensions=allowed_extensions,
            max_size=max_size
        )

        if not is_valid:
            return False, error, 0

        # Generate filename if not provided
        if not filename:
            filename = FileUploadService.generate_filename(file.name, prefix=folder)

        # Build full path
        file_path = os.path.join(folder, filename)

        # Get file size
        file_size = file.size if hasattr(file, 'size') else 0

        # Save file using Django's storage backend
        # This will use S3 if configured, otherwise local storage
        try:
            # Read file content
            if hasattr(file, 'read'):
                file_content = file.read()
            else:
                file_content = file

            # Save to storage
            saved_path = default_storage.save(file_path, ContentFile(file_content))

            # Get URL
            if hasattr(default_storage, 'url'):
                file_url = default_storage.url(saved_path)
            else:
                # For local storage, construct URL
                file_url = f"/media/{saved_path}"

            return True, file_url, file_size

        except Exception as e:
            return False, f"Upload failed: {str(e)}", 0

    @staticmethod
    def delete_file(file_url):
        """
        Delete file from storage.

        Args:
            file_url: File URL or path

        Returns:
            bool: Success status
        """
        try:
            # Extract path from URL
            if file_url.startswith('http'):
                # S3 URL - extract key
                path = file_url.split('/')[-2:]  # Get last two parts
                path = '/'.join(path)
            else:
                # Local path
                path = file_url.replace('/media/', '')

            # Delete file
            if default_storage.exists(path):
                default_storage.delete(path)
                return True

            return False

        except Exception:
            return False

    # ===========================
    # Violation Photo Uploads
    # ===========================

    @staticmethod
    def upload_violation_photo(file, violation_id):
        """
        Upload a violation photo.

        Args:
            file: Uploaded file object
            violation_id: Violation ID (for folder organization)

        Returns:
            tuple: (success, file_url_or_error, file_size)
        """
        folder = f"violations/{violation_id}/photos"

        return FileUploadService.upload_file(
            file=file,
            folder=folder,
            allowed_extensions=FileUploadService.ALLOWED_IMAGES,
            max_size=FileUploadService.MAX_IMAGE_SIZE
        )

    # ===========================
    # ARC Document Uploads
    # ===========================

    @staticmethod
    def upload_arc_document(file, arc_request_id, document_type='other'):
        """
        Upload an ARC request document.

        Args:
            file: Uploaded file object
            arc_request_id: ARC Request ID
            document_type: Type of document (plans, specs, photo, contract, other)

        Returns:
            tuple: (success, file_url_or_error, file_size)
        """
        folder = f"arc-requests/{arc_request_id}/{document_type}"

        # Photos only allow images, others allow all
        if document_type == 'photo':
            allowed = FileUploadService.ALLOWED_IMAGES
            max_size = FileUploadService.MAX_IMAGE_SIZE
        else:
            allowed = FileUploadService.ALLOWED_ALL
            max_size = FileUploadService.MAX_DOCUMENT_SIZE

        return FileUploadService.upload_file(
            file=file,
            folder=folder,
            allowed_extensions=allowed,
            max_size=max_size
        )

    # ===========================
    # Work Order Attachment Uploads
    # ===========================

    @staticmethod
    def upload_work_order_attachment(file, work_order_id):
        """
        Upload a work order attachment.

        Args:
            file: Uploaded file object
            work_order_id: Work Order ID

        Returns:
            tuple: (success, file_url_or_error, file_size)
        """
        folder = f"work-orders/{work_order_id}/attachments"

        return FileUploadService.upload_file(
            file=file,
            folder=folder,
            allowed_extensions=FileUploadService.ALLOWED_ALL,
            max_size=FileUploadService.MAX_DOCUMENT_SIZE
        )

    # ===========================
    # Helper Methods
    # ===========================

    @staticmethod
    def get_file_info(file_url):
        """
        Get information about an uploaded file.

        Args:
            file_url: File URL

        Returns:
            dict: File information (exists, size, content_type)
        """
        try:
            # Extract path
            if file_url.startswith('http'):
                path = file_url.split('/')[-2:]
                path = '/'.join(path)
            else:
                path = file_url.replace('/media/', '')

            # Check if exists
            exists = default_storage.exists(path)

            if exists:
                size = default_storage.size(path)

                # Get content type
                content_type, _ = mimetypes.guess_type(path)

                return {
                    'exists': True,
                    'size': size,
                    'content_type': content_type,
                    'path': path,
                }
            else:
                return {
                    'exists': False,
                    'size': 0,
                    'content_type': None,
                    'path': path,
                }

        except Exception as e:
            return {
                'exists': False,
                'size': 0,
                'content_type': None,
                'error': str(e),
            }

    @staticmethod
    def get_storage_stats(tenant_id=None):
        """
        Get storage usage statistics.

        Args:
            tenant_id: Optional tenant ID to filter by

        Returns:
            dict: Storage statistics
        """
        # This is a placeholder - would need to implement tenant-specific
        # storage tracking in production

        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'by_category': {
                'violations': {'count': 0, 'size_bytes': 0},
                'arc-requests': {'count': 0, 'size_bytes': 0},
                'work-orders': {'count': 0, 'size_bytes': 0},
            }
        }

        # In production, would query file records from database
        # and calculate actual usage

        return stats
