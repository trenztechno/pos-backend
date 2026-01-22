# Storage Configuration Guide

## Overview

The system supports **two storage backends** for images (Item images and Vendor logos):
1. **Local Storage** (Default) - Images stored on server filesystem
2. **AWS S3** (Recommended for Production) - Images stored in S3 bucket

The image **path is always stored in the database** (Item.image, Vendor.logo fields), regardless of storage backend. The system automatically generates full URLs based on the storage backend.

---

## Current Setup: Local Storage (Default)

**How it works:**
- Images stored in: `media/items/{item_id}/{filename}`
- Path stored in database: `items/{item_id}/{filename}`
- Served via: `http://localhost:8000/media/items/{item_id}/{filename}`
- **No configuration needed** - works out of the box

---

## Switching to AWS S3

### Step 1: Install Dependencies

The dependencies are already in `requirements.txt`. Install them:

```bash
cd /home/rathina-devan/Desktop/personal/freelance/pos
source venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `django-storages==1.14.2`
- `boto3==1.34.0`

### Step 2: Configuration Already Done! ✅

The S3 configuration is already set up in `backend/settings.py`. It automatically:
- Adds `storages` to `INSTALLED_APPS` when `USE_S3=True`
- Configures AWS S3 settings from environment variables
- Validates that AWS credentials are provided
- Switches between local and S3 storage based on `USE_S3` setting

**No code changes needed!** Just configure your `.env` file.

### Step 3: Create S3 Bucket

1. **Go to AWS S3 Console** (https://console.aws.amazon.com/s3/)
2. **Create a new bucket:**
   - Choose a unique bucket name (e.g., `pos-app-images-prod`)
   - Select region (e.g., `us-east-1`, `ap-south-1`)
   - **Block Public Access:** Uncheck "Block all public access" (images need to be publicly readable)
   - Enable versioning (optional, recommended)
3. **Set Bucket Policy** (for public read access):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-bucket-name/*"
       }
     ]
   }
   ```
4. **CORS Configuration** (for web/mobile app access):
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
       "AllowedOrigins": ["*"],
       "ExposeHeaders": []
     }
   ]
   ```

### Step 4: Get AWS Credentials

1. **Go to AWS IAM Console** (https://console.aws.amazon.com/iam/)
2. **Create a new user** (or use existing):
   - User name: `pos-app-s3-user`
   - Access type: **Programmatic access**
3. **Attach Policy:**
   - Attach policy: `AmazonS3FullAccess` (or create custom policy with read/write permissions)
4. **Save Credentials:**
   - **Access Key ID** (copy this)
   - **Secret Access Key** (copy this - shown only once!)

### Step 5: Configure Environment Variables (.env file)

Add these to your `.env` file:

```bash
# Toggle between local and S3 storage
USE_S3=True

# AWS Credentials (required when USE_S3=True)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=pos-app-images-prod
AWS_S3_REGION_NAME=us-east-1
```

**Important:** Never commit your `.env` file to git! It contains sensitive credentials.

---

## How It Works

### Database Storage (Same for Both)

The database stores the **relative path** to the image:
- **Item images:** `items/{item_id}/{filename}.jpg`
- **Vendor logos:** `vendors/{vendor_id}/logo.jpg`

**Same path format for both local and S3!** This means you can switch storage backends without database changes.

### Image URLs (Auto-Generated)

The serializers automatically generate full URLs based on storage backend:

**Item Images:**
- **Local:** `http://localhost:8000/media/items/{item_id}/{filename}.jpg`
- **S3:** `https://your-bucket.s3.us-east-1.amazonaws.com/items/{item_id}/{filename}.jpg`

**Vendor Logos:**
- **Local:** `http://localhost:8000/media/vendors/{vendor_id}/logo.jpg`
- **S3:** `https://your-bucket.s3.us-east-1.amazonaws.com/vendors/{vendor_id}/logo.jpg`

The `image_url` field in API responses automatically uses the correct URL based on your `USE_S3` setting.

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

**Switching from Local to S3:**

