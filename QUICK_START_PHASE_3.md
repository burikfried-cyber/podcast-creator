# 🚀 Quick Start - Phase 3 Audio Generation

## Install Google Cloud TTS

```bash
cd backend
pip install google-cloud-texttospeech
```

---

## Setup Google Cloud (5 minutes)

### 1. Go to Google Cloud Console
https://console.cloud.google.com/

### 2. Create Project
- Click "New Project"
- Name: "podcast-creator"
- Click "Create"

### 3. Enable Text-to-Speech API
- Go to "APIs & Services" → "Library"
- Search "Cloud Text-to-Speech API"
- Click "Enable"

### 4. Create Service Account
- Go to "IAM & Admin" → "Service Accounts"
- Click "Create Service Account"
- Name: `podcast-tts-service`
- Role: "Cloud Text-to-Speech User"
- Click "Done"

### 5. Download Key
- Click on service account
- Go to "Keys" tab
- Click "Add Key" → "Create new key"
- Select "JSON"
- Click "Create"
- **Save the downloaded file!**

---

## Configure Credentials

### Windows (PowerShell)
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your-key.json"
```

### Linux/Mac
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"
```

### Or add to .env file
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json
AUDIO_STORAGE_PATH=/tmp/podcast_audio
```

---

## Test It!

```bash
cd backend
python test_audio_generation.py
```

Expected output:
```
============================================================
PHASE 3: AUDIO GENERATION TEST SUITE
============================================================

TEST 0: Google Cloud TTS Availability
PASS: Google TTS is available and configured

TEST 1: Cost Estimation
PASS: Cost estimation working correctly

TEST 2: Audio Synthesis - Free Tier
PASS: Free tier audio synthesis successful

TEST 3: Audio Synthesis - Premium Tier
PASS: Premium tier audio synthesis successful

TEST 4: Full Audio Generation Pipeline
PASS: Full audio generation pipeline successful

TEST 5: Storage Statistics
PASS: Storage statistics retrieved

============================================================
ALL TESTS PASSED!
============================================================
```

---

## Usage

Audio generation is **automatic** when creating podcasts!

```python
# Just create a podcast as usual
POST /api/v1/podcasts/generate
{
    "location": "Paris, France",
    "podcast_type": "location"
}

# Audio will be generated automatically!
# Response includes:
{
    "audio_url": "/audio/podcast_xxx.mp3",
    "duration_seconds": 600
}
```

---

## Pricing (Don't Worry - It's Cheap!)

### Free Tier (per month)
- **Standard voices:** 4 million characters FREE
- **Neural voices:** 1 million characters FREE

### Cost per 10-minute podcast
- **Free tier:** $0.03 (3 cents)
- **Premium tier:** $0.12 (12 cents)

### Free tier covers
- **100-250 podcasts per month for FREE!**

---

## Troubleshooting

### "Google TTS not available"
```bash
pip install google-cloud-texttospeech
```

### "Client not initialized"
```bash
# Set credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\key.json"
```

### "API not enabled"
- Go to Google Cloud Console
- Enable "Cloud Text-to-Speech API"

---

## What You Get

✅ High-quality MP3 audio files  
✅ Natural-sounding voices (Neural2)  
✅ Automatic duration calculation  
✅ Cost tracking  
✅ Graceful error handling  
✅ Free tier covers 100+ podcasts/month  

---

## Files Created

- `backend/app/services/audio/google_tts_service.py` - TTS integration
- `backend/app/services/audio/audio_service.py` - Audio management
- `backend/test_audio_generation.py` - Test suite

---

## Next Steps

1. ✅ Install library
2. ✅ Setup Google Cloud
3. ✅ Configure credentials
4. ✅ Test audio generation
5. 🚀 **Start creating podcasts with audio!**

---

**That's it! Audio generation is ready!** 🎙️🔊
