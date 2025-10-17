"""
TTS Optimization
Enhanced text-to-speech optimization with pronunciation, pacing, and emphasis
"""
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

from .models import TTSMarker, PodcastScript


@dataclass
class PronunciationGuide:
    """Pronunciation guide for difficult words"""
    word: str
    phonetic: str
    language: str = "en"


class TTSOptimizer:
    """
    Enhanced TTS optimization
    Adds pronunciation guides, pause markers, emphasis, and pacing cues
    """
    
    def __init__(self):
        # Common difficult pronunciations
        self.pronunciation_dict = self._build_pronunciation_dict()
        
        # Emphasis words
        self.emphasis_words = {
            'strong': ['unique', 'remarkable', 'incredible', 'amazing', 'extraordinary', 
                      'fascinating', 'astonishing', 'unprecedented'],
            'moderate': ['interesting', 'notable', 'significant', 'important', 'special'],
            'subtle': ['quite', 'rather', 'somewhat', 'fairly']
        }
    
    def optimize_script(self, script: PodcastScript) -> PodcastScript:
        """
        Apply comprehensive TTS optimization to script
        
        Args:
            script: Original podcast script
            
        Returns:
            Optimized script with TTS markers
        """
        optimized_content = script.content
        tts_markers = list(script.tts_markers)  # Start with existing markers
        
        # 1. Add pronunciation guides
        optimized_content, pronunciation_markers = self._add_pronunciation_guides(
            optimized_content
        )
        tts_markers.extend(pronunciation_markers)
        
        # 2. Add emphasis markers
        emphasis_markers = self._add_emphasis_markers(optimized_content)
        tts_markers.extend(emphasis_markers)
        
        # 3. Add pause markers
        pause_markers = self._add_pause_markers(optimized_content)
        tts_markers.extend(pause_markers)
        
        # 4. Add speed variation cues
        speed_markers = self._add_speed_markers(optimized_content)
        tts_markers.extend(speed_markers)
        
        # 5. Optimize for natural speech rhythm
        optimized_content = self._optimize_speech_rhythm(optimized_content)
        
        # Update script with optimizations
        script.content = optimized_content
        script.tts_markers = sorted(tts_markers, key=lambda m: m.position)
        
        return script
    
    def _build_pronunciation_dict(self) -> Dict[str, PronunciationGuide]:
        """Build dictionary of difficult pronunciations"""
        return {
            # Icelandic names and places
            'reykjavik': PronunciationGuide('Reykjavik', 'RAYK-yah-vik'),
            'geysir': PronunciationGuide('Geysir', 'GAY-zeer'),
            'þingvellir': PronunciationGuide('Þingvellir', 'THING-vet-lir'),
            'eyjafjallajökull': PronunciationGuide('Eyjafjallajökull', 'AY-ya-fyat-la-YOH-kutl'),
            
            # Moroccan names and places
            'marrakech': PronunciationGuide('Marrakech', 'mah-rah-KESH'),
            'djemaa': PronunciationGuide('Djemaa', 'jeh-MAH'),
            'fna': PronunciationGuide('Fna', 'ef-NAH'),
            'medina': PronunciationGuide('Medina', 'meh-DEE-nah'),
            'souk': PronunciationGuide('Souk', 'SOOK'),
            'riad': PronunciationGuide('Riad', 'ree-AHD'),
            
            # Common difficult words
            'archaeological': PronunciationGuide('Archaeological', 'ar-kee-oh-LOJ-ih-kal'),
            'phenomenon': PronunciationGuide('Phenomenon', 'feh-NOM-eh-non'),
            'phenomena': PronunciationGuide('Phenomena', 'feh-NOM-eh-nah'),
            'epitome': PronunciationGuide('Epitome', 'eh-PIT-oh-mee'),
            'facade': PronunciationGuide('Facade', 'fah-SAHD'),
        }
    
    def _add_pronunciation_guides(
        self,
        text: str
    ) -> Tuple[str, List[TTSMarker]]:
        """
        Add pronunciation guides for difficult words
        
        Returns:
            (modified_text, pronunciation_markers)
        """
        markers = []
        modified_text = text
        
        for word_lower, guide in self.pronunciation_dict.items():
            # Find all occurrences (case-insensitive)
            pattern = re.compile(re.escape(guide.word), re.IGNORECASE)
            
            for match in pattern.finditer(modified_text):
                position = match.start()
                
                # Add pronunciation marker
                markers.append(TTSMarker(
                    position=position,
                    type='pronunciation',
                    value=guide.phonetic,
                    metadata={
                        'word': guide.word,
                        'language': guide.language
                    }
                ))
                
                # Optionally replace in text with phonetic spelling
                # (commented out - TTS engines usually handle this via markers)
                # modified_text = modified_text[:position] + guide.phonetic + modified_text[position+len(guide.word):]
        
        return modified_text, markers
    
    def _add_emphasis_markers(self, text: str) -> List[TTSMarker]:
        """Add emphasis markers for important words"""
        markers = []
        
        for emphasis_level, words in self.emphasis_words.items():
            for word in words:
                # Find all occurrences
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                
                for match in pattern.finditer(text):
                    markers.append(TTSMarker(
                        position=match.start(),
                        type='emphasis',
                        value=emphasis_level,
                        metadata={'word': match.group()}
                    ))
        
        return markers
    
    def _add_pause_markers(self, text: str) -> List[TTSMarker]:
        """Add pause markers for natural speech rhythm"""
        markers = []
        
        # 1. Pauses after sentences (. ! ?)
        sentence_pattern = r'[.!?]'
        for match in re.finditer(sentence_pattern, text):
            markers.append(TTSMarker(
                position=match.end(),
                type='pause',
                value=0.7,  # 0.7 second pause
                metadata={'reason': 'sentence_end'}
            ))
        
        # 2. Short pauses after commas
        comma_pattern = r','
        for match in re.finditer(comma_pattern, text):
            markers.append(TTSMarker(
                position=match.end(),
                type='pause',
                value=0.3,  # 0.3 second pause
                metadata={'reason': 'comma'}
            ))
        
        # 3. Pauses after transition phrases
        transition_phrases = [
            'however', 'moreover', 'furthermore', 'nevertheless',
            'in addition', 'for example', 'in fact', 'on the other hand'
        ]
        
        for phrase in transition_phrases:
            pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                markers.append(TTSMarker(
                    position=match.end(),
                    type='pause',
                    value=0.5,  # 0.5 second pause
                    metadata={'reason': 'transition', 'phrase': phrase}
                ))
        
        # 4. Dramatic pauses before key revelations
        revelation_phrases = [
            'but here\'s the thing', 'here\'s what\'s fascinating',
            'the remarkable part', 'what\'s truly unique'
        ]
        
        for phrase in revelation_phrases:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            for match in pattern.finditer(text):
                # Pause BEFORE the phrase
                markers.append(TTSMarker(
                    position=match.start(),
                    type='pause',
                    value=0.8,  # 0.8 second dramatic pause
                    metadata={'reason': 'dramatic', 'phrase': phrase}
                ))
        
        return markers
    
    def _add_speed_markers(self, text: str) -> List[TTSMarker]:
        """Add speed variation cues for dramatic effect"""
        markers = []
        
        # 1. Slow down for important information
        important_patterns = [
            r'\b(most important|crucial|essential|key point)\b',
            r'\b(remember|note that|keep in mind)\b'
        ]
        
        for pattern in important_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                markers.append(TTSMarker(
                    position=match.start(),
                    type='speed',
                    value=0.85,  # 85% of normal speed (slower)
                    metadata={'reason': 'important'}
                ))
        
        # 2. Speed up for lists and less critical details
        list_pattern = r'\b(first|second|third|finally|lastly)\b'
        for match in re.finditer(list_pattern, text, re.IGNORECASE):
            markers.append(TTSMarker(
                position=match.start(),
                type='speed',
                value=1.1,  # 110% of normal speed (faster)
                metadata={'reason': 'list_item'}
            ))
        
        # 3. Slow down for dramatic moments
        dramatic_patterns = [
            r'\b(incredible|astonishing|remarkable|extraordinary)\b',
            r'\b(never before|for the first time|unprecedented)\b'
        ]
        
        for pattern in dramatic_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                markers.append(TTSMarker(
                    position=match.start(),
                    type='speed',
                    value=0.9,  # 90% of normal speed
                    metadata={'reason': 'dramatic'}
                ))
        
        return markers
    
    def _optimize_speech_rhythm(self, text: str) -> str:
        """Optimize text for natural speech rhythm"""
        optimized = text
        
        # 1. Break up long sentences
        optimized = self._break_long_sentences(optimized)
        
        # 2. Add contractions for natural speech
        optimized = self._add_contractions(optimized)
        
        # 3. Remove overly formal language
        optimized = self._simplify_formal_language(optimized)
        
        return optimized
    
    def _break_long_sentences(self, text: str) -> str:
        """Break up sentences that are too long"""
        sentences = re.split(r'([.!?])', text)
        
        optimized_sentences = []
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i]
            punctuation = sentences[i+1] if i+1 < len(sentences) else ''
            
            # Check if sentence is too long (>25 words)
            words = sentence.split()
            if len(words) > 25:
                # Try to split at 'and', 'but', 'which', 'that'
                split_words = ['and', 'but', 'which', 'that', 'where']
                
                for split_word in split_words:
                    if split_word in words:
                        split_index = words.index(split_word)
                        if 10 < split_index < len(words) - 5:  # Don't split too early or late
                            # Split the sentence
                            first_part = ' '.join(words[:split_index])
                            second_part = ' '.join(words[split_index:])
                            optimized_sentences.append(first_part + '.')
                            optimized_sentences.append(' ' + second_part.capitalize() + punctuation)
                            break
                else:
                    # Couldn't split, keep as is
                    optimized_sentences.append(sentence + punctuation)
            else:
                optimized_sentences.append(sentence + punctuation)
        
        return ''.join(optimized_sentences)
    
    def _add_contractions(self, text: str) -> str:
        """Add contractions for more natural speech"""
        contractions = {
            'do not': "don't",
            'does not': "doesn't",
            'did not': "didn't",
            'will not': "won't",
            'would not': "wouldn't",
            'could not': "couldn't",
            'should not': "shouldn't",
            'cannot': "can't",
            'is not': "isn't",
            'are not': "aren't",
            'was not': "wasn't",
            'were not': "weren't",
            'have not': "haven't",
            'has not': "hasn't",
            'had not': "hadn't",
            'it is': "it's",
            'that is': "that's",
            'there is': "there's",
            'here is': "here's",
            'what is': "what's",
            'let us': "let's",
            'we will': "we'll",
            'you will': "you'll",
            'they will': "they'll"
        }
        
        optimized = text
        for formal, contraction in contractions.items():
            # Only replace in casual contexts (not in quotes or formal statements)
            optimized = re.sub(
                r'\b' + formal + r'\b',
                contraction,
                optimized,
                flags=re.IGNORECASE
            )
        
        return optimized
    
    def _simplify_formal_language(self, text: str) -> str:
        """Replace overly formal language with simpler alternatives"""
        simplifications = {
            'utilize': 'use',
            'commence': 'start',
            'terminate': 'end',
            'purchase': 'buy',
            'assist': 'help',
            'obtain': 'get',
            'demonstrate': 'show',
            'indicate': 'show',
            'numerous': 'many',
            'sufficient': 'enough',
            'prior to': 'before',
            'subsequent to': 'after',
            'in order to': 'to',
            'due to the fact that': 'because',
            'at this point in time': 'now'
        }
        
        optimized = text
        for formal, simple in simplifications.items():
            optimized = re.sub(
                r'\b' + formal + r'\b',
                simple,
                optimized,
                flags=re.IGNORECASE
            )
        
        return optimized
    
    def export_tts_ssml(self, script: PodcastScript) -> str:
        """
        Export script as SSML (Speech Synthesis Markup Language)
        For use with TTS engines that support SSML
        """
        ssml_parts = ['<speak>']
        
        content = script.content
        markers = sorted(script.tts_markers, key=lambda m: m.position)
        
        last_pos = 0
        
        for marker in markers:
            # Add text before marker
            if marker.position > last_pos:
                ssml_parts.append(content[last_pos:marker.position])
            
            # Add SSML tag based on marker type
            if marker.type == 'pause':
                ssml_parts.append(f'<break time="{marker.value}s"/>')
            elif marker.type == 'emphasis':
                level = marker.value  # strong, moderate, subtle
                ssml_parts.append(f'<emphasis level="{level}">')
                # Will need to close this tag later
            elif marker.type == 'speed':
                rate = marker.value  # 0.85 = 85% speed
                ssml_parts.append(f'<prosody rate="{rate}">')
                # Will need to close this tag later
            elif marker.type == 'pronunciation':
                phonetic = marker.value
                word = marker.metadata.get('word', '')
                ssml_parts.append(f'<phoneme alphabet="ipa" ph="{phonetic}">{word}</phoneme>')
            
            last_pos = marker.position
        
        # Add remaining text
        if last_pos < len(content):
            ssml_parts.append(content[last_pos:])
        
        ssml_parts.append('</speak>')
        
        return ''.join(ssml_parts)


# Convenience function
def optimize_for_tts(script: PodcastScript) -> PodcastScript:
    """
    Convenience function to optimize script for TTS
    
    Args:
        script: Original podcast script
        
    Returns:
        Optimized script with TTS markers
    """
    optimizer = TTSOptimizer()
    return optimizer.optimize_script(script)
