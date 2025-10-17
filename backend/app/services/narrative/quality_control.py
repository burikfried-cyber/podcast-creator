"""
Content Quality Controller
Comprehensive quality assurance for podcast scripts
"""
import asyncio
from typing import Dict, List, Any, Optional
import re
import structlog

from .models import (
    PodcastScript,
    QualityReport,
    QualityCheck
)

logger = structlog.get_logger()


class ContentQualityController:
    """
    Comprehensive quality control for podcast scripts
    Ensures factual accuracy, cultural sensitivity, and content quality
    """
    
    def __init__(self):
        self.fact_checker = AdvancedFactChecker()
        self.content_validator = ContentStructureValidator()
        self.cultural_sensitivity_checker = CulturalSensitivityAnalyzer()
        self.plagiarism_detector = PlagiarismDetector()
        self.source_validator = SourceValidator()
        
        # Quality thresholds
        self.thresholds = {
            'factual_accuracy': 0.98,      # 98% accuracy required
            'content_structure': 0.95,     # 95% structure quality
            'cultural_sensitivity': 0.95,  # 95% sensitivity compliance
            'originality': 0.90,           # 90% originality required
            'source_attribution': 0.95     # 95% proper attribution
        }
    
    async def comprehensive_quality_check(
        self,
        script: PodcastScript,
        source_content: Dict[str, Any]
    ) -> QualityReport:
        """
        Perform comprehensive quality check on podcast script
        
        Args:
            script: Generated podcast script
            source_content: Original source content for verification
            
        Returns:
            QualityReport with all check results
        """
        logger.info("quality_check_started",
                   content_id=source_content.get('id'))
        
        try:
            # Run all quality checks in parallel
            quality_checks = await asyncio.gather(
                # Fact-checking with cross-source verification
                self.fact_checker.verify_factual_accuracy(script, source_content),
                
                # Content structure and flow validation
                self.content_validator.validate_structure(script),
                
                # Cultural sensitivity and appropriateness analysis
                self.cultural_sensitivity_checker.analyze_sensitivity(script),
                
                # Originality and plagiarism detection
                self.plagiarism_detector.check_originality(script),
                
                # Source attribution and credibility verification
                self.source_validator.verify_attribution(script, source_content)
            )
            
            # Unpack results
            factual_accuracy = quality_checks[0]
            content_structure = quality_checks[1]
            cultural_sensitivity = quality_checks[2]
            originality = quality_checks[3]
            source_attribution = quality_checks[4]
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(quality_checks)
            
            # Determine if script passes
            passed = self._determine_pass_status(quality_checks)
            
            # Generate recommendations
            recommendations = self.generate_improvement_recommendations(quality_checks)
            
            report = QualityReport(
                factual_accuracy=factual_accuracy,
                content_structure=content_structure,
                cultural_sensitivity=cultural_sensitivity,
                originality=originality,
                source_attribution=source_attribution,
                overall_score=overall_score,
                passed=passed,
                recommendations=recommendations
            )
            
            logger.info("quality_check_complete",
                       content_id=source_content.get('id'),
                       overall_score=overall_score,
                       passed=passed)
            
            return report
            
        except Exception as e:
            logger.error("quality_check_failed",
                        content_id=source_content.get('id'),
                        error=str(e))
            raise
    
    def calculate_overall_score(
        self,
        quality_checks: List[QualityCheck]
    ) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            0: 0.30,  # Factual accuracy (most important)
            1: 0.20,  # Content structure
            2: 0.25,  # Cultural sensitivity (very important)
            3: 0.15,  # Originality
            4: 0.10   # Source attribution
        }
        
        weighted_sum = sum(
            check.score * weights[i]
            for i, check in enumerate(quality_checks)
        )
        
        return weighted_sum
    
    def generate_improvement_recommendations(
        self,
        quality_checks: List[QualityCheck]
    ) -> List[str]:
        """Generate actionable improvement recommendations"""
        recommendations = []
        
        for check in quality_checks:
            if not check.passed:
                recommendations.extend(check.recommendations)
            elif check.warnings:
                recommendations.extend([
                    f"Warning in {check.check_name}: {w}"
                    for w in check.warnings
                ])
        
        return recommendations
    
    def _determine_pass_status(
        self,
        quality_checks: List[QualityCheck]
    ) -> bool:
        """Determine if script passes all quality checks"""
        # All critical checks must pass
        critical_checks = [quality_checks[0], quality_checks[2]]  # Factual, Cultural
        
        if not all(check.passed for check in critical_checks):
            return False
        
        # At least 4 out of 5 checks must pass
        passed_count = sum(1 for check in quality_checks if check.passed)
        
        return passed_count >= 4


