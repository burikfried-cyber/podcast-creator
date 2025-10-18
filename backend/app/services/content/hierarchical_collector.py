"""
Hierarchical Content Collector
Collects content at multiple geographic levels based on user preferences.
Implements smart weighting to balance local vs contextual information.
"""
import asyncio
from typing import Dict, List, Optional, Any
import structlog
from app.services.content.content_aggregator import content_aggregator

logger = structlog.get_logger()


class HierarchicalContentCollector:
    """
    Collects content at multiple geographic levels based on user preferences.
    Supports three context preferences: very_local, balanced, broad_context
    """
    
    def __init__(self):
        self.aggregator = content_aggregator
        
        # Weight distributions for each context preference
        self.weight_profiles = {
            "very_local": {
                "local": 0.60,
                "district": 0.25,
                "city": 0.10,
                "region": 0.03,
                "country": 0.02
            },
            "balanced": {
                "local": 0.30,
                "district": 0.25,
                "city": 0.30,
                "region": 0.10,
                "country": 0.05
            },
            "broad_context": {
                "local": 0.10,
                "district": 0.15,
                "city": 0.35,
                "region": 0.20,
                "country": 0.20
            }
        }
    
    async def collect_hierarchical_content(
        self,
        primary_location: str,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Collect content at multiple geographic levels.
        
        Args:
            primary_location: User's specific location (e.g., "Shibuya Crossing, Tokyo")
            user_preferences: User's depth, context preference
            
        Returns:
            Multi-level content with automatic weighting
        """
        try:
            logger.info("hierarchical_collection_started", location=primary_location)
            
            # Step 1: Get primary location content (includes hierarchy)
            primary_content = await self.aggregator.gather_location_content(primary_location)
            
            if not primary_content or primary_content.get("error"):
                logger.warning(f"Primary location gathering failed for {primary_location}")
                return self._get_fallback_content(primary_location)
            
            # Step 2: Extract hierarchy
            hierarchy = primary_content.get("hierarchy", {})
            
            # Step 3: Determine context preference
            context_preference = self._get_context_preference(user_preferences)
            
            # Step 4: Collect additional context at higher levels (if needed)
            additional_contexts = await self._collect_additional_contexts(
                hierarchy,
                context_preference,
                primary_location
            )
            
            # Step 5: Build content levels dictionary
            content_levels = self._build_content_levels(
                primary_content,
                additional_contexts,
                hierarchy
            )
            
            # Step 6: Calculate weights based on available levels
            content_weights = self._calculate_weights(
                content_levels,
                context_preference
            )
            
            # Step 7: Build final result
            result = {
                "primary_location": primary_location,
                "hierarchy": hierarchy,
                "content_levels": content_levels,
                "content_weights": content_weights,
                "context_preference": context_preference,
                "primary_content": primary_content,  # Full aggregated content
                "collection_metadata": {
                    "levels_collected": len([v for v in content_levels.values() if v]),
                    "total_weight": sum(content_weights.values())
                }
            }
            
            logger.info("hierarchical_collection_completed",
                       location=primary_location,
                       context=context_preference,
                       levels_collected=result["collection_metadata"]["levels_collected"])
            
            return result
            
        except Exception as e:
            logger.error("hierarchical_collection_error", error=str(e), location=primary_location)
            return self._get_fallback_content(primary_location)
    
    def _get_context_preference(self, user_preferences: Optional[Dict]) -> str:
        """
        Determine context preference from user preferences.
        Maps depth_preference (1-6) to context levels.
        """
        if not user_preferences:
            return "balanced"
        
        # Check if context_level is explicitly provided
        if "context_level" in user_preferences:
            context = user_preferences["context_level"]
            if context in ["very_local", "balanced", "broad_context"]:
                return context
        
        # Map depth_preference to context level
        depth = user_preferences.get("depth_preference", 3)
        
        if depth <= 2:
            return "very_local"
        elif depth <= 4:
            return "balanced"
        else:
            return "broad_context"
    
    async def _collect_additional_contexts(
        self,
        hierarchy: Dict[str, Optional[str]],
        context_preference: str,
        primary_location: str
    ) -> Dict[str, Dict]:
        """
        Smart collection strategy: Only fetch what's needed.
        
        Rules:
        - very_local: No additional fetches (use primary content only)
        - balanced: Fetch city if different from primary
        - broad_context: Fetch city AND country if different
        """
        additional = {}
        
        city_name = hierarchy.get("city")
        country_name = hierarchy.get("country")
        
        # Determine what to fetch based on context preference
        fetch_city = False
        fetch_country = False
        
        if context_preference == "balanced":
            # Fetch city only if it's different from primary location
            if city_name and city_name.lower() not in primary_location.lower():
                fetch_city = True
        
        elif context_preference == "broad_context":
            # Fetch both city and country
            if city_name and city_name.lower() not in primary_location.lower():
                fetch_city = True
            if country_name:
                fetch_country = True
        
        # Collect in parallel
        tasks = []
        task_keys = []
        
        if fetch_city:
            tasks.append(self.aggregator.gather_location_content(city_name))
            task_keys.append("city")
            logger.info("fetching_city_context", city=city_name)
        
        if fetch_country:
            tasks.append(self.aggregator.gather_location_content(country_name))
            task_keys.append("country")
            logger.info("fetching_country_context", country=country_name)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result:
                    additional[task_keys[i]] = result
                else:
                    logger.warning(f"failed_to_fetch_{task_keys[i]}", 
                                 location=city_name if task_keys[i] == "city" else country_name)
        
        return additional
    
    def _build_content_levels(
        self,
        primary_content: Dict,
        additional_contexts: Dict,
        hierarchy: Dict
    ) -> Dict[str, Optional[Dict]]:
        """
        Build content levels dictionary from primary and additional content.
        """
        content_levels = {
            "local": primary_content,  # Always have primary content
            "district": None,
            "city": None,
            "region": None,
            "country": None
        }
        
        # Add additional contexts if fetched
        if "city" in additional_contexts:
            content_levels["city"] = additional_contexts["city"]
        
        if "country" in additional_contexts:
            content_levels["country"] = additional_contexts["country"]
        
        # Note: district and region are typically part of primary content hierarchy
        # We don't fetch them separately to optimize performance
        
        return content_levels
    
    def _calculate_weights(
        self,
        content_levels: Dict[str, Optional[Dict]],
        context_preference: str
    ) -> Dict[str, float]:
        """
        Calculate content weights based on available levels and preference.
        Redistributes weights if levels are missing.
        """
        # Get base weights for this preference
        base_weights = self.weight_profiles[context_preference].copy()
        
        # Identify available levels
        available_levels = [level for level, content in content_levels.items() if content]
        
        # Identify missing levels
        missing_levels = [level for level, content in content_levels.items() if not content]
        
        # Calculate total weight of missing levels
        missing_weight = sum(base_weights[level] for level in missing_levels)
        
        # Redistribute missing weight proportionally to available levels
        if missing_weight > 0 and available_levels:
            # Calculate total base weight of available levels
            available_base_weight = sum(base_weights[level] for level in available_levels)
            
            # Redistribute proportionally
            final_weights = {}
            for level in content_levels.keys():
                if level in available_levels:
                    # Proportional redistribution
                    proportion = base_weights[level] / available_base_weight
                    final_weights[level] = base_weights[level] + (missing_weight * proportion)
                else:
                    final_weights[level] = 0.0
        else:
            # All levels available or no redistribution needed
            final_weights = {level: base_weights[level] if level in available_levels else 0.0 
                           for level in content_levels.keys()}
        
        # Normalize to ensure sum = 1.0
        total_weight = sum(final_weights.values())
        if total_weight > 0:
            final_weights = {level: weight / total_weight for level, weight in final_weights.items()}
        
        # Round to 2 decimal places
        final_weights = {level: round(weight, 2) for level, weight in final_weights.items()}
        
        logger.info("weights_calculated",
                   context=context_preference,
                   weights=final_weights,
                   total=sum(final_weights.values()))
        
        return final_weights
    
    def _get_fallback_content(self, primary_location: str) -> Dict:
        """Return fallback content when collection fails"""
        return {
            "primary_location": primary_location,
            "hierarchy": {
                "neighborhood": None,
                "district": None,
                "city": None,
                "region": None,
                "country": None
            },
            "content_levels": {
                "local": {},
                "district": None,
                "city": None,
                "region": None,
                "country": None
            },
            "content_weights": {
                "local": 1.0,
                "district": 0.0,
                "city": 0.0,
                "region": 0.0,
                "country": 0.0
            },
            "context_preference": "balanced",
            "primary_content": {},
            "collection_metadata": {
                "levels_collected": 0,
                "total_weight": 1.0,
                "error": "Collection failed"
            }
        }


# Singleton instance
hierarchical_collector = HierarchicalContentCollector()
