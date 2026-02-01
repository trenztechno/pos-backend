# Authentication Flow & Backward Compatibility

## Overview

This document explains the authentication flow and ensures backward compatibility with existing vendors.

---

## Login Flow (No GST Required)

**Endpoint:** `POST /auth/login`

**Required Fields:**
- `username` (required)
- `password` (required)

**GST Number:** NOT required for login

**Why:** 
- Existing vendors created before phone field was added may not have phone numbers
- Login should work for all approved vendors regardless of phone status
- Phone number is only needed for password reset, not for login

**Flow:**
1. User provides username and password
2. System authenticates credentials
3. System resolves vendor:
   - If user is **vendor owner** → `user.vendor_profile`
   - If user is **vendor staff** → `VendorUser` link (`vendor_memberships`)
4. If user is a vendor (owner or staff), system checks:
   - Vendor is approved
   - User account is active
5. Returns token if valid
6. **Does NOT check GST number** - backward compatible
7. **Returns vendor data** (for both owner and staff users)

**Login Response (for vendors):**
```json
{
  "token": "...",
  "user_id": 1,
  "username": "vendor1",
  "message": "Login successful",
  "vendor": {
    "id": "...",
    "business_name": "ABC Store",
    "gst_no": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "http://localhost:8000/media/vendors/.../logo.png",
    "footer_note": "Thank you for visiting!"
  }
}
```

**Note:** The login response includes:
- `fssai_license`: FSSAI License Number (for bill printing)
- `logo_url`: URL to vendor logo (for bill printing)
- `footer_note`: Custom footer note (for bill printing)

**Note:** Billing mode (GST/Non-GST) is set per bill, not per vendor. Each bill can be either GST or Non-GST.

---

## Registration Flow (GST Optional)

**Endpoint:** `POST /auth/register`

**Required Fields:**
- `username` (required)
- `email` (required)
- `password` (required)
- `password_confirm` (required)
- `business_name` (required)
- `phone` (required)
- `address` (required)

**Optional Fields:**
- `gst_no` (optional) - GST number (GSTIN). Can be omitted during registration and added later via profile update
- `fssai_license` (optional) - FSSAI License Number for bill printing. Can be added later via profile update

**Note:** Billing mode (GST/Non-GST) is set per bill when creating bills, not during registration.

**Why Phone is Required:**
- New vendors need phone for password reset functionality
- Ensures all new vendors can use password reset feature
- Phone number is used for verification during password reset

**GST Number:**
- Can be provided during registration (must be unique if provided)
- Can be omitted and added later via `PATCH /auth/profile`
- Can be updated or cleared via profile update endpoint

---

## Password Reset Flow (Phone Required, Owner Only)

**Step 1:** `POST /auth/forgot-password`
- Requires: `username` (vendor owner) + `phone`
- Verifies both match the **vendor owner** account (must have phone)
- Returns confirmation if valid

**Step 2:** `POST /auth/reset-password`
- Requires: `username` (vendor owner) + `phone` + `new_password` + `new_password_confirm`
- Resets password and invalidates all tokens for the owner

**Notes:** 
- Vendors without phone number cannot use password reset.
- Password reset is **only** for the vendor owner account.
- Staff users never go through this flow; their passwords are reset by the owner via a protected API.

---

## Backward Compatibility

### Existing Vendors (Created Before Phone Field)

✅ **Can Login:** Yes - login doesn't require phone
✅ **Can Use API:** Yes - all API endpoints work
❌ **Can Reset Password:** No - need phone number first

### New Vendors (Created After Phone Field)

✅ **Can Login:** Yes
✅ **Can Use API:** Yes
✅ **Can Reset Password:** Yes - have phone number

### Default Users (Admin, SalesRep)

✅ **Can Login:** Yes - they're not vendors
✅ **Can Use Admin/Sales Rep Interface:** Yes
❌ **Cannot Use Password Reset:** Password reset is vendor-owner-only

### Vendor Staff Users (Created by Owner)

✅ **Can Login:** Yes - via `POST /auth/login`  
✅ **Can Use API:** Yes - all billing endpoints (items, bills, dashboard, etc.)  
❌ **Cannot Use Password Reset:** Must ask vendor owner to reset password via API  
❌ **Cannot Access Django Admin:** `is_staff=False`, `is_superuser=False`

---

## Adding/Updating GST Number

Vendors can add or update their GST number at any time:

1. **Option 1: Via Profile Update API**
   - Use `PATCH /auth/profile` with `gst_no` field
   - Can set, update, or clear (set to empty string) GST number
   - Must be unique if provided

2. **Option 2: Via Admin Panel**
   - Go to Django Admin
   - Edit vendor → Add/Update GST number → Save

3. **Option 3: Via Sales Rep Interface**
   - Sales rep can view vendor details
   - Can update GST number if needed

---

## Workflow Protection

### Login Workflow (Protected)
- ✅ Does NOT check GST number
- ✅ Works for vendors with or without GST
- ✅ Only checks: username, password, approval status
- ✅ Backward compatible with existing vendors

### Registration Workflow (Protected)
- ✅ GST number is optional (can be omitted)
- ✅ Validates GST is unique if provided
- ✅ Creates vendor with or without GST number
- ✅ GST can be added/updated later via profile endpoint
- ✅ Ensures password reset will work (requires phone, not GST)

### Password Reset Workflow (Protected)
- ✅ Requires phone number (security feature)
- ✅ Validates username + phone match
- ✅ Only works for **vendor owner** accounts with phone
- ✅ Clear error if vendor doesn't have phone

---

## Testing Backward Compatibility

### Test 1: Existing Vendor Without GST
```bash
# Should work - login doesn't require GST
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"old_vendor","password":"password123"}'
```

### Test 2: New Vendor With GST
```bash
# Should work - has GST
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"new_vendor","password":"password123"}'
```

### Test 3: Password Reset Without Phone
```bash
# Should fail with clear error
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"username":"old_vendor","phone":"+911234567890"}'
# Expected: "Your vendor account does not have a phone number..."
```

---

## Summary

✅ **Login:** Works for all vendors (with or without GST/phone)  
✅ **Registration:** Requires phone, GST is optional (can be added later)  
✅ **Password Reset:** Requires phone number (security feature, not GST)  
✅ **GST Management:** Can be set, updated, or cleared via profile endpoint  
✅ **Backward Compatible:** Existing vendors can still login  
✅ **Protected Workflow:** No breaking changes to login flow


