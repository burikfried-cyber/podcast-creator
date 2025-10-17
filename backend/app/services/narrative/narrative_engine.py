"""
Narrative Intelligence Engine
Core engine for analyzing content and constructing compelling narratives
"""
import asyncio
from typing import Dict, List, Any, Optional
import structlog

from .models import (
    NarrativeType,
    ConstructedNarrative,
    NarrativeStructure,
    StoryElement,
    ScriptSection,
    UserProfile
)
from .templates import (
    ChronologicalRevelationTemplate,
    QuestionDrivenExplorationTemplate,
    TimelineBasedProgressionTemplate,
    ThemeBasedExplorationTemplate,
    StoryDrivenNarrativeTemplate
)
from app.services.content import WikipediaService, LocationService
from app.services.content.llm_singleton import get_llm_service

logger = structlog.get_logger()


class NarrativeIntelligenceEngine:
    """
    Core engine for narrative construction
    Analyzes content and builds compelling story structures
    """
    
    def __init__(self):
        # Initialize narrative templates
        self.narrative_templates = {
            'discovery_narrative': ChronologicalRevelationTemplate(),
            'mystery_narrative': QuestionDrivenExplorationTemplate(),
            'historical_narrative': TimelineBasedProgressionTemplate(),
            'cultural_narrative': ThemeBasedExplorationTemplate(),
            'personal_narrative': StoryDrivenNarrativeTemplate()
        }
        
        # Story element generators
        self.story_elements = {
            'hook': HookGenerator(),
            'transitions': TransitionGenerator(),
            'climax': ClimaxBuilder(),
            'conclusion': ConclusionGenerator()
        }
        
        # Initialize content services
        self.wikipedia = WikipediaService()
        self.location_service = LocationService()
        self.llm = get_llm_service(provider="perplexity")  # Use singleton!
    
    async def construct_narrative(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile,
        podcast_type: str
    ) -> ConstructedNarrative:
        """
        Main method to construct complete narrative
        
        Args:
            content_data: Content to build narrative from
            user_preferences: User preferences for personalization
            podcast_type: Type of podcast (base, standout, topic, personalized)
            
        Returns:
            ConstructedNarrative with complete story structure
        """
        logger.info("narrative_construction_started",
                   content_id=content_data.get('id'),
                   podcast_type=podcast_type)
        
        try:
            # Step 0: Fetch real content from Wikipedia and location services
            location = content_data.get('location', '')
            logger.info("fetching_real_content", location=location)
            
            # Fetch Wikipedia content
            wiki_content = await self.wikipedia.get_location_content(location)
            interesting_facts = await self.wikipedia.get_interesting_facts(wiki_content)
            
            # Fetch location details
            location_details = await self.location_service.get_location_details(location)
            
            # Merge real content into content_data
            content_data['wiki_content'] = wiki_content
            content_data['interesting_facts'] = interesting_facts
            content_data['location_details'] = location_details
            content_data['title'] = wiki_content.get('title', location)
            
            logger.info("real_content_fetched",
                       title=content_data['title'],
                       facts_count=len(interesting_facts))
            
            # Step 1: Analyze content for narrative potential
            narrative_analysis = await self.analyze_narrative_potential(content_data)
            
            # Step 2: Select optimal template
            template = await self.select_narrative_template(
                narrative_analysis,
                user_preferences,
                podcast_type
            )
            
            # Step 3: Build story structure
            story_structure = await template.build_structure(
                content_data,
                user_preferences
            )
            
            # Step 4: Generate story elements
            story_elements = await self.generate_story_elements(
                story_structure,
                content_data,
                user_preferences
            )
            
            # Step 5: Create narrative flow
            narrative_flow = await self.create_narrative_flow(
                story_structure,
                story_elements
            )
            
            # Step 6: Optimize for engagement
            optimized_narrative = await self.optimize_for_engagement(
                narrative_flow,
                user_preferences,
                content_data
            )
            
            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(
                optimized_narrative,
                narrative_analysis
            )
            
            # Calculate total duration
            total_duration = sum(
                element.timing_seconds for element in story_elements
            )
            
            constructed_narrative = ConstructedNarrative(
                narrative_type=story_structure.narrative_type,
                structure=story_structure,
                story_elements=story_elements,
                narrative_flow=optimized_narrative,
                engagement_score=engagement_score,
                estimated_duration_seconds=total_duration,
                metadata={
                    'content_id': content_data.get('id'),
                    'podcast_type': podcast_type,
                    'template_used': template.template.name,
                    'narrative_analysis': narrative_analysis
                }
            )
            
            logger.info("narrative_construction_complete",
                       content_id=content_data.get('id'),
                       engagement_score=engagement_score,
                       duration=total_duration)
            
            return constructed_narrative
            
        except Exception as e:
            logger.error("narrative_construction_failed",
                        content_id=content_data.get('id'),
                        error=str(e))
            raise
    
    async def analyze_narrative_potential(
        self,
        content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content to determine narrative potential and characteristics
        
        Returns:
            Analysis with narrative indicators, themes, and structure hints
        """
        analysis = {
            'has_timeline': False,
            'has_mystery': False,
            'has_personal_story': False,
            'has_cultural_themes': False,
            'has_historical_depth': False,
            'complexity_score': 0.0,
            'engagement_potential': 0.0,
            'recommended_templates': []
        }
        
        content_text = self._extract_content_text(content_data)
        
        # Analyze for timeline elements
        if self._has_temporal_markers(content_text):
            analysis['has_timeline'] = True
            analysis['recommended_templates'].append('discovery_narrative')
            analysis['recommended_templates'].append('historical_narrative')
        
        # Analyze for mystery elements
        if self._has_mystery_elements(content_text, content_data):
            analysis['has_mystery'] = True
            analysis['recommended_templates'].append('mystery_narrative')
        
        # Analyze for personal stories
        if self._has_personal_elements(content_text):
            analysis['has_personal_story'] = True
            analysis['recommended_templates'].append('personal_narrative')
        
        # Analyze for cultural themes
        if self._has_cultural_themes(content_text, content_data):
            analysis['has_cultural_themes'] = True
            analysis['recommended_templates'].append('cultural_narrative')
        
        # Analyze for historical depth
        if self._has_historical_depth(content_text, content_data):
            analysis['has_historical_depth'] = True
            analysis['recommended_templates'].append('historical_narrative')
        
        # Calculate complexity and engagement potential
        analysis['complexity_score'] = self._calculate_complexity(content_data)
        analysis['engagement_potential'] = self._calculate_engagement_potential(
            content_data,
            analysis
        )
        
        return analysis
    
    async def select_narrative_template(
        self,
        narrative_analysis: Dict[str, Any],
        user_preferences: UserProfile,
        podcast_type: str
    ) -> Any:
        """
        Select optimal narrative template based on analysis and preferences
        """
        # Get recommended templates from analysis
        recommended = narrative_analysis.get('recommended_templates', [])
        
        # Apply podcast type preferences
        if podcast_type == 'standout_podcast' and 'mystery_narrative' in recommended:
            return self.narrative_templates['mystery_narrative']
        
        if podcast_type == 'base_podcast' and 'discovery_narrative' in recommended:
            return self.narrative_templates['discovery_narrative']
        
        # Apply user preferences
        if user_preferences.surprise_tolerance >= 4 and 'mystery_narrative' in recommended:
            return self.narrative_templates['mystery_narrative']
        
        # Default selection based on content characteristics
        if narrative_analysis.get('has_mystery'):
            return self.narrative_templates['mystery_narrative']
        elif narrative_analysis.get('has_historical_depth'):
            return self.narrative_templates['historical_narrative']
        elif narrative_analysis.get('has_cultural_themes'):
            return self.narrative_templates['cultural_narrative']
        elif narrative_analysis.get('has_personal_story'):
            return self.narrative_templates['personal_narrative']
        else:
            # Default to chronological revelation
            return self.narrative_templates['discovery_narrative']
    
    async def generate_story_elements(
        self,
        story_structure: NarrativeStructure,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> List[StoryElement]:
        """
        Generate individual story elements (hook, transitions, climax, etc.)
        """
        elements = []
        
        # Generate hook
        hook = await self.story_elements['hook'].generate(
            content_data,
            story_structure,
            user_preferences
        )
        elements.append(hook)
        
        # Generate main content elements based on story arc
        for i, arc_point in enumerate(story_structure.story_arc):
            element = StoryElement(
                type=ScriptSection.MAIN_CONTENT,
                content=arc_point,
                timing_seconds=self._calculate_element_duration(
                    story_structure,
                    i,
                    user_preferences
                ),
                emphasis_level=self._determine_emphasis(i, story_structure),
                metadata={'arc_position': i, 'arc_point': arc_point}
            )
            elements.append(element)
            
            # Add transition between elements (except after last)
            if i < len(story_structure.story_arc) - 1:
                transition = await self.story_elements['transitions'].generate(
                    arc_point,
                    story_structure.story_arc[i + 1],
                    user_preferences
                )
                elements.append(transition)
        
        # Generate climax
        climax = await self.story_elements['climax'].build(
            content_data,
            story_structure,
            user_preferences
        )
        elements.append(climax)
        
        # Generate conclusion
        conclusion = await self.story_elements['conclusion'].generate(
            content_data,
            story_structure,
            user_preferences
        )
        elements.append(conclusion)
        
        return elements
    
    async def create_narrative_flow(
        self,
        story_structure: NarrativeStructure,
        story_elements: List[StoryElement]
    ) -> List[Dict[str, Any]]:
        """
        Create cohesive narrative flow from structure and elements
        """
        narrative_flow = []
        
        for i, element in enumerate(story_elements):
            flow_point = {
                'position': i,
                'element': element,
                'timing': {
                    'start': sum(e.timing_seconds for e in story_elements[:i]),
                    'duration': element.timing_seconds,
                    'end': sum(e.timing_seconds for e in story_elements[:i+1])
                },
                'pacing': self._determine_pacing(element, story_structure),
                'engagement_level': self._calculate_element_engagement(element),
                'transitions': {
                    'from_previous': i > 0,
                    'to_next': i < len(story_elements) - 1
                }
            }
            narrative_flow.append(flow_point)
        
        return narrative_flow
    
    async def optimize_for_engagement(
        self,
        narrative_flow: List[Dict[str, Any]],
        user_preferences: UserProfile,
        content_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Optimize narrative flow for maximum user engagement
        """
        optimized_flow = []
        
        for flow_point in narrative_flow:
            # Apply user preference optimizations
            if user_preferences.surprise_tolerance >= 3:
                # Increase emphasis on surprising elements
                if flow_point['element'].type in [ScriptSection.CLIMAX, ScriptSection.HOOK]:
                    flow_point['element'].emphasis_level = min(
                        flow_point['element'].emphasis_level + 1,
                        5
                    )
            
            # Adjust pacing based on user preference
            if user_preferences.preferred_pace == 'fast':
                flow_point['pacing'] = min(flow_point['pacing'] * 1.2, 2.0)
            elif user_preferences.preferred_pace == 'slow':
                flow_point['pacing'] = max(flow_point['pacing'] * 0.8, 0.5)
            
            # Add engagement hooks at strategic points
            if self._is_strategic_point(flow_point, narrative_flow):
                flow_point['engagement_hook'] = self._generate_engagement_hook(
                    flow_point,
                    content_data
                )
            
            optimized_flow.append(flow_point)
        
        return optimized_flow
    
    # Helper methods
    
    def _extract_content_text(self, content_data: Dict[str, Any]) -> str:
        """Extract text content for analysis"""
        parts = []
        if 'title' in content_data:
            parts.append(content_data['title'])
        if 'content' in content_data:
            parts.append(content_data['content'])
        if 'description' in content_data:
            parts.append(content_data['description'])
        return ' '.join(parts)
    
    def _has_temporal_markers(self, text: str) -> bool:
        """Check for temporal markers in text"""
        temporal_words = [
            'ancient', 'historical', 'century', 'year', 'ago',
            'timeline', 'evolution', 'development', 'originated'
        ]
        text_lower = text.lower()
        return any(word in text_lower for word in temporal_words)
    
    def _has_mystery_elements(
        self,
        text: str,
        content_data: Dict[str, Any]
    ) -> bool:
        """Check for mystery elements"""
        mystery_words = [
            'mystery', 'unknown', 'unexplained', 'mysterious',
            'enigma', 'puzzle', 'confounding', 'baffling'
        ]
        text_lower = text.lower()
        
        # Check text
        has_mystery_words = any(word in text_lower for word in mystery_words)
        
        # Check if content has high standout score (indicates unusual/mysterious)
        has_standout = content_data.get('standout_score', 0) > 5.0
        
        return has_mystery_words or has_standout
    
    def _has_personal_elements(self, text: str) -> bool:
        """Check for personal story elements"""
        personal_words = [
            'story', 'people', 'person', 'family', 'community',
            'lived', 'experience', 'journey', 'life'
        ]
        text_lower = text.lower()
        return sum(1 for word in personal_words if word in text_lower) >= 2
    
    def _has_cultural_themes(
        self,
        text: str,
        content_data: Dict[str, Any]
    ) -> bool:
        """Check for cultural themes"""
        cultural_words = [
            'culture', 'cultural', 'tradition', 'heritage',
            'indigenous', 'ritual', 'ceremony', 'custom'
        ]
        text_lower = text.lower()
        
        # Check text
        has_cultural_words = any(word in text_lower for word in cultural_words)
        
        # Check if cultural detector scored high
        method_scores = content_data.get('method_scores', {})
        has_cultural_score = method_scores.get('cultural', 0) > 3.0
        
        return has_cultural_words or has_cultural_score
    
    def _has_historical_depth(
        self,
        text: str,
        content_data: Dict[str, Any]
    ) -> bool:
        """Check for historical depth"""
        historical_words = [
            'historical', 'history', 'ancient', 'medieval',
            'prehistoric', 'archaeological', 'heritage'
        ]
        text_lower = text.lower()
        
        # Check text
        has_historical_words = any(word in text_lower for word in historical_words)
        
        # Check if historical detector scored high
        method_scores = content_data.get('method_scores', {})
        has_historical_score = method_scores.get('historical', 0) > 3.0
        
        return has_historical_words or has_historical_score
    
    def _calculate_complexity(self, content_data: Dict[str, Any]) -> float:
        """Calculate content complexity score"""
        # Simple heuristic based on content length and structure
        text = self._extract_content_text(content_data)
        word_count = len(text.split())
        
        # Normalize to 0-1 scale
        complexity = min(word_count / 1000, 1.0)
        return complexity
    
    def _calculate_engagement_potential(
        self,
        content_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> float:
        """Calculate engagement potential score"""
        score = 0.0
        
        # Bonus for mystery elements
        if analysis.get('has_mystery'):
            score += 0.3
        
        # Bonus for personal stories
        if analysis.get('has_personal_story'):
            score += 0.2
        
        # Bonus for cultural themes
        if analysis.get('has_cultural_themes'):
            score += 0.2
        
        # Bonus for historical depth
        if analysis.get('has_historical_depth'):
            score += 0.15
        
        # Bonus for standout content
        if content_data.get('standout_score', 0) > 5.0:
            score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_element_duration(
        self,
        story_structure: NarrativeStructure,
        element_index: int,
        user_preferences: UserProfile
    ) -> float:
        """Calculate duration for a story element"""
        # Get total estimated duration
        duration_map = {
            'short': 300,
            'medium': 600,
            'long': 900
        }
        total_duration = duration_map.get(user_preferences.preferred_length, 600)
        
        # Distribute duration based on pacing profile
        num_elements = len(story_structure.story_arc)
        base_duration = total_duration / num_elements
        
        return base_duration
    
    def _determine_emphasis(
        self,
        position: int,
        story_structure: NarrativeStructure
    ) -> int:
        """Determine emphasis level for element"""
        # Check if this is a key moment
        for key_moment in story_structure.key_moments:
            if key_moment.get('position') == position:
                return key_moment.get('emphasis', 3)
        
        # Default emphasis based on position
        if position == 0:  # Opening
            return 4
        elif position == len(story_structure.story_arc) - 1:  # Closing
            return 4
        else:
            return 2
    
    def _determine_pacing(
        self,
        element: StoryElement,
        story_structure: NarrativeStructure
    ) -> float:
        """Determine pacing for element (0.5 = slow, 1.0 = normal, 2.0 = fast)"""
        if element.type == ScriptSection.HOOK:
            return 1.2  # Slightly faster to grab attention
        elif element.type == ScriptSection.CLIMAX:
            return 1.5  # Faster for excitement
        elif element.type == ScriptSection.CONCLUSION:
            return 0.9  # Slower for reflection
        else:
            return 1.0  # Normal pace
    
    def _calculate_element_engagement(self, element: StoryElement) -> float:
        """Calculate engagement level for element"""
        # Base engagement on element type and emphasis
        base_engagement = {
            ScriptSection.HOOK: 0.9,
            ScriptSection.CLIMAX: 0.95,
            ScriptSection.MAIN_CONTENT: 0.7,
            ScriptSection.TRANSITION: 0.5,
            ScriptSection.CONCLUSION: 0.8
        }.get(element.type, 0.6)
        
        # Adjust for emphasis level
        emphasis_bonus = (element.emphasis_level - 1) * 0.05
        
        return min(base_engagement + emphasis_bonus, 1.0)
    
    def _is_strategic_point(
        self,
        flow_point: Dict[str, Any],
        narrative_flow: List[Dict[str, Any]]
    ) -> bool:
        """Check if this is a strategic point for engagement hook"""
        position = flow_point['position']
        total_points = len(narrative_flow)
        
        # Add hooks at 25%, 50%, 75% points
        strategic_positions = [
            int(total_points * 0.25),
            int(total_points * 0.50),
            int(total_points * 0.75)
        ]
        
        return position in strategic_positions
    
    def _generate_engagement_hook(
        self,
        flow_point: Dict[str, Any],
        content_data: Dict[str, Any]
    ) -> str:
        """Generate engagement hook for strategic point"""
        hooks = [
            "But here's where it gets interesting...",
            "You won't believe what happens next...",
            "This is the fascinating part...",
            "Here's the surprising twist..."
        ]
        # Simple selection - could be more sophisticated
        return hooks[flow_point['position'] % len(hooks)]
    
    def _calculate_engagement_score(
        self,
        narrative_flow: List[Dict[str, Any]],
        narrative_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall engagement score for narrative"""
        # Average engagement across all flow points
        avg_engagement = sum(
            point['engagement_level'] for point in narrative_flow
        ) / len(narrative_flow)
        
        # Bonus for high engagement potential
        potential_bonus = narrative_analysis.get('engagement_potential', 0) * 0.2
        
        return min(avg_engagement + potential_bonus, 1.0)


# Story element generators

class HookGenerator:
    """Generate compelling hooks"""
    
    def __init__(self):
        self.llm = get_llm_service(provider="perplexity")
    
    async def generate(
        self,
        content_data: Dict[str, Any],
        story_structure: NarrativeStructure,
        user_preferences: UserProfile
    ) -> StoryElement:
        """Generate hook element using LLM"""
        # Use LLM to generate hook
        hook_text = await self.llm.generate_hook(
            content_data,
            story_structure.narrative_type.value
        )
        
        return StoryElement(
            type=ScriptSection.HOOK,
            content=hook_text,
            timing_seconds=15.0,
            emphasis_level=5,
            metadata={'hook_style': story_structure.narrative_type.value}
        )


class TransitionGenerator:
    """Generate smooth transitions"""
    
    async def generate(
        self,
        from_point: str,
        to_point: str,
        user_preferences: UserProfile
    ) -> StoryElement:
        """Generate transition element"""
        transitions = [
            "Moving forward...",
            "But that's not all...",
            "Let's explore further...",
            "This leads us to...",
            "Now, here's the interesting part..."
        ]
        
        # Simple selection - could be context-aware
        transition_text = transitions[0]
        
        return StoryElement(
            type=ScriptSection.TRANSITION,
            content=transition_text,
            timing_seconds=3.0,  # Transitions are brief
            emphasis_level=1,
            metadata={'from': from_point, 'to': to_point}
        )


class ClimaxBuilder:
    """Build narrative climax"""
    
    async def build(
        self,
        content_data: Dict[str, Any],
        story_structure: NarrativeStructure,
        user_preferences: UserProfile
    ) -> StoryElement:
        """Build climax element"""
        # Find the most engaging fact or revelation
        climax_text = "And here's the most remarkable part of all..."
        
        return StoryElement(
            type=ScriptSection.CLIMAX,
            content=climax_text,
            timing_seconds=30.0,  # Climax gets more time
            emphasis_level=5,
            metadata={'is_climax': True}
        )


class ConclusionGenerator:
    """Generate satisfying conclusions"""
    
    def __init__(self):
        self.llm = get_llm_service(provider="perplexity")
    
    async def generate(
        self,
        content_data: Dict[str, Any],
        story_structure: NarrativeStructure,
        user_preferences: UserProfile
    ) -> StoryElement:
        """Generate conclusion element using LLM"""
        # Use LLM to generate conclusion
        conclusion_text = await self.llm.generate_conclusion(
            content_data,
            story_structure.narrative_type.value
        )
        
        return StoryElement(
            type=ScriptSection.CONCLUSION,
            content=conclusion_text,
            timing_seconds=20.0,
            emphasis_level=4,
            metadata={'is_conclusion': True}
        )
