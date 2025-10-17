"""
BBC News API Client
Note: BBC News API is limited to non-commercial use
This is a simplified client for educational purposes
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class BBCNewsAPIClient(BaseAPIClient):
    """
    BBC News API Client
    Note: Limited availability, primarily for educational/research use
    """
    
    def __init__(self, api_key: Optional[str] = None):
        config = APIConfig(
            name="BBC",
            base_url="https://newsapi.org/v2",  # Using NewsAPI as proxy
            tier=APITier.FREEMIUM,
            category=APICategory.NEWS,
            rate_limit=100,  # 100 requests per day (free tier)
            rate_period=86400,
            cost_per_request=0.002,
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
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        Search BBC news articles via NewsAPI
        
        Args:
            query: Search query
            page_size: Results per page
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with articles
        """
        params = {
            "q": query,
            "sources": "bbc-news",
            "pageSize": min(page_size, 100),
            "apiKey": self.api_key
        }
        
        if from_date:
            params["from"] = from_date
        
        if to_date:
            params["to"] = to_date
        
        params.update(kwargs)
        
        response = await self.get("/everything", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_top_headlines(
        self,
        category: Optional[str] = None,
        page_size: int = 10
    ) -> APIResponse:
        """
        Get BBC top headlines
        
        Args:
            category: News category (business, entertainment, etc.)
            page_size: Results per page
            
        Returns:
            APIResponse with headlines
        """
        params = {
            "sources": "bbc-news",
            "pageSize": min(page_size, 100),
            "apiKey": self.api_key
        }
        
        if category:
            params["category"] = category
        
        response = await self.get("/top-headlines", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform NewsAPI response"""
        if not raw_data or "articles" not in raw_data:
            return {"total_results": 0, "items": [], "source": "BBC"}
        
        items = []
        for article in raw_data.get("articles", []):
            items.append({
                "id": article.get("url"),
                "title": article.get("title"),
                "description": article.get("description"),
                "body": article.get("content"),
                "date": article.get("publishedAt"),
                "author": article.get("author"),
                "url": article.get("url"),
                "thumbnail": article.get("urlToImage"),
                "source": "BBC"
            })
        
        return {
            "total_results": raw_data.get("totalResults", len(items)),
            "items": items,
            "source": "BBC"
        }
