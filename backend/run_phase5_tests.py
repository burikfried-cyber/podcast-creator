"""
Phase 5 Test Runner
Runs comprehensive tests and writes results to file
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.narrative.podcast_generator import PodcastGenerator
from app.services.narrative.models import PodcastType, UserProfile
from app.services.narrative.tts_optimizer import TTSOptimizer


async def run_all_tests():
    """Run all Phase 5 tests and collect results"""
    
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
    
    # Sample content for testing
    sample_content = {
        'id': 'test_001',
        'title': 'The Westman Islands Puffin Colony Living in Human Houses',
        'content': '''A unique phenomenon where puffins cohabitate with humans in the Westman Islands. 
        This interspecies living arrangement confounds scientists and is found nowhere else in the world.
        The tradition dates back centuries and has been preserved by the local community.
        Researchers are baffled by how this unusual relationship developed.''',
        'location': {'lat': 63.4, 'lng': -20.3, 'name': 'Westman Islands'},
        'standout_score': 8.5,
        'tier': 'exceptional',
        'method_scores': {
            'cultural': 6.0,
            'historical': 5.0,
            'uniqueness': 8.0,
            'atlas_obscura': 7.0
        }
    }
    
    user_preferences = UserProfile(
        user_id='test_user',
        surprise_tolerance=3,
        preferred_length='medium',
        preferred_style='balanced',
        preferred_pace='moderate',
        interests=['nature', 'culture']
    )
    
    generator = PodcastGenerator()
    
    # Test 1: Generate Base Podcast
    print("Test 1: Generate Base Podcast...")
    try:
        result = await generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        test_result = {
            'name': 'Generate Base Podcast',
            'passed': result['success'],
            'details': {
                'success': result['success'],
                'has_script': 'script' in result,
                'has_narrative': 'narrative' in result,
                'has_quality_report': 'quality_report' in result,
                'script_length': len(result['script'].content) if result.get('script') else 0,
                'num_sections': len(result['script'].sections) if result.get('script') else 0,
                'duration_seconds': result['script'].estimated_duration_seconds if result.get('script') else 0,
                'quality_score': result['script'].quality_score if result.get('script') else 0,
                'engagement_score': result['narrative'].engagement_score if result.get('narrative') else 0
            }
        }
        
        if result['success']:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Generate Base Podcast',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 1: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 2: Generate Standout Podcast
    print("Test 2: Generate Standout Podcast...")
    try:
        result = await generator.generate_standout_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        test_result = {
            'name': 'Generate Standout Podcast',
            'passed': result['success'],
            'details': {
                'success': result['success'],
                'podcast_type': result['script'].podcast_type.value if result.get('script') else None,
                'has_mystery_elements': 'remarkable' in result['script'].content.lower() or 'unique' in result['script'].content.lower() if result.get('script') else False
            }
        }
        
        if result['success']:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Generate Standout Podcast',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 2: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 3: Quality Control
    print("Test 3: Quality Control...")
    try:
        result = await generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        quality_report = result.get('quality_report')
        
        test_result = {
            'name': 'Quality Control',
            'passed': quality_report is not None,
            'details': {
                'has_quality_report': quality_report is not None,
                'overall_score': quality_report.overall_score if quality_report else None,
                'factual_accuracy': quality_report.factual_accuracy.score if quality_report else None,
                'content_structure': quality_report.content_structure.score if quality_report else None,
                'cultural_sensitivity': quality_report.cultural_sensitivity.score if quality_report else None,
                'originality': quality_report.originality.score if quality_report else None,
                'source_attribution': quality_report.source_attribution.score if quality_report else None,
                'passed_quality': quality_report.passed if quality_report else None
            }
        }
        
        if quality_report is not None:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Quality Control',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 3: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 4: TTS Optimization
    print("Test 4: TTS Optimization...")
    try:
        result = await generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result.get('script')
        has_markers = len(script.tts_markers) > 0 if script else False
        
        test_result = {
            'name': 'TTS Optimization',
            'passed': has_markers,
            'details': {
                'has_tts_markers': has_markers,
                'num_markers': len(script.tts_markers) if script else 0,
                'marker_types': list({m.type for m in script.tts_markers}) if script and has_markers else []
            }
        }
        
        if has_markers:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'TTS Optimization',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 4: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 5: User Personalization (Different Lengths)
    print("Test 5: User Personalization (Different Lengths)...")
    try:
        short_prefs = UserProfile(user_id='test', preferred_length='short')
        result_short = await generator.generate_base_podcast(sample_content, short_prefs)
        
        long_prefs = UserProfile(user_id='test', preferred_length='long')
        result_long = await generator.generate_base_podcast(sample_content, long_prefs)
        
        short_duration = result_short['script'].estimated_duration_seconds if result_short.get('script') else 0
        long_duration = result_long['script'].estimated_duration_seconds if result_long.get('script') else 0
        
        passed = long_duration > short_duration
        
        test_result = {
            'name': 'User Personalization (Different Lengths)',
            'passed': passed,
            'details': {
                'short_duration': short_duration,
                'long_duration': long_duration,
                'long_is_longer': passed
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'User Personalization (Different Lengths)',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 5: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 6: Script Structure
    print("Test 6: Script Structure...")
    try:
        result = await generator.generate_base_podcast(
            content_data=sample_content,
            user_preferences=user_preferences
        )
        
        script = result.get('script')
        section_types = {section.type.value for section in script.sections} if script else set()
        
        has_hook = 'hook' in section_types
        has_conclusion = 'conclusion' in section_types
        has_content = len(script.content) > 100 if script else False
        
        passed = has_hook and has_conclusion and has_content
        
        test_result = {
            'name': 'Script Structure',
            'passed': passed,
            'details': {
                'has_hook': has_hook,
                'has_conclusion': has_conclusion,
                'has_substantial_content': has_content,
                'content_length': len(script.content) if script else 0,
                'num_sections': len(script.sections) if script else 0,
                'section_types': list(section_types)
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Script Structure',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 6: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 7: Batch Generation
    print("Test 7: Batch Generation...")
    try:
        content_items = [
            {**sample_content, 'id': f'test_{i}', 'title': f'Test Content {i}'}
            for i in range(3)
        ]
        
        batch_results = await generator.batch_generate_podcasts(
            content_items=content_items,
            podcast_type=PodcastType.BASE,
            max_concurrent=2
        )
        
        successes = sum(1 for r in batch_results if isinstance(r, dict) and r.get('success'))
        passed = len(batch_results) == 3 and successes == 3
        
        test_result = {
            'name': 'Batch Generation',
            'passed': passed,
            'details': {
                'total_items': len(batch_results),
                'successes': successes,
                'failures': len(batch_results) - successes
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'Batch Generation',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 7: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    # Test 8: TTS Optimizer Pronunciation Dictionary
    print("Test 8: TTS Optimizer Pronunciation Dictionary...")
    try:
        optimizer = TTSOptimizer()
        
        has_dict = len(optimizer.pronunciation_dict) > 0
        has_reykjavik = 'reykjavik' in optimizer.pronunciation_dict
        has_geysir = 'geysir' in optimizer.pronunciation_dict
        
        passed = has_dict and has_reykjavik and has_geysir
        
        test_result = {
            'name': 'TTS Optimizer Pronunciation Dictionary',
            'passed': passed,
            'details': {
                'has_pronunciation_dict': has_dict,
                'dict_size': len(optimizer.pronunciation_dict),
                'has_reykjavik': has_reykjavik,
                'has_geysir': has_geysir,
                'sample_pronunciations': list(optimizer.pronunciation_dict.keys())[:5]
            }
        }
        
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            
    except Exception as e:
        test_result = {
            'name': 'TTS Optimizer Pronunciation Dictionary',
            'passed': False,
            'error': str(e)
        }
        results['summary']['failed'] += 1
        results['summary']['errors'].append(f"Test 8: {str(e)}")
    
    results['tests'].append(test_result)
    results['summary']['total'] += 1
    
    return results


async def main():
    """Main test runner"""
    print("=" * 80)
    print("PHASE 5 COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    try:
        results = await run_all_tests()
        
        # Write results to file
        output_file = Path("phase5_test_results.json")
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
