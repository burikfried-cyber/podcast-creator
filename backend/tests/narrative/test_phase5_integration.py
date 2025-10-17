"""
Phase 5 Integration Tests
Comprehensive end-to-end testing of narrative construction and script generation
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.services.narrative.podcast_generator import PodcastGenerator, generate_podcast_script
from app.services.narrative.models import PodcastType, UserProfile
from app.services.narrative.tts_optimizer import TTSOptimizer


@pytest.fixture
def podcast_generator():
    """Create podcast generator instance"""
    return PodcastGenerator()


@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return {
        'id': 'test_001',
        'title': 'The Westman Islands Puffin Colony Living in Human Houses',
        'content': '''A unique phenomenon where puffins cohabitate with humans in the Westman Islands. 
        This interspecies living arrangement confounds scientists and is found nowhere else in the world.
        The tradition dates back centuries and has been preserved by the local community.
        Researchers are baffled by how this unusual relationship developed.''',
        'location': {'lat': 63.4, 'lng': -20.3, 'name': 'Westman Islands'},
        'standout_score': 8.5,
        'tier': 'exceptional',
        'method_scores': {
            'cultural': 6.0,
            'historical': 5.0,
            'uniqueness': 8.0,
            'atlas_obscura': 7.0
        }
    }


@pytest.fixture
def user_preferences():
    """Sample user preferences"""
    return UserProfile(
        user_id='test_user',
        surprise_tolerance=3,
        preferred_length='medium',
        preferred_style='balanced',
        preferred_pace='moderate',
        interests=['nature', 'culture']
    )


class TestEndToEndGeneration:
    """Test complete end-to-end podcast generation"""
    
    @pytest.mark.asyncio
    async def test_generate_base_podcast(self, podcast_generator, sample_content, user_preferences):
        """Test complete base podcast generation"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        # Check success
        assert result['success'] is True
        assert 'script' in result
        assert 'narrative' in result
        assert 'quality_report' in result
        
        # Check script
        script = result['script']
        assert script.podcast_type == PodcastType.BASE
        assert len(script.content) > 0
        assert len(script.sections) > 0
        assert script.estimated_duration_seconds > 0
        assert script.quality_score > 0
        
        # Check narrative
        narrative = result['narrative']
        assert narrative.engagement_score > 0
        assert len(narrative.story_elements) > 0
        
        # Check quality report
        quality_report = result['quality_report']
        assert quality_report is not None
        assert quality_report.overall_score >= 0
    
    @pytest.mark.asyncio
    async def test_generate_standout_podcast(self, podcast_generator, sample_content, user_preferences):
        """Test standout podcast generation"""
        result = await podcast_generator.generate_standout_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        assert result['success'] is True
        script = result['script']
        
        # Standout podcasts should emphasize mystery/remarkable elements
        assert script.podcast_type == PodcastType.STANDOUT
        assert 'remarkable' in script.content.lower() or 'unique' in script.content.lower()
    
    @pytest.mark.asyncio
    async def test_generate_topic_podcast(self, podcast_generator, sample_content, user_preferences):
        """Test topic-specific podcast generation"""
        result = await podcast_generator.generate_topic_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        assert result['success'] is True
        script = result['script']
        
        # Topic podcasts should be longer/more detailed
        assert script.podcast_type == PodcastType.TOPIC
    
    @pytest.mark.asyncio
    async def test_generate_personalized_podcast(self, podcast_generator, sample_content, user_preferences):
        """Test personalized podcast generation"""
        result = await podcast_generator.generate_personalized_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        assert result['success'] is True
        script = result['script']
        
        # Personalized podcasts should adapt to user
        assert script.podcast_type == PodcastType.PERSONALIZED


