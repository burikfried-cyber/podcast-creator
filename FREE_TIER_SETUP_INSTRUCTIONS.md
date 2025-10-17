# 🆓 FREE Tier Setup Instructions

## ✅ What I've Done So Far

### **1. Created Content Services:**
- ✅ `WikipediaService` - Fetches real facts (FREE)
- ✅ `LocationService` - Gets location data (FREE)
- ✅ `LLMService` - Generates content with Ollama (FREE)

### **2. Updated Narrative Engine:**
- ✅ Fetches real Wikipedia content
- ✅ Fetches location details
- ✅ Uses LLM for hooks and conclusions
- ✅ Integrates real facts into narratives

### **3. Installing Dependencies:**
- ⏳ Running: `pip install wikipedia geopy ollama TTS pydub soundfile`

---

## 🔧 What You Need to Do

### **Step 1: Install Ollama** (5 minutes)

**Download & Install:**
1. Go to: https://ollama.ai/download
2. Download Windows installer
3. Run the installer
4. Open a new terminal

**Pull the model:**
```bash
ollama pull llama3
```

**Verify:**
```bash
ollama list
# Should show: llama3
```

**Test it:**
```bash
ollama run llama3 "Tell me about Paris in 2 sentences"
```

You should see a response! This means Ollama is working.

---

### **Step 2: Verify Python Dependencies**

After the pip install completes, verify:

```bash
cd backend
python -c "import wikipedia; print('Wikipedia OK')"
python -c "import geopy; print('Geopy OK')"
python -c "import ollama; print('Ollama OK')"
```

All should print "OK".

---

### **Step 3: Create Storage Directory**

```bash
mkdir -p backend/storage/podcasts
```

---

### **Step 4: Update Environment Variables**

**File:** `backend/.env`

Add these lines:
```bash
# LLM Configuration
USE_OPENAI=false
OLLAMA_MODEL=llama3

# TTS Configuration  
USE_ELEVENLABS=false

# Storage
AUDIO_STORAGE_PATH=./storage/podcasts
```

---

## 🚀 What Happens Next

### **When You Generate a Podcast:**

**1. Content Fetching (5-10 seconds):**
- ✅ Fetches Wikipedia article about location
- ✅ Extracts interesting facts
- ✅ Gets location coordinates and details
- ✅ Logs: "real_content_fetched"

**2. Narrative Generation (20-30 seconds):**
- ✅ Ollama generates engaging hook
- ✅ Creates story structure with real facts
- ✅ Generates compelling conclusion
- ✅ Logs: "narrative_construction_complete"

**3. Script Assembly (5-10 seconds):**
- ✅ Assembles complete script
- ✅ Adds transitions
- ✅ Optimizes for speech
- ✅ Logs: "script_assembly_complete"

**4. Quality Check (2-3 seconds):**
- ✅ Validates content quality
- ✅ Checks engagement score
- ✅ Logs: "quality_check_complete"

**Total Time: 30-50 seconds** (much more realistic!)

---

## 📊 What You'll Get

### **Script Quality:**
- ✅ Real facts from Wikipedia
- ✅ Actual location information
- ✅ AI-generated narrative (Ollama)
- ✅ Engaging storytelling
- ✅ 1500-2000 words

### **Example Output:**
```
Title: Discover Paris, France

Hook: "What if I told you that Paris, the City of Light, 
holds secrets that have shaped Western civilization for 
over two millennia?"

Content: [Real facts from Wikipedia about Paris's history, 
culture, landmarks, and significance]

Conclusion: "From its Roman origins to its modern-day 
splendor, Paris continues to inspire millions..."
```

---

## 🎵 Audio Generation (Coming Next)

After we test content generation, I'll add:

### **FREE Option: Coqui TTS**
- ✅ Open source
- ✅ Runs locally
- ✅ Decent quality
- ✅ $0 cost

### **Implementation:**
```python
from TTS.api import TTS

tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text=script, file_path="podcast.wav")
```

---

## 🧪 Testing Plan

### **Step 1: Test Content Fetching**
```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Watch logs for:
# - "fetching_real_content"
# - "real_content_fetched"
# - "narrative_construction_complete"
```

### **Step 2: Generate Test Podcast**
1. Go to http://localhost:5173
2. Login
3. Click "Generate"
4. Enter "Tokyo, Japan"
5. Click "Generate Podcast"
6. **Watch the logs!**

### **Expected Logs:**
```
INFO: fetching_real_content location="Tokyo, Japan"
INFO: real_content_fetched title="Tokyo" facts_count=10
INFO: generating_with_ollama model="llama3"
INFO: ollama_generation_complete length=2500
INFO: narrative_construction_complete
INFO: script_assembly_complete
INFO: quality_check_complete
INFO: podcast_generation_complete
```

### **Expected Duration:**
- ⏱️ 30-50 seconds (realistic!)
- Not <1 second like before

---

## ⚠️ Troubleshooting

### **If Ollama fails:**
```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve

# Then pull model again
ollama pull llama3
```

### **If Wikipedia fails:**
```python
# Test manually
python
>>> import wikipedia
>>> page = wikipedia.page("Paris")
>>> print(page.summary[:200])
```

### **If generation is still too fast:**
- Check logs for "generating_with_ollama"
- If missing, Ollama isn't being called
- Verify `USE_OPENAI=false` in .env

---

## 📈 Quality Comparison

### **Before (Placeholder Content):**
```
Hook: "What if I told you that Paris, France holds a mystery..."
Content: [Generic template text]
Duration: <1 second
Quality: ⭐⭐ (placeholder)
```

### **After (Real Content + Ollama):**
```
Hook: "In the heart of Europe lies a city that has witnessed 
revolutions, inspired artists, and defined romance for centuries..."
Content: [Real Wikipedia facts + AI narrative]
Duration: 30-50 seconds
Quality: ⭐⭐⭐⭐ (good, engaging)
```

---

## 🎯 Success Criteria

**You'll know it's working when:**
1. ✅ Generation takes 30-50 seconds (not <1 second)
2. ✅ Script contains real facts about the location
3. ✅ Content is engaging and well-written
4. ✅ Logs show "generating_with_ollama"
5. ✅ Script is 1500-2000 words

---

## 🚀 Next Steps After Testing

1. **Test content generation** with FREE tier
2. **Add Coqui TTS** for audio (also FREE)
3. **Test end-to-end** flow
4. **Optionally upgrade** to paid services if desired

---

## 💡 Pro Tips

### **Speed Up Ollama:**
- Use smaller model: `ollama pull phi` (faster, less quality)
- Use GPU if available (automatic)
- Reduce max_tokens in LLM service

### **Improve Quality:**
- Use larger model: `ollama pull llama3:70b` (slower, better quality)
- Adjust temperature in LLM service
- Add more Wikipedia facts

### **Save Money:**
- Stay on FREE tier for testing
- Only upgrade to paid when ready for production
- Mix & match: FREE content + PAID audio

---

## ✅ Ready to Test!

**Once Ollama is installed:**
1. Verify it's working: `ollama run llama3 "test"`
2. Start backend: `uvicorn app.main:app --reload`
3. Generate a podcast
4. **Watch the magic happen!** ✨

**Let me know when Ollama is installed and I'll help you test!** 🚀
