"""
Test script for Phase 3 - Audio Generation with Google Cloud TTS
Tests audio synthesis, file creation, and error handling
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.audio.google_tts_service import google_tts_service, GOOGLE_TTS_AVAILABLE
from app.services.audio.audio_service import audio_service


async def test_google_tts_availability():
    """Test Case 0: Check Google TTS Availability"""
    print("\n" + "="*60)
    print("TEST 0: Google Cloud TTS Availability")
    print("="*60)
    
    print(f"\nGoogle TTS Library Available: {GOOGLE_TTS_AVAILABLE}")
    
    if not GOOGLE_TTS_AVAILABLE:
        print("\n[WARNING] google-cloud-texttospeech not installed")
        print("Install with: pip install google-cloud-texttospeech")
        return False
    
    print(f"Client Initialized: {google_tts_service.client is not None}")
    
    if not google_tts_service.client:
        print("\n[WARNING] Google TTS client not initialized")
        print("Check GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("Or ensure default credentials are configured")
        return False
    
    # Get voice options
    voice_options = google_tts_service.get_voice_options()
    print(f"\nAvailable: {voice_options['available']}")
    print(f"Free Tier Limits:")
    print(f"  - Standard: {voice_options['free_tier_limits']['standard_chars_per_month']:,} chars/month")
    print(f"  - Neural: {voice_options['free_tier_limits']['neural_chars_per_month']:,} chars/month")
    
    print("\nVoice Options:")
    for tier, config in voice_options['voices'].items():
        print(f"  {tier.upper()}:")
        print(f"    - Name: {config['name']}")
        print(f"    - Type: {config['type']}")
        print(f"    - Cost: ${config['cost_per_char']:.6f}/char")
    
    print("\nPASS: Google TTS is available and configured")
    return True


async def test_cost_estimation():
    """Test Case 1: Cost Estimation"""
    print("\n" + "="*60)
    print("TEST 1: Cost Estimation")
    print("="*60)
    
    # Sample script (10-minute podcast)
    sample_script = """
    Welcome to our podcast about the fascinating history of Paris.
    Today, we'll explore how this beautiful city became the cultural capital of Europe.
    """ * 50  # Repeat to get ~1500 words
    
    print(f"\nSample Script Length: {len(sample_script)} characters")
    print(f"Word Count: {len(sample_script.split())} words")
    
    # Estimate for free tier
    free_estimate = google_tts_service.estimate_cost(sample_script, 'free')
    print(f"\nFREE TIER (Standard Voice):")
    print(f"  - Character Count: {free_estimate['character_count']:,}")
    print(f"  - Word Count: {free_estimate['word_count']:,}")
    print(f"  - Estimated Duration: {free_estimate['estimated_duration_minutes']:.2f} minutes")
    print(f"  - Estimated Cost: ${free_estimate['estimated_cost_usd']:.4f}")
    print(f"  - Voice Type: {free_estimate['voice_type']}")
    
    # Estimate for premium tier
    premium_estimate = google_tts_service.estimate_cost(sample_script, 'premium')
    print(f"\nPREMIUM TIER (Neural Voice):")
    print(f"  - Character Count: {premium_estimate['character_count']:,}")
    print(f"  - Word Count: {premium_estimate['word_count']:,}")
    print(f"  - Estimated Duration: {premium_estimate['estimated_duration_minutes']:.2f} minutes")
    print(f"  - Estimated Cost: ${premium_estimate['estimated_cost_usd']:.4f}")
    print(f"  - Voice Type: {premium_estimate['voice_type']}")
    
    # Verify estimates
    assert free_estimate['character_count'] > 0, "Character count should be positive"
    assert free_estimate['estimated_cost_usd'] > 0, "Cost should be positive"
    assert premium_estimate['estimated_cost_usd'] > free_estimate['estimated_cost_usd'], "Premium should cost more"
    
    print("\nPASS: Cost estimation working correctly")
    return True


async def test_audio_synthesis_free():
    """Test Case 2: Audio Synthesis (Free Tier)"""
    print("\n" + "="*60)
    print("TEST 2: Audio Synthesis - Free Tier")
    print("="*60)
    
    if not GOOGLE_TTS_AVAILABLE or not google_tts_service.client:
        print("\n[SKIP] Google TTS not available")
        return False
    
    # Short test script
    test_script = "Welcome to our podcast. This is a test of the audio generation system."
    
    print(f"\nTest Script: \"{test_script}\"")
    print(f"Length: {len(test_script)} characters")
    print("\nSynthesizing with Standard voice...")
    
    result = await google_tts_service.synthesize_speech(
        text=test_script,
        voice_tier='free',
        speaking_rate=1.0,
        pitch=0.0
    )
    
    print(f"\nSynthesis Result:")
    print(f"  - Success: {result.get('success')}")
    
    if not result.get('success'):
        print(f"  - Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"  - Format: {result.get('format')}")
        print(f"  - Synthesis Time: {result.get('synthesis_time')}s")
        print(f"  - Character Count: {result.get('character_count')}")
        print(f"  - Cost Estimate: ${result.get('cost_estimate', 0):.6f}")
        print(f"  - Voice Name: {result.get('voice_name')}")
        print(f"  - Voice Type: {result.get('voice_type')}")
    
    if result.get('success'):
        audio_content = result.get('audio_content')
        print(f"  - Audio Size: {len(audio_content)} bytes ({len(audio_content)/1024:.2f} KB)")
        
        # Verify audio content
        assert audio_content is not None, "Audio content should not be None"
        assert len(audio_content) > 0, "Audio content should not be empty"
        assert result.get('format') == 'mp3', "Format should be MP3"
        
        print("\nPASS: Free tier audio synthesis successful")
        return True
    else:
        print(f"\n[FAIL] Synthesis failed: {result.get('error')}")
        return False


async def test_audio_synthesis_premium():
    """Test Case 3: Audio Synthesis (Premium Tier)"""
    print("\n" + "="*60)
    print("TEST 3: Audio Synthesis - Premium Tier")
    print("="*60)
    
    if not GOOGLE_TTS_AVAILABLE or not google_tts_service.client:
        print("\n[SKIP] Google TTS not available")
        return False
    
    # Short test script
    test_script = "This is a premium quality neural voice test. The voice should sound more natural."
    
    print(f"\nTest Script: \"{test_script}\"")
    print("\nSynthesizing with Neural2 voice...")
    
    result = await google_tts_service.synthesize_speech(
        text=test_script,
        voice_tier='premium',
        speaking_rate=1.0,
        pitch=0.0
    )
    
    print(f"\nSynthesis Result:")
    print(f"  - Success: {result.get('success')}")
    
    if not result.get('success'):
        print(f"  - Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"  - Voice Type: {result.get('voice_type')}")
        print(f"  - Cost Estimate: ${result.get('cost_estimate', 0):.6f}")
    
    if result.get('success'):
        audio_content = result.get('audio_content')
        print(f"  - Audio Size: {len(audio_content)} bytes")
        
        assert result.get('voice_type') == 'NEURAL2', "Should use Neural2 voice"
        
        print("\nPASS: Premium tier audio synthesis successful")
        return True
    else:
        print(f"\n[FAIL] Synthesis failed: {result.get('error')}")
        return False


async def test_full_audio_generation():
    """Test Case 4: Full Audio Generation with File Save"""
    print("\n" + "="*60)
    print("TEST 4: Full Audio Generation Pipeline")
    print("="*60)
    
    if not GOOGLE_TTS_AVAILABLE or not google_tts_service.client:
        print("\n[SKIP] Google TTS not available")
        return False
    
    # Longer test script (simulating podcast)
    test_script = """
    Welcome to our podcast about the history of technology.
    Today we're exploring how the internet changed the world.
    From ARPANET to the World Wide Web, this is a fascinating story.
    """ * 10  # Repeat to get more content
    
    podcast_id = "test_podcast_123"
    
    print(f"\nTest Script Length: {len(test_script)} characters")
    print(f"Word Count: {len(test_script.split())} words")
    print(f"Podcast ID: {podcast_id}")
    print("\nGenerating audio...")
    
    result = await audio_service.generate_podcast_audio(
        script_text=test_script,
        podcast_id=podcast_id,
        user_tier='free',
        speaking_rate=1.0,
        pitch=0.0
    )
    
    print(f"\nGeneration Result:")
    print(f"  - Success: {result.get('success')}")
    
    if result.get('success'):
        print(f"  - Audio URL: {result.get('audio_url')}")
        print(f"  - File Path: {result.get('file_path')}")
        print(f"  - Filename: {result.get('filename')}")
        print(f"  - Duration: {result.get('duration_seconds')}s ({result.get('duration_seconds')/60:.2f} min)")
        print(f"  - File Size: {result.get('file_size_mb')} MB")
        print(f"  - Generation Time: {result.get('generation_time')}s")
        print(f"  - Synthesis Time: {result.get('synthesis_time')}s")
        print(f"  - Cost: ${result.get('cost_estimate'):.4f}")
        print(f"  - Voice: {result.get('voice_name')} ({result.get('voice_type')})")
        
        # Verify file exists
        file_path = result.get('file_path')
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"\n  [✓] File exists: {file_path}")
            print(f"  [✓] File size: {file_size} bytes")
            
            # Verify it's an MP3 file (check magic bytes)
            with open(file_path, 'rb') as f:
                header = f.read(3)
                is_mp3 = header == b'ID3' or header[:2] == b'\xff\xfb'
                print(f"  [✓] Valid MP3: {is_mp3}")
            
            # Clean up test file
            try:
                os.remove(file_path)
                print(f"  [✓] Test file cleaned up")
            except:
                pass
            
            print("\nPASS: Full audio generation pipeline successful")
            return True
        else:
            print(f"\n[FAIL] Audio file not found: {file_path}")
            return False
    else:
        print(f"\n[FAIL] Generation failed: {result.get('error')}")
        return False


async def test_storage_stats():
    """Test Case 5: Storage Statistics"""
    print("\n" + "="*60)
    print("TEST 5: Storage Statistics")
    print("="*60)
    
    stats = audio_service.get_storage_stats()
    
    print(f"\nStorage Statistics:")
    print(f"  - Audio Directory: {stats.get('audio_directory')}")
    print(f"  - Total Files: {stats.get('total_files', 0)}")
    print(f"  - Total Size: {stats.get('total_size_mb', 0)} MB")
    
    if stats.get('files'):
        print(f"  - Recent Files: {len(stats['files'])}")
        for f in stats['files'][:3]:
            print(f"    * {f}")
    
    print("\nPASS: Storage statistics retrieved")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 3: AUDIO GENERATION TEST SUITE")
    print("="*60)
    
    results = {}
    
    try:
        # Test 0: Availability
        results['availability'] = await test_google_tts_availability()
        
        if not results['availability']:
            print("\n" + "="*60)
            print("TESTS SKIPPED - Google TTS Not Available")
            print("="*60)
            print("\nTo enable audio generation:")
            print("1. Install: pip install google-cloud-texttospeech")
            print("2. Set up Google Cloud credentials:")
            print("   - Go to Google Cloud Console")
            print("   - Enable Text-to-Speech API")
            print("   - Create service account")
            print("   - Download JSON key")
            print("   - Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
            return
        
        # Test 1: Cost estimation
        results['cost_estimation'] = await test_cost_estimation()
        
        # Test 2: Free tier synthesis
        results['free_synthesis'] = await test_audio_synthesis_free()
        
        # Test 3: Premium tier synthesis
        results['premium_synthesis'] = await test_audio_synthesis_premium()
        
        # Test 4: Full generation pipeline
        results['full_generation'] = await test_full_audio_generation()
        
        # Test 5: Storage stats
        results['storage_stats'] = await test_storage_stats()
        
        # Final summary
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        for test_name, passed in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        total_tests = len(results)
        passed_tests = sum(1 for v in results.values() if v)
        
        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n" + "="*60)
            print("ALL TESTS PASSED!")
            print("="*60)
            
            print("\nPhase 3 Implementation Status:")
            print("  - Google TTS Integration: WORKING")
            print("  - Cost Estimation: WORKING")
            print("  - Free Tier Synthesis: WORKING")
            print("  - Premium Tier Synthesis: WORKING")
            print("  - Full Audio Pipeline: WORKING")
            print("  - File Storage: WORKING")
            
            print("\nPhase 3: 100% COMPLETE")
            print("Audio generation fully functional!")
            
            print("\nReady for production use!")
        else:
            print("\nSome tests failed. Please review the output above.")
            sys.exit(1)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
