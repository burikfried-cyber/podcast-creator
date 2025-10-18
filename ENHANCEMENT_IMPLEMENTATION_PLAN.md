# COMPREHENSIVE ENHANCEMENT & IMPLEMENTATION PLAN
**Location-Based Podcast Generator - Production Enhancement Strategy**

**Generated:** October 18, 2025  
**Current Status:** Live in production with critical gaps  
**Target:** Production-ready with enhanced features

---

## EXECUTIVE SUMMARY

Based on comprehensive analysis of the current implementation and research into best practices, this plan provides **complete, research-based, architecture-integrated specifications** for enhancing three critical components:

1. **Information Collection System** - From basic Wikipedia to multi-source deep research
2. **Script Generation Engine** - From template text to information-rich narratives
3. **Audio Synthesis System** - From disabled code to production TTS

**Key Findings from Current State:**
- Only 25% of coded features are active (3,850 / 15,400 lines)
- Data collection limited to 2 sources (Wikipedia + Location service)
- Script quality poor due to Perplexity prompt issues
- Audio completely disabled despite 2,700 lines of code ready

**Enhancement Approach:**
- Build on existing architecture (preserve what works)
- Activate dormant systems (standout detection, user preferences)
- Add research-based enhancements (multi-source APIs, deep research)
- Maintain <30s generation time target

---

## 🎯 PART 1: ENHANCED INFORMATION COLLECTION SYSTEM

### Current State Analysis

**What Works (90% implemented):**
- ✅ Wikipedia API integration (2-5s, 95% success rate)
- ✅ Location service (1-3s, 90% success rate)
- ✅ Basic caching (15-minute TTL)
- ✅ Error handling and logging

**Critical Gaps:**
- ❌ Only 2 data sources active (25+ available in code)
- ❌ No standout content detection (coded but not integrated)
- ❌ No multi-level location hierarchy (street → neighborhood → city → country)
- ❌ No deep research for question-based queries
- ❌ No content quality scoring
- ❌ Surface-level information only

**Research Findings - Best Practices 2025:**

Based on extensive research, the optimal information collection system requires:

1. **Multi-Source API Integration** (15-20 sources minimum)
   - Free tier prioritization for cost optimization
   - Hierarchical fallback chains for reliability
   - Parallel processing for speed (<5s total)

2. **Hierarchical Location Resolution**
   - Street/address → Neighborhood → District → City → Region → Country
   - Google Maps Places API + Geocoding for hierarchy
   - Administrative boundaries for context

3. **Deep Research Capability** (for question-based queries)
   - Multi-step iterative search
   - Source synthesis and reasoning
   - Perplexity Sonar or OpenAI Deep Research integration

4. **Content Quality Scoring**
   - Source authority weighting
   - Cross-validation for facts
   - Standout vs mundane classification

---

### ENHANCEMENT 1.1: MULTI-SOURCE API INTEGRATION SYSTEM

#### **Architecture Integration Points**

**Existing Files to Enhance:**
```
backend/app/services/content/
├── wikipedia_service.py (KEEP - works well)
├── location_service.py (ENHANCE - add hierarchy)
├── content_aggregator.py (NEW - orchestrate all sources)
└── quality_scorer.py (NEW - score content)

backend/app/services/detection/
├── standout_detector.py (ACTIVATE - currently dormant)
└── content_classifier.py (ENHANCE - integrate with sources)
```

#### **API Source Selection Matrix (Research-Based)**

Based on research into 2025 best practices, here are the optimal APIs:

**TIER 1: FREE HIGH-QUALITY (Primary Sources)**
| API | Coverage | Use Case | Rate Limit | Integration Complexity |
|-----|----------|----------|------------|----------------------|
| **Wikipedia API** | Global, all topics | General knowledge, history | None (current) | ✅ ACTIVE |
| **Wikidata API** | 100M+ entities | Structured data, facts | 5000/hour | LOW - Add now |
| **OpenStreetMap Nominatim** | Global geography | Location details, POIs | 1/sec | LOW - Add now |
| **GeoNames** | 11M+ place names | Geographic hierarchy | 1000/hour free | LOW - Add now |
| **UNESCO World Heritage API** | 1100+ sites | Cultural significance | Fair use | LOW - Add now |
| **Data.gov APIs** | 200k+ US datasets | Official data, statistics | 1000/hour | MEDIUM |
| **Open Culture Data** | Dutch cultural | Cultural heritage | Fair use | LOW |

**TIER 2: FREEMIUM (Enhanced Quality)**
| API | Free Tier | Use Case | Cost After Free | Priority |
|-----|-----------|----------|----------------|----------|
| **Perplexity Sonar API** | Limited | Deep research, synthesis | $0.005/request | HIGH - Already have key |
| **Geoapify Places API** | 3000/day | POI, local context | $49/mo after | MEDIUM |
| **IPGeolocation.io** | 30k/month | Enhanced location data | $15/mo after | LOW |

**TIER 3: PREMIUM (Optional Enhancement)**
| API | Cost | Use Case | When to Add |
|-----|------|----------|-------------|
| **TripAdvisor Content API** | Partner/~$0.02/req | Tourism insights | Phase 2 |
| **Amadeus Destination APIs** | $0.01/req after free | POI, location scores | Phase 2 |

**TIER 4: SPECIALIZED (Domain-Specific)**
| API | Coverage | Use Case | Integration |
|-----|----------|----------|-------------|
| **arXiv API** | 2.2M+ papers | Academic research | Question-based |
| **CrossRef API** | 130M+ records | Scholarly metadata | Question-based |
| **Guardian API** | News since 1999 | Current events | Time-sensitive |

#### **Implementation Strategy**

**Phase 1A: Activate Existing + Add Free Sources (Week 1)**

Add 5 high-value free APIs to complement Wikipedia:

1. **Wikidata Integration**
```python
# backend/app/services/content/wikidata_service.py

import aiohttp
import asyncio
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger

class WikidataService:
    """
    Wikidata API integration for structured entity data.
    Provides facts, relationships, and metadata Wikipedia lacks.
    """
    
    def __init__(self):
        self.base_url = "https://www.wikidata.org/w/api.php"
        self.sparql_url = "https://query.wikidata.org/sparql"
        self.session = None
        self.cache_ttl = 3600  # 1 hour
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": "LocationPodcastGenerator/1.0"}
            )
        return self.session
    
    async def search_entity(self, location_name: str) -> Optional[str]:
        """
        Search for Wikidata entity ID by location name.
        Returns entity ID (Q-number) or None.
        """
        try:
            session = await self._get_session()
            
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "type": "item",
                "search": location_name,
                "limit": 1
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("search"):
                        entity_id = data["search"][0]["id"]
                        logger.info(f"Found Wikidata entity: {entity_id} for {location_name}")
                        return entity_id
                        
        except Exception as e:
            logger.error(f"Wikidata entity search failed: {e}")
            
        return None
    
    async def get_entity_data(self, entity_id: str) -> Dict:
        """
        Retrieve comprehensive entity data including claims and properties.
        """
        try:
            session = await self._get_session()
            
            params = {
                "action": "wbgetentities",
                "format": "json",
                "ids": entity_id,
                "languages": "en",
                "props": "claims|labels|descriptions|sitelinks"
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    entity_data = data["entities"][entity_id]
                    
                    # Extract structured data
                    structured_data = {
                        "entity_id": entity_id,
                        "label": entity_data.get("labels", {}).get("en", {}).get("value"),
                        "description": entity_data.get("descriptions", {}).get("en", {}).get("value"),
                        "facts": await self._extract_facts(entity_data.get("claims", {})),
                        "wikipedia_link": await self._get_wikipedia_link(entity_data.get("sitelinks", {}))
                    }
                    
                    return structured_data
                    
        except Exception as e:
            logger.error(f"Wikidata entity data retrieval failed: {e}")
            
        return {}
    
    async def _extract_facts(self, claims: Dict) -> List[Dict]:
        """
        Extract interesting facts from Wikidata claims.
        Focus on properties relevant to locations.
        """
        interesting_properties = {
            "P17": "country",
            "P131": "located_in",
            "P1082": "population",
            "P571": "inception",
            "P625": "coordinates",
            "P706": "located_on_terrain_feature",
            "P2044": "elevation",
            "P421": "timezone",
            "P1566": "geonames_id",
            "P281": "postal_code"
        }
        
        facts = []
        
        for prop_id, prop_name in interesting_properties.items():
            if prop_id in claims:
                claim_data = claims[prop_id]
                if claim_data:
                    # Extract value from first claim
                    mainsnak = claim_data[0].get("mainsnak", {})
                    datavalue = mainsnak.get("datavalue", {})
                    
                    if datavalue:
                        value = datavalue.get("value")
                        facts.append({
                            "property": prop_name,
                            "value": value,
                            "property_id": prop_id
                        })
        
        return facts
    
    async def _get_wikipedia_link(self, sitelinks: Dict) -> Optional[str]:
        """Extract English Wikipedia link from sitelinks."""
        enwiki = sitelinks.get("enwiki", {})
        if enwiki:
            title = enwiki.get("title")
            return f"https://en.wikipedia.org/wiki/{title}" if title else None
        return None
    
    async def get_location_facts(self, location_name: str) -> Dict:
        """
        High-level method to get structured location facts from Wikidata.
        
        Returns:
        {
            "entity_id": "Q64",
            "structured_facts": [...],
            "related_entities": [...],
            "confidence": 0.95
        }
        """
        try:
            # Step 1: Find entity ID
            entity_id = await self.search_entity(location_name)
            
            if not entity_id:
                return {"error": "Entity not found", "confidence": 0.0}
            
            # Step 2: Get entity data
            entity_data = await self.get_entity_data(entity_id)
            
            if not entity_data:
                return {"error": "Entity data unavailable", "confidence": 0.0}
            
            # Step 3: Format for podcast use
            return {
                "entity_id": entity_id,
                "label": entity_data.get("label"),
                "description": entity_data.get("description"),
                "structured_facts": entity_data.get("facts", []),
                "wikipedia_link": entity_data.get("wikipedia_link"),
                "confidence": 0.90,
                "source": "wikidata"
            }
            
        except Exception as e:
            logger.error(f"Wikidata location facts retrieval failed: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    async def close(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

# Singleton instance
wikidata_service = WikidataService()
```

