"""
Simple script to analyze detection scores without pytest
"""
import asyncio
import json
from pathlib import Path
import sys

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

async def main():
    # Load test data
    TEST_DB_PATH = Path("C:/Users/burik/podcastCreator/enhanceDetection/complete_test_databases.json")
    
    with open(TEST_DB_PATH, 'r', encoding='utf-8') as f:
        test_databases = json.load(f)
    
    # Create detector
    detector = EnhancedStandoutDetector(MockDB())
    detector.preference_model = MockPreferenceModel()
    
    iceland_data = test_databases["Iceland_Reykjavik"]
    marrakech_data = test_databases["Morocco_Marrakech"]
    
    print(f"\n{'='*80}")
    print(f"FULL DATABASE SCORE ANALYSIS - ALL 40 ITEMS")
    print(f"{'='*80}\n")
    
    # Test ALL items from both locations
    tiers = [
        ("EXCEPTIONAL (Tier 1)", iceland_data["exceptional"] + marrakech_data["exceptional"]),
        ("VERY GOOD (Tier 2)", iceland_data["very_good"] + marrakech_data["very_good"]),
        ("GOOD (Tier 3)", iceland_data["good"] + marrakech_data["good"]),
        ("MUNDANE (Tier 4)", iceland_data.get("ordinary", []) + marrakech_data.get("ordinary", []))
    ]
    
    all_scores = []
    
    for tier_name, items in tiers:
        print(f"\n{tier_name}")
        print(f"{'-'*80}")
        
        for item in items:
            result = await detector.detect_standout_content(item)
            
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
    print(f"SUMMARY STATISTICS - {len(all_scores)} ITEMS TESTED")
    print(f"{'='*80}\n")
    
    tier_stats = {}
    tier_targets = {
        "EXCEPTIONAL (Tier 1)": 5.0,
        "VERY GOOD (Tier 2)": 3.8,
        "GOOD (Tier 3)": 2.3,
        "MUNDANE (Tier 4)": 1.5
    }
    
    for tier_name, _ in tiers:
        tier_scores = [s['score'] for s in all_scores if s['tier'] == tier_name]
        if tier_scores:
            target = tier_targets.get(tier_name, 0)
            above_target = sum(1 for s in tier_scores if s >= target)
            tier_stats[tier_name] = {
                'avg': sum(tier_scores) / len(tier_scores),
                'min': min(tier_scores),
                'max': max(tier_scores),
                'count': len(tier_scores),
                'target': target,
                'above_target': above_target,
                'accuracy': (above_target / len(tier_scores)) * 100 if tier_name != "MUNDANE (Tier 4)" else ((len(tier_scores) - above_target) / len(tier_scores)) * 100
            }
    
    for tier_name, stats in tier_stats.items():
        print(f"{tier_name}:")
        print(f"  Average Score: {stats['avg']:.2f} (target: {stats['target']:.1f})")
        print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
        print(f"  Count: {stats['count']}")
        if tier_name == "MUNDANE (Tier 4)":
            print(f"  Below Target: {stats['count'] - stats['above_target']}/{stats['count']} ({stats['accuracy']:.1f}%)")
        else:
            print(f"  Above Target: {stats['above_target']}/{stats['count']} ({stats['accuracy']:.1f}%)")
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
    
    print(f"\n{'='*80}")
    print(f"GAP ANALYSIS")
    print(f"{'='*80}\n")
    
    # Calculate overall accuracy
    total_correct = sum(stats['above_target'] if tier_name != "MUNDANE (Tier 4)" else (stats['count'] - stats['above_target']) for tier_name, stats in tier_stats.items())
    total_items = sum(stats['count'] for tier_name, stats in tier_stats.items())
    overall_accuracy = (total_correct / total_items) * 100
    
    print(f"Overall Accuracy: {overall_accuracy:.1f}% ({total_correct}/{total_items} items)")
    print()
    
    # Calculate score gaps
    for tier_name, stats in tier_stats.items():
        gap = stats['target'] - stats['avg']
        if tier_name == "MUNDANE (Tier 4)":
            gap = stats['avg'] - stats['target']  # For mundane, we want it below target
        
        if gap > 0:
            multiplier_needed = stats['target'] / stats['avg'] if stats['avg'] > 0 else 0
            print(f"{tier_name}:")
            print(f"  Current Avg: {stats['avg']:.2f}")
            print(f"  Target: {stats['target']:.1f}")
            print(f"  Gap: {gap:.2f} ({gap/stats['target']*100:.1f}% short)")
            if tier_name != "MUNDANE (Tier 4)":
                print(f"  Multiplier Needed: {multiplier_needed:.2f}x")
            print()
    
    print(f"{'='*80}\n")
    
    # Save results to file
    output_file = Path("test_score_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_scores, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    # Save detailed analysis
    analysis_file = Path("full_test_analysis.json")
    analysis = {
        'tier_stats': tier_stats,
        'method_effectiveness': {method: {'avg': avg, 'count': method_counts[method]} for method, avg in method_avgs.items()},
        'overall_accuracy': overall_accuracy,
        'total_items': total_items
    }
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Analysis saved to: {analysis_file}")

if __name__ == "__main__":
    asyncio.run(main())
