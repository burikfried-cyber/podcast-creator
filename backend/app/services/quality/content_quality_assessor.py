"""
Content Quality Assessor
Multi-dimensional scoring for content quality assessment
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import re
import structlog

logger = structlog.get_logger()


@dataclass
class QualityScore:
    """Quality score with breakdown"""
    overall: float
    source_authority: float
    content_completeness: float
    factual_accuracy: float
    content_freshness: float
    engagement_potential: float
    confidence: float
    details: Dict[str, Any]


class SourceAuthority(Enum):
    """Source authority levels"""
    GOVERNMENT = 1.0
    ACADEMIC = 0.9
    MUSEUM = 0.85
    NEWS_MAJOR = 0.8
    COMMERCIAL = 0.7
    COMMUNITY = 0.5
    UNKNOWN = 0.3


# Source authority mapping
SOURCE_AUTHORITY_MAP = {
    "UNESCO": SourceAuthority.GOVERNMENT,
    "Smithsonian": SourceAuthority.MUSEUM,
    "Europeana": SourceAuthority.MUSEUM,
    "DigitalNZ": SourceAuthority.GOVERNMENT,
    "OpenTripMap": SourceAuthority.COMMUNITY,
    "Nominatim": SourceAuthority.COMMUNITY,
    "Guardian": SourceAuthority.NEWS_MAJOR,
    "BBC": SourceAuthority.NEWS_MAJOR,
}


class ContentQualityAssessor:
    """
    Assesses content quality across multiple dimensions
    
    Scoring dimensions:
    1. Source Authority (25%) - Credibility of the source
    2. Content Completeness (20%) - Presence of required fields
    3. Factual Accuracy (25%) - Cross-source verification
    4. Content Freshness (15%) - Recency of information
    5. Engagement Potential (15%) - Predicted user engagement
    """
    
    def __init__(self):
        self.weights = {
            "source_authority": 0.25,
            "content_completeness": 0.20,
            "factual_accuracy": 0.25,
            "content_freshness": 0.15,
            "engagement_potential": 0.15
        }
    
    async def assess_content_quality(
        self,
        content: Dict[str, Any],
        sources: List[str],
        cross_reference_data: Optional[List[Dict[str, Any]]] = None
    ) -> QualityScore:
        """
        Assess content quality
        
        Args:
            content: Content to assess
            sources: List of source names
            cross_reference_data: Optional data from other sources for verification
            
        Returns:
            QualityScore with detailed breakdown
        """
        # 1. Source Authority
        authority_score = self._assess_source_authority(sources)
        
        # 2. Content Completeness
        completeness_score = self._assess_content_completeness(content)
        
        # 3. Factual Accuracy
        accuracy_score = await self._assess_factual_accuracy(
            content,
            cross_reference_data or []
        )
        
        # 4. Content Freshness
        freshness_score = self._assess_content_freshness(content)
        
        # 5. Engagement Potential
        engagement_score = self._assess_engagement_potential(content)
        
        # Calculate weighted overall score
        overall_score = (
            authority_score * self.weights["source_authority"] +
            completeness_score * self.weights["content_completeness"] +
            accuracy_score * self.weights["factual_accuracy"] +
            freshness_score * self.weights["content_freshness"] +
            engagement_score * self.weights["engagement_potential"]
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            authority_score,
            completeness_score,
            accuracy_score,
            len(sources)
        )
        
        return QualityScore(
            overall=overall_score,
            source_authority=authority_score,
            content_completeness=completeness_score,
            factual_accuracy=accuracy_score,
            content_freshness=freshness_score,
            engagement_potential=engagement_score,
            confidence=confidence,
            details={
                "sources": sources,
                "num_sources": len(sources),
                "has_cross_reference": bool(cross_reference_data)
            }
        )
    
    def _assess_source_authority(self, sources: List[str]) -> float:
        """
        Assess source authority
        
        Args:
            sources: List of source names
            
        Returns:
            Authority score (0.0-1.0)
        """
        if not sources:
            return 0.0
        
        scores = []
        for source in sources:
            authority = SOURCE_AUTHORITY_MAP.get(source, SourceAuthority.UNKNOWN)
            scores.append(authority.value)
        
        # Use highest authority score
        return max(scores)
    
    def _assess_content_completeness(self, content: Dict[str, Any]) -> float:
        """
        Assess content completeness
        
        Args:
            content: Content dictionary
            
        Returns:
            Completeness score (0.0-1.0)
        """
        # Required fields with weights
        required_fields = {
            "title": 0.3,
            "description": 0.3,
            "location": 0.15,
            "date": 0.10,
            "source": 0.05,
            "url": 0.05,
            "type": 0.05
        }
        
        score = 0.0
        
        for field, weight in required_fields.items():
            value = content.get(field)
            
            if value:
                # Check if value is meaningful (not empty string/list)
                if isinstance(value, str) and len(value.strip()) > 0:
                    score += weight
                elif isinstance(value, (list, dict)) and len(value) > 0:
                    score += weight
                elif isinstance(value, (int, float)):
                    score += weight
        
        return min(score, 1.0)
    
    async def _assess_factual_accuracy(
        self,
        content: Dict[str, Any],
        cross_reference_data: List[Dict[str, Any]]
    ) -> float:
        """
        Assess factual accuracy through cross-source verification
        
        Args:
            content: Content to verify
            cross_reference_data: Data from other sources
            
        Returns:
            Accuracy score (0.0-1.0)
        """
        if not cross_reference_data:
            # No cross-reference data, use baseline score
            return 0.7
        
        # Check for consistency across sources
        consistency_checks = []
        
        # Title similarity
        title = content.get("title", "").lower()
        if title:
            title_matches = sum(
                1 for ref in cross_reference_data
                if self._text_similarity(title, ref.get("title", "").lower()) > 0.7
            )
            consistency_checks.append(title_matches / len(cross_reference_data))
        
        # Date consistency
        date = content.get("date")
        if date:
            date_matches = sum(
                1 for ref in cross_reference_data
                if ref.get("date") == date
            )
            consistency_checks.append(date_matches / len(cross_reference_data))
        
        # Location consistency
        location = content.get("location", "").lower()
        if location:
            location_matches = sum(
                1 for ref in cross_reference_data
                if location in ref.get("location", "").lower()
            )
            consistency_checks.append(location_matches / len(cross_reference_data))
        
        if consistency_checks:
            # Average consistency score
            avg_consistency = sum(consistency_checks) / len(consistency_checks)
            # Boost score if multiple sources agree
            return min(0.7 + (avg_consistency * 0.3), 1.0)
        
        return 0.7
    
    def _assess_content_freshness(self, content: Dict[str, Any]) -> float:
        """
        Assess content freshness based on date
        
        Args:
            content: Content dictionary
            
        Returns:
            Freshness score (0.0-1.0)
        """
        # Extract date
        date_str = content.get("date")
        
        if not date_str:
            # No date, assume moderate freshness
            return 0.5
        
        try:
            # Try to parse date
            if isinstance(date_str, str):
                # Extract year from various formats
                year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                if year_match:
                    year = int(year_match.group())
                    current_year = datetime.now().year
                    age = current_year - year
                    
                    # Exponential decay: fresh content scores higher
                    # Score = e^(-age/20)
                    # Recent (0-5 years): 0.78-1.0
                    # Medium (5-20 years): 0.37-0.78
                    # Old (20+ years): <0.37
                    import math
                    score = math.exp(-age / 20)
                    return min(score, 1.0)
            
            return 0.5
            
        except Exception as e:
            logger.debug(f"Failed to parse date: {date_str}, error: {e}")
            return 0.5
    
    def _assess_engagement_potential(self, content: Dict[str, Any]) -> float:
        """
        Assess engagement potential based on content features
        
        Args:
            content: Content dictionary
            
        Returns:
            Engagement score (0.0-1.0)
        """
        score = 0.0
        
        # Has media (images, videos)
        if content.get("thumbnail") or content.get("media"):
            score += 0.3
        
        # Has rich description
        description = content.get("description", "")
        if isinstance(description, str):
            if len(description) > 200:
                score += 0.2
            elif len(description) > 50:
                score += 0.1
        
        # Has interesting keywords
        interesting_keywords = [
            "unique", "rare", "exceptional", "mysterious", "ancient",
            "hidden", "secret", "unusual", "remarkable", "extraordinary"
        ]
        
        text = f"{content.get('title', '')} {description}".lower()
        keyword_matches = sum(1 for keyword in interesting_keywords if keyword in text)
        score += min(keyword_matches * 0.1, 0.3)
        
        # Has specific details (dates, numbers, names)
        if re.search(r'\b\d{4}\b', text):  # Year
            score += 0.1
        if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', content.get('title', '')):  # Proper names
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_confidence(
        self,
        authority: float,
        completeness: float,
        accuracy: float,
        num_sources: int
    ) -> float:
        """
        Calculate confidence in the quality score
        
        Args:
            authority: Authority score
            completeness: Completeness score
            accuracy: Accuracy score
            num_sources: Number of sources
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence from scores
        base_confidence = (authority + completeness + accuracy) / 3
        
        # Boost confidence with multiple sources
        source_boost = min(num_sources * 0.1, 0.3)
        
        return min(base_confidence + source_boost, 1.0)
    
    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """
        Calculate simple text similarity
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


# Global assessor instance
content_quality_assessor = ContentQualityAssessor()
