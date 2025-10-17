# 🚀 Quick Start Guide - Integration Testing

## 📋 What You Need to Do (3 Steps)

### **Step 1: Install Dependencies** (5-10 minutes)

#### **Check System Requirements**
```powershell
# Check Node.js (need 18.x or 20.x)
node --version

# Check Python (need 3.11+)
python --version

# Check npm (need 9.x or 10.x)
npm --version

# Check pip
pip --version
```

**If any are missing:** See `DEPENDENCY_CHECKLIST.md` for installation instructions.

#### **Install Backend Dependencies**
```powershell
cd C:\Users\burik\podcastCreator2\backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### **Install Frontend Dependencies**
```powershell
cd C:\Users\burik\podcastCreator2\frontend

# Install all packages
npm install
```

---

### **Step 2: Run Verification Tests** (2-3 minutes)

#### **Verify Implementation**
```powershell
cd C:\Users\burik\podcastCreator2\frontend
node verify_implementation.js
```

**Expected:** ✅ 90%+ success rate, "All critical checks passed!"

#### **Verify TypeScript**
```powershell
cd C:\Users\burik\podcastCreator2\frontend
npx tsc --noEmit
```

**Expected:** No errors (warnings are okay)

#### **Verify Build**
```powershell
cd C:\Users\burik\podcastCreator2\frontend
npm run build
```

**Expected:** Build completes successfully

---

### **Step 3: Start Integration Testing** (30-60 minutes)

#### **Open TWO PowerShell Terminals**

**Terminal 1 - Backend:**
```powershell
cd C:\Users\burik\podcastCreator2\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Terminal 2 - Frontend:**
```powershell
cd C:\Users\burik\podcastCreator2\frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x ready in xxx ms
➜  Local:   http://localhost:5173/
```

#### **Open Browser**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

---

## 🧪 Quick Test Flow (5 minutes)

### **Test 1: Registration**
1. Go to http://localhost:5173
2. Click "Get Started" or "Register"
3. Fill in:
   - Name: Test User
   - Email: test@example.com
   - Password: TestPassword123!
4. Click "Register"
5. ✅ Should redirect to onboarding

### **Test 2: Onboarding**
1. Complete 5-step onboarding:
   - Welcome → Next
   - Select 3-5 topics → Next
   - Choose content depth → Next
   - Set surprise tolerance → Next
   - Review → Complete
2. ✅ Should redirect to dashboard

### **Test 3: Generate Podcast**
1. Click "Generate Podcast"
2. Enter location: "Paris, France"
3. Click "Generate"
4. ✅ Should show progress and complete

### **Test 4: Play Podcast**
1. Go to Library
2. Click on generated podcast
3. Click Play
4. ✅ Audio should play

---

## ✅ Success Criteria

**Integration is successful when:**
- [ ] User can register and login
- [ ] Onboarding flow completes
- [ ] Podcast generates successfully
- [ ] Audio plays in player
- [ ] No red errors in browser console
- [ ] No 500 errors in backend logs

---

## 🐛 Quick Troubleshooting

### **Backend won't start:**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### **Frontend won't start:**
```powershell
# Reinstall dependencies
rm -rf node_modules
npm install
```

### **CORS errors:**
Check `backend/app/core/config.py` has:
```python
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

### **Database errors:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

---

## 📚 Detailed Guides

- **Complete Testing:** `INTEGRATION_TESTING_GUIDE.md`
- **Dependencies:** `DEPENDENCY_CHECKLIST.md`
- **Remaining Tasks:** `frontend/TODO_PHASE7_COMPLETION.md`
- **Project Status:** `PROJECT_STATUS.md`

---

## 🎯 What's Next

After successful integration testing:
1. ✅ Complete remaining 22% of Phase 7
2. ✅ Add component tests
3. ✅ Enhance accessibility
4. ✅ Deploy to production

---

## 🚀 You're Ready!

**Just 3 steps:**
1. Install dependencies
2. Run verification
3. Start testing

**Let's do this! 💪**

---

## 📞 Quick Commands Reference

```powershell
# Backend
cd C:\Users\burik\podcastCreator2\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd C:\Users\burik\podcastCreator2\frontend
npm install
node verify_implementation.js
npm run dev

# Verify
http://localhost:5173      # Frontend
http://localhost:8000/docs # Backend API
```

**That's it! Simple and straightforward!** 🎉
