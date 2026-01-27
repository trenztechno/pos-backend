# Mobile App Developer Guide

**Quick Start Guide for React Native / Flutter / Mobile App Development**

This server serves your mobile POS app. Follow this guide to integrate with the API.

---

## 🚀 Where to Start

### Step 1: Get the Server Running

**Ask the backend team to run:**
```bash
./setup.sh
```

This sets up everything. Once done, you'll get:
- Server URL (usually `http://localhost:8000` or production URL)
- Test vendor credentials (see below)

### Step 2: Get Your Test Credentials

**Use these approved vendor accounts (ready to use immediately):**

```
✅ APPROVED VENDOR 1 (ABC Store):
   Username: vendor1
   Password: vendor123
   Status: Approved & Active
   Has test data: Categories, Items

✅ APPROVED VENDOR 2 (XYZ Restaurant):
   Username: vendor2
   Password: vendor123
   Status: Approved & Active
   Has test data: Categories, Items

⏳ PENDING VENDOR (For Testing Approval Flow):
   Username: pendingvendor
   Password: pending123
   Status: Pending Approval
   Purpose: Test what happens when vendor is not approved
```

### Step 3: Test Authentication

**Login to get your token:**
```javascript
// React Native / JavaScript Example
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'vendor1',
    password: 'vendor123'
  })
});

const data = await loginResponse.json();
const token = data.token; // Save this token!

console.log('Token:', token);
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "vendor1",
  "message": "Login successful",
  "vendor": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "ABC Store",
    "gst_no": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/.../logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
    "footer_note": "Thank you for visiting!"
  }
}
```

**Note:** `logo_url` is a pre-signed URL (temporary, expires in 1 hour). Download and cache it immediately if you need to display it.

**Save this token securely!** Use it in all API calls.

**Important:** Billing mode (GST/Non-GST) is set per bill, not per vendor. Each bill can be either GST or Non-GST.

### Step 4: Test API Endpoints

**Get all items:**
```javascript
const itemsResponse = await fetch('http://localhost:8000/items/', {
  headers: {
    'Authorization': `Token ${token}`
  }
});

const items = await itemsResponse.json();
console.log('Items:', items);
```

**Get all categories:**
```javascript
const categoriesResponse = await fetch('http://localhost:8000/items/categories/', {
  headers: {
    'Authorization': `Token ${token}`
  }
});

const categories = await categoriesResponse.json();
console.log('Categories:', categories);
```

---

## 📚 Essential Documentation

**You only need these 2 files:**

1. **`API_DOCUMENTATION.md`** - Complete API reference
   - All endpoints with examples
   - Request/response formats
   - Error handling
   - Authentication flow

2. **`TEST_ACCOUNTS.md`** - Test credentials and scenarios
   - All test accounts
   - Quick test commands
   - Test data summary

**That's it!** Everything else is for backend/server setup.

---

## 📱 Mobile App Implementation Flow

### 1. App Startup (Initial Sync)

```javascript
// When app starts, do initial sync
async function initialSync() {
  // 1. Login
  const loginResponse = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      username: 'vendor1', 
      password: 'vendor123' 
    })
  });
  const { token } = await loginResponse.json();
  
  // Save token securely (AsyncStorage / SecureStore)
  await AsyncStorage.setItem('auth_token', token);
  
  // 2. Download all categories
  const categoriesResponse = await fetch('http://localhost:8000/items/categories/', {
    headers: { 'Authorization': `Token ${token}` }
  });
  const categories = await categoriesResponse.json();
  
  // 3. Download all items
  const itemsResponse = await fetch('http://localhost:8000/items/', {
    headers: { 'Authorization': `Token ${token}` }
  });
  const items = await itemsResponse.json();
  
  // 4. Save to local SQLite database
  await saveCategoriesToLocalDB(categories);
  await saveItemsToLocalDB(items);
  
  // 5. Download item images (from image_url field - pre-signed URLs)
  // IMPORTANT: Pre-signed URLs expire after 1 hour! Download immediately and cache locally.
  for (const item of items) {
    if (item.image_url) {
      // image_url is a pre-signed URL (temporary, secure)
      // Download and cache locally - don't store the URL, it expires!
      await downloadAndCacheImage(item.image_url, item.id);
    }
  }
  
  console.log('Initial sync complete!');
}
```

