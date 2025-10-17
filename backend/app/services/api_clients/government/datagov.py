"""
Data.gov API Client
200k+ US government datasets
"""
from typing import Dict, Any, Optional
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class DataGovAPIClient(BaseAPIClient):
    """Data.gov CKAN API for US government datasets"""
    
    def __init__(self):
        config = APIConfig(
            name="DataGov",
            base_url="https://catalog.data.gov/api/3",
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
        rows: int = 10,
        sort: str = "score desc",
        **kwargs
    ) -> APIResponse:
        """
        Search datasets
        
        Args:
            query: Search query
            rows: Number of results
            sort: Sort order
            **kwargs: Additional filters (e.g., organization, tags)
            
        Returns:
            APIResponse with datasets
        """
        params = {
            "q": query,
            "rows": rows,
            "sort": sort
        }
        params.update(kwargs)
        
        response = await self.get("/action/package_search", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    async def get_dataset(self, dataset_id: str) -> APIResponse:
        """
        Get dataset details
        
        Args:
            dataset_id: Dataset ID or name
            
        Returns:
            APIResponse with dataset details
        """
        params = {"id": dataset_id}
        response = await self.get("/action/package_show", params=params)
        if response.success:
            response.data = self.transform_dataset(response.data.get("result", {}))
        return response
    
    async def get_organizations(self, limit: int = 20) -> APIResponse:
        """Get list of organizations"""
        params = {"limit": limit, "all_fields": True}
        response = await self.get("/action/organization_list", params=params)
        return response
    
    async def search_by_organization(
        self,
        organization: str,
        rows: int = 10
    ) -> APIResponse:
        """Search datasets by organization"""
        params = {
            "fq": f"organization:{organization}",
            "rows": rows
        }
        
        response = await self.get("/action/package_search", params=params)
        if response.success:
            response.data = self.transform_response(response.data)
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Data.gov search response"""
        if not raw_data or "result" not in raw_data:
            return {"total_results": 0, "items": [], "source": "DataGov"}
        
        result = raw_data["result"]
        items = []
        
        for dataset in result.get("results", []):
            items.append(self.transform_dataset(dataset))
        
        return {
            "total_results": result.get("count", len(items)),
            "items": items,
            "source": "DataGov"
        }
    
    def transform_dataset(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Transform individual dataset"""
        # Extract resources
        resources = []
        for resource in dataset.get("resources", []):
            resources.append({
                "name": resource.get("name"),
                "format": resource.get("format"),
                "url": resource.get("url"),
                "description": resource.get("description")
            })
        
        return {
            "id": dataset.get("id"),
            "title": dataset.get("title"),
            "description": dataset.get("notes"),
            "organization": dataset.get("organization", {}).get("title"),
            "tags": [tag.get("name") for tag in dataset.get("tags", [])],
            "date": dataset.get("metadata_created"),
            "modified": dataset.get("metadata_modified"),
            "license": dataset.get("license_title"),
            "url": f"https://catalog.data.gov/dataset/{dataset.get('name')}",
            "resources": resources,
            "num_resources": len(resources),
            "source": "DataGov"
        }
