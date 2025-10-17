"""
DigitalNZ API Client
Access to 30M+ New Zealand cultural items
"""
from typing import Dict, Any, Optional, List
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class DigitalNZAPIClient(BaseAPIClient):
    """DigitalNZ API Client for New Zealand cultural heritage"""
    
    def __init__(self, api_key: str):
        config = APIConfig(
            name="DigitalNZ",
            base_url="https://api.digitalnz.org",
            tier=APITier.FREE,
            category=APICategory.CULTURAL,
            rate_limit=10000,
            rate_period=86400,
            cost_per_request=0.0,
            requires_auth=True,
            auth_type="api_key"
        )
        super().__init__(config, api_key)
    
    async def search(self, query: str, per_page: int = 20, page: int = 1, **kwargs) -> APIResponse:
        params = {
            "text": query,
            "per_page": min(per_page, 100),
            "page": page,
            "api_key": self.api_key
        }
        params.update(kwargs)
        
        response = await self.get("/v3/records.json", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not raw_data or "search" not in raw_data:
            return {"total_results": 0, "items": [], "source": "DigitalNZ"}
        
        search = raw_data["search"]
        items = []
        
        for result in search.get("results", []):
            items.append({
                "id": result.get("id"),
                "title": result.get("title"),
                "description": result.get("description"),
                "creator": result.get("creator"),
                "date": result.get("date"),
                "category": result.get("category"),
                "content_partner": result.get("content_partner"),
                "thumbnail": result.get("thumbnail_url"),
                "url": result.get("landing_url"),
                "source": "DigitalNZ"
            })
        
        return {
            "total_results": search.get("result_count", 0),
            "items": items,
            "source": "DigitalNZ"
        }
