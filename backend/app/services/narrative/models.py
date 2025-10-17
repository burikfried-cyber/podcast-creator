"""
Data models for narrative construction and script generation
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class NarrativeType(str, Enum):
    """Types of narrative structures"""
    DISCOVERY = "discovery_narrative"
    MYSTERY = "mystery_narrative"
    HISTORICAL = "historical_narrative"
    CULTURAL = "cultural_narrative"
    PERSONAL = "personal_narrative"


class PodcastType(str, Enum):
    """Types of podcast formats"""
    BASE = "base_podcast"
    STANDOUT = "standout_podcast"
    TOPIC = "topic_podcast"
    PERSONALIZED = "personalized_podcast"


class ScriptSection(str, Enum):
    """Sections of a podcast script"""
    HOOK = "hook"
    INTRODUCTION = "introduction"
    MAIN_CONTENT = "main_content"
    TRANSITION = "transition"
    CLIMAX = "climax"
    CONCLUSION = "conclusion"


@dataclass
class StoryElement:
    """Individual story element (hook, transition, climax, etc.)"""
    type: ScriptSection
    content: str
    timing_seconds: float
    emphasis_level: int = 1  # 1-5 scale
    tts_markers: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeStructure:
    """Structure of the narrative"""
    narrative_type: NarrativeType
    story_arc: List[str]  # Sequence of story beats
    key_moments: List[Dict[str, Any]]
    pacing_profile: Dict[str, float]  # Section -> duration ratio
    engagement_hooks: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstructedNarrative:
    """Complete constructed narrative"""
    narrative_type: NarrativeType
    structure: NarrativeStructure
    story_elements: List[StoryElement]
    narrative_flow: List[Dict[str, Any]]
    engagement_score: float
    estimated_duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_total_duration(self) -> float:
        """Calculate total duration from story elements"""
        return sum(element.timing_seconds for element in self.story_elements)


@dataclass
class TTSMarker:
    """Text-to-Speech optimization marker"""
    position: int  # Character position in text
    type: str  # pause, emphasis, speed, pronunciation
    value: Any  # Marker-specific value
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PodcastScript:
    """Complete podcast script ready for TTS"""
    podcast_type: PodcastType
    content: str  # Full script text
    sections: List[StoryElement]
    tts_markers: List[TTSMarker]
    timing_cues: Dict[str, float]
    metadata: Dict[str, Any]
    quality_score: float
    estimated_duration_seconds: float
    title: str = ""  # Podcast title
    description: str = ""  # Podcast description
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_section_by_type(self, section_type: ScriptSection) -> Optional[StoryElement]:
        """Get first section of specified type"""
        for section in self.sections:
            if section.type == section_type:
                return section
        return None
    
    def get_all_sections_by_type(self, section_type: ScriptSection) -> List[StoryElement]:
        """Get all sections of specified type"""
        return [s for s in self.sections if s.type == section_type]


@dataclass
class QualityCheck:
    """Individual quality check result"""
    check_name: str
    passed: bool
    score: float  # 0.0 - 1.0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""
    factual_accuracy: QualityCheck
    content_structure: QualityCheck
    cultural_sensitivity: QualityCheck
    originality: QualityCheck
    source_attribution: QualityCheck
    overall_score: float
    passed: bool
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_failed_checks(self) -> List[QualityCheck]:
        """Get all failed quality checks"""
        checks = [
            self.factual_accuracy,
            self.content_structure,
            self.cultural_sensitivity,
            self.originality,
            self.source_attribution
        ]
        return [check for check in checks if not check.passed]
    
    def get_all_issues(self) -> List[str]:
        """Get all issues from all checks"""
        all_issues = []
        for check in [self.factual_accuracy, self.content_structure, 
                      self.cultural_sensitivity, self.originality, 
                      self.source_attribution]:
            all_issues.extend(check.issues)
        return all_issues


@dataclass
class NarrativeTemplate:
    """Base template for narrative construction"""
    name: str
    narrative_type: NarrativeType
    structure_pattern: List[str]
    pacing_guidelines: Dict[str, float]
    engagement_strategies: List[str]
    suitable_for: List[str]  # Content types this template works well with
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentIntegrationPoint:
    """Point where content is integrated into narrative"""
    position: int  # Position in narrative flow
    content_type: str  # Type of content (fact, story, description, etc.)
    content_data: Dict[str, Any]
    integration_style: str  # How to integrate (direct, paraphrased, summarized)
    emphasis_level: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """User profile for personalization"""
    user_id: str
    surprise_tolerance: int = 2  # 0-5 scale
    preferred_length: str = "medium"  # short, medium, long
    preferred_style: str = "balanced"  # casual, balanced, formal
    preferred_pace: str = "moderate"  # slow, moderate, fast
    interests: List[str] = field(default_factory=list)
    engagement_history: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
