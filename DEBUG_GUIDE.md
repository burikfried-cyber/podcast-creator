# 🐛 Debug Guide - Podcast Generation

## 🔍 Current Situation

**Backend:** ✅ Working - Generates podcasts successfully  
**Frontend:** ⚠️ Shows 0% progress but podcast completes  
**Script:** ✅ Generated and saved to database  
**Audio:** ❌ Not generated yet (coming soon)

---

## 📊 What's Actually Happening

### **Backend (Working):**
1. ✅ Receives generation request
2. ✅ Fetches Wikipedia content (20-30s)
3. ✅ Fetches location data (2-3s)
4. ✅ Generates script with Perplexity (20-30s)
5. ✅ Saves to database with status='completed'
6. ✅ Script content is saved (800-1000 characters)

### **Frontend (Issue):**
1. ⚠️ Shows 0% during generation
2. ✅ Podcast appears in library when complete
3. ⚠️ May show "template" data initially
4. ✅ Script should be visible on podcast page

---

## 🧪 Testing Steps

### **Step 1: Check Backend Logs**

```bash
cd backend
python view_logs.py
```

**Look for:**
```
✅ STEP 1: Content gathering complete [DONE]
✅ STEP 2: Script generation complete [DONE]
✅ STEP 3: Script extracted [DONE]
✅ STEP 4: Audio preparation complete [DONE]
✅ STEP 5: Podcast generation COMPLETE! [DONE]
✅ SUCCESS: Discover [Location Name]
```

**If you see all 5 steps DONE:** Backend is working! ✅

---

### **Step 2: Check Database**

```bash
cd backend
python -c "import sqlite3; conn = sqlite3.connect('podcast_generator.db'); cursor = conn.cursor(); cursor.execute('SELECT id, title, status, progress_percentage, LENGTH(script_content) FROM podcasts ORDER BY created_at DESC LIMIT 3'); print('\\n'.join([str(row) for row in cursor.fetchall()]))"
```

**Expected Output:**
```
('podcast-id', 'Discover Tokyo, Japan', 'completed', 100, 889)
```

**Check:**
- ✅ status = 'completed' (lowercase!)
- ✅ progress_percentage = 100
- ✅ script_content length > 0

---

### **Step 3: Check API Response**

**Open browser console and generate a podcast:**

1. Open DevTools (F12)
2. Go to Network tab
3. Generate a podcast
4. Find the GET request to `/api/v1/podcasts/{id}`
5. Check the response

**Expected Response:**
```json
{
  "id": "...",
  "title": "Discover Tokyo, Japan",
  "description": "...",
  "script_content": "Welcome to Tokyo...",  // Should have content!
  "audio_url": null,  // OK - not generated yet
  "status": "completed",
  "progress_percentage": 100
}
```

**If script_content is null or empty:** Backend issue ❌  
**If script_content has text:** Frontend issue ⚠️

---

### **Step 4: Check Frontend Console**

**After opening a podcast, check console for:**

```
📻 Podcast Data Received: {
  id: "...",
  title: "Discover Tokyo, Japan",
  hasScript: true,  // Should be true!
  scriptLength: 889,  // Should be > 0
  scriptPreview: "Welcome to Tokyo...",
  hasAudio: false,  // OK for now
  status: "completed"
}
```

**If hasScript is false:** API not returning script ❌  
**If hasScript is true:** Script should be visible on page ✅

---

## 🔧 Common Issues & Fixes

### **Issue 1: Frontend Shows 0% Forever**

**Cause:** Status polling not detecting completion

**Debug:**
1. Check browser console for errors
2. Check Network tab for status API calls
3. Look for status response

**Fix:**
- ✅ Already applied: Case-insensitive status check
- Restart frontend: `npm run dev`

---

### **Issue 2: Podcast Shows But No Script**

**Cause:** Script not being returned by API

**Debug:**
1. Check backend logs for "podcast_retrieved"
2. Look for `has_script: true` and `script_length: 889`
3. If false, check database directly

**Fix:**
```bash
# Check if script is in database
cd backend
python -c "import sqlite3; conn = sqlite3.connect('podcast_generator.db'); cursor = conn.cursor(); cursor.execute('SELECT id, title, LENGTH(script_content) FROM podcasts WHERE script_content IS NOT NULL'); print('\\n'.join([str(row) for row in cursor.fetchall()]))"
```

If script is in DB but not in API response:
- Check Pydantic schema includes script_content
- Check `from_orm` is working

