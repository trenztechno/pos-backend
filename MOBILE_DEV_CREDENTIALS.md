# Mobile Developer Setup & Credentials

**📱 Everything you need to start developing the mobile app!**

---

## 🔐 Login Credentials

### Vendor Account (Approved & Ready to Use)

```
Username: mobiledev
Password: mobile123
Token: 3c9c593d714fc7318a41acd2d9ad128452aef877
```

**Note:** Token is auto-generated. You can also login via API to get a fresh token.

---

## 🏢 Vendor Information

```
Business Name: Mobile Dev Restaurant
GST Number: 29MOBILE1234D1E5
FSSAI License: 12345678901234
Address: 123 Developer Street, Tech City, State - 560001
Footer Note: Thank you for visiting! We appreciate your business.
```

**Logo:** ✅ Available (uploaded to S3)

---

## 📦 Data Available

### Categories (8 Total)

**Global Categories (Available to all vendors):**
- Beverage
- Snacks

**Vendor-Specific Categories:**
- Breakfast
- Lunch
- Dinner
- Snacks
- Beverage
- Desserts

### Items (15 Total - All with Images!)

All items have:
- ✅ Real food images (downloaded from internet, stored in S3)
- ✅ Complete GST fields (mrp_price, price_type, gst_percentage, veg_nonveg)
- ✅ Stock quantities
- ✅ Categories assigned

**Sample Items:**
1. Masala Dosa (₹70.00, 5% GST, veg) - Breakfast
2. Idli Sambar (₹45.00, 5% GST, veg) - Breakfast
3. Egg Omelette (₹55.00, 5% GST, nonveg) - Breakfast
4. Biryani (₹180.00, 18% GST, nonveg) - Lunch
5. Veg Thali (₹140.00, 18% GST, veg) - Lunch
6. Chicken Curry (₹200.00, 18% GST, nonveg) - Lunch, Dinner
7. Butter Naan (₹35.00, 5% GST, veg) - Dinner
8. Paneer Tikka (₹160.00, 18% GST, veg) - Dinner
9. Samosa (₹25.00, 5% GST, veg) - Snacks
10. Chicken Wings (₹140.00, 18% GST, nonveg) - Snacks
11. Coca Cola (₹30.00, 18% GST, veg) - Beverage
12. Fresh Lime Soda (₹45.00, 5% GST, veg) - Beverage
13. Coffee (₹35.00, 5% GST, veg) - Beverage
14. Ice Cream (₹70.00, 18% GST, veg) - Desserts
15. Gulab Jamun (₹60.00, 5% GST, veg) - Desserts

### Sample Bills (2 Total)

1. **GST Bill (INV-2024-001)**
   - Total: ₹352.50
   - Includes CGST, SGST breakdown
   - Multiple items

2. **Non-GST Bill (INV-2024-002)**
   - Total: ₹320.00
   - Simple total (no tax)

---

## 🔗 API Endpoints

### Base URL
```
http://localhost:8000  (development)
https://your-server.com  (production)
```

### Authentication
All endpoints (except `/health/`, `/auth/login`, `/auth/register`) require:
```
Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877
```

### Key Endpoints

#### 1. Login (Get Fresh Token)
```http
POST /auth/login
Content-Type: application/json

{
  "username": "mobiledev",
  "password": "mobile123"
}
```

**Response:**
```json
{
  "token": "3c9c593d714fc7318a41acd2d9ad128452aef877",
  "user_id": 1,
  "username": "mobiledev",
  "vendor": {
    "id": "...",
    "business_name": "Mobile Dev Restaurant",
    "gst_no": "29MOBILE1234D1E5",
    "fssai_license": "12345678901234",
    "logo_url": "https://trenz-pos-storage.s3.ap-south-1.amazonaws.com/vendors/.../logo.jpg",
    "footer_note": "Thank you for visiting! We appreciate your business."
  }
}
```

#### 2. Get All Items
```http
GET /items/
Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877
```

**Response includes:**
- All 15 items
- `image_url` field with S3 URLs
- Complete GST fields (mrp_price, price_type, gst_percentage, veg_nonveg)
- Categories
- Stock quantities

#### 3. Get All Categories
```http
GET /items/categories/
Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877
```

#### 4. Get Item Details
```http
GET /items/{item_id}/
Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877
```