2. **GeoNames Hierarchical Location Service**
```python
# backend/app/services/content/geonames_service.py

import aiohttp
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger

class GeoNamesService:
    """
    GeoNames API integration for geographic hierarchy and place details.
    Provides: neighborhood → district → city → region → country hierarchy
    """
    
    def __init__(self):
        self.base_url = "http://api.geonames.org"
        self.username = settings.GEONAMES_USERNAME or "demo"  # Register for free username
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=8)
            )
        return self.session
    
    async def search_location(self, location_name: str, max_rows: int = 5) -> List[Dict]:
        """
        Search for location by name.
        Returns list of possible matches with basic info.
        """
        try:
            session = await self._get_session()
            
            params = {
                "q": location_name,
                "maxRows": max_rows,
                "username": self.username,
                "type": "json",
                "style": "FULL"
            }
            
            async with session.get(f"{self.base_url}/searchJSON", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("geonames", [])
                    
        except Exception as e:
            logger.error(f"GeoNames search failed: {e}")
            
        return []
    
    async def get_hierarchy(self, geoname_id: int) -> Dict:
        """
        Get complete geographic hierarchy for a location.
        Returns: planet → continent → country → admin1 → admin2 → city → neighborhood
        """
        try:
            session = await self._get_session()
            
            params = {
                "geonameId": geoname_id,
                "username": self.username
            }
            
            async with session.get(f"{self.base_url}/hierarchyJSON", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    hierarchy_raw = data.get("geonames", [])
                    
                    # Parse into structured hierarchy
                    hierarchy = {
                        "planet": None,
                        "continent": None,
                        "country": None,
                        "region": None,  # admin1
                        "district": None,  # admin2
                        "city": None,
                        "neighborhood": None
                    }
                    
                    for item in hierarchy_raw:
                        fcode = item.get("fcode", "")
                        
                        if fcode.startswith("PCLI"):  # Country
                            hierarchy["country"] = {
                                "name": item.get("name"),
                                "geonameId": item.get("geonameId"),
                                "population": item.get("population")
                            }
                        elif fcode.startswith("ADM1"):  # Region/State
                            hierarchy["region"] = {
                                "name": item.get("name"),
                                "geonameId": item.get("geonameId"),
                                "population": item.get("population")
                            }
                        elif fcode.startswith("ADM2"):  # District/County
                            hierarchy["district"] = {
                                "name": item.get("name"),
                                "geonameId": item.get("geonameId"),
                                "population": item.get("population")
                            }
                        elif fcode.startswith("PPL"):  # Populated place (city/town/village)
                            hierarchy["city"] = {
                                "name": item.get("name"),
                                "geonameId": item.get("geonameId"),
                                "population": item.get("population"),
                                "feature_code": fcode
                            }
                    
                    return hierarchy
                    
        except Exception as e:
            logger.error(f"GeoNames hierarchy retrieval failed: {e}")
            
        return {}
    
    async def get_nearby_places(self, latitude: float, longitude: float, radius_km: int = 5) -> List[Dict]:
        """
        Get nearby places of interest within radius.
        Useful for discovering neighborhood context.
        """
        try:
            session = await self._get_session()
            
            params = {
                "lat": latitude,
                "lng": longitude,
                "radius": radius_km,
                "maxRows": 20,
                "username": self.username,
                "style": "FULL"
            }
            
            async with session.get(f"{self.base_url}/findNearbyJSON", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("geonames", [])
                    
        except Exception as e:
            logger.error(f"GeoNames nearby places search failed: {e}")
            
        return []
    
    async def get_location_details(self, location_name: str) -> Dict:
        """
        High-level method to get complete location information including hierarchy.
        
        Returns:
        {
            "location": {...},
            "hierarchy": {...},
            "nearby_places": [...],
            "confidence": 0.85
        }
        """
        try:
            # Step 1: Search for location
            search_results = await self.search_location(location_name)
            
            if not search_results:
                return {"error": "Location not found", "confidence": 0.0}
            
            # Take first result (highest relevance)
            location = search_results[0]
            geoname_id = location.get("geonameId")
            
            # Step 2: Get hierarchy
            hierarchy = await self.get_hierarchy(geoname_id)
            
            # Step 3: Get nearby places (if coordinates available)
            nearby_places = []
            if location.get("lat") and location.get("lng"):
                nearby_places = await self.get_nearby_places(
                    location["lat"], 
                    location["lng"],
                    radius_km=5
                )
            
            return {
                "location": {
                    "name": location.get("name"),
                    "geonameId": geoname_id,
                    "coordinates": {
                        "lat": location.get("lat"),
                        "lng": location.get("lng")
                    },
                    "population": location.get("population"),
                    "timezone": location.get("timezone", {}).get("timeZoneId"),
                    "feature_code": location.get("fcode")
                },
                "hierarchy": hierarchy,
                "nearby_places": nearby_places[:10],  # Limit to top 10
                "confidence": 0.85,
                "source": "geonames"
            }
            
        except Exception as e:
            logger.error(f"GeoNames location details retrieval failed: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    async def close(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

# Singleton instance
geonames_service = GeoNamesService()
```

3. **Content Aggregation Orchestrator**
```python
# backend/app/services/content/content_aggregator.py

import asyncio
from typing import Dict, List
from app.services.content.wikipedia_service import wikipedia_service
from app.services.content.wikidata_service import wikidata_service
from app.services.content.geonames_service import geonames_service
from app.services.content.location_service import location_service
from app.core.logging import logger

class ContentAggregator:
    """
    Orchestrates parallel content collection from multiple sources.
    Implements fallback chains and error handling for reliability.
    
    Target: <5 seconds total collection time
    """
    
    def __init__(self):
        self.sources = {
            "wikipedia": wikipedia_service,
            "wikidata": wikidata_service,
            "geonames": geonames_service,
            "location": location_service
        }
        
    async def gather_location_content(
        self, 
        location_name: str,
        podcast_type: str = "base",
        user_preferences: Dict = None
    ) -> Dict:
        """
        Gather content from all sources in parallel.
        
        Args:
            location_name: Location to research
            podcast_type: "base", "standout", "topic", "personalized"
            user_preferences: User depth, surprise tolerance, topics
            
        Returns:
            Aggregated content from all sources with quality scores
        """
        try:
            logger.info(f"Starting parallel content gathering for: {location_name}")
            
            # Execute all sources in parallel
            results = await asyncio.gather(
                self._gather_wikipedia(location_name),
                self._gather_wikidata(location_name),
                self._gather_geonames(location_name),
                self._gather_location_data(location_name),
                return_exceptions=True
            )
            
            # Unpack results
            wikipedia_data, wikidata_data, geonames_data, location_data = results
            
            # Handle exceptions
            wikipedia_data = {} if isinstance(wikipedia_data, Exception) else wikipedia_data
            wikidata_data = {} if isinstance(wikidata_data, Exception) else wikidata_data
            geonames_data = {} if isinstance(geonames_data, Exception) else geonames_data
            location_data = {} if isinstance(location_data, Exception) else location_data
            
            # Aggregate and structure
            aggregated_content = {
                "location_name": location_name,
                "sources": {
                    "wikipedia": wikipedia_data,
                    "wikidata": wikidata_data,
                    "geonames": geonames_data,
                    "location": location_data
                },
                "hierarchy": self._build_hierarchy(geonames_data, location_data),
                "structured_facts": self._merge_facts(wikipedia_data, wikidata_data),
                "geographic_context": self._build_geographic_context(geonames_data, location_data),
                "quality_scores": await self._score_content(wikipedia_data, wikidata_data, geonames_data),
                "collection_metadata": {
                    "sources_succeeded": sum(1 for d in [wikipedia_data, wikidata_data, geonames_data, location_data] if d),
                    "sources_total": 4,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
            
            logger.info(f"Content gathering complete: {aggregated_content['collection_metadata']['sources_succeeded']}/4 sources")
            
            return aggregated_content
            
        except Exception as e:
            logger.error(f"Content aggregation failed: {e}")
            return {"error": str(e), "location_name": location_name}
    
    async def _gather_wikipedia(self, location_name: str) -> Dict:
        """Gather Wikipedia content with error handling."""
        try:
            # Use existing Wikipedia service
            content = await self.sources["wikipedia"].get_content(location_name)
            return content if content else {}
        except Exception as e:
            logger.warning(f"Wikipedia gathering failed: {e}")
            return {}
    
    async def _gather_wikidata(self, location_name: str) -> Dict:
        """Gather Wikidata structured facts."""
        try:
            facts = await self.sources["wikidata"].get_location_facts(location_name)
            return facts if facts else {}
        except Exception as e:
            logger.warning(f"Wikidata gathering failed: {e}")
            return {}
    
    async def _gather_geonames(self, location_name: str) -> Dict:
        """Gather GeoNames hierarchy and nearby places."""
        try:
            details = await self.sources["geonames"].get_location_details(location_name)
            return details if details else {}
        except Exception as e:
            logger.warning(f"GeoNames gathering failed: {e}")
            return {}
    
    async def _gather_location_data(self, location_name: str) -> Dict:
        """Gather basic location data from existing service."""
        try:
            data = await self.sources["location"].get_location_data(location_name)
            return data if data else {}
        except Exception as e:
            logger.warning(f"Location service gathering failed: {e}")
            return {}
    
    def _build_hierarchy(self, geonames_data: Dict, location_data: Dict) -> Dict:
        """
        Build multi-level location hierarchy from GeoNames + location data.
        
        Returns hierarchy:
        {
            "neighborhood": "Shibuya Crossing",
            "district": "Shibuya",
            "city": "Tokyo",
            "region": "Kantō",
            "country": "Japan",
            "continent": "Asia"
        }
        """
        hierarchy = {
            "neighborhood": None,
            "district": None,
            "city": None,
            "region": None,
            "country": None,
            "continent": None
        }
        
        # Extract from GeoNames hierarchy if available
        if geonames_data.get("hierarchy"):
            gn_hierarchy = geonames_data["hierarchy"]
            hierarchy["country"] = gn_hierarchy.get("country", {}).get("name")
            hierarchy["region"] = gn_hierarchy.get("region", {}).get("name")
            hierarchy["district"] = gn_hierarchy.get("district", {}).get("name")
            hierarchy["city"] = gn_hierarchy.get("city", {}).get("name")
        
        # Fallback to location service data
        if not hierarchy["country"] and location_data.get("country"):
            hierarchy["country"] = location_data["country"]
        
        if not hierarchy["city"] and location_data.get("city"):
            hierarchy["city"] = location_data["city"]
        
        return hierarchy
    
    def _merge_facts(self, wikipedia_data: Dict, wikidata_data: Dict) -> List[Dict]:
        """
        Merge and deduplicate facts from Wikipedia and Wikidata.
        Prioritize structured Wikidata facts, supplement with Wikipedia.
        """
        facts = []
        
        # Add Wikidata structured facts (highest quality)
        if wikidata_data.get("structured_facts"):
            facts.extend(wikidata_data["structured_facts"])
        
        # Add Wikipedia interesting facts (different format)
        if wikipedia_data.get("interesting_facts"):
            for fact in wikipedia_data["interesting_facts"]:
                facts.append({
                    "property": "wikipedia_fact",
                    "value": fact,
                    "source": "wikipedia"
                })
        
        return facts
    
    def _build_geographic_context(self, geonames_data: Dict, location_data: Dict) -> Dict:
        """
        Build comprehensive geographic context including nearby places.
        """
        context = {
            "coordinates": None,
            "population": None,
            "timezone": None,
            "nearby_places": [],
            "climate": None
        }
        
        # From GeoNames
        if geonames_data.get("location"):
            context["coordinates"] = geonames_data["location"].get("coordinates")
            context["population"] = geonames_data["location"].get("population")
            context["timezone"] = geonames_data["location"].get("timezone")
        
        if geonames_data.get("nearby_places"):
            context["nearby_places"] = geonames_data["nearby_places"][:5]
        
        # From location service
        if location_data.get("climate"):
            context["climate"] = location_data["climate"]
        
        return context
    
    async def _score_content(
        self, 
        wikipedia_data: Dict, 
        wikidata_data: Dict, 
        geonames_data: Dict
    ) -> Dict:
        """
        Score content quality from each source.
        
        Metrics:
        - Completeness: How much information was retrieved
        - Authority: Reliability of source
        - Freshness: How recent is the data
        """
        scores = {
            "wikipedia": self._score_wikipedia_content(wikipedia_data),
            "wikidata": self._score_wikidata_content(wikidata_data),
            "geonames": self._score_geonames_content(geonames_data),
            "overall": 0.0
        }
        
        # Calculate overall score (weighted average)
        weights = {"wikipedia": 0.4, "wikidata": 0.3, "geonames": 0.3}
        scores["overall"] = sum(
            scores[source] * weight 
            for source, weight in weights.items()
        )
        
        return scores
    
    def _score_wikipedia_content(self, data: Dict) -> float:
        """Score Wikipedia content completeness."""
        if not data or data.get("error"):
            return 0.0
        
        score = 0.0
        
        # Has summary
        if data.get("summary"):
            score += 0.3
        
        # Has interesting facts
        if data.get("interesting_facts") and len(data["interesting_facts"]) >= 3:
            score += 0.3
        
        # Has full content
        if data.get("content") and len(data["content"]) > 500:
            score += 0.4
        
        return min(score, 1.0)
    
    def _score_wikidata_content(self, data: Dict) -> float:
        """Score Wikidata structured facts availability."""
        if not data or data.get("error"):
            return 0.0
        
        score = 0.0
        
        # Has entity ID
        if data.get("entity_id"):
            score += 0.2
        
        # Has structured facts
        facts_count = len(data.get("structured_facts", []))
        if facts_count > 0:
            score += min(0.8, facts_count * 0.1)
        
        return min(score, 1.0)
    
    def _score_geonames_content(self, data: Dict) -> float:
        """Score GeoNames geographic completeness."""
        if not data or data.get("error"):
            return 0.0
        
        score = 0.0
        
        # Has hierarchy
        if data.get("hierarchy"):
            hierarchy_levels = sum(1 for v in data["hierarchy"].values() if v)
            score += min(0.5, hierarchy_levels * 0.1)
        
        # Has nearby places
        if data.get("nearby_places"):
            score += 0.3
        
        # Has coordinates
        if data.get("location", {}).get("coordinates"):
            score += 0.2
        
        return min(score, 1.0)

# Singleton instance
content_aggregator = ContentAggregator()
```

**WINDSURF PROMPT 1A: Multi-Source API Integration**

