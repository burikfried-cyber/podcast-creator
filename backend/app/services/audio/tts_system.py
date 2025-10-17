"""
Multi-Tier TTS System
Cost-optimized text-to-speech synthesis with multiple providers
"""
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Tuple
import structlog

from .models import (
    TTSProvider,
    TTSProviderTier,
    TTSRequest,
    AudioResult,
    AudioFormat,
    VoicePreferences,
    UserTier,
    QualityMetrics,
    CostTracking,
    SynthesisJob,
    QUALITY_TIERS,
    USER_TIER_QUALITY_MAP
)

logger = structlog.get_logger()


class MultiTierTTSSystem:
    """
    Multi-tier TTS system with cost-optimized provider selection
    Supports free, premium, and ultra-premium providers
    """
    
    def __init__(self):
        # Initialize TTS provider registry
        self.tts_providers = self._initialize_providers()
        
        # Provider selection weights
        self.selection_weights = {
            'quality': 0.4,
            'cost': 0.4,
            'features': 0.2
        }
        
        # Budget limits per user tier (per 1000 characters)
        self.tier_budgets = {
            UserTier.FREE: 0.0,  # Free tier uses free providers only
            UserTier.PREMIUM: 0.02,  # $0.02 per 1000 chars
            UserTier.ULTRA_PREMIUM: 0.50  # $0.50 per 1000 chars
        }
        
        # Cache for synthesis results
        self.synthesis_cache: Dict[str, AudioResult] = {}
        
        # Cost tracking
        self.cost_tracker: List[CostTracking] = []
    
    def _initialize_providers(self) -> Dict[str, Dict[str, TTSProvider]]:
        """Initialize TTS provider registry"""
        return {
            'free': {
                'espeak': TTSProvider(
                    name='eSpeak',
                    tier=TTSProviderTier.FREE,
                    cost_per_char=0.0,
                    quality_score=3,
                    supported_languages=50,
                    api_endpoint='local_espeak',
                    supported_features=['basic_synthesis'],
                    max_chars_per_request=10000,
                    rate_limit_per_minute=1000
                ),
                'festival': TTSProvider(
                    name='Festival',
                    tier=TTSProviderTier.FREE,
                    cost_per_char=0.0,
                    quality_score=3,
                    supported_languages=10,
                    api_endpoint='local_festival',
                    supported_features=['basic_synthesis'],
                    max_chars_per_request=10000,
                    rate_limit_per_minute=1000
                )
            },
            'premium': {
                'azure_neural': TTSProvider(
                    name='Azure Neural TTS',
                    tier=TTSProviderTier.PREMIUM,
                    cost_per_char=0.000016,  # $16 per 1M chars
                    quality_score=9,
                    supported_languages=75,
                    api_endpoint='https://speech.microsoft.com',
                    supported_features=['neural_voices', 'ssml', 'custom_voices'],
                    max_chars_per_request=5000,
                    rate_limit_per_minute=100
                ),
                'aws_polly': TTSProvider(
                    name='AWS Polly',
                    tier=TTSProviderTier.PREMIUM,
                    cost_per_char=0.000004,  # $4 per 1M chars
                    quality_score=8,
                    supported_languages=60,
                    api_endpoint='https://polly.amazonaws.com',
                    supported_features=['neural_voices', 'ssml', 'speech_marks'],
                    max_chars_per_request=3000,
                    rate_limit_per_minute=80
                ),
                'google_cloud': TTSProvider(
                    name='Google Cloud TTS',
                    tier=TTSProviderTier.PREMIUM,
                    cost_per_char=0.000016,  # $16 per 1M chars
                    quality_score=9,
                    supported_languages=40,
                    api_endpoint='https://texttospeech.googleapis.com',
                    supported_features=['wavenet_voices', 'ssml', 'audio_profiles'],
                    max_chars_per_request=5000,
                    rate_limit_per_minute=100
                )
            },
            'ultra_premium': {
                'elevenlabs': TTSProvider(
                    name='ElevenLabs',
                    tier=TTSProviderTier.ULTRA_PREMIUM,
                    cost_per_char=0.0003,  # $300 per 1M chars
                    quality_score=10,
                    supported_languages=15,
                    api_endpoint='https://api.elevenlabs.io',
                    supported_features=['voice_cloning', 'emotion_control', 'custom_models'],
                    max_chars_per_request=5000,
                    rate_limit_per_minute=50
                ),
                'murf': TTSProvider(
                    name='Murf.ai',
                    tier=TTSProviderTier.ULTRA_PREMIUM,
                    cost_per_char=0.00023,  # $230 per 1M chars
                    quality_score=9,
                    supported_languages=20,
                    api_endpoint='https://api.murf.ai',
                    supported_features=['ai_voices', 'emotion_control', 'custom_pronunciation'],
                    max_chars_per_request=5000,
                    rate_limit_per_minute=60
                )
            }
        }
    
    async def synthesize_podcast(
        self,
        script_text: str,
        user_tier: UserTier,
        voice_preferences: Optional[VoicePreferences] = None,
        target_quality: Optional[str] = None
    ) -> AudioResult:
        """
        Main method to synthesize podcast audio
        
        Args:
            script_text: Text to synthesize
            user_tier: User subscription tier
            voice_preferences: Voice customization preferences
            target_quality: Target quality level (overrides tier default)
            
        Returns:
            AudioResult with synthesized audio
        """
        logger.info("tts_synthesis_started",
                   text_length=len(script_text),
                   user_tier=user_tier.value)
        
        try:
            # Set defaults
            if voice_preferences is None:
                voice_preferences = VoicePreferences()
            
            if target_quality is None:
                target_quality = USER_TIER_QUALITY_MAP[user_tier]
            
            # Check cache
            cache_key = self._generate_cache_key(script_text, voice_preferences, target_quality)
            if cache_key in self.synthesis_cache:
                logger.info("tts_cache_hit", cache_key=cache_key)
                return self.synthesis_cache[cache_key]
            
            # Select optimal TTS provider
            provider = await self.select_optimal_tts(
                user_tier=user_tier,
                text_length=len(script_text),
                voice_preferences=voice_preferences,
                target_quality=target_quality
            )
            
            # Optimize script for speech synthesis
            speech_optimized = await self.optimize_script_for_speech(
                script_text,
                provider
            )
            
            # Generate audio with selected provider
            raw_audio = await self._synthesize_with_provider(
                provider=provider,
                text=speech_optimized,
                voice_preferences=voice_preferences
            )
            
            # Create audio result
            audio_result = AudioResult(
                audio_data=raw_audio,
                format=AudioFormat.WAV,  # Raw format from TTS
                duration_seconds=self._estimate_duration(len(script_text)),
                sample_rate=44100,
                bit_depth=16,
                channels=1,
                file_size_bytes=len(raw_audio),
                provider_used=provider.name,
                synthesis_cost=provider.calculate_cost(len(script_text)),
                quality_metrics=None,  # Will be assessed in processing
                metadata={
                    'text_length': len(script_text),
                    'voice_preferences': voice_preferences.__dict__,
                    'target_quality': target_quality
                }
            )
            
            # Track cost
            await self._track_cost(audio_result, user_tier)
            
            # Cache result
            self.synthesis_cache[cache_key] = audio_result
            
            logger.info("tts_synthesis_complete",
                       provider=provider.name,
                       cost=audio_result.synthesis_cost,
                       duration=audio_result.duration_seconds)
            
            return audio_result
            
        except Exception as e:
            logger.error("tts_synthesis_failed",
                        error=str(e),
                        text_length=len(script_text))
            raise
    
    async def select_optimal_tts(
        self,
        user_tier: UserTier,
        text_length: int,
        voice_preferences: VoicePreferences,
        target_quality: str
    ) -> TTSProvider:
        """
        Select optimal TTS provider based on tier, budget, and requirements
        
        Uses weighted scoring:
        - 40% Quality score
        - 40% Cost efficiency
        - 20% Feature match
        """
        # Calculate budget
        budget = self._calculate_budget(user_tier, text_length)
        
        # Get quality tier configuration
        quality_config = QUALITY_TIERS.get(target_quality, QUALITY_TIERS['standard'])
        required_tier = quality_config['tts_tier']
        required_features = quality_config['features']
        
        # Filter providers by tier and budget
        available_providers = self._filter_providers_by_tier(required_tier)
        available_providers = self._filter_providers_by_budget(
            available_providers,
            budget,
            text_length
        )
        
        if not available_providers:
            # Fallback to free tier if no providers available
            logger.warning("no_providers_available_fallback_to_free",
                          user_tier=user_tier.value,
                          budget=budget)
            available_providers = list(self.tts_providers['free'].values())
        
        # Score providers - use list of tuples instead of dict
        provider_scores = []
        for provider in available_providers:
            # Quality score (0-1)
            quality_score = provider.quality_score / 10.0
            
            # Cost score (0-1) - lower cost = higher score
            cost = provider.calculate_cost(text_length)
            cost_score = 1.0 - min(cost / budget, 1.0) if budget > 0 else 1.0
            
            # Feature match score (0-1)
            feature_score = self._calculate_feature_match(
                provider,
                required_features
            )
            
            # Weighted total score
            total_score = (
                quality_score * self.selection_weights['quality'] +
                cost_score * self.selection_weights['cost'] +
                feature_score * self.selection_weights['features']
            )
            
            provider_scores.append((provider, total_score))
        
        # Select provider with highest score
        best_provider, best_score = max(provider_scores, key=lambda x: x[1])
        
        logger.info("tts_provider_selected",
                   provider=best_provider.name,
                   score=best_score,
                   cost=best_provider.calculate_cost(text_length))
        
        return best_provider
    
    async def optimize_script_for_speech(
        self,
        text: str,
        provider: TTSProvider
    ) -> str:
        """
        Optimize script for speech synthesis
        Handles SSML, pronunciation, pacing
        """
        optimized = text
        
        # If provider supports SSML, wrap in SSML tags
        if provider.supports_feature('ssml'):
            optimized = self._wrap_in_ssml(optimized)
        
        # Add pronunciation guides for difficult words
        optimized = self._add_pronunciation_guides(optimized, provider)
        
        # Optimize for provider's character limit
        if len(optimized) > provider.max_chars_per_request:
            optimized = self._chunk_text(optimized, provider.max_chars_per_request)
        
        return optimized
    
    async def _synthesize_with_provider(
        self,
        provider: TTSProvider,
        text: str,
        voice_preferences: VoicePreferences
    ) -> bytes:
        """
        Synthesize audio with specific provider
        This is a mock implementation - actual implementation would call provider APIs
        """
        # Mock implementation - returns empty bytes
        # In production, this would call the actual TTS API
        
        logger.info("calling_tts_provider",
                   provider=provider.name,
                   text_length=len(text))
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Mock audio data (in production, this would be actual audio from API)
        mock_audio = b'MOCK_AUDIO_DATA_' + text[:100].encode('utf-8')
        
        return mock_audio
    
    async def batch_synthesize(
        self,
        texts: List[str],
        user_tier: UserTier,
        voice_preferences: Optional[VoicePreferences] = None,
        max_concurrent: int = 5
    ) -> List[AudioResult]:
        """
        Batch synthesize multiple texts concurrently
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def synthesize_with_limit(text):
            async with semaphore:
                return await self.synthesize_podcast(text, user_tier, voice_preferences)
        
        results = await asyncio.gather(
            *[synthesize_with_limit(text) for text in texts],
            return_exceptions=True
        )
        
        return results
    
    # Helper methods
    
    def _calculate_budget(self, user_tier: UserTier, text_length: int) -> float:
        """Calculate budget for synthesis based on user tier"""
        budget_per_1k = self.tier_budgets[user_tier]
        return (text_length / 1000) * budget_per_1k
    
    def _filter_providers_by_tier(
        self,
        required_tier: TTSProviderTier
    ) -> List[TTSProvider]:
        """Filter providers by tier level"""
        tier_hierarchy = {
            TTSProviderTier.FREE: ['free'],
            TTSProviderTier.PREMIUM: ['free', 'premium'],
            TTSProviderTier.ULTRA_PREMIUM: ['free', 'premium', 'ultra_premium']
        }
        
        allowed_tiers = tier_hierarchy.get(required_tier, ['free'])
        providers = []
        
        for tier_name in allowed_tiers:
            if tier_name in self.tts_providers:
                providers.extend(self.tts_providers[tier_name].values())
        
        return providers
    
    def _filter_providers_by_budget(
        self,
        providers: List[TTSProvider],
        budget: float,
        text_length: int
    ) -> List[TTSProvider]:
        """Filter providers that fit within budget"""
        if budget == 0:
            # Free tier only
            return [p for p in providers if p.cost_per_char == 0]
        
        return [
            p for p in providers
            if p.calculate_cost(text_length) <= budget
        ]
    
    def _calculate_feature_match(
        self,
        provider: TTSProvider,
        required_features: List[str]
    ) -> float:
        """Calculate how well provider matches required features"""
        if not required_features:
            return 1.0
        
        matches = sum(
            1 for feature in required_features
            if provider.supports_feature(feature)
        )
        
        return matches / len(required_features)
    
    def _generate_cache_key(
        self,
        text: str,
        voice_preferences: VoicePreferences,
        target_quality: str
    ) -> str:
        """Generate cache key for synthesis result"""
        key_data = f"{text}_{voice_preferences.language}_{voice_preferences.gender}_{voice_preferences.style}_{target_quality}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _estimate_duration(self, text_length: int) -> float:
        """Estimate audio duration based on text length"""
        # Average speaking rate: ~150 words per minute
        # Average word length: ~5 characters
        words = text_length / 5
        minutes = words / 150
        return minutes * 60  # Convert to seconds
    
    def _wrap_in_ssml(self, text: str) -> str:
        """Wrap text in SSML tags"""
        return f'<speak>{text}</speak>'
    
    def _add_pronunciation_guides(
        self,
        text: str,
        provider: TTSProvider
    ) -> str:
        """Add pronunciation guides for difficult words"""
        # Simple implementation - in production would use comprehensive dictionary
        pronunciation_map = {
            'Reykjavik': '<phoneme alphabet="ipa" ph="ˈreɪkjəvɪk">Reykjavik</phoneme>',
            'Geysir': '<phoneme alphabet="ipa" ph="ˈɡeɪzɪr">Geysir</phoneme>',
        }
        
        if provider.supports_feature('ssml'):
            for word, phoneme in pronunciation_map.items():
                text = text.replace(word, phoneme)
        
        return text
    
    def _chunk_text(self, text: str, max_length: int) -> str:
        """Chunk text to fit provider's character limit"""
        # Simple chunking - in production would be more sophisticated
        if len(text) <= max_length:
            return text
        
        # Take first chunk for now
        return text[:max_length]
    
    async def _track_cost(
        self,
        audio_result: AudioResult,
        user_tier: UserTier
    ):
        """Track synthesis cost"""
        cost_entry = CostTracking(
            tts_cost=audio_result.synthesis_cost,
            storage_cost=0.0,  # Will be calculated later
            bandwidth_cost=0.0,  # Will be calculated later
            processing_cost=0.0,  # Will be calculated later
            total_cost=audio_result.synthesis_cost,
            provider=audio_result.provider_used,
            user_tier=user_tier
        )
        
        self.cost_tracker.append(cost_entry)
    
    def get_cost_summary(self, user_tier: Optional[UserTier] = None) -> Dict[str, Any]:
        """Get cost summary statistics"""
        relevant_costs = self.cost_tracker
        
        if user_tier:
            relevant_costs = [c for c in self.cost_tracker if c.user_tier == user_tier]
        
        if not relevant_costs:
            return {
                'total_syntheses': 0,
                'total_cost': 0.0,
                'average_cost': 0.0
            }
        
        total_cost = sum(c.total_cost for c in relevant_costs)
        
        return {
            'total_syntheses': len(relevant_costs),
            'total_cost': total_cost,
            'average_cost': total_cost / len(relevant_costs),
            'by_provider': self._group_costs_by_provider(relevant_costs)
        }
    
    def _group_costs_by_provider(
        self,
        costs: List[CostTracking]
    ) -> Dict[str, Dict[str, float]]:
        """Group costs by provider"""
        by_provider = {}
        
        for cost in costs:
            if cost.provider not in by_provider:
                by_provider[cost.provider] = {
                    'count': 0,
                    'total_cost': 0.0
                }
            
            by_provider[cost.provider]['count'] += 1
            by_provider[cost.provider]['total_cost'] += cost.total_cost
        
        # Calculate averages
        for provider in by_provider:
            count = by_provider[provider]['count']
            by_provider[provider]['average_cost'] = by_provider[provider]['total_cost'] / count
        
        return by_provider
    
    def get_available_providers(
        self,
        user_tier: UserTier
    ) -> List[Dict[str, Any]]:
        """Get list of available providers for user tier"""
        quality = USER_TIER_QUALITY_MAP[user_tier]
        quality_config = QUALITY_TIERS[quality]
        required_tier = quality_config['tts_tier']
        
        providers = self._filter_providers_by_tier(required_tier)
        
        return [
            {
                'name': p.name,
                'quality_score': p.quality_score,
                'cost_per_1000_chars': p.cost_per_char * 1000,
                'languages': p.supported_languages,
                'features': p.supported_features
            }
            for p in providers
        ]


# Convenience function
async def synthesize_audio(
    text: str,
    user_tier: str = "free",
    voice_preferences: Optional[Dict[str, Any]] = None
) -> AudioResult:
    """
    Convenience function to synthesize audio
    
    Args:
        text: Text to synthesize
        user_tier: User tier (free, premium, ultra_premium)
        voice_preferences: Voice customization dict
        
    Returns:
        AudioResult with synthesized audio
    """
    tts_system = MultiTierTTSSystem()
    
    # Convert string to enum
    tier_enum = UserTier(user_tier)
    
    # Convert dict to VoicePreferences if provided
    voice_prefs = None
    if voice_preferences:
        voice_prefs = VoicePreferences(**voice_preferences)
    
    return await tts_system.synthesize_podcast(
        script_text=text,
        user_tier=tier_enum,
        voice_preferences=voice_prefs
    )