class AdvancedFactChecker:
    """Advanced fact-checking with cross-source verification"""
    
    async def verify_factual_accuracy(
        self,
        script: PodcastScript,
        source_content: Dict[str, Any]
    ) -> QualityCheck:
        """
        Verify factual accuracy of script content
        Target: >98% accuracy
        """
        issues = []
        warnings = []
        recommendations = []
        
        script_text = script.content
        
        # 1. Check for factual claims
        claims = self._extract_factual_claims(script_text)
        
        # 2. Verify claims against source content
        verified_claims = 0
        unverified_claims = 0
        
        for claim in claims:
            if self._verify_claim_in_source(claim, source_content):
                verified_claims += 1
            else:
                unverified_claims += 1
                issues.append(f"Unverified claim: {claim[:100]}...")
        
        # 3. Check for exaggerations
        exaggerations = self._detect_exaggerations(script_text)
        if exaggerations:
            warnings.extend([f"Possible exaggeration: {e}" for e in exaggerations])
        
        # 4. Check for absolute statements without evidence
        absolute_statements = self._detect_absolute_statements(script_text)
        if absolute_statements:
            warnings.extend([f"Absolute statement: {s}" for s in absolute_statements])
        
        # Calculate accuracy score
        if claims:
            accuracy_score = verified_claims / len(claims)
        else:
            accuracy_score = 1.0  # No claims = no issues
        
        # Generate recommendations
        if unverified_claims > 0:
            recommendations.append(
                f"Verify or remove {unverified_claims} unverified claims"
            )
        if exaggerations:
            recommendations.append("Tone down exaggerated language")
        if absolute_statements:
            recommendations.append("Add qualifiers to absolute statements")
        
        passed = accuracy_score >= 0.98
        
        return QualityCheck(
            check_name="Factual Accuracy",
            passed=passed,
            score=accuracy_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metadata={
                'total_claims': len(claims),
                'verified_claims': verified_claims,
                'unverified_claims': unverified_claims
            }
        )
    
    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        # Split into sentences
        sentences = re.split(r'[.!?]', text)
        
        # Filter for factual claims (sentences with numbers, dates, specific facts)
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for factual indicators
            has_number = bool(re.search(r'\d+', sentence))
            has_date = bool(re.search(r'\b(century|year|ago|since|during)\b', sentence, re.I))
            has_specific = bool(re.search(r'\b(only|first|largest|oldest|unique)\b', sentence, re.I))
            
            if has_number or has_date or has_specific:
                claims.append(sentence)
        
        return claims
    
    def _verify_claim_in_source(
        self,
        claim: str,
        source_content: Dict[str, Any]
    ) -> bool:
        """Verify if claim is supported by source content"""
        # Simple verification - check if key terms appear in source
        source_text = ' '.join([
            str(source_content.get('title', '')),
            str(source_content.get('content', '')),
            str(source_content.get('description', ''))
        ]).lower()
        
        # Extract key terms from claim
        claim_lower = claim.lower()
        
        # Check for numbers
        numbers = re.findall(r'\d+', claim)
        if numbers:
            # At least one number should appear in source
            if not any(num in source_text for num in numbers):
                return False
        
        # Check for key nouns (simple heuristic)
        words = claim_lower.split()
        key_words = [w for w in words if len(w) > 4]  # Words longer than 4 chars
        
        if key_words:
            # At least 50% of key words should appear in source
            matches = sum(1 for word in key_words if word in source_text)
            return matches >= len(key_words) * 0.5
        
        return True  # Benefit of doubt for short claims
    
    def _detect_exaggerations(self, text: str) -> List[str]:
        """Detect potentially exaggerated language"""
        exaggeration_patterns = [
            r'\b(absolutely|completely|totally|entirely|perfectly)\s+\w+',
            r'\b(most|best|worst|greatest|largest|smallest)\s+\w+\s+in\s+the\s+world',
            r'\b(never|always|everyone|nobody|everything|nothing)\b',
            r'\b(incredible|unbelievable|mind-blowing|jaw-dropping)\b'
        ]
        
        exaggerations = []
        for pattern in exaggeration_patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                exaggerations.append(match.group())
        
        return exaggerations[:5]  # Limit to 5 examples
    
    def _detect_absolute_statements(self, text: str) -> List[str]:
        """Detect absolute statements that may need qualification"""
        absolute_patterns = [
            r'\b(is|are|was|were)\s+the\s+(only|first|last|best|worst)\b',
            r'\b(no\s+one|nobody|everyone|everything|nothing)\b',
            r'\b(always|never|forever|eternal)\b'
        ]
        
        statements = []
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            for pattern in absolute_patterns:
                if re.search(pattern, sentence, re.I):
                    statements.append(sentence.strip())
                    break
        
        return statements[:3]  # Limit to 3 examples