```
TASK: Enhance information collection system with multi-source API integration

CURRENT STATE:
- Only Wikipedia + basic location service active
- 90% data collection completion but only 2 sources
- Code exists at backend/app/services/content/
- Wikipedia service works perfectly (preserve it)

REQUIREMENTS:

1. ADD WIKIDATA SERVICE (backend/app/services/content/wikidata_service.py):
   - Search entity by location name
   - Retrieve structured facts (population, inception, coordinates, etc.)
   - Extract 10+ key properties for locations
   - Return confidence scores
   - 10-second timeout with error handling
   - Cache results for 1 hour

2. ADD GEONAMES SERVICE (backend/app/services/content/geonames_service.py):
   - Hierarchical location resolution (neighborhood → district → city → region → country)
   - Search location by name (max 5 results)
   - Get full hierarchy using hierarchyJSON endpoint
   - Get nearby places within 5km radius
   - Parse feature codes (PCLI, ADM1, ADM2, PPL)
   - 8-second timeout with graceful fallbacks

3. CREATE CONTENT AGGREGATOR (backend/app/services/content/content_aggregator.py):
   - Orchestrate parallel calls to all sources (Wikipedia, Wikidata, GeoNames, Location)
   - Use asyncio.gather() for concurrent execution
   - Target <5 seconds total collection time
   - Handle exceptions gracefully (return empty dict on failure)
   - Build hierarchical location structure
   - Merge facts from all sources (deduplicate)
   - Score content quality per source (completeness, authority)
   - Return aggregated result with metadata

4. INTEGRATE WITH EXISTING PODCAST SERVICE:
   - Update backend/app/services/podcast_service.py
   - Replace direct Wikipedia calls with content_aggregator.gather_location_content()
   - Pass aggregated content to narrative engine
   - Maintain backward compatibility
   - Log source success rates

ARCHITECTURE:
- Async/await patterns throughout
- aiohttp for HTTP clients
- Singleton pattern for services
- Error handling with try/except and return_exceptions
- Structured logging for observability
- Cache results in Redis (15-minute TTL for new sources)

API ENDPOINTS:
Wikidata:
- Base: https://www.wikidata.org/w/api.php
- SPARQL: https://query.wikidata.org/sparql
- Actions: wbsearchentities, wbgetentities
- Rate limit: None (fair use)

GeoNames:
- Base: http://api.geonames.org
- Endpoints: searchJSON, hierarchyJSON, findNearbyJSON
- Auth: username (add GEONAMES_USERNAME to .env, default "demo")
- Rate limit: 1000/hour free tier

DATA STRUCTURES:
Aggregated content format:
{
  "location_name": str,
  "sources": {
    "wikipedia": Dict,
    "wikidata": Dict,
    "geonames": Dict,
    "location": Dict
  },
  "hierarchy": {
    "neighborhood": str | None,
    "district": str | None,
    "city": str | None,
    "region": str | None,
    "country": str | None
  },
  "structured_facts": List[Dict],
  "geographic_context": Dict,
  "quality_scores": {
    "wikipedia": float,
    "wikidata": float,
    "geonames": float,
    "overall": float
  },
  "collection_metadata": Dict
}

TESTING:
- Test with "Tokyo, Japan" (should return hierarchy + nearby places)
- Test with "Paris, France" (should return Wikidata facts + Wikipedia)
- Test with invalid location (should handle gracefully)
- Verify <5 second collection time
- Verify all sources called in parallel
- Check quality scores are between 0.0-1.0

ENVIRONMENT VARIABLES TO ADD:
```
# .env
GEONAMES_USERNAME=your_free_username_here
```

DELIVERABLES:
1. wikidata_service.py (complete implementation)
2. geonames_service.py (complete implementation)
3. content_aggregator.py (complete implementation)
4. Updated podcast_service.py (integration)
5. Tests for all new services
6. Documentation for API rate limits and caching

SUCCESS CRITERIA:
- Content gathering completes in <5 seconds
- All 4 sources called in parallel
- Hierarchical location structure built correctly
- Quality scores calculated for each source
- Graceful handling of API failures
- Backward compatible with existing code
- Logs show source success/failure clearly
```

---

### ENHANCEMENT 1.2: MULTI-LEVEL LOCATION HIERARCHY

**Research Finding:** Users want contextual information at multiple geographic levels.

**Example User Need:**
- "I'm in Shibuya Crossing, Tokyo" should provide:
  - **Immediate**: Shibuya Crossing facts (1-2 min)
  - **District**: Shibuya district context (30-60 sec)
  - **City**: Tokyo overview (2-3 min)
  - **Country**: Japan cultural context (1-2 min)
  
**Weight distribution based on podcast type and user preferences:**

| User Preference | Neighborhood | District | City | Country |
|----------------|--------------|----------|------|---------|
| **Very Local** | 60% | 25% | 10% | 5% |
| **Balanced** | 30% | 30% | 30% | 10% |
| **Broad Context** | 10% | 20% | 40% | 30% |

**Implementation:**

```python
# backend/app/services/content/hierarchical_collector.py

from typing import Dict, List
from app.services.content.content_aggregator import content_aggregator
from app.core.logging import logger

class HierarchicalContentCollector:
    """
    Collects content at multiple geographic levels based on user preferences.
    Implements smart weighting to balance local vs contextual information.
    """
    
    def __init__(self):
        self.aggregator = content_aggregator
        
    async def collect_hierarchical_content(
        self,
        primary_location: str,
        user_preferences: Dict = None
    ) -> Dict:
        """
        Collect content at multiple geographic levels.
        
        Args:
            primary_location: User's specific location (e.g., "Shibuya Crossing, Tokyo")
            user_preferences: User's depth, context preference
            
        Returns:
            Multi-level content with automatic weighting
        """
        try:
            # Step 1: Get primary location content (includes hierarchy)
            primary_content = await self.aggregator.gather_location_content(primary_location)
            
            if not primary_content or primary_content.get("error"):
                logger.warning(f"Primary location gathering failed for {primary_location}")
                return primary_content
            
            # Step 2: Extract hierarchy
            hierarchy = primary_content.get("hierarchy", {})
            
            # Step 3: Determine context preference
            context_preference = self._get_context_preference(user_preferences)
            
            # Step 4: Collect additional context at higher levels (if needed)
            additional_contexts = await self._collect_additional_contexts(
                hierarchy,
                context_preference,
                primary_location
            )
            
            # Step 5: Calculate content weights
            weights = self._calculate_content_weights(hierarchy, context_preference)
            
            # Step 6: Assemble multi-level content
            hierarchical_content = {
                "primary_location": primary_location,
                "hierarchy": hierarchy,
                "content_levels": {
                    "local": primary_content,  # The specific place
                    "district": additional_contexts.get("district"),
                    "city": additional_contexts.get("city"),
                    "region": additional_contexts.get("region"),
                    "country": additional_contexts.get("country")
                },
                "content_weights": weights,
                "context_preference": context_preference
            }
            
            return hierarchical_content
            
        except Exception as e:
            logger.error(f"Hierarchical content collection failed: {e}")
            return {"error": str(e), "primary_location": primary_location}
    
    def _get_context_preference(self, user_preferences: Dict) -> str:
        """
        Determine user's context preference from user preferences.
        
        Returns: "very_local", "balanced", or "broad_context"
        """
        if not user_preferences:
            return "balanced"  # Default
        
        # Check explicit context preference if exists
        if user_preferences.get("context_level"):
            return user_preferences["context_level"]
        
        # Infer from depth preference
        depth = user_preferences.get("depth_preference", 3)
        
        if depth <= 2:  # Surface, Basic
            return "very_local"
        elif depth <= 4:  # Intermediate, Advanced
            return "balanced"
        else:  # Expert, Academic
            return "broad_context"
    
    async def _collect_additional_contexts(
        self,
        hierarchy: Dict,
        context_preference: str,
        primary_location: str
    ) -> Dict:
        """
        Collect content for higher geographic levels if needed.
        Only fetch if context_preference demands it.
        """
        additional_contexts = {}
        
        # Skip additional collection if user wants very local content
        if context_preference == "very_local":
            return additional_contexts
        
        # Collect city context if not the primary location
        city = hierarchy.get("city")
        if city and city.lower() not in primary_location.lower():
            city_content = await self.aggregator.gather_location_content(city)
            additional_contexts["city"] = city_content
        
        # Collect country context if broad context requested
        if context_preference == "broad_context":
            country = hierarchy.get("country")
            if country:
                country_content = await self.aggregator.gather_location_content(country)
                additional_contexts["country"] = country_content
        
        return additional_contexts
    
    def _calculate_content_weights(self, hierarchy: Dict, context_preference: str) -> Dict:
        """
        Calculate how much time/content to allocate to each geographic level.
        
        Returns weights that sum to 1.0:
        {
            "local": 0.6,
            "district": 0.25,
            "city": 0.1,
            "country": 0.05
        }
        """
        # Weight templates by preference
        weight_templates = {
            "very_local": {
                "local": 0.60,
                "district": 0.25,
                "city": 0.10,
                "region": 0.03,
                "country": 0.02
            },
            "balanced": {
                "local": 0.30,
                "district": 0.25,
                "city": 0.30,
                "region": 0.10,
                "country": 0.05
            },
            "broad_context": {
                "local": 0.10,
                "district": 0.15,
                "city": 0.35,
                "region": 0.20,
                "country": 0.20
            }
        }
        
        weights = weight_templates.get(context_preference, weight_templates["balanced"])
        
        # Adjust weights based on what's actually available in hierarchy
        available_levels = [level for level, value in hierarchy.items() if value]
        
        # Redistribute weight from missing levels
        adjusted_weights = {}
        total_available_weight = sum(weights.get(level, 0) for level in available_levels)
        
        for level in available_levels:
            if total_available_weight > 0:
                adjusted_weights[level] = weights.get(level, 0) / total_available_weight
            else:
                adjusted_weights[level] = 1.0 / len(available_levels)
        
        return adjusted_weights

# Singleton instance
hierarchical_collector = HierarchicalContentCollector()
```

**WINDSURF PROMPT 1B: Hierarchical Location Collection**

```
TASK: Implement multi-level hierarchical location content collection

CURRENT STATE:
- Content aggregator implemented (Phase 1A complete)
- Single-level content collection only
- No support for neighborhood → city → country context

REQUIREMENTS:

1. CREATE HIERARCHICAL COLLECTOR (backend/app/services/content/hierarchical_collector.py):
   - Use content_aggregator for each geographic level
   - Extract hierarchy from primary location (neighborhood, district, city, region, country)
   - Determine user's context preference (very_local, balanced, broad_context)
   - Collect additional content for higher levels (city, country) if needed
   - Calculate content weights based on hierarchy and preference
   - Return multi-level structured content

2. CONTEXT PREFERENCE LOGIC:
   very_local (depth 1-2):
   - 60% primary location
   - 25% district
   - 10% city
   - 5% region/country
   
   balanced (depth 3-4):
   - 30% primary location
   - 25% district
   - 30% city
   - 10% region
   - 5% country
   
   broad_context (depth 5-6):
   - 10% primary location
   - 15% district
   - 35% city
   - 20% region
   - 20% country

3. SMART COLLECTION STRATEGY:
   - Always collect primary location content
   - Collect city content ONLY if different from primary location
   - Collect country content ONLY if broad_context requested
   - Skip district/region if not in hierarchy
   - Redistribute weights if levels missing

4. INTEGRATE WITH PODCAST SERVICE:
   - Update backend/app/services/podcast_service.py
   - Use hierarchical_collector instead of content_aggregator
   - Pass user_preferences (includes context_level)
   - Handle multi-level content in narrative engine

DATA STRUCTURES:
Input user_preferences:
{
  "depth_preference": int (1-6),
  "context_level": str ("very_local" | "balanced" | "broad_context"),
  "surprise_tolerance": int (1-6)
}

Output hierarchical_content:
{
  "primary_location": str,
  "hierarchy": {
    "neighborhood": str | None,
    "district": str | None,
    "city": str | None,
    "region": str | None,
    "country": str | None
  },
  "content_levels": {
    "local": Dict,  # Primary location content
    "district": Dict | None,
    "city": Dict | None,
    "region": Dict | None,
    "country": Dict | None
  },
  "content_weights": {
    "local": float,
    "district": float,
    "city": float,
    "region": float,
    "country": float
  },
  "context_preference": str
}

TESTING:
Test Case 1: Very Local Preference
- Input: "Shibuya Crossing, Tokyo", depth=2, context="very_local"
- Expected: 60% Shibuya Crossing, 25% Shibuya district, 10% Tokyo, 5% Japan
- City content should NOT be fetched (already have from hierarchy)

Test Case 2: Balanced Preference
- Input: "Eiffel Tower, Paris", depth=3, context="balanced"
- Expected: 30% Eiffel Tower, 30% Paris, balanced weights
- Fetch Paris content separately

Test Case 3: Broad Context
- Input: "Colosseum, Rome", depth=5, context="broad_context"
- Expected: 10% Colosseum, 35% Rome, 20% Italy
- Fetch both Rome and Italy content

PERFORMANCE:
- Maximum 3 parallel collection calls (primary + city + country)
- Use asyncio.gather() for parallel fetching
- Target <8 seconds total (primary 5s + additional 3s)
- Skip unnecessary collections to save time

INTEGRATION:
Update podcast_service.py:
```python
# Before
content_data = await content_aggregator.gather_location_content(location)

