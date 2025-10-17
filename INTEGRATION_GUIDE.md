# 🔗 Complete Integration Guide

## 📋 Overview

This guide will help you fully integrate and test the Location Podcast Generator application.

---

## ✅ What We Just Added

### **New API Endpoints**
- `POST /api/v1/podcasts/generate` - Generate new podcast
- `GET /api/v1/podcasts/status/{job_id}` - Check generation status
- `GET /api/v1/podcasts/{id}` - Get podcast details
- `GET /api/v1/podcasts/` - List user's podcasts
- `DELETE /api/v1/podcasts/{id}` - Delete podcast
- `POST /api/v1/podcasts/{id}/regenerate` - Regenerate podcast

### **New Services**
- `PodcastService` - Business logic for podcast operations
- Integration with `PodcastGenerator` - Script generation

### **New Schemas**
- `PodcastCreate` - Request schema
- `PodcastResponse` - Response schema
- `GenerationStatusResponse` - Status tracking
- `PodcastListResponse` - List response

---

## 🧪 Testing the Integration

### **Step 1: Start the Backend**

```powershell
cd C:\Users\burik\podcastCreator2\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected:** Server starts on http://localhost:8000

---

### **Step 2: Test API Endpoints**

#### **A. Register a User**
```powershell
curl -X POST "http://localhost:8000/api/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true
}
```

---

#### **B. Login**
```powershell
curl -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

**Save the access_token** - you'll need it for authenticated requests!

---

#### **C. Generate a Podcast**
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

curl -X POST "http://localhost:8000/api/v1/podcasts/generate" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "location": "Paris, France",
    "podcast_type": "base",
    "preferences": {
      "surprise_tolerance": 2,
      "preferred_length": "medium"
    }
  }'
```

**Expected Response:**
```json
{
  "job_id": "1",
  "status": "processing",
  "message": "Podcast generation started",
  "podcast_id": 1,
  "progress": null
}
```

---

#### **D. Check Generation Status**
```powershell
curl -X GET "http://localhost:8000/api/v1/podcasts/status/1" `
  -H "Authorization: Bearer $token"
```

**Expected Response:**
```json
{
  "job_id": "1",
  "status": "completed",
  "message": "Generation in progress",
  "podcast_id": 1,
  "progress": 100
}
```

---

#### **E. Get Podcast Details**
```powershell
curl -X GET "http://localhost:8000/api/v1/podcasts/1" `
  -H "Authorization: Bearer $token"
```

**Expected Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "location": "Paris, France",
  "podcast_type": "base",
  "status": "completed",
  "title": "About Paris, France",
  "description": "Information about Paris, France",
  "script_content": "This is a podcast about Paris, France...",
  "audio_url": null,
  "duration_seconds": 180,
  "created_at": "2025-10-15T12:00:00",
  "completed_at": "2025-10-15T12:02:00"
}
```

---

#### **F. List All Podcasts**
```powershell
curl -X GET "http://localhost:8000/api/v1/podcasts/" `
  -H "Authorization: Bearer $token"
