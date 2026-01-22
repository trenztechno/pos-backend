# Pre-Signed URLs for S3 Images

## Overview

The system now uses **pre-signed URLs** for S3 images by default. This is more secure than public bucket access and doesn't require configuring bucket policies.

## How It Works

1. **When API returns image URLs**, it automatically generates temporary pre-signed URLs
2. **URLs are valid for a set time** (default: 1 hour)
3. **Mobile app can cache and use** these URLs
4. **URLs automatically expire**, preventing unauthorized access

## Benefits

✅ **No public bucket needed** - Bucket can remain private  
✅ **Temporary access** - URLs expire after set time  
✅ **More secure** - Only authenticated API users get image URLs  
✅ **No 403 errors** - Works without bucket policy changes  
✅ **No bucket configuration** - Just works out of the box

## Configuration

### Enable Pre-Signed URLs (Default)

Add to `.env` file:
```bash
# Pre-signed URL settings (enabled by default)
USE_S3_PRESIGNED_URLS=True
S3_PRESIGNED_URL_EXPIRATION=3600  # 1 hour in seconds (default)
```

### Disable Pre-Signed URLs (Use Public Bucket)

If you prefer public bucket access:
```bash
USE_S3_PRESIGNED_URLS=False
```

Then configure bucket policy for public read (see troubleshooting section in `STORAGE_CONFIGURATION.md`)

## URL Expiration

- **Default:** 1 hour (3600 seconds)
- **Custom:** Set `S3_PRESIGNED_URL_EXPIRATION` in `.env`
- **Mobile app:** Should cache URLs and refresh when expired

## Example URLs

**Pre-signed URL (temporary, secure):**
```
https://bucket.s3.region.amazonaws.com/path/to/image.jpg?X-Amz-Algorithm=...&X-Amz-Expires=3600&...
```

**Public URL (permanent, requires bucket policy):**
```
https://bucket.s3.region.amazonaws.com/path/to/image.jpg
```

## Mobile App Implementation

1. **Cache URLs** - Store pre-signed URLs locally
2. **Refresh on expiration** - Request new URLs when old ones expire
3. **Handle gracefully** - If URL expires, request new one from API

## Testing

After enabling pre-signed URLs:
1. Run `python test_mobile_dev_setup.py`
2. All images should return `200 OK` (no 403 errors)
3. URLs will have query parameters (signature)

## Troubleshooting

### URLs still return 403
- Check `USE_S3_PRESIGNED_URLS=True` in `.env`
- Verify AWS credentials are correct
- Check IAM user has `s3:GetObject` permission

### URLs expire too quickly
- Increase `S3_PRESIGNED_URL_EXPIRATION` (max: 604800 = 7 days)
- Mobile app should refresh URLs before expiration

### Pre-signed URL generation fails
- System falls back to original URL
- Check AWS credentials and permissions
- Verify bucket name and region are correct


