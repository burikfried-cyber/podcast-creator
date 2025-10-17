"""Tourism API Clients"""
from .opentripmap import OpenTripMapAPIClient
from .geoapify import GeoapifyPlacesAPIClient
from .foursquare import FoursquareAPIClient
from .amadeus import AmadeusAPIClient

__all__ = [
    "OpenTripMapAPIClient",
    "GeoapifyPlacesAPIClient",
    "FoursquareAPIClient",
    "AmadeusAPIClient"
]