class TestScriptQuality:
    """Test script quality and structure"""
    
    @pytest.mark.asyncio
    async def test_script_has_required_sections(self, podcast_generator, sample_content, user_preferences):
        """Test that script has required sections"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        section_types = {section.type.value for section in script.sections}
        
        # Should have hook and conclusion at minimum
        assert 'hook' in section_types
        assert 'conclusion' in section_types
    
    @pytest.mark.asyncio
    async def test_script_content_not_empty(self, podcast_generator, sample_content, user_preferences):
        """Test that script content is not empty"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        
        # Check content
        assert len(script.content) > 100  # Should have substantial content
        assert len(script.content.split()) > 50  # At least 50 words
        
        # Check sections
        for section in script.sections:
            assert len(section.content) > 0
    
    @pytest.mark.asyncio
    async def test_script_mentions_source_content(self, podcast_generator, sample_content, user_preferences):
        """Test that script mentions source content"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        content_lower = script.content.lower()
        
        # Should mention key elements from source
        title_words = sample_content['title'].lower().split()
        
        # At least some words from title should appear
        mentions = sum(1 for word in title_words if len(word) > 3 and word in content_lower)
        assert mentions > 0


class TestQualityControl:
    """Test quality control functionality"""
    
    @pytest.mark.asyncio
    async def test_quality_report_generated(self, podcast_generator, sample_content, user_preferences):
        """Test that quality report is generated"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        quality_report = result['quality_report']
        
        assert quality_report is not None
        assert hasattr(quality_report, 'factual_accuracy')
        assert hasattr(quality_report, 'content_structure')
        assert hasattr(quality_report, 'cultural_sensitivity')
        assert hasattr(quality_report, 'originality')
        assert hasattr(quality_report, 'source_attribution')
    
    @pytest.mark.asyncio
    async def test_quality_checks_have_scores(self, podcast_generator, sample_content, user_preferences):
        """Test that quality checks have scores"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        quality_report = result['quality_report']
        
        # All checks should have scores
        assert 0 <= quality_report.factual_accuracy.score <= 1.0
        assert 0 <= quality_report.content_structure.score <= 1.0
        assert 0 <= quality_report.cultural_sensitivity.score <= 1.0
        assert 0 <= quality_report.originality.score <= 1.0
        assert 0 <= quality_report.source_attribution.score <= 1.0
        
        # Overall score should be calculated
        assert 0 <= quality_report.overall_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_quality_report_has_recommendations(self, podcast_generator, sample_content, user_preferences):
        """Test that quality report includes recommendations"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        quality_report = result['quality_report']
        
        # Should have recommendations list (even if empty)
        assert hasattr(quality_report, 'recommendations')
        assert isinstance(quality_report.recommendations, list)


class TestTTSOptimization:
    """Test TTS optimization"""
    
    @pytest.mark.asyncio
    async def test_tts_markers_present(self, podcast_generator, sample_content, user_preferences):
        """Test that TTS markers are present"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        
        # Should have TTS markers
        assert len(script.tts_markers) > 0
    
    @pytest.mark.asyncio
    async def test_tts_markers_have_types(self, podcast_generator, sample_content, user_preferences):
        """Test that TTS markers have proper types"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        
        # Check marker types
        marker_types = {marker.type for marker in script.tts_markers}
        
        # Should have at least pause markers
        assert 'pause' in marker_types
    
    def test_tts_optimizer_pronunciation_guides(self):
        """Test TTS optimizer pronunciation guides"""
        optimizer = TTSOptimizer()
        
        # Check that pronunciation dictionary exists
        assert len(optimizer.pronunciation_dict) > 0
        
        # Check specific pronunciations
        assert 'reykjavik' in optimizer.pronunciation_dict
        assert 'geysir' in optimizer.pronunciation_dict


class TestUserPersonalization:
    """Test user personalization"""
    
    @pytest.mark.asyncio
    async def test_different_lengths_produce_different_durations(self, podcast_generator, sample_content):
        """Test that different length preferences produce different durations"""
        # Short preference
        short_prefs = UserProfile(
            user_id='test',
            preferred_length='short'
        )
        result_short = await podcast_generator.generate_base_podcast(
            sample_content,
            short_prefs
        )
        
        # Long preference
        long_prefs = UserProfile(
            user_id='test',
            preferred_length='long'
        )
        result_long = await podcast_generator.generate_base_podcast(
            sample_content,
            long_prefs
        )
        
        # Long should be longer than short
        assert result_long['script'].estimated_duration_seconds > result_short['script'].estimated_duration_seconds
    
    @pytest.mark.asyncio
    async def test_different_styles_affect_content(self, podcast_generator, sample_content):
        """Test that different styles affect content"""
        # Casual style
        casual_prefs = UserProfile(
            user_id='test',
            preferred_style='casual'
        )
        result_casual = await podcast_generator.generate_base_podcast(
            sample_content,
            casual_prefs
        )
        
        # Formal style
        formal_prefs = UserProfile(
            user_id='test',
            preferred_style='formal'
        )
        result_formal = await podcast_generator.generate_base_podcast(
            sample_content,
            formal_prefs
        )
        
        # Casual should have contractions, formal should not
        casual_content = result_casual['script'].content
        formal_content = result_formal['script'].content
        
        # Count contractions
        contractions = ["don't", "won't", "can't", "it's", "let's", "we'll"]
        casual_contractions = sum(1 for c in contractions if c in casual_content.lower())
        formal_contractions = sum(1 for c in contractions if c in formal_content.lower())
        
        # Casual should have more contractions (or at least not fewer)
        assert casual_contractions >= formal_contractions


