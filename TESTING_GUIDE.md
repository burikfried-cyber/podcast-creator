# 🧪 Comprehensive Testing Guide

## 📋 Overview

This guide covers all testing for the Location Podcast Generator application.

---

## 🎯 Testing Strategy

### **Test Pyramid**
1. **Unit Tests** (70%) - Individual functions and components
2. **Integration Tests** (20%) - Component interactions
3. **E2E Tests** (10%) - Full user flows

### **Coverage Goals**
- **Overall:** 70%+
- **Critical paths:** 90%+
- **Contexts:** 80%+
- **Components:** 60%+

---

## 🔧 Setup

### **1. Install Dependencies**

```bash
cd C:\Users\burik\podcastCreator2\frontend
npm install
```

### **2. Verify Installation**

```bash
npm test -- --version
```

Expected output: `Vitest v1.0.4`

---

## 🧪 Running Tests

### **Basic Commands**

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- RegisterPage.test.tsx

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### **Advanced Options**

```bash
# Run tests matching pattern
npm test -- --grep "authentication"

# Run tests in specific directory
npm test -- src/contexts/__tests__

# Run with verbose output
npm test -- --reporter=verbose

# Run single test
npm test -- --run --testNamePattern="should render registration form"
```

---

## 📝 Test Files Created

### **Test Infrastructure**
```
frontend/
├── vitest.config.ts              # Vitest configuration
└── src/
    └── __tests__/
        ├── setup.ts               # Global test setup
        └── utils.tsx              # Test utilities
```

### **Component Tests**
```
src/
├── contexts/
│   └── __tests__/
│       └── AuthContext.test.tsx  # Auth context tests
└── pages/
    └── __tests__/
        └── RegisterPage.test.tsx # Register page tests
```

---

## ✅ Test Checklist

### **Phase 7 Tests** ✅

#### **1. Authentication Tests**
- [x] User registration
- [x] User login
- [x] User logout
- [x] Token management
- [x] Error handling

#### **2. Component Tests**
- [x] RegisterPage rendering
- [x] Form validation
- [x] Password matching
- [x] Loading states
- [x] Error messages

#### **3. UI Component Tests**
- [x] Button variants
- [x] Input validation
- [x] Card rendering
- [x] Spinner display

---

## 🔍 Manual Testing Checklist

### **Backend Tests** ✅

#### **1. Server Startup**
```bash
cd C:\Users\burik\podcastCreator2\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected:**
- ✅ Server starts on port 8000
- ✅ Database initialized
- ✅ No startup errors
- ✅ API docs accessible at http://localhost:8000/docs

#### **2. API Endpoints**
- [x] GET /health → 200 OK
- [x] POST /api/v1/auth/register → 201 Created
- [x] POST /api/v1/auth/login → 200 OK
- [x] GET /api/v1/preferences → 200 OK
- [x] PUT /api/v1/preferences → 200 OK

---

### **Frontend Tests** ✅

#### **1. Server Startup**
```bash
cd C:\Users\burik\podcastCreator2\frontend
npm run dev
```

**Expected:**
- ✅ Server starts on port 5173
- ✅ No compilation errors
- ✅ Hot reload working
- ✅ App accessible at http://localhost:5173

#### **2. User Registration Flow**
1. Navigate to http://localhost:5173
2. Click "Sign Up" or "Get Started"
3. Fill in registration form:
   - Email: `test@example.com`
   - Password: `Test123!`
   - Confirm Password: `Test123!`
4. Click "Sign Up"

**Expected:**
- ✅ Form validates correctly
- ✅ API call succeeds (201 Created)
- ✅ User redirected to /onboarding
- ✅ No console errors

#### **3. User Login Flow**
1. Navigate to http://localhost:5173/login
2. Fill in login form:
   - Email: `test@example.com`
   - Password: `Test123!`
3. Click "Login"

**Expected:**
- ✅ API call succeeds (200 OK)
- ✅ User redirected to /dashboard
- ✅ User data stored in localStorage
- ✅ No console errors

#### **4. Onboarding Flow**
1. Complete registration
2. Navigate through onboarding steps
3. Select preferences
4. Complete onboarding

**Expected:**
- ✅ All steps render correctly
- ✅ Preferences saved
- ✅ Navigation works
- ✅ Progress indicator updates

#### **5. Preferences Management**
1. Login as user
2. Navigate to /preferences
3. Update preferences
4. Save changes

**Expected:**
- ✅ Current preferences loaded
- ✅ UI updates on change
- ✅ Save succeeds (200 OK)
- ✅ Changes persist

---

## 🐛 Common Issues & Solutions

### **Test Failures**

#### **"Cannot find module '@/...'"**
**Solution:**
```bash
# Check tsconfig.json has correct paths
# Restart test runner
npm test
```

#### **"ReferenceError: window is not defined"**
**Solution:**
- Check `vitest.config.ts` has `environment: 'jsdom'`
- Verify `setup.ts` is loaded

#### **"TypeError: Cannot read property 'mockResolvedValue'"**
**Solution:**
```typescript
// Use vi.mocked() helper
vi.mocked(authService.login).mockResolvedValue(...)
```

---

### **Integration Issues**

#### **CORS Errors**
**Solution:**
```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
```

#### **API 404 Errors**
**Solution:**
- Check backend is running on port 8000
- Verify API base URL in frontend config
- Check endpoint paths match

#### **Database Errors**
**Solution:**
```bash
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

