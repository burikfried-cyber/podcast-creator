"""
GeoNames API Client
11M+ geographic names and features
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class GeoNamesAPIClient(BaseAPIClient):
    """GeoNames API for geographic information"""
    
    def __init__(self, username: str):
        config = APIConfig(
            name="GeoNames",
            base_url="http://api.geonames.org",
            tier=APITier.FREE,
            category=APICategory.GEOGRAPHIC,
            rate_limit=2000,  # 2000 credits per hour (free tier)
            rate_period=3600,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=3600,
            requires_auth=True,
            auth_type="api_key"
        )
        super().__init__(config, username)
        self.username = username
    
    async def search(
        self,
        query: str,
        max_rows: int = 10,
        feature_class: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        Search geographic names
        
        Args:
            query: Search query
            max_rows: Maximum results
            feature_class: Filter by feature class (A=country, P=city, etc.)
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with geographic names
        """
        params = {
            "q": query,
            "maxRows": max_rows,
            "username": self.username,
            "type": "json"
        }
        
        if feature_class:
            params["featureClass"] = feature_class
        
        params.update(kwargs)
        
        response = await self.get("/searchJSON", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_nearby_places(
        self,
        lat: float,
        lng: float,
        radius: int = 10,
        max_rows: int = 10
    ) -> APIResponse:
        """
        Find nearby places
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in km
            max_rows: Maximum results
            
        Returns:
            APIResponse with nearby places
        """
        params = {
            "lat": lat,
            "lng": lng,
            "radius": radius,
            "maxRows": max_rows,
            "username": self.username,
            "type": "json"
        }
        
        response = await self.get("/findNearbyJSON", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_wikipedia_articles(
        self,
        lat: float,
        lng: float,
        radius: int = 10,
        max_rows: int = 10
    ) -> APIResponse:
        """
        Find Wikipedia articles near location
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in km
            max_rows: Maximum results
            
        Returns:
            APIResponse with Wikipedia articles
        """
        params = {
            "lat": lat,
            "lng": lng,
            "radius": radius,
            "maxRows": max_rows,
            "username": self.username,
            "type": "json"
        }
        
        response = await self.get("/findNearbyWikipediaJSON", params=params)
        if response.success:
            response.data = self.transform_wikipedia_response(response.data)
        return response
    
    async def get_country_info(self, country_code: Optional[str] = None) -> APIResponse:
        """Get country information"""
        params = {
            "username": self.username,
            "type": "json"
        }
        
        if country_code:
            params["country"] = country_code
        
        response = await self.get("/countryInfoJSON", params=params)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GeoNames search response"""
        if not raw_data or "geonames" not in raw_data:
            return {"total_results": 0, "items": [], "source": "GeoNames"}
        
        items = []
        for place in raw_data.get("geonames", []):
            items.append({
                "id": place.get("geonameId"),
                "title": place.get("name"),
                "description": place.get("toponymName"),
                "latitude": float(place.get("lat", 0)),
                "longitude": float(place.get("lng", 0)),
                "country": place.get("countryName"),
                "country_code": place.get("countryCode"),
                "admin_name": place.get("adminName1"),
                "feature_class": place.get("fclass"),
                "feature_code": place.get("fcode"),
                "population": place.get("population"),
                "elevation": place.get("elevation"),
                "timezone": place.get("timezone"),
                "source": "GeoNames"
            })
        
        return {
            "total_results": raw_data.get("totalResultsCount", len(items)),
            "items": items,
            "source": "GeoNames"
        }
    
    def transform_wikipedia_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Wikipedia articles response"""
        if not raw_data or "geonames" not in raw_data:
            return {"total_results": 0, "items": [], "source": "GeoNames"}
        
        items = []
        for article in raw_data.get("geonames", []):
            items.append({
                "id": article.get("geonameId"),
                "title": article.get("title"),
                "description": article.get("summary"),
                "latitude": float(article.get("lat", 0)),
                "longitude": float(article.get("lng", 0)),
                "url": article.get("wikipediaUrl"),
                "thumbnail": article.get("thumbnailImg"),
                "language": article.get("lang"),
                "distance": article.get("distance"),
                "source": "GeoNames"
            })
        
        return {
            "total_results": len(items),
            "items": items,
            "source": "GeoNames"
        }
