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
- Existing vendors created before GST field was added don't have GST numbers
- Login should work for all approved vendors regardless of GST status
- GST is only needed for password reset, not for login

**Flow:**
1. User provides username and password
2. System authenticates credentials
3. Checks if vendor is approved and active
4. Returns token if valid
5. **Does NOT check GST number** - backward compatible
6. **Returns vendor data** (for vendors)

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

## Registration Flow (GST Required)

**Endpoint:** `POST /auth/register`

**Required Fields:**
- `username` (required)
- `email` (required)
- `password` (required)
- `password_confirm` (required)
- `business_name` (required)
- `phone` (required)
- `gst_no` (required) ⭐ **New vendors must have GST**
- `address` (required)
- `fssai_license` (optional) - FSSAI License Number for bill printing

**Note:** Billing mode (GST/Non-GST) is set per bill when creating bills, not during registration.

**Why GST is Required:**
- New vendors need GST for password reset functionality
- Ensures all new vendors can use password reset feature
- GST must be unique across all vendors

---

## Password Reset Flow (GST Required)

**Step 1:** `POST /auth/forgot-password`
- Requires: `username` + `gst_no`
- Verifies both match the same vendor account
- Returns confirmation if valid

**Step 2:** `POST /auth/reset-password`
- Requires: `username` + `gst_no` + `new_password` + `new_password_confirm`
- Resets password and invalidates all tokens

**Note:** 
- Vendors without GST cannot use password reset
- They must contact admin to add GST number first
- This is intentional - ensures security

---

## Backward Compatibility

### Existing Vendors (Created Before GST Field)

✅ **Can Login:** Yes - login doesn't require GST
✅ **Can Use API:** Yes - all API endpoints work
❌ **Can Reset Password:** No - need GST number first

### New Vendors (Created After GST Field)

✅ **Can Login:** Yes
✅ **Can Use API:** Yes
✅ **Can Reset Password:** Yes - have GST number

### Default Users (Admin, SalesRep)

✅ **Can Login:** Yes - they're not vendors
✅ **Can Use Admin/Sales Rep Interface:** Yes
❌ **Cannot Use Password Reset:** Password reset is vendor-only

---

## Migration Path for Existing Vendors

If you have existing vendors without GST numbers:

1. **Option 1: Add GST via Admin Panel**
   - Go to Django Admin
   - Edit vendor → Add GST number → Save
   - Vendor can now use password reset

2. **Option 2: Add GST via Sales Rep Interface**
   - Sales rep can view vendor details
   - Can update GST number if needed

3. **Option 3: Vendor Re-registers**
   - Vendor creates new account with GST
   - Admin approves new account
   - Old account can be deleted

---

## Workflow Protection

### Login Workflow (Protected)
- ✅ Does NOT check GST number
- ✅ Works for vendors with or without GST
- ✅ Only checks: username, password, approval status
- ✅ Backward compatible with existing vendors

### Registration Workflow (Protected)
- ✅ Requires GST number (new requirement)
- ✅ Validates GST is unique
- ✅ Creates vendor with GST number
- ✅ Ensures password reset will work

### Password Reset Workflow (Protected)
- ✅ Requires GST number (security feature)
- ✅ Validates username + GST match
- ✅ Only works for vendors with GST
- ✅ Clear error if vendor doesn't have GST

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

### Test 3: Password Reset Without GST
```bash
# Should fail with clear error
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"username":"old_vendor","gst_no":"ANYGST"}'
# Expected: "Your vendor account does not have a GST number..."
```

---

## Summary

✅ **Login:** Works for all vendors (with or without GST)  
✅ **Registration:** Requires GST (new vendors)  
✅ **Password Reset:** Requires GST (security feature)  
✅ **Backward Compatible:** Existing vendors can still login  
✅ **Protected Workflow:** No breaking changes to login flow


