"""
S3 Utility Functions for Pre-Signed URLs
Generates secure, temporary URLs for S3 objects without requiring public bucket access
"""
from django.conf import settings
from datetime import timedelta
import boto3
from botocore.config import Config

def get_s3_client():
    """Get configured S3 client"""
    if not settings.USE_S3:
        return None
    
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version='s3v4')
    )

def generate_presigned_url(file_field, expiration=None):
    """
    Generate a pre-signed URL for an S3 object
    
    Args:
        file_field: Django FileField or ImageField object
        expiration: URL expiration time in seconds (default: S3_PRESIGNED_URL_EXPIRATION)
    
    Returns:
        Pre-signed URL string, or None if not S3 or file doesn't exist
    """
    if not settings.USE_S3 or not file_field:
        return None
    
    # Check if file is stored in S3 (URL starts with http/https)
    file_url = file_field.url
    if not (file_url.startswith('http://') or file_url.startswith('https://')):
        # Local storage, return as-is (will be handled by serializer)
        return None
    
    # Extract S3 key from file field
    # Django-storages stores the S3 key in file_field.name (most reliable)
    try:
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Get the key from the file field's name attribute (most reliable method)
        if hasattr(file_field, 'name') and file_field.name:
            key = file_field.name
        else:
            # Fallback: Extract from URL
            # URL format: https://bucket.s3.region.amazonaws.com/path/to/file
            if f'{bucket_name}.s3' in file_url:
                # Extract key from URL
                key = file_url.split(f'{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/')[-1]
                # Remove query parameters if any
                key = key.split('?')[0]
            elif f'/{bucket_name}/' in file_url:
                # Try alternative URL format
                key = file_url.split(f'/{bucket_name}/')[-1].split('?')[0]
            else:
                # If we can't extract key, return original URL as fallback
                return file_url
        
        # Get S3 client
        s3_client = get_s3_client()
        if not s3_client:
            return file_url  # Fallback to original URL
        
        # Set expiration
        if expiration is None:
            expiration = getattr(settings, 'S3_PRESIGNED_URL_EXPIRATION', 3600)
        
        # Generate pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': key
            },
            ExpiresIn=expiration
        )
        
        return presigned_url
    
    except Exception as e:
        # If pre-signed URL generation fails, return original URL as fallback
        # This ensures the system still works even if there's an S3 configuration issue
        return file_url