# After  
hierarchical_content = await hierarchical_collector.collect_hierarchical_content(
    location, 
    user_preferences
)
```

DELIVERABLES:
1. hierarchical_collector.py (complete implementation)
2. Updated podcast_service.py (use hierarchical collector)
3. Tests for all 3 context preferences
4. Documentation on weight calculation logic

SUCCESS CRITERIA:
- Multi-level content collected correctly
- Weights sum to 1.0 for available levels
- Performance <8 seconds for broad_context
- Graceful handling of missing hierarchy levels
- User preferences properly applied
```

---

### ENHANCEMENT 1.3: QUESTION-BASED DEEP RESEARCH

**Research Finding:** Best practice is to use "deep research" agents for complex question answering.

**Architecture Options:**

1. **OpenAI Deep Research API** (Premium, most capable)
   - Powered by o3 model with RL training
   - Multi-step autonomous research
   - Cost: ~$0.50-$1.00 per query
   
2. **Perplexity Deep Research** (Recommended - Already have API key!)
   - Free tier available, Pro unlimited
   - 2-4 minute research time
   - Dozens of searches, hundreds of sources
   
3. **Gemini Deep Research** (Alternative)
   - Google's research agent
   - Integrated with Google Search

**Implementation Strategy:** Use **Perplexity Deep Research** (already configured!)

```python
# backend/app/services/research/deep_research_service.py

import aiohttp
import asyncio
from typing import Dict, Optional
from app.core.config import settings
from app.core.logging import logger

class DeepResearchService:
    """
    Deep research service using Perplexity's research capabilities.
    For complex questions requiring multi-step investigation.
    
    Use cases:
    - "What led to the fall of the Roman Empire?"
    - "How did Japanese tea ceremony influence architecture?"
    - "What's the history of quantum computing?"
    """
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=180),  # 3 minutes for deep research
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def research_question(
        self,
        question: str,
        depth_level: int = 3,
        focus_areas: List[str] = None
    ) -> Dict:
        """
        Conduct deep research on a complex question.
        
        Args:
            question: Research question
            depth_level: 1-6 scale (affects prompt complexity)
            focus_areas: Optional focus areas to guide research
            
        Returns:
            {
                "question": str,
                "comprehensive_answer": str,
                "key_findings": List[str],
                "sources": List[Dict],
                "confidence": float,
                "research_time": float
            }
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Build research prompt
            research_prompt = self._build_research_prompt(
                question, depth_level, focus_areas
            )
            
            # Make deep research request
            session = await self._get_session()
            
            payload = {
                "model": "sonar-pro",  # Perplexity's research model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert research assistant conducting comprehensive research. Provide detailed, well-sourced answers with specific facts, examples, and context."
                    },
                    {
                        "role": "user",
                        "content": research_prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.3,  # Lower for factual accuracy
                "search_domain_filter": [],  # No domain restrictions
                "search_recency_filter": "month"  # Recent sources
            }
            
            async with session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract answer and citations
                    answer = data["choices"][0]["message"]["content"]
                    citations = data.get("citations", [])
                    
                    # Parse structured response
                    research_result = self._parse_research_response(
                        answer, citations, question
                    )
                    
                    research_result["research_time"] = asyncio.get_event_loop().time() - start_time
                    
                    logger.info(f"Deep research completed in {research_result['research_time']:.1f}s")
                    
                    return research_result
                else:
                    error_text = await response.text()
                    logger.error(f"Deep research failed: HTTP {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}", "question": question}
                    
        except Exception as e:
            logger.error(f"Deep research exception: {e}")
            return {"error": str(e), "question": question}
    
    def _build_research_prompt(
        self,
        question: str,
        depth_level: int,
        focus_areas: List[str]
    ) -> str:
        """
        Build research prompt tailored to depth level and focus areas.
        """
        depth_instructions = {
            1: "Provide a brief overview suitable for a general audience.",
            2: "Provide essential facts and basic context.",
            3: "Provide comprehensive information with historical context and multiple perspectives.",
            4: "Provide advanced analysis with scholarly sources and detailed examples.",
            5: "Provide expert-level investigation with academic rigor and complex relationships.",
            6: "Provide research-grade analysis with theoretical frameworks and methodological considerations."
        }
        
        prompt_parts = [
            f"Conduct comprehensive research on the following question:",
            f"\n**Question:** {question}\n",
            f"**Depth:** {depth_instructions.get(depth_level, depth_instructions[3])}"
        ]
        
        if focus_areas:
            prompt_parts.append(f"\n**Focus Areas:** {', '.join(focus_areas)}")
        
        prompt_parts.extend([
            "\n**Requirements:**",
            "- Provide a comprehensive, well-structured answer",
            "- Include specific facts, dates, and examples",
            "- Explain key concepts and their relationships",
            "- Discuss multiple perspectives where relevant",
            "- Cite sources for major claims",
            "- Organize information logically",
            "\n**Format your response as:**",
            "1. Overview (2-3 sentences)",
            "2. Key Findings (3-5 main points with details)",
            "3. Detailed Explanation (main body of research)",
            "4. Conclusion (synthesis and significance)"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_research_response(
        self,
        answer: str,
        citations: List[str],
        question: str
    ) -> Dict:
        """
        Parse Perplexity's research response into structured format.
        """
        # Split answer into sections (basic parsing)
        sections = answer.split("\n\n")
        
        # Extract key findings (look for numbered lists or bullet points)
        key_findings = []
        for section in sections:
            if any(marker in section for marker in ["1.", "2.", "3.", "-", "•"]):
                # Split into individual findings
                findings = [
                    line.strip() 
                    for line in section.split("\n") 
                    if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith(("-", "•")))
                ]
                key_findings.extend(findings[:5])  # Limit to top 5
        
        # Format sources from citations
        sources = [
            {
                "url": citation,
                "type": "web",
                "retrieved_from": "perplexity_deep_research"
            }
            for citation in citations[:10]  # Limit to top 10 sources
        ]
        
        # Estimate confidence based on citation count and answer length
        confidence = min(
            1.0,
            (len(citations) * 0.05) + (len(answer) / 5000)
        )
        
        return {
            "question": question,
            "comprehensive_answer": answer,
            "key_findings": key_findings,
            "sources": sources,
            "confidence": round(confidence, 2),
            "research_method": "perplexity_deep_research"
        }
    
    async def close(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

# Singleton instance
deep_research_service = DeepResearchService()
```

**Integration with Question Detection:**

```python
# backend/app/services/content/question_detector.py

import re
from typing import Dict, Optional

class QuestionDetector:
    """
    Detect if user input is a question vs a location.
    Routes to appropriate collection strategy.
    """
    
    def __init__(self):
        self.question_patterns = [
            r"^(what|why|how|when|where|who|which)",
            r"\?$",  # Ends with question mark
            r"(explain|describe|tell me about|history of|story of)",
            r"(led to|resulted in|caused|influenced)",
        ]
        
    def is_question(self, user_input: str) -> bool:
        """
        Determine if input is a question requiring deep research.
        
        Examples:
        - "What led to the fall of Rome?" → True
        - "Paris, France" → False
        - "History of quantum computing" → True
        - "Tokyo Tower" → False
        """
        user_input_lower = user_input.lower().strip()
        
        # Check against question patterns
        for pattern in self.question_patterns:
            if re.search(pattern, user_input_lower):
                return True
        
        # Check for question words in first 3 words
        words = user_input_lower.split()[:3]
        question_words = ["what", "why", "how", "when", "where", "who", "which", "explain", "describe"]
        
        if any(qw in words for qw in question_words):
            return True
        
        return False
    
    def extract_location_from_question(self, question: str) -> Optional[str]:
        """
        Extract location from questions like:
        "What's the history of Tokyo?"
        "Why is Paris famous?"
        
        Returns location name or None.
        """
        # Pattern: "of {LOCATION}"
        of_match = re.search(r"of ([A-Z][a-zA-Z\s,]+?)[\?.]", question)
        if of_match:
            return of_match.group(1).strip()
        
        # Pattern: "in {LOCATION}"
        in_match = re.search(r"in ([A-Z][a-zA-Z\s,]+?)[\?.]", question)
        if in_match:
            return in_match.group(1).strip()
        
        return None

# Singleton instance
question_detector = QuestionDetector()
```

**WINDSURF PROMPT 1C: Question-Based Deep Research**

```
TASK: Implement question-based deep research using Perplexity API

CURRENT STATE:
- Perplexity API already configured (PERPLEXITY_API_KEY in .env)
- Currently only used for script generation
- No question detection or deep research capability

REQUIREMENTS:

1. CREATE DEEP RESEARCH SERVICE (backend/app/services/research/deep_research_service.py):
   - Use Perplexity Sonar Pro model for research
   - Build depth-appropriate research prompts (6 depth levels)
   - Request comprehensive, well-structured answers
   - Parse response into structured format (overview, key findings, explanation, conclusion)
   - Extract citations from response
   - Calculate confidence score based on citations + answer length
   - 3-minute timeout for complex research

2. CREATE QUESTION DETECTOR (backend/app/services/content/question_detector.py):
   - Detect if input is question vs location using regex patterns
   - Question indicators: starts with what/why/how/when/where/who, ends with ?, contains "explain/describe/history of"
   - Extract location from questions ("What's the history of Tokyo?" → "Tokyo")
   - Return boolean for is_question() method

3. INTEGRATE WITH PODCAST SERVICE (backend/app/services/podcast_service.py):
   - Check if input is question using question_detector
   - If question: use deep_research_service.research_question()
   - If location: use hierarchical_collector (existing flow)
   - Pass depth_level from user preferences to research service
   - Combine research results with location context if location extracted

PERPLEXITY API CONFIGURATION:
Endpoint: https://api.perplexity.ai/chat/completions
Model: sonar-pro (research-optimized)
Parameters:
- max_tokens: 4000 (long research responses)
- temperature: 0.3 (factual accuracy over creativity)
- search_recency_filter: "month" (recent sources)
Headers:
- Authorization: Bearer {PERPLEXITY_API_KEY}
- Content-Type: application/json

RESEARCH PROMPT STRUCTURE:
```
Conduct comprehensive research on the following question:

**Question:** {user_question}
**Depth:** {depth_instruction_based_on_user_depth_preference}
**Focus Areas:** {optional_focus_areas}

**Requirements:**
- Provide comprehensive, well-structured answer
- Include specific facts, dates, examples
- Explain key concepts and relationships
- Discuss multiple perspectives where relevant
- Cite sources for major claims
- Organize information logically

**Format your response as:**
1. Overview (2-3 sentences)
2. Key Findings (3-5 main points with details)
3. Detailed Explanation (main body of research)
4. Conclusion (synthesis and significance)
```

DEPTH INSTRUCTIONS:
Depth 1-2: "Provide brief overview suitable for general audience"
Depth 3-4: "Provide comprehensive information with historical context and multiple perspectives"
Depth 5-6: "Provide expert-level investigation with academic rigor and complex relationships"

DATA STRUCTURES:
Question detection:
{
  "is_question": bool,
  "extracted_location": str | None,
  "question_type": str  # "what", "why", "how", etc.
}

Research result:
{
  "question": str,
  "comprehensive_answer": str (full research text),
  "key_findings": List[str] (3-5 main points),
  "sources": List[Dict] (citations with URLs),
  "confidence": float (0.0-1.0),
  "research_time": float (seconds),
  "research_method": "perplexity_deep_research"
}

TESTING:
Test Case 1: Simple Question
- Input: "What is the Eiffel Tower?"
- Expected: is_question=True, extracted_location="Eiffel Tower"
- Research should provide history, facts, significance

Test Case 2: Complex Question
- Input: "Why did the Roman Empire fall?"
- Expected: is_question=True, comprehensive research with multiple factors
- Should cite historical sources, provide analysis

Test Case 3: Not a Question
- Input: "Paris, France"
- Expected: is_question=False, use normal location collection

INTEGRATION LOGIC (podcast_service.py):
```python
# Check if input is question
detection = question_detector.is_question(location_or_question)

if detection:
    # Deep research path
    research_result = await deep_research_service.research_question(
        location_or_question,
        depth_level=user_preferences.get("depth_preference", 3)
    )
    
    # Optional: Also get location context if location extracted
    extracted_location = question_detector.extract_location_from_question(location_or_question)
    if extracted_location:
        location_context = await hierarchical_collector.collect_hierarchical_content(
            extracted_location,
            user_preferences
        )
        # Combine research + location context
    
    content_data = research_result
