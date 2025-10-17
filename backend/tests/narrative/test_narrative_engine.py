"""
Tests for Narrative Intelligence Engine
"""
import pytest
from unittest.mock import Mock, AsyncMock

from app.services.narrative.narrative_engine import NarrativeIntelligenceEngine
from app.services.narrative.models import UserProfile, NarrativeType


@pytest.fixture
def narrative_engine():
    """Create narrative engine instance"""
    return NarrativeIntelligenceEngine()


@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return {
        'id': 'test_001',
        'title': 'The Mysterious Puffin Houses of Iceland',
        'content': 'A unique phenomenon where puffins live in human houses. This ancient tradition has been preserved for centuries.',
        'location': {'lat': 63.4, 'lng': -20.3},
        'standout_score': 7.5,
        'method_scores': {
            'cultural': 6.0,
            'historical': 5.0,
            'uniqueness': 8.0
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
        preferred_pace='moderate'
    )


class TestNarrativeAnalysis:
    """Test narrative potential analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_narrative_potential(self, narrative_engine, sample_content):
        """Test content analysis for narrative potential"""
        analysis = await narrative_engine.analyze_narrative_potential(sample_content)
        
        assert 'has_timeline' in analysis
        assert 'has_mystery' in analysis
        assert 'complexity_score' in analysis
        assert 'engagement_potential' in analysis
        assert 'recommended_templates' in analysis
        assert isinstance(analysis['recommended_templates'], list)
    
    @pytest.mark.asyncio
    async def test_detects_mystery_elements(self, narrative_engine):
        """Test detection of mystery elements"""
        content = {
            'id': 'test_002',
            'title': 'The Unexplained Mystery',
            'content': 'This mysterious phenomenon baffles scientists and remains unexplained.',
            'standout_score': 8.0
        }
        
        analysis = await narrative_engine.analyze_narrative_potential(content)
        
        assert analysis['has_mystery'] is True
        assert 'mystery_narrative' in analysis['recommended_templates']
    
    @pytest.mark.asyncio
    async def test_detects_historical_depth(self, narrative_engine):
        """Test detection of historical depth"""
        content = {
            'id': 'test_003',
            'title': 'Ancient Historical Site',
            'content': 'This ancient archaeological site dates back thousands of years.',
            'method_scores': {'historical': 7.0}
        }
        
        analysis = await narrative_engine.analyze_narrative_potential(content)
        
        assert analysis['has_historical_depth'] is True
        assert 'historical_narrative' in analysis['recommended_templates']


class TestTemplateSelection:
    """Test narrative template selection"""
    
    @pytest.mark.asyncio
    async def test_select_mystery_template_for_standout(
        self,
        narrative_engine,
        sample_content,
        user_preferences
    ):
        """Test that standout podcasts prefer mystery template"""
        analysis = await narrative_engine.analyze_narrative_potential(sample_content)
        
        template = await narrative_engine.select_narrative_template(
            analysis,
            user_preferences,
            'standout_podcast'
        )
        
        assert template.template.narrative_type == NarrativeType.MYSTERY
    
    @pytest.mark.asyncio
    async def test_select_discovery_template_for_base(
        self,
        narrative_engine,
        sample_content,
        user_preferences
    ):
        """Test that base podcasts prefer discovery template"""
        analysis = await narrative_engine.analyze_narrative_potential(sample_content)
        
        template = await narrative_engine.select_narrative_template(
            analysis,
            user_preferences,
            'base_podcast'
        )
        
        assert template.template.narrative_type == NarrativeType.DISCOVERY


class TestNarrativeConstruction:
    """Test complete narrative construction"""
    
    @pytest.mark.asyncio
    async def test_construct_narrative(
        self,
        narrative_engine,
        sample_content,
        user_preferences
    ):
        """Test complete narrative construction"""
        narrative = await narrative_engine.construct_narrative(
            content_data=sample_content,
            user_preferences=user_preferences,
            podcast_type='base_podcast'
        )
        
        assert narrative is not None
        assert narrative.narrative_type in NarrativeType
        assert narrative.structure is not None
        assert len(narrative.story_elements) > 0
        assert narrative.engagement_score >= 0.0
        assert narrative.engagement_score <= 1.0
        assert narrative.estimated_duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_narrative_has_required_elements(
        self,
        narrative_engine,
        sample_content,
        user_preferences
    ):
        """Test that narrative has required story elements"""
        narrative = await narrative_engine.construct_narrative(
            content_data=sample_content,
            user_preferences=user_preferences,
            podcast_type='base_podcast'
        )
        
        # Check for hook and conclusion
        element_types = {elem.type for elem in narrative.story_elements}
        
        assert 'hook' in {t.value for t in element_types}
        assert 'conclusion' in {t.value for t in element_types}
    
    @pytest.mark.asyncio
    async def test_narrative_duration_matches_preference(
        self,
        narrative_engine,
        sample_content
    ):
        """Test that narrative duration matches user preference"""
        # Test short preference
        short_prefs = UserProfile(
            user_id='test',
            preferred_length='short'
        )
        narrative_short = await narrative_engine.construct_narrative(
            sample_content,
            short_prefs,
            'base_podcast'
        )
        
        # Test long preference
        long_prefs = UserProfile(
            user_id='test',
            preferred_length='long'
        )
        narrative_long = await narrative_engine.construct_narrative(
            sample_content,
            long_prefs,
            'base_podcast'
        )
        
        # Long should be longer than short
        assert narrative_long.estimated_duration_seconds > narrative_short.estimated_duration_seconds


class TestEngagementOptimization:
    """Test engagement optimization"""
    
    @pytest.mark.asyncio
    async def test_high_surprise_tolerance_increases_emphasis(
        self,
        narrative_engine,
        sample_content
    ):
        """Test that high surprise tolerance increases emphasis"""
        high_surprise = UserProfile(
            user_id='test',
            surprise_tolerance=4
        )
        
        narrative = await narrative_engine.construct_narrative(
            sample_content,
            high_surprise,
            'standout_podcast'
        )
        
        # Check that some elements have high emphasis
        high_emphasis_elements = [
            elem for elem in narrative.story_elements
            if elem.emphasis_level >= 4
        ]
        
        assert len(high_emphasis_elements) > 0
