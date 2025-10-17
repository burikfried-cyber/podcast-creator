"""
Narrative templates for different story structures
"""
from typing import Dict, List, Any
from abc import ABC, abstractmethod

from .models import (
    NarrativeType,
    NarrativeStructure,
    NarrativeTemplate,
    UserProfile,
    StoryElement,
    ScriptSection
)


class BaseNarrativeTemplate(ABC):
    """Base class for narrative templates"""
    
    def __init__(self):
        self.template = self._define_template()
    
    @abstractmethod
    def _define_template(self) -> NarrativeTemplate:
        """Define the template structure"""
        pass
    
    @abstractmethod
    async def build_structure(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> NarrativeStructure:
        """Build narrative structure from content and preferences"""
        pass
    
    def _calculate_pacing(
        self,
        total_duration: float,
        user_preferences: UserProfile
    ) -> Dict[str, float]:
        """Calculate section durations based on pacing preferences"""
        # Adjust base pacing based on user preference
        pace_multipliers = {
            "slow": 1.2,
            "moderate": 1.0,
            "fast": 0.8
        }
        multiplier = pace_multipliers.get(user_preferences.preferred_pace, 1.0)
        
        # Apply multiplier to template pacing
        return {
            section: duration * multiplier
            for section, duration in self.template.pacing_guidelines.items()
        }


class ChronologicalRevelationTemplate(BaseNarrativeTemplate):
    """Progressive disclosure of information over time"""
    
    def _define_template(self) -> NarrativeTemplate:
        return NarrativeTemplate(
            name="Chronological Revelation",
            narrative_type=NarrativeType.DISCOVERY,
            structure_pattern=[
                "intriguing_hook",
                "historical_context",
                "early_development",
                "key_turning_point",
                "modern_significance",
                "surprising_conclusion"
            ],
            pacing_guidelines={
                "hook": 0.10,  # 10% of total time
                "context": 0.15,
                "development": 0.30,
                "turning_point": 0.20,
                "significance": 0.15,
                "conclusion": 0.10
            },
            engagement_strategies=[
                "reveal_information_gradually",
                "build_anticipation",
                "connect_past_to_present",
                "highlight_unexpected_developments"
            ],
            suitable_for=["historical", "cultural", "discovery"]
        )
    
    async def build_structure(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> NarrativeStructure:
        """Build chronological narrative structure"""
        
        # Extract timeline from content
        timeline_events = self._extract_timeline(content_data)
        
        # Create story arc following chronological order
        story_arc = [
            f"Discovery of {content_data.get('title', 'phenomenon')}",
            "Historical origins and early development",
            "Key moments that shaped its evolution",
            "Turning points and transformations",
            "Current state and modern relevance",
            "Surprising facts and future implications"
        ]
        
        # Identify key moments for emphasis
        key_moments = self._identify_key_moments(timeline_events, content_data)
        
        # Calculate pacing
        estimated_duration = self._estimate_duration(user_preferences)
        pacing_profile = self._calculate_pacing(estimated_duration, user_preferences)
        
        # Generate engagement hooks
        engagement_hooks = [
            f"Did you know that {content_data.get('title')} has a surprising origin?",
            "The story begins centuries ago...",
            "But here's where it gets interesting...",
            "Fast forward to today..."
        ]
        
        return NarrativeStructure(
            narrative_type=NarrativeType.DISCOVERY,
            story_arc=story_arc,
            key_moments=key_moments,
            pacing_profile=pacing_profile,
            engagement_hooks=engagement_hooks,
            metadata={
                "timeline_events": len(timeline_events),
                "estimated_duration": estimated_duration
            }
        )
    
    def _extract_timeline(self, content_data: Dict[str, Any]) -> List[Dict]:
        """Extract timeline events from content"""
        # Placeholder - would analyze content for temporal markers
        return []
    
    def _identify_key_moments(
        self,
        timeline_events: List[Dict],
        content_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify key moments for emphasis"""
        return [
            {"type": "origin", "emphasis": 3},
            {"type": "transformation", "emphasis": 4},
            {"type": "modern_relevance", "emphasis": 3}
        ]
    
    def _estimate_duration(self, user_preferences: UserProfile) -> float:
        """Estimate total duration based on user preferences"""
        duration_map = {
            "short": 300,   # 5 minutes
            "medium": 600,  # 10 minutes
            "long": 900     # 15 minutes
        }
        return duration_map.get(user_preferences.preferred_length, 600)


class QuestionDrivenExplorationTemplate(BaseNarrativeTemplate):
    """Pose intriguing questions and reveal answers"""
    
    def _define_template(self) -> NarrativeTemplate:
        return NarrativeTemplate(
            name="Question-Driven Exploration",
            narrative_type=NarrativeType.MYSTERY,
            structure_pattern=[
                "mysterious_hook",
                "central_question",
                "investigation_clues",
                "deeper_mysteries",
                "revelation",
                "implications"
            ],
            pacing_guidelines={
                "hook": 0.08,
                "question": 0.12,
                "clues": 0.35,
                "mysteries": 0.20,
                "revelation": 0.15,
                "implications": 0.10
            },
            engagement_strategies=[
                "pose_intriguing_questions",
                "reveal_clues_gradually",
                "build_mystery",
                "deliver_satisfying_answers"
            ],
            suitable_for=["mystery", "standout", "unusual"]
        )
    
    async def build_structure(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> NarrativeStructure:
        """Build question-driven narrative structure"""
        
        # Generate central questions
        central_questions = self._generate_questions(content_data)
        
        story_arc = [
            f"What makes {content_data.get('title')} so unusual?",
            "Let's investigate the mystery...",
            "Here's what we discovered...",
            "But that's not the whole story...",
            "The answer is more fascinating than you'd think...",
            "And here's why it matters..."
        ]
        
        key_moments = [
            {"type": "question_posed", "emphasis": 4},
            {"type": "clue_revealed", "emphasis": 3},
            {"type": "answer_revealed", "emphasis": 5}
        ]
        
        estimated_duration = self._estimate_duration(user_preferences)
        pacing_profile = self._calculate_pacing(estimated_duration, user_preferences)
        
        engagement_hooks = central_questions
        
        return NarrativeStructure(
            narrative_type=NarrativeType.MYSTERY,
            story_arc=story_arc,
            key_moments=key_moments,
            pacing_profile=pacing_profile,
            engagement_hooks=engagement_hooks,
            metadata={"questions_count": len(central_questions)}
        )
    
    def _generate_questions(self, content_data: Dict[str, Any]) -> List[str]:
        """Generate intriguing questions from content"""
        return [
            f"Why is {content_data.get('title')} so unique?",
            "How did this come to be?",
            "What makes it different from anything else?"
        ]
    
    def _estimate_duration(self, user_preferences: UserProfile) -> float:
        duration_map = {
            "short": 300,
            "medium": 600,
            "long": 900
        }
        return duration_map.get(user_preferences.preferred_length, 600)


class TimelineBasedProgressionTemplate(BaseNarrativeTemplate):
    """Historical development and evolution"""
    
    def _define_template(self) -> NarrativeTemplate:
        return NarrativeTemplate(
            name="Timeline-Based Progression",
            narrative_type=NarrativeType.HISTORICAL,
            structure_pattern=[
                "historical_hook",
                "ancient_origins",
                "medieval_development",
                "modern_transformation",
                "current_state",
                "future_outlook"
            ],
            pacing_guidelines={
                "hook": 0.08,
                "origins": 0.20,
                "development": 0.25,
                "transformation": 0.22,
                "current": 0.15,
                "future": 0.10
            },
            engagement_strategies=[
                "connect_across_time_periods",
                "highlight_evolution",
                "show_continuity_and_change",
                "relate_past_to_present"
            ],
            suitable_for=["historical", "cultural", "evolutionary"]
        )
    
    async def build_structure(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> NarrativeStructure:
        """Build timeline-based narrative structure"""
        
        story_arc = [
            f"The ancient origins of {content_data.get('title')}",
            "How it evolved through the centuries",
            "Major transformations and turning points",
            "Its role in modern times",
            "What the future might hold"
        ]
        
        key_moments = [
            {"type": "origin_point", "emphasis": 4},
            {"type": "major_change", "emphasis": 4},
            {"type": "modern_relevance", "emphasis": 3}
        ]
        
        estimated_duration = self._estimate_duration(user_preferences)
        pacing_profile = self._calculate_pacing(estimated_duration, user_preferences)
        
        engagement_hooks = [
            "Travel back in time with us...",
            "Centuries ago...",
            "Through the ages...",
            "Today, we see..."
        ]
        
        return NarrativeStructure(
            narrative_type=NarrativeType.HISTORICAL,
            story_arc=story_arc,
            key_moments=key_moments,
            pacing_profile=pacing_profile,
            engagement_hooks=engagement_hooks
        )
    
    def _estimate_duration(self, user_preferences: UserProfile) -> float:
        duration_map = {
            "short": 300,
            "medium": 600,
            "long": 900
        }
        return duration_map.get(user_preferences.preferred_length, 600)


class ThemeBasedExplorationTemplate(BaseNarrativeTemplate):
    """Explore interconnected themes and concepts"""
    
    def _define_template(self) -> NarrativeTemplate:
        return NarrativeTemplate(
            name="Theme-Based Exploration",
            narrative_type=NarrativeType.CULTURAL,
            structure_pattern=[
                "thematic_hook",
                "core_theme_introduction",
                "theme_exploration",
                "interconnections",
                "deeper_meaning",
                "universal_relevance"
            ],
            pacing_guidelines={
                "hook": 0.10,
                "introduction": 0.15,
                "exploration": 0.30,
                "interconnections": 0.20,
                "meaning": 0.15,
                "relevance": 0.10
            },
            engagement_strategies=[
                "explore_multiple_perspectives",
                "show_interconnections",
                "reveal_deeper_meanings",
                "connect_to_universal_themes"
            ],
            suitable_for=["cultural", "thematic", "conceptual"]
        )
    
    async def build_structure(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> NarrativeStructure:
        """Build theme-based narrative structure"""
        
        themes = self._extract_themes(content_data)
        
        story_arc = [
            f"Exploring the themes of {content_data.get('title')}",
            "The central cultural significance",
            "How these themes interconnect",
            "Deeper meanings and symbolism",
            "Universal human connections"
        ]
        
        key_moments = [
            {"type": "theme_introduction", "emphasis": 3},
            {"type": "connection_revealed", "emphasis": 4},
            {"type": "universal_meaning", "emphasis": 4}
        ]
        
        estimated_duration = self._estimate_duration(user_preferences)
        pacing_profile = self._calculate_pacing(estimated_duration, user_preferences)
        
        engagement_hooks = [
            f"What does {content_data.get('title')} tell us about culture?",
            "Let's explore the deeper meanings...",
            "These themes connect in surprising ways..."
        ]
        
        return NarrativeStructure(
            narrative_type=NarrativeType.CULTURAL,
            story_arc=story_arc,
            key_moments=key_moments,
            pacing_profile=pacing_profile,
            engagement_hooks=engagement_hooks,
            metadata={"themes": themes}
        )
    
    def _extract_themes(self, content_data: Dict[str, Any]) -> List[str]:
        """Extract themes from content"""
        return ["tradition", "identity", "community", "heritage"]
    
    def _estimate_duration(self, user_preferences: UserProfile) -> float:
        duration_map = {
            "short": 300,
            "medium": 600,
            "long": 900
        }
        return duration_map.get(user_preferences.preferred_length, 600)


class StoryDrivenNarrativeTemplate(BaseNarrativeTemplate):
    """Personal stories and human experiences"""
    
    def _define_template(self) -> NarrativeTemplate:
        return NarrativeTemplate(
            name="Story-Driven Narrative",
            narrative_type=NarrativeType.PERSONAL,
            structure_pattern=[
                "personal_hook",
                "character_introduction",
                "journey_begins",
                "challenges_and_growth",
                "transformation",
                "lasting_impact"
            ],
            pacing_guidelines={
                "hook": 0.10,
                "introduction": 0.15,
                "journey": 0.25,
                "challenges": 0.25,
                "transformation": 0.15,
                "impact": 0.10
            },
            engagement_strategies=[
                "focus_on_human_stories",
                "build_emotional_connection",
                "show_personal_transformation",
                "highlight_universal_experiences"
            ],
            suitable_for=["personal", "biographical", "experiential"]
        )
    
    async def build_structure(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> NarrativeStructure:
        """Build story-driven narrative structure"""
        
        story_arc = [
            f"Meet the people behind {content_data.get('title')}",
            "Their journey begins...",
            "Challenges they faced",
            "How they overcame obstacles",
            "The transformation that followed",
            "The lasting impact on their lives"
        ]
        
        key_moments = [
            {"type": "character_intro", "emphasis": 3},
            {"type": "challenge", "emphasis": 4},
            {"type": "transformation", "emphasis": 5}
        ]
        
        estimated_duration = self._estimate_duration(user_preferences)
        pacing_profile = self._calculate_pacing(estimated_duration, user_preferences)
        
        engagement_hooks = [
            "This is a story about real people...",
            "Their journey was anything but ordinary...",
            "What happened next changed everything..."
        ]
        
        return NarrativeStructure(
            narrative_type=NarrativeType.PERSONAL,
            story_arc=story_arc,
            key_moments=key_moments,
            pacing_profile=pacing_profile,
            engagement_hooks=engagement_hooks
        )
    
    def _estimate_duration(self, user_preferences: UserProfile) -> float:
        duration_map = {
            "short": 300,
            "medium": 600,
            "long": 900
        }
        return duration_map.get(user_preferences.preferred_length, 600)
