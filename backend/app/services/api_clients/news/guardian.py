"""
The Guardian API Client
Content from 1999 onwards
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class GuardianAPIClient(BaseAPIClient):
    """The Guardian Open Platform API"""
    
    def __init__(self, api_key: str):
        config = APIConfig(
            name="Guardian",
            base_url="https://content.guardianapis.com",
            tier=APITier.FREE,
            category=APICategory.NEWS,
            rate_limit=5000,  # 5000 calls per day
            rate_period=86400,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=1800,
            requires_auth=True,
            auth_type="api_key"
        )
        super().__init__(config, api_key)
    
    async def search(
        self,
        query: str,
        page_size: int = 10,
        order_by: str = "relevance",
        section: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        Search Guardian content
        
        Args:
            query: Search query
            page_size: Results per page (max 50)
            order_by: Sort order (newest, oldest, relevance)
            section: Filter by section
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with articles
        """
        params = {
            "q": query,
            "page-size": min(page_size, 50),
            "order-by": order_by,
            "show-fields": "headline,trailText,thumbnail,bodyText",
            "show-tags": "keyword",
            "api-key": self.api_key
        }
        
        if section:
            params["section"] = section
        
        if from_date:
            params["from-date"] = from_date
        
        if to_date:
            params["to-date"] = to_date
        
        params.update(kwargs)
        
        response = await self.get("/search", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_article(self, article_id: str) -> APIResponse:
        """
        Get article by ID
        
        Args:
            article_id: Guardian article ID
            
        Returns:
            APIResponse with article details
        """
        params = {
            "show-fields": "all",
            "show-tags": "all",
            "api-key": self.api_key
        }
        
        response = await self.get(f"/{article_id}", params=params)
        if response.success:
            response.data = self.transform_article(response.data)
        return response
    
    async def get_sections(self) -> APIResponse:
        """Get all available sections"""
        params = {"api-key": self.api_key}
        response = await self.get("/sections", params=params)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Guardian search response"""
        if not raw_data or "response" not in raw_data:
            return {"total_results": 0, "items": [], "source": "Guardian"}
        
        response = raw_data["response"]
        items = []
        
        for result in response.get("results", []):
            fields = result.get("fields", {})
            tags = result.get("tags", [])
            
            items.append({
                "id": result.get("id"),
                "title": fields.get("headline", result.get("webTitle")),
                "description": fields.get("trailText"),
                "body": fields.get("bodyText"),
                "date": result.get("webPublicationDate"),
                "section": result.get("sectionName"),
                "type": result.get("type"),
                "url": result.get("webUrl"),
                "thumbnail": fields.get("thumbnail"),
                "tags": [tag.get("webTitle") for tag in tags],
                "source": "Guardian"
            })
        
        return {
            "total_results": response.get("total", len(items)),
            "items": items,
            "source": "Guardian"
        }
    
    def transform_article(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform detailed article response"""
        if not raw_data or "response" not in raw_data:
            return {}
        
        content = raw_data["response"].get("content", {})
        fields = content.get("fields", {})
        
        return {
            "id": content.get("id"),
            "title": fields.get("headline"),
            "description": fields.get("standfirst"),
            "body": fields.get("body"),
            "date": content.get("webPublicationDate"),
            "section": content.get("sectionName"),
            "url": content.get("webUrl"),
            "thumbnail": fields.get("thumbnail"),
            "byline": fields.get("byline"),
            "source": "Guardian"
        }