else:
    # Normal location path (existing)
    content_data = await hierarchical_collector.collect_hierarchical_content(
        location_or_question,
        user_preferences
    )
```

PERFORMANCE:
- Question detection: <10ms (regex patterns)
- Deep research: 30-180 seconds (depends on complexity)
- Show progress to user: "Researching your question..."
- Timeout at 3 minutes, return partial results if available

DELIVERABLES:
1. deep_research_service.py (complete implementation)
2. question_detector.py (complete implementation)
3. Updated podcast_service.py (question routing logic)
4. Tests for question detection and research
5. Documentation on research prompt engineering

SUCCESS CRITERIA:
- Correctly identifies questions vs locations (>95% accuracy)
- Research responses comprehensive and well-structured
- Citations included in research results
- Depth level properly applied to research prompts
- Integration seamless with existing location flow
- Performance acceptable (30-180s for complex questions)
```

---

### ENHANCEMENT 1.4: ACTIVATE STANDOUT DETECTION

**Current State:** Standout detection code exists (1,500 lines) but is NOT integrated.

**File:** `backend/app/services/detection/standout_detector.py` (already implemented)

**Integration Task:** Connect standout detector to content collection pipeline.

```python
# backend/app/services/content/enhanced_aggregator.py

from app.services.content.content_aggregator import content_aggregator
from app.services.detection.standout_detector import standout_detector
from app.core.logging import logger
from typing import Dict

class EnhancedContentAggregator:
    """
    Enhanced aggregator that integrates standout detection.
    Adds quality classification to collected content.
    """
    
    def __init__(self):
        self.aggregator = content_aggregator
        self.detector = standout_detector
        
    async def gather_and_classify_content(
        self,
        location_name: str,
        podcast_type: str = "base"
    ) -> Dict:
        """
        Gather content and classify for standout qualities.
        
        Returns aggregated content with:
        - standout_score: 0.0-1.0
        - standout_categories: List[str]
        - classification: "mundane", "interesting", "standout", "exceptional"
        """
        try:
            # Step 1: Gather content from all sources
            content = await self.aggregator.gather_location_content(location_name, podcast_type)
            
            if not content or content.get("error"):
                return content
            
            # Step 2: Run standout detection (only if podcast_type includes standout)
            if podcast_type in ["standout", "personalized"]:
                standout_analysis = await self.detector.detect_standout_content(content)
                
                # Add standout analysis to content
                content["standout_analysis"] = {
                    "standout_score": standout_analysis.get("overall_score", 0.0),
                    "standout_categories": standout_analysis.get("categories", []),
                    "classification": self._classify_by_score(standout_analysis.get("overall_score", 0.0)),
                    "detection_methods": standout_analysis.get("methods_triggered", []),
                    "reasoning": standout_analysis.get("reasoning", "")
                }
                
                logger.info(
                    f"Standout detection: {location_name} scored {standout_analysis.get('overall_score', 0.0):.2f}"
                )
            else:
                content["standout_analysis"] = None
            
            return content
            
        except Exception as e:
            logger.error(f"Enhanced content aggregation failed: {e}")
            return {"error": str(e), "location_name": location_name}
    
    def _classify_by_score(self, score: float) -> str:
        """
        Classify content by standout score.
        
        0.0-0.3: mundane (common, everyday)
        0.3-0.5: interesting (noteworthy but not unique)
        0.5-0.8: standout (remarkable, unusual)
        0.8-1.0: exceptional (one-of-a-kind, paradigm-shifting)
        """
        if score >= 0.8:
            return "exceptional"
        elif score >= 0.5:
            return "standout"
        elif score >= 0.3:
            return "interesting"
        else:
            return "mundane"

# Singleton instance
enhanced_aggregator = EnhancedContentAggregator()
```

**WINDSURF PROMPT 1D: Activate Standout Detection**

```
TASK: Integrate existing standout detection code into content pipeline

CURRENT STATE:
- Standout detector code exists at backend/app/services/detection/standout_detector.py
- ~1,500 lines of code with 9 detection methods
- NOT currently integrated with content collection
- Target: 80% Tier 1 accuracy (from master plan)

REQUIREMENTS:

1. CREATE ENHANCED AGGREGATOR (backend/app/services/content/enhanced_aggregator.py):
   - Wrap existing content_aggregator
   - Call standout_detector.detect_standout_content() after content collection
   - Add standout_analysis to aggregated content
   - Only run detection for "standout" and "personalized" podcast types
   - Classify content by score: mundane (<0.3), interesting (0.3-0.5), standout (0.5-0.8), exceptional (>0.8)

2. UPDATE PODCAST SERVICE (backend/app/services/podcast_service.py):
   - Replace content_aggregator with enhanced_aggregator
   - Pass podcast_type to aggregator
   - Use standout_analysis in narrative generation (if available)

3. STANDOUT ANALYSIS STRUCTURE:
   ```python
   content["standout_analysis"] = {
       "standout_score": float (0.0-1.0),
       "standout_categories": List[str] (e.g., ["impossibility", "uniqueness"]),
       "classification": str ("mundane" | "interesting" | "standout" | "exceptional"),
       "detection_methods": List[str] (methods that triggered),
       "reasoning": str (explanation of why standout)
   }
   ```

4. PRESERVE EXISTING DETECTION METHODS:
   The standout_detector already implements:
   - impossibility_detection
   - uniqueness_verification
   - temporal_analysis
   - cultural_anomaly
   - atlas_obscura
   - historical_peculiarity
   - geographic_rarity
   - linguistic_anomaly
   - cross_cultural
   
   DO NOT modify these methods - just integrate them.

5. CONDITIONAL EXECUTION:
   - podcast_type="base" → Skip standout detection (save processing time)
   - podcast_type="standout" → Run standout detection
   - podcast_type="topic" → Skip standout detection
   - podcast_type="personalized" → Run standout detection

INTEGRATION FLOW:
```
User Request (podcast_type="standout")
  ↓
enhanced_aggregator.gather_and_classify_content()
  ↓
content_aggregator.gather_location_content() (Phase 1A)
  ↓
standout_detector.detect_standout_content() (existing code)
  ↓
Add standout_analysis to content
  ↓
Return to podcast_service
  ↓
narrative_engine uses standout_analysis for script
```

TESTING:
Test Case 1: Standout Location
- Input: "Salar de Uyuni, Bolivia" (world's largest salt flat)
- Expected: standout_score > 0.7, classification="standout"
- Methods: geographic_rarity, impossibility

Test Case 2: Normal Location
- Input: "Paris, France"
- Expected: standout_score 0.3-0.5, classification="interesting"

Test Case 3: Base Podcast (Skip Detection)
- Input: "Tokyo, Japan", podcast_type="base"
- Expected: standout_analysis = None (not run)

PERFORMANCE:
- Standout detection should add <2 seconds to total time
- Run detection only when needed (conditional)
- Log detection results for observability

FILES TO MODIFY:
1. Create: backend/app/services/content/enhanced_aggregator.py
2. Update: backend/app/services/podcast_service.py (line ~85-100)
3. Update: backend/app/services/narrative/script_assembly.py (use standout_analysis if available)

DELIVERABLES:
1. enhanced_aggregator.py (complete implementation)
2. Updated podcast_service.py (use enhanced aggregator)
3. Updated script_assembly.py (integrate standout scores)
4. Tests for standout integration
5. Documentation on classification thresholds

SUCCESS CRITERIA:
- Standout detection correctly integrated
- Conditional execution working (only for standout/personalized types)
- Performance impact <2 seconds
- Classification thresholds validated
- Standout analysis used in narrative generation
- Existing detection accuracy preserved (80% Tier 1)
```

---

## 📝 PART 2: ENHANCED SCRIPT GENERATION ENGINE

### Current State Analysis

**What Works:**
- ✅ Narrative engine with 5 templates (500+ lines)
- ✅ Script assembly with 4 formats (600+ lines)
- ✅ Quality control framework (700+ lines)
- ✅ TTS optimization (400+ lines)

**Critical Issues:**
- ❌ Perplexity returns template text ("Let's continue...")
- ❌ Incomplete responses from AI
- ❌ Scripts lack real information (empty podcast keywords)
- ❌ Quality checks may not be running
- ❌ Information not properly integrated into narrative

**Research Findings - Best Practices 2025:**

1. **Prompt Engineering** (Critical!)
   - Use CLEAR framework: Concise, Logical, Explicit, Adaptive, Reflective
   - Provide specific output format specifications
   - Include examples of desired output
   - Use step-by-step instructions
   - Iterate and refine prompts based on results

2. **Information-Rich Scripts**
   - Weave facts into narrative naturally
   - Use storytelling techniques (not lists of facts)
   - Connect information with transitions
   - Provide context for every fact
   - Avoid "podcast filler" phrases

3. **Quality Assurance**
   - Validate completeness before returning
   - Check for template text patterns
   - Verify information density
   - Ensure logical flow

---

### ENHANCEMENT 2.1: IMPROVED PERPLEXITY PROMPTS

**Root Cause:** Current prompts are too vague, allowing Perplexity to return incomplete responses.

**Solution:** Research-based prompt engineering with explicit format requirements.

