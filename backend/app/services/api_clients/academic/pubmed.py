"""
PubMed API Client
35M+ biomedical citations
"""
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


class PubMedAPIClient(BaseAPIClient):
    """PubMed E-utilities API for biomedical literature"""
    
    def __init__(self, api_key: Optional[str] = None):
        config = APIConfig(
            name="PubMed",
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            tier=APITier.FREE,
            category=APICategory.ACADEMIC,
            rate_limit=10 if api_key else 3,  # 10/sec with key, 3/sec without
            rate_period=1,
            cost_per_request=0.0,
            timeout=30,
            cache_ttl=3600,
            requires_auth=False
        )
        super().__init__(config, api_key)
    
    async def search(
        self,
        query: str,
        retmax: int = 10,
        sort: str = "relevance",
        **kwargs
    ) -> APIResponse:
        """
        Search PubMed articles
        
        Args:
            query: Search query
            retmax: Maximum results
            sort: Sort order (relevance, pub_date, etc.)
            **kwargs: Additional parameters
            
        Returns:
            APIResponse with article IDs
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "sort": sort,
            "retmode": "json"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        params.update(kwargs)
        
        # First, search for IDs
        search_response = await self.get("/esearch.fcgi", params=params)
        
        if not search_response.success:
            return search_response
        
        # Extract IDs
        id_list = search_response.data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return APIResponse(
                success=True,
                data={"total_results": 0, "items": [], "source": "PubMed"},
                source="PubMed"
            )
        
        # Fetch article details
        return await self.get_articles_by_ids(id_list)
    
    async def get_articles_by_ids(self, ids: List[str]) -> APIResponse:
        """
        Get article details by PubMed IDs
        
        Args:
            ids: List of PubMed IDs
            
        Returns:
            APIResponse with article details
        """
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        response = await self.get("/efetch.fcgi", params=params)
        
        if response.success:
            response.data = self.transform_response(response.data)
        
        return response
    
    def transform_response(self, raw_data: str) -> Dict[str, Any]:
        """Transform PubMed XML response"""
        try:
            root = ET.fromstring(raw_data)
            items = []
            
            for article in root.findall(".//PubmedArticle"):
                medline = article.find(".//MedlineCitation")
                if medline is None:
                    continue
                
                pmid_elem = medline.find(".//PMID")
                article_elem = medline.find(".//Article")
                
                if article_elem is None:
                    continue
                
                # Extract authors
                authors = []
                author_list = article_elem.find(".//AuthorList")
                if author_list is not None:
                    for author in author_list.findall(".//Author"):
                        last_name = author.find("LastName")
                        fore_name = author.find("ForeName")
                        if last_name is not None and fore_name is not None:
                            authors.append(f"{fore_name.text} {last_name.text}")
                
                # Extract abstract
                abstract_elem = article_elem.find(".//Abstract/AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else None
                
                # Extract journal info
                journal = article_elem.find(".//Journal")
                journal_title = None
                pub_date = None
                if journal is not None:
                    journal_title_elem = journal.find(".//Title")
                    journal_title = journal_title_elem.text if journal_title_elem is not None else None
                    
                    pub_date_elem = journal.find(".//PubDate/Year")
                    pub_date = pub_date_elem.text if pub_date_elem is not None else None
                
                # Extract title
                title_elem = article_elem.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else None
                
                items.append({
                    "id": pmid_elem.text if pmid_elem is not None else None,
                    "title": title,
                    "description": abstract,
                    "authors": authors,
                    "journal": journal_title,
                    "date": pub_date,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/" if pmid_elem is not None else None,
                    "source": "PubMed"
                })
            
            return {
                "total_results": len(items),
                "items": items,
                "source": "PubMed"
            }
            
        except ET.ParseError as e:
            return {
                "total_results": 0,
                "items": [],
                "source": "PubMed",
                "error": str(e)
            }
