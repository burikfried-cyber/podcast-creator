# Critical Issues Found - Oct 16, 2025 9:14 AM

## Problem 1: Script Contains Template Text, Not Real Facts

**Evidence:**
```
script_content: "Today, we're exploring Jerusalem, and you're about to discover something extraordinary. Let's continue... Discovery of Jerusalem Let's continue..."
```

**Root Cause:** LLM (Perplexity) is NOT being called to generate real content. The script assembly is using template connectors.

**Impact:** HIGH - Users see generic template text instead of real facts about locations.

**Fix Needed:**
1. Add logging to track if LLM.generate_narrative() is called
2. Check if Perplexity API is actually being invoked
3. Verify API key is set correctly
4. Check for silent failures in LLM generation

---

## Problem 2: Library Endpoint Takes 4-5 Seconds

**Evidence:**
```
09:10:59 | GET /api/v1/podcasts/ | duration_ms: 4610.31  (4.6 seconds!)
09:11:11 | GET /api/v1/podcasts/ | duration_ms: 5409.11  (5.4 seconds!)
```

**Root Cause:** Database query or serialization is slow.

**Impact:** HIGH - UI freezes, timeouts, poor user experience.

**Fix Needed:**
1. Add database query logging
2. Check if script_content is being loaded unnecessarily
3. Consider excluding script_content from list view
4. Add pagination
5. Add caching

---

## Problem 3: LLM Initialized 4 Times Per Request

**Evidence:**
```
09:06:33 | LLM initialized with Perplexity
09:06:34 | LLM initialized with Perplexity
09:06:35 | LLM initialized with Perplexity
09:06:36 | LLM initialized with Perplexity
```

**Root Cause:** Multiple services creating new LLM instances.

**Impact:** MEDIUM - Slower performance, unnecessary overhead.

**Fix Needed:**
1. Make LLM service a singleton
2. Reuse single instance across services
3. Add dependency injection

---

## Problem 4: Frontend Shows 0% Progress

**Evidence:** Backend reaches 100%, but frontend stuck at 0%.

**Root Cause:** Unknown - need to check:
1. Status polling responses
2. Frontend state updates
3. Response parsing

**Impact:** HIGH - Users think generation failed.

**Fix Needed:**
1. Add frontend console logging
2. Check status API responses
3. Verify progress updates

---

## Problem 5: Library Timeouts

**Evidence:** User reports library times out.

**Root Cause:** Related to Problem 2 - slow queries.

**Impact:** HIGH - Users can't view their podcasts.

**Fix Needed:** Same as Problem 2.

---

## Immediate Actions

### Action 1: Add Comprehensive Logging
- LLM generation calls
- Database query times
- API response times
- Frontend state changes

### Action 2: Test LLM Generation
Run a simple test to verify Perplexity is working:
```python
from app.services.content.llm_service import LLMService
import asyncio

async def test():
    llm = LLMService(provider="perplexity")
    result = await llm.generate_narrative(
        facts={"title": "Jerusalem", "summary": "Ancient city"},
        narrative_type="discovery"
    )
    print(result)

asyncio.run(test())
```

### Action 3: Optimize Library Query
Exclude script_content from list view:
```python
query = select(
    Podcast.id,
    Podcast.title,
    Podcast.description,
    Podcast.status,
    # Don't load script_content!
).filter(Podcast.user_id == user_id)
```

### Action 4: Fix Frontend Progress
Add detailed logging to ProgressPage.tsx to see what's happening.

---

## Testing Plan

1. **Restart backend** with new logging
2. **Generate test podcast** for "Paris, France"
3. **Check logs** for:
   - llm_generate_narrative_called
   - llm_generation_complete
   - Database query times
4. **Check frontend console** for progress updates
5. **Check library** loads quickly
6. **Check podcast page** shows real content

---

## Expected Fixes

After fixes:
- Script should contain real facts from Perplexity
- Library should load in under 1 second
- Frontend should show progress 0% -> 100%
- No timeouts
- LLM initialized once, not 4 times