```python
# backend/app/services/narrative/enhanced_podcast_generator.py

from typing import Dict, List
import aiohttp
from app.core.config import settings
from app.core.logging import logger

class EnhancedPodcastGenerator:
    """
    Enhanced podcast script generator with research-based prompt engineering.
    Fixes template text issues and ensures information-rich output.
    """
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.session = None
        
    async def generate_information_rich_script(
        self,
        content_data: Dict,
        podcast_type: str,
        target_duration_minutes: int,
        user_preferences: Dict = None
    ) -> Dict:
        """
        Generate information-rich podcast script using enhanced prompts.
        
        Returns:
        {
            "script": str (complete podcast script),
            "metadata": Dict,
            "quality_metrics": Dict,
            "generation_method": str
        }
        """
        try:
            # Build enhanced prompt with explicit requirements
            prompt = self._build_enhanced_prompt(
                content_data,
                podcast_type,
                target_duration_minutes,
                user_preferences
            )
            
            # Generate script with validation
            script = await self._generate_with_validation(prompt, max_retries=2)
            
            # Validate script quality
            quality_metrics = self._validate_script_quality(script, content_data)
            
            if quality_metrics["has_template_text"]:
                logger.warning("Template text detected, regenerating...")
                # Retry with stricter prompt
                prompt = self._build_stricter_prompt(content_data, podcast_type, target_duration_minutes)
                script = await self._generate_with_validation(prompt, max_retries=1)
                quality_metrics = self._validate_script_quality(script, content_data)
            
            return {
                "script": script,
                "metadata": {
                    "podcast_type": podcast_type,
                    "target_duration": target_duration_minutes,
                    "actual_word_count": len(script.split()),
                    "estimated_duration": len(script.split()) / 150  # 150 words/minute
                },
                "quality_metrics": quality_metrics,
                "generation_method": "enhanced_perplexity_prompting"
            }
            
        except Exception as e:
            logger.error(f"Enhanced script generation failed: {e}")
            return {"error": str(e), "generation_method": "failed"}
    
    def _build_enhanced_prompt(
        self,
        content_data: Dict,
        podcast_type: str,
        target_duration: int,
        user_preferences: Dict
    ) -> str:
        """
        Build enhanced prompt using CLEAR framework and explicit requirements.
        
        CLEAR Framework:
        - Concise: Remove superfluous language
        - Logical: Structured flow of instructions
        - Explicit: Precise output specifications
        - Adaptive: Flexible based on content
        - Reflective: Self-checking instructions
        """
        
        # Calculate target word count (150 words/minute for podcasts)
        target_words = target_duration * 150
        
        # Extract key information from content
        location_name = content_data.get("location_name", "this location")
        facts = self._extract_key_facts(content_data)
        hierarchy = content_data.get("hierarchy", {})
        
        # Build structured prompt
        prompt_parts = [
            "# PODCAST SCRIPT GENERATION TASK",
            "",
            "## OBJECTIVE",
            f"Write a complete, information-rich {target_duration}-minute podcast script about {location_name}.",
            f"Target: {target_words} words (150 words/minute speaking pace).",
            "",
            "## CRITICAL REQUIREMENTS",
            "- Write the COMPLETE script from start to finish",
            "- DO NOT use placeholder text like 'Let's continue...' or '[More content here]'",
            "- DO NOT stop mid-sentence or mid-section",
            "- Include ALL sections: introduction, main content, conclusion",
            "- Weave facts naturally into narrative (not as lists)",
            "- Use specific examples and concrete details",
            "- NO generic podcast filler phrases",
            "",
            "## CONTENT TO INCLUDE",
            self._format_facts_for_prompt(facts, hierarchy),
            "",
            "## STRUCTURE (REQUIRED)",
            f"1. **Hook/Introduction** (30 seconds, ~75 words)",
            f"   - Captivating opening about {location_name}",
            f"   - Set scene and context",
            f"   - Preview key points",
            "",
            f"2. **Main Content** ({target_duration - 1} minutes, ~{target_words - 225} words)",
            f"   - Weave facts into narrative flow",
            f"   - Connect information with smooth transitions",
            f"   - Use storytelling techniques",
            f"   - Provide specific examples and details",
            f"   - Explain significance and context",
            "",
            "3. **Conclusion** (30 seconds, ~75 words)",
            "   - Summarize key takeaways",
            "   - Memorable closing",
            "",
            "## STYLE GUIDELINES",
            "- Conversational yet informative",
            "- Natural transitions between topics",
            "- Vary sentence length for rhythm",
            "- Use vivid, descriptive language",
            "- Avoid repetitive phrases",
            "",
            "## VALIDATION CHECKLIST (Before finishing)",
            "- [ ] Script is complete (no 'Let's continue...')",
            "- [ ] All sections present (intro, main, conclusion)",
            f"- [ ] Word count near {target_words} words",
            "- [ ] Facts woven into narrative naturally",
            "- [ ] Specific examples provided",
            "- [ ] Smooth transitions throughout",
            "",
            "## OUTPUT FORMAT",
            "Provide ONLY the podcast script text.",
            "Do NOT include meta-commentary, section labels in the script, or notes.",
            "Write as if this is the final, polished script ready for voice recording.",
            "",
            "---",
            "",
            "BEGIN SCRIPT:"
        ]
        
        return "\n".join(prompt_parts)
    
    def _extract_key_facts(self, content_data: Dict) -> List[str]:
        """
        Extract the most important facts from collected content.
        Prioritize interesting, specific, concrete information.
        """
        facts = []
        
        # From Wikipedia interesting facts
        wikipedia_data = content_data.get("sources", {}).get("wikipedia", {})
        if wikipedia_data.get("interesting_facts"):
            facts.extend(wikipedia_data["interesting_facts"][:5])
        
        # From Wikidata structured facts
        wikidata_data = content_data.get("sources", {}).get("wikidata", {})
        if wikidata_data.get("structured_facts"):
            for fact in wikidata_data["structured_facts"][:5]:
                fact_str = f"{fact.get('property')}: {fact.get('value')}"
                facts.append(fact_str)
        
        # From standout analysis (if available)
        if content_data.get("standout_analysis"):
            reasoning = content_data["standout_analysis"].get("reasoning")
            if reasoning:
                facts.append(f"Notable: {reasoning}")
        
        return facts
    
    def _format_facts_for_prompt(self, facts: List[str], hierarchy: Dict) -> str:
        """
        Format facts and hierarchy information for inclusion in prompt.
        """
        lines = []
        
        if hierarchy:
            lines.append("**Geographic Context:**")
            for level, value in hierarchy.items():
                if value:
                    lines.append(f"- {level.capitalize()}: {value}")
            lines.append("")
        
        if facts:
            lines.append("**Key Facts to Include (weave naturally):**")
            for i, fact in enumerate(facts[:10], 1):  # Max 10 facts
                lines.append(f"{i}. {fact}")
        
        return "\n".join(lines) if lines else "No specific facts provided."
    
    async def _generate_with_validation(self, prompt: str, max_retries: int = 2) -> str:
        """
        Generate script with automatic validation and retry.
        """
        for attempt in range(max_retries + 1):
            try:
                script = await self._call_perplexity_api(prompt)
                
                # Basic validation
                if len(script) < 300:
                    logger.warning(f"Script too short ({len(script)} chars), attempt {attempt + 1}")
                    continue
                
                if "let's continue" in script.lower() or "[more content" in script.lower():
                    logger.warning(f"Template text detected, attempt {attempt + 1}")
                    continue
                
                # Validation passed
                return script
                
            except Exception as e:
                logger.error(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise
        
        # If all retries failed, return what we have
        return script
    
    async def _call_perplexity_api(self, prompt: str) -> str:
        """
        Call Perplexity API with proper configuration.
        """
        session = await self._get_session()
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert podcast scriptwriter. You create complete, polished scripts that are ready for voice recording. You NEVER use placeholder text or incomplete sections."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.7,  # Balanced creativity and consistency
            "top_p": 0.9
        }
        
        async with session.post(self.base_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                script = data["choices"][0]["message"]["content"]
                return script.strip()
            else:
                error_text = await response.text()
                raise Exception(f"Perplexity API error: HTTP {response.status} - {error_text}")
    
    def _validate_script_quality(self, script: str, content_data: Dict) -> Dict:
        """
        Validate script quality with multiple checks.
        
        Returns:
        {
            "is_complete": bool,
            "has_template_text": bool,
            "information_density": float (0.0-1.0),
            "has_introduction": bool,
            "has_conclusion": bool,
            "passes_validation": bool
        }
        """
        metrics = {
            "is_complete": True,
            "has_template_text": False,
            "information_density": 0.0,
            "has_introduction": False,
            "has_conclusion": False,
            "passes_validation": False
        }
        
        script_lower = script.lower()
        
        # Check for template text
        template_indicators = [
            "let's continue",
            "[more content",
            "[continue here",
            "to be continued",
            "..."
        ]
        metrics["has_template_text"] = any(indicator in script_lower for indicator in template_indicators)
        
        # Check completeness (minimum length)
        metrics["is_complete"] = len(script) >= 500
        
        # Check for introduction (should be near start)
        first_200_chars = script[:200].lower()
        intro_words = ["welcome", "today", "discover", "explore", "join", "imagine"]
        metrics["has_introduction"] = any(word in first_200_chars for word in intro_words)
        
        # Check for conclusion (should be near end)
        last_200_chars = script[-200:].lower()
        conclusion_words = ["finally", "in conclusion", "to sum up", "remember", "thank you"]
        metrics["has_conclusion"] = any(word in last_200_chars for word in conclusion_words)
        
        # Calculate information density (ratio of content words to filler words)
        words = script.split()
        filler_words = ["um", "uh", "like", "you know", "basically", "actually"]
        content_words = [w for w in words if w.lower() not in filler_words]
        metrics["information_density"] = len(content_words) / max(len(words), 1)
        
        # Overall pass/fail
        metrics["passes_validation"] = (
            metrics["is_complete"] and
            not metrics["has_template_text"] and
            metrics["information_density"] > 0.85 and
            metrics["has_introduction"] and
            metrics["has_conclusion"]
        )
        
        return metrics
    
    def _build_stricter_prompt(
        self,
        content_data: Dict,
        podcast_type: str,
        target_duration: int
    ) -> str:
        """
        Build stricter prompt when first attempt returns template text.
        """
        target_words = target_duration * 150
        location_name = content_data.get("location_name", "this location")
        
        prompt = f"""
        URGENT SCRIPT COMPLETION TASK

        Previous attempt returned incomplete script with template text.
        This is NOT acceptable.

        TASK: Write a COMPLETE, FINISHED podcast script about {location_name}.

        ABSOLUTE REQUIREMENTS:
        1. Write EXACTLY {target_words} words (count them!)
        2. NO placeholder text whatsoever
        3. NO "Let's continue..." or similar phrases
        4. Complete introduction, body, and conclusion
        5. Every sentence must be finished
        6. Script must be 100% ready for voice recording

        If you cannot write the complete script, do not start.
        If you start, you MUST finish completely.

        Write the script now. BEGIN:
        """
        
        return prompt
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

# Singleton instance
enhanced_podcast_generator = EnhancedPodcastGenerator()
```

**WINDSURF PROMPT 2A: Enhanced Script Generation with Prompt Engineering**

```
TASK: Fix Perplexity script generation using research-based prompt engineering

CURRENT PROBLEM:
- Perplexity returns template text ("Let's continue...")
- Scripts incomplete and low quality
- Missing real information
- Located at backend/app/services/narrative/podcast_generator.py

ROOT CAUSE:
- Prompts too vague
- No explicit completeness requirements
- No validation of output
- No retry mechanism

SOLUTION: Implement CLEAR framework prompt engineering

REQUIREMENTS:

1. CREATE ENHANCED GENERATOR (backend/app/services/narrative/enhanced_podcast_generator.py):
   - Build structured prompts using CLEAR framework:
     * Concise: Remove superfluous language
     * Logical: Structured flow of instructions
     * Explicit: Precise output format specifications
     * Adaptive: Flexible based on content
     * Reflective: Self-checking validation
   
   - Include in every prompt:
     * Exact word count target (duration * 150 words/min)
     * Complete structure requirements (intro, main, conclusion)
     * Explicit ban on template text
     * Validation checklist
     * Output format specification
   
   - Implement validation:
     * Check script length (>500 chars minimum)
     * Detect template text patterns
     * Verify introduction and conclusion present
     * Calculate information density
   
   - Auto-retry mechanism:
     * If template text detected, regenerate with stricter prompt
     * Max 2 retries
     * Log all attempts

2. PROMPT STRUCTURE (EXACT FORMAT):
   ```
   # PODCAST SCRIPT GENERATION TASK

   ## OBJECTIVE
   Write a complete, information-rich {duration}-minute podcast script about {location}.
   Target: {word_count} words (150 words/minute speaking pace).

   ## CRITICAL REQUIREMENTS
   - Write the COMPLETE script from start to finish
   - DO NOT use placeholder text like 'Let's continue...'
   - DO NOT stop mid-sentence or mid-section
   - Include ALL sections: introduction, main content, conclusion
   - Weave facts naturally into narrative
   - Use specific examples and concrete details

   ## CONTENT TO INCLUDE
   {formatted_facts_and_hierarchy}

   ## STRUCTURE (REQUIRED)
   1. Hook/Introduction (30 seconds, ~75 words)
   2. Main Content ({duration-1} minutes, ~{word_count-150} words)
   3. Conclusion (30 seconds, ~75 words)

   ## STYLE GUIDELINES
   - Conversational yet informative
   - Natural transitions between topics
   - Vary sentence length
   - Vivid, descriptive language

   ## VALIDATION CHECKLIST
   - [ ] Script is complete
   - [ ] All sections present
   - [ ] Word count near target
   - [ ] Facts woven naturally
   - [ ] Smooth transitions

   ## OUTPUT FORMAT
   Provide ONLY the podcast script text.
   No meta-commentary, section labels, or notes.

   BEGIN SCRIPT:
   ```

3. VALIDATION METRICS:
   ```python
   quality_metrics = {
       "is_complete": bool,  # >500 chars
       "has_template_text": bool,  # Check for indicators
       "information_density": float,  # Content words / total words
       "has_introduction": bool,  # Intro words in first 200 chars
       "has_conclusion": bool,  # Conclusion words in last 200 chars
       "passes_validation": bool  # All checks pass
   }
   ```

4. TEMPLATE TEXT DETECTION:
   Indicators to check:
   - "let's continue"
   - "[more content"
   - "[continue here"
   - "to be continued"
   - "..."

5. INTEGRATION (backend/app/services/podcast_service.py):
   Replace:
   ```python
   # Old
   script = await podcast_generator.generate_script(content_data)
   
   # New
   script_result = await enhanced_podcast_generator.generate_information_rich_script(
       content_data,
       podcast_type,
       target_duration=10,  # minutes
       user_preferences
   )
   script = script_result["script"]
   quality_metrics = script_result["quality_metrics"]
   ```

PERPLEXITY API CONFIGURATION:
Model: sonar-pro
Max tokens: 4000 (long scripts)
Temperature: 0.7 (balanced)
Top_p: 0.9
System message: "You are an expert podcast scriptwriter. You create complete, polished scripts ready for voice recording. You NEVER use placeholder text."

TESTING:
Test Case 1: Normal Location
- Input: Content for "Paris, France", duration=10 min
- Expected: 1500-word complete script, no template text
- Validate: All sections present, information_density >0.85

Test Case 2: Retry on Template Text
- Simulate template text in first response
- Expected: Automatic retry with stricter prompt
- Validate: Second attempt successful

Test Case 3: Information Integration
- Input: Content with 10 specific facts
- Expected: Facts woven naturally into narrative
- Validate: All facts mentioned, not as list

PERFORMANCE:
- First generation: 10-20 seconds
- With retry: 20-40 seconds
- Timeout: 60 seconds
- Log generation time and retry attempts

FILES:
1. Create: backend/app/services/narrative/enhanced_podcast_generator.py
2. Update: backend/app/services/podcast_service.py (use enhanced generator)
3. Update: backend/app/services/narrative/__init__.py (export new generator)

DELIVERABLES:
1. enhanced_podcast_generator.py (complete implementation)
2. Updated podcast_service.py integration
3. Tests for prompt validation and retry mechanism
4. Documentation on prompt engineering methodology
5. Example prompts for different podcast types

SUCCESS CRITERIA:
- Template text eliminated (0% occurrence)
- Scripts always complete (introduction + main + conclusion)
- Information density >0.85
- Word count within 10% of target
- Retry mechanism functional
- Generation time <40 seconds (including retries)
- User satisfaction with script quality >8/10
```

