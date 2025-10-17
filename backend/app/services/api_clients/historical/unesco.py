"""
UNESCO World Heritage API Client
Access to 1100+ World Heritage Sites
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
import structlog

logger = structlog.get_logger()


class UNESCOWorldHeritageAPIClient(BaseAPIClient):
    """
    UNESCO World Heritage API Client
    
    Provides access to World Heritage Sites information
    Note: This is a simple XML feed, not a full REST API
    
    Documentation: https://whc.unesco.org/en/syndication
    """
    
    def __init__(self):
        """Initialize UNESCO client (no API key required)"""
        config = APIConfig(
            name="UNESCO",
            base_url="https://whc.unesco.org",
            tier=APITier.FREE,
            category=APICategory.CULTURAL,
            rate_limit=100,  # Conservative limit
            rate_period=3600,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=3600,  # Cache for 1 hour
            requires_auth=False
        )
        
        super().__init__(config)
    
    async def search(
        self,
        query: str,
        **kwargs
    ) -> APIResponse:
        """
        Search World Heritage Sites
        Note: This performs client-side filtering of the XML feed
        
        Args:
            query: Search query (matches against name and description)
            **kwargs: Additional filters
            
        Returns:
            APIResponse with matching sites
        """
        # Get all sites
        response = await self.get_all_sites()
        
        if not response.success:
            return response
        
        # Filter by query
        query_lower = query.lower()
        filtered_items = [
            item for item in response.data["items"]
            if query_lower in item.get("title", "").lower()
            or query_lower in item.get("description", "").lower()
            or query_lower in item.get("location", "").lower()
        ]
        
        response.data["items"] = filtered_items
        response.data["total_results"] = len(filtered_items)
        
        return response
    
    async def get_all_sites(self) -> APIResponse:
        """
        Get all World Heritage Sites
        
        Returns:
            APIResponse with all sites
        """
        response = await self.get("/en/list/xml")
        
        if response.success:
            response.data = self.transform_response(response.data)
        
        return response
    
    async def get_site_by_id(self, site_id: str) -> APIResponse:
        """
        Get specific site by ID
        
        Args:
            site_id: UNESCO site ID
            
        Returns:
            APIResponse with site details
        """
        # Get all sites and filter
        response = await self.get_all_sites()
        
        if not response.success:
            return response
        
        # Find matching site
        site = next(
            (item for item in response.data["items"] if item["id"] == site_id),
            None
        )
        
        if site:
            response.data = site
        else:
            response.success = False
            response.error = f"Site {site_id} not found"
            response.data = None
        
        return response
    
    async def get_sites_by_country(self, country: str) -> APIResponse:
        """
        Get sites in a specific country
        
        Args:
            country: Country name
            
        Returns:
            APIResponse with sites in country
        """
        response = await self.get_all_sites()
        
        if not response.success:
            return response
        
        country_lower = country.lower()
        filtered_items = [
            item for item in response.data["items"]
            if country_lower in item.get("location", "").lower()
        ]
        
        response.data["items"] = filtered_items
        response.data["total_results"] = len(filtered_items)
        
        return response
    
    def transform_response(self, raw_data: str) -> Dict[str, Any]:
        """
        Transform UNESCO XML response to standardized format
        
        Args:
            raw_data: Raw XML string
            
        Returns:
            Standardized data dictionary
        """
        try:
            root = ET.fromstring(raw_data)
            items = []
            
            for row in root.findall(".//row"):
                # Extract data from XML
                site_id = self._get_xml_text(row, "id_number")
                name = self._get_xml_text(row, "site")
                
                # Parse coordinates
                latitude = self._get_xml_text(row, "latitude")
                longitude = self._get_xml_text(row, "longitude")
                
                transformed = {
                    "id": site_id,
                    "title": name,
                    "description": self._get_xml_text(row, "short_description"),
                    "justification": self._get_xml_text(row, "justification"),
                    "location": self._get_xml_text(row, "states"),
                    "region": self._get_xml_text(row, "region"),
                    "category": self._get_xml_text(row, "category"),
                    "criteria": self._get_xml_text(row, "criteria_txt"),
                    "date_inscribed": self._get_xml_text(row, "date_inscribed"),
                    "latitude": float(latitude) if latitude else None,
                    "longitude": float(longitude) if longitude else None,
                    "area_hectares": self._get_xml_text(row, "area_hectares"),
                    "danger": self._get_xml_text(row, "danger") == "1",
                    "url": f"https://whc.unesco.org/en/list/{site_id}",
                    "source": "UNESCO"
                }
                items.append(transformed)
            
            return {
                "total_results": len(items),
                "items": items,
                "source": "UNESCO"
            }
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse UNESCO XML: {e}")
            return {
                "total_results": 0,
                "items": [],
                "source": "UNESCO",
                "error": str(e)
            }
    
    @staticmethod
    def _get_xml_text(element: ET.Element, tag: str) -> Optional[str]:
        """Extract text from XML element"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
