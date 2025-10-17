"""
Audio Delivery System
Cloud storage, CDN distribution, and streaming setup
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import structlog

from .models import (
    ProcessedAudio,
    AudioDelivery,
    StreamingConfig,
    DeliveryMetrics,
    AudioFormat
)

logger = structlog.get_logger()


class AudioDeliverySystem:
    """
    Comprehensive audio delivery system
    Handles storage, CDN distribution, and streaming
    """
    
    def __init__(self):
        self.storage = AudioStorageManager()
        self.cdn = CDNManager()
        self.streaming = StreamingManager()
        
        # Delivery statistics
        self.delivery_stats = []
    
    async def deliver_audio(
        self,
        processed_audio: ProcessedAudio,
        user_id: str,
        content_id: str,
        enable_streaming: bool = True
    ) -> AudioDelivery:
        """
        Main method to deliver audio
        
        Args:
            processed_audio: Processed audio ready for delivery
            user_id: User ID for tracking
            content_id: Content ID for organization
            enable_streaming: Enable streaming capabilities
            
        Returns:
            AudioDelivery with URLs and configuration
        """
        logger.info("audio_delivery_started",
                   user_id=user_id,
                   content_id=content_id,
                   file_size=processed_audio.file_size_bytes)
        
        try:
            # Step 1: Store audio in cloud storage
            storage_url = await self.storage.store_audio(
                audio_data=processed_audio.audio_data,
                user_id=user_id,
                content_id=content_id,
                format=processed_audio.format,
                metadata={
                    'duration': processed_audio.duration_seconds,
                    'bitrate': processed_audio.bitrate,
                    'quality_score': processed_audio.quality_metrics.clarity_score
                }
            )
            
            # Step 2: Upload to CDN for global delivery
            cdn_url = await self.cdn.upload_audio(
                audio_data=processed_audio.audio_data,
                storage_url=storage_url,
                content_id=content_id,
                cache_duration=86400  # 24 hours
            )
            
            # Step 3: Setup streaming (if enabled)
            streaming_config = None
            if enable_streaming:
                streaming_config = await self.streaming.setup_streaming(
                    cdn_url=cdn_url,
                    audio_metadata={
                        'duration': processed_audio.duration_seconds,
                        'format': processed_audio.format.value,
                        'bitrate': processed_audio.bitrate
                    },
                    adaptive_streaming=True
                )
            
            # Create delivery result
            delivery = AudioDelivery(
                download_url=cdn_url,
                streaming_url=streaming_config.url if streaming_config else None,
                cdn_url=cdn_url,
                playback_options={
                    'format': processed_audio.format.value,
                    'duration': processed_audio.duration_seconds,
                    'bitrate': processed_audio.bitrate,
                    'can_stream': enable_streaming
                },
                quality_variants=streaming_config.quality_variants if streaming_config else [],
                expiry_time=datetime.utcnow() + timedelta(days=7),
                cache_headers={
                    'Cache-Control': 'public, max-age=86400',
                    'ETag': self._generate_etag(processed_audio.audio_data)
                },
                metadata={
                    'user_id': user_id,
                    'content_id': content_id,
                    'storage_url': storage_url,
                    'file_size': processed_audio.file_size_bytes
                }
            )
            
            logger.info("audio_delivery_complete",
                       cdn_url=cdn_url,
                       streaming_enabled=enable_streaming)
            
            return delivery
            
        except Exception as e:
            logger.error("audio_delivery_failed",
                        error=str(e),
                        user_id=user_id,
                        content_id=content_id)
            raise
    
    async def track_delivery_metrics(
        self,
        delivery: AudioDelivery,
        download_time_ms: float,
        first_byte_time_ms: float,
        cdn_hit: bool,
        region: str,
        user_agent: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Track delivery performance metrics"""
        metrics = DeliveryMetrics(
            download_time_ms=download_time_ms,
            first_byte_time_ms=first_byte_time_ms,
            cdn_hit=cdn_hit,
            geographic_region=region,
            user_agent=user_agent,
            success=success,
            error_message=error
        )
        
        self.delivery_stats.append(metrics)
        
        logger.info("delivery_metrics_tracked",
                   download_time=download_time_ms,
                   cdn_hit=cdn_hit,
                   region=region)
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics summary"""
        if not self.delivery_stats:
            return {
                'total_deliveries': 0,
                'average_download_time': 0.0,
                'cdn_hit_rate': 0.0,
                'success_rate': 0.0
            }
        
        total = len(self.delivery_stats)
        successful = sum(1 for m in self.delivery_stats if m.success)
        cdn_hits = sum(1 for m in self.delivery_stats if m.cdn_hit)
        
        return {
            'total_deliveries': total,
            'average_download_time': sum(m.download_time_ms for m in self.delivery_stats) / total,
            'average_first_byte_time': sum(m.first_byte_time_ms for m in self.delivery_stats) / total,
            'cdn_hit_rate': (cdn_hits / total) * 100,
            'success_rate': (successful / total) * 100,
            'by_region': self._group_by_region()
        }
    
    def _group_by_region(self) -> Dict[str, Dict[str, Any]]:
        """Group delivery stats by geographic region"""
        by_region = {}
        
        for metric in self.delivery_stats:
            region = metric.geographic_region
            if region not in by_region:
                by_region[region] = {
                    'count': 0,
                    'total_download_time': 0.0,
                    'successes': 0
                }
            
            by_region[region]['count'] += 1
            by_region[region]['total_download_time'] += metric.download_time_ms
            if metric.success:
                by_region[region]['successes'] += 1
        
        # Calculate averages
        for region in by_region:
            count = by_region[region]['count']
            by_region[region]['average_download_time'] = by_region[region]['total_download_time'] / count
            by_region[region]['success_rate'] = (by_region[region]['successes'] / count) * 100
        
        return by_region
    
    def _generate_etag(self, audio_data: bytes) -> str:
        """Generate ETag for caching"""
        return hashlib.md5(audio_data).hexdigest()


class AudioStorageManager:
    """Manage audio storage in cloud"""
    
    async def store_audio(
        self,
        audio_data: bytes,
        user_id: str,
        content_id: str,
        format: AudioFormat,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store audio in cloud storage with geographic distribution
        
        Args:
            audio_data: Audio data to store
            user_id: User ID for organization
            content_id: Content ID
            format: Audio format
            metadata: Additional metadata
            
        Returns:
            Storage URL
        """
        logger.debug("storing_audio",
                    user_id=user_id,
                    content_id=content_id,
                    size=len(audio_data))
        
        # Mock implementation - in production would use:
        # - AWS S3 with intelligent tiering
        # - Google Cloud Storage
        # - Azure Blob Storage
        
        # Generate storage path
        storage_path = f"audio/{user_id}/{content_id}.{format.value}"
        
        # Mock storage URL
        storage_url = f"https://storage.example.com/{storage_path}"
        
        # In production would:
        # 1. Upload to cloud storage
        # 2. Set storage class (intelligent tiering)
        # 3. Enable encryption
        # 4. Set lifecycle policies
        # 5. Add metadata tags
        
        logger.info("audio_stored",
                   storage_url=storage_url,
                   size=len(audio_data))
        
        return storage_url


