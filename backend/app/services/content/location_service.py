"""
Location Service
Fetches location data using Geopy/Nominatim (100% FREE)
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class LocationService:
    """Service for fetching location data"""
    
    def __init__(self):
        # Initialize Nominatim geocoder (OpenStreetMap - FREE)
        self.geolocator = Nominatim(user_agent="podcast_creator_app")
    
    async def get_location_details(self, location: str) -> Dict[str, Any]:
        """
        Fetch location details using Nominatim (OpenStreetMap)
        
        Args:
            location: Location name or address
            
        Returns:
            Dictionary with location details
        """
        try:
            logger.info("location_fetch_started", location=location)
            
            # Geocode the location
            location_data = self.geolocator.geocode(
                location,
                exactly_one=True,
                addressdetails=True,
                language='en'
            )
            
            if not location_data:
                logger.warning("location_not_found", location=location)
                return self._get_fallback_location(location)
            
            # Extract details
            details = {
                'display_name': location_data.address,
                'latitude': location_data.latitude,
                'longitude': location_data.longitude,
                'address': location_data.raw.get('address', {}),
                'type': location_data.raw.get('type', 'unknown'),
                'importance': location_data.raw.get('importance', 0),
                'place_id': location_data.raw.get('place_id'),
                'city': None,
                'state': None,
                'country': None,
                'country_code': ''
            }
            
            # Extract address components
            address = location_data.raw.get('address', {})
            details['city'] = address.get('city') or address.get('town') or address.get('village')
            details['state'] = address.get('state')
            details['country'] = address.get('country')
            details['country_code'] = address.get('country_code', '').upper()
            
            logger.info("location_fetch_complete",
                       location=location,
                       display_name=details['display_name'])
            
            return details
            
        except Exception as e:
            logger.error("location_fetch_failed",
                        location=location,
                        error=str(e))
            return self._get_fallback_location(location)
    
    def _get_fallback_location(self, location: str) -> Dict[str, Any]:
        """Fallback location data when geocoding fails"""
        return {
            'display_name': location,
            'latitude': None,
            'longitude': None,
            'address': {},
            'type': 'unknown',
            'importance': 0,
            'city': None,
            'state': None,
            'country': None,
            'country_code': ''
        }
