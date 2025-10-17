"""
Data models for audio synthesis and delivery system
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta


class UserTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    ULTRA_PREMIUM = "ultra_premium"


class AudioFormat(str, Enum):
    """Supported audio formats"""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"
    AAC = "aac"


class TTSProviderTier(str, Enum):
    """TTS provider tiers"""
    FREE = "free"
    PREMIUM = "premium"
    ULTRA_PREMIUM = "ultra_premium"


@dataclass
class TTSProvider:
    """TTS provider configuration"""
    name: str
    tier: TTSProviderTier
    cost_per_char: float  # Cost per character in USD
    quality_score: int  # 1-10 scale
    supported_languages: int
    api_endpoint: str
    supported_features: List[str]
    max_chars_per_request: int = 5000
    rate_limit_per_minute: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_cost(self, text_length: int) -> float:
        """Calculate synthesis cost for given text length"""
        return text_length * self.cost_per_char
    
    def supports_feature(self, feature: str) -> bool:
        """Check if provider supports a feature"""
        return feature in self.supported_features


@dataclass
class VoicePreferences:
    """User voice preferences"""
    language: str = "en-US"
    gender: str = "neutral"  # male, female, neutral
    age: str = "adult"  # child, young_adult, adult, senior
    style: str = "conversational"  # conversational, formal, energetic, calm
    speed: float = 1.0  # 0.5 - 2.0
    pitch: float = 1.0  # 0.5 - 2.0
    emotion: Optional[str] = None  # happy, sad, excited, calm, etc.
    custom_voice_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityMetrics:
    """Audio quality metrics"""
    snr: float  # Signal-to-Noise Ratio (dB)
    thd: float  # Total Harmonic Distortion (%)
    dynamic_range: float  # dB
    peak_level: float  # dBFS
    loudness_lufs: float  # LUFS (Loudness Units relative to Full Scale)
    frequency_response: Dict[str, float] = field(default_factory=dict)
    mos_score: Optional[float] = None  # Mean Opinion Score (1-5)
    clarity_score: float = 0.0  # 0-1 scale
    naturalness_score: float = 0.0  # 0-1 scale
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioResult:
    """Result from TTS synthesis"""
    audio_data: bytes
    format: AudioFormat
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int
    file_size_bytes: int
    provider_used: str
    synthesis_cost: float
    quality_metrics: Optional[QualityMetrics] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProcessedAudio:
    """Processed and optimized audio"""
    audio_data: bytes
    format: AudioFormat
    duration_seconds: float
    sample_rate: int
    bitrate: str
    file_size_bytes: int
    quality_metrics: QualityMetrics
    processing_time_seconds: float
    optimizations_applied: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CompressionSettings:
    """Audio compression settings"""
    bitrate: str  # e.g., "192kbps"
    sample_rate: str  # e.g., "44.1kHz"
    quality: int  # 0-9 (0=best, 9=worst for MP3)
    format: AudioFormat = AudioFormat.MP3
    vbr: bool = False  # Variable Bit Rate
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingConfig:
    """Streaming configuration"""
    url: str
    protocol: str  # HLS, DASH, etc.
    segment_duration: int  # seconds
    quality_variants: List[Dict[str, Any]]
    adaptive_streaming: bool
    buffer_size: int  # seconds
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioDelivery:
    """Audio delivery information"""
    download_url: str
    streaming_url: Optional[str] = None
    cdn_url: Optional[str] = None
    playback_options: Dict[str, Any] = field(default_factory=dict)
    quality_variants: List[Dict[str, Any]] = field(default_factory=list)
    expiry_time: Optional[datetime] = None
    cache_headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if delivery URL has expired"""
        if self.expiry_time is None:
            return False
        return datetime.utcnow() > self.expiry_time


@dataclass
class TTSRequest:
    """Request for TTS synthesis"""
    text: str
    voice_preferences: VoicePreferences
    user_tier: UserTier
    target_quality: str  # ultra_premium, premium, standard, basic
    output_format: AudioFormat = AudioFormat.MP3
    ssml_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioProcessingOptions:
    """Options for audio processing"""
    normalize: bool = True
    target_loudness: float = -23.0  # LUFS
    noise_reduction: bool = True
    clarity_boost: bool = True
    dynamic_range_optimization: bool = True
    compression_settings: Optional[CompressionSettings] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostTracking:
    """Cost tracking for audio synthesis"""
    tts_cost: float
    storage_cost: float
    bandwidth_cost: float
    processing_cost: float
    total_cost: float
    provider: str
    user_tier: UserTier
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioCache:
    """Audio cache entry"""
    cache_key: str
    audio_data: bytes
    format: AudioFormat
    duration_seconds: float
    file_size_bytes: int
    hit_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def increment_hit(self):
        """Increment cache hit counter"""
        self.hit_count += 1
        self.last_accessed = datetime.utcnow()


@dataclass
class QualityAssessment:
    """Quality assessment result"""
    overall_score: float  # 0-10 scale
    objective_metrics: QualityMetrics
    subjective_score: Optional[float] = None  # MOS score
    passed: bool = True
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeliveryMetrics:
    """Metrics for audio delivery"""
    download_time_ms: float
    first_byte_time_ms: float
    cdn_hit: bool
    geographic_region: str
    user_agent: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SynthesisJob:
    """TTS synthesis job"""
    job_id: str
    status: str  # pending, processing, completed, failed
    request: TTSRequest
    result: Optional[AudioResult] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Quality tier configurations
QUALITY_TIERS = {
    'ultra_premium': {
        'bitrate': '320kbps',
        'sample_rate': '48kHz',
        'quality': 0,
        'format': AudioFormat.MP3,
        'tts_tier': TTSProviderTier.ULTRA_PREMIUM,
        'features': ['neural_voices', 'emotion_control', 'custom_voices']
    },
    'premium': {
        'bitrate': '192kbps',
        'sample_rate': '44.1kHz',
        'quality': 2,
        'format': AudioFormat.MP3,
        'tts_tier': TTSProviderTier.PREMIUM,
        'features': ['neural_voices', 'ssml']
    },
    'standard': {
        'bitrate': '128kbps',
        'sample_rate': '44.1kHz',
        'quality': 4,
        'format': AudioFormat.MP3,
        'tts_tier': TTSProviderTier.PREMIUM,
        'features': ['ssml']
    },
    'basic': {
        'bitrate': '96kbps',
        'sample_rate': '22kHz',
        'quality': 6,
        'format': AudioFormat.MP3,
        'tts_tier': TTSProviderTier.FREE,
        'features': ['basic_synthesis']
    }
}


# User tier to quality tier mapping
USER_TIER_QUALITY_MAP = {
    UserTier.FREE: 'basic',
    UserTier.PREMIUM: 'premium',
    UserTier.ULTRA_PREMIUM: 'ultra_premium'
}