### 2. Offline Operations (Local First)

```javascript
// User creates/updates/deletes items - ALWAYS do locally first!
async function createItemLocally(itemData) {
  // 1. Generate UUID on client
  const itemId = generateUUID();
  
  // 2. Save to local SQLite immediately
  await db.insert('items', {
    id: itemId,
    name: itemData.name,
    price: itemData.price,
    // ... other fields
    is_synced: false, // Mark as not synced
    created_at: new Date().toISOString()
  });
  
  // 3. Show in UI immediately (don't wait for server!)
  
  // 4. Queue for sync (if online, sync immediately; if offline, queue)
  if (isOnline()) {
    await syncItemToServer(itemId, 'create');
  } else {
    await queueOperationForSync({
      operation: 'create',
      item_id: itemId,
      data: itemData,
      timestamp: new Date().toISOString()
    });
  }
}
```

### 3. Sync When Online (Background Sync)

```javascript
// When internet becomes available, sync queued operations
async function syncQueuedOperations() {
  const token = await AsyncStorage.getItem('auth_token');
  const queuedOps = await db.query('SELECT * FROM sync_queue WHERE synced = 0');
  
  // Group by type (categories or items)
  const itemOps = queuedOps.filter(op => op.type === 'item');
  const categoryOps = queuedOps.filter(op => op.type === 'category');
  
  // Sync items
  if (itemOps.length > 0) {
    const syncPayload = itemOps.map(op => ({
      operation: op.operation, // 'create', 'update', 'delete'
      data: JSON.parse(op.data),
      timestamp: op.timestamp
    }));
    
    const response = await fetch('http://localhost:8000/items/sync', {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(syncPayload)
    });
    
    const result = await response.json();
    
    // Mark as synced
    for (const op of itemOps) {
      await db.update('sync_queue', { synced: true }, { id: op.id });
    }
  }
  
  // Sync categories similarly...
}
```

### 4. Create Bill (Offline-First - Never Block!)

**Complete Bill Creation Examples for All Cases:**

#### Example 1: GST Bill - Intra-State - Cash Payment

```javascript
// Creating a GST bill with intra-state tax (CGST + SGST)
async function createGSTBillIntraStateCash(billData) {
  const billingMode = 'gst';
  const paymentMode = 'cash';
  const isInterState = false; // Intra-state transaction
  
  // Calculate subtotal
  let subtotal = 0;
  let totalItemGST = 0;
  
  billData.items.forEach(item => {
    const itemSubtotal = item.mrp_price * item.quantity;
    subtotal += itemSubtotal;
    
    // Calculate GST for each item
    if (item.gst_percentage > 0) {
      const itemGST = itemSubtotal * (item.gst_percentage / 100);
      totalItemGST += itemGST;
      item.item_gst = itemGST;
    }
  });
  
  // Calculate CGST and SGST (split equally for intra-state)
  const cgst = totalItemGST / 2;
  const sgst = totalItemGST / 2;
  const igst = 0;
  const totalTax = totalItemGST;
  const total = subtotal + totalTax;
  
  // Generate invoice number
  const invoiceNumber = await generateInvoiceNumber(billingMode);
  
  // Prepare bill payload
  const billPayload = {
    invoice_number: invoiceNumber,
    bill_id: generateUUID(),
    billing_mode: billingMode,
    restaurant_name: vendorData.business_name,
    address: vendorData.address,
    gstin: vendorData.gst_no,
    fssai_license: vendorData.fssai_license,
    bill_date: new Date().toISOString().split('T')[0],
    items: billData.items.map(item => ({
      id: generateUUID(),
      item_id: item.item_id || null, // Link to master item if exists
      name: item.name,
      price: item.price,
      mrp_price: item.mrp_price,
      price_type: item.price_type || 'exclusive',
      gst_percentage: item.gst_percentage || 0,
      quantity: item.quantity,
      subtotal: item.mrp_price * item.quantity,
      item_gst: item.item_gst || 0,
      veg_nonveg: item.veg_nonveg || null
    })),
    subtotal: subtotal,
    cgst: cgst,
    sgst: sgst,
    igst: igst,
    total_tax: totalTax,
    total: total,
    payment_mode: paymentMode,
    amount_paid: total,
    change_amount: 0,
    timestamp: new Date().toISOString()
  };
  
  // Save locally first
  await db.insert('bills', {
    id: billPayload.bill_id,
    bill_data: JSON.stringify(billPayload),
    is_synced: false
  });
  
  // Print immediately
  await printBill(billPayload);
  
  // Sync in background
  if (isOnline()) {
    await syncBillToServer(billPayload);
  }
}
```

