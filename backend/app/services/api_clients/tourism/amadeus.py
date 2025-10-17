"""
Amadeus API Client
POI, Location Scoring, Tours & Activities
"""
from typing import Dict, Any, Optional, List
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class AmadeusAPIClient(BaseAPIClient):
    """Amadeus API for travel and tourism data"""
    
    def __init__(self, api_key: str, api_secret: str):
        config = APIConfig(
            name="Amadeus",
            base_url="https://api.amadeus.com/v1",
            tier=APITier.FREEMIUM,
            category=APICategory.TOURISM,
            rate_limit=1000,  # 1000 requests per month (free tier)
            rate_period=2592000,  # 30 days
            cost_per_request=0.01,  # Varies by endpoint
            timeout=30,
            cache_ttl=3600,  # 1 hour
            requires_auth=True,
            auth_type="bearer"
        )
        super().__init__(config, api_key)
        self.api_secret = api_secret
        self._access_token = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token"""
        if self._access_token:
            return self._access_token
        
        # In production, implement OAuth flow
        # For now, assume api_key is the access token
        self._access_token = self.api_key
        return self._access_token
    
    async def search(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: int = 5,
        **kwargs
    ) -> APIResponse:
        """
        Search points of interest
        
        Args:
            query: Search query (categories: SIGHTS, BEACH_PARK, etc.)
            latitude: Latitude
            longitude: Longitude
            radius: Search radius in km
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with POIs
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "categories": query
        }
        params.update(kwargs)
        
        response = await self.get("/reference-data/locations/pois", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_location_score(
        self,
        latitude: float,
        longitude: float
    ) -> APIResponse:
        """
        Get location score (safety, tourism, etc.)
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            APIResponse with location scores
        """
        params = {
            "latitude": latitude,
            "longitude": longitude
        }
        
        response = await self.get("/location/analytics/category-rated-areas", params=params)
        return response
    
    async def search_activities(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1,
        **kwargs
    ) -> APIResponse:
        """
        Search tours and activities
        
        Args:
            latitude: Latitude
            longitude: Longitude
            radius: Search radius in km
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with activities
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius
        }
        params.update(kwargs)
        
        response = await self.get("/shopping/activities", params=params)
        if response.success:
            response.data = self.transform_activities(response.data)
        return response
    
    async def get_activity_details(self, activity_id: str) -> APIResponse:
        """Get detailed activity information"""
        response = await self.get(f"/shopping/activities/{activity_id}")
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform POI search response"""
        if not raw_data or "data" not in raw_data:
            return {"total_results": 0, "items": [], "source": "Amadeus"}
        
        items = []
        for poi in raw_data.get("data", []):
            geo_code = poi.get("geoCode", {})
            
            items.append({
                "id": poi.get("id"),
                "title": poi.get("name"),
                "description": poi.get("shortDescription"),
                "category": poi.get("category"),
                "tags": poi.get("tags", []),
                "latitude": geo_code.get("latitude"),
                "longitude": geo_code.get("longitude"),
                "rank": poi.get("rank"),
                "source": "Amadeus"
            })
        
        return {
            "total_results": len(items),
            "items": items,
            "source": "Amadeus"
        }
    
    def transform_activities(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform activities response"""
        if not raw_data or "data" not in raw_data:
            return {"total_results": 0, "items": [], "source": "Amadeus"}
        
        items = []
        for activity in raw_data.get("data", []):
            geo_code = activity.get("geoCode", {})
            price = activity.get("price", {})
            
            items.append({
                "id": activity.get("id"),
                "title": activity.get("name"),
                "description": activity.get("shortDescription"),
                "latitude": geo_code.get("latitude"),
                "longitude": geo_code.get("longitude"),
                "rating": activity.get("rating"),
                "price": price.get("amount"),
                "currency": price.get("currencyCode"),
                "duration": activity.get("minimumDuration"),
                "pictures": activity.get("pictures", []),
                "source": "Amadeus"
            })
        
        return {
            "total_results": len(items),
            "items": items,
            "source": "Amadeus"
        }