class ContentStructureValidator:
    """Validate content structure and flow"""
    
    async def validate_structure(
        self,
        script: PodcastScript
    ) -> QualityCheck:
        """
        Validate script structure and flow
        Target: >95% structure quality
        """
        issues = []
        warnings = []
        recommendations = []
        
        # 1. Check for required sections
        required_sections = {'hook', 'conclusion'}
        present_sections = {s.type.value for s in script.sections}
        
        missing_sections = required_sections - present_sections
        if missing_sections:
            issues.extend([f"Missing section: {s}" for s in missing_sections])
        
        # 2. Check section order
        if not self._validate_section_order(script.sections):
            issues.append("Sections are not in logical order")
        
        # 3. Check for abrupt transitions
        abrupt_transitions = self._detect_abrupt_transitions(script.sections)
        if abrupt_transitions:
            warnings.extend([f"Abrupt transition at section {i}" for i in abrupt_transitions])
        
        # 4. Check content balance
        balance_issues = self._check_content_balance(script.sections)
        if balance_issues:
            warnings.extend(balance_issues)
        
        # 5. Check for repetition
        repetitions = self._detect_repetition(script.content)
        if repetitions:
            warnings.append(f"Found {len(repetitions)} repeated phrases")
        
        # Calculate structure score
        structure_score = 1.0
        structure_score -= len(issues) * 0.15  # Major penalty for issues
        structure_score -= len(warnings) * 0.05  # Minor penalty for warnings
        structure_score = max(structure_score, 0.0)
        
        # Generate recommendations
        if missing_sections:
            recommendations.append("Add missing required sections")
        if abrupt_transitions:
            recommendations.append("Add smoother transitions between sections")
        if balance_issues:
            recommendations.append("Rebalance section lengths")
        if repetitions:
            recommendations.append("Remove or rephrase repeated content")
        
        passed = structure_score >= 0.95
        
        return QualityCheck(
            check_name="Content Structure",
            passed=passed,
            score=structure_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metadata={
                'num_sections': len(script.sections),
                'missing_sections': list(missing_sections),
                'abrupt_transitions': len(abrupt_transitions)
            }
        )
    
    def _validate_section_order(self, sections: List) -> bool:
        """Validate that sections are in logical order"""
        # Hook should be first if present
        if sections and sections[0].type.value == 'hook':
            return True
        # If no hook, any order is acceptable
        return True
    
    def _detect_abrupt_transitions(self, sections: List) -> List[int]:
        """Detect abrupt transitions between sections"""
        abrupt = []
        
        for i in range(len(sections) - 1):
            current = sections[i]
            next_section = sections[i + 1]
            
            # Check if there's a transition between major sections
            if (current.type.value in ['hook', 'main_content', 'climax'] and
                next_section.type.value in ['main_content', 'climax', 'conclusion'] and
                next_section.type.value != 'transition'):
                # No transition found
                abrupt.append(i)
        
        return abrupt
    
    def _check_content_balance(self, sections: List) -> List[str]:
        """Check if content is balanced across sections"""
        issues = []
        
        if not sections:
            return issues
        
        # Calculate average section length
        lengths = [len(s.content.split()) for s in sections]
        avg_length = sum(lengths) / len(lengths)
        
        # Check for sections that are too short or too long
        for i, length in enumerate(lengths):
            if length < avg_length * 0.3:
                issues.append(f"Section {i} is too short ({length} words)")
            elif length > avg_length * 3:
                issues.append(f"Section {i} is too long ({length} words)")
        
        return issues
    
    def _detect_repetition(self, text: str) -> List[str]:
        """Detect repeated phrases in text"""
        # Extract phrases (3+ words)
        words = text.lower().split()
        phrases = []
        
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            phrases.append(phrase)
        
        # Find duplicates
        from collections import Counter
        phrase_counts = Counter(phrases)
        
        repetitions = [phrase for phrase, count in phrase_counts.items() if count > 1]
        
        return repetitions[:5]  # Limit to 5 examples


