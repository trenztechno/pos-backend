# Django Admin Panel Guide

**Complete guide for managing vendors, staff users, and security PINs through Django Admin**

---

## 🔐 Admin Login

**URL:** `http://localhost:8000/admin/`

**Default Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

---

## 📋 What You Can Manage

### 1. **Vendors** (`/admin/auth_app/vendor/`)

**List View Shows:**
- **Vendor ID**: Custom vendor ID number (e.g., V001, V002) - auto-generated if not provided
- **UUID**: Database UUID (for reference)
- Business Name
- Username (owner)
- Email
- Phone
- Approval Status (✓ Approved / ⏳ Pending)
- PIN Status (✓ / ✗)
- Staff Users Count
- Created Date

**Actions Available:**
- ✅ **Approve selected vendors** - Bulk approve vendors (sets `is_approved = True`)
- ❌ **Reject selected vendors** - Bulk reject vendors (sets `is_approved = False`)
- ⚠️ **Note:** Approval and Activation are separate. Use Django admin to also control `user.is_active` for activation/deactivation.

**Edit Vendor Page Includes:**

#### Vendor Information
- Owner User (primary account)
- **Vendor ID**: Custom vendor ID number (e.g., V001) - auto-generated if not provided, can be customized for easy identification
- Business Name
- Phone
- Address

#### License & Registration
- GST Number (GSTIN)
- FSSAI License Number

#### Bill Customization
- Logo (with preview)
- Footer Note

#### 🔒 Security PIN Management (NEW!)
- **Security PIN Status** - Shows if PIN is set (read-only)
- **Security PIN** - Enter new PIN to set/change (password field, min 4 digits)
- **Clear Security PIN** - Checkbox to remove PIN

**How to Set/Change PIN:**
1. Open vendor edit page
2. Scroll to "Security PIN Management" section
3. Enter new PIN in "Security PIN" field (min 4 digits)
4. Click "Save"
5. PIN is hashed and stored securely

**How to Clear PIN:**
1. Open vendor edit page
2. Check "Clear Security PIN" checkbox
3. Click "Save"

#### Approval Status
- Is Approved checkbox (controls `is_approved` - approval status)

#### User Active Status
- User → Is Active checkbox (controls `user.is_active` - activation status)
- **Important:** Both approval AND activation must be true for vendor to use the system
- Approval and Activation are separate controls

#### Staff Users (Inline Table)
- **Add/Edit/Delete staff users directly from vendor page!**
- Shows: User, Role (Owner/Staff), Active Status, Created Date, Created By
- Can add new staff users by clicking "Add another Vendor user"
- Can edit existing staff users inline
- Can delete staff users inline

---

### 2. **Vendor Users** (`/admin/auth_app/vendoruser/`)

**Dedicated page for managing all vendor staff users**

**List View Shows:**
- Vendor User ID
- Vendor (business name)
- User (username)
- Role (👑 Owner / 👤 Staff) - Color coded
- Active Status
- Created Date
- Created By

**Filters:**
- By Role (Owner/Staff)
- By Active Status
- By Created Date

**Search:**
- Business Name
- Username
- Email

**Edit Page Includes:**
- Vendor (autocomplete)
- User (autocomplete)
- Is Owner (checkbox)
- Is Active (checkbox)
- Created By (autocomplete)
- Created At (read-only)
- ID (read-only)

**Actions:**
- Create new vendor user
- Edit existing vendor user
- Delete vendor user
- Bulk activate/deactivate

---

## 🎯 Common Admin Tasks

### Task 1: Approve and Activate a New Vendor

**To Approve:**
1. Go to `/admin/auth_app/vendor/`
2. Find vendor in list (pending vendors show ⏳)
3. Click vendor name to edit
4. Check "Is approved" checkbox
5. Click "Save"

**To Activate (Allow Login):**
1. In the same vendor edit page, scroll to "Owner User" section
2. Click the user link to edit the User
3. Check "Active" checkbox
4. Click "Save"
5. Vendor can now login!

**OR use bulk action:**
1. Select vendor(s) from list
2. Choose "✓ Approve selected vendors" from Actions dropdown
3. Click "Go"
4. Then activate the user separately (see above)

**Note:** Approval and Activation are separate. A vendor can be approved but inactive (cannot login), or active but not approved (cannot use API). Both must be true for full access.

---

### Task 2: Set Security PIN for Vendor

