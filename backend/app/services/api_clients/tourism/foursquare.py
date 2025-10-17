"""
Foursquare Places API Client
105M+ venues worldwide with rich POI data
"""
from typing import Dict, Any, Optional, List
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class FoursquareAPIClient(BaseAPIClient):
    """Foursquare Places API for venue discovery"""
    
    def __init__(self, api_key: str):
        config = APIConfig(
            name="Foursquare",
            base_url="https://api.foursquare.com/v3",
            tier=APITier.FREEMIUM,
            category=APICategory.TOURISM,
            rate_limit=950,  # 950 calls per day (free tier)
            rate_period=86400,
            cost_per_request=0.005,  # ~$5 per 1000 requests
            timeout=30,
            cache_ttl=1800,
            requires_auth=True,
            auth_type="bearer"
        )
        super().__init__(config, api_key)
    
    async def search(
        self,
        query: str,
        ll: Optional[str] = None,
        near: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> APIResponse:
        """
        Search for places
        
        Args:
            query: Search query
            ll: Latitude,longitude (e.g., "40.7,-74.0")
            near: Location name (e.g., "New York, NY")
            limit: Number of results (max 50)
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with venues
        """
        params = {
            "query": query,
            "limit": min(limit, 50)
        }
        
        if ll:
            params["ll"] = ll
        elif near:
            params["near"] = near
        
        params.update(kwargs)
        
        response = await self.get("/places/search", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def search_nearby(
        self,
        lat: float,
        lon: float,
        categories: Optional[List[str]] = None,
        radius: int = 1000,
        limit: int = 20
    ) -> APIResponse:
        """
        Search nearby places
        
        Args:
            lat: Latitude
            lon: Longitude
            categories: Category IDs to filter
            radius: Search radius in meters (max 100000)
            limit: Number of results
            
        Returns:
            APIResponse with nearby venues
        """
        params = {
            "ll": f"{lat},{lon}",
            "radius": min(radius, 100000),
            "limit": min(limit, 50)
        }
        
        if categories:
            params["categories"] = ",".join(categories)
        
        response = await self.get("/places/nearby", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_place_details(self, fsq_id: str) -> APIResponse:
        """
        Get detailed place information
        
        Args:
            fsq_id: Foursquare place ID
            
        Returns:
            APIResponse with place details
        """
        response = await self.get(f"/places/{fsq_id}")
        if response.success:
            response.data = self.transform_place_details(response.data)
        return response
    
    async def get_place_photos(self, fsq_id: str, limit: int = 10) -> APIResponse:
        """Get photos for a place"""
        params = {"limit": limit}
        response = await self.get(f"/places/{fsq_id}/photos", params=params)
        return response
    
    async def get_place_tips(self, fsq_id: str, limit: int = 10) -> APIResponse:
        """Get user tips/reviews for a place"""
        params = {"limit": limit}
        response = await self.get(f"/places/{fsq_id}/tips", params=params)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Foursquare search response"""
        if not raw_data or "results" not in raw_data:
            return {"total_results": 0, "items": [], "source": "Foursquare"}
        
        items = []
        for result in raw_data.get("results", []):
            geocodes = result.get("geocodes", {}).get("main", {})
            location = result.get("location", {})
            categories = result.get("categories", [])
            
            items.append({
                "id": result.get("fsq_id"),
                "title": result.get("name"),
                "description": result.get("description"),
                "category": [cat.get("name") for cat in categories],
                "latitude": geocodes.get("latitude"),
                "longitude": geocodes.get("longitude"),
                "address": location.get("formatted_address"),
                "locality": location.get("locality"),
                "region": location.get("region"),
                "country": location.get("country"),
                "postcode": location.get("postcode"),
                "distance": result.get("distance"),
                "popularity": result.get("popularity"),
                "rating": result.get("rating"),
                "price": result.get("price"),
                "website": result.get("website"),
                "tel": result.get("tel"),
                "verified": result.get("verified", False),
                "source": "Foursquare"
            })
        
        return {
            "total_results": len(items),
            "items": items,
            "source": "Foursquare"
        }
    
    def transform_place_details(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform detailed place response"""
        if not raw_data:
            return {}
        
        geocodes = raw_data.get("geocodes", {}).get("main", {})
        location = raw_data.get("location", {})
        
        return {
            "id": raw_data.get("fsq_id"),
            "title": raw_data.get("name"),
            "description": raw_data.get("description"),
            "categories": [cat.get("name") for cat in raw_data.get("categories", [])],
            "latitude": geocodes.get("latitude"),
            "longitude": geocodes.get("longitude"),
            "address": location.get("formatted_address"),
            "hours": raw_data.get("hours"),
            "rating": raw_data.get("rating"),
            "popularity": raw_data.get("popularity"),
            "price": raw_data.get("price"),
            "stats": raw_data.get("stats"),
            "website": raw_data.get("website"),
            "social_media": raw_data.get("social_media"),
            "verified": raw_data.get("verified"),
            "source": "Foursquare"
        }