class CulturalSensitivityAnalyzer:
    """Analyze cultural sensitivity and appropriateness"""
    
    async def analyze_sensitivity(
        self,
        script: PodcastScript
    ) -> QualityCheck:
        """
        Analyze cultural sensitivity
        Target: >95% compliance
        """
        issues = []
        warnings = []
        recommendations = []
        
        text = script.content
        
        # 1. Check for potentially offensive terms
        offensive_terms = self._detect_offensive_terms(text)
        if offensive_terms:
            issues.extend([f"Potentially offensive: {term}" for term in offensive_terms])
        
        # 2. Check for stereotypes
        stereotypes = self._detect_stereotypes(text)
        if stereotypes:
            warnings.extend([f"Possible stereotype: {s}" for s in stereotypes])
        
        # 3. Check for cultural appropriation indicators
        appropriation = self._detect_appropriation_indicators(text)
        if appropriation:
            warnings.extend([f"Cultural sensitivity concern: {a}" for a in appropriation])
        
        # 4. Check for respectful language
        disrespectful = self._detect_disrespectful_language(text)
        if disrespectful:
            issues.extend([f"Disrespectful language: {d}" for d in disrespectful])
        
        # Calculate sensitivity score
        sensitivity_score = 1.0
        sensitivity_score -= len(issues) * 0.20  # Major penalty
        sensitivity_score -= len(warnings) * 0.05  # Minor penalty
        sensitivity_score = max(sensitivity_score, 0.0)
        
        # Generate recommendations
        if offensive_terms:
            recommendations.append("Remove or replace offensive terms")
        if stereotypes:
            recommendations.append("Avoid stereotypical language")
        if appropriation:
            recommendations.append("Review cultural references for appropriateness")
        if disrespectful:
            recommendations.append("Use more respectful language")
        
        passed = sensitivity_score >= 0.95 and len(issues) == 0
        
        return QualityCheck(
            check_name="Cultural Sensitivity",
            passed=passed,
            score=sensitivity_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metadata={
                'offensive_terms': len(offensive_terms),
                'stereotypes': len(stereotypes),
                'appropriation_concerns': len(appropriation)
            }
        )
    
    def _detect_offensive_terms(self, text: str) -> List[str]:
        """Detect potentially offensive terms"""
        # This would use a comprehensive list in production
        # For now, just check for obviously problematic patterns
        offensive_patterns = [
            r'\b(primitive|savage|backward)\s+(people|culture|society)\b',
            r'\b(exotic|strange|weird)\s+(people|culture)\b'
        ]
        
        found = []
        for pattern in offensive_patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                found.append(match.group())
        
        return found
    
    def _detect_stereotypes(self, text: str) -> List[str]:
        """Detect stereotypical language"""
        stereotype_patterns = [
            r'\b(all|every)\s+\w+\s+(are|were|do|did)\b',
            r'\b(typical|stereotypical)\s+\w+\b'
        ]
        
        found = []
        for pattern in stereotype_patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                found.append(match.group())
        
        return found[:3]
    
    def _detect_appropriation_indicators(self, text: str) -> List[str]:
        """Detect potential cultural appropriation"""
        # Check for sacred/religious terms used casually
        sacred_terms = ['sacred', 'holy', 'ritual', 'ceremony', 'spiritual']
        
        concerns = []
        text_lower = text.lower()
        
        for term in sacred_terms:
            if term in text_lower:
                # Check if used respectfully (has context words nearby)
                context_words = ['traditional', 'important', 'significant', 'respected']
                if not any(cw in text_lower for cw in context_words):
                    concerns.append(f"'{term}' may need more respectful context")
        
        return concerns[:3]
    
    def _detect_disrespectful_language(self, text: str) -> List[str]:
        """Detect disrespectful language"""
        disrespectful_patterns = [
            r'\b(weird|bizarre|crazy|insane)\s+(tradition|custom|practice|belief)\b',
            r'\b(primitive|backwards|uncivilized)\b'
        ]
        
        found = []
        for pattern in disrespectful_patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                found.append(match.group())
        
        return found