#### Example 2: GST Bill - Inter-State - UPI Payment

```javascript
// Creating a GST bill with inter-state tax (IGST only)
async function createGSTBillInterStateUPI(billData) {
  const billingMode = 'gst';
  const paymentMode = 'upi';
  const isInterState = true; // Inter-state transaction
  const upiReference = billData.upi_reference; // Transaction ID
  
  // Calculate subtotal and GST
  let subtotal = 0;
  let totalItemGST = 0;
  
  billData.items.forEach(item => {
    const itemSubtotal = item.mrp_price * item.quantity;
    subtotal += itemSubtotal;
    
    if (item.gst_percentage > 0) {
      const itemGST = itemSubtotal * (item.gst_percentage / 100);
      totalItemGST += itemGST;
      item.item_gst = itemGST;
    }
  });
  
  // For inter-state: IGST only (no CGST/SGST)
  const cgst = 0;
  const sgst = 0;
  const igst = totalItemGST;
  const totalTax = totalItemGST;
  const total = subtotal + totalTax;
  
  const invoiceNumber = await generateInvoiceNumber(billingMode);
  
  const billPayload = {
    invoice_number: invoiceNumber,
    bill_id: generateUUID(),
    billing_mode: billingMode,
    restaurant_name: vendorData.business_name,
    address: vendorData.address,
    gstin: vendorData.gst_no,
    fssai_license: vendorData.fssai_license,
    bill_date: new Date().toISOString().split('T')[0],
    items: billData.items.map(item => ({
      id: generateUUID(),
      item_id: item.item_id || null,
      name: item.name,
      price: item.price,
      mrp_price: item.mrp_price,
      price_type: item.price_type || 'exclusive',
      gst_percentage: item.gst_percentage || 0,
      quantity: item.quantity,
      subtotal: item.mrp_price * item.quantity,
      item_gst: item.item_gst || 0,
      veg_nonveg: item.veg_nonveg || null
    })),
    subtotal: subtotal,
    cgst: cgst,
    sgst: sgst,
    igst: igst,
    total_tax: totalTax,
    total: total,
    payment_mode: paymentMode,
    payment_reference: upiReference,
    amount_paid: total,
    timestamp: new Date().toISOString()
  };
  
  await db.insert('bills', {
    id: billPayload.bill_id,
    bill_data: JSON.stringify(billPayload),
    is_synced: false
  });
  
  await printBill(billPayload);
  
  if (isOnline()) {
    await syncBillToServer(billPayload);
  }
}
```

#### Example 3: Non-GST Bill - Cash Payment

