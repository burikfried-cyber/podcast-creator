"""
Content Aggregator - Orchestrates parallel calls to all content sources
"""
import asyncio
import time
from typing import Dict, List, Any
import structlog
from app.services.content.wikipedia_service import WikipediaService
from app.services.content.wikidata_service import wikidata_service
from app.services.content.geonames_service import geonames_service
from app.services.content.location_service import LocationService

logger = structlog.get_logger()


class ContentAggregator:
    """
    Orchestrates parallel content collection from multiple sources.
    Target: <5 seconds total collection time
    """
    
    def __init__(self):
        self.wikipedia = WikipediaService()
        self.wikidata = wikidata_service
        self.geonames = geonames_service
        self.location_service = LocationService()
        
    async def gather_location_content(self, location_name: str) -> Dict[str, Any]:
        """
        Main entry point: Gather content from all sources in parallel.
        
        Args:
            location_name: Location to gather content for
            
        Returns:
            Aggregated content with metadata
        """
        start_time = time.time()
        
        logger.info("content_aggregation_started", location=location_name)
        
        try:
            # Execute all sources in parallel using asyncio.gather
            results = await asyncio.gather(
                self._gather_wikipedia(location_name),
                self._gather_wikidata(location_name),
                self._gather_geonames(location_name),
                self._gather_location_data(location_name),
                return_exceptions=True  # Don't let one failure break all
            )
            
            # Unpack results (handle exceptions)
            wikipedia_data = results[0] if not isinstance(results[0], Exception) else {}
            wikidata_data = results[1] if not isinstance(results[1], Exception) else {}
            geonames_data = results[2] if not isinstance(results[2], Exception) else {}
            location_data = results[3] if not isinstance(results[3], Exception) else {}
            
            # Build aggregated result
            aggregated = {
                "location_name": location_name,
                "sources": {
                    "wikipedia": wikipedia_data,
                    "wikidata": wikidata_data,
                    "geonames": geonames_data,
                    "location": location_data
                },
                "hierarchy": self._build_hierarchy(geonames_data),
                "structured_facts": self._merge_facts(wikipedia_data, wikidata_data),
                "geographic_context": self._build_geographic_context(geonames_data),
                "quality_scores": self._calculate_quality_scores(
                    wikipedia_data, wikidata_data, geonames_data, location_data
                ),
                "collection_metadata": {
                    "collection_time_seconds": round(time.time() - start_time, 2),
                    "sources_successful": self._count_successful_sources(results),
                    "sources_failed": self._count_failed_sources(results),
                    "timestamp": time.time()
                }
            }
            
            # Log source success rates
            self._log_source_results(aggregated)
            
            logger.info("content_aggregation_completed",
                       location=location_name,
                       collection_time=aggregated["collection_metadata"]["collection_time_seconds"],
                       sources_successful=aggregated["collection_metadata"]["sources_successful"])
            
            return aggregated
            
        except Exception as e:
            logger.error("content_aggregation_error", error=str(e), location=location_name)
            return self._get_fallback_aggregated_content(location_name)
    
    async def _gather_wikipedia(self, location_name: str) -> Dict:
        """Gather Wikipedia content"""
        try:
            return await self.wikipedia.get_location_content(location_name)
        except Exception as e:
            logger.error("wikipedia_gather_failed", error=str(e))
            return {}
    
    async def _gather_wikidata(self, location_name: str) -> Dict:
        """Gather Wikidata content"""
        try:
            return await self.wikidata.get_location_content(location_name)
        except Exception as e:
            logger.error("wikidata_gather_failed", error=str(e))
            return {}
    
    async def _gather_geonames(self, location_name: str) -> Dict:
        """Gather GeoNames content"""
        try:
            return await self.geonames.get_location_content(location_name)
        except Exception as e:
            logger.error("geonames_gather_failed", error=str(e))
            return {}
    
    async def _gather_location_data(self, location_name: str) -> Dict:
        """Gather basic location service data"""
        try:
            return await self.location_service.get_location_details(location_name)
        except Exception as e:
            logger.error("location_service_gather_failed", error=str(e))
            return {}
    
    def _build_hierarchy(self, geonames_data: Dict) -> Dict[str, Any]:
        """Build hierarchical location structure from GeoNames"""
        if not geonames_data or "error" in geonames_data:
            return {
                "neighborhood": None,
                "district": None,
                "city": None,
                "region": None,
                "country": None
            }
        
        return geonames_data.get("hierarchy", {})
    
    def _merge_facts(self, wikipedia_data: Dict, wikidata_data: Dict) -> List[Dict]:
        """Merge and deduplicate facts from Wikipedia and Wikidata"""
        facts = []
        
        # Add Wikipedia interesting facts
        if wikipedia_data and "interesting_facts" in wikipedia_data:
            wiki_facts = wikipedia_data.get("interesting_facts", [])
            for fact in wiki_facts:
                if isinstance(fact, str):
                    facts.append({
                        "source": "wikipedia",
                        "type": "narrative",
                        "content": fact
                    })
        
        # Add Wikidata structured facts
        if wikidata_data and "facts" in wikidata_data:
            wd_facts = wikidata_data.get("facts", [])
            for fact in wd_facts:
                facts.append({
                    "source": "wikidata",
                    "type": "structured",
                    "property": fact.get("property"),
                    "value": fact.get("value")
                })
        
        return facts
    
    def _build_geographic_context(self, geonames_data: Dict) -> Dict:
        """Build geographic context from GeoNames data"""
        if not geonames_data or "error" in geonames_data:
            return {}
        
        return {
            "coordinates": geonames_data.get("coordinates", {}),
            "population": geonames_data.get("population", 0),
            "feature_type": geonames_data.get("feature_code"),
            "nearby_places": geonames_data.get("nearby_places", [])
        }
    
    def _calculate_quality_scores(self, wikipedia: Dict, wikidata: Dict, 
                                  geonames: Dict, location: Dict) -> Dict[str, float]:
        """Calculate quality scores for each source"""
        scores = {
            "wikipedia": self._score_source(wikipedia),
            "wikidata": self._score_source(wikidata),
            "geonames": self._score_source(geonames),
            "location": self._score_source(location)
        }
        
        # Calculate overall score (weighted average)
        weights = {"wikipedia": 0.35, "wikidata": 0.30, "geonames": 0.25, "location": 0.10}
        overall = sum(scores[src] * weights[src] for src in scores)
        scores["overall"] = round(overall, 2)
        
        return scores
    
    def _score_source(self, source_data: Dict) -> float:
        """Score individual source based on data completeness"""
        if not source_data or "error" in source_data:
            return 0.0
        
        # Use confidence_score if available
        if "confidence_score" in source_data:
            return source_data["confidence_score"]
        
        # Otherwise calculate basic score
        score = 0.0
        if source_data.get("title") or source_data.get("name"): score += 0.3
        if source_data.get("summary") or source_data.get("description"): score += 0.3
        if source_data.get("content") or source_data.get("facts"): score += 0.4
        
        return round(score, 2)
    
    def _count_successful_sources(self, results: List) -> int:
        """Count how many sources returned successfully"""
        count = 0
        for result in results:
            if not isinstance(result, Exception) and result and "error" not in result:
                count += 1
        return count
    
    def _count_failed_sources(self, results: List) -> int:
        """Count how many sources failed"""
        return len(results) - self._count_successful_sources(results)
    
    def _log_source_results(self, aggregated: Dict):
        """Log detailed source success/failure information"""
        sources = aggregated.get("sources", {})
        quality_scores = aggregated.get("quality_scores", {})
        
        for source_name, source_data in sources.items():
            if source_data and "error" not in source_data:
                logger.info(f"{source_name}_success",
                           quality_score=quality_scores.get(source_name, 0.0))
            else:
                logger.warning(f"{source_name}_failed",
                             error=source_data.get("error", "Unknown error"))
    
    def _get_fallback_aggregated_content(self, location_name: str) -> Dict:
        """Return fallback content when aggregation fails completely"""
        return {
            "location_name": location_name,
            "sources": {
                "wikipedia": {},
                "wikidata": {},
                "geonames": {},
                "location": {}
            },
            "hierarchy": {
                "neighborhood": None,
                "district": None,
                "city": None,
                "region": None,
                "country": None
            },
            "structured_facts": [],
            "geographic_context": {},
            "quality_scores": {
                "wikipedia": 0.0,
                "wikidata": 0.0,
                "geonames": 0.0,
                "location": 0.0,
                "overall": 0.0
            },
            "collection_metadata": {
                "collection_time_seconds": 0.0,
                "sources_successful": 0,
                "sources_failed": 4,
                "timestamp": time.time(),
                "error": "Complete aggregation failure"
            }
        }


# Singleton instance
content_aggregator = ContentAggregator()