class TestBatchGeneration:
    """Test batch generation functionality"""
    
    @pytest.mark.asyncio
    async def test_batch_generate_multiple_podcasts(self, podcast_generator, sample_content):
        """Test batch generation of multiple podcasts"""
        # Create multiple content items
        content_items = [
            {**sample_content, 'id': f'test_{i}', 'title': f'Test Content {i}'}
            for i in range(3)
        ]
        
        results = await podcast_generator.batch_generate_podcasts(
            content_items=content_items,
            podcast_type=PodcastType.BASE,
            max_concurrent=2
        )
        
        # Should have results for all items
        assert len(results) == 3
        
        # All should be successful
        successes = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        assert successes == 3


class TestConvenienceFunction:
    """Test convenience function"""
    
    @pytest.mark.asyncio
    async def test_generate_podcast_script_function(self, sample_content):
        """Test convenience function for generating scripts"""
        result = await generate_podcast_script(
            content_data=sample_content,
            podcast_type='base',
            user_preferences={
                'user_id': 'test',
                'surprise_tolerance': 2,
                'preferred_length': 'medium'
            }
        )
        
        assert result['success'] is True
        assert 'script' in result
        assert 'quality_report' in result


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_handles_missing_content_gracefully(self, podcast_generator):
        """Test that missing content is handled gracefully"""
        # Minimal content
        minimal_content = {
            'id': 'test_minimal',
            'title': 'Test'
        }
        
        result = await podcast_generator.generate_base_podcast(
            content_data=minimal_content
        )
        
        # Should still succeed (or fail gracefully)
        assert 'success' in result
    
    @pytest.mark.asyncio
    async def test_quality_check_can_be_disabled(self, podcast_generator, sample_content):
        """Test that quality check can be disabled"""
        result = await podcast_generator.generate_podcast(
            content_data=sample_content,
            podcast_type=PodcastType.BASE,
            quality_check=False
        )
        
        assert result['success'] is True
        # Quality report should be None when disabled
        assert result['quality_report'] is None


class TestMetadata:
    """Test metadata generation"""
    
    @pytest.mark.asyncio
    async def test_script_has_metadata(self, podcast_generator, sample_content, user_preferences):
        """Test that script has proper metadata"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        
        # Check metadata
        assert script.metadata is not None
        assert 'content_id' in script.metadata
        assert 'title' in script.metadata
        assert 'narrative_type' in script.metadata
    
    @pytest.mark.asyncio
    async def test_result_has_metadata(self, podcast_generator, sample_content, user_preferences):
        """Test that result has metadata"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        # Check result metadata
        assert 'metadata' in result
        metadata = result['metadata']
        
        assert 'content_id' in metadata
        assert 'podcast_type' in metadata
        assert 'duration_seconds' in metadata
        assert 'quality_score' in metadata


class TestTimingAndDuration:
    """Test timing and duration calculations"""
    
    @pytest.mark.asyncio
    async def test_script_has_timing_cues(self, podcast_generator, sample_content, user_preferences):
        """Test that script has timing cues"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        
        # Should have timing cues
        assert script.timing_cues is not None
        assert len(script.timing_cues) > 0
        assert 'total_duration' in script.timing_cues
    
    @pytest.mark.asyncio
    async def test_duration_is_reasonable(self, podcast_generator, sample_content, user_preferences):
        """Test that duration is reasonable"""
        result = await podcast_generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result['script']
        
        # Duration should be reasonable (not 0, not crazy high)
        assert script.estimated_duration_seconds > 0
        assert script.estimated_duration_seconds < 3600  # Less than 1 hour
