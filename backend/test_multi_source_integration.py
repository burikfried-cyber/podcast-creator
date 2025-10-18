"""
Test script for multi-source API integration
Run this to verify all services work correctly
"""
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.content.wikidata_service import wikidata_service
from app.services.content.geonames_service import geonames_service
from app.services.content.content_aggregator import content_aggregator


async def test_wikidata():
    """Test Wikidata service"""
    print("\n" + "="*60)
    print("TEST 1: Wikidata Service")
    print("="*60)
    
    location = "Tokyo, Japan"
    print(f"Testing location: {location}")
    
    start = time.time()
    result = await wikidata_service.get_location_content(location)
    elapsed = time.time() - start
    
    print(f"\n✓ Response time: {elapsed:.2f}s")
    print(f"✓ Entity ID: {result.get('entity_id')}")
    print(f"✓ Label: {result.get('label')}")
    print(f"✓ Description: {result.get('description')}")
    print(f"✓ Facts count: {result.get('facts_count')}")
    print(f"✓ Confidence score: {result.get('confidence_score')}")
    
    if result.get('facts'):
        print(f"\n✓ Sample facts:")
        for fact in result['facts'][:5]:
            print(f"  - {fact.get('property')}: {fact.get('value')}")
    
    # Verify success criteria
    assert elapsed < 10, "Timeout exceeded (>10s)"
    assert result.get('entity_id'), "No entity ID found"
    assert result.get('confidence_score', 0) > 0, "Zero confidence score"
    
    print("\n✅ Wikidata test PASSED")
    return result


async def test_geonames():
    """Test GeoNames service"""
    print("\n" + "="*60)
    print("TEST 2: GeoNames Service")
    print("="*60)
    
    location = "Paris, France"
    print(f"Testing location: {location}")
    
    start = time.time()
    result = await geonames_service.get_location_content(location)
    elapsed = time.time() - start
    
    print(f"\n✓ Response time: {elapsed:.2f}s")
    print(f"✓ GeoName ID: {result.get('geoname_id')}")
    print(f"✓ Name: {result.get('name')}")
    print(f"✓ Country: {result.get('country')}")
    print(f"✓ Population: {result.get('population')}")
    print(f"✓ Confidence score: {result.get('confidence_score')}")
    
    hierarchy = result.get('hierarchy', {})
    print(f"\n✓ Hierarchy:")
    for level, value in hierarchy.items():
        if value:
            print(f"  - {level}: {value}")
    
    nearby = result.get('nearby_places', [])
    if nearby:
        print(f"\n✓ Nearby places ({len(nearby)}):")
        for place in nearby[:3]:
            print(f"  - {place.get('name')} ({place.get('distance')}km)")
    
    # Verify success criteria
    assert elapsed < 8, "Timeout exceeded (>8s)"
    assert result.get('geoname_id'), "No geoname ID found"
    assert result.get('confidence_score', 0) > 0, "Zero confidence score"
    
    print("\n✅ GeoNames test PASSED")
    return result


async def test_content_aggregator():
    """Test content aggregator (all sources in parallel)"""
    print("\n" + "="*60)
    print("TEST 3: Content Aggregator (All Sources)")
    print("="*60)
    
    location = "Tokyo, Japan"
    print(f"Testing location: {location}")
    print("Calling all 4 sources in parallel...")
    
    start = time.time()
    result = await content_aggregator.gather_location_content(location)
    elapsed = time.time() - start
    
    metadata = result.get('collection_metadata', {})
    sources = result.get('sources', {})
    quality_scores = result.get('quality_scores', {})
    
    print(f"\n✓ Collection time: {metadata.get('collection_time_seconds')}s")
    print(f"✓ Sources successful: {metadata.get('sources_successful')}/4")
    print(f"✓ Sources failed: {metadata.get('sources_failed')}/4")
    print(f"✓ Overall quality score: {quality_scores.get('overall')}")
    
    print(f"\n✓ Individual source scores:")
    for source_name, score in quality_scores.items():
        if source_name != 'overall':
            status = "✓" if score > 0 else "✗"
            print(f"  {status} {source_name}: {score}")
    
    hierarchy = result.get('hierarchy', {})
    print(f"\n✓ Location hierarchy:")
    for level, value in hierarchy.items():
        print(f"  - {level}: {value or 'N/A'}")
    
    facts = result.get('structured_facts', [])
    print(f"\n✓ Total structured facts: {len(facts)}")
    if facts:
        print(f"  Sample facts:")
        for fact in facts[:3]:
            if fact.get('type') == 'structured':
                print(f"  - [{fact.get('source')}] {fact.get('property')}: {fact.get('value')}")
    
    geo_context = result.get('geographic_context', {})
    if geo_context:
        coords = geo_context.get('coordinates', {})
        print(f"\n✓ Geographic context:")
        print(f"  - Coordinates: {coords.get('lat')}, {coords.get('lng')}")
        print(f"  - Population: {geo_context.get('population')}")
        print(f"  - Nearby places: {len(geo_context.get('nearby_places', []))}")
    
    # Verify success criteria
    assert elapsed < 5, f"Collection time exceeded target (<5s): {elapsed:.2f}s"
    assert metadata.get('sources_successful', 0) >= 2, "Too few sources successful"
    assert quality_scores.get('overall', 0) > 0, "Zero overall quality score"
    assert 0 <= quality_scores.get('overall', 0) <= 1, "Quality score out of range"
    
    print("\n✅ Content aggregator test PASSED")
    return result


async def test_invalid_location():
    """Test graceful handling of invalid location"""
    print("\n" + "="*60)
    print("TEST 4: Invalid Location (Graceful Degradation)")
    print("="*60)
    
    location = "InvalidLocationXYZ123"
    print(f"Testing location: {location}")
    
    start = time.time()
    result = await content_aggregator.gather_location_content(location)
    elapsed = time.time() - start
    
    metadata = result.get('collection_metadata', {})
    
    print(f"\n✓ Collection time: {metadata.get('collection_time_seconds')}s")
    print(f"✓ Sources successful: {metadata.get('sources_successful')}/4")
    print(f"✓ Sources failed: {metadata.get('sources_failed')}/4")
    print(f"✓ Overall quality score: {result.get('quality_scores', {}).get('overall')}")
    
    # Verify graceful handling
    assert elapsed < 5, "Timeout exceeded"
    assert result is not None, "No result returned"
    assert 'sources' in result, "Missing sources in result"
    
    print("\n✅ Invalid location test PASSED (graceful handling)")
    return result


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MULTI-SOURCE API INTEGRATION TEST SUITE")
    print("="*60)
    
    try:
        # Test individual services
        await test_wikidata()
        await test_geonames()
        
        # Test aggregator
        await test_content_aggregator()
        
        # Test error handling
        await test_invalid_location()
        
        # Final summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n✓ Wikidata service: Working")
        print("✓ GeoNames service: Working")
        print("✓ Content aggregator: Working")
        print("✓ Parallel execution: Working")
        print("✓ Error handling: Working")
        print("✓ Quality scoring: Working")
        print("\n🎉 Multi-source API integration is ready for production!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        await wikidata_service.close()
        await geonames_service.close()


if __name__ == "__main__":
    asyncio.run(main())
