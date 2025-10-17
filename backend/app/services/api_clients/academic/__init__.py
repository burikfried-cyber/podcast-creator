"""Academic & Research API Clients"""
from .arxiv import ArXivAPIClient
from .pubmed import PubMedAPIClient
from .crossref import CrossRefAPIClient

__all__ = [
    "ArXivAPIClient",
    "PubMedAPIClient",
    "CrossRefAPIClient"
]
