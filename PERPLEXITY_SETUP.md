# 🎯 Perplexity Setup - BEST OPTION!

## ✅ Why Perplexity is Perfect

### **Advantages:**
- ✅ **You already have it!** (subscription)
- ✅ **Better than Ollama** - Higher quality content
- ✅ **Has web search** - Can fetch real-time info
- ✅ **Fast** - Cloud-based, no local processing
- ✅ **Cheap** - ~$0.001 per request (way cheaper than OpenAI)
- ✅ **No installation** - Just need API key

### **Quality Comparison:**
- **Ollama (local):** ⭐⭐⭐ Good
- **Perplexity:** ⭐⭐⭐⭐ Excellent
- **OpenAI GPT-4:** ⭐⭐⭐⭐⭐ Best (but expensive)

**Perplexity is the sweet spot!** 🎯

---

## 🔑 Step 1: Get Your API Key

### **1. Go to Perplexity API:**
https://www.perplexity.ai/settings/api

### **2. Generate API Key:**
- Click "Generate API Key"
- Copy the key (starts with `pplx-...`)

### **3. Add to Environment:**

**File:** `backend/.env`

Add this line:
```bash
PERPLEXITY_API_KEY=pplx-your-key-here
```

---

## ⚙️ Step 2: Verify Setup

### **Check .env file:**
```bash
# backend/.env should have:
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx
```

### **Test the connection:**
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('PERPLEXITY_API_KEY')[:10] + '...')"
```

Should print: `API Key: pplx-xxxxx...`

---

## 🚀 Step 3: Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

**Watch for this log:**
```
INFO: LLM initialized with Perplexity (BEST OPTION)
```

---

## 🎉 Step 4: Test Generation!

### **1. Go to frontend:**
http://localhost:5173

### **2. Generate a podcast:**
- Login
- Click "Generate"
- Enter "Tokyo, Japan"
- Click "Generate Podcast"

### **3. Watch the logs:**
```
INFO: fetching_real_content location="Tokyo, Japan"
INFO: real_content_fetched title="Tokyo" facts_count=10
INFO: generating_with_perplexity
INFO: perplexity_generation_complete length=2500
INFO: narrative_construction_complete
INFO: podcast_generation_complete
```

### **4. Expected duration:**
- ⏱️ **30-40 seconds** (realistic!)
- Not <1 second like before

---

## 📊 What You'll Get

### **Script Quality:**
- ✅ Real Wikipedia facts
- ✅ AI-generated narrative (Perplexity)
- ✅ Engaging storytelling
- ✅ 1500-2000 words
- ✅ Professional quality

### **Example Output:**
```
Title: Discover Tokyo, Japan

Hook: "In the heart of Japan lies a metropolis where ancient 
temples stand beside neon skyscrapers, where tradition and 
innovation dance in perfect harmony..."

Content: [Real facts from Wikipedia + Perplexity's AI narrative]
- Tokyo's fascinating history
- Cultural significance
- Modern innovations
- Hidden gems

Conclusion: "From its humble origins as a fishing village to 
becoming one of the world's most dynamic cities, Tokyo continues 
to captivate and inspire..."
```

---

## 💰 Cost Estimate

### **Per Podcast:**
- Wikipedia: **FREE**
- Location data: **FREE**
- Perplexity API: **~$0.001** (basically free!)
- **Total: ~$0.001 per podcast**

### **Comparison:**
- Ollama: $0 (but slower, local processing)
- Perplexity: ~$0.001 (fast, cloud-based)
- OpenAI GPT-4: ~$0.10 (100x more expensive!)

**Perplexity is 100x cheaper than OpenAI!** 🎉

---

## 🎵 Next: Audio Generation

After content works, we'll add audio:

### **FREE Option: Coqui TTS**
- Open source
- Runs locally
- Decent quality
- $0 cost

### **PAID Option: ElevenLabs**
- Professional quality
- Cloud-based
- ~$4.50 per podcast

**We'll start with FREE (Coqui) for testing!**

---

## ⚠️ Troubleshooting

### **If you see: "PERPLEXITY_API_KEY not set"**
1. Check `.env` file exists in `backend/` folder
2. Check key starts with `pplx-`
3. Restart backend server

### **If generation fails:**
1. Check API key is valid
2. Check internet connection
3. Check Perplexity API status: https://status.perplexity.ai

### **If it's still using Ollama:**
1. Make sure `.env` has `PERPLEXITY_API_KEY`
2. Restart backend server
3. Check logs for "LLM initialized with Perplexity"

---

## 🎯 Success Checklist

- [ ] Got Perplexity API key
- [ ] Added to `.env` file
- [ ] Restarted backend
- [ ] Saw "LLM initialized with Perplexity" in logs
- [ ] Generated test podcast
- [ ] Took 30-40 seconds (not <1 second)
- [ ] Script has real content
- [ ] Quality is excellent!

---

## 🚀 Ready to Go!

**Once you have your API key:**
1. Add to `.env`
2. Restart backend
3. Generate a podcast
4. **Enjoy high-quality content for pennies!** 🎉

**This is the best option for your use case!** ✨
