# Storage Configuration Guide

## Overview

The system supports **two storage backends** for item images:
1. **Local Storage** (Default) - Images stored on server filesystem
2. **AWS S3** (Optional) - Images stored in S3 bucket

The image **path is always stored in the database** (Item.image field), regardless of storage backend.

---

## Current Setup: Local Storage (Default)

**How it works:**
- Images stored in: `media/items/{item_id}/{filename}`
- Path stored in database: `items/{item_id}/{filename}`
- Served via: `http://localhost:8000/media/items/{item_id}/{filename}`
- **No configuration needed** - works out of the box

---

## Switching to AWS S3

### Step 1: Install django-storages

```bash
pip install django-storages boto3
```

### Step 2: Add to settings.py

```python
# In INSTALLED_APPS, add:
INSTALLED_APPS = [
    # ... existing apps ...
    'storages',  # Add this
]

# Add AWS S3 configuration (when ready to use S3):
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_S3:
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    
    # Use S3 for media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Local storage (default)
    MEDIA_URL = 'media/'
    MEDIA_ROOT = BASE_DIR / 'media'
```

### Step 3: Environment Variables (.env file)

```bash
# Toggle between local and S3
USE_S3=True

# AWS Credentials (only needed if USE_S3=True)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

### Step 4: Create S3 Bucket

1. Go to AWS S3 Console
2. Create a new bucket
3. Set bucket permissions (public read for images)
4. Get your AWS credentials (Access Key ID and Secret)

---

## How It Works

### Database Storage (Same for Both)

The `Item.image` field stores the **path** to the image:
- **Local:** `items/{item_id}/{filename}.jpg`
- **S3:** `items/{item_id}/{filename}.jpg` (same path format!)

### Image URLs

The serializer automatically generates full URLs:
- **Local:** `http://localhost:8000/media/items/{id}/{filename}`
- **S3:** `https://your-bucket.s3.amazonaws.com/items/{id}/{filename}`

### Toggle Storage

Just change `USE_S3` in `.env` file:
- `USE_S3=False` → Local storage
- `USE_S3=True` → S3 storage

**No code changes needed!** The same code works for both.

---

## Benefits

✅ **Same database schema** - path stored the same way  
✅ **Same API** - no changes to endpoints  
✅ **Easy toggle** - just change one setting  
✅ **No migration needed** - paths work for both  
✅ **Test locally, deploy to S3** - perfect workflow  

---

## Testing

1. **Test locally first** (USE_S3=False)
2. **Create items with images** - verify paths stored correctly
3. **Switch to S3** (USE_S3=True) - configure AWS credentials
4. **Create new items** - images go to S3, paths stored same way
5. **Old items still work** - paths are compatible

---

## Migration Path

**Existing local images:**
- Keep using local storage for existing images
- New images can use S3
- Or migrate all images to S3 later (optional script)

**No breaking changes** - system handles both!

