# 🧪 Testing Guide with Structured Logging

## ✅ What's New

### **Structured Log Files:**
- ✅ Auto-creates timestamped log files in `backend/logs/`
- ✅ Keeps only last 5 log files (auto-cleanup)
- ✅ Clear step-by-step progress tracking
- ✅ Easy-to-read format with sections
- ✅ Highlights errors and successes

---

## 🚀 Step 1: Start Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**You'll see:**
```
📝 Logging to: C:\Users\burik\podcastCreator2\backend\logs\podcast_generation_20251016_073000.log
📂 View logs at: C:\Users\burik\podcastCreator2\backend\logs
```

---

## 🎯 Step 2: Generate Test Podcast

1. Go to http://localhost:5173
2. Login
3. Generate podcast for **"Tokyo, Japan"**
4. Watch it process

---

## 📊 Step 3: View Logs

### **Option A: View in Real-Time**
```bash
# In a new terminal
cd backend
python view_logs.py
```

### **Option B: Open Log File Directly**
```bash
# Open in your editor
code logs/podcast_generation_*.log
```

---

## 🔍 What to Look For

### **Successful Generation:**
```
================================================================================
  PODCAST GENERATION: Tokyo, Japan
================================================================================

STEP 1: Gathering content from Wikipedia and Location services [RUNNING]
STEP 1: Content gathering complete [DONE]

STEP 2: Generating podcast script with Perplexity AI [RUNNING]
STEP 2: Script generation complete [DONE]

STEP 3: Extracting script details and metadata [RUNNING]
STEP 3: Script extracted: Discover Tokyo, Japan [DONE]

STEP 4: Preparing audio generation (skipped for now) [RUNNING]
STEP 4: Audio preparation complete [DONE]

STEP 5: Finalizing podcast [RUNNING]
STEP 5: Podcast generation COMPLETE! [DONE]

================================================================================
  SUCCESS: Discover Tokyo, Japan
================================================================================
```

### **If There's an Error:**
```
================================================================================
  ERROR: Podcast Generation Failed
================================================================================

ERROR | podcast_generation_failed | error: "No script in generation result"
ERROR | full_traceback | [Full stack trace here]

================================================================================
  FAILED: No script in generation result
================================================================================
```

---

## 🐛 Debugging Process

### **1. Check Progress:**
Look for the last completed STEP:
- **STEP 1 DONE** → Content gathering worked
- **STEP 2 DONE** → Script generation worked
- **STEP 3 DONE** → Script extraction worked
- **STEP 4 DONE** → Audio prep worked
- **STEP 5 DONE** → Complete success!

### **2. Find Errors:**
Search for:
- `ERROR` - Critical errors
- `FAILED` - Failed operations
- `traceback` - Full error details

### **3. Check API Calls:**
Look for:
- `wikipedia_fetch_complete` - Wikipedia worked
- `location_fetch_complete` - Location service worked
- `perplexity_generation_complete` - Perplexity worked

---

## 📋 Common Issues & Solutions

### **Issue 1: Stuck at STEP 1**
**Symptom:** Never reaches "Content gathering complete"

**Check:**
- Wikipedia API connection
- Internet connectivity
- Location name spelling

**Solution:** Check logs for `wikipedia_fetch_failed` or `location_fetch_failed`

---

### **Issue 2: Stuck at STEP 2**
**Symptom:** Never reaches "Script generation complete"

**Check:**
- Perplexity API key
- API rate limits
- Network timeout

**Solution:** Look for `perplexity_generation_failed` in logs

---

### **Issue 3: Stuck at STEP 3**
**Symptom:** Script generation completes but extraction fails

**Check:**
- Script object structure
- Missing attributes

**Solution:** Look for "No script in result" error

---

### **Issue 4: Frontend Shows 0%**
**Symptom:** Backend progresses but frontend stuck

**Check:**
- CORS settings
- Frontend polling interval
- API endpoint connectivity

**Solution:** Check browser console for API errors

---

## 🎯 Test Checklist

Run through this checklist:

- [ ] Backend starts without errors
- [ ] Log file is created in `backend/logs/`
- [ ] Can generate podcast from frontend
- [ ] Logs show STEP 1 complete
- [ ] Logs show STEP 2 complete
- [ ] Logs show STEP 3 complete
- [ ] Logs show STEP 4 complete
- [ ] Logs show STEP 5 complete
- [ ] Logs show SUCCESS section
- [ ] Frontend shows 100% progress
- [ ] Can view podcast in library

---

## 📤 Sharing Logs

If you need to share logs with me:

```bash
cd backend
python view_logs.py > test_results.txt
```

Then paste the contents of `test_results.txt`

---

## 🧹 Clean Up Old Logs

Logs auto-clean (keeps last 5), but you can manually clean:

```bash
cd backend/logs
del podcast_generation_*.log
```

---

## 🚀 Ready to Test!

1. **Start backend** - Watch for log file path
2. **Generate podcast** - Use "Tokyo, Japan"
3. **View logs** - Run `python view_logs.py`
4. **Check results** - Look for SUCCESS or ERROR sections

**Let me know what you see in the logs!** 📝
