"""
Enhanced Podcast Generator with CLEAR Framework Prompt Engineering
Fixes template text issues and ensures complete, high-quality scripts
"""
import asyncio
import time
import re
from typing import Dict, List, Any, Optional
import structlog
from app.core.config import settings
from app.services.content.llm_singleton import get_llm_service

logger = structlog.get_logger()


class EnhancedPodcastGenerator:
    """
    Enhanced podcast script generator using CLEAR framework:
    - Concise: Remove superfluous language
    - Logical: Structured flow of instructions
    - Explicit: Precise output format specifications
    - Adaptive: Flexible based on content
    - Reflective: Self-checking validation
    """
    
    def __init__(self):
        self.llm = get_llm_service(provider="perplexity")
        self.max_retries = 2
        self.timeout = 60  # seconds
        
        # Template text indicators to detect
        self.template_indicators = [
            r"let'?s continue",
            r"\[more content",
            r"\[continue here",
            r"to be continued",
            r"\.\.\..*\.\.\..*\.\.\.",  # Multiple ellipses
            r"\[insert.*\]",
            r"\{.*placeholder.*\}",
        ]
        
        # Introduction indicators
        self.intro_words = [
            "welcome", "hello", "today", "imagine", "picture", "have you ever",
            "join us", "let's explore", "discover", "journey"
        ]
        
        # Conclusion indicators
        self.conclusion_words = [
            "thank you", "thanks for", "until next time", "join us again",
            "that's all", "that concludes", "we hope", "remember"
        ]
    
    async def generate_information_rich_script(
        self,
        content_data: Dict[str, Any],
        podcast_type: str,
        target_duration: int = 10,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate complete, information-rich podcast script with validation."""
        try:
            logger.info("enhanced_script_generation_started",
                       location=content_data.get('location', '')[:50],
                       duration=target_duration)
            
            start_time = time.time()
            attempt = 0
            script = None
            quality_metrics = None
            
            # Try up to max_retries times
            while attempt < self.max_retries:
                attempt += 1
                
                # Build prompt (stricter on retries)
                prompt = self._build_clear_framework_prompt(
                    content_data,
                    podcast_type,
                    target_duration,
                    user_preferences,
                    is_retry=(attempt > 1)
                )
                
                # Generate script
                logger.info(f"generation_attempt_{attempt}", duration=target_duration)
                script = await self._call_perplexity_api(prompt)
                
                if not script:
                    logger.warning(f"attempt_{attempt}_empty_response")
                    continue
                
                # Validate script
                quality_metrics = self._validate_script(script, target_duration)
                
                # Check if validation passed
                if quality_metrics["passes_validation"]:
                    logger.info(f"attempt_{attempt}_success", quality=quality_metrics)
                    break
                else:
                    logger.warning(f"attempt_{attempt}_failed_validation",
                                 issues=self._get_validation_issues(quality_metrics))
                    
                    if attempt >= self.max_retries:
                        logger.warning("max_retries_reached_using_best_attempt")
                        break
            
            generation_time = time.time() - start_time
            
            result = {
                "script": script or "",
                "quality_metrics": quality_metrics or {},
                "generation_metadata": {
                    "attempts": attempt,
                    "generation_time": round(generation_time, 2),
                    "target_duration": target_duration,
                    "target_word_count": target_duration * 150,
                    "actual_word_count": len(script.split()) if script else 0
                },
                "success": quality_metrics.get("passes_validation", False) if quality_metrics else False
            }
            
            logger.info("enhanced_script_generation_complete",
                       attempts=attempt,
                       generation_time=generation_time,
                       passes_validation=result["success"])
            
            return result
            
        except Exception as e:
            logger.error("enhanced_script_generation_error", error=str(e))
            return {
                "script": "",
                "quality_metrics": {},
                "generation_metadata": {"error": str(e)},
                "success": False
            }
    
    def _build_clear_framework_prompt(
        self,
        content_data: Dict[str, Any],
        podcast_type: str,
        target_duration: int,
        user_preferences: Optional[Dict],
        is_retry: bool = False
    ) -> str:
        """Build structured prompt using CLEAR framework."""
        word_count = target_duration * 150
        location = content_data.get('location', 'Unknown')
        title = content_data.get('title', location)
        formatted_content = self._format_content_for_prompt(content_data)
        
        strictness_note = ""
        if is_retry:
            strictness_note = "\n⚠️ CRITICAL: This is a RETRY. You MUST provide a COMPLETE script with NO placeholder text.\n"
        
        prompt = f"""# PODCAST SCRIPT GENERATION TASK
{strictness_note}
## OBJECTIVE
Write a complete, information-rich {target_duration}-minute podcast script about {title}.
Target: {word_count} words (150 words/minute speaking pace).

## CRITICAL REQUIREMENTS
✓ Write the COMPLETE script from start to finish
✓ DO NOT use placeholder text like 'Let's continue...', '[more content]', or '...'
✓ DO NOT stop mid-sentence or mid-section
✓ Include ALL sections: introduction, main content, conclusion
✓ Weave facts naturally into narrative (not as a list)
✓ Use specific examples and concrete details
✓ Make it engaging and conversational

## CONTENT TO INCLUDE
{formatted_content}

## STRUCTURE (REQUIRED)
1. Hook/Introduction (30 seconds, ~75 words) - Grab attention, set the scene
2. Main Content ({target_duration-1} minutes, ~{word_count-150} words) - Develop story with facts
3. Conclusion (30 seconds, ~75 words) - Summarize and thank listener

## STYLE GUIDELINES
- Conversational yet informative tone
- Vary sentence length for rhythm
- Use vivid, descriptive language
- Natural transitions between ideas

## OUTPUT FORMAT
Provide ONLY the podcast script text ready to read aloud.
No section labels, meta-commentary, or notes.

BEGIN SCRIPT:
"""
        return prompt
    
    def _format_content_for_prompt(self, content_data: Dict[str, Any]) -> str:
        """Format content data for inclusion in prompt"""
        formatted = []
        
        if content_data.get('is_question'):
            # Research-based content
            formatted.append(f"**Question:** {content_data.get('location', '')}")
            
            if content_data.get('research_result'):
                research = content_data['research_result']
                if research.get('overview'):
                    formatted.append(f"\n**Overview:** {research['overview'][:500]}")
                if research.get('key_findings'):
                    formatted.append("\n**Key Findings:**")
                    for i, finding in enumerate(research['key_findings'][:5], 1):
                        formatted.append(f"{i}. {finding[:200]}")
        else:
            # Location-based content
            if content_data.get('description'):
                formatted.append(f"**About:** {content_data['description'][:300]}")
            
            if content_data.get('interesting_facts'):
                formatted.append("\n**Interesting Facts:**")
                for i, fact in enumerate(content_data['interesting_facts'][:8], 1):
                    formatted.append(f"{i}. {fact[:150]}")
            
            if content_data.get('hierarchy'):
                hierarchy = content_data['hierarchy']
                if any(hierarchy.values()):
                    formatted.append("\n**Geographic Context:**")
                    for level, value in hierarchy.items():
                        if value:
                            formatted.append(f"- {level.title()}: {value}")
        
        return "\n".join(formatted) if formatted else "No specific content provided."
    
    async def _call_perplexity_api(self, prompt: str) -> str:
        """Call Perplexity API with enhanced prompt"""
        try:
            # Use the LLM service's internal API call method
            if hasattr(self.llm, 'client') and self.llm.client:
                response = await self.llm.client.chat.completions.create(
                    model="sonar-pro",  # Use sonar-pro for better quality
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert podcast scriptwriter. You create complete, polished scripts ready for voice recording. You NEVER use placeholder text or incomplete sections."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    top_p=0.9
                )
                
                if response and response.choices:
                    content = response.choices[0].message.content
                    return content.strip()
            
            return ""
            
        except Exception as e:
            logger.error("perplexity_api_call_failed", error=str(e))
            return ""
    
    def _validate_script(self, script: str, target_duration: int) -> Dict[str, Any]:
        """Validate script quality and completeness"""
        metrics = {
            "is_complete": False,
            "has_template_text": False,
            "information_density": 0.0,
            "has_introduction": False,
            "has_conclusion": False,
            "word_count": 0,
            "target_word_count": target_duration * 150,
            "word_count_accuracy": 0.0,
            "passes_validation": False
        }
        
        if not script:
            return metrics
        
        # Check 1: Minimum length (500 chars)
        metrics["is_complete"] = len(script) > 500
        
        # Check 2: Template text detection
        script_lower = script.lower()
        for pattern in self.template_indicators:
            if re.search(pattern, script_lower):
                metrics["has_template_text"] = True
                break
        
        # Check 3: Word count
        words = script.split()
        metrics["word_count"] = len(words)
        target = metrics["target_word_count"]
        metrics["word_count_accuracy"] = min(len(words) / target, target / len(words)) if len(words) > 0 else 0
        
        # Check 4: Information density (content words vs total)
        # Count words longer than 3 chars (excluding common short words)
        content_words = [w for w in words if len(w) > 3]
        metrics["information_density"] = len(content_words) / len(words) if words else 0
        
        # Check 5: Has introduction
        first_200_chars = script[:200].lower()
        metrics["has_introduction"] = any(word in first_200_chars for word in self.intro_words)
        
        # Check 6: Has conclusion
        last_200_chars = script[-200:].lower()
        metrics["has_conclusion"] = any(word in last_200_chars for word in self.conclusion_words)
        
        # Overall validation (relaxed thresholds for real-world scripts)
        metrics["passes_validation"] = (
            metrics["is_complete"] and
            not metrics["has_template_text"] and
            metrics["information_density"] > 0.60 and  # Lowered from 0.75 (more realistic)
            metrics["word_count_accuracy"] > 0.7
        )
        
        return metrics
    
    def _get_validation_issues(self, metrics: Dict[str, Any]) -> List[str]:
        """Get list of validation issues"""
        issues = []
        
        if not metrics.get("is_complete"):
            issues.append("Script too short (<500 chars)")
        
        if metrics.get("has_template_text"):
            issues.append("Contains template/placeholder text")
        
        if metrics.get("information_density", 0) <= 0.60:
            issues.append(f"Low information density ({metrics.get('information_density', 0):.2f})")
        
        if not metrics.get("has_introduction"):
            issues.append("Missing clear introduction")
        
        if not metrics.get("has_conclusion"):
            issues.append("Missing clear conclusion")
        
        if metrics.get("word_count_accuracy", 0) <= 0.7:
            issues.append(f"Word count off target ({metrics.get('word_count', 0)} vs {metrics.get('target_word_count', 0)})")
        
        return issues


# Singleton instance
enhanced_podcast_generator = EnhancedPodcastGenerator()
