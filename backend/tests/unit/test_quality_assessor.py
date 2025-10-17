"""
Unit Tests for Content Quality Assessor
Tests for multi-dimensional quality scoring
"""
import pytest

# Mark all tests in this file as unit tests (no external dependencies)
pytestmark = pytest.mark.unit
from app.services.quality.content_quality_assessor import (
    ContentQualityAssessor,
    SourceAuthority,
    SOURCE_AUTHORITY_MAP
)


@pytest.fixture
def assessor():
    """Create quality assessor instance"""
    return ContentQualityAssessor()


@pytest.mark.asyncio
async def test_source_authority_scoring(assessor):
    """Test source authority assessment"""
    # Government source
    score_gov = assessor._assess_source_authority(["UNESCO"])
    assert score_gov == 1.0
    
    # Academic source
    score_academic = assessor._assess_source_authority(["Smithsonian"])
    assert score_academic == 0.85
    
    # Community source
    score_community = assessor._assess_source_authority(["OpenTripMap"])
    assert score_community == 0.5


@pytest.mark.asyncio
async def test_content_completeness(assessor):
    """Test content completeness assessment"""
    # Complete content
    complete_content = {
        "title": "Test Title",
        "description": "A detailed description",
        "location": "Paris, France",
        "date": "2020",
        "source": "Test",
        "url": "http://example.com",
        "type": "article"
    }
    
    score = assessor._assess_content_completeness(complete_content)
    assert score == 1.0
    
    # Incomplete content
    incomplete_content = {
        "title": "Test Title"
    }
    
    score_incomplete = assessor._assess_content_completeness(incomplete_content)
    assert score_incomplete < 0.5


@pytest.mark.asyncio
async def test_content_freshness(assessor):
    """Test content freshness assessment"""
    # Recent content
    recent_content = {"date": "2024"}
    score_recent = assessor._assess_content_freshness(recent_content)
    assert score_recent > 0.9
    
    # Old content
    old_content = {"date": "1950"}
    score_old = assessor._assess_content_freshness(old_content)
    assert score_old < 0.5
    
    # No date
    no_date_content = {}
    score_no_date = assessor._assess_content_freshness(no_date_content)
    assert score_no_date == 0.5  # Default


@pytest.mark.asyncio
async def test_engagement_potential(assessor):
    """Test engagement potential assessment"""
    # High engagement content
    engaging_content = {
        "title": "Mysterious Ancient Discovery",
        "description": "A remarkable and unique archaeological find that reveals extraordinary secrets from the past. This exceptional discovery includes detailed documentation and rare photographs.",
        "thumbnail": "http://example.com/image.jpg",
        "media": ["video1.mp4"]
    }
    
    score = assessor._assess_engagement_potential(engaging_content)
    assert score > 0.5
    
    # Low engagement content
    boring_content = {
        "title": "Item",
        "description": "Thing"
    }
    
    score_low = assessor._assess_engagement_potential(boring_content)
    assert score_low < 0.3


@pytest.mark.asyncio
async def test_overall_quality_score(assessor):
    """Test overall quality score calculation"""
    content = {
        "title": "UNESCO World Heritage Site",
        "description": "A detailed description of this remarkable historical site",
        "location": "Paris, France",
        "date": "2023",
        "source": "UNESCO",
        "url": "http://example.com",
        "thumbnail": "http://example.com/image.jpg"
    }
    
    score = await assessor.assess_content_quality(
        content=content,
        sources=["UNESCO"]
    )
    
    assert score.overall > 0.7
    assert score.source_authority == 1.0
    assert score.content_completeness > 0.8
    assert score.confidence > 0.7


@pytest.mark.asyncio
async def test_cross_reference_verification(assessor):
    """Test factual accuracy with cross-reference"""
    content = {
        "title": "Eiffel Tower",
        "date": "1889",
        "location": "Paris"
    }
    
    cross_ref = [
        {"title": "Eiffel Tower", "date": "1889", "location": "Paris, France"},
        {"title": "Tour Eiffel", "date": "1889", "location": "Paris"}
    ]
    
    score = await assessor.assess_content_quality(
        content=content,
        sources=["Source1"],
        cross_reference_data=cross_ref
    )
    
    assert score.factual_accuracy > 0.7


@pytest.mark.asyncio
async def test_text_similarity(assessor):
    """Test text similarity calculation"""
    text1 = "The Eiffel Tower in Paris"
    text2 = "Eiffel Tower Paris France"
    
    similarity = assessor._text_similarity(text1, text2)
    assert similarity > 0.5
    
    text3 = "Completely different content"
    similarity_low = assessor._text_similarity(text1, text3)
    assert similarity_low < 0.3


@pytest.mark.asyncio
async def test_confidence_calculation(assessor):
    """Test confidence score calculation"""
    # High confidence: good scores, multiple sources
    confidence_high = assessor._calculate_confidence(
        authority=0.9,
        completeness=0.9,
        accuracy=0.9,
        num_sources=3
    )
    assert confidence_high > 0.9
    
    # Low confidence: poor scores, single source
    confidence_low = assessor._calculate_confidence(
        authority=0.5,
        completeness=0.5,
        accuracy=0.5,
        num_sources=1
    )
    assert confidence_low < 0.7


@pytest.mark.asyncio
async def test_source_authority_map():
    """Test source authority mapping"""
    assert SOURCE_AUTHORITY_MAP["UNESCO"] == SourceAuthority.GOVERNMENT
    assert SOURCE_AUTHORITY_MAP["Smithsonian"] == SourceAuthority.MUSEUM
    assert SOURCE_AUTHORITY_MAP["Guardian"] == SourceAuthority.NEWS_MAJOR
