# 🚀 Complete Production Deployment Guide

## 📋 Overview

Deploy your podcast creator to production with PostgreSQL, Railway, and Vercel.

---

## 🎯 Phase 1: Database Setup (Supabase PostgreSQL)

### **Step 1: Create Supabase Project**

1. Go to **https://supabase.com** → Sign up
2. Create new project:
   - Name: `podcast-creator`
   - Password: Generate strong password (SAVE IT!)
   - Region: Choose closest to your users
   - Plan: Free tier

3. Wait 2-3 minutes for setup

### **Step 2: Get Connection String**

1. Go to **Settings** → **Database**
2. Copy **Connection string** (URI format)
3. Replace `[YOUR-PASSWORD]` with your password

Example:
```
postgresql://postgres:YourPass123@db.abc123.supabase.co:5432/postgres
```

### **Step 3: Test Locally**

Update `backend/.env`:
```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
```

Install PostgreSQL driver:
```bash
cd backend
pip install asyncpg
```

Start backend:
```bash
uvicorn app.main:app --reload
```

Check logs for:
```
✅ using_postgresql_database
✅ database_engine_created | type: PostgreSQL
```

---

## 🧪 Phase 2: Run Tests

### **Install Test Dependencies**

```bash
cd backend
pip install pytest pytest-asyncio httpx
```

### **Run Complete Test Suite**

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_complete_generation.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### **Expected Output**

```
tests/test_complete_generation.py::test_complete_podcast_generation_flow PASSED
tests/test_complete_generation.py::test_concurrent_podcast_generation PASSED
tests/test_complete_generation.py::test_podcast_script_quality PASSED
tests/test_complete_generation.py::test_library_pagination PASSED
tests/test_complete_generation.py::test_error_handling PASSED
tests/test_complete_generation.py::test_database_performance PASSED

======================== 6 passed in 180.23s ========================
```

### **Fix Any Failures**

If tests fail:
1. Check database connection
2. Verify API keys are set
3. Check logs for errors
4. Fix issues before deploying

---

## ☁️ Phase 3: Deploy Backend (Railway)

### **Step 1: Prepare for Deployment**

Create `backend/Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Create `backend/railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### **Step 2: Deploy to Railway**

1. Go to **https://railway.app** → Sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Select `backend` folder as root

### **Step 3: Set Environment Variables**

In Railway dashboard, go to **Variables** and add:

```bash
# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# API Keys
PERPLEXITY_API_KEY=your_perplexity_key
OPENAI_API_KEY=your_openai_key

# Security
SECRET_KEY=your_secret_key_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Config
DEBUG=false
ENVIRONMENT=production

# CORS (update after frontend deployment)
CORS_ORIGINS=https://your-frontend.vercel.app
```

### **Step 4: Deploy**

1. Railway will auto-deploy
2. Wait for build to complete (2-3 minutes)
3. Get your backend URL: `https://your-app.railway.app`

### **Step 5: Test Deployed Backend**

```bash
# Health check
curl https://your-app.railway.app/health

# Expected response
{"status":"healthy","database":"connected"}
```

---

## 🌐 Phase 4: Deploy Frontend (Vercel)

### **Step 1: Update API URL**

Update `frontend/.env.production`:
```bash
VITE_API_URL=https://your-app.railway.app/api/v1
```

### **Step 2: Deploy to Vercel**

1. Go to **https://vercel.com** → Sign up with GitHub
2. Click **"Add New Project"**
3. Import your repository
4. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### **Step 3: Set Environment Variables**

In Vercel dashboard, go to **Settings** → **Environment Variables**:

```bash
VITE_API_URL=https://your-app.railway.app/api/v1
```

### **Step 4: Deploy**

1. Click **"Deploy"**
2. Wait for build (1-2 minutes)
3. Get your URL: `https://your-app.vercel.app`

### **Step 5: Update CORS**

Go back to Railway and update `CORS_ORIGINS`:
```bash
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

Redeploy backend.

---

## ✅ Phase 5: Verification

### **Test Complete Flow**

1. **Open frontend:** `https://your-app.vercel.app`
2. **Sign up / Log in**
3. **Generate podcast:** "Tokyo, Japan"
4. **Watch progress:** Should update in real-time
5. **Check library:** Should load quickly
6. **Verify script:** Should have real content (not templates)

### **Check Logs**

**Railway (Backend):**
- Go to **Deployments** → **View Logs**
- Look for errors

**Vercel (Frontend):**
- Go to **Deployments** → **View Function Logs**
- Check for API errors

**Supabase (Database):**
- Go to **Database** → **Table Editor**
- Verify data is being created

---

## 📊 Phase 6: Monitoring

### **Set Up Sentry (Error Tracking)**

1. Go to **https://sentry.io** → Sign up
2. Create new project → **FastAPI**
3. Get DSN

Update Railway environment:
```bash
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

Add to `backend/app/main.py`:
```python
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,
)
```

### **Monitor Performance**

**Railway Metrics:**
- CPU usage
- Memory usage
- Request rate
- Response time

**Supabase Metrics:**
- Database size
- Query performance
- Connection count

**Vercel Analytics:**
- Page views
- Load time
- User geography

---

## 🎯 Phase 7: Optimization

### **Backend Optimization**

1. **Enable caching:**
   - Add Redis (Railway add-on)
   - Cache Wikipedia/Location API responses

2. **Optimize queries:**
   - Add database indexes
   - Use connection pooling

3. **Rate limiting:**
   - Implement per-user rate limits
   - Prevent abuse

### **Frontend Optimization**

1. **Code splitting:**
   - Lazy load routes
   - Reduce bundle size

2. **Image optimization:**
   - Use WebP format
   - Lazy load images

3. **Caching:**
   - Service worker
   - Cache API responses

---

## 💰 Cost Breakdown

### **Free Tier (Testing):**
- Supabase: Free (500MB)
- Railway: $5 credit/month
- Vercel: Free
- **Total: ~$0-5/month**

### **Production (Paid):**
- Supabase Pro: $25/month (8GB)
- Railway: $10-20/month
- Vercel Pro: $20/month (optional)
- **Total: $35-65/month**

---

## 🐛 Troubleshooting

### **Backend won't start**
- Check environment variables
- Verify database connection
- Check Railway logs

### **Frontend can't connect**
- Verify API URL is correct
- Check CORS settings
- Check network tab in browser

### **Database errors**
- Check connection string
- Verify Supabase is running
- Check connection pool settings

### **Slow performance**
- Check database query times
- Monitor Railway metrics
- Optimize slow endpoints

---

## 🎉 You're Live!

Your podcast creator is now deployed and ready for users!

### **Next Steps:**

1. **Share with beta testers**
2. **Collect feedback**
3. **Monitor errors and performance**
4. **Iterate based on feedback**
5. **Add new features**

### **Useful Commands:**

```bash
# View Railway logs
railway logs

# Redeploy backend
git push origin main

# Redeploy frontend
git push origin main

# Run migrations
railway run alembic upgrade head

# Check database
railway run python -c "from app.db.base import check_db_connection; import asyncio; asyncio.run(check_db_connection())"
```

---

## 📚 Resources

- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs
- **Supabase Docs:** https://supabase.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **PostgreSQL Docs:** https://www.postgresql.org/docs

---

**Congratulations! Your app is production-ready! 🚀**
