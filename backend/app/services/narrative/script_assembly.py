"""
Script Assembly Engine
Assembles complete podcast scripts from narratives and content
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from .models import (
    PodcastType,
    PodcastScript,
    ConstructedNarrative,
    StoryElement,
    ScriptSection,
    TTSMarker,
    UserProfile
)
from app.services.content.llm_singleton import get_llm_service

logger = structlog.get_logger()


class ScriptAssemblyEngine:
    """
    Assembles complete podcast scripts from constructed narratives
    Integrates content, applies styling, and optimizes for TTS
    """
    
    def __init__(self):
        # Content integrators for different podcast types
        self.content_integrators = {
            'base_podcast': BasePodcastIntegrator(),
            'standout_podcast': StandoutPodcastIntegrator(),
            'topic_podcast': TopicPodcastIntegrator(),
            'personalized_podcast': PersonalizedPodcastIntegrator()
        }
        
        # Initialize LLM for content generation (singleton)
        self.llm = get_llm_service(provider="perplexity")
    
    async def assemble_podcast_script(
        self,
        narrative: ConstructedNarrative,
        content_data: Dict[str, Any],
        podcast_type: str,
        user_preferences: UserProfile
    ) -> PodcastScript:
        """
        Main method to assemble complete podcast script
        
        Args:
            narrative: Constructed narrative structure
            content_data: Source content to integrate
            podcast_type: Type of podcast (base, standout, topic, personalized)
            user_preferences: User preferences for styling
            
        Returns:
            Complete PodcastScript ready for TTS
        """
        logger.info("script_assembly_started",
                   content_id=content_data.get('id'),
                   podcast_type=podcast_type)
        
        try:
            # Get appropriate integrator
            integrator = self.content_integrators.get(
                podcast_type,
                self.content_integrators['base_podcast']
            )
            
            # Step 1: Create structured script foundation
            script_structure = await integrator.create_structure(
                narrative,
                user_preferences
            )
            
            # Step 2: Integrate content at optimal narrative points
            content_integrated = await integrator.integrate_content(
                script_structure,
                content_data,
                narrative
            )
            
            # Step 3: Add narrative connectors and smooth transitions
            connected_script = await self.add_narrative_connectors(
                content_integrated,
                narrative
            )
            
            # Step 4: Apply user's preferred style and tone
            styled_script = await self.apply_style_preferences(
                connected_script,
                user_preferences
            )
            
            # Step 5: Optimize for TTS synthesis
            tts_optimized = await self.optimize_for_tts(styled_script)
            
            # Step 6: Generate metadata and timing cues
            metadata = self.generate_metadata(content_data, narrative)
            timing_cues = self.generate_timing_cues(tts_optimized)
            
            # Step 7: Assess script quality
            quality_score = await self.assess_script_quality(
                tts_optimized,
                narrative
            )
            
            # Generate title and description
            location = content_data.get('location', 'Unknown Location')
            title = f"Discover {location}"
            description = f"An engaging podcast exploring the fascinating stories and secrets of {location}"
            
            # Build final podcast script
            podcast_script = PodcastScript(
                podcast_type=PodcastType(podcast_type),
                content=tts_optimized['full_text'],
                sections=tts_optimized['sections'],
                tts_markers=tts_optimized['tts_markers'],
                timing_cues=timing_cues,
                metadata=metadata,
                quality_score=quality_score,
                estimated_duration_seconds=narrative.estimated_duration_seconds,
                title=title,
                description=description
            )
            
            logger.info("script_assembly_complete",
                       content_id=content_data.get('id'),
                       quality_score=quality_score,
                       word_count=len(tts_optimized['full_text'].split()))
            
            return podcast_script
            
        except Exception as e:
            logger.error("script_assembly_failed",
                        content_id=content_data.get('id'),
                        error=str(e))
            raise
    
    async def add_narrative_connectors(
        self,
        script_structure: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> Dict[str, Any]:
        """
        Add narrative connectors and smooth transitions between sections
        """
        connected = {
            'sections': [],
            'connectors': []
        }
        
        sections = script_structure['sections']
        
        for i, section in enumerate(sections):
            # Add the section
            connected['sections'].append(section)
            
            # Add connector before next section (except after last)
            if i < len(sections) - 1:
                connector = self._generate_connector(
                    section,
                    sections[i + 1],
                    narrative
                )
                connected['connectors'].append(connector)
                connected['sections'].append(connector)
        
        return connected
    
    async def apply_style_preferences(
        self,
        script_structure: Dict[str, Any],
        user_preferences: UserProfile
    ) -> Dict[str, Any]:
        """
        Apply user's preferred style and tone to the script
        """
        style = user_preferences.preferred_style
        
        styled_sections = []
        
        for section in script_structure['sections']:
            styled_content = self._apply_style_to_text(
                section.content,
                style
            )
            
            # Create new section with styled content
            styled_section = StoryElement(
                type=section.type,
                content=styled_content,
                timing_seconds=section.timing_seconds,
                emphasis_level=section.emphasis_level,
                tts_markers=section.tts_markers.copy(),
                metadata=section.metadata.copy()
            )
            
            styled_sections.append(styled_section)
        
        return {
            'sections': styled_sections,
            'style_applied': style
        }
    
    async def optimize_for_tts(
        self,
        script_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize script for Text-to-Speech synthesis
        Adds pronunciation guides, pause markers, emphasis markers
        """
        tts_markers = []
        optimized_sections = []
        full_text_parts = []
        char_position = 0
        
        for section in script_structure['sections']:
            # Process section content for TTS
            optimized_content, section_markers = self._optimize_text_for_tts(
                section.content,
                char_position
            )
            
            # Update character position
            char_position += len(optimized_content) + 1  # +1 for space
            
            # Add section markers to global list
            tts_markers.extend(section_markers)
            
            # Add pause after sections
            if section.type in [ScriptSection.HOOK, ScriptSection.CONCLUSION]:
                tts_markers.append(TTSMarker(
                    position=char_position,
                    type='pause',
                    value=1.0,  # 1 second pause
                    metadata={'reason': 'section_end'}
                ))
            
            # Create optimized section
            optimized_section = StoryElement(
                type=section.type,
                content=optimized_content,
                timing_seconds=section.timing_seconds,
                emphasis_level=section.emphasis_level,
                tts_markers=section.tts_markers.copy(),
                metadata=section.metadata.copy()
            )
            
            optimized_sections.append(optimized_section)
            full_text_parts.append(optimized_content)
        
        return {
            'sections': optimized_sections,
            'tts_markers': tts_markers,
            'full_text': ' '.join(full_text_parts)
        }
    
    def generate_metadata(
        self,
        content_data: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> Dict[str, Any]:
        """Generate comprehensive metadata for the script"""
        return {
            'content_id': content_data.get('id'),
            'title': content_data.get('title'),
            'narrative_type': narrative.narrative_type.value,
            'engagement_score': narrative.engagement_score,
            'estimated_duration': narrative.estimated_duration_seconds,
            'num_sections': len(narrative.story_elements),
            'generated_at': datetime.utcnow().isoformat(),
            'source_content': {
                'location': content_data.get('location'),
                'standout_score': content_data.get('standout_score'),
                'tier': content_data.get('tier')
            }
        }
    
    def generate_timing_cues(
        self,
        optimized_script: Dict[str, Any]
    ) -> Dict[str, float]:
        """Generate timing cues for each section"""
        timing_cues = {}
        current_time = 0.0
        
        for i, section in enumerate(optimized_script['sections']):
            section_key = f"section_{i}_{section.type.value}"
            timing_cues[section_key] = {
                'start': current_time,
                'duration': section.timing_seconds,
                'end': current_time + section.timing_seconds
            }
            current_time += section.timing_seconds
        
        timing_cues['total_duration'] = current_time
        
        return timing_cues
    
    async def assess_script_quality(
        self,
        optimized_script: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> float:
        """
        Assess overall script quality
        Returns score 0.0-1.0
        """
        scores = []
        
        # 1. Narrative coherence (based on engagement score)
        scores.append(narrative.engagement_score)
        
        # 2. Content completeness (all sections present)
        required_sections = {ScriptSection.HOOK, ScriptSection.CONCLUSION}
        present_sections = {s.type for s in optimized_script['sections']}
        completeness = len(required_sections & present_sections) / len(required_sections)
        scores.append(completeness)
        
        # 3. Length appropriateness (not too short, not too long)
        word_count = len(optimized_script['full_text'].split())
        ideal_range = (500, 2000)  # 5-15 minutes at ~150 words/min
        if ideal_range[0] <= word_count <= ideal_range[1]:
            length_score = 1.0
        elif word_count < ideal_range[0]:
            length_score = word_count / ideal_range[0]
        else:
            length_score = ideal_range[1] / word_count
        scores.append(length_score)
        
        # 4. TTS optimization (markers present)
        tts_score = min(len(optimized_script['tts_markers']) / 10, 1.0)
        scores.append(tts_score)
        
        # Average all scores
        return sum(scores) / len(scores)
    
    # Helper methods
    
    def _generate_connector(
        self,
        from_section: StoryElement,
        to_section: StoryElement,
        narrative: ConstructedNarrative
    ) -> StoryElement:
        """Generate connector between sections"""
        connectors = [
            "Let's continue...",
            "Now, here's what's fascinating...",
            "Moving on...",
            "This brings us to...",
            "And here's where it gets interesting..."
        ]
        
        # Simple selection - could be more sophisticated
        connector_text = connectors[0]
        
        return StoryElement(
            type=ScriptSection.TRANSITION,
            content=connector_text,
            timing_seconds=2.0,
            emphasis_level=1,
            metadata={'connector': True}
        )
    
    def _apply_style_to_text(self, text: str, style: str) -> str:
        """Apply style transformation to text"""
        if style == 'casual':
            # Make more conversational
            text = text.replace('However,', 'But')
            text = text.replace('Therefore,', 'So')
            text = text.replace('Nevertheless,', 'Still')
        elif style == 'formal':
            # Make more formal
            text = text.replace("don't", 'do not')
            text = text.replace("can't", 'cannot')
            text = text.replace("won't", 'will not')
        # 'balanced' style needs no changes
        
        return text
    
    def _optimize_text_for_tts(
        self,
        text: str,
        start_position: int
    ) -> tuple[str, List[TTSMarker]]:
        """
        Optimize text for TTS and generate markers
        Returns (optimized_text, markers)
        """
        markers = []
        optimized_text = text
        
        # Add emphasis markers for important words
        emphasis_words = ['unique', 'fascinating', 'remarkable', 'incredible', 'amazing']
        for word in emphasis_words:
            if word in text.lower():
                pos = text.lower().find(word)
                if pos != -1:
                    markers.append(TTSMarker(
                        position=start_position + pos,
                        type='emphasis',
                        value='strong',
                        metadata={'word': word}
                    ))
        
        # Add pause markers after sentences
        import re
        sentences = re.split(r'[.!?]', text)
        current_pos = start_position
        for sentence in sentences[:-1]:  # Exclude last empty string
            current_pos += len(sentence) + 1  # +1 for punctuation
            markers.append(TTSMarker(
                position=current_pos,
                type='pause',
                value=0.5,  # 0.5 second pause
                metadata={'reason': 'sentence_end'}
            ))
        
        return optimized_text, markers


# Content Integrators for different podcast types

class BasePodcastIntegrator:
    """Integrator for base podcast format"""
    
    async def create_structure(
        self,
        narrative: ConstructedNarrative,
        user_preferences: UserProfile
    ) -> Dict[str, Any]:
        """Create base podcast structure"""
        return {
            'sections': narrative.story_elements,
            'format': 'base',
            'target_duration': narrative.estimated_duration_seconds
        }
    
    async def integrate_content(
        self,
        script_structure: Dict[str, Any],
        content_data: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> Dict[str, Any]:
        """Integrate content into base podcast structure"""
        sections = []
        
        for section in script_structure['sections']:
            # Enhance section with actual content
            enhanced_content = self._enhance_with_content(
                section.content,
                content_data
            )
            
            enhanced_section = StoryElement(
                type=section.type,
                content=enhanced_content,
                timing_seconds=section.timing_seconds,
                emphasis_level=section.emphasis_level,
                tts_markers=section.tts_markers.copy(),
                metadata=section.metadata.copy()
            )
            
            sections.append(enhanced_section)
        
        return {'sections': sections}
    
    def _enhance_with_content(
        self,
        template_text: str,
        content_data: Dict[str, Any]
    ) -> str:
        """Enhance template with actual content"""
        # Replace placeholders with actual content
        enhanced = template_text
        
        if '{title}' in enhanced:
            enhanced = enhanced.replace('{title}', content_data.get('title', ''))
        
        if '{content}' in enhanced:
            enhanced = enhanced.replace('{content}', content_data.get('content', ''))
        
        return enhanced


class StandoutPodcastIntegrator(BasePodcastIntegrator):
    """Integrator for standout podcast format"""
    
    async def integrate_content(
        self,
        script_structure: Dict[str, Any],
        content_data: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> Dict[str, Any]:
        """Integrate content with emphasis on standout elements"""
        sections = []
        
        for section in script_structure['sections']:
            # Enhance with standout focus
            enhanced_content = self._enhance_with_standout_focus(
                section.content,
                content_data
            )
            
            # Increase emphasis for standout content
            emphasis = min(section.emphasis_level + 1, 5)
            
            enhanced_section = StoryElement(
                type=section.type,
                content=enhanced_content,
                timing_seconds=section.timing_seconds,
                emphasis_level=emphasis,
                tts_markers=section.tts_markers.copy(),
                metadata=section.metadata.copy()
            )
            
            sections.append(enhanced_section)
        
        return {'sections': sections}
    
    def _enhance_with_standout_focus(
        self,
        template_text: str,
        content_data: Dict[str, Any]
    ) -> str:
        """Enhance with focus on standout elements"""
        enhanced = self._enhance_with_content(template_text, content_data)
        
        # Add standout emphasis
        if content_data.get('standout_score', 0) > 5.0:
            enhanced = f"Here's something truly remarkable: {enhanced}"
        
        return enhanced


class TopicPodcastIntegrator(BasePodcastIntegrator):
    """Integrator for topic-specific podcast format"""
    
    async def integrate_content(
        self,
        script_structure: Dict[str, Any],
        content_data: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> Dict[str, Any]:
        """Integrate content with topic-specific depth"""
        sections = []
        
        for section in script_structure['sections']:
            # Enhance with topic depth
            enhanced_content = self._enhance_with_topic_depth(
                section.content,
                content_data
            )
            
            enhanced_section = StoryElement(
                type=section.type,
                content=enhanced_content,
                timing_seconds=section.timing_seconds * 1.2,  # More time for depth
                emphasis_level=section.emphasis_level,
                tts_markers=section.tts_markers.copy(),
                metadata=section.metadata.copy()
            )
            
            sections.append(enhanced_section)
        
        return {'sections': sections}
    
    def _enhance_with_topic_depth(
        self,
        template_text: str,
        content_data: Dict[str, Any]
    ) -> str:
        """Enhance with topic-specific depth"""
        enhanced = self._enhance_with_content(template_text, content_data)
        
        # Add depth indicators
        enhanced = f"Let's dive deeper into this: {enhanced}"
        
        return enhanced


class PersonalizedPodcastIntegrator(BasePodcastIntegrator):
    """Integrator for personalized podcast format"""
    
    async def integrate_content(
        self,
        script_structure: Dict[str, Any],
        content_data: Dict[str, Any],
        narrative: ConstructedNarrative
    ) -> Dict[str, Any]:
        """Integrate content with personalization"""
        sections = []
        
        for section in script_structure['sections']:
            # Enhance with personalization
            enhanced_content = self._enhance_with_personalization(
                section.content,
                content_data
            )
            
            enhanced_section = StoryElement(
                type=section.type,
                content=enhanced_content,
                timing_seconds=section.timing_seconds,
                emphasis_level=section.emphasis_level,
                tts_markers=section.tts_markers.copy(),
                metadata=section.metadata.copy()
            )
            
            sections.append(enhanced_section)
        
        return {'sections': sections}
    
    def _enhance_with_personalization(
        self,
        template_text: str,
        content_data: Dict[str, Any]
    ) -> str:
        """Enhance with personalization"""
        enhanced = self._enhance_with_content(template_text, content_data)
        
        # Add personal touch
        enhanced = f"Based on your interests, {enhanced}"
        
        return enhanced
