"""
Content Classification System
Multi-dimensional labeling for content organization
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ContentClassifier:
    """
    Multi-Dimensional Content Classification
    
    Dimensions:
    1. Topic Classification (10 primary + 120 subcategories)
    2. Depth Level Assessment (1-6 scale)
    3. Content Type Identification
    4. Surprise Potential Scoring (1-6 scale)
    5. Cultural Sensitivity Flagging
    6. Source Reliability Scoring
    """
    
    def __init__(self):
        # Topic categories (from Phase 3)
        self.topic_categories = {
            "technology": ["ai", "robotics", "computing", "internet", "innovation"],
            "science": ["physics", "chemistry", "biology", "astronomy", "research"],
            "history": ["ancient", "medieval", "modern", "war", "civilization"],
            "culture": ["traditions", "festivals", "customs", "beliefs", "practices"],
            "arts": ["painting", "sculpture", "music", "literature", "performance"],
            "nature": ["wildlife", "ecosystems", "geology", "climate", "conservation"],
            "architecture": ["buildings", "monuments", "design", "urban", "heritage"],
            "food": ["cuisine", "recipes", "ingredients", "traditions", "restaurants"],
            "sports": ["athletics", "competitions", "teams", "events", "recreation"],
            "business": ["economy", "trade", "industry", "entrepreneurship", "finance"]
        }
        
        # Depth levels
        self.depth_levels = {
            0: "surface",      # Basic facts only
            1: "light",        # Simple explanations
            2: "moderate",     # Detailed information
            3: "detailed",     # In-depth analysis
            4: "deep",         # Expert knowledge
            5: "academic"      # Scholarly depth
        }
        
        # Content types
        self.content_types = [
            "facts",           # Factual information
            "stories",         # Narrative content
            "experiences",     # Personal/visitor experiences
            "explanations",    # How/why explanations
            "mysteries",       # Unexplained phenomena
            "practical",       # Practical information
            "historical",      # Historical accounts
            "cultural"         # Cultural insights
        ]
        
        # Surprise levels (from Phase 3)
        self.surprise_levels = {
            0: "predictable",   # Expected content
            1: "familiar",      # Slightly interesting
            2: "balanced",      # Moderately surprising
            3: "adventurous",   # Quite surprising
            4: "exploratory",   # Very surprising
            5: "radical"        # Extremely surprising
        }
    
    async def classify_content(
        self,
        content: Dict[str, Any],
        standout_results: Optional[Dict[str, Any]] = None,
        base_content_results: Optional[Dict[str, Any]] = None,
        topic_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify content across all dimensions
        
        Args:
            content: Content to classify
            standout_results: Optional standout detection results
            base_content_results: Optional base content detection results
            topic_results: Optional topic-specific detection results
            
        Returns:
            Multi-dimensional classification
        """
        try:
            logger.info("content_classification_started",
                       content_id=content.get("id"))
            
            # Classify topics
            topic_classification = self._classify_topics(content, topic_results)
            
            # Assess depth level
            depth_level = self._assess_depth_level(content, base_content_results)
            
            # Identify content types
            content_types = self._identify_content_types(content)
            
            # Score surprise potential
            surprise_score = self._score_surprise_potential(content, standout_results)
            
            # Flag cultural sensitivity
            cultural_flags = self._flag_cultural_sensitivity(content)
            
            # Score source reliability
            reliability_score = self._score_source_reliability(content)
            
            logger.info("content_classification_complete",
                       content_id=content.get("id"),
                       topics=len(topic_classification["primary_topics"]))
            
            return {
                "success": True,
                "content_id": content.get("id"),
                "topic_classification": topic_classification,
                "depth_level": depth_level,
                "content_types": content_types,
                "surprise_score": surprise_score,
                "cultural_sensitivity": cultural_flags,
                "source_reliability": reliability_score,
                "classified_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("content_classification_failed",
                        content_id=content.get("id"),
                        error=str(e))
            raise
    
    def _classify_topics(
        self,
        content: Dict[str, Any],
        topic_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Classify content into topic categories"""
        text = self._extract_text(content)
        text_lower = text.lower()
        
        # Score each topic category
        topic_scores = {}
        for category, keywords in self.topic_categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[category] = score
        
        # Get top topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        primary_topics = [topic for topic, score in sorted_topics[:3]]
        
        # Use topic results if available
        if topic_results and "topic" in topic_results:
            detected_topic = topic_results["topic"]
            if detected_topic not in primary_topics:
                primary_topics.insert(0, detected_topic)
        
        return {
            "primary_topics": primary_topics[:3],
            "all_topics": list(topic_scores.keys()),
            "topic_scores": topic_scores,
            "confidence": min(sum(topic_scores.values()) / 10.0, 1.0)
        }
    
    def _assess_depth_level(
        self,
        content: Dict[str, Any],
        base_content_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess content depth level"""
        text = self._extract_text(content)
        
        # Indicators for different depth levels
        depth_indicators = {
            5: ["research", "study", "analysis", "methodology", "peer-reviewed", "academic"],
            4: ["detailed", "comprehensive", "in-depth", "expert", "technical"],
            3: ["explains", "describes", "analyzes", "examines", "explores"],
            2: ["information", "details", "about", "includes", "features"],
            1: ["simple", "basic", "introduction", "overview", "brief"],
            0: ["quick", "summary", "facts", "list", "highlights"]
        }
        
        # Score each level
        level_scores = {}
        for level, indicators in depth_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text.lower())
            level_scores[level] = score
        
        # Determine level
        if level_scores:
            assessed_level = max(level_scores.items(), key=lambda x: x[1])[0]
        else:
            assessed_level = 2  # Default to moderate
        
        # Consider text length
        word_count = len(text.split())
        if word_count < 100:
            assessed_level = min(assessed_level, 1)
        elif word_count > 500:
            assessed_level = min(assessed_level + 1, 5)
        
        return {
            "level": assessed_level,
            "level_name": self.depth_levels[assessed_level],
            "word_count": word_count,
            "confidence": 0.7
        }
    
    def _identify_content_types(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Identify content types present"""
        text = self._extract_text(content)
        text_lower = text.lower()
        
        # Type indicators
        type_indicators = {
            "facts": ["fact", "data", "statistic", "number", "measurement"],
            "stories": ["story", "tale", "narrative", "once", "happened"],
            "experiences": ["experience", "visit", "visitor", "traveler", "journey"],
            "explanations": ["because", "why", "how", "reason", "explains"],
            "mysteries": ["mystery", "unknown", "unexplained", "enigma", "puzzle"],
            "practical": ["hours", "cost", "ticket", "access", "how to"],
            "historical": ["history", "historical", "ancient", "past", "century"],
            "cultural": ["culture", "tradition", "custom", "local", "community"]
        }
        
        # Identify present types
        identified_types = []
        type_scores = {}
        
        for content_type, indicators in type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                type_scores[content_type] = score
                identified_types.append(content_type)
        
        # Sort by score
        identified_types.sort(key=lambda t: type_scores.get(t, 0), reverse=True)
        
        return {
            "types": identified_types[:4],  # Top 4 types
            "primary_type": identified_types[0] if identified_types else "facts",
            "type_scores": type_scores
        }
    
    def _score_surprise_potential(
        self,
        content: Dict[str, Any],
        standout_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Score surprise potential (0-5 scale)"""
        # Use standout detection results if available
        if standout_results and "base_score" in standout_results:
            base_score = standout_results["base_score"]
            # Map 0-10 scale to 0-5 scale
            surprise_level = int(min(base_score / 2, 5))
        else:
            # Fallback: analyze text
            text = self._extract_text(content)
            text_lower = text.lower()
            
            surprise_keywords = [
                "unique", "rare", "unusual", "extraordinary", "remarkable",
                "surprising", "unexpected", "incredible", "amazing", "astonishing"
            ]
            
            surprise_count = sum(1 for keyword in surprise_keywords if keyword in text_lower)
            surprise_level = min(surprise_count, 5)
        
        return {
            "level": surprise_level,
            "level_name": self.surprise_levels[surprise_level],
            "confidence": 0.8 if standout_results else 0.5
        }
    
    def _flag_cultural_sensitivity(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Flag cultural sensitivity concerns"""
        text = self._extract_text(content)
        text_lower = text.lower()
        
        # Sensitivity indicators
        sensitivity_categories = {
            "religious": ["religion", "religious", "sacred", "holy", "worship", "prayer"],
            "political": ["political", "government", "conflict", "war", "controversial"],
            "social": ["taboo", "sensitive", "private", "restricted", "forbidden"],
            "cultural": ["tradition", "custom", "belief", "cultural", "indigenous"]
        }
        
        flags = []
        for category, indicators in sensitivity_categories.items():
            if any(indicator in text_lower for indicator in indicators):
                flags.append(category)
        
        return {
            "has_sensitivity": len(flags) > 0,
            "categories": flags,
            "requires_review": len(flags) >= 2,
            "notes": "Content may require cultural sensitivity review" if flags else "No sensitivity concerns detected"
        }
    
    def _score_source_reliability(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Score source reliability"""
        # Check for source information
        has_source = "source" in content or "sources" in content
        has_references = "references" in content or "citations" in content
        has_author = "author" in content or "contributor" in content
        
        # Calculate reliability score (0-1)
        reliability = 0.5  # Base score
        
        if has_source:
            reliability += 0.2
        if has_references:
            reliability += 0.2
        if has_author:
            reliability += 0.1
        
        # Check for verification indicators
        text = self._extract_text(content)
        text_lower = text.lower()
        
        verification_keywords = ["verified", "confirmed", "documented", "official", "authenticated"]
        if any(keyword in text_lower for keyword in verification_keywords):
            reliability += 0.1
        
        reliability = min(reliability, 1.0)
        
        return {
            "score": reliability,
            "level": self._reliability_level(reliability),
            "has_source": has_source,
            "has_references": has_references,
            "has_author": has_author
        }
    
    def _reliability_level(self, score: float) -> str:
        """Convert reliability score to level"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _extract_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from content"""
        text_parts = []
        
        for key, value in content.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend([str(v) for v in value if isinstance(v, str)])
        
        return " ".join(text_parts)


def get_content_classifier() -> ContentClassifier:
    """Get content classifier instance"""
    return ContentClassifier()