1. **Option 1: Gradual Migration (Recommended)**
   - Keep existing local images working
   - New uploads automatically go to S3
   - Old images still accessible from local storage
   - Migrate old images to S3 later (optional)

2. **Option 2: Full Migration**
   - Upload all existing images to S3 manually
   - Update `USE_S3=True` in `.env`
   - All new and existing images use S3

**No breaking changes** - system handles both storage backends seamlessly!

## Pre-Signed URLs (Recommended - More Secure) 🔒

**By default, the system uses pre-signed URLs for S3 images.** This is more secure than public bucket access:

### Benefits:
- ✅ **No public bucket needed** - Bucket can remain private
- ✅ **Temporary access** - URLs expire after set time (default: 1 hour)
- ✅ **More secure** - Only authenticated API users get image URLs
- ✅ **No 403 errors** - Works without bucket policy changes

### Configuration:

Add to `.env` file:
```bash
# Pre-signed URL settings (default: enabled)
USE_S3_PRESIGNED_URLS=True
S3_PRESIGNED_URL_EXPIRATION=3600  # 1 hour in seconds (default)
```

### How It Works:
1. When API returns image URLs, it generates temporary pre-signed URLs
2. URLs are valid for the expiration time (default: 1 hour)
3. Mobile app can cache and use these URLs
4. URLs automatically expire, preventing unauthorized access

### Disable Pre-Signed URLs:
If you want public bucket access instead:
```bash
USE_S3_PRESIGNED_URLS=False
```
Then configure bucket policy for public read (see troubleshooting section below)

**See [PRESIGNED_URLS_GUIDE.md](PRESIGNED_URLS_GUIDE.md) for complete details.**

## Benefits of S3

✅ **Scalability** - Handle millions of images  
✅ **Performance** - CDN-ready, fast global access  
✅ **Reliability** - 99.999999999% durability  
✅ **Cost-effective** - Pay only for what you use  
✅ **No server storage** - Frees up server disk space  
✅ **Easy backup** - Built-in versioning and backup  
✅ **Mobile-friendly** - Direct S3 URLs work great for mobile apps  
✅ **Secure** - Pre-signed URLs by default (no public bucket needed)  

## Troubleshooting

### Error: "django-storages is required for S3 storage"
**Solution:** Run `pip install django-storages boto3`

### Error: "AWS credentials are missing"
**Solution:** Check your `.env` file has all required AWS variables set

### ⚠️ Images return 403 Forbidden (Most Common Issue)
**Problem:** Images are uploaded but return `403 Forbidden` when accessed.

**Solution (If using pre-signed URLs - Recommended):**
- Pre-signed URLs should work without bucket policy changes
- Check `USE_S3_PRESIGNED_URLS=True` in `.env`
- Verify AWS credentials are correct
- Check IAM user has `s3:GetObject` permission
- See [PRESIGNED_URLS_GUIDE.md](PRESIGNED_URLS_GUIDE.md) for troubleshooting

**Solution (If using public bucket - Not Recommended):**
1. **Unblock Public Access:**
   - S3 Console → Your Bucket → Permissions
   - Edit "Block public access" settings
   - **Uncheck all 4 boxes** (or at least uncheck ACL-related ones)
   - Save and confirm

2. **Set Bucket Policy for Public Read:**
   - Go to Permissions → Bucket policy → Edit
   - Add this policy (replace `your-bucket-name`):
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [{
           "Sid": "PublicReadGetObject",
           "Effect": "Allow",
           "Principal": "*",
           "Action": "s3:GetObject",
           "Resource": "arn:aws:s3:::your-bucket-name/*"
       }]
   }
   ```

3. **Verify CORS Configuration:**
   - Go to Permissions → CORS → Edit
   - Add CORS config (see Step 3 in main guide above)

**Note:** We recommend using pre-signed URLs instead of public bucket access for better security.

### Images show 404 after upload
**Solution:**
1. Verify file was uploaded to S3 (check S3 console)
2. Check bucket name matches `AWS_STORAGE_BUCKET_NAME`
3. Verify region matches `AWS_S3_REGION_NAME`

