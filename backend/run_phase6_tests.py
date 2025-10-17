"""
Phase 6 Test Runner
Runs comprehensive tests and writes results to file
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.audio.tts_system import MultiTierTTSSystem
from app.services.audio.audio_processor import AudioProcessingPipeline
from app.services.audio.delivery_system import AudioDeliverySystem
from app.services.audio.quality_assurance import AudioQualityAssurance
from app.services.audio.models import UserTier, VoicePreferences, AudioProcessingOptions


async def run_all_tests():
    """Run all Phase 6 tests and collect results"""
    
    results = {
        'test_run_time': datetime.utcnow().isoformat(),
        'tests': [],
        'summary': {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    }
    
    sample_text = "Welcome to this amazing podcast about the Westman Islands. Today we'll explore the unique phenomenon of puffins living in human houses. This fascinating story has captivated researchers for decades."
    
    # Initialize systems
    tts_system = MultiTierTTSSystem()
    audio_processor = AudioProcessingPipeline()
    delivery_system = AudioDeliverySystem()
    quality_assurance = AudioQualityAssurance()
    
    # Test 1: TTS Synthesis - Free Tier
    print("Test 1: TTS Synthesis - Free Tier...")
    try:
        result = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        passed = (
            result is not None and
            result.provider_used in ['eSpeak', 'Festival'] and
            result.synthesis_cost == 0.0 and
            result.duration_seconds > 0
        )
        
        test_result = {
            'name': 'TTS Synthesis - Free Tier',
            'passed': passed,
            'details': {
                'provider': result.provider_used,
                'cost': result.synthesis_cost,
                'duration': result.duration_seconds,
                'file_size': result.file_size_bytes
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'TTS Synthesis - Free Tier',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 1: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 2: TTS Synthesis - Premium Tier
    print("Test 2: TTS Synthesis - Premium Tier...")
    try:
        result = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        passed = (
            result is not None and
            result.provider_used in ['Azure Neural TTS', 'AWS Polly', 'Google Cloud TTS'] and
            result.synthesis_cost > 0
        )
        
        test_result = {
            'name': 'TTS Synthesis - Premium Tier',
            'passed': passed,
            'details': {
                'provider': result.provider_used,
                'cost': result.synthesis_cost,
                'duration': result.duration_seconds
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'TTS Synthesis - Premium Tier',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 2: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 3: Provider Selection
    print("Test 3: Provider Selection...")
    try:
        provider = await tts_system.select_optimal_tts(
            user_tier=UserTier.PREMIUM,
            text_length=1000,
            voice_preferences=VoicePreferences(),
            target_quality='premium'
        )
        
        passed = provider is not None and provider.quality_score >= 8
        
        test_result = {
            'name': 'Provider Selection',
            'passed': passed,
            'details': {
                'provider': provider.name,
                'quality_score': provider.quality_score,
                'cost_per_char': provider.cost_per_char
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Provider Selection',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 3: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 4: Audio Processing
    print("Test 4: Audio Processing...")
    try:
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        passed = (
            processed is not None and
            processed.format.value == 'mp3' and
            processed.bitrate == '128kbps' and
            len(processed.optimizations_applied) > 0
        )
        
        test_result = {
            'name': 'Audio Processing',
            'passed': passed,
            'details': {
                'format': processed.format.value,
                'bitrate': processed.bitrate,
                'file_size': processed.file_size_bytes,
                'processing_time': processed.processing_time_seconds,
                'optimizations': processed.optimizations_applied,
                'quality_score': processed.quality_metrics.clarity_score
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Audio Processing',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 4: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 5: Multiple Quality Tiers
    print("Test 5: Multiple Quality Tiers...")
    try:
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        quality_results = {}
        for quality in ['basic', 'standard', 'premium', 'ultra_premium']:
            processed = await audio_processor.post_process_audio(
                raw_audio=raw_audio,
                target_quality=quality
            )
            quality_results[quality] = {
                'bitrate': processed.bitrate,
                'file_size': processed.file_size_bytes,
                'quality_score': processed.quality_metrics.clarity_score
            }
        
        passed = len(quality_results) == 4
        
        test_result = {
            'name': 'Multiple Quality Tiers',
            'passed': passed,
            'details': quality_results
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Multiple Quality Tiers',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 5: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 6: Audio Delivery
    print("Test 6: Audio Delivery...")
    try:
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.FREE
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='standard'
        )
        
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_content'
        )
        
        passed = (
            delivery is not None and
            delivery.download_url is not None and
            delivery.cdn_url is not None and
            not delivery.is_expired()
        )
        
        test_result = {
            'name': 'Audio Delivery',
            'passed': passed,
            'details': {
                'has_download_url': delivery.download_url is not None,
                'has_cdn_url': delivery.cdn_url is not None,
                'has_streaming': delivery.streaming_url is not None,
                'is_expired': delivery.is_expired(),
                'quality_variants': len(delivery.quality_variants)
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Audio Delivery',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 6: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 7: Streaming Setup
    print("Test 7: Streaming Setup...")
    try:
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='premium'
        )
        
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_streaming',
            enable_streaming=True
        )
        
        passed = (
            delivery.streaming_url is not None and
            len(delivery.quality_variants) > 0
        )
        
        test_result = {
            'name': 'Streaming Setup',
            'passed': passed,
            'details': {
                'streaming_url': delivery.streaming_url,
                'num_variants': len(delivery.quality_variants),
                'variants': delivery.quality_variants
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Streaming Setup',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 7: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 8: Quality Assessment
    print("Test 8: Quality Assessment...")
    try:
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='premium'
        )
        
        assessment = await quality_assurance.assess_audio_quality(
            processed_audio=processed
        )
        
        passed = (
            assessment is not None and
            0 <= assessment.overall_score <= 10 and
            assessment.objective_metrics is not None
        )
        
        test_result = {
            'name': 'Quality Assessment',
            'passed': passed,
            'details': {
                'overall_score': assessment.overall_score,
                'passed_qa': assessment.passed,
                'num_issues': len(assessment.issues),
                'num_warnings': len(assessment.warnings),
                'snr': assessment.objective_metrics.snr,
                'clarity': assessment.objective_metrics.clarity_score,
                'naturalness': assessment.objective_metrics.naturalness_score
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Quality Assessment',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 8: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 9: Complete End-to-End Pipeline
    print("Test 9: Complete End-to-End Pipeline...")
    try:
        start_time = time.time()
        
        # Synthesize
        raw_audio = await tts_system.synthesize_podcast(
            script_text=sample_text,
            user_tier=UserTier.PREMIUM
        )
        
        # Process
        processed = await audio_processor.post_process_audio(
            raw_audio=raw_audio,
            target_quality='premium'
        )
        
        # Quality check
        assessment = await quality_assurance.assess_audio_quality(
            processed_audio=processed
        )
        
        # Deliver
        delivery = await delivery_system.deliver_audio(
            processed_audio=processed,
            user_id='test_user',
            content_id='test_e2e'
        )
        
        total_time = time.time() - start_time
        
        passed = (
            raw_audio is not None and
            processed is not None and
            assessment is not None and
            delivery is not None and
            total_time < 30.0  # Should complete in reasonable time
        )
        
        test_result = {
            'name': 'Complete End-to-End Pipeline',
            'passed': passed,
            'details': {
                'total_time_seconds': total_time,
                'synthesis_cost': raw_audio.synthesis_cost,
                'processing_time': processed.processing_time_seconds,
                'quality_score': assessment.overall_score,
                'delivery_url': delivery.download_url is not None
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Complete End-to-End Pipeline',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 9: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 10: Cost Tracking
    print("Test 10: Cost Tracking...")
    try:
        # Generate a few syntheses with different text to avoid cache
        for i in range(3):
            await tts_system.synthesize_podcast(
                script_text=f"{sample_text} Variation {i}",
                user_tier=UserTier.PREMIUM
            )
        
        stats = tts_system.get_cost_summary()
        
        passed = (
            stats['total_syntheses'] >= 3 and
            stats['total_cost'] >= 0 and
            'by_provider' in stats
        )
        
        test_result = {
            'name': 'Cost Tracking',
            'passed': passed,
            'details': stats
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Cost Tracking',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 10: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    return results


async def main():
    """Main test runner"""
    print("=" * 80)
    print("PHASE 6 COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    try:
        results = await run_all_tests()
        
        # Write results to file
        output_file = Path("phase6_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print()
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {results['summary']['total']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Success Rate: {(results['summary']['passed'] / results['summary']['total'] * 100):.1f}%")
        print()
        
        if results['summary']['errors']:
            print("ERRORS:")
            for error in results['summary']['errors']:
                print(f"  - {error}")
            print()
        
        print(f"Results saved to: {output_file}")
        print("=" * 80)
        
        # Return exit code
        return 0 if results['summary']['failed'] == 0 else 1
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
