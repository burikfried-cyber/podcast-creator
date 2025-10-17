"""
Wikipedia Service
Fetches real content from Wikipedia (100% FREE)
"""
import wikipedia
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger()


class WikipediaService:
    """Service for fetching content from Wikipedia"""
    
    def __init__(self):
        # Set language to English
        wikipedia.set_lang("en")
    
    async def get_location_content(self, location: str) -> Dict[str, Any]:
        """
        Fetch comprehensive content about a location from Wikipedia
        
        Args:
            location: Location name (e.g., "Paris, France")
            
        Returns:
            Dictionary with Wikipedia content
        """
        try:
            logger.info("wikipedia_fetch_started", location=location)
            
            # Search for the location
            search_results = wikipedia.search(location, results=3)
            
            if not search_results:
                logger.warning("wikipedia_no_results", location=location)
                return self._get_fallback_content(location)
            
            # Get the first result (most relevant)
            page_title = search_results[0]
            
            try:
                page = wikipedia.page(page_title, auto_suggest=False)
            except wikipedia.DisambiguationError as e:
                # If disambiguation, try the first option
                logger.info("wikipedia_disambiguation", options=e.options[:5])
                page = wikipedia.page(e.options[0], auto_suggest=False)
            except wikipedia.PageError:
                logger.warning("wikipedia_page_not_found", title=page_title)
                return self._get_fallback_content(location)
            
            # Extract content
            content = {
                'title': page.title,
                'summary': page.summary,
                'content': page.content[:5000],  # First 5000 chars
                'url': page.url,
                'categories': page.categories[:10],
                'sections': self._extract_sections(page.content),
                'links': page.links[:20],  # Related topics
                'images': page.images[:5] if hasattr(page, 'images') else [],
                'coordinates': page.coordinates if hasattr(page, 'coordinates') else None
            }
            
            logger.info("wikipedia_fetch_complete",
                       location=location,
                       title=page.title,
                       content_length=len(page.content))
            
            return content
            
        except Exception as e:
            logger.error("wikipedia_fetch_failed",
                        location=location,
                        error=str(e))
            return self._get_fallback_content(location)
    
    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract sections from Wikipedia content"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('==') and line.endswith('=='):
                # Save previous section
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                # Start new section
                current_section = line.strip('= ')
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        return sections[:10]  # Return first 10 sections
    
    def _get_fallback_content(self, location: str) -> Dict[str, Any]:
        """Fallback content when Wikipedia fetch fails"""
        return {
            'title': location,
            'summary': f"Information about {location}.",
            'content': f"This is a fascinating location with rich history and culture.",
            'url': '',
            'categories': [],
            'sections': [],
            'links': [],
            'images': [],
            'coordinates': None
        }
    
    async def get_related_topics(self, location: str, limit: int = 10) -> List[str]:
        """Get related topics for a location"""
        try:
            search_results = wikipedia.search(location, results=limit)
            return search_results
        except Exception as e:
            logger.error("wikipedia_related_topics_failed", error=str(e))
            return []
    
    async def get_interesting_facts(self, content: Dict[str, Any]) -> List[str]:
        """Extract interesting facts from Wikipedia content"""
        facts = []
        
        # Extract from summary
        summary_sentences = content.get('summary', '').split('. ')
        facts.extend(summary_sentences[:3])
        
        # Extract from sections
        for section in content.get('sections', [])[:5]:
            section_sentences = section.get('content', '').split('. ')
            if section_sentences:
                facts.append(section_sentences[0])
        
        return [f for f in facts if len(f) > 20][:10]  # Return top 10 facts
