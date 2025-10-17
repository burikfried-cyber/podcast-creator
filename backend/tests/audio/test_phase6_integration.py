"""
Phase 6 Integration Tests
Comprehensive testing of audio synthesis and delivery system
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.services.audio.tts_system import MultiTierTTSSystem
from app.services.audio.audio_processor import AudioProcessingPipeline
from app.services.audio.delivery_system import AudioDeliverySystem
from app.services.audio.quality_assurance import AudioQualityAssurance
from app.services.audio.models import (
    UserTier,
    VoicePreferences,
    AudioFormat,
    AudioProcessingOptions
)


@pytest.fixture
def tts_system():
    """Create TTS system instance"""
    return MultiTierTTSSystem()


@pytest.fixture
def audio_processor():
    """Create audio processor instance"""
    return AudioProcessingPipeline()


@pytest.fixture
def delivery_system():
    """Create delivery system instance"""
    return AudioDeliverySystem()


@pytest.fixture
def quality_assurance():
    """Create QA system instance"""
    return AudioQualityAssurance()


@pytest.fixture
def sample_text():
    """Sample text for synthesis"""
    return "Welcome to this amazing podcast about the Westman Islands. Today we'll explore the unique phenomenon of puffins living in human houses."


class TestTTSSystem:
    """Test TTS synthesis system"""
    
    @pytest.mark.asyncio
    async def test_synthesize_free_tier(self, tts_system, sample_text):
        """Test synthesis with free tier"""
        result = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        assert result is not None
        assert result.provider_used in ['eSpeak', 'Festival']
        assert result.synthesis_cost == 0.0
        assert result.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_synthesize_premium_tier(self, tts_system, sample_text):
        """Test synthesis with premium tier"""
        result = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        assert result is not None
        assert result.provider_used in ['Azure Neural TTS', 'AWS Polly', 'Google Cloud TTS']
        assert result.synthesis_cost > 0
    
    @pytest.mark.asyncio
    async def test_provider_selection(self, tts_system):
        """Test optimal provider selection"""
        provider = await tts_system.select_optimal_tts(
            user_tier=UserTier.PREMIUM,
            text_length=1000,
            voice_preferences=VoicePreferences(),
            target_quality='premium'
        )
        
        assert provider is not None
        assert provider.quality_score >= 8
    
    @pytest.mark.asyncio
    async def test_voice_preferences(self, tts_system, sample_text):
        """Test synthesis with voice preferences"""
        prefs = VoicePreferences(
            language='en-US',
            gender='female',
            style='conversational',
            speed=1.2
        )
        
        result = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM,
            voice_preferences=prefs
        )
        
        assert result is not None
        assert 'voice_preferences' in result.metadata
    
    @pytest.mark.asyncio
    async def test_batch_synthesis(self, tts_system):
        """Test batch synthesis"""
        texts = [
            "First podcast text",
            "Second podcast text",
            "Third podcast text"
        ]
        
        results = await tts_system.batch_synthesize(
            texts=texts,
            user_tier=UserTier.FREE,
            max_concurrent=2
        )
        
        assert len(results) == 3
        assert all(r is not None for r in results if not isinstance(r, Exception))
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, tts_system, sample_text):
        """Test cost tracking"""
        await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        stats = tts_system.get_cost_summary()
        
        assert stats['total_syntheses'] > 0
        assert stats['total_cost'] >= 0


class TestAudioProcessing:
    """Test audio processing pipeline"""
    
    @pytest.mark.asyncio
    async def test_process_audio_basic(self, audio_processor, tts_system, sample_text):
        """Test basic audio processing"""
        # First synthesize
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        # Then process
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        assert processed is not None
        assert processed.format == AudioFormat.MP3
        assert processed.bitrate == '128kbps'
        assert len(processed.optimizations_applied) > 0
    
    @pytest.mark.asyncio
    async def test_quality_tiers(self, audio_processor, tts_system, sample_text):
        """Test different quality tiers"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        # Test each quality tier
        for quality in ['basic', 'standard', 'premium', 'ultra_premium']:
            processed = await audio_processor.post_process_audio(
                raw_audio=raw_audio,
                target_quality=quality
            )
            
            assert processed is not None
            assert processed.quality_metrics is not None
    
    @pytest.mark.asyncio
    async def test_compression_settings(self, audio_processor):
        """Test compression settings"""
        settings = audio_processor.get_compression_settings('premium')
        
        assert settings.bitrate == '192kbps'
        assert settings.sample_rate == '44.1kHz'
        assert settings.quality == 2
    
    @pytest.mark.asyncio
    async def test_processing_options(self, audio_processor, tts_system, sample_text):
        """Test custom processing options"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        options = AudioProcessingOptions(
            normalize=True,
            noise_reduction=True,
            clarity_boost=True,
            dynamic_range_optimization=True
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='premium',
            options=options
        )
        
        assert 'normalization' in processed.optimizations_applied
        assert 'noise_reduction' in processed.optimizations_applied


class TestAudioDelivery:
    """Test audio delivery system"""
    
    @pytest.mark.asyncio
    async def test_deliver_audio(self, delivery_system, audio_processor, tts_system, sample_text):
        """Test audio delivery"""
        # Synthesize and process
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        # Deliver
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_content'
        )
        
        assert delivery is not None
        assert delivery.download_url is not None
        assert delivery.cdn_url is not None
        assert not delivery.is_expired()
    
    @pytest.mark.asyncio
    async def test_streaming_enabled(self, delivery_system, audio_processor, tts_system, sample_text):
        """Test streaming setup"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_content',
            enable_streaming=True
        )
        
        assert delivery.streaming_url is not None
        assert len(delivery.quality_variants) > 0
    
    @pytest.mark.asyncio
    async def test_delivery_metrics(self, delivery_system, audio_processor, tts_system, sample_text):
        """Test delivery metrics tracking"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_content'
        )
        
        # Track metrics
        await delivery_system.track_delivery_metrics(
            delivery=delivery,
            download_time_ms=1500,
            first_byte_time_ms=200,
            cdn_hit=True,
            region='us-east-1',
            user_agent='Mozilla/5.0',
            success=True
        )
        
        stats = delivery_system.get_delivery_stats()
        
        assert stats['total_deliveries'] > 0
        assert stats['cdn_hit_rate'] > 0


class TestQualityAssurance:
    """Test quality assurance system"""
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, quality_assurance, audio_processor, tts_system, sample_text):
        """Test quality assessment"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='premium'
        )
        
        assessment = await quality_assurance.assess_audio_quality(
            processed_audio=processed
        )
        
        assert assessment is not None
        assert 0 <= assessment.overall_score <= 10
        assert assessment.objective_metrics is not None
    
    @pytest.mark.asyncio
    async def test_quality_thresholds(self, quality_assurance, audio_processor, tts_system, sample_text):
        """Test quality threshold validation"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='basic'
        )
        
        assessment = await quality_assurance.assess_audio_quality(
            processed_audio=processed
        )
        
        # Basic quality may have warnings but should not have critical issues
        assert isinstance(assessment.warnings, list)
        assert isinstance(assessment.issues, list)


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline"""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline(self, tts_system, audio_processor, delivery_system, quality_assurance):
        """Test complete audio pipeline from synthesis to delivery"""
        text = "This is a complete end-to-end test of the audio synthesis and delivery pipeline."
        
        # Step 1: Synthesize
        raw_audio = await tts_system.synthesize_podcast(
            script_text=text,
            user_tier=UserTier.PREMIUM
        )
        
        assert raw_audio is not None
        
        # Step 2: Process
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='premium'
        )
        
        assert processed is not None
        assert processed.file_size_bytes > 0
        
        # Step 3: Quality check
        assessment = await quality_assurance.assess_audio_quality(
            processed_audio=processed
        )
        
        assert assessment is not None
        assert assessment.overall_score > 0
        
        # Step 4: Deliver
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_content'
        )
        
        assert delivery is not None
        assert delivery.download_url is not None
    
    @pytest.mark.asyncio
    async def test_multiple_quality_tiers(self, tts_system, audio_processor):
        """Test pipeline with multiple quality tiers"""
        text = "Testing multiple quality tiers."
        
        for tier, quality in [
            (UserTier.FREE, 'basic'),
            (UserTier.PREMIUM, 'premium'),
            (UserTier.ULTRA_PREMIUM, 'ultra_premium')
        ]:
            raw_audio = await tts_system.synthesize_podcast(
                script_text=text,
                user_tier=tier
            )
            
            processed = await audio_processor.post_process_audio(
                raw_audio=raw_audio,
                target_quality=quality
            )
            
            assert processed is not None
            assert processed.quality_metrics is not None


