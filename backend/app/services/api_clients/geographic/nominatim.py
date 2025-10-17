"""
Nominatim API Client
OpenStreetMap geocoding service
"""
from typing import Dict, Any
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class NominatimAPIClient(BaseAPIClient):
    """Nominatim API for geocoding and reverse geocoding"""
    
    def __init__(self):
        config = APIConfig(
            name="Nominatim",
            base_url="https://nominatim.openstreetmap.org",
            tier=APITier.FREE,
            category=APICategory.GEOGRAPHIC,
            rate_limit=1,  # 1 request per second
            rate_period=1,
            cost_per_request=0.0,
            requires_auth=False
        )
        super().__init__(config)
    
    async def search(self, query: str, limit: int = 10, **kwargs) -> APIResponse:
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1
        }
        params.update(kwargs)
        
        response = await self.get("/search", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def reverse_geocode(self, lat: float, lon: float) -> APIResponse:
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }
        
        response = await self.get("/reverse", params=params)
        return response
    
    def transform_response(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, list):
            items = []
            for item in raw_data:
                items.append({
                    "id": item.get("place_id"),
                    "title": item.get("display_name"),
                    "type": item.get("type"),
                    "latitude": float(item.get("lat", 0)),
                    "longitude": float(item.get("lon", 0)),
                    "address": item.get("address", {}),
                    "source": "Nominatim"
                })
            return {"total_results": len(items), "items": items, "source": "Nominatim"}
        
        return {"total_results": 0, "items": [], "source": "Nominatim"}