---

### **Issue 3: Script Shows "Template" Content**

**Cause:** Old podcasts from before real generation was working

**Fix:**
```bash
# Delete old test podcasts
cd backend
python -c "import sqlite3; conn = sqlite3.connect('podcast_generator.db'); cursor = conn.cursor(); cursor.execute('DELETE FROM podcasts WHERE script_content IS NULL OR title IS NULL'); conn.commit(); print(f'Deleted {cursor.rowcount} incomplete podcasts')"
```

---

### **Issue 4: "Audio Not Available" Message**

**This is NORMAL!** ✅

Audio generation is not implemented yet. Users should see:
- ✅ Yellow banner: "Audio generation coming soon!"
- ✅ Script content below
- ✅ Can read the full script

---

## 📝 Enhanced Logging

### **Backend Logs Now Include:**

```json
{
  "event": "podcast_retrieved",
  "podcast_id": "...",
  "has_title": true,
  "has_script": true,
  "script_length": 889,
  "has_audio": false,
  "status": "completed"
}
```

### **Frontend Console Now Shows:**

```javascript
📻 Podcast Data Received: {
  id: "...",
  title: "Discover Tokyo, Japan",
  hasScript: true,
  scriptLength: 889,
  scriptPreview: "Welcome to Tokyo...",
  hasAudio: false,
  status: "completed"
}
```

---

## 🎯 Quick Diagnostic Checklist

Run through this checklist:

### **Backend:**
- [ ] Backend starts without errors
- [ ] Can generate podcast
- [ ] Logs show all 5 STEPS complete
- [ ] Logs show SUCCESS message
- [ ] Database has script_content
- [ ] API returns script in response

### **Frontend:**
- [ ] Can login
- [ ] Can start generation
- [ ] Podcast appears in library
- [ ] Can open podcast page
- [ ] Console shows podcast data
- [ ] Console shows hasScript: true
- [ ] Script is visible on page
- [ ] Yellow banner shows (no audio)

---

## 🚀 Next Test

1. **Restart both servers**
   ```bash
   # Backend
   cd backend
   uvicorn app.main:app --reload
   
   # Frontend
   cd frontend
   npm run dev
   ```

2. **Generate new podcast**
   - Use "Paris, France"
   - Wait 60-90 seconds
   - Don't stop servers!

3. **Check logs**
   ```bash
   cd backend
   python view_logs.py
   ```

4. **Open podcast**
   - Go to library
   - Click on podcast
   - Check console (F12)
   - Look for script content

5. **Report findings:**
   - Does console show hasScript: true?
   - Is script visible on page?
   - What does the script say?

---

## 📞 Debugging Commands

### **Check Latest Podcast:**
```bash
cd backend
python -c "import sqlite3; conn = sqlite3.connect('podcast_generator.db'); cursor = conn.cursor(); cursor.execute('SELECT id, title, status, LENGTH(script_content), audio_url FROM podcasts ORDER BY created_at DESC LIMIT 1'); print(cursor.fetchone())"
```

### **View Script Content:**
```bash
cd backend
python -c "import sqlite3; conn = sqlite3.connect('podcast_generator.db'); cursor = conn.cursor(); cursor.execute('SELECT script_content FROM podcasts ORDER BY created_at DESC LIMIT 1'); print(cursor.fetchone()[0][:500])"
```

### **Check All Completed Podcasts:**
```bash
cd backend
python -c "import sqlite3; conn = sqlite3.connect('podcast_generator.db'); cursor = conn.cursor(); cursor.execute('SELECT id, title, status FROM podcasts WHERE status = \"completed\"'); print('\\n'.join([str(row) for row in cursor.fetchall()]))"
```

---

## 🎉 Expected Final State

**When everything works:**

1. ✅ Generate podcast (60-90 seconds)
2. ✅ Appears in library with title
3. ✅ Click to open
4. ✅ See title and description
5. ✅ See yellow banner "Audio coming soon"
6. ✅ Scroll down to see full script
7. ✅ Script is real content about the location
8. ✅ Can read the entire narrative

**No audio yet - that's OK!** The script is the main deliverable for now.

---

## 🔄 If Still Having Issues

1. **Check backend logs:** `python view_logs.py`
2. **Check database:** Run diagnostic commands above
3. **Check frontend console:** Look for podcast data
4. **Share findings:** Tell me what you see!

The logging is now comprehensive enough to pinpoint exactly where the issue is! 🎯