```

**Expected Response:**
```json
{
  "podcasts": [...],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

### **Step 3: Test with Frontend**

#### **Start Frontend**
```powershell
cd C:\Users\burik\podcastCreator2\frontend
npm run dev
```

#### **Test User Flow**
1. Open http://localhost:5173
2. Register/Login
3. Go to "Generate Podcast" page
4. Enter location: "Paris, France"
5. Click "Generate"
6. Watch status update
7. View completed podcast

---

## 🔌 What's Still Missing

### **1. Content Gathering Integration** ⚠️

**Current Status:** Using mock data  
**Need:** Real API integration

**APIs to Integrate:**
- **Wikipedia API** - Historical/cultural information
- **Google Places API** - Location details, photos
- **OpenWeatherMap API** - Weather data
- **News API** - Current events

**How to Add:**

Create `backend/app/services/content_gathering_service.py`:

```python
import aiohttp
from typing import Dict, Any

class ContentGatheringService:
    async def gather_location_content(self, location: str) -> Dict[str, Any]:
        # Wikipedia
        wiki_data = await self._fetch_wikipedia(location)
        
        # Google Places
        places_data = await self._fetch_google_places(location)
        
        # Combine data
        return {
            'location': location,
            'title': wiki_data.get('title'),
            'description': wiki_data.get('extract'),
            'content': wiki_data.get('content'),
            'places': places_data,
            'sources': ['wikipedia', 'google_places']
        }
    
    async def _fetch_wikipedia(self, location: str):
        # TODO: Implement Wikipedia API call
        pass
    
    async def _fetch_google_places(self, location: str):
        # TODO: Implement Google Places API call
        pass
```

---

### **2. Audio Generation Integration** ⚠️

**Current Status:** Not implemented  
**Need:** Text-to-speech integration

**Options:**
1. **ElevenLabs** (Best quality, paid)
2. **Azure Speech** (Good quality, Microsoft)
3. **Google Cloud TTS** (Good quality, Google)
4. **AWS Polly** (Good quality, Amazon)

**How to Add:**

Create `backend/app/services/audio_generation_service.py`:

```python
import aiohttp
from typing import str

class AudioGenerationService:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate_audio(self, text: str, voice: str = "default") -> str:
        # Call ElevenLabs or Azure Speech API
        # Return audio file URL
        pass
```

---

### **3. Frontend Integration** ⚠️

**Need:** Connect frontend to new podcast endpoints

**Files to Update:**
- `frontend/src/services/api.ts` - Add podcast API calls
- `frontend/src/pages/GeneratePage.tsx` - Create generation page
- `frontend/src/pages/LibraryPage.tsx` - Update library page
- `frontend/src/components/PodcastPlayer.tsx` - Add player component

---

## 🚀 Next Steps

### **Immediate (Today)**

1. ✅ **Test Backend Endpoints**
   - Use curl or Postman
   - Verify all endpoints work
   - Check database records

2. ⚠️ **Update Frontend**
   - Add podcast generation page
   - Add library page
   - Connect to API

3. ⚠️ **End-to-End Test**
   - Complete user flow
   - Generate → View → Play

---

### **Short Term (This Week)**

1. **Add Content Gathering**
   - Wikipedia API integration
   - Google Places API integration
   - Test with real data

2. **Add Audio Generation**
   - Choose TTS provider
   - Integrate API
   - Test audio quality

3. **Improve UI/UX**
   - Loading states
   - Error handling
   - Progress indicators

---

### **Medium Term (Next Week)**

1. **Cloud Deployment**
   - Choose cloud provider
   - Set up infrastructure
   - Deploy application

2. **Testing & Optimization**
   - Load testing
   - Performance optimization
   - Bug fixes

3. **User Feedback**
   - Beta testing
   - Collect feedback
   - Iterate

---

## 📊 Integration Checklist

### **Backend**
- [x] API endpoints created
- [x] Database models exist
- [x] Authentication working
- [x] Podcast generation logic
- [ ] Content gathering integration
- [ ] Audio generation integration
- [ ] Error handling complete
- [ ] Logging comprehensive

### **Frontend**
- [x] User authentication UI
- [x] Onboarding flow
- [x] Preferences management
- [ ] Podcast generation page
- [ ] Library page
- [ ] Audio player
- [ ] Status polling
- [ ] Error handling

### **Integration**
- [ ] Frontend → Backend connection
- [ ] API authentication
- [ ] Real-time status updates
- [ ] File upload/download
- [ ] Error propagation

### **Testing**
- [x] Backend unit tests
- [x] Frontend component tests
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Load tests

---

## 🐛 Common Issues

### **Issue: CORS Errors**
**Solution:** Check `backend/app/core/config.py`:
```python
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
```

### **Issue: Authentication Fails**
**Solution:** Check token in requests:
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

### **Issue: Podcast Generation Hangs**
**Solution:** Check background task execution and logs

---

## 📞 Need Help?

### **Check Logs**
```powershell
# Backend logs
# Check terminal where uvicorn is running

# Database
# Check PostgreSQL logs
```

### **API Documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🎯 Success Criteria

**Integration is complete when:**
- ✅ User can register and login
- ✅ User can set preferences
- ⚠️ User can generate podcast
- ⚠️ User can view podcast library
- ⚠️ User can play podcast audio
- ⚠️ All errors handled gracefully
- ⚠️ Loading states work correctly

---

## 🎉 You're Almost There!

**Current Progress: 70%**

**Remaining:**
- Frontend podcast pages (20%)
- Content/Audio integration (10%)

**Let's complete this together!** 🚀
