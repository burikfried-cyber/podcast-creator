"""
LLM Service Singleton
Ensures only one LLM instance is created and reused
"""
from typing import Optional
from .llm_service import LLMService

_llm_instance: Optional[LLMService] = None

def get_llm_service(provider: str = "perplexity") -> LLMService:
    """
    Get or create the singleton LLM service instance
    
    Args:
        provider: LLM provider (perplexity, openai, ollama)
        
    Returns:
        Singleton LLM service instance
    """
    global _llm_instance
    
    if _llm_instance is None:
        _llm_instance = LLMService(provider=provider)
    
    return _llm_instance

def reset_llm_service():
    """Reset the singleton (useful for testing)"""
    global _llm_instance
    _llm_instance = None