#### 5. Create Bill (Sales Backup)
```http
POST /backup/sync
Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877
Content-Type: application/json

{
  "device_id": "your-device-id",
  "bill_data": {
    "invoice_number": "INV-2024-003",
    "bill_id": "uuid-here",
    "billing_mode": "gst",
    "restaurant_name": "Mobile Dev Restaurant",
    "address": "123 Developer Street, Tech City, State - 560001",
    "gstin": "29MOBILE1234D1E5",
    "fssai_license": "12345678901234",
    "bill_number": "BN-2024-003",
    "bill_date": "2024-01-21",
    "items": [
      {
        "id": "item-uuid",
        "name": "Biryani",
        "price": 180.00,
        "mrp_price": 180.00,
        "price_type": "exclusive",
        "gst_percentage": 18.00,
        "quantity": 2,
        "subtotal": 360.00,
        "item_gst": 64.80
      }
    ],
    "subtotal": 360.00,
    "cgst": 32.40,
    "sgst": 32.40,
    "igst": 0.00,
    "total_tax": 64.80,
    "total": 424.80,
    "footer_note": "Thank you for visiting! We appreciate your business.",
    "timestamp": "2024-01-21T10:00:00Z"
  }
}
```

---

## 📋 Item Data Structure

Each item includes:

```json
{
  "id": "uuid",
  "name": "Masala Dosa",
  "description": "Crispy dosa with spicy potato filling",
  "price": "60.00",
  "mrp_price": "70.00",
  "price_type": "exclusive",
  "gst_percentage": "5.00",
  "veg_nonveg": "veg",
  "additional_discount": "0.00",
  "stock_quantity": 50,
  "sku": "DOSA-001",
  "is_active": true,
  "image_url": "https://trenz-pos-storage.s3.ap-south-1.amazonaws.com/items/.../masala_dosa.jpg",
  "categories_list": [
    {"id": "uuid", "name": "Breakfast"}
  ]
}
```

---

## 🧪 Testing Checklist

### ✅ What You Can Test

1. **Authentication**
   - [ ] Login with `mobiledev` / `mobile123`
   - [ ] Get token from login response
   - [ ] Use token in API requests

2. **Items**
   - [ ] Fetch all items (15 items)
   - [ ] Check `image_url` fields (all should have S3 URLs)
   - [ ] Filter by category
   - [ ] Search items
   - [ ] View item details

3. **Categories**
   - [ ] Fetch all categories (8 categories)
   - [ ] Filter items by category

4. **Bills**
   - [ ] Create GST bill
   - [ ] Create Non-GST bill
   - [ ] Verify bill structure matches requirements

5. **Images**
   - [ ] Load item images from S3 URLs
   - [ ] Load vendor logo from login response
   - [ ] Test image caching

---

## 🎯 Key Features to Implement

### 1. GST Billing
- Items have `gst_percentage` (0%, 5%, 18%)
- Items have `price_type` (exclusive/inclusive)
- Calculate CGST/SGST for intra-state
- Calculate IGST for inter-state

### 2. Non-GST Billing
- No tax calculations
- Simple subtotal = total

### 3. Bill Format
- Invoice number (auto-generated, sequential)
- Restaurant name, address, GSTIN, FSSAI
- Bill number & date
- Item-wise amounts
- GST breakup (for GST bills)
- Footer note

### 4. Image Handling
- All images are on S3
- Use `image_url` from API
- Cache images locally for offline use

---

## 📱 Quick Start

### 1. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mobiledev",
    "password": "mobile123"
  }'
```

### 2. Get Items
```bash
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877"
```

### 3. Get Categories
```bash
curl -X GET http://localhost:8000/items/categories/ \
  -H "Authorization: Token 3c9c593d714fc7318a41acd2d9ad128452aef877"
```

---

## 📚 Documentation

- **Complete API Docs:** `API_DOCUMENTATION.md`
- **Mobile App Guide:** `MOBILE_APP_GUIDE.md`
- **Storage Config:** `STORAGE_CONFIGURATION.md`

---

## ⚠️ Important Notes

1. **Token Expiry:** Tokens don't expire, but you can logout to invalidate
2. **Offline-First:** Save bills locally first, sync later
3. **Image URLs:** All images are on S3, accessible via `image_url` field
4. **GST Calculation:** Handle in mobile app (exclusive vs inclusive pricing)
5. **Invoice Numbers:** Generate sequentially on mobile, sync with server

---

## 🆘 Support

If you need to:
- **Reset data:** Run `python populate_mobile_dev_data.py` again
- **Get fresh token:** Login again via API
- **Check server:** `curl http://localhost:8000/health/`

---

**Happy Coding! 🚀**

