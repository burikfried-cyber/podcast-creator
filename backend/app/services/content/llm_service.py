"""
LLM Service
Supports Perplexity (recommended), OpenAI, and Ollama
"""
from typing import Dict, Any, Optional, List
import structlog
from app.core.config import settings

logger = structlog.get_logger()

# Try to import OpenAI client (works for both OpenAI and Perplexity)
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI client not available - install with: pip install openai")

# Try to import Ollama (fallback)
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not available - install with: pip install ollama")


class LLMService:
    """Service for LLM-based content generation"""
    
    def __init__(self, provider: str = "perplexity"):
        """
        Initialize LLM service
        
        Args:
            provider: "perplexity" (recommended), "openai", or "ollama"
        """
        self.provider = provider
        
        # Try Perplexity first (best option!)
        if provider == "perplexity":
            api_key = settings.PERPLEXITY_API_KEY
            if api_key and OPENAI_AVAILABLE:
                self.client = AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.perplexity.ai"
                )
                # Use current Perplexity model (updated model names as of 2025)
                self.model = "sonar"  # Basic model with web search
                logger.info("LLM initialized with Perplexity", model=self.model)
            else:
                logger.warning("PERPLEXITY_API_KEY not set, trying OpenAI...")
                provider = "openai"
        
        # Try OpenAI
        if provider == "openai":
            api_key = settings.OPENAI_API_KEY
            if api_key and OPENAI_AVAILABLE:
                self.client = AsyncOpenAI(api_key=api_key)
                self.model = "gpt-4-turbo-preview"
                logger.info("LLM initialized with OpenAI")
            else:
                logger.warning("OPENAI_API_KEY not set, falling back to Ollama...")
                provider = "ollama"
        
        # Fallback to Ollama (local, free)
        if provider == "ollama":
            if OLLAMA_AVAILABLE:
                self.model = "llama3"
                logger.info("LLM initialized with Ollama (FREE, LOCAL)")
            else:
                logger.error("No LLM available! Set PERPLEXITY_API_KEY or install Ollama")
    
    async def generate_narrative(
        self,
        facts: Dict[str, Any],
        narrative_type: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate narrative content using LLM
        
        Args:
            facts: Wikipedia and location facts
            narrative_type: Type of narrative (discovery, mystery, etc.)
            user_preferences: User preferences for personalization
            
        Returns:
            Generated narrative text
        """
        logger.info("llm_generate_narrative_called",
                   narrative_type=narrative_type,
                   provider=self.provider,
                   has_facts=bool(facts))
        
        try:
            prompt = self._build_prompt(facts, narrative_type, user_preferences)
            logger.info("llm_prompt_built", prompt_length=len(prompt))
            
            if self.provider in ["perplexity", "openai"]:
                result = await self._generate_with_api(prompt)
                logger.info("llm_generation_complete", result_length=len(result))
                return result
            else:
                result = await self._generate_with_ollama(prompt)
                logger.info("llm_generation_complete", result_length=len(result))
                return result
                
        except Exception as e:
            logger.error("narrative_generation_failed", error=str(e), error_type=type(e).__name__)
            import traceback
            logger.error("llm_traceback", traceback=traceback.format_exc())
            return self._get_fallback_narrative(facts)
    
    def _build_prompt(
        self,
        facts: Dict[str, Any],
        narrative_type: str,
        user_preferences: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM"""
        location = facts.get('title', 'this location')
        summary = facts.get('summary', '')
        interesting_facts = facts.get('interesting_facts', [])
        
        prompt = f"""Create an engaging podcast script about {location}.

NARRATIVE STYLE: {narrative_type}

FACTS TO INCLUDE:
{summary}

INTERESTING DETAILS:
{chr(10).join(f'- {fact}' for fact in interesting_facts[:5])}

REQUIREMENTS:
- Make it conversational and engaging
- Target duration: 10-15 minutes (about 1500-2000 words)
- Include a compelling hook at the start
- Build narrative tension and interest
- End with a memorable conclusion
- Use vivid descriptions and storytelling techniques
- Make it feel like a conversation, not a lecture

Generate the complete podcast script now:"""
        
        return prompt
    
    async def _generate_with_api(self, prompt: str) -> str:
        """Generate using Perplexity or OpenAI API"""
        try:
            logger.info(f"generating_with_{self.provider}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert podcast scriptwriter who creates engaging, informative, and entertaining content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            logger.info(f"{self.provider}_generation_complete", length=len(content))
            return content
            
        except Exception as e:
            logger.error(f"{self.provider}_generation_failed", error=str(e))
            raise
    
    async def _generate_with_ollama(self, prompt: str) -> str:
        """Generate using Ollama (FREE)"""
        try:
            logger.info("generating_with_ollama", model=self.model)
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'num_predict': 2000
                }
            )
            
            content = response['response']
            logger.info("ollama_generation_complete", length=len(content))
            return content
            
        except Exception as e:
            logger.error("ollama_generation_failed", error=str(e))
            raise
    
    def _get_fallback_narrative(self, facts: Dict[str, Any]) -> str:
        """Fallback narrative when LLM fails"""
        location = facts.get('title', 'this location')
        summary = facts.get('summary', 'a fascinating place')
        
        return f"""Welcome to our podcast about {location}.

{summary}

This location has a rich history and many interesting stories to tell. From its early beginnings to its present day significance, {location} continues to captivate visitors and residents alike.

Throughout this episode, we'll explore the unique characteristics that make this place special, discover hidden gems, and learn about the people and events that shaped its identity.

Whether you're planning a visit or simply curious about the world around us, this journey through {location} promises to be both informative and entertaining.

Let's begin our exploration."""
    
    async def generate_hook(
        self,
        facts: Dict[str, Any],
        narrative_type: str
    ) -> str:
        """Generate a compelling hook using LLM"""
        logger.info("llm_generate_hook_called", narrative_type=narrative_type)
        
        location = facts.get('title', 'this location')
        summary = facts.get('summary', '')[:500]  # First 500 chars
        
        prompt = f"""Create a compelling 2-3 sentence hook for a podcast about {location}.

Context: {summary}

Style: {narrative_type}

Requirements:
- Grab attention immediately
- Create curiosity
- Be conversational and engaging
- Don't use cliches like "What if I told you"

Hook:"""

        try:
            if self.provider in ["perplexity", "openai"]:
                return await self._generate_with_api(prompt)
            else:
                return await self._generate_with_ollama(prompt)
        except Exception as e:
            logger.error("hook_generation_failed", error=str(e))
            # Fallback to template
            return f"Today, we're exploring {location}, and you're about to discover something extraordinary."
    
    async def generate_conclusion(
        self,
        facts: Dict[str, Any],
        narrative_type: str
    ) -> str:
        """Generate a memorable conclusion using LLM"""
        logger.info("llm_generate_conclusion_called", narrative_type=narrative_type)
        
        location = facts.get('title', 'this location')
        summary = facts.get('summary', '')[:500]
        
        prompt = f"""Create a memorable 2-3 sentence conclusion for a podcast about {location}.

Context: {summary}

Style: {narrative_type}

Requirements:
- Wrap up the journey
- Leave a lasting impression
- Be warm and inviting
- Encourage further exploration

Conclusion:"""

        try:
            if self.provider in ["perplexity", "openai"]:
                return await self._generate_with_api(prompt)
            else:
                return await self._generate_with_ollama(prompt)
        except Exception as e:
            logger.error("conclusion_generation_failed", error=str(e))
            # Fallback to template
            return f"""And that's the story of {location}. From its fascinating history to its vibrant present, this place continues to inspire and amaze.

Whether you visit in person or explore from afar, {location} offers endless opportunities for discovery and wonder.

Thank you for joining us on this journey. Until next time, keep exploring!"""