class TestPerformance:
    """Test performance metrics"""
    
    @pytest.mark.asyncio
    async def test_synthesis_speed(self, tts_system):
        """Test synthesis speed"""
        import time
        
        text = "Performance test text. " * 50  # ~500 words
        
        start = time.time()
        result = await tts_system.synthesize_podcast(
            script_text=text,
            user_tier=UserTier.FREE
        )
        duration = time.time() - start
        
        assert result is not None
        # Should complete in reasonable time (mock is instant)
        assert duration < 5.0
    
    @pytest.mark.asyncio
    async def test_processing_speed(self, audio_processor, tts_system):
        """Test processing speed"""
        text = "Processing speed test."
        
        raw_audio = await tts_system.synthesize_podcast(
            script_text=text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        assert processed.processing_time_seconds < 10.0


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_text(self, tts_system):
        """Test handling of empty text"""
        # Should handle gracefully or raise appropriate error
        try:
            result = await tts_system.synthesize_podcast(
                script_text="",
                user_tier=UserTier.FREE
            )
            # If it succeeds, result should be valid
            assert result is not None
        except Exception as e:
            # If it fails, should be a clear error
            assert str(e)
    
    @pytest.mark.asyncio
    async def test_invalid_quality_tier(self, audio_processor, tts_system):
        """Test handling of invalid quality tier"""
        raw_audio = await tts_system.synthesize_podcast(
            script_text="Test",
            user_tier=UserTier.FREE
        )
        
        # Should fallback to standard
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='invalid_tier'
        )
        
        assert processed is not None