```javascript
// Creating a Non-GST bill
async function createNonGSTBillCash(billData) {
  const billingMode = 'non_gst';
  const paymentMode = 'cash';
  
  // Calculate subtotal (no tax)
  let subtotal = 0;
  
  billData.items.forEach(item => {
    subtotal += item.mrp_price * item.quantity;
  });
  
  // For Non-GST: total = subtotal (no tax)
  const total = subtotal;
  
  const invoiceNumber = await generateInvoiceNumber(billingMode);
  
  const billPayload = {
    invoice_number: invoiceNumber,
    bill_id: generateUUID(),
    billing_mode: billingMode,
    restaurant_name: vendorData.business_name,
    address: vendorData.address,
    gstin: vendorData.gst_no,
    fssai_license: vendorData.fssai_license,
    bill_date: new Date().toISOString().split('T')[0],
    items: billData.items.map(item => ({
      id: generateUUID(),
      item_id: item.item_id || null,
      name: item.name,
      price: item.price,
      mrp_price: item.mrp_price,
      price_type: item.price_type || 'exclusive',
      quantity: item.quantity,
      subtotal: item.mrp_price * item.quantity,
      veg_nonveg: item.veg_nonveg || null
    })),
    subtotal: subtotal,
    total: total,
    payment_mode: paymentMode,
    amount_paid: total,
    change_amount: 0,
    timestamp: new Date().toISOString()
  };
  
  await db.insert('bills', {
    id: billPayload.bill_id,
    bill_data: JSON.stringify(billPayload),
    is_synced: false
  });
  
  await printBill(billPayload);
  
  if (isOnline()) {
    await syncBillToServer(billPayload);
  }
}
```

#### Example 4: GST Bill - Credit Payment (Pending Payment)

```javascript
// Creating a GST bill with credit payment (pending payment)
async function createGSTBillCredit(billData) {
  const billingMode = 'gst';
  const paymentMode = 'credit';
  
  // Calculate subtotal and GST (same as intra-state example)
  let subtotal = 0;
  let totalItemGST = 0;
  
  billData.items.forEach(item => {
    const itemSubtotal = item.mrp_price * item.quantity;
    subtotal += itemSubtotal;
    
    if (item.gst_percentage > 0) {
      const itemGST = itemSubtotal * (item.gst_percentage / 100);
      totalItemGST += itemGST;
      item.item_gst = itemGST;
    }
  });
  
  const cgst = totalItemGST / 2;
  const sgst = totalItemGST / 2;
  const igst = 0;
  const totalTax = totalItemGST;
  const total = subtotal + totalTax;
  
  const invoiceNumber = await generateInvoiceNumber(billingMode);
  
  const billPayload = {
    invoice_number: invoiceNumber,
    bill_id: generateUUID(),
    billing_mode: billingMode,
    restaurant_name: vendorData.business_name,
    address: vendorData.address,
    gstin: vendorData.gst_no,
    fssai_license: vendorData.fssai_license,
    bill_date: new Date().toISOString().split('T')[0],
    items: billData.items.map(item => ({
      id: generateUUID(),
      item_id: item.item_id || null,
      name: item.name,
      price: item.price,
      mrp_price: item.mrp_price,
      price_type: item.price_type || 'exclusive',
      gst_percentage: item.gst_percentage || 0,
      quantity: item.quantity,
      subtotal: item.mrp_price * item.quantity,
      item_gst: item.item_gst || 0,
      veg_nonveg: item.veg_nonveg || null
    })),
    subtotal: subtotal,
    cgst: cgst,
    sgst: sgst,
    igst: igst,
    total_tax: totalTax,
    total: total,
    payment_mode: paymentMode,
    amount_paid: 0, // No payment received yet
    customer_name: billData.customer_name,
    customer_phone: billData.customer_phone,
    timestamp: new Date().toISOString()
  };
  
  await db.insert('bills', {
    id: billPayload.bill_id,
    bill_data: JSON.stringify(billPayload),
    is_synced: false
  });
  
  await printBill(billPayload);
  
  if (isOnline()) {
    await syncBillToServer(billPayload);
  }
  
  // Outstanding amount = total - amount_paid
  const outstandingAmount = total - 0;
  console.log('Outstanding amount:', outstandingAmount);
}
```

#### Example 5: GST Bill with Discounts

