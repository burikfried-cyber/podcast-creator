"""
Detailed Score Analysis - Test all tiers and show method scores
"""
import pytest
import json
import asyncio
from pathlib import Path

# Mock classes
class MockDB:
    pass

class MockPreferenceModel:
    async def get_surprise_preference(self, user_id: str):
        return {"surprise_tolerance": 2}
    async def get_topic_preferences(self, user_id: str):
        return {}
    async def get_depth_preference(self, user_id: str):
        return {}

from app.services.detection.standout_detector import EnhancedStandoutDetector

TEST_DB_PATH = Path("C:/Users/burik/podcastCreator/enhanceDetection/complete_test_databases.json")

@pytest.fixture
def test_databases():
    with open(TEST_DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def standout_detector():
    detector = EnhancedStandoutDetector(MockDB())
    detector.preference_model = MockPreferenceModel()
    return detector


@pytest.mark.asyncio
async def test_detailed_score_analysis(standout_detector, test_databases):
    """Analyze scores across all tiers"""
    
    iceland_data = test_databases["Iceland_Reykjavik"]
    
    print(f"\n{'='*80}")
    print(f"DETAILED SCORE ANALYSIS")
    print(f"{'='*80}\n")
    
    # Test each tier
    tiers = [
        ("EXCEPTIONAL (Tier 1)", iceland_data["exceptional"][:2]),
        ("VERY GOOD (Tier 2)", iceland_data["very_good"][:2]),
        ("GOOD (Tier 3)", iceland_data["good"][:2]),
        ("MUNDANE (Tier 4)", iceland_data.get("ordinary", [])[:2])
    ]
    
    all_scores = []
    
    for tier_name, items in tiers:
        print(f"\n{tier_name}")
        print(f"{'-'*80}")
        
        for item in items:
            result = await standout_detector.detect_standout_content(item)
            
            print(f"\n  Title: {item['title'][:60]}...")
            print(f"  Final Score: {result['base_score']:.2f}")
            print(f"  Tier: {result['tier']}")
            print(f"  Method Scores:")
            
            # Sort methods by score
            sorted_methods = sorted(
                result['method_scores'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for method, score in sorted_methods:
                if score > 0:
                    print(f"    {method:20s}: {score:.2f}")
            
            all_scores.append({
                'tier': tier_name,
                'title': item['title'],
                'score': result['base_score'],
                'detected_tier': result['tier'],
                'methods': result['method_scores']
            })
    
    # Summary statistics
    print(f"\n{'='*80}")
    print(f"SUMMARY STATISTICS")
    print(f"{'='*80}\n")
    
    tier_stats = {}
    for tier_name, _ in tiers:
        tier_scores = [s['score'] for s in all_scores if s['tier'] == tier_name]
        if tier_scores:
            tier_stats[tier_name] = {
                'avg': sum(tier_scores) / len(tier_scores),
                'min': min(tier_scores),
                'max': max(tier_scores),
                'count': len(tier_scores)
            }
    
    for tier_name, stats in tier_stats.items():
        print(f"{tier_name}:")
        print(f"  Average Score: {stats['avg']:.2f}")
        print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
        print(f"  Count: {stats['count']}")
        print()
    
    # Method effectiveness
    print(f"METHOD EFFECTIVENESS (Average Scores):")
    print(f"{'-'*80}")
    
    method_totals = {}
    method_counts = {}
    
    for score_data in all_scores:
        for method, score in score_data['methods'].items():
            if score > 0:
                method_totals[method] = method_totals.get(method, 0) + score
                method_counts[method] = method_counts.get(method, 0) + 1
    
    method_avgs = {
        method: method_totals[method] / method_counts[method]
        for method in method_totals
    }
    
    for method, avg in sorted(method_avgs.items(), key=lambda x: x[1], reverse=True):
        print(f"  {method:20s}: {avg:.2f} (used {method_counts[method]} times)")
    
    print(f"\n{'='*80}\n")