---

### ENHANCEMENT 2.2: INFORMATION INTEGRATION & NARRATIVE FLOW

**Problem:** Scripts lack real information—filled with "podcast filler" instead of facts.

**Solution:** Post-generation fact-weaving and narrative enhancement.

```python
# backend/app/services/narrative/information_weaver.py

from typing import Dict, List
import re

class InformationWeaver:
    """
    Weaves collected facts into generated script naturally.
    Ensures information density and narrative flow.
    """
    
    def __init__(self):
        self.filler_phrases = [
            "as we all know",
            "it's interesting to note",
            "one thing to remember",
            "let's dive in",
            "without further ado",
            "at the end of the day"
        ]
        
    def enhance_script_with_facts(
        self,
        original_script: str,
        content_data: Dict,
        target_fact_count: int = 10
    ) -> Dict:
        """
        Enhance script by weaving in additional facts if missing.
        
        Returns:
        {
            "enhanced_script": str,
            "facts_added": int,
            "information_density_improvement": float,
            "enhancements_made": List[str]
        }
        """
        try:
            # Extract facts from content
            available_facts = self._extract_all_facts(content_data)
            
            # Analyze current script for fact coverage
            facts_in_script = self._count_facts_in_script(original_script, available_facts)
            
            # If script already has enough facts, return as-is
            if facts_in_script >= target_fact_count * 0.8:
                return {
                    "enhanced_script": original_script,
                    "facts_added": 0,
                    "information_density_improvement": 0.0,
                    "enhancements_made": ["No enhancement needed - sufficient facts present"]
                }
            
            # Identify missing facts
            missing_facts = self._identify_missing_facts(original_script, available_facts)
            
            # Weave missing facts into script
            enhanced_script = self._weave_facts_into_script(
                original_script,
                missing_facts[:target_fact_count - facts_in_script]
            )
            
            # Calculate improvements
            original_density = self._calculate_information_density(original_script)
            enhanced_density = self._calculate_information_density(enhanced_script)
            
            return {
                "enhanced_script": enhanced_script,
                "facts_added": len(missing_facts[:target_fact_count - facts_in_script]),
                "information_density_improvement": enhanced_density - original_density,
                "enhancements_made": [
                    f"Wove {len(missing_facts)} additional facts into narrative",
                    f"Information density improved by {(enhanced_density - original_density) * 100:.1f}%"
                ]
            }
            
        except Exception as e:
            logger.error(f"Information weaving failed: {e}")
            return {
                "enhanced_script": original_script,
                "error": str(e)
            }
    
    def _extract_all_facts(self, content_data: Dict) -> List[Dict]:
        """
        Extract all available facts from content data.
        
        Returns list of facts with metadata:
        [
            {"text": "Population: 13.96 million", "category": "demographics", "importance": 0.8},
            ...
        ]
        """
        facts = []
        
        # Wikipedia interesting facts
        wikipedia_data = content_data.get("sources", {}).get("wikipedia", {})
        if wikipedia_data.get("interesting_facts"):
            for fact in wikipedia_data["interesting_facts"]:
                facts.append({
                    "text": fact,
                    "category": "historical",
                    "importance": 0.7,
                    "source": "wikipedia"
                })
        
        # Wikidata structured facts
        wikidata_data = content_data.get("sources", {}).get("wikidata", {})
        if wikidata_data.get("structured_facts"):
            for fact in wikidata_data["structured_facts"]:
                fact_text = f"{fact.get('property')}: {fact.get('value')}"
                facts.append({
                    "text": fact_text,
                    "category": "structured",
                    "importance": 0.9,  # Structured data is high quality
                    "source": "wikidata"
                })
        
        # Geographic context
        geo_context = content_data.get("geographic_context", {})
        if geo_context.get("population"):
            facts.append({
                "text": f"Population: {geo_context['population']:,}",
                "category": "demographics",
                "importance": 0.8,
                "source": "geonames"
            })
        
        # Standout analysis reasoning
        standout_analysis = content_data.get("standout_analysis")
        if standout_analysis and standout_analysis.get("reasoning"):
            facts.append({
                "text": standout_analysis["reasoning"],
                "category": "standout",
                "importance": 1.0,  # Very important
                "source": "standout_detector"
            })
        
        # Sort by importance (highest first)
        facts.sort(key=lambda f: f["importance"], reverse=True)
        
        return facts
    
    def _count_facts_in_script(self, script: str, available_facts: List[Dict]) -> int:
        """
        Count how many available facts are already in the script.
        """
        script_lower = script.lower()
        count = 0
        
        for fact in available_facts:
            # Check if key parts of fact are in script
            fact_keywords = self._extract_keywords(fact["text"])
            
            # If 70% of keywords present, consider fact included
            keywords_present = sum(1 for kw in fact_keywords if kw in script_lower)
            if keywords_present / max(len(fact_keywords), 1) >= 0.7:
                count += 1
        
        return count
    
    def _identify_missing_facts(self, script: str, available_facts: List[Dict]) -> List[Dict]:
        """
        Identify facts that are not yet in the script.
        """
        missing = []
        script_lower = script.lower()
        
        for fact in available_facts:
            fact_keywords = self._extract_keywords(fact["text"])
            keywords_present = sum(1 for kw in fact_keywords if kw in script_lower)
            
            # If <50% of keywords present, fact is missing
            if keywords_present / max(len(fact_keywords), 1) < 0.5:
                missing.append(fact)
        
        return missing
    
    def _weave_facts_into_script(self, script: str, facts_to_add: List[Dict]) -> str:
        """
        Weave facts into script at natural insertion points.
        
        Strategy:
        1. Find paragraph breaks
        2. Insert facts with natural transitions
        3. Maintain narrative flow
        """
        if not facts_to_add:
            return script
        
        # Split into paragraphs
        paragraphs = script.split("\n\n")
        
        # Determine insertion points (evenly distributed)
        num_facts = len(facts_to_add)
        num_paragraphs = len(paragraphs)
        
        if num_paragraphs < 2:
            # Script has no paragraph breaks, add facts at end
            for fact in facts_to_add:
                script += f"\n\n{self._create_transition_sentence(fact)}"
            return script
        
        # Calculate insertion interval
        insertion_interval = max(1, num_paragraphs // (num_facts + 1))
        
        # Insert facts at intervals
        enhanced_paragraphs = []
        fact_index = 0
        
        for i, paragraph in enumerate(paragraphs):
            enhanced_paragraphs.append(paragraph)
            
            # Insert fact after every N paragraphs
            if (i + 1) % insertion_interval == 0 and fact_index < num_facts:
                fact = facts_to_add[fact_index]
                transition_sentence = self._create_transition_sentence(fact)
                enhanced_paragraphs.append(transition_sentence)
                fact_index += 1
        
        # Join back together
        return "\n\n".join(enhanced_paragraphs)
    
    def _create_transition_sentence(self, fact: Dict) -> str:
        """
        Create a natural transition sentence that includes the fact.
        
        Example:
        Fact: "Population: 13.96 million"
        Output: "Home to nearly 14 million people, Tokyo is one of the world's largest cities."
        """
        fact_text = fact["text"]
        category = fact["category"]
        
        # Transition templates by category
        templates = {
            "demographics": [
                f"With {fact_text}, this makes it one of the most populated areas in the region.",
                f"Interestingly, {fact_text}, contributing to its vibrant atmosphere."
            ],
            "historical": [
                f"A fascinating piece of history: {fact_text}",
                f"What makes this particularly interesting is that {fact_text}"
            ],
            "structured": [
                f"Another notable aspect is that {fact_text}",
                f"It's also worth mentioning that {fact_text}"
            ],
            "standout": [
                f"What truly sets this place apart is that {fact_text}",
                f"Perhaps most remarkably, {fact_text}"
            ]
        }
        
        # Select template based on category
        category_templates = templates.get(category, templates["structured"])
        
        # Use first template (could be randomized)
        return category_templates[0]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from a fact.
        """
        # Remove common words
        common_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "of"}
        
        # Split and filter
        words = re.findall(r'\w+', text.lower())
        keywords = [w for w in words if w not in common_words and len(w) > 3]
        
        return keywords
    
    def _calculate_information_density(self, script: str) -> float:
        """
        Calculate information density of script.
        Higher = more informative content, less filler.
        """
        words = script.lower().split()
        total_words = len(words)
        
        # Count filler phrases
        filler_count = sum(
            script.lower().count(phrase) 
            for phrase in self.filler_phrases
        )
        
        # Count numbers (often indicate facts)
        number_count = len(re.findall(r'\d+', script))
        
        # Calculate density
        # More numbers = higher density
        # More filler = lower density
        density = (number_count * 0.5) / max(total_words, 1) - (filler_count * 0.1) / max(total_words, 1)
        
        return max(0.0, min(1.0, density))

# Singleton instance
information_weaver = InformationWeaver()
```

**Implementation Note:** This enhancement can be added in the future but is not critical for Phase 1. The primary fix is the enhanced prompting (2A).

---

## 🎙️ PART 3: AUDIO SYNTHESIS SYSTEM (TTS)

### Current State

**Status:** 0% active (completely disabled despite 2,700 lines of code ready)

**What Exists:**
- ✅ Multi-tier TTS system coded (6 providers)
- ✅ Audio processing pipeline (4 stages)
- ✅ Quality assurance framework
- ✅ Delivery system with CDN

**What's Needed:**
1. Uncomment audio generation code
2. Configure one TTS provider
3. Test end-to-end
4. Add to production

### Research Findings - Best TTS Options 2025

Based on comprehensive research:

**FREE TIER (Start Here):**
1. **Google Cloud TTS** - Best free tier
   - 4M characters/month standard voices
   - 1M characters/month neural voices
   - Good quality (7-8/10)
   - Easy integration

2. **AWS Polly** - Good alternative
   - 5M characters/month (first 12 months)
   - Standard + Neural voices
   - Good quality (7-8/10)

**PREMIUM (High Quality):**
1. **ElevenLabs** - Best quality (10/10)
   - 10k characters/month free
   - $0.30/1M chars after
   - Exceptional voice quality
   - Emotion control

2. **Azure Neural TTS** - Enterprise grade
   - 500k characters/month free
   - $0.016/1M chars after
   - High quality (9/10)

**RECOMMENDATION:** Start with **Google Cloud TTS** (best free tier) + add **ElevenLabs** option for premium users.

---

### ENHANCEMENT 3.1: ACTIVATE AUDIO GENERATION

**Step 1: Configure Google Cloud TTS (Free Tier)**

```python
# backend/app/services/audio/google_tts_service.py

from google.cloud import texttospeech
import asyncio
from typing import Dict
from app.core.config import settings
from app.core.logging import logger

class GoogleTTSService:
    """
    Google Cloud Text-to-Speech integration.
    Free tier: 4M characters/month (standard), 1M characters/month (neural)
    """
    
    def __init__(self):
        # Initialize Google Cloud TTS client
        self.client = None
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize TTS client with credentials."""
        try:
            # Google Cloud credentials from environment or service account file
            self.client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google TTS: {e}")
            self.client = None
    
    async def synthesize_speech(
        self,
        text: str,
        voice_name: str = "en-US-Neural2-A",
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ) -> Dict:
        """
        Synthesize speech from text using Google Cloud TTS.
        
        Args:
            text: Script text to synthesize
            voice_name: Google voice ID (Neural2 voices recommended)
            speaking_rate: 0.25 to 4.0 (1.0 = normal)
            pitch: -20.0 to 20.0 (0.0 = normal)
            
        Returns:
        {
            "audio_content": bytes,
            "audio_format": "mp3",
            "synthesis_time": float,
            "character_count": int,
            "estimated_cost": float
        }
        """
        try:
            if not self.client:
                raise Exception("Google TTS client not initialized")
            
            start_time = asyncio.get_event_loop().time()
            
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_name
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            
            # Perform synthesis (blocking, so run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.client.synthesize_speech,
                synthesis_input,
                voice,
                audio_config
            )
            
            synthesis_time = asyncio.get_event_loop().time() - start_time
            
            # Calculate cost (free tier, but track usage)
            character_count = len(text)
            is_neural = "Neural" in voice_name
            cost_per_char = 0.000016 if is_neural else 0.000004
            estimated_cost = character_count * cost_per_char
            
            logger.info(
                f"Google TTS synthesis complete: {character_count} chars in {synthesis_time:.1f}s, "
                f"estimated cost ${estimated_cost:.4f}"
            )
            
            return {
                "audio_content": response.audio_content,
                "audio_format": "mp3",
                "synthesis_time": synthesis_time,
                "character_count": character_count,
                "estimated_cost": estimated_cost,
                "provider": "google_cloud_tts",
                "voice_used": voice_name
            }
            
        except Exception as e:
            logger.error(f"Google TTS synthesis failed: {e}")
            return {"error": str(e), "provider": "google_cloud_tts"}

# Singleton instance
google_tts_service = GoogleTTSService()
```