```javascript
// Creating a GST bill with item-level and bill-level discounts
async function createGSTBillWithDiscounts(billData) {
  const billingMode = 'gst';
  const paymentMode = billData.payment_mode || 'cash';
  
  let subtotal = 0;
  let totalItemGST = 0;
  let totalDiscount = 0;
  
  billData.items.forEach(item => {
    let itemSubtotal = item.mrp_price * item.quantity;
    
    // Apply item-level discount
    if (item.additional_discount > 0) {
      itemSubtotal -= item.additional_discount;
      totalDiscount += item.additional_discount;
    }
    
    subtotal += itemSubtotal;
    
    // Calculate GST on discounted amount
    if (item.gst_percentage > 0) {
      const itemGST = itemSubtotal * (item.gst_percentage / 100);
      totalItemGST += itemGST;
      item.item_gst = itemGST;
    }
  });
  
  // Apply bill-level discount
  if (billData.discount_amount > 0) {
    subtotal -= billData.discount_amount;
    totalDiscount += billData.discount_amount;
  }
  
  const cgst = totalItemGST / 2;
  const sgst = totalItemGST / 2;
  const igst = 0;
  const totalTax = totalItemGST;
  const total = subtotal + totalTax;
  
  const invoiceNumber = await generateInvoiceNumber(billingMode);
  
  const billPayload = {
    invoice_number: invoiceNumber,
    bill_id: generateUUID(),
    billing_mode: billingMode,
    restaurant_name: vendorData.business_name,
    address: vendorData.address,
    gstin: vendorData.gst_no,
    fssai_license: vendorData.fssai_license,
    bill_date: new Date().toISOString().split('T')[0],
    items: billData.items.map(item => ({
      id: generateUUID(),
      item_id: item.item_id || null,
      name: item.name,
      price: item.price,
      mrp_price: item.mrp_price,
      price_type: item.price_type || 'exclusive',
      gst_percentage: item.gst_percentage || 0,
      quantity: item.quantity,
      subtotal: (item.mrp_price * item.quantity) - (item.additional_discount || 0),
      item_gst: item.item_gst || 0,
      additional_discount: item.additional_discount || 0,
      discount_amount: item.additional_discount || 0,
      veg_nonveg: item.veg_nonveg || null
    })),
    subtotal: subtotal,
    cgst: cgst,
    sgst: sgst,
    igst: igst,
    total_tax: totalTax,
    discount_amount: totalDiscount,
    discount_percentage: (totalDiscount / (subtotal + totalDiscount)) * 100,
    total: total,
    payment_mode: paymentMode,
    amount_paid: total,
    timestamp: new Date().toISOString()
  };
  
  await db.insert('bills', {
    id: billPayload.bill_id,
    bill_data: JSON.stringify(billPayload),
    is_synced: false
  });
  
  await printBill(billPayload);
  
  if (isOnline()) {
    await syncBillToServer(billPayload);
  }
}
```

#### Example 6: Sync Bill to Server

```javascript
// Sync bill to server (background sync)
async function syncBillToServer(billPayload) {
  try {
    const token = await AsyncStorage.getItem('auth_token');
    
    const response = await fetch('http://localhost:8000/backup/sync', {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        bill_data: billPayload,
        device_id: await getDeviceId()
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      // Mark as synced in local DB
      await db.update('bills', { is_synced: true }, { id: billPayload.bill_id });
      console.log('Bill synced successfully:', result);
    } else {
      console.error('Sync failed:', await response.text());
    }
  } catch (error) {
    console.error('Sync error:', error);
    // Queue for retry later
    await queueBillForSync(billPayload.bill_id);
  }
}
```

**Payment Mode Summary:**
- `"cash"` - Cash payment (no reference needed)
- `"upi"` - UPI payment (include `payment_reference` for transaction ID)
- `"card"` - Card payment (include `payment_reference` for card transaction ID)
- `"credit"` - Credit payment (pending payment, `amount_paid` typically 0)
- `"other"` - Other payment methods (wallet, cheque, etc.)

---

## 🔑 Key API Endpoints You'll Use