class CDNManager:
    """Manage CDN distribution"""
    
    async def upload_audio(
        self,
        audio_data: bytes,
        storage_url: str,
        content_id: str,
        cache_duration: int = 86400
    ) -> str:
        """
        Upload audio to CDN for global distribution
        
        Args:
            audio_data: Audio data
            storage_url: Original storage URL
            content_id: Content ID
            cache_duration: Cache duration in seconds
            
        Returns:
            CDN URL
        """
        logger.debug("uploading_to_cdn",
                    content_id=content_id,
                    cache_duration=cache_duration)
        
        # Mock implementation - in production would use:
        # - CloudFront (AWS)
        # - Cloud CDN (Google)
        # - Azure CDN
        # - Cloudflare
        
        # Generate CDN URL
        cdn_url = f"https://cdn.example.com/audio/{content_id}"
        
        # In production would:
        # 1. Upload to CDN edge locations
        # 2. Set cache headers
        # 3. Enable compression
        # 4. Configure geographic distribution
        # 5. Set up invalidation rules
        
        logger.info("audio_uploaded_to_cdn",
                   cdn_url=cdn_url,
                   cache_duration=cache_duration)
        
        return cdn_url


class StreamingManager:
    """Manage streaming configuration"""
    
    async def setup_streaming(
        self,
        cdn_url: str,
        audio_metadata: Dict[str, Any],
        adaptive_streaming: bool = True,
        segment_duration: int = 10
    ) -> StreamingConfig:
        """
        Setup streaming capabilities with adaptive bitrate
        
        Args:
            cdn_url: CDN URL for audio
            audio_metadata: Audio metadata
            adaptive_streaming: Enable adaptive streaming
            segment_duration: Segment duration in seconds
            
        Returns:
            StreamingConfig with URLs and options
        """
        logger.debug("setting_up_streaming",
                    cdn_url=cdn_url,
                    adaptive=adaptive_streaming)
        
        # Mock implementation - in production would:
        # 1. Generate HLS/DASH manifests
        # 2. Create multiple quality variants
        # 3. Segment audio files
        # 4. Upload segments to CDN
        # 5. Configure adaptive bitrate switching
        
        # Generate streaming URL
        streaming_url = f"{cdn_url}/stream.m3u8"
        
        # Create quality variants
        quality_variants = []
        
        if adaptive_streaming:
            quality_variants = [
                {
                    'quality': 'high',
                    'bitrate': '192kbps',
                    'url': f"{cdn_url}/high/stream.m3u8"
                },
                {
                    'quality': 'medium',
                    'bitrate': '128kbps',
                    'url': f"{cdn_url}/medium/stream.m3u8"
                },
                {
                    'quality': 'low',
                    'bitrate': '96kbps',
                    'url': f"{cdn_url}/low/stream.m3u8"
                }
            ]
        
        config = StreamingConfig(
            url=streaming_url,
            protocol='HLS',  # HTTP Live Streaming
            segment_duration=segment_duration,
            quality_variants=quality_variants,
            adaptive_streaming=adaptive_streaming,
            buffer_size=30,  # 30 seconds buffer
            options={
                'format': audio_metadata.get('format'),
                'duration': audio_metadata.get('duration'),
                'can_seek': True,
                'can_download': True
            }
        )
        
        logger.info("streaming_setup_complete",
                   streaming_url=streaming_url,
                   variants=len(quality_variants))
        
        return config


# Convenience function
async def deliver_audio_file(
    processed_audio: ProcessedAudio,
    user_id: str,
    content_id: str,
    enable_streaming: bool = True
) -> AudioDelivery:
    """
    Convenience function to deliver audio
    
    Args:
        processed_audio: Processed audio
        user_id: User ID
        content_id: Content ID
        enable_streaming: Enable streaming
        
    Returns:
        AudioDelivery with URLs
    """
    delivery_system = AudioDeliverySystem()
    
    return await delivery_system.deliver_audio(
        processed_audio=processed_audio,
        user_id=user_id,
        content_id=content_id,
        enable_streaming=enable_streaming
    )