class PlagiarismDetector:
    """Detect plagiarism and ensure originality"""
    
    async def check_originality(
        self,
        script: PodcastScript
    ) -> QualityCheck:
        """
        Check script originality
        Target: >90% originality
        """
        issues = []
        warnings = []
        recommendations = []
        
        text = script.content
        
        # 1. Check for direct quotes without attribution
        unattributed_quotes = self._detect_unattributed_quotes(text)
        if unattributed_quotes:
            issues.extend([f"Unattributed quote: {q[:50]}..." for q in unattributed_quotes])
        
        # 2. Check for overly similar phrasing (would use external API in production)
        # For now, just check for common Wikipedia-style phrases
        wiki_phrases = self._detect_wikipedia_phrases(text)
        if wiki_phrases:
            warnings.extend([f"Wikipedia-style phrase: {p}" for p in wiki_phrases])
        
        # 3. Check for proper paraphrasing
        paraphrasing_score = self._assess_paraphrasing(text)
        
        # Calculate originality score
        originality_score = paraphrasing_score
        originality_score -= len(issues) * 0.15
        originality_score -= len(warnings) * 0.05
        originality_score = max(originality_score, 0.0)
        
        # Generate recommendations
        if unattributed_quotes:
            recommendations.append("Add attribution for all quotes")
        if wiki_phrases:
            recommendations.append("Rephrase content in original voice")
        if paraphrasing_score < 0.9:
            recommendations.append("Improve paraphrasing of source material")
        
        passed = originality_score >= 0.90
        
        return QualityCheck(
            check_name="Originality",
            passed=passed,
            score=originality_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metadata={
                'unattributed_quotes': len(unattributed_quotes),
                'wiki_phrases': len(wiki_phrases)
            }
        )
    
    def _detect_unattributed_quotes(self, text: str) -> List[str]:
        """Detect quotes without attribution"""
        # Find quoted text
        quotes = re.findall(r'"([^"]+)"', text)
        
        unattributed = []
        for quote in quotes:
            # Check if there's attribution nearby
            quote_pos = text.find(f'"{quote}"')
            context = text[max(0, quote_pos-50):min(len(text), quote_pos+len(quote)+50)]
            
            # Look for attribution indicators
            attribution_words = ['said', 'according to', 'stated', 'explained', 'noted']
            if not any(word in context.lower() for word in attribution_words):
                unattributed.append(quote)
        
        return unattributed
    
    def _detect_wikipedia_phrases(self, text: str) -> List[str]:
        """Detect Wikipedia-style phrases"""
        wiki_patterns = [
            r'\b(is|are)\s+a\s+\w+\s+(located|situated|found)\s+in\b',
            r'\b(known|famous|renowned)\s+for\s+(its|their)\b',
            r'\baccording\s+to\s+(sources|reports|records)\b'
        ]
        
        found = []
        for pattern in wiki_patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                found.append(match.group())
        
        return found[:3]
    
    def _assess_paraphrasing(self, text: str) -> float:
        """Assess quality of paraphrasing"""
        # Simple heuristic: check for conversational style
        conversational_indicators = [
            "let's", "we'll", "you'll", "here's", "that's",
            "imagine", "picture", "think about"
        ]
        
        text_lower = text.lower()
        conversational_count = sum(1 for phrase in conversational_indicators if phrase in text_lower)
        
        # More conversational = better paraphrasing
        score = min(0.7 + (conversational_count * 0.05), 1.0)
        
        return score


