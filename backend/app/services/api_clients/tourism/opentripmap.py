"""
OpenTripMap API Client
Access to 1M+ global POIs and attractions
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class OpenTripMapAPIClient(BaseAPIClient):
    """OpenTripMap API for tourist attractions and POIs"""
    
    def __init__(self, api_key: str):
        config = APIConfig(
            name="OpenTripMap",
            base_url="https://api.opentripmap.com/0.1/en",
            tier=APITier.FREE,
            category=APICategory.TOURISM,
            rate_limit=1000,
            rate_period=86400,
            cost_per_request=0.0,
            requires_auth=True,
            auth_type="api_key"
        )
        super().__init__(config, api_key)
    
    async def search(self, query: str, lat: float, lon: float, radius: int = 5000, **kwargs) -> APIResponse:
        """Search POIs by name near location"""
        params = {
            "name": query,
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "apikey": self.api_key
        }
        params.update(kwargs)
        
        response = await self.get("/places/autosuggest", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_places_by_bbox(
        self,
        lon_min: float,
        lat_min: float,
        lon_max: float,
        lat_max: float,
        kinds: Optional[str] = None,
        limit: int = 10
    ) -> APIResponse:
        """Get places within bounding box"""
        params = {
            "lon_min": lon_min,
            "lat_min": lat_min,
            "lon_max": lon_max,
            "lat_max": lat_max,
            "limit": limit,
            "apikey": self.api_key
        }
        
        if kinds:
            params["kinds"] = kinds
        
        response = await self.get("/places/bbox", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_place_details(self, xid: str) -> APIResponse:
        """Get detailed information about a place"""
        params = {"apikey": self.api_key}
        response = await self.get(f"/places/xid/{xid}", params=params)
        return response
    
    def transform_response(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, list):
            items = []
            for item in raw_data:
                items.append({
                    "id": item.get("xid"),
                    "title": item.get("name"),
                    "description": item.get("info"),
                    "kinds": item.get("kinds", "").split(","),
                    "latitude": item.get("point", {}).get("lat"),
                    "longitude": item.get("point", {}).get("lon"),
                    "source": "OpenTripMap"
                })
            return {"total_results": len(items), "items": items, "source": "OpenTripMap"}
        
        return {"total_results": 0, "items": [], "source": "OpenTripMap"}
