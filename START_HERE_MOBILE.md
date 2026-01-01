# 🚀 START HERE - Mobile App Developer

**Quick reference for mobile app developers**

---

## 📚 Read These 3 Files (In Order)

1. **`MOBILE_APP_GUIDE.md`** ⭐ **START HERE!**
   - Step-by-step integration guide
   - Code examples
   - Offline-first implementation
   - Testing checklist

2. **`API_DOCUMENTATION.md`**
   - Complete API reference
   - All endpoints with examples
   - Request/response formats

3. **`TEST_ACCOUNTS.md`**
   - Test credentials
   - Testing scenarios
   - Quick test commands

---

## 🔑 Quick Start (5 Minutes)

### 1. Get Server URL
Ask backend team for server URL (usually `http://localhost:8000`)

### 2. Login & Get Token
```javascript
POST http://localhost:8000/auth/login
{
  "username": "vendor1",
  "password": "vendor123"
}
```

### 3. Use Token in API Calls
```javascript
GET http://localhost:8000/items/
Authorization: Token YOUR_TOKEN_HERE
```

**That's it!** You're ready to build! 🎉

---

## 🧪 Test Accounts

**For Development:**
- `vendor1` / `vendor123` ✅ Approved, has test data
- `vendor2` / `vendor123` ✅ Approved, has test data

**For Testing:**
- `pendingvendor` / `pending123` ⏳ Pending approval (test approval flow)

---

## 📱 Key Endpoints You'll Use

```
POST /auth/login              → Get token
GET  /items/                  → Get all items
GET  /items/categories/      → Get all categories
POST /items/                  → Create item
POST /items/sync              → Batch sync (offline) ⭐
POST /backup/sync             → Upload bills
```

---

## 🗑️ Files to Ignore

**You don't need these (backend/server files):**
- All `.py` files
- `setup.sh`, `setup_db.sh`
- `SETUP.md`, `STORAGE_CONFIGURATION.md`
- `requirements.txt`, `manage.py`
- `venv/`, `logs/`, `__pycache__/`

**You only need:**
- `MOBILE_APP_GUIDE.md` ✅
- `API_DOCUMENTATION.md` ✅
- `TEST_ACCOUNTS.md` ✅

---

## 📞 Need Help?

1. Check `MOBILE_APP_GUIDE.md` - Has everything you need
2. Check `API_DOCUMENTATION.md` - Complete API reference
3. Ask backend team - They handle server setup

---

**Now go read `MOBILE_APP_GUIDE.md` and start building! 🚀**

