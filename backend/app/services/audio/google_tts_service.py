"""
Google Cloud Text-to-Speech Service
Handles audio synthesis using Google Cloud TTS API
"""
import asyncio
import time
import os
import base64
import json
import tempfile
from typing import Dict, Optional, Any
import structlog
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()

# Try to import Google Cloud TTS
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    logger.warning("google-cloud-texttospeech not available - install with: pip install google-cloud-texttospeech")


class GoogleTTSService:
    """
    Google Cloud Text-to-Speech service for podcast audio generation
    Uses Neural2 voices for high-quality, natural-sounding speech
    """
    
    def __init__(self):
        """Initialize Google TTS client"""
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Voice configurations
        self.voices = {
            'free': {
                'name': 'en-US-Standard-A',
                'type': 'STANDARD',
                'cost_per_char': 0.000004
            },
            'premium': {
                'name': 'en-US-Neural2-A',
                'type': 'NEURAL2',
                'cost_per_char': 0.000016
            }
        }
        
        # Initialize client if available
        if GOOGLE_TTS_AVAILABLE:
            try:
                # Check for base64 encoded credentials (for Railway/cloud deployment)
                base64_creds = os.getenv("GOOGLE_CREDENTIALS_BASE64")
                
                if base64_creds:
                    # Decode base64 credentials and create temporary file
                    logger.info("using_base64_credentials")
                    creds_json = base64.b64decode(base64_creds).decode('utf-8')
                    creds_dict = json.loads(creds_json)
                    
                    # Create temporary credentials file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(creds_dict, f)
                        temp_creds_path = f.name
                    
                    # Set environment variable to temp file
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
                    logger.info("google_tts_credentials_decoded", path=temp_creds_path)
                
                # Initialize client (will use GOOGLE_APPLICATION_CREDENTIALS or default)
                self.client = texttospeech.TextToSpeechClient()
                logger.info("google_tts_initialized", status="success")
            except Exception as e:
                logger.error("google_tts_initialization_failed", error=str(e))
                self.client = None
        else:
            logger.warning("google_tts_not_available", 
                         message="Install google-cloud-texttospeech to enable audio generation")
    
    async def synthesize_speech(
        self,
        text: str,
        voice_tier: str = 'free',
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        language_code: str = 'en-US'
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using Google Cloud TTS
        
        Args:
            text: Script text to synthesize
            voice_tier: 'free' (Standard) or 'premium' (Neural2)
            speaking_rate: Speed of speech (0.25-4.0, default 1.0)
            pitch: Pitch adjustment (-20.0 to 20.0, default 0.0)
            language_code: Language code (default 'en-US')
            
        Returns:
            Dictionary with audio_content, format, synthesis_time, character_count, cost_estimate
        """
        if not self.client:
            logger.error("google_tts_not_initialized")
            return {
                'success': False,
                'error': 'Google TTS not available',
                'audio_content': None
            }
        
        try:
            logger.info("tts_synthesis_started",
                       text_length=len(text),
                       voice_tier=voice_tier,
                       speaking_rate=speaking_rate)
            
            start_time = time.time()
            
            # Get voice configuration
            voice_config = self.voices.get(voice_tier, self.voices['free'])
            
            # Run synthesis in executor (blocking call)
            loop = asyncio.get_event_loop()
            audio_content = await loop.run_in_executor(
                self.executor,
                self._synthesize_blocking,
                text,
                voice_config,
                speaking_rate,
                pitch,
                language_code
            )
            
            synthesis_time = time.time() - start_time
            
            # Calculate metrics
            character_count = len(text)
            cost_estimate = character_count * voice_config['cost_per_char']
            
            logger.info("tts_synthesis_complete",
                       synthesis_time=round(synthesis_time, 2),
                       character_count=character_count,
                       cost_estimate=round(cost_estimate, 4),
                       voice_type=voice_config['type'])
            
            return {
                'success': True,
                'audio_content': audio_content,
                'format': 'mp3',
                'synthesis_time': round(synthesis_time, 2),
                'character_count': character_count,
                'cost_estimate': round(cost_estimate, 4),
                'voice_name': voice_config['name'],
                'voice_type': voice_config['type']
            }
            
        except Exception as e:
            logger.error("tts_synthesis_failed", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'audio_content': None
            }
    
    def _synthesize_blocking(
        self,
        text: str,
        voice_config: Dict,
        speaking_rate: float,
        pitch: float,
        language_code: str
    ) -> bytes:
        """
        Blocking synthesis call (runs in executor)
        
        Args:
            text: Text to synthesize
            voice_config: Voice configuration dict
            speaking_rate: Speaking rate
            pitch: Pitch adjustment
            language_code: Language code
            
        Returns:
            Audio content as bytes
        """
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_config['name']
        )
        
        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch
        )
        
        # Perform the text-to-speech request
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content
    
    def get_voice_options(self) -> Dict[str, Any]:
        """Get available voice options and pricing"""
        return {
            'voices': self.voices,
            'available': GOOGLE_TTS_AVAILABLE and self.client is not None,
            'free_tier_limits': {
                'standard_chars_per_month': 4_000_000,
                'neural_chars_per_month': 1_000_000
            }
        }
    
    def estimate_cost(self, text: str, voice_tier: str = 'free') -> Dict[str, Any]:
        """
        Estimate cost for synthesizing text
        
        Args:
            text: Text to synthesize
            voice_tier: 'free' or 'premium'
            
        Returns:
            Cost estimate details
        """
        voice_config = self.voices.get(voice_tier, self.voices['free'])
        character_count = len(text)
        cost = character_count * voice_config['cost_per_char']
        
        # Estimate duration (150 words per minute)
        word_count = len(text.split())
        duration_minutes = word_count / 150
        
        return {
            'character_count': character_count,
            'word_count': word_count,
            'estimated_duration_minutes': round(duration_minutes, 2),
            'estimated_cost_usd': round(cost, 4),
            'voice_tier': voice_tier,
            'voice_type': voice_config['type']
        }


# Singleton instance
google_tts_service = GoogleTTSService()
