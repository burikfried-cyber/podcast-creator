"""
Data.europa.eu API Client
1.3M+ European open datasets
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class DataEuropaAPIClient(BaseAPIClient):
    """Data.europa.eu CKAN API for European open data"""
    
    def __init__(self):
        config = APIConfig(
            name="DataEuropa",
            base_url="https://data.europa.eu/api/hub",
            tier=APITier.FREE,
            category=APICategory.GOVERNMENT,
            rate_limit=1000,  # Conservative limit
            rate_period=3600,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=3600,
            requires_auth=False
        )
        super().__init__(config)
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        sort: str = "relevance+desc",
        **kwargs
    ) -> APIResponse:
        """
        Search datasets
        
        Args:
            query: Search query
            limit: Number of results
            sort: Sort order
            **kwargs: Additional filters
            
        Returns:
            APIResponse with datasets
        """
        params = {
            "q": query,
            "limit": limit,
            "sort": sort,
            "filter": "dataset"
        }
        params.update(kwargs)
        
        response = await self.get("/search/datasets", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_dataset(self, dataset_id: str) -> APIResponse:
        """
        Get dataset details
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            APIResponse with dataset details
        """
        response = await self.get(f"/datasets/{dataset_id}")
        if response.success:
            response.data = self.transform_dataset(response.data)
        return response
    
    async def search_by_country(
        self,
        country_code: str,
        query: Optional[str] = None,
        limit: int = 10
    ) -> APIResponse:
        """
        Search datasets by country
        
        Args:
            country_code: ISO country code (e.g., "FR", "DE")
            query: Optional search query
            limit: Number of results
            
        Returns:
            APIResponse with datasets
        """
        params = {
            "limit": limit,
            "filter": "dataset",
            "country": country_code
        }
        
        if query:
            params["q"] = query
        
        response = await self.get("/search/datasets", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def search_by_topic(
        self,
        topic: str,
        limit: int = 10
    ) -> APIResponse:
        """
        Search datasets by topic
        
        Args:
            topic: Topic/theme
            limit: Number of results
            
        Returns:
            APIResponse with datasets
        """
        params = {
            "limit": limit,
            "filter": "dataset",
            "facet": f"theme:{topic}"
        }
        
        response = await self.get("/search/datasets", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Data.europa search response"""
        if not raw_data or "result" not in raw_data:
            return {"total_results": 0, "items": [], "source": "DataEuropa"}
        
        result = raw_data["result"]
        items = []
        
        for dataset in result.get("results", []):
            items.append(self.transform_dataset(dataset))
        
        return {
            "total_results": result.get("count", len(items)),
            "items": items,
            "source": "DataEuropa"
        }
    
    def transform_dataset(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Transform individual dataset"""
        # Extract distributions (resources)
        distributions = []
        for dist in dataset.get("distributions", []):
            distributions.append({
                "format": dist.get("format"),
                "url": dist.get("accessUrl"),
                "license": dist.get("license")
            })
        
        return {
            "id": dataset.get("id"),
            "title": dataset.get("title", {}).get("en", dataset.get("title")),
            "description": dataset.get("description", {}).get("en", dataset.get("description")),
            "publisher": dataset.get("publisher", {}).get("name"),
            "country": dataset.get("country", {}).get("id"),
            "themes": dataset.get("themes", []),
            "keywords": dataset.get("keywords", {}).get("en", []),
            "date": dataset.get("issued"),
            "modified": dataset.get("modified"),
            "license": dataset.get("license"),
            "url": dataset.get("landingPage"),
            "distributions": distributions,
            "num_distributions": len(distributions),
            "source": "DataEuropa"
        }