**Step 2: Simple Audio Service Manager**

```python
# backend/app/services/audio/audio_service.py

from app.services.audio.google_tts_service import google_tts_service
from app.core.config import settings
from app.core.logging import logger
from typing import Dict
import hashlib
import os

class AudioService:
    """
    Simple audio service that generates and stores podcast audio.
    Phase 1: Use Google Cloud TTS only
    Phase 2: Add ElevenLabs for premium
    """
    
    def __init__(self):
        self.tts_service = google_tts_service
        self.audio_storage_path = settings.AUDIO_STORAGE_PATH or "/tmp/podcast_audio"
        os.makedirs(self.audio_storage_path, exist_ok=True)
        
    async def generate_podcast_audio(
        self,
        script_text: str,
        podcast_id: str,
        user_tier: str = "free"
    ) -> Dict:
        """
        Generate audio for podcast script.
        
        Args:
            script_text: Complete podcast script
            podcast_id: Unique podcast ID
            user_tier: "free" or "premium"
            
        Returns:
        {
            "audio_url": str,
            "audio_file_path": str,
            "duration_seconds": float,
            "file_size_mb": float,
            "synthesis_cost": float
        }
        """
        try:
            logger.info(f"Generating audio for podcast {podcast_id} ({len(script_text)} chars)")
            
            # Select voice based on user tier
            voice_name = self._select_voice(user_tier)
            
            # Synthesize speech
            synthesis_result = await self.tts_service.synthesize_speech(
                text=script_text,
                voice_name=voice_name,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            if synthesis_result.get("error"):
                return {"error": synthesis_result["error"]}
            
            # Save audio file
            audio_content = synthesis_result["audio_content"]
            file_path = self._save_audio_file(audio_content, podcast_id)
            
            # Calculate duration (estimate: 150 words/min, average 5 chars/word)
            word_count = len(script_text.split())
            duration_seconds = (word_count / 150) * 60
            
            # Calculate file size
            file_size_mb = len(audio_content) / (1024 * 1024)
            
            logger.info(
                f"Audio generated: {file_path}, {duration_seconds:.0f}s, {file_size_mb:.2f}MB"
            )
            
            return {
                "audio_url": f"/audio/{podcast_id}.mp3",  # Served by FastAPI static files
                "audio_file_path": file_path,
                "duration_seconds": duration_seconds,
                "file_size_mb": file_size_mb,
                "synthesis_cost": synthesis_result["estimated_cost"],
                "provider": synthesis_result["provider"],
                "voice_used": synthesis_result["voice_used"]
            }
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return {"error": str(e)}
    
    def _select_voice(self, user_tier: str) -> str:
        """
        Select voice based on user tier.
        
        Free: Standard voices
        Premium: Neural voices (better quality)
        """
        voice_options = {
            "free": "en-US-Standard-A",  # Standard quality, free tier
            "premium": "en-US-Neural2-A"  # Neural quality, still free tier
        }
        
        return voice_options.get(user_tier, voice_options["free"])
    
    def _save_audio_file(self, audio_content: bytes, podcast_id: str) -> str:
        """
        Save audio content to file.
        """
        file_name = f"{podcast_id}.mp3"
        file_path = os.path.join(self.audio_storage_path, file_name)
        
        with open(file_path, "wb") as f:
            f.write(audio_content)
        
        return file_path

# Singleton instance
audio_service = AudioService()
```

**Step 3: Integrate with Podcast Service**

```python
# backend/app/services/podcast_service.py
# UPDATE LINES 141-148

# BEFORE (commented out):
# Step 4: Generate audio (90%)
# log_step(4, "Preparing audio generation (skipped for now)", "RUNNING")
# TODO: Integrate audio generation service
# For now, we'll skip audio generation
# audio_url = await self._generate_audio(script.content)
# podcast.audio_url = audio_url

# AFTER (active):
# Step 4: Generate audio
log_step(4, "Generating audio", "RUNNING")

from app.services.audio.audio_service import audio_service

audio_result = await audio_service.generate_podcast_audio(
    script_text=script.content,
    podcast_id=str(podcast.id),
    user_tier=user.tier if user else "free"
)

if audio_result.get("error"):
    log_step(4, f"Audio generation failed: {audio_result['error']}", "WARNING")
    # Continue without audio for now
else:
    podcast.audio_url = audio_result["audio_url"]
    podcast.duration_seconds = audio_result["duration_seconds"]
    log_step(4, f"Audio generated: {audio_result['duration_seconds']:.0f}s", "COMPLETE")

db.commit()
```

**WINDSURF PROMPT 3A: Activate Audio Generation with Google Cloud TTS**

```
TASK: Activate audio generation using Google Cloud Text-to-Speech

CURRENT STATE:
- Audio code exists but is completely disabled (line 141-148 in podcast_service.py)
- 2,700 lines of TTS code ready but not active
- No audio files created for users

REQUIREMENTS:

1. SETUP GOOGLE CLOUD TTS:
   - Install: pip install google-cloud-texttospeech
   - Add to requirements.txt
   - Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   - Or use default credentials from Cloud Console

2. CREATE GOOGLE TTS SERVICE (backend/app/services/audio/google_tts_service.py):
   - Initialize TextToSpeechClient
   - Implement synthesize_speech() method:
     * Accept text, voice_name, speaking_rate, pitch
     * Use Neural2 voices for better quality (en-US-Neural2-A recommended)
     * Return audio content (bytes), format (mp3), synthesis time, character count, cost estimate
   - Run synthesis in executor (blocking call)
   - Log synthesis metrics

3. CREATE AUDIO SERVICE MANAGER (backend/app/services/audio/audio_service.py):
   - Wrap Google TTS service
   - Implement generate_podcast_audio():
     * Call TTS with script text
     * Save audio to file (create /tmp/podcast_audio directory)
     * Calculate duration estimate (word_count / 150 * 60 seconds)
     * Calculate file size
     * Return audio_url, file_path, duration, size, cost
   - Select voice based on user tier:
     * free: en-US-Standard-A (standard voice)
     * premium: en-US-Neural2-A (neural voice)

4. INTEGRATE WITH PODCAST SERVICE (backend/app/services/podcast_service.py):
   - Line 141-148: UNCOMMENT and REPLACE
   - Import audio_service
   - Call audio_service.generate_podcast_audio()
   - Handle errors gracefully (log warning, continue without audio)
   - Update podcast.audio_url and podcast.duration_seconds
   - Commit to database

5. CONFIGURE STATIC FILE SERVING (backend/app/main.py):
   - Mount /audio route to serve audio files
   ```python
   from fastapi.staticfiles import StaticFiles
   import os
   
   AUDIO_DIR = os.getenv("AUDIO_STORAGE_PATH", "/tmp/podcast_audio")
   os.makedirs(AUDIO_DIR, exist_ok=True)
   
   app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
   ```

GOOGLE CLOUD TTS CONFIGURATION:
Voices: en-US-Neural2-A, en-US-Neural2-C, en-US-Neural2-F (female/male options)
Audio format: MP3 (widely compatible)
Speaking rate: 1.0 (normal)
Pitch: 0.0 (normal)
Free tier: 4M standard chars/month, 1M neural chars/month

COST TRACKING:
- Standard voices: $0.000004 per character
- Neural voices: $0.000016 per character
- 10-minute podcast (~1500 words = 7500 chars) = $0.03-$0.12
- Free tier covers 100-250 podcasts/month

TESTING:
Test Case 1: Generate Audio
- Input: Complete script (1500 words)
- Expected: MP3 file created, duration ~10 minutes
- Validate: File exists, playable, correct duration

Test Case 2: Free vs Premium Voice
- Input: Same script, free user vs premium user
- Expected: Standard voice for free, Neural for premium
- Validate: Different voice quality

Test Case 3: Error Handling
- Input: Google API error (simulate)
- Expected: Log warning, continue without audio
- Validate: Podcast created, audio_url = None

ENVIRONMENT VARIABLES:
```
# .env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
AUDIO_STORAGE_PATH=/tmp/podcast_audio
```

Get Google Cloud credentials:
1. Go to Google Cloud Console
2. Create new project (if needed)
3. Enable Text-to-Speech API
4. Create service account
5. Download JSON key file
6. Set GOOGLE_APPLICATION_CREDENTIALS path

PERFORMANCE:
- TTS synthesis: 10-30 seconds for 10-minute podcast
- File save: <1 second
- Total audio generation: <35 seconds
- Does NOT block script generation (sequential is fine)

DELIVERABLES:
1. google_tts_service.py (complete implementation)
2. audio_service.py (complete implementation)
3. Updated podcast_service.py (uncomment and integrate)
4. Updated main.py (static file serving)
5. Requirements.txt with google-cloud-texttospeech
6. Documentation on Google Cloud setup
7. Tests for audio generation

SUCCESS CRITERIA:
- Audio generation active and functional
- MP3 files created and playable
- Duration estimates accurate (±10%)
- Cost tracking working
- Error handling graceful
- Performance <35 seconds for audio generation
- Free tier properly utilized
```

---

## 📋 IMPLEMENTATION SUMMARY

### **Phase 1: Information Collection Enhancement (Week 1)**
- **1A:** Multi-source API integration (Wikidata, GeoNames, aggregator)
- **1B:** Hierarchical location collection (multi-level context)
- **1C:** Question-based deep research (Perplexity integration)
- **1D:** Activate standout detection (integrate existing code)

### **Phase 2: Script Generation Enhancement (Week 2)**
- **2A:** Enhanced Perplexity prompts (CLEAR framework, eliminate template text)
- **2B:** Information weaving (optional, future enhancement)

### **Phase 3: Audio Synthesis Activation (Week 2)**
- **3A:** Activate Google Cloud TTS (uncomment, configure, test)
- **3B:** Add ElevenLabs premium option (future, optional)

### **Total Timeline: 2 Weeks**
- Week 1: Information collection (1A, 1B, 1C, 1D)
- Week 2: Script + Audio (2A, 3A)

### **Windsurf Prompts Provided:**
1. **Prompt 1A:** Multi-source API integration
2. **Prompt 1B:** Hierarchical location collection
3. **Prompt 1C:** Question-based deep research
4. **Prompt 1D:** Activate standout detection
5. **Prompt 2A:** Enhanced script generation prompts
6. **Prompt 3A:** Activate Google Cloud TTS

Each prompt is **complete, thorough, and architecture-integrated** with:
- Current state analysis
- Exact requirements
- Code examples
- Data structures
- Testing procedures
- Success criteria
- Integration points

---

## 🎯 SUCCESS METRICS

### **Information Collection**
- Sources active: 4+ (currently 2)
- Collection time: <8 seconds (multi-level)
- Hierarchy depth: 3-5 levels
- Question detection accuracy: >95%
- Standout detection: 80% Tier 1 accuracy

### **Script Generation**
- Template text: 0% occurrence (currently ~50%)
- Information density: >0.85 (fact-rich)
- Completion rate: 100% (intro + main + conclusion)
- User satisfaction: >8/10

### **Audio Generation**
- Audio created: 100% of podcasts (currently 0%)
- Quality (MOS): >4.0/5 (Google Neural voices)
- Generation time: <35 seconds
- Cost per podcast: <$0.15 (free tier)

### **Overall System**
- End-to-end time: <60 seconds (currently ~20s without audio)
- User satisfaction: >85%
- Production stability: 99% uptime
- Cost optimization: <$0.30 per podcast total

---

## 📚 ADDITIONAL RESEARCH REFERENCES

All enhancements are based on 2025 best practices from:
- OpenAI Deep Research documentation
- Perplexity Deep Research methodology
- Google Cloud TTS API specifications
- Academic papers on prompt engineering
- Production podcast generation systems
- Geolocation API best practices (IPGeolocation.io, GeoNames, Geoapify)
- TTS quality comparisons (ElevenLabs, Google, Azure, AWS)

**Complete, actionable plan ready for immediate Windsurf implementation.**