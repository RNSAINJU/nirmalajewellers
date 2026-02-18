"""
File upload validation utilities for security.

This module provides validators for secure file uploads, checking:
- File size limits
- File extensions
- MIME types
- Content validation
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_excel_file(file, max_mb=10):
    """
    Comprehensive validator for Excel file uploads.
    
    Checks:
    - File size (default max 10MB)
    - File extension (.xlsx, .xls)
    - MIME type
    
    Args:
        file: Django UploadedFile object
        max_mb: Maximum allowed file size in MB
        
    Raises:
        ValidationError: If file is invalid
        
    Usage:
        from common.file_validators import validate_excel_file
        
        try:
            validate_excel_file(request.FILES['file'])
        except ValidationError as e:
            # Handle error
    """
    # Max size check
    max_bytes = max_mb * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            _("File too large. Maximum size is %(max)sMB." % {'max': max_mb}),
            code='file_too_large'
        )
    
    # File extension check
    allowed_extensions = ['.xlsx', '.xls']
    if '.' not in file.name:
        raise ValidationError(
            _("File must have an extension (.xlsx or .xls)"),
            code='no_extension'
        )
    
    file_ext = '.' + file.name.rsplit('.', 1)[-1].lower()
    if file_ext not in allowed_extensions:
        raise ValidationError(
            _("Only Excel files (.xlsx, .xls) are allowed. Got: %(ext)s" % {'ext': file_ext}),
            code='invalid_extension'
        )
    
    # MIME type check  
    allowed_mimetypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'application/x-tika-ooxml',
        'application/x-excel',
    ]
    
    if file.content_type and file.content_type not in allowed_mimetypes:
        raise ValidationError(
            _("Invalid file type. Expected Excel file, got: %(mime)s" % {'mime': file.content_type}),
            code='invalid_mimetype'
        )
    
    return True


def validate_file_size(max_mb=10):
    """
    Factory function to create reusable file size validators.
    
    Usage in models:
        from django.db import models
        from common.file_validators import validate_file_size
        
        class MyModel(models.Model):
            file = models.FileField(
                upload_to='uploads/',
                validators=[validate_file_size(5)]  # Max 5MB
            )
    """
    max_bytes = max_mb * 1024 * 1024
    
    def validator(file):
        if file.size > max_bytes:
            raise ValidationError(
                _("File too large. Maximum size is %(max)sMB." % {'max': max_mb}),
                code='file_too_large'
            )
    
    validator.max_mb = max_mb  # Store for reference
    return validator


def validate_file_extension(allowed_extensions):
    """
    Factory function to validate file extensions.
    
    Usage:
        validators=[validate_file_extension(['.pdf', '.doc', '.docx'])]
    """
    # Ensure extensions start with dot
    ext_set = set(
        (ext if ext.startswith('.') else '.' + ext).lower() 
        for ext in allowed_extensions
    )
    
    def validator(file):
        if '.' not in file.name:
            raise ValidationError(
                _("File must have an extension"),
                code='no_extension'
            )
        
        file_ext = '.' + file.name.rsplit('.', 1)[-1].lower()
        if file_ext not in ext_set:
            raise ValidationError(
                _("Files with %(ext)s extension are not allowed." % {'ext': file_ext}),
                code='invalid_extension'
            )
    
    validator.allowed_extensions = ext_set
    return validator


def get_safe_filename(filename):
    """
    Generate a safe filename by removing special characters.
    
    Usage:
        safe_name = get_safe_filename(request.FILES['file'].name)
    """
    import re
    # Remove non-alphanumeric characters (except dots and hyphens)
    safe_name = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    # Remove multiple consecutive dots/hyphens
    safe_name = re.sub(r'[._-]{2,}', '_', safe_name)
    return safe_name


# Pre-made validators for common scenarios
EXCEL_FILE_VALIDATOR = validate_file_extension(['.xlsx', '.xls'])
PDF_FILE_VALIDATOR = validate_file_extension(['.pdf'])
IMAGE_FILE_VALIDATOR = validate_file_extension(['.jpg', '.jpeg', '.png', '.gif', '.webp'])
