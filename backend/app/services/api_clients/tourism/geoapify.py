"""
Geoapify Places API Client
500+ categories, OSM-based location data
"""
from typing import Dict, Any, Optional, List
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class GeoapifyPlacesAPIClient(BaseAPIClient):
    """Geoapify Places API for location search and geocoding"""
    
    def __init__(self, api_key: str):
        config = APIConfig(
            name="Geoapify",
            base_url="https://api.geoapify.com/v2",
            tier=APITier.FREEMIUM,
            category=APICategory.TOURISM,
            rate_limit=3000,  # 3000 requests per day (free tier)
            rate_period=86400,
            cost_per_request=0.001,  # $1 per 1000 requests
            timeout=30,
            cache_ttl=1800,
            requires_auth=True,
            auth_type="api_key"
        )
        super().__init__(config, api_key)
    
    async def search(
        self,
        query: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        limit: int = 10,
        **kwargs
    ) -> APIResponse:
        """
        Search for places
        
        Args:
            query: Search text
            lat: Latitude for bias
            lon: Longitude for bias
            limit: Number of results
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with places
        """
        params = {
            "text": query,
            "limit": limit,
            "apiKey": self.api_key
        }
        
        if lat and lon:
            params["bias"] = f"proximity:{lon},{lat}"
        
        params.update(kwargs)
        
        response = await self.get("/places", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def search_by_category(
        self,
        categories: List[str],
        lat: float,
        lon: float,
        radius: int = 5000,
        limit: int = 20
    ) -> APIResponse:
        """
        Search places by category near location
        
        Args:
            categories: List of categories (e.g., ["tourism.attraction", "catering.restaurant"])
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters
            limit: Number of results
            
        Returns:
            APIResponse with places
        """
        params = {
            "categories": ",".join(categories),
            "filter": f"circle:{lon},{lat},{radius}",
            "limit": limit,
            "apiKey": self.api_key
        }
        
        response = await self.get("/places", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_place_details(self, place_id: str) -> APIResponse:
        """Get detailed information about a place"""
        params = {"apiKey": self.api_key}
        response = await self.get(f"/place-details", params={**params, "id": place_id})
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Geoapify response to standardized format"""
        if not raw_data or "features" not in raw_data:
            return {"total_results": 0, "items": [], "source": "Geoapify"}
        
        items = []
        for feature in raw_data.get("features", []):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])
            
            items.append({
                "id": props.get("place_id"),
                "title": props.get("name", props.get("formatted")),
                "description": props.get("address_line2"),
                "category": props.get("categories", []),
                "latitude": coords[1] if len(coords) > 1 else None,
                "longitude": coords[0] if len(coords) > 0 else None,
                "address": props.get("formatted"),
                "city": props.get("city"),
                "country": props.get("country"),
                "postcode": props.get("postcode"),
                "website": props.get("website"),
                "phone": props.get("phone"),
                "opening_hours": props.get("opening_hours"),
                "source": "Geoapify"
            })
        
        return {
            "total_results": len(items),
            "items": items,
            "source": "Geoapify"
        }