### Authentication
- `POST /auth/login` - Get token (use on app startup)
- `GET /auth/profile` - Get vendor profile (business details, logo)
- `PATCH /auth/profile` - Update vendor profile (upload logo, update business details)
- `POST /auth/register` - Register new vendor (requires: username, email, password, business_name, phone, gst_no, address)
- `POST /auth/forgot-password` - Verify GST number to initiate password reset
- `POST /auth/reset-password` - Reset password using GST number
 - `POST /auth/vendor/users/create` - Vendor owner creates staff users (same vendor, same access to billing)
 - `GET /auth/vendor/users` - List all vendor users (owner + staff)
 - `POST /auth/vendor/users/<user_id>/reset-password` - Owner resets staff password (staff have no forgot-password)
 - `DELETE /auth/vendor/users/<user_id>` - Owner deactivates staff user

### Categories
- `GET /items/categories/` - Get all categories (initial sync)
- `POST /items/categories/` - Create category (instant add)
- `PATCH /items/categories/<uuid>` - Update category
- `DELETE /items/categories/<uuid>` - Delete category
- `POST /items/categories/sync` - Batch sync categories (offline sync)

### Items
- `GET /items/` - Get all items (initial sync)
  - Query params: `?category=<uuid>` (filter by category)
  - Query params: `?search=<term>` (search items)
- `POST /items/` - Create item (instant add)
- `GET /items/<uuid>` - Get item details
- `PATCH /items/<uuid>` - Update item
- `DELETE /items/<uuid>` - Delete item
- `POST /items/sync` - Batch sync items (offline sync) ⭐ **IMPORTANT**

### Sales Backup (Bi-Directional Sync)
- `GET /backup/sync` - **Download bills from server** (for new devices logging in)
  - Query params: `since` (ISO timestamp), `limit` (default 1000), `billing_mode` (gst/non_gst), `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)
  - Returns structured Bill objects with nested BillItem objects
  - Use this when a new device logs in to load existing sales history
- `POST /backup/sync` - **Upload bills** (background sync)
  - Accepts single bill object or array of bills
  - Bills stored in structured format (Bill + BillItem models)
  - Duplicate bills (same invoice_number) are automatically skipped

### Settings
- `POST /settings/push` - Backup device settings

---

## 🎯 Important Rules to Follow

### 1. Offline-First Principle ⭐ **CRITICAL**
- ✅ **Always save locally first** (SQLite)
- ✅ **Never block UI** waiting for server response
- ✅ **Print immediately** after saving bill locally
- ✅ **Sync in background** when online
- ✅ **Queue operations** when offline

### 2. Authentication
- ✅ **Token required** for all endpoints (except `/health/`, `/auth/login`, `/auth/register`)
- ✅ **Include token** in header: `Authorization: Token <token>`
- ✅ **Store token securely** (AsyncStorage / SecureStore)
- ✅ **Token expires** on logout (delete token on server)

### 3. Vendor Approval
- ✅ **New vendors** must be approved before they can use API
- ✅ **Unapproved vendors** get "pending approval" message
- ✅ **Use approved test accounts** (`vendor1`, `vendor2`) for development

### 4. Data Isolation
- ✅ **Each vendor** only sees their own data
- ✅ **Server automatically filters** by vendor
- ✅ **No need to filter** on mobile side

### 5. Multi-Category Support
- ✅ **Items can belong to multiple categories**
- ✅ **Use `category_ids` array** when creating/updating items
- ✅ **Example:** `category_ids: ["uuid1", "uuid2"]`

### 6. Billing Mode (GST vs Non-GST) - Per Bill ⭐ **IMPORTANT**
- ✅ **Billing mode is set per bill**, not per vendor
- ✅ **Each bill can be GST or Non-GST** - user selects when creating bill
- ✅ **For GST bills**, include tax details:
  - `cgst`: Central GST amount (for intra-state)
  - `sgst`: State GST amount (for intra-state)
  - `igst`: Integrated GST amount (for inter-state)
  - `total_tax`: Sum of all taxes
- ✅ **For Non-GST bills**, no tax fields needed
- ✅ **Include `billing_mode` in bill JSON** when syncing to server

**GST Bill Example:**
```javascript
const billData = {
  bill_id: "uuid",
  billing_mode: "gst",
  items: [...],
  subtotal: 1000.00,
  cgst: 90.00,      // 9% for intra-state
  sgst: 90.00,      // 9% for intra-state
  igst: 0.00,       // 0 for intra-state, 180.00 for inter-state
  total_tax: 180.00,
  total: 1180.00,
  timestamp: "2026-01-01T10:00:00Z"
};
```

**Non-GST Bill Example:**
```javascript
const billData = {
  bill_id: "uuid",
  billing_mode: "non_gst",
  items: [...],
  subtotal: 1000.00,
  total: 1000.00,
  timestamp: "2026-01-01T10:00:00Z"
};
```

### 7. Image Handling (Pre-Signed URLs) 🔒
- ✅ **Images stored on server** (local or S3)
- ✅ **Pre-signed URLs returned** in `image_url` field (secure, temporary URLs)
- ✅ **URLs expire after 1 hour** (configurable) - cache images locally immediately
- ✅ **Download and cache** images locally during initial sync
- ✅ **Works offline** after initial download
- ✅ **Refresh URLs when expired** - request new URLs from API if cached image missing

**Important:** Pre-signed URLs are temporary and expire. Always download and cache images locally immediately. Don't store pre-signed URLs long-term - they will expire!

**Example:**
```javascript
// Get items with pre-signed URLs
const items = await fetch('http://localhost:8000/items/', {
  headers: { 'Authorization': `Token ${token}` }
}).then(r => r.json());

