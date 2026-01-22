# Image Upload vs Pre-Signed URLs - Clarification

## 🔄 The Flow

### 1. UPLOADING Images (You → Server)
```
Mobile App                    Server                    S3
    |                            |                       |
    |--[Image File]------------->|                       |
    |  (multipart/form-data)     |                       |
    |                            |--[Upload Image]----->|
    |                            |                       |
    |<--[Response with pre-signed URL]--|               |
    |                            |                       |
```

**What you do:**
- Send image file directly using `multipart/form-data`
- **NO pre-signed URL needed for upload**
- Just send the file like normal file upload

**Example:**
```javascript
const formData = new FormData();
formData.append('name', 'Pizza');
formData.append('image', imageFile); // ← Just send the file!

fetch('/items/', {
  method: 'POST',
  body: formData
});
```

### 2. DOWNLOADING/VIEWING Images (Server → You)
```
Mobile App                    Server                    S3
    |                            |                       |
    |--[GET /items/]----------->|                       |
    |                            |                       |
    |<--[image_url: pre-signed URL]--|                 |
    |                            |                       |
    |--[GET image using pre-signed URL]---------------->|
    |                            |                       |
    |<--[Image Data]-----------------------------------|
```

**What you get:**
- Server returns `image_url` with a **pre-signed URL**
- Pre-signed URL is for **downloading/viewing** the image
- URL expires after 1 hour

**Example Response:**
```json
{
  "id": "...",
  "name": "Pizza",
  "image_url": "https://bucket.s3.region.amazonaws.com/items/.../image.jpg?X-Amz-Algorithm=...&X-Amz-Expires=3600&..."
  // ↑ This pre-signed URL is for DOWNLOADING, not uploading!
}
```

## ✅ Summary

| Action | What You Do | Pre-Signed URL? |
|--------|-------------|-----------------|
| **Upload Image** | Send file directly (multipart/form-data) | ❌ NO - not needed |
| **Download Image** | Use `image_url` from response | ✅ YES - server gives you pre-signed URL |

## 🎯 Key Points

1. **Upload = Send file directly** (no pre-signed URL)
2. **Download = Use pre-signed URL** (server gives you this)
3. **Pre-signed URLs are for viewing/downloading**, not uploading
4. **Pre-signed URLs expire** after 1 hour - cache images locally!

## 📝 Example: Complete Flow

```javascript
// 1. UPLOAD image (no pre-signed URL needed)
const formData = new FormData();
formData.append('name', 'Pizza');
formData.append('image', imageFile); // ← Just send the file!

const response = await fetch('/items/', {
  method: 'POST',
  body: formData
});

const item = await response.json();

// 2. DOWNLOAD image using pre-signed URL (server gave you this)
const imageUrl = item.image_url; // ← Pre-signed URL for downloading
// Download and cache this image immediately!
await downloadAndCacheImage(imageUrl, item.id);
```

