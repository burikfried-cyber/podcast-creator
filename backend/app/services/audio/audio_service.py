"""
Audio Service Manager
Manages podcast audio generation, storage, and serving
"""
import os
import time
import hashlib
from typing import Dict, Optional, Any
from pathlib import Path
import structlog

from .google_tts_service import google_tts_service

logger = structlog.get_logger()


class AudioService:
    """
    Audio service manager for podcast audio generation
    Wraps Google TTS and handles file storage
    """
    
    def __init__(self):
        """Initialize audio service"""
        self.tts_service = google_tts_service
        
        # Get audio storage path from environment or use default
        self.audio_dir = os.getenv("AUDIO_STORAGE_PATH", "/tmp/podcast_audio")
        
        # Create directory if it doesn't exist
        os.makedirs(self.audio_dir, exist_ok=True)
        logger.info("audio_service_initialized", audio_dir=self.audio_dir)
    
    async def generate_podcast_audio(
        self,
        script_text: str,
        podcast_id: str,
        user_tier: str = 'free',
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate podcast audio from script text
        
        Args:
            script_text: Complete podcast script
            podcast_id: Unique podcast identifier
            user_tier: 'free' or 'premium' (determines voice quality)
            speaking_rate: Speed of speech (0.25-4.0)
            pitch: Pitch adjustment (-20.0 to 20.0)
            
        Returns:
            Dictionary with audio_url, file_path, duration, size, cost
        """
        try:
            logger.info("audio_generation_started",
                       podcast_id=podcast_id,
                       script_length=len(script_text),
                       user_tier=user_tier)
            
            start_time = time.time()
            
            # Synthesize speech using Google TTS
            synthesis_result = await self.tts_service.synthesize_speech(
                text=script_text,
                voice_tier=user_tier,
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            
            if not synthesis_result.get('success'):
                error_msg = synthesis_result.get('error', 'Unknown TTS error')
                logger.error("audio_synthesis_failed", error=error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'audio_url': None
                }
            
            # Get audio content
            audio_content = synthesis_result['audio_content']
            
            # Generate filename
            filename = self._generate_filename(podcast_id, 'mp3')
            file_path = os.path.join(self.audio_dir, filename)
            
            # Save audio file
            with open(file_path, 'wb') as f:
                f.write(audio_content)
            
            # Calculate metrics
            file_size = len(audio_content)
            word_count = len(script_text.split())
            duration_seconds = int((word_count / 150) * 60)  # 150 words per minute
            
            # Generate audio URL
            audio_url = f"/audio/{filename}"
            
            generation_time = time.time() - start_time
            
            logger.info("audio_generation_complete",
                       podcast_id=podcast_id,
                       file_path=file_path,
                       file_size=file_size,
                       duration_seconds=duration_seconds,
                       generation_time=round(generation_time, 2),
                       cost=synthesis_result.get('cost_estimate', 0))
            
            return {
                'success': True,
                'audio_url': audio_url,
                'file_path': file_path,
                'filename': filename,
                'duration_seconds': duration_seconds,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'generation_time': round(generation_time, 2),
                'synthesis_time': synthesis_result.get('synthesis_time', 0),
                'character_count': synthesis_result.get('character_count', 0),
                'cost_estimate': synthesis_result.get('cost_estimate', 0),
                'voice_name': synthesis_result.get('voice_name', ''),
                'voice_type': synthesis_result.get('voice_type', '')
            }
            
        except Exception as e:
            logger.error("audio_generation_error", error=str(e), podcast_id=podcast_id)
            return {
                'success': False,
                'error': str(e),
                'audio_url': None
            }
    
    def _generate_filename(self, podcast_id: str, extension: str) -> str:
        """
        Generate unique filename for audio file
        
        Args:
            podcast_id: Podcast identifier
            extension: File extension (e.g., 'mp3')
            
        Returns:
            Filename string
        """
        # Create hash of podcast_id for uniqueness
        hash_suffix = hashlib.md5(podcast_id.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        return f"podcast_{podcast_id}_{timestamp}_{hash_suffix}.{extension}"
    
    def get_audio_path(self, filename: str) -> Optional[str]:
        """
        Get full path to audio file
        
        Args:
            filename: Audio filename
            
        Returns:
            Full file path or None if not found
        """
        file_path = os.path.join(self.audio_dir, filename)
        if os.path.exists(file_path):
            return file_path
        return None
    
    def delete_audio(self, filename: str) -> bool:
        """
        Delete audio file
        
        Args:
            filename: Audio filename
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            file_path = os.path.join(self.audio_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("audio_deleted", filename=filename)
                return True
            return False
        except Exception as e:
            logger.error("audio_deletion_failed", error=str(e), filename=filename)
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get audio storage statistics
        
        Returns:
            Storage statistics dictionary
        """
        try:
            files = os.listdir(self.audio_dir)
            audio_files = [f for f in files if f.endswith('.mp3')]
            
            total_size = sum(
                os.path.getsize(os.path.join(self.audio_dir, f))
                for f in audio_files
            )
            
            return {
                'audio_directory': self.audio_dir,
                'total_files': len(audio_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': audio_files[:10]  # First 10 files
            }
        except Exception as e:
            logger.error("storage_stats_error", error=str(e))
            return {
                'error': str(e)
            }
    
    def estimate_generation_cost(
        self,
        script_text: str,
        user_tier: str = 'free'
    ) -> Dict[str, Any]:
        """
        Estimate cost and duration for audio generation
        
        Args:
            script_text: Script text
            user_tier: 'free' or 'premium'
            
        Returns:
            Cost and duration estimates
        """
        return self.tts_service.estimate_cost(script_text, user_tier)


# Singleton instance
audio_service = AudioService()