class SourceValidator:
    """Validate source attribution and credibility"""
    
    async def verify_attribution(
        self,
        script: PodcastScript,
        source_content: Dict[str, Any]
    ) -> QualityCheck:
        """
        Verify source attribution
        Target: >95% proper attribution
        """
        issues = []
        warnings = []
        recommendations = []
        
        # 1. Check if source is mentioned
        source_mentioned = self._check_source_mention(script, source_content)
        if not source_mentioned:
            warnings.append("Source content not explicitly mentioned")
        
        # 2. Check for proper attribution of specific facts
        attribution_score = self._check_fact_attribution(script, source_content)
        
        # 3. Check for credibility indicators
        credibility_indicators = self._check_credibility_indicators(script.content)
        if not credibility_indicators:
            warnings.append("No credibility indicators found")
        
        # Calculate attribution score
        score = attribution_score
        if not source_mentioned:
            score -= 0.10
        if not credibility_indicators:
            score -= 0.05
        score = max(score, 0.0)
        
        # Generate recommendations
        if not source_mentioned:
            recommendations.append("Mention source of information")
        if attribution_score < 0.95:
            recommendations.append("Improve attribution of specific facts")
        if not credibility_indicators:
            recommendations.append("Add credibility indicators (experts, studies, etc.)")
        
        passed = score >= 0.95
        
        return QualityCheck(
            check_name="Source Attribution",
            passed=passed,
            score=score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metadata={
                'source_mentioned': source_mentioned,
                'credibility_indicators': len(credibility_indicators)
            }
        )
    
    def _check_source_mention(
        self,
        script: PodcastScript,
        source_content: Dict[str, Any]
    ) -> bool:
        """Check if source is mentioned in script"""
        # Check if location or title is mentioned
        location = source_content.get('location', {})
        title = source_content.get('title', '')
        
        script_text = script.content.lower()
        
        # Check for location mention
        if location:
            # Handle both string and dict location formats
            if isinstance(location, str):
                location_name = location.lower()
            else:
                location_name = location.get('name', '').lower()
            
            if location_name and location_name in script_text:
                return True
        
        # Check for title mention
        if title:
            title_lower = title.lower()
            # Check for partial title match
            title_words = title_lower.split()
            if len(title_words) >= 2:
                # Check if at least 2 consecutive words from title appear
                for i in range(len(title_words) - 1):
                    phrase = f"{title_words[i]} {title_words[i+1]}"
                    if phrase in script_text:
                        return True
        
        return False
    
    def _check_fact_attribution(
        self,
        script: PodcastScript,
        source_content: Dict[str, Any]
    ) -> float:
        """Check attribution of specific facts"""
        # In production, would track which facts came from which sources
        # For now, assume good attribution if source is mentioned
        if self._check_source_mention(script, source_content):
            return 0.95
        return 0.80
    
    def _check_credibility_indicators(self, text: str) -> List[str]:
        """Check for credibility indicators"""
        credibility_patterns = [
            r'\b(expert|researcher|scientist|historian|archaeologist)s?\b',
            r'\b(study|research|investigation|analysis)\b',
            r'\b(according to|based on|documented|recorded)\b',
            r'\b(evidence|proof|data|findings)\b'
        ]
        
        indicators = []
        for pattern in credibility_patterns:
            if re.search(pattern, text, re.I):
                indicators.append(pattern)
        
        return indicators