// Download and cache images immediately
for (const item of items) {
  if (item.image_url) {
    // Pre-signed URL looks like:
    // https://bucket.s3.region.amazonaws.com/items/.../image.jpg?X-Amz-Algorithm=...&X-Amz-Expires=3600&...
    await downloadAndCacheImage(item.image_url, item.id);
    // Store locally, don't rely on URL after 1 hour
  }
}
```

### 8. Bi-Directional Sync for Bills ⭐ **NEW**
- ✅ **Download bills on login**: When a new device logs in, download existing bills from server
- ✅ **Use GET /backup/sync**: Call this after login to load sales history
- ✅ **Filter options**: Use query params to filter by date, billing_mode, etc.
- ✅ **Structured format**: Bills returned in structured format (Bill + BillItem objects)
- ✅ **Duplicate handling**: Server automatically skips duplicate bills (same invoice_number)

**Example: Download bills on app startup**
```javascript
async function downloadBillsFromServer(token) {
  try {
    const response = await fetch('http://localhost:8000/backup/sync', {
      headers: {
        'Authorization': `Token ${token}`
      }
    });
    
    const data = await response.json();
    const bills = data.bills || [];
    
    // Save bills to local SQLite
    for (const bill of bills) {
      await db.insert('bills', {
        id: bill.id,
        bill_data: JSON.stringify(bill),
        is_synced: true // Already synced from server
      });
    }
    
    console.log(`Downloaded ${bills.length} bills from server`);
  } catch (error) {
    console.error('Error downloading bills:', error);
  }
}

