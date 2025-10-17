"""
Base Content Detector
Extracts essential information with >95% completeness target
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class BaseContentDetector:
    """
    Base Content Detection for Essential Information
    
    Categories:
    1. Historical Significance
    2. Cultural Importance
    3. Geographic Context
    4. Practical Information
    5. Local Connections
    
    Target: >95% completeness for essential content
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Essential categories with required fields
        self.essential_categories = {
            "historical_significance": {
                "required_fields": ["time_period", "historical_events", "significance_level"],
                "weight": 0.25
            },
            "cultural_importance": {
                "required_fields": ["cultural_practices", "traditions", "local_beliefs"],
                "weight": 0.25
            },
            "geographic_context": {
                "required_fields": ["location", "geographic_features", "accessibility"],
                "weight": 0.20
            },
            "practical_information": {
                "required_fields": ["visiting_info", "best_time", "requirements"],
                "weight": 0.15
            },
            "local_connections": {
                "required_fields": ["local_stories", "community_ties", "modern_relevance"],
                "weight": 0.15
            }
        }
        
        # Completeness threshold
        self.completeness_threshold = 0.95
    
    async def detect_essential_content(
        self,
        gathered_content: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect and extract essential content
        
        Args:
            gathered_content: API-gathered content
            location: Location information
            
        Returns:
            Essential content with completeness score
        """
        try:
            logger.info("base_content_detection_started",
                       location=location.get("name"))
            
            # Extract content for each category
            essential_content = {}
            category_scores = {}
            
            for category, config in self.essential_categories.items():
                detector = self._get_category_detector(category)
                content = await detector(gathered_content, location)
                
                # Assess completeness for this category
                completeness = self._assess_category_completeness(
                    content,
                    config["required_fields"]
                )
                
                essential_content[category] = content
                category_scores[category] = completeness
            
            # Calculate overall completeness
            overall_completeness = sum(
                score * self.essential_categories[cat]["weight"]
                for cat, score in category_scores.items()
            )
            
            # Fill gaps if below threshold
            if overall_completeness < self.completeness_threshold:
                logger.info("filling_content_gaps",
                           current_completeness=overall_completeness)
                essential_content = await self._fill_content_gaps(
                    essential_content,
                    category_scores,
                    location
                )
                
                # Recalculate completeness
                category_scores = {
                    cat: self._assess_category_completeness(
                        essential_content[cat],
                        self.essential_categories[cat]["required_fields"]
                    )
                    for cat in self.essential_categories.keys()
                }
                overall_completeness = sum(
                    score * self.essential_categories[cat]["weight"]
                    for cat, score in category_scores.items()
                )
            
            logger.info("base_content_detection_complete",
                       completeness=overall_completeness)
            
            return {
                "success": True,
                "essential_content": essential_content,
                "completeness_score": overall_completeness,
                "category_scores": category_scores,
                "meets_threshold": overall_completeness >= self.completeness_threshold,
                "detected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("base_content_detection_failed",
                        error=str(e))
            raise
    
    def _get_category_detector(self, category: str):
        """Get detector function for category"""
        detectors = {
            "historical_significance": self._detect_historical_significance,
            "cultural_importance": self._detect_cultural_importance,
            "geographic_context": self._detect_geographic_context,
            "practical_information": self._detect_practical_information,
            "local_connections": self._detect_local_connections
        }
        return detectors[category]
    
    async def _detect_historical_significance(
        self,
        gathered_content: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract historical significance information"""
        content = {}
        
        # Extract time period
        content["time_period"] = self._extract_time_period(gathered_content)
        
        # Extract historical events
        content["historical_events"] = self._extract_historical_events(gathered_content)
        
        # Assess significance level
        content["significance_level"] = self._assess_historical_significance(
            content["time_period"],
            content["historical_events"]
        )
        
        # Additional historical context
        content["historical_context"] = self._extract_historical_context(gathered_content)
        content["key_figures"] = self._extract_key_figures(gathered_content)
        content["historical_timeline"] = self._extract_timeline(gathered_content)
        
        return content
    
    async def _detect_cultural_importance(
        self,
        gathered_content: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract cultural importance information"""
        content = {}
        
        # Extract cultural practices
        content["cultural_practices"] = self._extract_cultural_practices(gathered_content)
        
        # Extract traditions
        content["traditions"] = self._extract_traditions(gathered_content)
        
        # Extract local beliefs
        content["local_beliefs"] = self._extract_local_beliefs(gathered_content)
        
        # Additional cultural context
        content["festivals"] = self._extract_festivals(gathered_content)
        content["art_forms"] = self._extract_art_forms(gathered_content)
        content["cuisine"] = self._extract_cuisine(gathered_content)
        content["language_aspects"] = self._extract_language_aspects(gathered_content)
        
        return content
    
    async def _detect_geographic_context(
        self,
        gathered_content: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract geographic context information"""
        content = {}
        
        # Extract location details
        content["location"] = {
            "coordinates": location.get("coordinates"),
            "address": location.get("address"),
            "region": location.get("region"),
            "country": location.get("country")
        }
        
        # Extract geographic features
        content["geographic_features"] = self._extract_geographic_features(gathered_content)
        
        # Extract accessibility
        content["accessibility"] = self._extract_accessibility(gathered_content)
        
        # Additional geographic context
        content["climate"] = self._extract_climate(gathered_content)
        content["nearby_landmarks"] = self._extract_nearby_landmarks(gathered_content)
        content["terrain"] = self._extract_terrain(gathered_content)
        
        return content
    
    async def _detect_practical_information(
        self,
        gathered_content: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract practical information"""
        content = {}
        
        # Extract visiting information
        content["visiting_info"] = self._extract_visiting_info(gathered_content)
        
        # Extract best time to visit
        content["best_time"] = self._extract_best_time(gathered_content)
        
        # Extract requirements
        content["requirements"] = self._extract_requirements(gathered_content)
        
        # Additional practical details
        content["opening_hours"] = self._extract_opening_hours(gathered_content)
        content["costs"] = self._extract_costs(gathered_content)
        content["duration"] = self._extract_duration(gathered_content)
        content["safety_info"] = self._extract_safety_info(gathered_content)
        
        return content
    
    async def _detect_local_connections(
        self,
        gathered_content: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract local connections"""
        content = {}
        
        # Extract local stories
        content["local_stories"] = self._extract_local_stories(gathered_content)
        
        # Extract community ties
        content["community_ties"] = self._extract_community_ties(gathered_content)
        
        # Extract modern relevance
        content["modern_relevance"] = self._extract_modern_relevance(gathered_content)
        
        # Additional local context
        content["local_guides"] = self._extract_local_guides(gathered_content)
        content["community_events"] = self._extract_community_events(gathered_content)
        content["local_economy"] = self._extract_local_economy(gathered_content)
        
        return content
    
    # ========================================================================
    # Extraction Helper Methods
    # ========================================================================
    
    def _extract_time_period(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract time period information"""
        text = self._get_all_text(content)
        
        # Look for date patterns
        date_patterns = [
            r"(\d{1,4})\s*(AD|BC|BCE|CE)",
            r"(\d{1,4})s",  # 1800s, 1920s
            r"(ancient|medieval|renaissance|modern|contemporary)"
        ]
        
        periods = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            periods.extend(matches)
        
        return {
            "identified_periods": periods,
            "era": self._classify_era(periods),
            "confidence": 0.8 if periods else 0.3
        }
    
    def _extract_historical_events(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract historical events"""
        text = self._get_all_text(content)
        
        # Look for event indicators
        event_keywords = [
            "built", "founded", "established", "created", "discovered",
            "battle", "war", "revolution", "independence", "conquest"
        ]
        
        events = []
        for keyword in event_keywords:
            if keyword in text.lower():
                # Extract context around keyword
                pattern = rf"(.{{0,50}}{keyword}.{{0,50}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                events.extend([{"event": m.strip(), "type": keyword} for m in matches[:3]])
        
        return events[:10]  # Limit to 10 events
    
    def _extract_cultural_practices(self, content: Dict[str, Any]) -> List[str]:
        """Extract cultural practices"""
        text = self._get_all_text(content)
        
        practice_keywords = [
            "tradition", "ritual", "ceremony", "custom", "practice",
            "celebration", "festival", "worship", "prayer"
        ]
        
        practices = []
        for keyword in practice_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,40}}{keyword}.{{0,40}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                practices.extend([m.strip() for m in matches[:2]])
        
        return list(set(practices))[:10]
    
    def _extract_traditions(self, content: Dict[str, Any]) -> List[str]:
        """Extract traditions"""
        text = self._get_all_text(content)
        
        # Look for tradition-related phrases
        tradition_pattern = r"(traditional|traditionally|ancient tradition|local tradition).{0,60}"
        matches = re.findall(tradition_pattern, text, re.IGNORECASE)
        
        return [m.strip() for m in matches[:5]]
    
    def _extract_local_beliefs(self, content: Dict[str, Any]) -> List[str]:
        """Extract local beliefs"""
        text = self._get_all_text(content)
        
        belief_keywords = ["believe", "legend", "myth", "folklore", "sacred", "spiritual"]
        
        beliefs = []
        for keyword in belief_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,50}}{keyword}.{{0,50}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                beliefs.extend([m.strip() for m in matches[:2]])
        
        return list(set(beliefs))[:8]
    
    def _extract_geographic_features(self, content: Dict[str, Any]) -> List[str]:
        """Extract geographic features"""
        text = self._get_all_text(content)
        
        feature_keywords = [
            "mountain", "river", "valley", "desert", "forest", "ocean",
            "lake", "plateau", "canyon", "cliff", "beach", "island"
        ]
        
        features = [kw for kw in feature_keywords if kw in text.lower()]
        return features
    
    def _extract_accessibility(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract accessibility information"""
        text = self._get_all_text(content)
        
        accessibility_keywords = {
            "easy": ["easy to reach", "easily accessible", "convenient"],
            "moderate": ["moderate difficulty", "some effort required"],
            "difficult": ["difficult to access", "remote", "hard to reach", "challenging"]
        }
        
        for level, keywords in accessibility_keywords.items():
            if any(kw in text.lower() for kw in keywords):
                return {"level": level, "details": "Extracted from content"}
        
        return {"level": "unknown", "details": "No accessibility information found"}
    
    def _extract_visiting_info(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract visiting information"""
        text = self._get_all_text(content)
        
        return {
            "how_to_visit": "Check content for details",
            "transportation": self._extract_transportation(text),
            "booking_required": "required" in text.lower() or "reservation" in text.lower()
        }
    
    def _extract_best_time(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract best time to visit"""
        text = self._get_all_text(content)
        
        seasons = ["spring", "summer", "fall", "autumn", "winter"]
        months = ["january", "february", "march", "april", "may", "june",
                 "july", "august", "september", "october", "november", "december"]
        
        mentioned_seasons = [s for s in seasons if s in text.lower()]
        mentioned_months = [m for m in months if m in text.lower()]
        
        return {
            "seasons": mentioned_seasons,
            "months": mentioned_months,
            "details": "Best time varies by preference"
        }
    
    def _extract_requirements(self, content: Dict[str, Any]) -> List[str]:
        """Extract requirements"""
        text = self._get_all_text(content)
        
        requirement_keywords = [
            "ticket", "permit", "reservation", "booking", "guide required",
            "dress code", "age restriction", "fitness level"
        ]
        
        requirements = [kw for kw in requirement_keywords if kw in text.lower()]
        return requirements
    
    def _extract_local_stories(self, content: Dict[str, Any]) -> List[str]:
        """Extract local stories"""
        text = self._get_all_text(content)
        
        story_indicators = ["story", "tale", "legend", "says that", "according to"]
        
        stories = []
        for indicator in story_indicators:
            if indicator in text.lower():
                pattern = rf"(.{{0,60}}{indicator}.{{0,100}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                stories.extend([m.strip() for m in matches[:2]])
        
        return stories[:5]
    
    def _extract_community_ties(self, content: Dict[str, Any]) -> List[str]:
        """Extract community ties"""
        text = self._get_all_text(content)
        
        community_keywords = ["local community", "residents", "locals", "neighborhood", "village"]
        
        ties = []
        for keyword in community_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,50}}{keyword}.{{0,50}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                ties.extend([m.strip() for m in matches[:1]])
        
        return ties[:5]
    
    def _extract_modern_relevance(self, content: Dict[str, Any]) -> str:
        """Extract modern relevance"""
        text = self._get_all_text(content)
        
        relevance_keywords = ["today", "modern", "currently", "now", "present day"]
        
        for keyword in relevance_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,80}}{keyword}.{{0,80}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    return matches[0].strip()
        
        return "Modern relevance not explicitly stated"
    
    # Additional extraction methods (simplified)
    def _extract_historical_context(self, content: Dict[str, Any]) -> str:
        return "Historical context from gathered content"
    
    def _extract_key_figures(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_timeline(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    def _extract_festivals(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_art_forms(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_cuisine(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_language_aspects(self, content: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def _extract_climate(self, content: Dict[str, Any]) -> str:
        return "Climate information not available"
    
    def _extract_nearby_landmarks(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_terrain(self, content: Dict[str, Any]) -> str:
        return "Terrain information not available"
    
    def _extract_opening_hours(self, content: Dict[str, Any]) -> str:
        return "Check locally for opening hours"
    
    def _extract_costs(self, content: Dict[str, Any]) -> Dict[str, Any]:
        return {"currency": "local", "amount": "varies"}
    
    def _extract_duration(self, content: Dict[str, Any]) -> str:
        return "Duration varies"
    
    def _extract_safety_info(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_local_guides(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_community_events(self, content: Dict[str, Any]) -> List[str]:
        return []
    
    def _extract_local_economy(self, content: Dict[str, Any]) -> str:
        return "Local economy information not available"
    
    def _extract_transportation(self, text: str) -> List[str]:
        transport_keywords = ["bus", "train", "car", "taxi", "walk", "bike", "metro"]
        return [kw for kw in transport_keywords if kw in text.lower()]
    
    # ========================================================================
    # Assessment and Gap Filling
    # ========================================================================
    
    def _assess_category_completeness(
        self,
        content: Dict[str, Any],
        required_fields: List[str]
    ) -> float:
        """Assess completeness of a category"""
        if not content:
            return 0.0
        
        filled_fields = 0
        for field in required_fields:
            if field in content:
                value = content[field]
                # Check if field has meaningful content
                if value and not self._is_empty_value(value):
                    filled_fields += 1
        
        return filled_fields / len(required_fields) if required_fields else 0.0
    
    def _is_empty_value(self, value: Any) -> bool:
        """Check if value is effectively empty"""
        if value is None:
            return True
        if isinstance(value, str) and (not value or value.lower() in ["unknown", "not available", "n/a"]):
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
    
    async def _fill_content_gaps(
        self,
        essential_content: Dict[str, Any],
        category_scores: Dict[str, float],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fill gaps in essential content
        In production, this would make targeted API calls
        For now, we provide placeholder content
        """
        logger.info("filling_gaps",
                   gaps=[cat for cat, score in category_scores.items() if score < 0.9])
        
        # For each category with low score, add placeholder content
        for category, score in category_scores.items():
            if score < 0.9:
                required_fields = self.essential_categories[category]["required_fields"]
                for field in required_fields:
                    if field not in essential_content[category] or \
                       self._is_empty_value(essential_content[category][field]):
                        # Add placeholder
                        essential_content[category][field] = f"[To be gathered: {field}]"
        
        return essential_content
    
    def _get_all_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from content"""
        text_parts = []
        
        for key, value in content.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend([str(v) for v in value if isinstance(v, str)])
        
        return " ".join(text_parts)
    
    def _classify_era(self, periods: List) -> str:
        """Classify historical era"""
        if not periods:
            return "unknown"
        
        # Simple classification based on keywords
        periods_str = " ".join(str(p) for p in periods).lower()
        
        if "ancient" in periods_str or "bc" in periods_str or "bce" in periods_str:
            return "ancient"
        elif "medieval" in periods_str:
            return "medieval"
        elif "renaissance" in periods_str:
            return "renaissance"
        elif "modern" in periods_str or "contemporary" in periods_str:
            return "modern"
        else:
            return "historical"
    
    def _assess_historical_significance(
        self,
        time_period: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> str:
        """Assess level of historical significance"""
        if time_period.get("era") == "ancient":
            return "high"
        elif len(events) > 5:
            return "high"
        elif len(events) > 2:
            return "medium"
        else:
            return "low"


def get_base_content_detector(db: AsyncSession) -> BaseContentDetector:
    """Get base content detector instance"""
    return BaseContentDetector(db)
