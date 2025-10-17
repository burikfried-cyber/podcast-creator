"""
Audio Quality Assurance
Comprehensive quality validation and testing
"""
import asyncio
from typing import Dict, List, Optional, Any
import structlog

from .models import (
    ProcessedAudio,
    QualityMetrics,
    QualityAssessment,
    AudioFormat
)

logger = structlog.get_logger()


class AudioQualityAssurance:
    """
    Comprehensive audio quality assurance system
    Validates objective and subjective quality metrics
    """
    
    def __init__(self):
        # Quality thresholds
        self.thresholds = {
            'snr_min': 40.0,  # Minimum SNR in dB
            'thd_max': 1.0,  # Maximum THD in %
            'dynamic_range_min': 60.0,  # Minimum dynamic range in dB
            'peak_level_max': -1.0,  # Maximum peak level in dBFS
            'loudness_target': -23.0,  # Target loudness in LUFS
            'loudness_tolerance': 2.0,  # Tolerance in LUFS
            'clarity_min': 0.6,  # Minimum clarity score
            'naturalness_min': 0.6  # Minimum naturalness score
        }
        
        # Assessment history
        self.assessment_history = []
    
    async def assess_audio_quality(
        self,
        processed_audio: ProcessedAudio,
        run_subjective: bool = False
    ) -> QualityAssessment:
        """
        Comprehensive quality assessment
        
        Args:
            processed_audio: Processed audio to assess
            run_subjective: Run subjective quality tests (MOS)
            
        Returns:
            QualityAssessment with results and recommendations
        """
        logger.info("quality_assessment_started",
                   duration=processed_audio.duration_seconds,
                   format=processed_audio.format.value)
        
        try:
            issues = []
            warnings = []
            recommendations = []
            
            metrics = processed_audio.quality_metrics
            
            # Objective quality checks
            objective_passed = await self._check_objective_metrics(
                metrics, issues, warnings, recommendations
            )
            
            # Subjective quality (if enabled)
            subjective_score = None
            if run_subjective:
                subjective_score = await self._assess_subjective_quality(
                    processed_audio
                )
                if subjective_score < 3.5:  # MOS scale 1-5
                    warnings.append(f"Subjective quality score low: {subjective_score:.2f}/5.0")
            
            # Cross-platform compatibility check
            compatibility_passed = await self._check_compatibility(
                processed_audio, issues, warnings
            )
            
            # Streaming quality check
            streaming_passed = await self._check_streaming_quality(
                processed_audio, warnings
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                metrics,
                subjective_score,
                len(issues),
                len(warnings)
            )
            
            # Determine pass/fail
            passed = (
                objective_passed and
                compatibility_passed and
                len(issues) == 0 and
                overall_score >= 7.0
            )
            
            assessment = QualityAssessment(
                overall_score=overall_score,
                objective_metrics=metrics,
                subjective_score=subjective_score,
                passed=passed,
                issues=issues,
                warnings=warnings,
                recommendations=recommendations
            )
            
            # Track assessment
            self.assessment_history.append(assessment)
            
            logger.info("quality_assessment_complete",
                       overall_score=overall_score,
                       passed=passed,
                       issues=len(issues),
                       warnings=len(warnings))
            
            return assessment
            
        except Exception as e:
            logger.error("quality_assessment_failed", error=str(e))
            raise
    
    async def _check_objective_metrics(
        self,
        metrics: QualityMetrics,
        issues: List[str],
        warnings: List[str],
        recommendations: List[str]
    ) -> bool:
        """Check objective quality metrics"""
        passed = True
        
        # SNR check
        if metrics.snr < self.thresholds['snr_min']:
            issues.append(f"SNR too low: {metrics.snr:.1f}dB (min: {self.thresholds['snr_min']}dB)")
            recommendations.append("Apply noise reduction or use higher quality TTS")
            passed = False
        
        # THD check
        if metrics.thd > self.thresholds['thd_max']:
            issues.append(f"THD too high: {metrics.thd:.2f}% (max: {self.thresholds['thd_max']}%)")
            recommendations.append("Check audio processing chain for distortion")
            passed = False
        
        # Dynamic range check
        if metrics.dynamic_range < self.thresholds['dynamic_range_min']:
            warnings.append(f"Dynamic range low: {metrics.dynamic_range:.1f}dB")
            recommendations.append("Consider reducing compression")
        
        # Peak level check
        if metrics.peak_level > self.thresholds['peak_level_max']:
            warnings.append(f"Peak level high: {metrics.peak_level:.1f}dBFS")
            recommendations.append("Apply limiting to prevent clipping")
        
        # Loudness check
        loudness_diff = abs(metrics.loudness_lufs - self.thresholds['loudness_target'])
        if loudness_diff > self.thresholds['loudness_tolerance']:
            warnings.append(f"Loudness off target: {metrics.loudness_lufs:.1f} LUFS (target: {self.thresholds['loudness_target']} LUFS)")
            recommendations.append("Adjust normalization target")
        
        # Clarity check
        if metrics.clarity_score < self.thresholds['clarity_min']:
            warnings.append(f"Clarity score low: {metrics.clarity_score:.2f}")
            recommendations.append("Apply clarity enhancement or use higher bitrate")
        
        # Naturalness check
        if metrics.naturalness_score < self.thresholds['naturalness_min']:
            warnings.append(f"Naturalness score low: {metrics.naturalness_score:.2f}")
            recommendations.append("Consider using premium TTS provider")
        
        return passed
    
    async def _assess_subjective_quality(
        self,
        processed_audio: ProcessedAudio
    ) -> float:
        """
        Assess subjective quality (MOS - Mean Opinion Score)
        
        In production, this would:
        1. Use trained ML models to predict MOS
        2. Collect user ratings
        3. Run listening tests
        
        Returns MOS score (1-5 scale)
        """
        # Mock implementation based on objective metrics
        metrics = processed_audio.quality_metrics
        
        # Estimate MOS from objective metrics
        # Higher clarity and naturalness = higher MOS
        estimated_mos = (
            (metrics.clarity_score * 2.5) +
            (metrics.naturalness_score * 2.5)
        )
        
        # Clamp to 1-5 range
        return max(1.0, min(5.0, estimated_mos))
    
    async def _check_compatibility(
        self,
        processed_audio: ProcessedAudio,
        issues: List[str],
        warnings: List[str]
    ) -> bool:
        """Check cross-platform compatibility"""
        passed = True
        
        # Format compatibility
        compatible_formats = [AudioFormat.MP3, AudioFormat.AAC, AudioFormat.OGG]
        if processed_audio.format not in compatible_formats:
            warnings.append(f"Format {processed_audio.format.value} may have limited compatibility")
        
        # Bitrate check
        bitrate_value = int(processed_audio.bitrate.replace('kbps', ''))
        if bitrate_value < 64:
            warnings.append("Very low bitrate may cause playback issues on some devices")
        
        # Sample rate check
        if processed_audio.sample_rate < 22050:
            warnings.append("Low sample rate may affect quality on high-end devices")
        
        # File size check
        max_size = 100 * 1024 * 1024  # 100MB
        if processed_audio.file_size_bytes > max_size:
            warnings.append(f"Large file size ({processed_audio.file_size_bytes / 1024 / 1024:.1f}MB) may cause loading issues")
        
        return passed
    
    async def _check_streaming_quality(
        self,
        processed_audio: ProcessedAudio,
        warnings: List[str]
    ) -> bool:
        """Check streaming quality"""
        # Duration check
        if processed_audio.duration_seconds > 3600:  # 1 hour
            warnings.append("Long duration may require segmentation for optimal streaming")
        
        # Bitrate consistency check (for VBR)
        # In production would analyze bitrate variance
        
        return True
    
    def _calculate_overall_score(
        self,
        metrics: QualityMetrics,
        subjective_score: Optional[float],
        num_issues: int,
        num_warnings: int
    ) -> float:
        """
        Calculate overall quality score (0-10 scale)
        
        Weighted combination of:
        - Objective metrics (50%)
        - Subjective score (30%)
        - Issue penalties (20%)
        """
        # Objective score (0-10)
        objective_score = (
            (metrics.clarity_score * 5) +
            (metrics.naturalness_score * 5)
        )
        
        # Subjective score (0-10, converted from 1-5 MOS)
        if subjective_score:
            subjective_component = ((subjective_score - 1) / 4) * 10
        else:
            subjective_component = objective_score  # Use objective as fallback
        
        # Issue penalty
        issue_penalty = (num_issues * 2.0) + (num_warnings * 0.5)
        
        # Weighted score
        score = (
            (objective_score * 0.5) +
            (subjective_component * 0.3) +
            (10 * 0.2)  # Base score for issue component
        ) - issue_penalty
        
        return max(0.0, min(10.0, score))
    
    def get_assessment_stats(self) -> Dict[str, Any]:
        """Get quality assessment statistics"""
        if not self.assessment_history:
            return {
                'total_assessments': 0,
                'average_score': 0.0,
                'pass_rate': 0.0
            }
        
        total = len(self.assessment_history)
        passed = sum(1 for a in self.assessment_history if a.passed)
        
        return {
            'total_assessments': total,
            'average_score': sum(a.overall_score for a in self.assessment_history) / total,
            'pass_rate': (passed / total) * 100,
            'average_issues': sum(len(a.issues) for a in self.assessment_history) / total,
            'average_warnings': sum(len(a.warnings) for a in self.assessment_history) / total
        }


# Convenience function
async def assess_quality(
    processed_audio: ProcessedAudio,
    run_subjective: bool = False
) -> QualityAssessment:
    """
    Convenience function to assess audio quality
    
    Args:
        processed_audio: Processed audio to assess
        run_subjective: Run subjective quality tests
        
    Returns:
        QualityAssessment with results
    """
    qa = AudioQualityAssurance()
    return await qa.assess_audio_quality(processed_audio, run_subjective)