// Call after login
const loginData = await login(username, password);
await downloadBillsFromServer(loginData.token);
```

### 9. UUIDs
- ✅ **All IDs are UUIDs** (not integers)
- ✅ **Generate UUIDs on client** (v4)
- ✅ **Use same UUID** when syncing to server

---

## 🧪 Testing Guide

### Test Accounts

**For Development:**
- `vendor1` / `vendor123` - Approved, has test data
- `vendor2` / `vendor123` - Approved, has test data

**For Testing Approval Flow:**
- `pendingvendor` / `pending123` - Pending approval
  - Try to login → Should get "pending approval" error
  - Approve via Sales Rep UI or Admin
  - Try login again → Should work

### Testing Checklist

- [ ] **Login with approved vendor** → Get token ✅
- [ ] **Login with pending vendor** → Get "pending approval" error ✅
- [ ] **Get categories** → See vendor-specific + global categories ✅
- [ ] **Get items** → See items with `image_url` and `categories_list` ✅
- [ ] **Create item locally** → Appears in UI immediately ✅
- [ ] **Create item with categories** → Item has multiple categories ✅
- [ ] **Update item** → Changes saved locally first ✅
- [ ] **Delete item** → Removed locally first ✅
- [ ] **Search items** → `?search=coke` works ✅
- [ ] **Filter by category** → `?category=<uuid>` works ✅
- [ ] **Batch sync items** → Offline changes synced ✅
- [ ] **Create bill offline** → Saved locally, printed, queued for sync ✅
- [ ] **Sync bills** → Bills uploaded when online ✅
- [ ] **Image download** → Images cached locally ✅
- [ ] **App works offline** → All features work without internet ✅

### Testing Offline-First Flow

1. **Turn off internet**
2. **Create item** → Should work, saved locally
3. **Create bill** → Should work, printed, saved locally
4. **Turn on internet**
5. **App should sync** → Items and bills uploaded to server

### Testing Sync Conflicts

1. **Create item on phone** (offline)
2. **Update same item on server** (via another client)
3. **Sync from phone** → Last-Write-Wins (newer timestamp wins)

---

## 📞 Common Issues & Solutions

### 401 Unauthorized
**Problem:** Token missing or invalid  
**Solution:** 
- Check if token is included in header
- Try logging in again to get new token
- Make sure vendor is approved

### 403 Forbidden
**Problem:** Vendor not approved  
**Solution:**
- Use approved test accounts (`vendor1`, `vendor2`)
- Or ask backend team to approve your vendor

### 404 Not Found
**Problem:** Resource doesn't exist  
**Solution:**
- Check if UUID is correct
- Resource might belong to another vendor (vendor isolation)

### Network Error
**Problem:** No internet connection  
**Solution:**
- This is expected! Save locally and queue for sync
- App should work offline

---

## 🗑️ Files You Can Ignore

**These are for backend/server setup only - you don't need them:**

- `setup.sh` - Server setup script
- `setup_db.sh` - Database setup
- `ensure_default_users.py` - User verification
- `create_test_data.py` - Test data creation
- `verify_all_endpoints.py` - Server verification
- `verify_system.py` - System verification
- `STORAGE_CONFIGURATION.md` - Server image storage config
- `SETUP.md` - Server setup instructions
- `ENDPOINTS_SUMMARY.md` - Server endpoint summary
- All Python files (`.py` files in all folders)
- `manage.py` - Django management
- `requirements.txt` - Python dependencies
- `.env` - Server configuration
- `venv/` - Python virtual environment
- `logs/` - Server logs
- All `__pycache__/` folders

**You only need:**
- `API_DOCUMENTATION.md` ✅
- `TEST_ACCOUNTS.md` ✅
- `MOBILE_APP_GUIDE.md` ✅ (this file)
- Server URL and credentials ✅

---

## 📝 Quick Reference

### Base URL
```
http://localhost:8000  (development)
https://your-server.com  (production)
```

### Authentication Header
```
Authorization: Token <your_token_here>
```

### Test Credentials
```
vendor1 / vendor123  (Approved, ready to use)
vendor2 / vendor123  (Approved, ready to use)
```

### Key Endpoints
```
POST /auth/login                    → Get token
POST /auth/register                 → Register new vendor (all fields required)
POST /auth/forgot-password          → Verify GST number for password reset
POST /auth/reset-password           → Reset password using GST number
GET  /items/                        → Get all items
GET  /items/categories/             → Get all categories
POST /items/sync                    → Batch sync items ⭐
POST /items/categories/sync          → Batch sync categories ⭐
POST /backup/sync                   → Upload bills
GET  /inventory/                    → Get inventory items (raw materials)
POST /inventory/                    → Create inventory item
PATCH /inventory/<id>/stock/         → Update stock (add/subtract)
```

---

**That's it! Start with Step 1 above and you're good to go! 🚀**

For complete API details, see `API_DOCUMENTATION.md`

