"""
Wikidata Service - Structured entity data from Wikidata (100% FREE)
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class WikidataService:
    """Wikidata API integration for structured entity data"""
    
    def __init__(self):
        self.base_url = "https://www.wikidata.org/w/api.php"
        self.session = None
        self.cache_ttl = 3600  # 1 hour
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": "LocationPodcastGenerator/1.0"}
            )
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_location_content(self, location_name: str) -> Dict[str, Any]:
        """Main entry point: Get Wikidata content for a location"""
        try:
            logger.info("wikidata_fetch_started", location=location_name)
            
            entity_id = await self.search_entity(location_name)
            if not entity_id:
                return self._get_fallback_content(location_name)
            
            entity_data = await self.get_entity_data(entity_id)
            if not entity_data:
                return self._get_fallback_content(location_name)
            
            confidence = self._calculate_confidence(entity_data)
            
            result = {
                "source": "wikidata",
                "location_name": location_name,
                "entity_id": entity_id,
                "label": entity_data.get("label"),
                "description": entity_data.get("description"),
                "facts": entity_data.get("facts", []),
                "wikipedia_link": entity_data.get("wikipedia_link"),
                "confidence_score": confidence,
                "facts_count": len(entity_data.get("facts", []))
            }
            
            logger.info("wikidata_fetch_completed", location=location_name, facts_count=result["facts_count"])
            return result
            
        except Exception as e:
            logger.error("wikidata_fetch_error", error=str(e), location=location_name)
            return self._get_fallback_content(location_name)
    
    async def search_entity(self, location_name: str) -> Optional[str]:
        """Search for Wikidata entity ID by location name"""
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
                        return data["search"][0]["id"]
        except Exception as e:
            logger.error("wikidata_search_error", error=str(e))
        return None
    
    async def get_entity_data(self, entity_id: str) -> Dict:
        """Retrieve entity data including claims and properties"""
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
                    if "entities" in data and entity_id in data["entities"]:
                        entity = data["entities"][entity_id]
                        return {
                            "entity_id": entity_id,
                            "label": entity.get("labels", {}).get("en", {}).get("value"),
                            "description": entity.get("descriptions", {}).get("en", {}).get("value"),
                            "facts": self._extract_facts(entity.get("claims", {})),
                            "wikipedia_link": self._get_wikipedia_link(entity.get("sitelinks", {}))
                        }
        except Exception as e:
            logger.error("wikidata_entity_error", error=str(e))
        return {}
    
    def _extract_facts(self, claims: Dict) -> List[Dict]:
        """Extract 10+ key properties for locations"""
        properties = {
            "P17": "country", "P131": "located_in", "P1082": "population",
            "P571": "inception", "P625": "coordinates", "P706": "terrain_feature",
            "P2044": "elevation", "P421": "timezone", "P1566": "geonames_id",
            "P281": "postal_code", "P36": "capital", "P37": "official_language",
            "P38": "currency", "P41": "flag", "P94": "coat_of_arms"
        }
        
        facts = []
        for prop_id, prop_name in properties.items():
            if prop_id in claims and claims[prop_id]:
                value = self._extract_value(claims[prop_id][0])
                if value:
                    facts.append({"property": prop_name, "value": value, "property_id": prop_id})
        return facts
    
    def _extract_value(self, claim: Dict) -> Any:
        """Extract value from Wikidata claim"""
        try:
            datavalue = claim.get("mainsnak", {}).get("datavalue", {})
            value = datavalue.get("value")
            if isinstance(value, dict):
                if "latitude" in value and "longitude" in value:
                    return {"lat": value["latitude"], "lon": value["longitude"]}
                elif "id" in value:
                    return value["id"]
                elif "time" in value:
                    return value["time"]
            return str(value) if value else None
        except:
            return None
    
    def _get_wikipedia_link(self, sitelinks: Dict) -> Optional[str]:
        """Extract English Wikipedia link"""
        enwiki = sitelinks.get("enwiki", {})
        if enwiki and "title" in enwiki:
            title = enwiki["title"].replace(" ", "_")
            return f"https://en.wikipedia.org/wiki/{title}"
        return None
    
    def _calculate_confidence(self, entity_data: Dict) -> float:
        """Calculate confidence score based on data completeness"""
        score = 0.0
        if entity_data.get("label"): score += 0.2
        if entity_data.get("description"): score += 0.2
        if entity_data.get("wikipedia_link"): score += 0.2
        facts_count = len(entity_data.get("facts", []))
        score += min(0.4, facts_count * 0.04)  # Up to 0.4 for 10+ facts
        return round(score, 2)
    
    def _get_fallback_content(self, location_name: str) -> Dict:
        """Return fallback content when Wikidata fails"""
        return {
            "source": "wikidata",
            "location_name": location_name,
            "entity_id": None,
            "label": None,
            "description": None,
            "facts": [],
            "wikipedia_link": None,
            "confidence_score": 0.0,
            "facts_count": 0,
            "error": "Entity not found or API unavailable"
        }


# Singleton instance
wikidata_service = WikidataService()