1. Go to `/admin/auth_app/vendor/`
2. Click vendor name to edit
3. Scroll to "Security PIN Management" section
4. Enter PIN in "Security PIN" field (e.g., `1234`)
5. Click "Save"
6. PIN is now set! (Status will show ✓ PIN Set)

---

### Task 3: Add Staff User to Vendor

**Method 1: From Vendor Edit Page (Inline)**
1. Go to `/admin/auth_app/vendor/`
2. Click vendor name to edit
3. Scroll to "Vendor users" section at bottom
4. Click "Add another Vendor user"
5. Fill in:
   - User: Select or create user
   - Is owner: Unchecked (for staff)
   - Is active: Checked
6. Click "Save"

**Method 2: From Vendor Users Page**
1. Go to `/admin/auth_app/vendoruser/`
2. Click "Add Vendor user"
3. Fill in:
   - Vendor: Select vendor
   - User: Select or create user
   - Is owner: Unchecked (for staff)
   - Is active: Checked
4. Click "Save"

---

### Task 4: Change Staff User Role

1. Go to `/admin/auth_app/vendoruser/`
2. Click vendor user to edit
3. Check/uncheck "Is owner" to change role
4. Click "Save"

---

### Task 5: Deactivate Staff User

1. Go to `/admin/auth_app/vendoruser/`
2. Click vendor user to edit
3. Uncheck "Is active"
4. Click "Save"

**OR from vendor edit page:**
1. Edit vendor
2. Find staff user in "Vendor users" inline table
3. Uncheck "Is active"
4. Click "Save"

---

### Task 6: View All Staff Users for a Vendor

1. Go to `/admin/auth_app/vendor/`
2. Click vendor name
3. Scroll to "Vendor users" section
4. See all users (owner + staff) in table

**OR:**
1. Go to `/admin/auth_app/vendoruser/`
2. Filter by vendor name in search box

---

## 🔍 Quick Reference

### Vendor Admin List Columns
- **ID** - Vendor UUID
- **Business Name** - Restaurant/store name
- **Username** - Owner username
- **Email** - Owner email
- **Phone** - Contact phone
- **Approval Status** - ✓ Approved / ⏳ Pending
- **PIN** - ✓ (set) / ✗ (not set)
- **Staff Users** - Count of active staff
- **Created At** - Registration date

### Vendor User Admin List Columns
- **ID** - VendorUser UUID
- **Vendor** - Business name
- **User** - Username
- **Role** - 👑 Owner / 👤 Staff
- **Is Active** - Active status
- **Created At** - When user was added
- **Created By** - Who added the user

---

## ⚠️ Important Notes

1. **Security PIN:**
   - PIN is hashed (never stored in plain text)
   - Minimum 4 characters
   - Required for vendor owner to manage staff via API
   - Can be set/changed/cleared from admin

2. **Owner vs Staff:**
   - **Owner** (`is_owner=True`): Can manage staff users, has full access
   - **Staff** (`is_owner=False`): Can do billing, cannot manage users

3. **User Creation:**
   - When adding staff user, you can select existing User or create new one
   - Use autocomplete to search for users
   - New users must be created in User admin first if they don't exist

4. **Bulk Actions:**
   - Select multiple vendors → Approve/Reject all at once
   - Select multiple vendor users → Activate/Deactivate all at once

---

## 🚀 Getting Started

1. **Start Server:**
   ```bash
   python manage.py runserver
   ```

2. **Open Admin:**
   ```
   http://localhost:8000/admin/
   ```

3. **Login:**
   - Username: `admin`
   - Password: `admin123`

4. **Navigate:**
   - Click "Vendors" to manage vendors
   - Click "Vendor users" to manage all staff users
   - Click any vendor name to edit and see inline staff users

---

## ✅ All Features Available in Admin

- ✅ View all vendors with approval status
- ✅ Approve/reject vendors (individual or bulk)
- ✅ Set/change/clear security PIN for vendors
- ✅ View PIN status for each vendor
- ✅ Add/edit/delete staff users (inline from vendor page)
- ✅ Manage all vendor users from dedicated page
- ✅ Change user roles (owner/staff)
- ✅ Activate/deactivate users
- ✅ View staff user count per vendor
- ✅ Search vendors by name, username, email, phone, GST
- ✅ Search vendor users by business name, username, email
- ✅ Filter by approval status, role, active status
- ✅ View logo previews
- ✅ Edit all vendor fields (business name, phone, address, GST, FSSAI, logo, footer note)

---

**Everything is manageable through Django Admin! 🎉**

