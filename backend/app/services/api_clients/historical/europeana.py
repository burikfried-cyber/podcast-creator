"""
Europeana API Client
Access to 55M+ European cultural heritage objects from 3500+ institutions
"""
from typing import Dict, Any, Optional, List
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)
import structlog

logger = structlog.get_logger()


class EuropeanaAPIClient(BaseAPIClient):
    """
    Europeana API Client
    
    Provides access to:
    - Search API: Search across collections
    - Record API: Get detailed item information
    - Entity API: Access to entities (people, places, concepts)
    - IIIF API: International Image Interoperability Framework
    - Annotation API: User-generated annotations
    - Recommendation API: Content recommendations
    
    Documentation: https://pro.europeana.eu/page/apis
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Europeana client
        
        Args:
            api_key: Europeana API key (wskey)
        """
        config = APIConfig(
            name="Europeana",
            base_url="https://api.europeana.eu",
            tier=APITier.FREE,
            category=APICategory.CULTURAL,
            rate_limit=10000,  # 10k requests per day
            rate_period=86400,  # 24 hours
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
        rows: int = 12,
        start: int = 1,
        profile: str = "standard",
        qf: Optional[List[str]] = None,
        reusability: Optional[str] = None,
        media: bool = True,
        thumbnail: bool = True,
        **kwargs
    ) -> APIResponse:
        """
        Search Europeana collections
        
        Args:
            query: Search query
            rows: Number of results (max 100)
            start: Start position (pagination)
            profile: Response profile (minimal, standard, rich)
            qf: Query filters (e.g., ["TYPE:IMAGE", "COUNTRY:France"])
            reusability: Filter by reusability (open, restricted, permission)
            media: Include only items with media
            thumbnail: Include only items with thumbnails
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with search results
        """
        params = {
            "query": query,
            "rows": min(rows, 100),
            "start": start,
            "profile": profile,
            "wskey": self.api_key
        }
        
        if qf:
            params["qf"] = qf
        
        if reusability:
            params["reusability"] = reusability
        
        if media:
            params["media"] = "true"
        
        if thumbnail:
            params["thumbnail"] = "true"
        
        params.update(kwargs)
        
        response = await self.get("/api/v2/search.json", params=params)
        
        if response.success:
            response.data = self.transform_response(response.data)
        
        return response
    
    async def get_record(self, record_id: str, profile: str = "rich") -> APIResponse:
        """
        Get detailed record information
        
        Args:
            record_id: Europeana record ID (e.g., "/123/abc")
            profile: Response profile (minimal, standard, rich)
            
        Returns:
            APIResponse with record details
        """
        params = {
            "profile": profile,
            "wskey": self.api_key
        }
        
        endpoint = f"/api/v2/record{record_id}.json"
        response = await self.get(endpoint, params=params)
        
        if response.success:
            response.data = self.transform_record(response.data)
        
        return response
    
    async def search_entities(
        self,
        query: str,
        entity_type: str = "agent",
        rows: int = 10,
        **kwargs
    ) -> APIResponse:
        """
        Search entities (people, places, concepts, time periods)
        
        Args:
            query: Search query
            entity_type: Type (agent, place, concept, timespan)
            rows: Number of results
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with entity results
        """
        params = {
            "query": query,
            "type": entity_type,
            "rows": rows,
            "wskey": self.api_key
        }
        params.update(kwargs)
        
        response = await self.get("/api/v2/entity/search", params=params)
        
        return response
    
    async def get_entity(self, entity_type: str, entity_id: str) -> APIResponse:
        """
        Get entity details
        
        Args:
            entity_type: Type (agent, place, concept, timespan)
            entity_id: Entity ID
            
        Returns:
            APIResponse with entity details
        """
        params = {"wskey": self.api_key}
        endpoint = f"/api/v2/entity/{entity_type}/{entity_id}"
        
        response = await self.get(endpoint, params=params)
        
        return response
    
    async def get_recommendations(
        self,
        record_id: str,
        rows: int = 10
    ) -> APIResponse:
        """
        Get content recommendations for a record
        
        Args:
            record_id: Europeana record ID
            rows: Number of recommendations
            
        Returns:
            APIResponse with recommendations
        """
        params = {
            "recordId": record_id,
            "rows": rows,
            "wskey": self.api_key
        }
        
        response = await self.get("/api/v2/recommendations", params=params)
        
        return response
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Europeana search response to standardized format
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Standardized data dictionary
        """
        if not raw_data or "items" not in raw_data:
            return {
                "total_results": 0,
                "items": [],
                "source": "Europeana"
            }
        
        items = []
        for item in raw_data.get("items", []):
            transformed = {
                "id": item.get("id"),
                "title": self._get_first_value(item.get("title")),
                "description": self._get_first_value(item.get("dcDescription")),
                "creator": self._get_first_value(item.get("dcCreator")),
                "date": self._get_first_value(item.get("year")),
                "type": self._get_first_value(item.get("type")),
                "subject": item.get("dcSubject", []),
                "language": self._get_first_value(item.get("language")),
                "country": self._get_first_value(item.get("country")),
                "provider": self._get_first_value(item.get("dataProvider")),
                "rights": self._get_first_value(item.get("rights")),
                "thumbnail": item.get("edmPreview", [None])[0] if item.get("edmPreview") else None,
                "url": item.get("guid"),
                "source": "Europeana",
                "raw": item
            }
            items.append(transformed)
        
        return {
            "total_results": raw_data.get("totalResults", 0),
            "items": items,
            "facets": raw_data.get("facets", []),
            "source": "Europeana"
        }
    
    def transform_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform detailed record response"""
        if not raw_data or "object" not in raw_data:
            return {}
        
        obj = raw_data["object"]
        
        return {
            "id": obj.get("about"),
            "title": self._get_first_value(obj.get("title")),
            "description": self._get_first_value(obj.get("dcDescription")),
            "creator": obj.get("dcCreator", []),
            "contributor": obj.get("dcContributor", []),
            "date": obj.get("year", []),
            "type": obj.get("type"),
            "format": obj.get("dcFormat", []),
            "subject": obj.get("dcSubject", []),
            "language": obj.get("dcLanguage", []),
            "coverage": obj.get("dcCoverage", []),
            "rights": obj.get("rights", []),
            "provider": obj.get("dataProvider", []),
            "aggregator": obj.get("provider", []),
            "country": obj.get("country", []),
            "media": obj.get("edmIsShownBy", []),
            "thumbnail": obj.get("edmPreview", []),
            "url": obj.get("edmIsShownAt", []),
            "source": "Europeana",
            "raw": obj
        }
    
    @staticmethod
    def _get_first_value(value: Any) -> Optional[str]:
        """Extract first value from list or return string"""
        if isinstance(value, list) and len(value) > 0:
            return str(value[0])
        elif isinstance(value, str):
            return value
        return None
