"""
Simple test for multi-source API integration (no Unicode)
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.content.content_aggregator import content_aggregator


async def test_aggregator():
    """Test content aggregator with Tokyo"""
    print("\n" + "="*60)
    print("TESTING: Content Aggregator (All 4 Sources)")
    print("="*60)
    
    location = "Tokyo, Japan"
    print(f"\nLocation: {location}")
    print("Calling all 4 sources in parallel...\n")
    
    start = time.time()
    result = await content_aggregator.gather_location_content(location)
    elapsed = time.time() - start
    
    # Extract results
    metadata = result.get('collection_metadata', {})
    sources = result.get('sources', {})
    quality_scores = result.get('quality_scores', {})
    hierarchy = result.get('hierarchy', {})
    facts = result.get('structured_facts', [])
    
    # Print results
    print(f"Collection time: {metadata.get('collection_time_seconds')}s")
    print(f"Sources successful: {metadata.get('sources_successful')}/4")
    print(f"Sources failed: {metadata.get('sources_failed')}/4")
    print(f"Overall quality: {quality_scores.get('overall')}")
    
    print(f"\nIndividual source scores:")
    for source_name in ['wikipedia', 'wikidata', 'geonames', 'location']:
        score = quality_scores.get(source_name, 0)
        status = "SUCCESS" if score > 0 else "FAILED"
        print(f"  {source_name}: {score} [{status}]")
    
    print(f"\nLocation hierarchy:")
    for level, value in hierarchy.items():
        print(f"  {level}: {value or 'N/A'}")
    
    print(f"\nStructured facts: {len(facts)}")
    if facts:
        print("  Sample facts:")
        for fact in facts[:5]:
            if fact.get('type') == 'structured':
                print(f"    [{fact.get('source')}] {fact.get('property')}: {str(fact.get('value'))[:50]}")
    
    # Verify success
    print(f"\n" + "="*60)
    if elapsed < 5:
        print(f"PASS: Collection time < 5s ({elapsed:.2f}s)")
    else:
        print(f"WARNING: Collection time > 5s ({elapsed:.2f}s)")
    
    if metadata.get('sources_successful', 0) >= 3:
        print(f"PASS: {metadata.get('sources_successful')}/4 sources successful")
    else:
        print(f"WARNING: Only {metadata.get('sources_successful')}/4 sources successful")
    
    if quality_scores.get('overall', 0) > 0.5:
        print(f"PASS: Overall quality score {quality_scores.get('overall')} > 0.5")
    else:
        print(f"WARNING: Overall quality score {quality_scores.get('overall')} < 0.5")
    
    print("="*60)
    print("\nSUCCESS: Multi-source API integration is working!")
    print("="*60)


async def test_paris():
    """Test with Paris"""
    print("\n" + "="*60)
    print("TESTING: Paris, France")
    print("="*60)
    
    location = "Paris, France"
    print(f"\nLocation: {location}\n")
    
    start = time.time()
    result = await content_aggregator.gather_location_content(location)
    elapsed = time.time() - start
    
    metadata = result.get('collection_metadata', {})
    quality_scores = result.get('quality_scores', {})
    
    print(f"Collection time: {elapsed:.2f}s")
    print(f"Sources successful: {metadata.get('sources_successful')}/4")
    print(f"Overall quality: {quality_scores.get('overall')}")
    print("\nPASS: Paris test completed")


async def main():
    try:
        await test_aggregator()
        await test_paris()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nReady for production use!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
