# 🗄️ Supabase PostgreSQL Setup Guide

## 📋 Step-by-Step Setup

### **Step 1: Create Supabase Account**

1. Go to **https://supabase.com**
2. Click **"Start your project"**
3. Sign up with GitHub (recommended) or email
4. Verify your email

---

### **Step 2: Create New Project**

1. Click **"New Project"**
2. Fill in details:
   - **Name:** `podcast-creator`
   - **Database Password:** Generate a strong password (SAVE THIS!)
   - **Region:** Choose closest to you (e.g., `US East` or `EU West`)
   - **Pricing Plan:** Free tier (500MB database)

3. Click **"Create new project"**
4. Wait 2-3 minutes for setup

---

### **Step 3: Get Connection Details**

1. Go to **Settings** (gear icon in sidebar)
2. Click **"Database"**
3. Scroll to **"Connection string"**
4. Copy the **"URI"** format:

```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```
postgresql://postgres:Abush11!@db.apfgwhphocgflatqmbcd.supabase.co:5432/postgres
5. Replace `[YOUR-PASSWORD]` with the password you created

**Example:**
```
postgresql://postgres:MySecurePass123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

---

### **Step 4: Get API Keys**

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL:** `https://[PROJECT-REF].supabase.co`
   - **anon public key:** (long string starting with `eyJ...`)
   - **service_role key:** (long string starting with `eyJ...`)

---

### **Step 5: Update Backend Environment**

Create/update `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Supabase (optional, for future features)
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_KEY=[YOUR-SERVICE-KEY]

# Existing keys (keep these)
PERPLEXITY_API_KEY=your_perplexity_key
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
```

---

### **Step 6: Update Database Configuration**

The code is already updated! Just need to:

1. **Install PostgreSQL driver:**
```bash
cd backend
pip install asyncpg
```

2. **Update `backend/app/db/base.py`** to use PostgreSQL config:

```python
# Change this line
from app.db.postgresql import engine, AsyncSessionLocal, Base, get_db, init_db, close_db
```

---

### **Step 7: Run Migrations**

```bash
cd backend

# Create initial migration
alembic revision --autogenerate -m "Initial PostgreSQL migration"

# Apply migration
alembic upgrade head
```

---

### **Step 8: Test Connection**

```bash
cd backend
python -c "
import asyncio
from app.db.postgresql import check_db_connection

async def test():
    result = await check_db_connection()
    print(f'Connection: {'✅ Success' if result else '❌ Failed'}')

asyncio.run(test())
"
```

Expected output:
```
✅ Connection: Success
```

---

### **Step 9: Start Backend**

```bash
cd backend
uvicorn app.main:app --reload
```

Check logs for:
```
✅ database_initialized | database: PostgreSQL
✅ Application started
```

---

### **Step 10: Test Full Flow**

1. **Generate a podcast** through the frontend
2. **Check Supabase dashboard:**
   - Go to **Table Editor**
   - You should see tables: `users`, `podcasts`, `user_preferences`
   - Click on `podcasts` table
   - You should see your generated podcast!

---

## 🎯 Verification Checklist

- [ ] Supabase project created
- [ ] Database password saved securely
- [ ] Connection string copied
- [ ] API keys copied
- [ ] `.env` file updated
- [ ] `asyncpg` installed
- [ ] Migrations run successfully
- [ ] Backend starts without errors
- [ ] Can generate podcasts
- [ ] Data appears in Supabase dashboard

---

## 🐛 Troubleshooting

### **Error: "could not connect to server"**
- Check your internet connection
- Verify the connection string is correct
- Check if password has special characters (URL encode them)

### **Error: "password authentication failed"**
- Double-check your database password
- Reset password in Supabase dashboard if needed

### **Error: "SSL connection required"**
- Add `?sslmode=require` to connection string:
```
postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres?sslmode=require
```

### **Migrations fail**
- Drop all tables in Supabase dashboard
- Run migrations again
- Or use: `alembic downgrade base` then `alembic upgrade head`

---

## 📊 Monitoring Your Database

### **Supabase Dashboard:**

1. **Database** → View tables and data
2. **SQL Editor** → Run custom queries
3. **Logs** → View database logs
4. **Reports** → See usage statistics

### **Useful Queries:**

**Check podcast count:**
```sql
SELECT COUNT(*) FROM podcasts;
```

**View recent podcasts:**
```sql
SELECT id, title, status, created_at 
FROM podcasts 
ORDER BY created_at DESC 
LIMIT 10;
```

**Check database size:**
```sql
SELECT pg_size_pretty(pg_database_size('postgres'));
```

---

## 🎉 You're Done!

Your app is now using production-ready PostgreSQL!

**Benefits:**
- ✅ No more locking issues
- ✅ True concurrent access
- ✅ Better performance
- ✅ Scalable
- ✅ Automatic backups

**Next Steps:**
1. Test thoroughly
2. Set up comprehensive testing
3. Deploy to cloud
4. Celebrate! 🎊
