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
    try:
        file_url = file_field.url
    except:
        return None
    
    if not (file_url.startswith('http://') or file_url.startswith('https://')):
        # Local storage, return as-is (will be handled by serializer)
        return None
    
    # Extract S3 key from file field
    # Django-storages stores the S3 key in file_field.name (most reliable)
    try:
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Get the key from the file field's name attribute (most reliable method)
        # For django-storages, the file_field.name contains the S3 key
        if hasattr(file_field, 'name') and file_field.name:
            key = file_field.name
        else:
            # Fallback: Extract from URL
            # URL format: https://bucket.s3.region.amazonaws.com/path/to/file
            # Or: https://bucket.s3.amazonaws.com/path/to/file
            if f'{bucket_name}.s3' in file_url:
                # Try different URL patterns
                patterns = [
                    f'{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/',
                    f'{bucket_name}.s3.amazonaws.com/',
                    f's3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{bucket_name}/',
                    f's3.amazonaws.com/{bucket_name}/',
                ]
                key = None
                for pattern in patterns:
                    if pattern in file_url:
                        key = file_url.split(pattern)[-1].split('?')[0]
                        break
                
                if not key:
                    # Last resort: try to extract after bucket name
                    if f'/{bucket_name}/' in file_url:
                        key = file_url.split(f'/{bucket_name}/')[-1].split('?')[0]
                    else:
                        # If we can't extract key, log and return None
                        import logging
                        logger = logging.getLogger('api')
                        logger.warning(f"Could not extract S3 key from URL: {file_url}")
                        return None
            elif f'/{bucket_name}/' in file_url:
                # Try alternative URL format
                key = file_url.split(f'/{bucket_name}/')[-1].split('?')[0]
            else:
                # If we can't extract key, log and return None
                import logging
                logger = logging.getLogger('api')
                logger.warning(f"Could not extract S3 key from URL: {file_url}")
                return None
        
        # Validate key is not empty
        if not key or not key.strip():
            import logging
            logger = logging.getLogger('api')
            logger.error(f"Empty S3 key extracted. URL: {file_url}, file_field.name: {getattr(file_field, 'name', 'NO NAME')}")
            return None
        
        # Get S3 client
        s3_client = get_s3_client()
        if not s3_client:
            import logging
            logger = logging.getLogger('api')
            logger.error("S3 client is None - check AWS credentials")
            return None
        
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
        # Log the error for debugging
        import logging
        logger = logging.getLogger('api')
        logger.error(f"Failed to generate pre-signed URL: {str(e)}")
        logger.error(f"File field name: {getattr(file_field, 'name', 'NO NAME')}, URL: {file_url}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return None so serializer can fall back to direct URL handling
        # This allows the system to work but we know pre-signed URLs failed
        return None

