"""
Smithsonian Open Access API Client
Access to 3M+ museum objects with rich metadata and high-resolution images
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


class SmithsonianAPIClient(BaseAPIClient):
    """
    Smithsonian Open Access API Client
    
    Provides access to millions of museum objects across:
    - Art & Design
    - History & Culture
    - Science & Technology
    
    Documentation: https://api.si.edu/openaccess/api/v1.0/
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Smithsonian client
        
        Args:
            api_key: Smithsonian API key
        """
        config = APIConfig(
            name="Smithsonian",
            base_url="https://api.si.edu/openaccess/api/v1.0",
            tier=APITier.FREE,
            category=APICategory.CULTURAL,
            rate_limit=1000,  # 1000 requests per hour
            rate_period=3600,
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
        rows: int = 10,
        start: int = 0,
        sort: str = "relevancy",
        type: Optional[str] = None,
        online_media: bool = True,
        **kwargs
    ) -> APIResponse:
        """
        Search Smithsonian collections
        
        Args:
            query: Search query (supports Lucene syntax)
            rows: Number of results (max 1000)
            start: Start position for pagination
            sort: Sort order (relevancy, id, newest, updated, random)
            type: Filter by type (edanmdm, ead_collection, ead_component)
            online_media: Include only items with online media
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with search results
        """
        params = {
            "q": query,
            "rows": min(rows, 1000),
            "start": start,
            "sort": sort,
            "api_key": self.api_key
        }
        
        if type:
            params["type"] = type
        
        if online_media:
            params["online_media_type"] = "true"
        
        params.update(kwargs)
        
        response = await self.get("/search", params=params)
        
        if response.success:
            response.data = self.transform_response(response.data)
        
        return response
    
    async def get_content(self, content_id: str) -> APIResponse:
        """
        Get detailed content by ID
        
        Args:
            content_id: Smithsonian content ID
            
        Returns:
            APIResponse with content details
        """
        params = {"api_key": self.api_key}
        endpoint = f"/content/{content_id}"
        
        response = await self.get(endpoint, params=params)
        
        if response.success:
            response.data = self.transform_content(response.data)
        
        return response
    
    async def get_terms(
        self,
        category: str = "topic",
        query: Optional[str] = None,
        rows: int = 10
    ) -> APIResponse:
        """
        Get controlled vocabulary terms
        
        Args:
            category: Term category (topic, place, culture, tax_kingdom, etc.)
            query: Filter terms by query
            rows: Number of results
            
        Returns:
            APIResponse with terms
        """
        params = {
            "category": category,
            "rows": rows,
            "api_key": self.api_key
        }
        
        if query:
            params["q"] = query
        
        response = await self.get("/terms", params=params)
        
        return response
    
    async def search_by_location(
        self,
        latitude: float,
        longitude: float,
        distance: float = 10.0,
        rows: int = 10
    ) -> APIResponse:
        """
        Search for content near a geographic location
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            distance: Search radius in kilometers
            rows: Number of results
            
        Returns:
            APIResponse with nearby content
        """
        # Construct geospatial query
        query = f"{{!geofilt pt={latitude},{longitude} sfield=location d={distance}}}"
        
        return await self.search(query=query, rows=rows)
    
    def transform_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Smithsonian search response to standardized format
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Standardized data dictionary
        """
        if not raw_data or "response" not in raw_data:
            return {
                "total_results": 0,
                "items": [],
                "source": "Smithsonian"
            }
        
        response = raw_data["response"]
        items = []
        
        for row in response.get("rows", []):
            content = row.get("content", {})
            descriptive_data = content.get("descriptiveNonRepeating", {})
            indexed_data = content.get("indexedStructured", {})
            freetext = content.get("freetext", {})
            
            # Extract media
            media = []
            online_media = descriptive_data.get("online_media", {})
            if online_media and "media" in online_media:
                for item in online_media["media"]:
                    if "content" in item:
                        media.append({
                            "url": item.get("content"),
                            "thumbnail": item.get("thumbnail"),
                            "type": item.get("type"),
                            "caption": item.get("caption")
                        })
            
            transformed = {
                "id": row.get("id"),
                "title": row.get("title"),
                "description": self._extract_text(freetext.get("notes")),
                "type": row.get("type"),
                "unit_code": row.get("unitCode"),
                "date": self._extract_dates(indexed_data.get("date")),
                "place": self._extract_places(indexed_data.get("place")),
                "topic": indexed_data.get("topic", []),
                "culture": indexed_data.get("culture", []),
                "object_type": indexed_data.get("object_type", []),
                "data_source": descriptive_data.get("data_source"),
                "record_link": descriptive_data.get("record_link"),
                "media": media,
                "thumbnail": media[0]["thumbnail"] if media else None,
                "source": "Smithsonian",
                "raw": row
            }
            items.append(transformed)
        
        return {
            "total_results": response.get("rowCount", 0),
            "items": items,
            "source": "Smithsonian"
        }
    
    def transform_content(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform detailed content response"""
        if not raw_data or "response" not in raw_data:
            return {}
        
        content = raw_data["response"]
        descriptive = content.get("descriptiveNonRepeating", {})
        indexed = content.get("indexedStructured", {})
        freetext = content.get("freetext", {})
        
        return {
            "id": content.get("id"),
            "title": content.get("title"),
            "description": self._extract_text(freetext.get("notes")),
            "unit_code": content.get("unitCode"),
            "metadata_usage": descriptive.get("metadata_usage"),
            "record_link": descriptive.get("record_link"),
            "date": indexed.get("date", []),
            "place": indexed.get("place", []),
            "topic": indexed.get("topic", []),
            "culture": indexed.get("culture", []),
            "object_type": indexed.get("object_type", []),
            "medium": freetext.get("physicalDescription", []),
            "dimensions": freetext.get("setName", []),
            "credit_line": freetext.get("creditLine", []),
            "data_source": descriptive.get("data_source"),
            "source": "Smithsonian",
            "raw": content
        }
    
    @staticmethod
    def _extract_text(notes: Optional[List[Dict]]) -> Optional[str]:
        """Extract text from notes array"""
        if not notes or not isinstance(notes, list):
            return None
        
        texts = []
        for note in notes:
            if isinstance(note, dict) and "content" in note:
                texts.append(note["content"])
        
        return " ".join(texts) if texts else None
    
    @staticmethod
    def _extract_dates(dates: Optional[List]) -> List[str]:
        """Extract date strings from date array"""
        if not dates:
            return []
        
        result = []
        for date in dates:
            if isinstance(date, str):
                result.append(date)
            elif isinstance(date, dict):
                result.append(date.get("content", ""))
        
        return result
    
    @staticmethod
    def _extract_places(places: Optional[List]) -> List[str]:
        """Extract place names from place array"""
        if not places:
            return []
        
        result = []
        for place in places:
            if isinstance(place, str):
                result.append(place)
            elif isinstance(place, dict):
                result.append(place.get("content", ""))
        
        return result
