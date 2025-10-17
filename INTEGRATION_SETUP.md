##🚀 Full Integration Setup Guide

## 📦 Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- ✅ Wikipedia (FREE)
- ✅ Geopy/Nominatim (FREE)
- ✅ Ollama client (FREE)
- ✅ OpenAI client (PAID - optional)
- ✅ Coqui TTS (FREE)
- ✅ ElevenLabs (PAID - optional)

---

## 🆓 Step 2: Setup FREE Tier (Ollama)

### **Install Ollama** (Local LLM - FREE)

**Windows:**
1. Download from: https://ollama.ai/download
2. Run installer
3. Open terminal and run:
```bash
ollama pull llama3
```

**Verify installation:**
```bash
ollama list
# Should show: llama3
```

**Test it:**
```bash
ollama run llama3 "Tell me about Paris"
```

---

## 💰 Step 3: Setup PAID Tier (Optional - Better Quality)

### **OpenAI API Key** (PAID - ~$0.10 per podcast)

1. Go to: https://platform.openai.com/api-keys
2. Create account & add payment method
3. Create API key
4. Add to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
USE_OPENAI=true
```

### **ElevenLabs API Key** (PAID - ~$4.50 per podcast)

1. Go to: https://elevenlabs.io
2. Sign up & get API key
3. Add to `.env`:
```bash
ELEVENLABS_API_KEY=your-key-here
USE_ELEVENLABS=true
```

---

## ⚙️ Step 4: Update Environment Variables

**File:** `backend/.env`

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./podcast_creator.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Configuration
USE_OPENAI=false  # Set to true to use OpenAI instead of Ollama
OPENAI_API_KEY=  # Only needed if USE_OPENAI=true

# TTS Configuration
USE_ELEVENLABS=false  # Set to true to use ElevenLabs instead of Coqui
ELEVENLABS_API_KEY=  # Only needed if USE_ELEVENLABS=true

# Storage
AUDIO_STORAGE_PATH=./storage/podcasts
```

---

## 🔧 Step 5: Update Narrative Engine

I'll update the narrative engine to use real content now.

---

## 📊 Comparison: FREE vs PAID

### **Content Generation:**

| Feature | FREE (Ollama) | PAID (OpenAI) |
|---------|---------------|---------------|
| Quality | Good | Excellent |
| Speed | 20-30 sec | 5-10 sec |
| Cost | $0 | ~$0.10 |
| Offline | ✅ Yes | ❌ No |

### **Audio Generation:**

| Feature | FREE (Coqui) | PAID (ElevenLabs) |
|---------|--------------|-------------------|
| Quality | Decent | Excellent |
| Speed | 30-40 sec | 10-20 sec |
| Cost | $0 | ~$4.50 |
| Voices | Limited | 100+ |

### **Total Cost Per Podcast:**

- **FREE Tier:** $0
- **PAID Tier:** ~$4.60

---

## 🎯 Recommended Setup for Testing

**Use FREE tier:**
- ✅ Wikipedia (always free)
- ✅ Geopy (always free)
- ✅ Ollama (free, runs locally)
- ✅ Coqui TTS (free, runs locally)

**Result:**
- Fully functional app
- $0 cost
- Slightly slower generation (60-90 seconds)
- Good quality content & audio

---

## 🚀 Upgrade Path

**Start FREE, then upgrade:**

1. **Test with FREE tier** - Make sure everything works
2. **Try OpenAI** - Better content quality (~$0.10/podcast)
3. **Try ElevenLabs** - Better audio quality (~$4.50/podcast)
4. **Mix & Match** - Use OpenAI + Coqui TTS, or Ollama + ElevenLabs

---

## ⚡ Quick Start Commands

### **FREE Tier (Recommended for Testing):**
```bash
# 1. Install Ollama
# Download from https://ollama.ai/download

# 2. Pull model
ollama pull llama3

# 3. Install Python deps
cd backend
pip install -r requirements.txt

# 4. Set environment
echo "USE_OPENAI=false" >> .env
echo "USE_ELEVENLABS=false" >> .env

# 5. Start backend
uvicorn app.main:app --reload

# 6. Test generation!
```

### **PAID Tier (Better Quality):**
```bash
# 1. Get API keys
# OpenAI: https://platform.openai.com/api-keys
# ElevenLabs: https://elevenlabs.io

# 2. Set environment
echo "USE_OPENAI=true" >> .env
echo "OPENAI_API_KEY=sk-your-key" >> .env
echo "USE_ELEVENLABS=true" >> .env
echo "ELEVENLABS_API_KEY=your-key" >> .env

# 3. Start backend
uvicorn app.main:app --reload

# 4. Test generation!
```

---

## 📝 Next Steps

After setup, I'll:
1. ✅ Update narrative engine to fetch real content
2. ✅ Integrate LLM for content generation
3. ✅ Add TTS for audio generation
4. ✅ Update progress tracking
5. ✅ Test end-to-end flow

**Ready to proceed?** Let me know which tier you want to use! 🚀
