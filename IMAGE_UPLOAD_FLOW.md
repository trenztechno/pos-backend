# Image Upload Flow - How It Works

## When Mobile Creates/Updates Item with Image

### 1. Mobile Sends Request
```
POST /items/
Content-Type: multipart/form-data

{
  "name": "Pizza",
  "mrp_price": "100.00",
  "image": <file data>
}
```

### 2. Server Receives & Processes
- Django REST Framework's `ItemSerializer` receives the image file
- When `serializer.save()` is called:
  - Django automatically uploads image to S3 (if `USE_S3=True`)
  - OR saves to local storage (if `USE_S3=False`)
  - Stores the S3 path in `item.image` field

### 3. Server Returns Response
- `ItemSerializer(item, context={'request': request}).data` is returned
- `get_image_url()` method is automatically called
- If `USE_S3_PRESIGNED_URLS=True`:
  - Generates pre-signed URL for the uploaded image
  - Returns pre-signed URL in `image_url` field
- Mobile receives response with pre-signed URL ready to use

## Example Response After Creation

```json
{
  "id": "uuid-here",
  "name": "Pizza",
  "mrp_price": "100.00",
  "image_url": "https://bucket.s3.region.amazonaws.com/items/uuid/image.jpg?X-Amz-Algorithm=...&X-Amz-Expires=3600&..."
}
```

## Current Implementation ✅

The system already works correctly:
1. ✅ Image uploads to S3 during creation/update
2. ✅ Response includes pre-signed URL via `get_image_url()`
3. ✅ Mobile can immediately use the URL

## Code Flow

```
POST /items/ (with image)
  ↓
ItemSerializer(data=request.data)
  ↓
serializer.save() → Uploads to S3, saves path to DB
  ↓
ItemSerializer(item).data
  ↓
get_image_url() → Generates pre-signed URL
  ↓
Response with image_url (pre-signed)
```

## Verification

The `get_image_url()` method is called automatically by DRF when serializing, so:
- ✅ GET /items/ → Pre-signed URLs
- ✅ POST /items/ → Pre-signed URLs (after upload)
- ✅ PATCH /items/<id>/ → Pre-signed URLs (after upload)

All responses use the same `get_image_url()` method, ensuring consistency!
