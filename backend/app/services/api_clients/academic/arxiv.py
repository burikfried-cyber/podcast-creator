"""
arXiv API Client
2.2M+ scientific preprints
"""
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class ArXivAPIClient(BaseAPIClient):
    """arXiv API for scientific papers"""
    
    def __init__(self):
        config = APIConfig(
            name="arXiv",
            base_url="http://export.arxiv.org",
            tier=APITier.FREE,
            category=APICategory.ACADEMIC,
            rate_limit=1,  # 1 request per 3 seconds
            rate_period=3,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=3600,
            requires_auth=False
        )
        super().__init__(config)
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        **kwargs
    ) -> APIResponse:
        """
        Search arXiv papers
        
        Args:
            query: Search query (supports field prefixes: ti:, au:, abs:, etc.)
            max_results: Maximum results
            sort_by: Sort order (relevance, lastUpdatedDate, submittedDate)
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with papers
        """
        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": sort_by
        }
        params.update(kwargs)
        
        response = await self.get("/api/query", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_by_id(self, arxiv_id: str) -> APIResponse:
        """Get paper by arXiv ID"""
        params = {"id_list": arxiv_id}
        response = await self.get("/api/query", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    def transform_response(self, raw_data: str) -> Dict[str, Any]:
        """Transform arXiv XML response"""
        try:
            # Parse Atom XML
            root = ET.fromstring(raw_data)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
            
            items = []
            for entry in root.findall("atom:entry", ns):
                # Extract authors
                authors = [
                    author.find("atom:name", ns).text
                    for author in entry.findall("atom:author", ns)
                    if author.find("atom:name", ns) is not None
                ]
                
                # Extract categories
                categories = [
                    cat.get("term")
                    for cat in entry.findall("atom:category", ns)
                ]
                
                items.append({
                    "id": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else None,
                    "title": entry.find("atom:title", ns).text if entry.find("atom:title", ns) is not None else None,
                    "description": entry.find("atom:summary", ns).text if entry.find("atom:summary", ns) is not None else None,
                    "authors": authors,
                    "date": entry.find("atom:published", ns).text if entry.find("atom:published", ns) is not None else None,
                    "updated": entry.find("atom:updated", ns).text if entry.find("atom:updated", ns) is not None else None,
                    "categories": categories,
                    "url": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else None,
                    "pdf_url": next(
                        (link.get("href") for link in entry.findall("atom:link", ns) if link.get("title") == "pdf"),
                        None
                    ),
                    "source": "arXiv"
                })
            
            return {
                "total_results": len(items),
                "items": items,
                "source": "arXiv"
            }
            
        except ET.ParseError as e:
            return {
                "total_results": 0,
                "items": [],
                "source": "arXiv",
                "error": str(e)
            }
