"""
Question Detector
Detects if user input is a question vs a location using pattern matching
"""
import re
from typing import Dict, Optional
import structlog

logger = structlog.get_logger()


class QuestionDetector:
    """
    Detects questions and extracts locations from question text.
    Uses regex patterns to identify question indicators.
    """
    
    def __init__(self):
        # Question word patterns (case-insensitive)
        self.question_starters = [
            r'^what\s',
            r'^why\s',
            r'^how\s',
            r'^when\s',
            r'^where\s',
            r'^who\s',
            r'^which\s',
            r'^can\s+you\s+(explain|tell|describe)',
            r'^could\s+you\s+(explain|tell|describe)',
            r'^tell\s+me\s+about',
            r'^explain\s',
            r'^describe\s',
        ]
        
        # Question phrase indicators
        self.question_phrases = [
            r'history\s+of\s+',
            r'story\s+of\s+',
            r'origin\s+of\s+',
            r'significance\s+of\s+',
            r'importance\s+of\s+',
            r'meaning\s+of\s+',
            r'purpose\s+of\s+',
            r'reason\s+for\s+',
            r'cause\s+of\s+',
            r'impact\s+of\s+',
        ]
        
        # Compile patterns for efficiency
        self.starter_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.question_starters]
        self.phrase_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.question_phrases]
    
    def is_question(self, text: str) -> Dict:
        """
        Detect if input is a question.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with detection results
        """
        if not text or not isinstance(text, str):
            return {
                "is_question": False,
                "extracted_location": None,
                "question_type": None,
                "confidence": 0.0
            }
        
        text = text.strip()
        confidence = 0.0
        question_type = None
        
        # Check 1: Ends with question mark (strong indicator)
        ends_with_question_mark = text.endswith('?')
        if ends_with_question_mark:
            confidence += 0.5
        
        # Check 2: Starts with question word
        starts_with_question = False
        for pattern in self.starter_patterns:
            if pattern.match(text):
                starts_with_question = True
                # Extract question type
                match = pattern.match(text)
                if match:
                    question_type = match.group(0).strip().lower().split()[0]
                confidence += 0.4
                break
        
        # Check 3: Contains question phrase
        contains_question_phrase = False
        for pattern in self.phrase_patterns:
            if pattern.search(text):
                contains_question_phrase = True
                confidence += 0.3
                break
        
        # Determine if it's a question
        is_question = confidence >= 0.3 or (ends_with_question_mark and len(text.split()) > 2)
        
        # Extract location if present
        extracted_location = None
        if is_question:
            extracted_location = self.extract_location_from_question(text)
        
        result = {
            "is_question": is_question,
            "extracted_location": extracted_location,
            "question_type": question_type,
            "confidence": min(confidence, 1.0),
            "indicators": {
                "ends_with_question_mark": ends_with_question_mark,
                "starts_with_question_word": starts_with_question,
                "contains_question_phrase": contains_question_phrase
            }
        }
        
        logger.info("question_detection",
                   text=text[:50],
                   is_question=is_question,
                   confidence=result["confidence"],
                   question_type=question_type)
        
        return result
    
    def extract_location_from_question(self, question: str) -> Optional[str]:
        """
        Extract location name from question text.
        
        Examples:
        - "What's the history of Tokyo?" → "Tokyo"
        - "Why did the Roman Empire fall?" → "Roman Empire"
        - "How was the Eiffel Tower built?" → "Eiffel Tower"
        
        Args:
            question: Question text
            
        Returns:
            Extracted location or None
        """
        if not question:
            return None
        
        # Pattern 1: "of [Location]" (most common)
        of_pattern = r'\bof\s+(?:the\s+)?([A-Z][A-Za-z\s,\-\']+?)(?:\?|$|,|\s+in\s+|\s+at\s+)'
        match = re.search(of_pattern, question)
        if match:
            location = match.group(1).strip()
            # Clean up trailing words
            location = re.sub(r'\s+(and|or|but|with|from|to|for|by)\s*$', '', location, flags=re.IGNORECASE)
            return location
        
        # Pattern 2: "about [Location]"
        about_pattern = r'\babout\s+(?:the\s+)?([A-Z][A-Za-z\s,\-\']+?)(?:\?|$|,|\s+in\s+|\s+at\s+)'
        match = re.search(about_pattern, question)
        if match:
            location = match.group(1).strip()
            location = re.sub(r'\s+(and|or|but|with|from|to|for|by)\s*$', '', location, flags=re.IGNORECASE)
            return location
        
        # Pattern 3: Capitalized words (likely proper nouns)
        # Look for sequences of capitalized words
        cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.findall(cap_pattern, question)
        
        if matches:
            # Filter out common question words
            question_words = {'What', 'Why', 'How', 'When', 'Where', 'Who', 'Which', 'Tell', 'Explain', 'Describe'}
            filtered = [m for m in matches if m not in question_words]
            
            if filtered:
                # Return the longest match (likely the full location name)
                location = max(filtered, key=len)
                return location
        
        return None
    
    def get_question_type(self, text: str) -> Optional[str]:
        """
        Get the type of question (what, why, how, etc.)
        
        Args:
            text: Question text
            
        Returns:
            Question type or None
        """
        detection = self.is_question(text)
        return detection.get("question_type")


# Singleton instance
question_detector = QuestionDetector()