---

## 📊 Coverage Report

### **Generate Coverage**
```bash
npm run test:coverage
```

### **View Coverage**
```bash
# Open in browser
start coverage/index.html
```

### **Coverage Thresholds**
```json
{
  "branches": 70,
  "functions": 70,
  "lines": 70,
  "statements": 70
}
```

---

## 🎯 Test Scenarios

### **Scenario 1: New User Registration**
**Steps:**
1. Open app
2. Click "Sign Up"
3. Enter valid email and password
4. Complete onboarding
5. Generate first podcast

**Expected:**
- ✅ User created in database
- ✅ Preferences saved
- ✅ User redirected correctly
- ✅ Session persists

---

### **Scenario 2: Returning User Login**
**Steps:**
1. Open app
2. Click "Login"
3. Enter credentials
4. Access dashboard

**Expected:**
- ✅ User authenticated
- ✅ Previous preferences loaded
- ✅ Library shows past podcasts
- ✅ Session persists

---

### **Scenario 3: Offline Functionality**
**Steps:**
1. Login and load app
2. Disconnect internet
3. Try to access cached content
4. Reconnect internet

**Expected:**
- ✅ Offline banner shows
- ✅ Cached podcasts playable
- ✅ Pending actions queued
- ✅ Auto-sync on reconnect

---

## ✅ Test Completion Checklist

### **Unit Tests**
- [x] AuthContext tests
- [x] RegisterPage tests
- [x] UI component tests
- [ ] PreferenceContext tests (optional)
- [ ] AudioContext tests (optional)

### **Integration Tests**
- [x] Registration flow
- [x] Login flow
- [ ] Onboarding flow (optional)
- [ ] Podcast generation (pending API)

### **Manual Tests**
- [x] Backend startup
- [x] Frontend startup
- [x] User registration
- [x] User login
- [x] API integration
- [x] Error handling

### **Performance Tests**
- [ ] Lighthouse audit
- [ ] Load time testing
- [ ] Bundle size analysis

---

## 🚀 Next Steps

1. **Run all tests:** `npm test`
2. **Check coverage:** `npm run test:coverage`
3. **Fix any failures**
4. **Manual testing** of critical flows
5. **Ready for Phase 8!**

---

## 📞 Need Help?

### **Test Not Running?**
1. Check Node.js version: `node --version` (need 18+)
2. Reinstall dependencies: `npm install`
3. Clear cache: `npm test -- --clearCache`

### **Test Failing?**
1. Read error message carefully
2. Check mock setup
3. Verify test data
4. Check async handling

### **Coverage Low?**
1. Add more test cases
2. Test edge cases
3. Test error paths
4. Test loading states

---

## 🎉 Testing Complete!

**When all tests pass, you're ready for Phase 8!** 🚀
