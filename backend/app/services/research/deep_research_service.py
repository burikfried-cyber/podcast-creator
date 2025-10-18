"""
Deep Research Service
Uses Perplexity Sonar Pro for comprehensive question-based research
"""
import aiohttp
import asyncio
import time
import re
from typing import Dict, List, Optional, Any
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class DeepResearchService:
    """
    Deep research service using Perplexity Sonar Pro model.
    Provides comprehensive, well-structured research answers with citations.
    """
    
    def __init__(self):
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"
        self.api_key = settings.PERPLEXITY_API_KEY
        self.timeout = 180  # 3 minutes
        
        # Depth level instructions
        self.depth_instructions = {
            1: "Provide a brief overview suitable for a general audience. Keep it concise and accessible.",
            2: "Provide a clear explanation with key facts and context. Suitable for general audience.",
            3: "Provide comprehensive information with historical context and multiple perspectives. Include specific examples.",
            4: "Provide detailed analysis with historical context, multiple perspectives, and expert insights.",
            5: "Provide expert-level investigation with academic rigor. Explore complex relationships and nuances.",
            6: "Provide exhaustive expert-level research with academic rigor, complex relationships, and scholarly depth."
        }
    
    async def research_question(
        self,
        question: str,
        depth_level: int = 3,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Conduct deep research on a question using Perplexity API.
        
        Args:
            question: The question to research
            depth_level: Research depth (1-6)
            focus_areas: Optional specific areas to focus on
            
        Returns:
            Dictionary with research results
        """
        try:
            logger.info("deep_research_started", question=question[:100], depth=depth_level)
            start_time = time.time()
            
            # Build research prompt
            prompt = self._build_research_prompt(question, depth_level, focus_areas)
            
            # Call Perplexity API
            response_text = await self._call_perplexity_api(prompt)
            
            if not response_text:
                logger.error("perplexity_api_returned_empty")
                return self._get_fallback_result(question)
            
            # Parse response into structured format
            parsed_result = self._parse_research_response(response_text)
            
            # Extract citations
            sources = self._extract_citations(response_text)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(response_text, sources)
            
            research_time = time.time() - start_time
            
            result = {
                "question": question,
                "comprehensive_answer": response_text,
                "overview": parsed_result.get("overview", ""),
                "key_findings": parsed_result.get("key_findings", []),
                "detailed_explanation": parsed_result.get("detailed_explanation", ""),
                "conclusion": parsed_result.get("conclusion", ""),
                "sources": sources,
                "confidence": confidence,
                "research_time": round(research_time, 2),
                "research_method": "perplexity_deep_research",
                "depth_level": depth_level,
                "model": self.model
            }
            
            logger.info("deep_research_completed",
                       question=question[:100],
                       research_time=research_time,
                       confidence=confidence,
                       sources_count=len(sources))
            
            return result
            
        except asyncio.TimeoutError:
            logger.error("deep_research_timeout", question=question[:100])
            return self._get_fallback_result(question, error="Research timeout after 3 minutes")
        except Exception as e:
            logger.error("deep_research_error", error=str(e), question=question[:100])
            return self._get_fallback_result(question, error=str(e))
    
    def _build_research_prompt(
        self,
        question: str,
        depth_level: int,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Build depth-appropriate research prompt"""
        
        # Clamp depth level to 1-6
        depth_level = max(1, min(6, depth_level))
        
        depth_instruction = self.depth_instructions.get(depth_level, self.depth_instructions[3])
        
        focus_text = ""
        if focus_areas:
            focus_text = f"\n**Focus Areas:** {', '.join(focus_areas)}"
        
        prompt = f"""Conduct comprehensive research on the following question:

**Question:** {question}
**Depth:** {depth_instruction}{focus_text}

**Requirements:**
- Provide comprehensive, well-structured answer
- Include specific facts, dates, examples, and statistics
- Explain key concepts and relationships clearly
- Discuss multiple perspectives where relevant
- Cite sources for major claims
- Organize information logically

**Format your response as:**
1. Overview (2-3 sentences summarizing the answer)
2. Key Findings (3-5 main points with supporting details)
3. Detailed Explanation (main body of research with evidence)
4. Conclusion (synthesis and significance)

Please provide a thorough, well-researched response."""
        
        return prompt
    
    async def _call_perplexity_api(self, prompt: str) -> str:
        """Call Perplexity API with research prompt"""
        
        if not self.api_key:
            logger.error("perplexity_api_key_missing")
            raise ValueError("PERPLEXITY_API_KEY not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a comprehensive research assistant. Provide detailed, well-structured answers with citations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.3,
            "search_recency_filter": "month"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract response text
                        if "choices" in data and len(data["choices"]) > 0:
                            message = data["choices"][0].get("message", {})
                            content = message.get("content", "")
                            
                            logger.info("perplexity_api_success",
                                       response_length=len(content),
                                       model=self.model)
                            
                            return content
                        else:
                            logger.error("perplexity_api_invalid_response", data=data)
                            return ""
                    else:
                        error_text = await response.text()
                        logger.error("perplexity_api_error",
                                   status=response.status,
                                   error=error_text)
                        return ""
                        
        except asyncio.TimeoutError:
            logger.error("perplexity_api_timeout")
            raise
        except Exception as e:
            logger.error("perplexity_api_exception", error=str(e))
            raise
    
    def _parse_research_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse research response into structured sections.
        Looks for Overview, Key Findings, Detailed Explanation, Conclusion.
        """
        result = {
            "overview": "",
            "key_findings": [],
            "detailed_explanation": "",
            "conclusion": ""
        }
        
        # Try to extract sections using headers
        overview_match = re.search(r'(?:^|\n)(?:##?\s*)?(?:1\.\s*)?Overview[:\s]*\n(.*?)(?=\n(?:##?\s*)?(?:2\.\s*)?Key Findings|\n(?:##?\s*)?Detailed|$)', response_text, re.DOTALL | re.IGNORECASE)
        if overview_match:
            result["overview"] = overview_match.group(1).strip()
        else:
            # Fallback: Use first paragraph as overview
            paragraphs = response_text.split('\n\n')
            if paragraphs:
                result["overview"] = paragraphs[0].strip()[:300]
        
        # Extract key findings (look for numbered or bulleted list)
        findings_match = re.search(r'(?:^|\n)(?:##?\s*)?(?:2\.\s*)?Key Findings[:\s]*\n(.*?)(?=\n(?:##?\s*)?(?:3\.\s*)?Detailed|\n(?:##?\s*)?Conclusion|$)', response_text, re.DOTALL | re.IGNORECASE)
        if findings_match:
            findings_text = findings_match.group(1).strip()
            # Split by bullet points or numbers
            findings = re.split(r'\n(?:[-*•]|\d+\.)\s+', findings_text)
            result["key_findings"] = [f.strip() for f in findings if f.strip()][:5]  # Max 5
        else:
            # Fallback: Extract bullet points or numbered lists from anywhere
            bullet_pattern = r'(?:^|\n)(?:[-*•]|\d+\.)\s+(.+?)(?=\n(?:[-*•]|\d+\.)|$)'
            findings = re.findall(bullet_pattern, response_text, re.MULTILINE)
            if findings:
                result["key_findings"] = [f.strip() for f in findings if len(f.strip()) > 20][:5]
        
        # Extract detailed explanation
        detailed_match = re.search(r'(?:^|\n)(?:##?\s*)?(?:3\.\s*)?Detailed Explanation[:\s]*\n(.*?)(?=\n(?:##?\s*)?(?:4\.\s*)?Conclusion|$)', response_text, re.DOTALL | re.IGNORECASE)
        if detailed_match:
            result["detailed_explanation"] = detailed_match.group(1).strip()
        else:
            # Fallback: Use full text as detailed explanation
            result["detailed_explanation"] = response_text
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:^|\n)(?:##?\s*)?(?:4\.\s*)?Conclusion[:\s]*\n(.*?)$', response_text, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            result["conclusion"] = conclusion_match.group(1).strip()
        else:
            # Fallback: Use last paragraph as conclusion
            paragraphs = response_text.split('\n\n')
            if len(paragraphs) > 1:
                result["conclusion"] = paragraphs[-1].strip()[:300]
        
        return result
    
    def _extract_citations(self, response_text: str) -> List[Dict]:
        """
        Extract citations/sources from response text.
        Looks for URLs and source references.
        """
        sources = []
        
        # Pattern 1: URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, response_text)
        
        for url in urls[:10]:  # Limit to 10 sources
            sources.append({
                "url": url,
                "type": "web"
            })
        
        # Pattern 2: Source citations like [1], (Source: ...), etc.
        citation_pattern = r'\[(\d+)\]|\(Source:\s*([^)]+)\)'
        citations = re.findall(citation_pattern, response_text)
        
        for citation in citations[:5]:
            if citation[0]:  # Numbered citation
                sources.append({
                    "reference": f"[{citation[0]}]",
                    "type": "citation"
                })
            elif citation[1]:  # Named source
                sources.append({
                    "source": citation[1].strip(),
                    "type": "named"
                })
        
        return sources
    
    def _calculate_confidence(self, response_text: str, sources: List[Dict]) -> float:
        """
        Calculate confidence score based on response quality.
        Factors: length, citations, structure
        """
        score = 0.0
        
        # Factor 1: Response length (up to 0.4)
        length = len(response_text)
        if length > 2000:
            score += 0.4
        elif length > 1000:
            score += 0.3
        elif length > 500:
            score += 0.2
        else:
            score += 0.1
        
        # Factor 2: Number of sources (up to 0.3)
        source_count = len(sources)
        if source_count >= 5:
            score += 0.3
        elif source_count >= 3:
            score += 0.2
        elif source_count >= 1:
            score += 0.1
        
        # Factor 3: Structure (up to 0.3)
        has_sections = any(keyword in response_text.lower() for keyword in ['overview', 'key findings', 'conclusion'])
        if has_sections:
            score += 0.3
        elif '\n\n' in response_text:  # Has paragraphs
            score += 0.15
        
        return round(min(score, 1.0), 2)
    
    def _get_fallback_result(self, question: str, error: str = "Research failed") -> Dict:
        """Return fallback result when research fails"""
        return {
            "question": question,
            "comprehensive_answer": f"Unable to complete research: {error}",
            "overview": "",
            "key_findings": [],
            "detailed_explanation": "",
            "conclusion": "",
            "sources": [],
            "confidence": 0.0,
            "research_time": 0.0,
            "research_method": "perplexity_deep_research",
            "depth_level": 3,
            "model": self.model,
            "error": error
        }


# Singleton instance
deep_research_service = DeepResearchService()
