"""
CrossRef API Client
130M+ metadata records for scholarly works
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class CrossRefAPIClient(BaseAPIClient):
    """CrossRef API for scholarly metadata"""
    
    def __init__(self, email: Optional[str] = None):
        config = APIConfig(
            name="CrossRef",
            base_url="https://api.crossref.org",
            tier=APITier.FREE,
            category=APICategory.ACADEMIC,
            rate_limit=50,  # 50 requests per second (polite pool with email)
            rate_period=1,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=3600,
            requires_auth=False,
            headers={"User-Agent": f"PodcastGenerator/1.0 (mailto:{email})"} if email else {}
        )
        super().__init__(config)
        self.email = email
    
    async def search(
        self,
        query: str,
        rows: int = 10,
        sort: str = "relevance",
        **kwargs
    ) -> APIResponse:
        """
        Search scholarly works
        
        Args:
            query: Search query
            rows: Number of results
            sort: Sort order (relevance, published, etc.)
            **kwargs: Additional filters
            
        Returns:
            APIResponse with works
        """
        params = {
            "query": query,
            "rows": rows,
            "sort": sort
        }
        params.update(kwargs)
        
        response = await self.get("/works", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_by_doi(self, doi: str) -> APIResponse:
        """
        Get work by DOI
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            APIResponse with work details
        """
        response = await self.get(f"/works/{doi}")
        if response.success:
            response.data = self.transform_work(response.data.get("message", {}))
        return response
    
    async def search_by_author(
        self,
        author: str,
        rows: int = 10
    ) -> APIResponse:
        """Search works by author name"""
        params = {
            "query.author": author,
            "rows": rows
        }
        
        response = await self.get("/works", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def search_by_title(
        self,
        title: str,
        rows: int = 10
    ) -> APIResponse:
        """Search works by title"""
        params = {
            "query.title": title,
            "rows": rows
        }
        
        response = await self.get("/works", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform CrossRef search response"""
        if not raw_data or "message" not in raw_data:
            return {"total_results": 0, "items": [], "source": "CrossRef"}
        
        message = raw_data["message"]
        items = []
        
        for work in message.get("items", []):
            items.append(self.transform_work(work))
        
        return {
            "total_results": message.get("total-results", len(items)),
            "items": items,
            "source": "CrossRef"
        }
    
    def transform_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """Transform individual work"""
        # Extract authors
        authors = []
        for author in work.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
        
        # Extract date
        date_parts = work.get("published-print", {}).get("date-parts", [[]])
        if not date_parts[0]:
            date_parts = work.get("published-online", {}).get("date-parts", [[]])
        
        year = date_parts[0][0] if date_parts and date_parts[0] else None
        
        # Extract title
        titles = work.get("title", [])
        title = titles[0] if titles else None
        
        # Extract abstract
        abstract = work.get("abstract")
        
        return {
            "id": work.get("DOI"),
            "title": title,
            "description": abstract,
            "authors": authors,
            "date": str(year) if year else None,
            "type": work.get("type"),
            "publisher": work.get("publisher"),
            "journal": work.get("container-title", [None])[0],
            "volume": work.get("volume"),
            "issue": work.get("issue"),
            "page": work.get("page"),
            "url": work.get("URL"),
            "doi": work.get("DOI"),
            "citations": work.get("is-referenced-by-count", 0),
            "source": "CrossRef"
        }
