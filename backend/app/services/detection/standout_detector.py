"""
Enhanced Standout Content Detector
Preserves existing 9-method detection system with API integration and personalization
Target: Maintain 80% Tier 1 accuracy
"""
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.preferences import get_preference_model

logger = structlog.get_logger()


class EnhancedStandoutDetector:
    """
    Enhanced Standout Content Detection
    
    Preserves 9 existing detection methods:
    1. Impossibility Detection
    2. Uniqueness Verification
    3. Temporal Analysis
    4. Cultural Anomaly
    5. Atlas Obscura Style
    6. Historical Peculiarity
    7. Geographic Rarity
    8. Linguistic Anomaly
    9. Cross-Cultural Rarity
    
    Enhanced with:
    - API-gathered context integration
    - User personalization (surprise tolerance)
    - Cross-source verification
    - Quality scoring
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.preference_model = get_preference_model(db)
        
        # Detection method weights (scaled by 3.5x based on 40-item test data)
        # Original weights were too conservative (summed to 1.0)
        # Data showed consistent 3.5x gap across all tiers
        self.method_weights = {
            "impossibility": 0.525,     # was 0.15 × 3.5
            "uniqueness": 0.525,        # was 0.15 × 3.5
            "temporal": 0.35,           # was 0.10 × 3.5
            "cultural": 0.42,           # was 0.12 × 3.5
            "atlas_obscura": 0.455,     # was 0.13 × 3.5
            "historical": 0.35,         # was 0.10 × 3.5
            "geographic": 0.28,         # was 0.08 × 3.5
            "linguistic": 0.315,        # was 0.09 × 3.5
            "cross_cultural": 0.28      # was 0.08 × 3.5
        }
        # New total: 3.5 (350%) - data-driven scaling
        
        # Score multipliers (from old system - CRITICAL for accuracy!)
        self.score_multipliers = {
            'linguistic': 1.5,
            'atlas_obscura': 1.0,
            'cultural': 3.0,        # 3x boost!
            'historical': 3.0,      # 3x boost!
            'cross_cultural': 1.0,
            'impossibility': 2.5,   # 2.5x boost!
            'uniqueness': 2.0,      # 2x boost!
            'temporal': 1.8,        # 1.8x boost!
            'geographic': 2.0       # 2x boost!
        }
        
        # Tier thresholds (data-driven from old system testing)
        self.tier_thresholds = {
            "exceptional": 5.0,  # Tier 1 (was 9.0 - too high!)
            "very_good": 3.8,    # Tier 2 (was 7.5 - too high!)
            "good": 2.3,         # Tier 3 (was 6.0 - too high!)
            "average": 1.5       # Tier 4 (was 4.0 - too high!)
        }
        
        # Method-specific thresholds (calibrated per method)
        self.method_thresholds = {
            'linguistic': 1.5,
            'atlas_obscura': 3.0,
            'cultural': 2.0,
            'historical': 1.5,
            'cross_cultural': 5.0,
            'impossibility': 2.5,
            'uniqueness': 3.0,
            'temporal': 2.5,
            'geographic': 2.0
        }
        
        # Impossibility keywords
        self.impossibility_keywords = [
            "impossible", "defies", "violates", "contradicts", "shouldn't exist",
            "physics-defying", "logically impossible", "temporal impossibility",
            "architectural impossibility", "confounds", "baffles", "unexplained"
        ]
        
        # Uniqueness keywords
        self.uniqueness_keywords = [
            "only place", "nowhere else", "unique in the world", "singular",
            "one of a kind", "unparalleled", "unprecedented", "sole example",
            "exclusively", "uniquely"
        ]
        
        # Temporal anomaly keywords
        self.temporal_keywords = [
            "anachronism", "before its time", "ahead of", "ancient technology",
            "impossible knowledge", "timeline contradiction", "shouldn't have known"
        ]
    
    async def detect_standout_content(
        self,
        content: Dict[str, Any],
        user_id: Optional[str] = None,
        api_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect standout content with personalization
        
        Args:
            content: Content to analyze
            user_id: Optional user ID for personalization
            api_context: Optional API-gathered context
            
        Returns:
            Detection results with scores and tier
        """
        try:
            logger.info("standout_detection_started",
                       content_id=content.get("id"),
                       user_id=user_id)
            
            # Apply all 9 detection methods
            method_scores = await self._apply_all_methods(content, api_context)
            
            # Calculate weighted total score
            total_score = sum(
                score * self.method_weights[method]
                for method, score in method_scores.items()
            )
            
            # LAYER 3: Apply synergy and diversity bonuses (from old system)
            total_score = self._apply_synergy_and_diversity_bonuses(total_score, method_scores)
            
            # Determine tier
            tier = self._determine_tier(total_score)
            
            # Apply personalization if user provided
            if user_id:
                personalized_score, personalized_tier = await self._personalize_detection(
                    user_id,
                    total_score,
                    tier,
                    method_scores
                )
            else:
                personalized_score = total_score
                personalized_tier = tier
            
            # Generate explanation
            explanation = self._generate_explanation(method_scores, tier)
            
            logger.info("standout_detection_complete",
                       content_id=content.get("id"),
                       score=total_score,
                       tier=tier)
            
            return {
                "success": True,
                "content_id": content.get("id"),
                "base_score": total_score,
                "personalized_score": personalized_score,
                "tier": tier,
                "personalized_tier": personalized_tier,
                "method_scores": method_scores,
                "explanation": explanation,
                "detected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("standout_detection_failed",
                        content_id=content.get("id"),
                        error=str(e))
            raise
    
    async def _apply_all_methods(
        self,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Apply all 9 detection methods with score multipliers and bonuses"""
        
        text = self._extract_text(content)
        
        # Get base scores from all methods
        base_scores = {
            "impossibility": self._detect_impossibility(text, content, api_context),
            "uniqueness": self._verify_uniqueness(text, content, api_context),
            "temporal": self._analyze_temporal(text, content, api_context),
            "cultural": self._detect_cultural_anomaly(text, content, api_context),
            "atlas_obscura": self._detect_atlas_obscura_style(text, content, api_context),
            "historical": self._detect_historical_peculiarity(text, content, api_context),
            "geographic": self._detect_geographic_rarity(text, content, api_context),
            "linguistic": self._detect_linguistic_anomaly(text, content),
            "cross_cultural": self._analyze_cross_cultural_rarity(text, content, api_context)
        }
        
        # Apply score multipliers (CRITICAL for accuracy!)
        multiplied_scores = {}
        for method, base_score in base_scores.items():
            multiplier = self.score_multipliers.get(method, 1.0)
            multiplied_scores[method] = min(base_score * multiplier, 10.0)
        
        # LAYER 1: Apply exceptional multiplier (from old system - Quick Win 2)
        multiplied_scores = self._apply_exceptional_multiplier(multiplied_scores, text)
        
        # LAYER 2: Apply cross-method validation bonus (from old system - Quick Win 4)
        multiplied_scores = self._apply_cross_method_validation(multiplied_scores)
        
        return multiplied_scores
    
    def _detect_impossibility(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 1: Impossibility Detection
        Identifies physics-defying, logical contradictions, temporal impossibilities
        """
        score = 0.0
        text_lower = text.lower()
        
        # Keyword matching (40%)
        keyword_count = sum(1 for keyword in self.impossibility_keywords if keyword in text_lower)
        keyword_score = min(keyword_count * 1.5, 4.0)
        
        # Physics violations (30%)
        physics_patterns = [
            r"defies (physics|gravity|laws)",
            r"violates (known|physical) laws",
            r"shouldn't (exist|be possible)",
            r"impossible (construction|architecture|feat)"
        ]
        physics_score = sum(2.0 for pattern in physics_patterns if re.search(pattern, text_lower))
        physics_score = min(physics_score, 3.0)
        
        # Logical contradictions (20%)
        contradiction_patterns = [
            r"(ancient|old) (technology|knowledge) (that|which) shouldn't",
            r"(built|created|made) (before|without) (tools|technology)",
            r"(animals|creatures) (that|which) (defy|violate)"
        ]
        contradiction_score = sum(1.5 for pattern in contradiction_patterns if re.search(pattern, text_lower))
        contradiction_score = min(contradiction_score, 2.0)
        
        # API context enhancement (10%)
        api_boost = 0.0
        if api_context and "impossibility_indicators" in api_context:
            api_boost = min(len(api_context["impossibility_indicators"]) * 0.5, 1.0)
        
        score = keyword_score + physics_score + contradiction_score + api_boost
        
        return min(score, 10.0)
    
    def _verify_uniqueness(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 2: Uniqueness Verification
        Verifies 'only place in world' and similar uniqueness claims
        """
        score = 0.0
        text_lower = text.lower()
        
        # Uniqueness claims (50%)
        uniqueness_count = sum(1 for keyword in self.uniqueness_keywords if keyword in text_lower)
        uniqueness_score = min(uniqueness_count * 2.0, 5.0)
        
        # Superlative language (30%)
        superlatives = [
            r"(first|last|only) (place|location|site|example)",
            r"(most|least) (unusual|unique|rare|extraordinary)",
            r"(never|nowhere) (else|before) (seen|found|discovered)"
        ]
        superlative_score = sum(1.5 for pattern in superlatives if re.search(pattern, text_lower))
        superlative_score = min(superlative_score, 3.0)
        
        # API verification (20%)
        verification_boost = 0.0
        if api_context and "uniqueness_verified" in api_context:
            if api_context["uniqueness_verified"]:
                verification_boost = 2.0
        
        score = uniqueness_score + superlative_score + verification_boost
        
        return min(score, 10.0)
    
    def _analyze_temporal(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 3: Temporal Analysis
        Detects anachronisms and timeline contradictions
        """
        score = 0.0
        text_lower = text.lower()
        
        # Temporal keywords (40%)
        temporal_count = sum(1 for keyword in self.temporal_keywords if keyword in text_lower)
        temporal_score = min(temporal_count * 1.5, 4.0)
        
        # Anachronism patterns (40%)
        anachronism_patterns = [
            r"(ancient|medieval|old) (technology|knowledge|technique) (that|which)",
            r"(before|without) (modern|contemporary) (tools|methods|technology)",
            r"(shouldn't|couldn't) have (known|built|created|understood)"
        ]
        anachronism_score = sum(1.5 for pattern in anachronism_patterns if re.search(pattern, text_lower))
        anachronism_score = min(anachronism_score, 4.0)
        
        # Historical dates (20%)
        date_patterns = r"\b(\d{1,4})\s*(AD|BC|BCE|CE)\b"
        dates = re.findall(date_patterns, text)
        if dates:
            # Ancient dates get higher scores
            oldest_year = min(int(d[0]) for d in dates if d[0].isdigit())
            if oldest_year < 500:
                score += 2.0
            elif oldest_year < 1500:
                score += 1.0
        
        score += temporal_score + anachronism_score
        
        return min(score, 10.0)
    
    def _detect_cultural_anomaly(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 4: Cultural Anomaly Detection
        Identifies unusual cultural practices and legal impossibilities
        """
        score = 0.0
        
        # 1. Legal Impossibilities (30% weight) - REGEX PATTERNS
        legal_patterns = [
            r"\b(illegal|forbidden|banned|prohibited|law|legal|legislation)\b.{0,50}\b(to|from|against)\b.{0,50}\b(die|death|dying|be born|marry|divorce)\b",
            r"\b(required|mandated|must|law requires|legally required)\b.{0,50}\b(to|must)\b.{0,50}\b(unusual|strange|unique|odd)\b",
            r"\b(only place|only country|only location)\b.{0,50}\b(where|that|with)\b.{0,50}\b(law|legal|illegal)\b",
        ]
        legal_score = sum(2.5 for pattern in legal_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        legal_score = min(legal_score, 3.0)
        
        # 2. Cultural Isolation (25% weight) - REGEX PATTERNS
        isolation_patterns = [
            r"\b(isolated|remote|uncontacted|undiscovered|hidden)\b.{0,50}\b(tribe|people|community|village|culture)\b",
            r"\b(unique to|only in|exclusively|solely|nowhere else)\b.{0,50}\b(this|location|place|region)\b",
            r"\b(preserved|maintained|survived)\b.{0,50}\b(for|over|since)\b.{0,50}\b(\d+)\s*(centuries|years|millennia)\b",
            r"\b(no contact|isolated from|cut off from)\b.{0,50}\b(outside world|modern|civilization)\b",
        ]
        isolation_score = sum(2.0 for pattern in isolation_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        isolation_score = min(isolation_score, 2.5)
        
        # 3. Temporal Cultural Anomalies (20% weight) - REGEX PATTERNS
        temporal_patterns = [
            r"\b(ancient|old|traditional|ancestral)\b.{0,50}\b(practice|custom|tradition|ritual)\b.{0,50}\b(still|continues|persists|survives)\b",
            r"\b(survived|preserved|maintained)\b.{0,50}\b(despite|through|against)\b.{0,50}\b(modernization|globalization|change)\b",
            r"\b(unchanged|unaltered|same)\b.{0,50}\b(for|over|since)\b.{0,50}\b(\d+)\s*(centuries|years)\b",
        ]
        temporal_score = sum(1.5 for pattern in temporal_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        temporal_score = min(temporal_score, 2.0)
        
        # 4. Cultural Contradictions (15% weight) - REGEX PATTERNS
        contradiction_patterns = [
            r"\b(despite|although|even though|in spite of)\b.{0,50}\b(modern|contemporary|current)\b.{0,50}\b(still|continues|maintains)\b",
            r"\b(shouldn't|couldn't|impossible)\b.{0,50}\b(exist|survive|persist|continue)\b.{0,50}\b(but|yet|however)\b",
            r"\b(contradicts|defies|challenges|opposes)\b.{0,50}\b(logic|reason|expectations|norms)\b",
        ]
        contradiction_score = sum(1.5 for pattern in contradiction_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        contradiction_score = min(contradiction_score, 1.5)
        
        # 5. Unique Practices (10% weight) - REGEX PATTERNS
        unique_patterns = [
            r"\b(only place|only culture|only people)\b.{0,50}\b(where|who|that)\b.{0,50}\b(practice|perform|do|use)\b",
            r"\b(unique|distinctive|peculiar|singular)\b.{0,50}\b(practice|custom|tradition|ritual|ceremony)\b",
            r"\b(found nowhere else|exists nowhere else|unique to)\b",
        ]
        unique_score = sum(1.0 for pattern in unique_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        unique_score = min(unique_score, 1.0)
        
        # Calculate total score
        score = legal_score + isolation_score + temporal_score + contradiction_score + unique_score
        
        return min(score, 10.0)
    
    def _detect_atlas_obscura_style(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 5: Atlas Obscura Style Detection
        Enhanced with regex patterns from old system
        """
        score = 0.0
        
        # CRITICAL: Mundane content penalty (from old system)
        mundane_patterns = [
            r"\b(shopping|shop|store|retail|mall|boutique)\b",
            r"\b(tourist|tourism|visitor|sightseeing)\b.{0,50}\b(attraction|destination)\b",
            r"\b(hotel|restaurant|café|bar|nightlife)\b(?!.{0,100}(secret|hidden|unique|only))",
            r"\b(popular|famous|well-known)\b.{0,50}\b(attraction|destination|spot)\b",
        ]
        mundane_penalty = sum(1 for pattern in mundane_patterns if re.search(pattern, text, re.IGNORECASE))
        if mundane_penalty > 2:
            return min(2.0, 3.0 * (1.0 - mundane_penalty / 5.0))
        
        # 1. Impossibility Detection (35% weight) - REGEX PATTERNS
        impossibility_patterns = [
            r"\b(defies|contradicts|violates|breaks)\b.{0,50}\b(physics|gravity|laws|science)\b",
            r"\b(impossible|shouldn't exist|couldn't exist|can't exist)\b",
            r"\b(confounds|confounding|baffles|baffling|puzzles|puzzling)\b.{0,50}\b(scientists|experts|researchers)\b",
            r"\b(supernatural|paranormal|magical|mystical|enchanted)\b",
            r"\b(ghost|spirit|demon|djinn|genie)\b.{0,50}\b(built|created|made|constructed)\b",
        ]
        impossibility_score = sum(2.0 for pattern in impossibility_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        impossibility_score = min(impossibility_score, 3.5)
        
        # 2. Mystery Elements (25% weight) - REGEX PATTERNS
        mystery_patterns = [
            r"\b(mystery|mysterious|enigma|enigmatic|puzzle|puzzling)\b",
            r"\b(unexplained|unknown|unclear|uncertain)\b.{0,50}\b(how|why|what|who)\b",
            r"\b(scientists|experts|researchers)\b.{0,50}\b(baffled|puzzled|can't explain|don't understand)\b",
            r"\b(no one knows|nobody knows|remains unknown)\b",
            r"\b(secret|hidden|concealed|classified)\b.{0,50}\b(room|chamber|passage|tunnel|vault)\b",
        ]
        mystery_score = sum(1.5 for pattern in mystery_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        mystery_score = min(mystery_score, 2.5)
        
        # 3. Uniqueness (20% weight) - REGEX PATTERNS
        uniqueness_patterns = [
            r"\b(only place|only location|only spot)\b.{0,50}\b(in (?:the )?world|on earth)\b",
            r"\b(nowhere else|found nowhere else|exists nowhere else)\b",
            r"\b(one of a kind|one and only|singular|unique)\b",
            r"\b(rarest|most unusual|most unique|most mysterious)\b",
            r"\b(etymological source|named after this|all .{0,30} named (?:after|from))\b",
        ]
        uniqueness_score = sum(2.0 for pattern in uniqueness_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        uniqueness_score = min(uniqueness_score, 2.0)
        
        # 4. Architectural Oddities (20% weight) - REGEX PATTERNS
        architectural_patterns = [
            r"\b(upside down|inverted|backwards|reversed)\b.{0,50}\b(house|building|structure)\b",
            r"\b(staircase|stairs|door|window)\b.{0,50}\b(to nowhere|leading nowhere|that goes nowhere)\b",
            r"\b(impossible|defying|gravity-defying)\b.{0,50}\b(architecture|construction|design)\b",
        ]
        architectural_score = sum(1.5 for pattern in architectural_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        architectural_score = min(architectural_score, 2.0)
        
        # Calculate weighted score
        score = impossibility_score + mystery_score + uniqueness_score + architectural_score
        
        # Apply mundane penalty
        if mundane_penalty > 0:
            score *= (1.0 - mundane_penalty * 0.15)
        
        return min(score, 10.0)
    
    def _detect_historical_peculiarity(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 6: Historical Peculiarity Detection
        Enhanced with regex patterns from old system
        """
        score = 0.0
        
        # 1. Archaeological Impossibilities (35% weight) - REGEX PATTERNS
        impossibility_patterns = [
            r"\b(built|constructed|created)\b.{0,50}\b(without|before)\b.{0,50}\b(modern|known|any)\b.{0,50}\b(tools|technology|methods)\b",
            r"\b(ancient|old|prehistoric)\b.{0,50}\b(construction|architecture|engineering|knowledge)\b.{0,50}\b(that|which)\b.{0,50}\b(defies|baffles|confounds)\b",
            r"\b(shouldn't|couldn't|impossible)\b.{0,50}\b(have)\b.{0,50}\b(built|known|created|existed)\b",
            r"\b(predates|older than|before)\b.{0,50}\b(recorded|documented|known)\b.{0,50}\b(history|civilization|writing)\b",
        ]
        impossibility_score = sum(2.5 for pattern in impossibility_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        impossibility_score = min(impossibility_score, 3.5)
        
        # 2. Historical Mysteries (30% weight) - REGEX PATTERNS
        mystery_patterns = [
            r"\b(mystery|mysterious|enigma|enigmatic)\b.{0,50}\b(origin|purpose|construction|builder|creator)\b",
            r"\b(unexplained|unknown|unclear)\b.{0,50}\b(how|why|who|when)\b.{0,50}\b(built|created|made|constructed)\b",
            r"\b(no one knows|nobody knows|remains unknown|lost to history)\b",
            r"\b(historians|archaeologists|experts)\b.{0,50}\b(baffled|puzzled|uncertain|disagree)\b",
        ]
        mystery_score = sum(2.0 for pattern in mystery_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        mystery_score = min(mystery_score, 3.0)
        
        # 3. Temporal Depth (20% weight) - REGEX PATTERNS
        temporal_patterns = [
            r"\b(\d+)\s*(thousand|million)\b.{0,50}\b(years|year)\b.{0,50}\b(old|ago|ancient)\b",
            r"\b(prehistoric|paleolithic|neolithic|bronze age|iron age)\b",
            r"\b(millennia|millennium|centuries|eons)\b.{0,50}\b(old|ago|ancient)\b",
        ]
        temporal_score = sum(1.5 for pattern in temporal_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        temporal_score = min(temporal_score, 2.0)
        
        # 4. Documentation Gaps (15% weight) - REGEX PATTERNS
        gap_patterns = [
            r"\b(no records|no documentation|undocumented|unrecorded)\b",
            r"\b(lost|forgotten|disappeared)\b.{0,50}\b(knowledge|technique|method|civilization)\b",
            r"\b(rediscovered|recently found|newly discovered)\b.{0,50}\b(after|following)\b.{0,50}\b(centuries|years)\b",
        ]
        gap_score = sum(1.0 for pattern in gap_patterns if re.search(pattern, text, re.IGNORECASE | re.DOTALL))
        gap_score = min(gap_score, 1.5)
        
        # Calculate total score
        score = impossibility_score + mystery_score + temporal_score + gap_score
        
        return min(score, 10.0)
    
    def _detect_geographic_rarity(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 7: Geographic Rarity Detection
        Identifies geographically unique or rare phenomena
        """
        score = 0.0
        text_lower = text.lower()
        
        # Geographic uniqueness (50%)
        geographic_keywords = [
            "only place", "nowhere else", "unique location", "sole site",
            "exclusively found", "endemic to", "found only in"
        ]
        geographic_count = sum(1 for keyword in geographic_keywords if keyword in text_lower)
        geographic_score = min(geographic_count * 1.5, 5.0)
        
        # Natural phenomena (30%)
        phenomena_keywords = [
            "geological", "natural wonder", "phenomenon", "formation",
            "unique ecosystem", "rare species", "endemic"
        ]
        phenomena_count = sum(1 for keyword in phenomena_keywords if keyword in text_lower)
        phenomena_score = min(phenomena_count * 0.8, 3.0)
        
        # Extreme geography (20%)
        extreme_keywords = ["extreme", "highest", "lowest", "deepest", "remotest", "isolated"]
        extreme_count = sum(1 for keyword in extreme_keywords if keyword in text_lower)
        extreme_score = min(extreme_count * 0.7, 2.0)
        
        score = geographic_score + phenomena_score + extreme_score
        
        return min(score, 10.0)
    
    def _detect_linguistic_anomaly(
        self,
        text: str,
        content: Dict[str, Any]
    ) -> float:
        """
        Method 8: Linguistic Anomaly Detection
        Identifies unusual language patterns and semantic surprises
        """
        score = 0.0
        text_lower = text.lower()
        
        # Semantic surprise (40%)
        # Look for unexpected word combinations
        surprising_combinations = [
            r"(animals|birds|creatures) (that|which) (vote|govern|decide)",
            r"(fish|cod|seafood) (duel|combat|fight)",
            r"(phone book|directory) (song|music|melody)",
            r"(sheep|livestock) (predict|forecast|warn)"
        ]
        surprise_score = sum(1.5 for pattern in surprising_combinations if re.search(pattern, text_lower))
        surprise_score = min(surprise_score, 4.0)
        
        # Alliteration and unusual syntax (30%)
        words = text_lower.split()
        if len(words) > 5:
            # Check for alliteration
            first_letters = [w[0] for w in words if len(w) > 3]
            if len(first_letters) > 0:
                most_common = max(set(first_letters), key=first_letters.count)
                alliteration_count = first_letters.count(most_common)
                if alliteration_count >= 3:
                    score += 3.0
        
        # Mystery language (20%)
        mystery_terms = ["supernatural", "magical", "mystical", "paranormal", "otherworldly"]
        mystery_count = sum(1 for term in mystery_terms if term in text_lower)
        mystery_score = min(mystery_count * 0.7, 2.0)
        
        # Archaic language (10%)
        archaic_terms = ["ancient", "olden", "bygone", "antiquated", "archaic"]
        archaic_count = sum(1 for term in archaic_terms if term in text_lower)
        archaic_score = min(archaic_count * 0.3, 1.0)
        
        score += surprise_score + mystery_score + archaic_score
        
        return min(score, 10.0)
    
    def _analyze_cross_cultural_rarity(
        self,
        text: str,
        content: Dict[str, Any],
        api_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Method 9: Cross-Cultural Rarity Analysis
        Identifies practices unique across cultures
        """
        score = 0.0
        text_lower = text.lower()
        
        # Global uniqueness (40%)
        global_keywords = [
            "only culture", "unique tradition", "nowhere else practiced",
            "sole example", "exclusively", "unparalleled tradition"
        ]
        global_count = sum(1 for keyword in global_keywords if keyword in text_lower)
        global_score = min(global_count * 1.5, 4.0)
        
        # Cultural diffusion (30%)
        diffusion_keywords = [
            "spread from", "originated in", "adopted by", "influenced",
            "cultural exchange", "diffusion", "transmission"
        ]
        diffusion_count = sum(1 for keyword in diffusion_keywords if keyword in text_lower)
        diffusion_score = min(diffusion_count * 1.0, 3.0)
        
        # Preservation uniqueness (20%)
        preservation_keywords = [
            "last remaining", "only surviving", "preserved tradition",
            "unchanged since", "maintained for centuries"
        ]
        preservation_count = sum(1 for keyword in preservation_keywords if keyword in text_lower)
        preservation_score = min(preservation_count * 0.8, 2.0)
        
        # Origin mystery (10%)
        origin_keywords = ["unknown origin", "mysterious beginning", "unclear how started"]
        origin_count = sum(1 for keyword in origin_keywords if keyword in text_lower)
        origin_score = min(origin_count * 0.5, 1.0)
        
        score = global_score + diffusion_score + preservation_score + origin_score
        
        # Anti-mundane filter
        mundane_keywords = ["restaurant", "hotel", "shopping", "common", "typical"]
        if any(keyword in text_lower for keyword in mundane_keywords):
            score *= 0.4
        
        return min(score, 10.0)
    
    def _extract_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from content for analysis"""
        text_parts = []
        
        if "title" in content:
            text_parts.append(content["title"])
        if "description" in content:
            text_parts.append(content["description"])
        if "content" in content:
            text_parts.append(content["content"])
        if "summary" in content:
            text_parts.append(content["summary"])
        
        return " ".join(text_parts)
    
    def _determine_tier(self, score: float) -> str:
        """Determine content tier based on score"""
        if score >= self.tier_thresholds["exceptional"]:
            return "exceptional"  # Tier 1
        elif score >= self.tier_thresholds["very_good"]:
            return "very_good"  # Tier 2
        elif score >= self.tier_thresholds["good"]:
            return "good"  # Tier 3
        elif score >= self.tier_thresholds["average"]:
            return "average"  # Tier 4
        else:
            return "below_average"
    
    async def _personalize_detection(
        self,
        user_id: str,
        base_score: float,
        tier: str,
        method_scores: Dict[str, float]
    ) -> Tuple[float, str]:
        """
        Personalize detection based on user surprise tolerance
        
        Args:
            user_id: User ID
            base_score: Base detection score
            tier: Base tier
            method_scores: Individual method scores
            
        Returns:
            Tuple of (personalized_score, personalized_tier)
        """
        try:
            # Get user surprise preference
            surprise_pref = await self.preference_model.get_surprise_preference(user_id)
            
            if not surprise_pref:
                return base_score, tier
            
            surprise_tolerance = surprise_pref.get("surprise_tolerance", 2)  # 0-5 scale
            
            # Adjust score based on surprise tolerance
            # Higher tolerance = boost standout content more
            # Lower tolerance = reduce standout content boost
            
            if surprise_tolerance >= 3:  # Adventurous/Exploratory/Radical
                # Boost exceptional content more, other content less
                if tier == "exceptional":
                    personalized_score = min(base_score * 1.2, 10.0)
                else:
                    personalized_score = min(base_score * 1.1, 10.0)
            elif surprise_tolerance <= 1:  # Predictable/Familiar
                # Reduce standout scores (prefer more normal content)
                personalized_score = base_score * 0.8
            else:  # Balanced (surprise_tolerance == 2)
                personalized_score = base_score
            
            # Recalculate tier
            personalized_tier = self._determine_tier(personalized_score)
            
            return personalized_score, personalized_tier
            
        except Exception as e:
            logger.error("personalization_failed",
                        user_id=user_id,
                        error=str(e))
            return base_score, tier
    
    def _generate_explanation(
        self,
        method_scores: Dict[str, float],
        tier: str
    ) -> str:
        """Generate human-readable explanation"""
        # Find top 3 methods
        top_methods = sorted(
            method_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        method_names = {
            "impossibility": "impossibility/physics-defying elements",
            "uniqueness": "verified uniqueness",
            "temporal": "temporal anomalies",
            "cultural": "cultural anomalies",
            "atlas_obscura": "mysterious/obscure qualities",
            "historical": "historical peculiarities",
            "geographic": "geographic rarity",
            "linguistic": "linguistic anomalies",
            "cross_cultural": "cross-cultural rarity"
        }
        
        explanations = [
            f"{method_names.get(method, method)} ({score:.1f})"
            for method, score in top_methods if score > 0
        ]
        
        if explanations:
            return f"Tier {tier.upper()}: Strong signals in {', '.join(explanations)}"
        else:
            return f"Tier {tier.upper()}: Standard content"
    
    def _apply_exceptional_multiplier(
        self,
        method_scores: Dict[str, float],
        text: str
    ) -> Dict[str, float]:
        """
        Quick Win 2 from old system: Apply multiplier for content with multiple strong signals.
        """
        text_lower = text.lower()
        
        # Count strong signals
        strong_signals = 0
        
        # 1. Impossibility
        if any(word in text_lower for word in ['impossible', 'defies', 'contradicts', "shouldn't exist"]):
            strong_signals += 1
        
        # 2. Uniqueness
        if any(phrase in text_lower for phrase in ['only place', 'nowhere else', 'one of a kind', 'only in the world']):
            strong_signals += 1
        
        # 3. Mystery
        if any(word in text_lower for word in ['mystery', 'unexplained', 'unknown', 'baffling', 'no one knows']):
            strong_signals += 1
        
        # 4. Supernatural
        if any(word in text_lower for word in ['supernatural', 'magical', 'djinn', 'spirit', 'ghost', 'cursed']):
            strong_signals += 1
        
        # 5. Temporal anomaly
        if any(phrase in text_lower for phrase in ['ancient but', 'before it was', 'predates', 'anachronism']):
            strong_signals += 1
        
        # Apply multiplier based on signal count
        if strong_signals >= 4:
            multiplier = 1.5  # 50% boost for 4+ signals
        elif strong_signals >= 3:
            multiplier = 1.3  # 30% boost for 3 signals
        else:
            multiplier = 1.0  # No boost
        
        # Apply multiplier to all scores
        if multiplier > 1.0:
            boosted_scores = {
                method: min(score * multiplier, 10.0)
                for method, score in method_scores.items()
            }
            return boosted_scores
        
        return method_scores
    
    def _apply_cross_method_validation(
        self,
        method_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Quick Win 4 from old system: Apply agreement bonus when methods agree.
        """
        # Count methods that exceed their thresholds
        active_methods = sum(
            1 for method, score in method_scores.items()
            if score >= self.method_thresholds.get(method, 2.0)
        )
        
        # Apply agreement bonus
        if active_methods >= 3:
            multiplier = 1.15  # 15% boost for 3+ methods agreeing
        elif active_methods >= 2:
            multiplier = 1.10  # 10% boost for 2 methods agreeing
        else:
            multiplier = 1.0  # No boost
        
        # Apply multiplier to all active scores
        if multiplier > 1.0:
            validated_scores = {
                method: min(score * multiplier, 10.0) if score > 0 else score
                for method, score in method_scores.items()
            }
            return validated_scores
        
        return method_scores
    
    def _apply_synergy_and_diversity_bonuses(
        self,
        base_score: float,
        method_scores: Dict[str, float]
    ) -> float:
        """
        Phase 3 Win 3 from old system: Apply synergy and diversity bonuses.
        """
        # Get qualified methods (those that scored above threshold)
        qualified_methods = {
            method: score for method, score in method_scores.items()
            if score >= self.method_thresholds.get(method, 2.0)
        }
        
        if not qualified_methods:
            return base_score
        
        num_methods = len(qualified_methods)
        
        # Synergy bonus: Multiple methods agreeing increases confidence
        # 2 methods: +5%, 3 methods: +10%, 4+ methods: +15%
        synergy_bonus = 0.0
        if num_methods >= 2:
            synergy_bonus = min((num_methods - 1) * 0.05, 0.15)
        
        # Diversity bonus: Different types of detection
        method_types = set(qualified_methods.keys())
        diversity_score = 0.0
        
        # Check for complementary method combinations
        has_historical = 'historical' in method_types
        has_cultural = 'cultural' in method_types
        has_obscura = 'atlas_obscura' in method_types
        has_impossibility = 'impossibility' in method_types
        has_uniqueness = 'uniqueness' in method_types
        
        # Bonus for complementary combinations
        if has_historical and has_cultural:
            diversity_score += 0.08  # Historical + Cultural = strong combination
        if has_obscura and (has_historical or has_cultural):
            diversity_score += 0.05  # Obscura + context = good
        if has_impossibility and has_uniqueness:
            diversity_score += 0.05  # Impossibility + Uniqueness = strong
        
        # Apply bonuses
        final_score = base_score * (1.0 + synergy_bonus + diversity_score)
        
        return min(final_score, 10.0)


def get_standout_detector(db: AsyncSession) -> EnhancedStandoutDetector:
    """Get standout detector instance"""
    return EnhancedStandoutDetector(db)
