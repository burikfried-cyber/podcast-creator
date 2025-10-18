"""
GeoNames Service - Hierarchical location data (FREE with registration)
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class GeoNamesService:
    """GeoNames API integration for hierarchical location data"""
    
    def __init__(self):
        self.base_url = "http://api.geonames.org"
        self.username = getattr(settings, 'GEONAMES_USERNAME', 'demo')
        self.session = None
        self.cache_ttl = 900  # 15 minutes
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=8),
                headers={"User-Agent": "LocationPodcastGenerator/1.0"}
            )
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_location_content(self, location_name: str) -> Dict[str, Any]:
        """Main entry point: Get GeoNames content for a location"""
        try:
            logger.info("geonames_fetch_started", location=location_name)
            
            # Search for location
            search_results = await self.search_location(location_name)
            if not search_results:
                return self._get_fallback_content(location_name)
            
            # Get best match
            best_match = search_results[0]
            geoname_id = best_match.get("geonameId")
            
            # Get hierarchy and nearby places in parallel
            hierarchy_task = self.get_hierarchy(geoname_id)
            nearby_task = self.get_nearby_places(best_match.get("lat"), best_match.get("lng"))
            
            hierarchy, nearby = await asyncio.gather(hierarchy_task, nearby_task, return_exceptions=True)
            
            if isinstance(hierarchy, Exception):
                hierarchy = []
            if isinstance(nearby, Exception):
                nearby = []
            
            result = {
                "source": "geonames",
                "location_name": location_name,
                "geoname_id": geoname_id,
                "name": best_match.get("name"),
                "country": best_match.get("countryName"),
                "feature_code": best_match.get("fcode"),
                "feature_class": best_match.get("fcl"),
                "coordinates": {
                    "lat": best_match.get("lat"),
                    "lng": best_match.get("lng")
                },
                "population": best_match.get("population", 0),
                "hierarchy": self._build_hierarchy_structure(hierarchy),
                "nearby_places": nearby[:10],  # Limit to 10
                "confidence_score": self._calculate_confidence(best_match, hierarchy)
            }
            
            logger.info("geonames_fetch_completed", location=location_name, geoname_id=geoname_id)
            return result
            
        except Exception as e:
            logger.error("geonames_fetch_error", error=str(e), location=location_name)
            return self._get_fallback_content(location_name)
    
    async def search_location(self, location_name: str, max_results: int = 5) -> List[Dict]:
        """Search location by name"""
        try:
            session = await self._get_session()
            params = {
                "q": location_name,
                "maxRows": max_results,
                "username": self.username,
                "type": "json"
            }
            
            async with session.get(f"{self.base_url}/searchJSON", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("geonames", [])
                else:
                    logger.warning("geonames_search_failed", status=response.status)
        except Exception as e:
            logger.error("geonames_search_error", error=str(e))
        return []
    
    async def get_hierarchy(self, geoname_id: int) -> List[Dict]:
        """Get full hierarchy using hierarchyJSON endpoint"""
        try:
            session = await self._get_session()
            params = {
                "geonameId": geoname_id,
                "username": self.username
            }
            
            async with session.get(f"{self.base_url}/hierarchyJSON", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("geonames", [])
        except Exception as e:
            logger.error("geonames_hierarchy_error", error=str(e))
        return []
    
    async def get_nearby_places(self, lat: float, lng: float, radius: int = 5) -> List[Dict]:
        """Get nearby places within radius (km)"""
        try:
            session = await self._get_session()
            params = {
                "lat": lat,
                "lng": lng,
                "radius": radius,
                "maxRows": 10,
                "username": self.username
            }
            
            async with session.get(f"{self.base_url}/findNearbyJSON", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    geonames = data.get("geonames", [])
                    return [{
                        "name": g.get("name"),
                        "distance": g.get("distance"),
                        "feature_code": g.get("fcode"),
                        "population": g.get("population", 0)
                    } for g in geonames]
        except Exception as e:
            logger.error("geonames_nearby_error", error=str(e))
        return []
    
    def _build_hierarchy_structure(self, hierarchy: List[Dict]) -> Dict[str, Optional[str]]:
        """Build hierarchical location structure from GeoNames hierarchy"""
        structure = {
            "neighborhood": None,
            "district": None,
            "city": None,
            "region": None,
            "country": None
        }
        
        # Parse feature codes: PCLI=country, ADM1=region, ADM2=district, PPL=city
        for item in hierarchy:
            fcode = item.get("fcode", "")
            name = item.get("name")
            
            if fcode == "PCLI":
                structure["country"] = name
            elif fcode == "ADM1":
                structure["region"] = name
            elif fcode == "ADM2":
                structure["district"] = name
            elif fcode in ["PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"]:
                structure["city"] = name
            elif fcode in ["PPLX", "PPLQ"]:
                structure["neighborhood"] = name
        
        return structure
    
    def _calculate_confidence(self, location_data: Dict, hierarchy: List[Dict]) -> float:
        """Calculate confidence score"""
        score = 0.0
        if location_data.get("name"): score += 0.3
        if location_data.get("countryName"): score += 0.2
        if location_data.get("population", 0) > 0: score += 0.2
        if len(hierarchy) > 0: score += 0.3
        return round(score, 2)
    
    def _get_fallback_content(self, location_name: str) -> Dict:
        """Return fallback content when GeoNames fails"""
        return {
            "source": "geonames",
            "location_name": location_name,
            "geoname_id": None,
            "name": None,
            "country": None,
            "feature_code": None,
            "feature_class": None,
            "coordinates": {"lat": None, "lng": None},
            "population": 0,
            "hierarchy": {
                "neighborhood": None,
                "district": None,
                "city": None,
                "region": None,
                "country": None
            },
            "nearby_places": [],
            "confidence_score": 0.0,
            "error": "Location not found or API unavailable"
        }


# Singleton instance
geonames_service = GeoNamesService()
