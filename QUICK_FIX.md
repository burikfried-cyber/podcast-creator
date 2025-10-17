# ⚡ QUICK FIX - Get Running in 2 Minutes

## 🎯 The Problem
Your network is blocking Supabase connections. 

## ✅ The Solution
Use SQLite locally, PostgreSQL in the cloud.

---

## 🚀 Get Running NOW (2 minutes)

### **Step 1: Switch to SQLite**
```bash
cd backend
copy .env.local .env
```

### **Step 2: Run the backend**
```bash
uvicorn app.main:app --reload
```

### **Step 3: Test it works**
Open: http://localhost:8000/docs

**Done!** Your backend is running with SQLite. ✅

---

## ☁️ Deploy to Cloud (30 minutes)

Your network blocks Supabase, but **Railway's servers won't have this issue!**

### **Why deploy now:**
1. Your computer struggles anyway
2. Cloud will connect to Supabase successfully
3. You'll have a real production environment
4. It's cheap ($0-10/month)

### **Quick deploy:**
1. Follow `DEPLOYMENT_QUICK_START.md`
2. Use PostgreSQL config on Railway
3. It will work perfectly!

---

## 📝 Summary

**Local:** SQLite (works now!)
**Cloud:** PostgreSQL (works on Railway!)

**Next:** Deploy to cloud and forget about network issues! 🚀
