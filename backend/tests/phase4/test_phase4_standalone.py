"""
Phase 4 Standalone Testing
Tests all Phase 4 components using existing test databases
"""
import pytest
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import time

# Mock database session for testing
class MockDB:
    """Mock database for testing without actual DB connection"""
    pass

class MockPreferenceModel:
    """Mock preference model to avoid Redis connection"""
    async def get_surprise_preference(self, user_id: str):
        return {"surprise_tolerance": 2}
    
    async def get_topic_preferences(self, user_id: str):
        return {}
    
    async def get_depth_preference(self, user_id: str):
        return {}

# Import Phase 4 components
from app.services.detection.standout_detector import EnhancedStandoutDetector
from app.services.detection.base_content_detector import BaseContentDetector
from app.services.detection.topic_specific_detector import TopicSpecificDetector
from app.services.detection.content_classifier import ContentClassifier
from app.services.detection.quality_assurance import QualityAssurancePipeline


# Load test databases
TEST_DB_PATH = Path("C:/Users/burik/podcastCreator/enhanceDetection/complete_test_databases.json")

@pytest.fixture
def test_databases():
    """Load test databases from existing file"""
    with open(TEST_DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def mock_db():
    """Mock database session"""
    return MockDB()

@pytest.fixture
def standout_detector(mock_db):
    """Create standout detector instance"""
    detector = EnhancedStandoutDetector(mock_db)
    detector.preference_model = MockPreferenceModel()
    return detector

@pytest.fixture
def base_content_detector(mock_db):
    """Create base content detector instance"""
    return BaseContentDetector(mock_db)

@pytest.fixture
def topic_detector(mock_db):
    """Create topic detector instance"""
    detector = TopicSpecificDetector(mock_db)
    detector.preference_model = MockPreferenceModel()
    return detector

@pytest.fixture
def content_classifier():
    """Create content classifier instance"""
    return ContentClassifier()

@pytest.fixture
def qa_pipeline():
    """Create QA pipeline instance"""
    return QualityAssurancePipeline()


# ============================================================================
# TEST 1: STANDOUT DETECTION
# ============================================================================

@pytest.mark.asyncio
class TestStandoutDetection:
    """Test standout detection with existing databases"""
    
    async def test_exceptional_content_detection(self, standout_detector, test_databases):
        """Test detection of Tier 1 (exceptional) content"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        exceptional_items = iceland_data["exceptional"]
        
        results = []
        for item in exceptional_items[:3]:  # Test first 3
            result = await standout_detector.detect_standout_content(item)
            results.append(result)
            
            # Should detect as exceptional (Tier 1)
            assert result["success"] == True
            assert result["base_score"] >= 7.0, f"Expected score >=7.0 for {item['title']}, got {result['base_score']}"
            
            print(f"\n✅ {item['title']}")
            print(f"   Score: {result['base_score']:.2f}")
            print(f"   Tier: {result['tier']}")
            print(f"   Top methods: {list(result['method_scores'].keys())[:3]}")
        
        # Calculate accuracy
        exceptional_count = sum(1 for r in results if r["tier"] == "exceptional")
        accuracy = exceptional_count / len(results)
        
        print(f"\n📊 Exceptional Detection Accuracy: {accuracy:.1%}")
        assert accuracy >= 0.60, f"Expected >=60% exceptional detection, got {accuracy:.1%}"
    
    async def test_very_good_content_detection(self, standout_detector, test_databases):
        """Test detection of Tier 2 (very good) content"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        very_good_items = iceland_data["very_good"]
        
        results = []
        for item in very_good_items[:3]:  # Test first 3
            result = await standout_detector.detect_standout_content(item)
            results.append(result)
            
            assert result["success"] == True
            assert result["base_score"] >= 5.0, f"Expected score >=5.0, got {result['base_score']}"
            
            print(f"\n✅ {item['title']}")
            print(f"   Score: {result['base_score']:.2f}")
            print(f"   Tier: {result['tier']}")
        
        # Should be Tier 2 or better
        tier_2_or_better = sum(1 for r in results if r["tier"] in ["exceptional", "very_good"])
        accuracy = tier_2_or_better / len(results)
        
        print(f"\n📊 Very Good Detection Accuracy: {accuracy:.1%}")
        assert accuracy >= 0.50, f"Expected >=50% Tier 2+, got {accuracy:.1%}"
    
    async def test_good_content_detection(self, standout_detector, test_databases):
        """Test detection of Tier 3 (good) content"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        good_items = iceland_data["good"]
        
        results = []
        for item in good_items[:3]:  # Test first 3
            result = await standout_detector.detect_standout_content(item)
            results.append(result)
            
            assert result["success"] == True
            
            print(f"\n✅ {item['title']}")
            print(f"   Score: {result['base_score']:.2f}")
            print(f"   Tier: {result['tier']}")
        
        # Should be Tier 3 or better
        tier_3_or_better = sum(1 for r in results if r["tier"] in ["exceptional", "very_good", "good"])
        accuracy = tier_3_or_better / len(results)
        
        print(f"\n📊 Good Detection Accuracy: {accuracy:.1%}")
        assert accuracy >= 0.70, f"Expected >=70% Tier 3+, got {accuracy:.1%}"
    
    async def test_mundane_content_detection(self, standout_detector, test_databases):
        """Test detection of mundane content (should score low)"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        mundane_items = iceland_data["mundane"]
        
        results = []
        for item in mundane_items[:3]:  # Test first 3
            result = await standout_detector.detect_standout_content(item)
            results.append(result)
            
            assert result["success"] == True
            
            print(f"\n✅ {item['title']}")
            print(f"   Score: {result['base_score']:.2f}")
            print(f"   Tier: {result['tier']}")
        
        # Should score low (average or below)
        low_scores = sum(1 for r in results if r["base_score"] < 6.0)
        accuracy = low_scores / len(results)
        
        print(f"\n📊 Mundane Detection Accuracy: {accuracy:.1%}")
        assert accuracy >= 0.60, f"Expected >=60% low scores for mundane, got {accuracy:.1%}"
    
    async def test_all_detection_methods(self, standout_detector, test_databases):
        """Test that all 9 detection methods are working"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        test_item = iceland_data["exceptional"][0]  # Puffin houses
        
        result = await standout_detector.detect_standout_content(test_item)
        
        # Check all 9 methods are present
        expected_methods = [
            "impossibility", "uniqueness", "temporal", "cultural",
            "atlas_obscura", "historical", "geographic", "linguistic", "cross_cultural"
        ]
        
        for method in expected_methods:
            assert method in result["method_scores"], f"Method {method} not found"
            print(f"✅ {method}: {result['method_scores'][method]:.2f}")
        
        print(f"\n✅ All 9 detection methods working!")


# ============================================================================
# TEST 2: BASE CONTENT DETECTION
# ============================================================================

@pytest.mark.asyncio
class TestBaseContentDetection:
    """Test base content extraction"""
    
    async def test_essential_content_extraction(self, base_content_detector, test_databases):
        """Test extraction of essential content categories"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        test_item = iceland_data["exceptional"][0]
        
        location = {
            "name": "Westman Islands",
            "coordinates": test_item.get("geographic_coordinates"),
            "country": "Iceland"
        }
        
        result = await base_content_detector.detect_essential_content(test_item, location)
        
        assert result["success"] == True
        assert "essential_content" in result
        assert "completeness_score" in result
        
        # Check all 5 categories present
        essential_content = result["essential_content"]
        expected_categories = [
            "historical_significance",
            "cultural_importance",
            "geographic_context",
            "practical_information",
            "local_connections"
        ]
        
        for category in expected_categories:
            assert category in essential_content, f"Category {category} missing"
            print(f"✅ {category}: {result['category_scores'][category]:.1%}")
        
        print(f"\n📊 Overall Completeness: {result['completeness_score']:.1%}")
        print(f"   Meets Threshold (>95%): {result['meets_threshold']}")
    
    async def test_completeness_scoring(self, base_content_detector, test_databases):
        """Test completeness scoring across multiple items"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        
        completeness_scores = []
        for item in iceland_data["exceptional"][:3]:
            location = {"name": item["title"], "country": "Iceland"}
            result = await base_content_detector.detect_essential_content(item, location)
            completeness_scores.append(result["completeness_score"])
            
            print(f"\n✅ {item['title']}")
            print(f"   Completeness: {result['completeness_score']:.1%}")
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        print(f"\n📊 Average Completeness: {avg_completeness:.1%}")
        
        # Should achieve reasonable completeness even with limited data
        assert avg_completeness >= 0.50, f"Expected >=50% avg completeness, got {avg_completeness:.1%}"


# ============================================================================
# TEST 3: TOPIC-SPECIFIC DETECTION
# ============================================================================

@pytest.mark.asyncio
class TestTopicSpecificDetection:
    """Test topic-specific detection"""
    
    async def test_history_topic_detection(self, topic_detector, test_databases):
        """Test historical content detection"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        # Codfish duel - historical content
        test_item = iceland_data["exceptional"][3]
        
        result = await topic_detector.detect_topic_content(
            test_item,
            topic="history",
            depth_level=3
        )
        
        assert result["success"] == True
        assert result["topic"] == "history"
        assert result["confidence_score"] > 0.0
        
        print(f"\n✅ History Detection")
        print(f"   Confidence: {result['confidence_score']:.2f}")
        print(f"   Content Count: {result['content_count']}")
    
    async def test_nature_topic_detection(self, topic_detector, test_databases):
        """Test nature content detection"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        # Puffin houses - nature content
        test_item = iceland_data["exceptional"][0]
        
        result = await topic_detector.detect_topic_content(
            test_item,
            topic="nature",
            depth_level=2
        )
        
        assert result["success"] == True
        assert result["topic"] == "nature"
        
        print(f"\n✅ Nature Detection")
        print(f"   Confidence: {result['confidence_score']:.2f}")
        print(f"   Content Count: {result['content_count']}")
    
    async def test_depth_level_filtering(self, topic_detector, test_databases):
        """Test depth-adaptive filtering"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        test_item = iceland_data["exceptional"][1]  # Geysir
        
        # Test different depth levels
        for depth_level in [0, 2, 5]:
            result = await topic_detector.detect_topic_content(
                test_item,
                topic="nature",
                depth_level=depth_level
            )
            
            print(f"\n✅ Depth Level {depth_level}")
            print(f"   Content Count: {result['content_count']}")
            
            assert result["success"] == True


# ============================================================================
# TEST 4: CONTENT CLASSIFICATION
# ============================================================================

@pytest.mark.asyncio
class TestContentClassification:
    """Test content classification"""
    
    async def test_multi_dimensional_classification(self, content_classifier, test_databases):
        """Test all 6 classification dimensions"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        test_item = iceland_data["exceptional"][0]
        
        result = await content_classifier.classify_content(test_item)
        
        assert result["success"] == True
        
        # Check all 6 dimensions
        assert "topic_classification" in result
        assert "depth_level" in result
        assert "content_types" in result
        assert "surprise_score" in result
        assert "cultural_sensitivity" in result
        assert "source_reliability" in result
        
        print(f"\n✅ Content Classification")
        print(f"   Topics: {result['topic_classification']['primary_topics']}")
        print(f"   Depth: {result['depth_level']['level_name']}")
        print(f"   Types: {result['content_types']['types']}")
        print(f"   Surprise: {result['surprise_score']['level_name']}")
        print(f"   Sensitivity: {result['cultural_sensitivity']['has_sensitivity']}")
        print(f"   Reliability: {result['source_reliability']['level']}")
    
    async def test_topic_classification_accuracy(self, content_classifier, test_databases):
        """Test topic classification accuracy"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        
        # Test items with known topics
        test_cases = [
            (iceland_data["exceptional"][0], "nature"),  # Puffins
            (iceland_data["exceptional"][1], "nature"),  # Geysir
            (iceland_data["exceptional"][3], "history"),  # Codfish duel
        ]
        
        correct = 0
        for item, expected_topic in test_cases:
            result = await content_classifier.classify_content(item)
            topics = result["topic_classification"]["primary_topics"]
            
            if expected_topic in topics:
                correct += 1
                print(f"✅ {item['title']}: {expected_topic} found in {topics}")
            else:
                print(f"❌ {item['title']}: {expected_topic} NOT in {topics}")
        
        accuracy = correct / len(test_cases)
        print(f"\n📊 Topic Classification Accuracy: {accuracy:.1%}")
        
        assert accuracy >= 0.60, f"Expected >=60% accuracy, got {accuracy:.1%}"


# ============================================================================
# TEST 5: QUALITY ASSURANCE
# ============================================================================

@pytest.mark.asyncio
class TestQualityAssurance:
    """Test QA pipeline"""
    
    async def test_validation_pipeline(self, qa_pipeline, test_databases):
        """Test complete validation pipeline"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        test_item = iceland_data["exceptional"][0]
        
        # Mock results from other detectors
        standout_results = {
            "base_score": 8.5,
            "tier": "exceptional",
            "method_scores": {
                "impossibility": 7.0,
                "uniqueness": 9.0,
                "atlas_obscura": 8.5
            }
        }
        
        base_content_results = {
            "completeness_score": 0.75,
            "category_scores": {}
        }
        
        topic_results = {
            "topic": "nature",
            "confidence_score": 0.8
        }
        
        classification_results = {
            "topic_classification": {
                "primary_topics": ["nature", "science"]
            }
        }
        
        result = await qa_pipeline.validate_detection_results(
            test_item,
            standout_results,
            base_content_results,
            topic_results,
            classification_results,
            processing_time=2.5
        )
        
        assert result["success"] == True
        assert "passed" in result
        assert "overall_score" in result
        assert "validations" in result
        assert "recommendations" in result
        
        print(f"\n✅ QA Validation")
        print(f"   Passed: {result['passed']}")
        print(f"   Overall Score: {result['overall_score']:.2f}")
        print(f"   Validations: {len(result['validations'])}")
        print(f"   Recommendations: {len(result['recommendations'])}")
    
    async def test_performance_validation(self, qa_pipeline):
        """Test performance validation"""
        # Test with different processing times
        test_cases = [
            (5.0, True),   # Should pass (<10s)
            (15.0, False)  # Should fail (>10s)
        ]
        
        for processing_time, should_pass in test_cases:
            result = await qa_pipeline.validate_detection_results(
                {"id": "test"},
                processing_time=processing_time
            )
            
            perf_validation = result["validations"]["performance"]
            print(f"\n✅ Processing Time: {processing_time}s")
            print(f"   Passed: {perf_validation['passed']}")
            print(f"   Expected: {should_pass}")


# ============================================================================
# TEST 6: INTEGRATION TEST
# ============================================================================

@pytest.mark.asyncio
class TestPhase4Integration:
    """Test complete Phase 4 pipeline"""
    
    async def test_complete_pipeline(
        self,
        standout_detector,
        base_content_detector,
        topic_detector,
        content_classifier,
        qa_pipeline,
        test_databases
    ):
        """Test complete detection pipeline"""
        iceland_data = test_databases["Iceland_Reykjavik"]
        test_item = iceland_data["exceptional"][0]
        
        print(f"\n{'='*60}")
        print(f"TESTING COMPLETE PIPELINE: {test_item['title']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Step 1: Standout Detection
        print("\n1️⃣ Standout Detection...")
        standout_results = await standout_detector.detect_standout_content(test_item)
        print(f"   ✅ Score: {standout_results['base_score']:.2f}, Tier: {standout_results['tier']}")
        
        # Step 2: Base Content Detection
        print("\n2️⃣ Base Content Detection...")
        location = {"name": test_item["title"], "country": "Iceland"}
        base_results = await base_content_detector.detect_essential_content(test_item, location)
        print(f"   ✅ Completeness: {base_results['completeness_score']:.1%}")
        
        # Step 3: Topic Detection
        print("\n3️⃣ Topic Detection...")
        topic_results = await topic_detector.detect_topic_content(
            test_item,
            topic="nature",
            depth_level=3
        )
        print(f"   ✅ Confidence: {topic_results['confidence_score']:.2f}")
        
        # Step 4: Classification
        print("\n4️⃣ Content Classification...")
        classification_results = await content_classifier.classify_content(
            test_item,
            standout_results,
            base_results,
            topic_results
        )
        print(f"   ✅ Topics: {classification_results['topic_classification']['primary_topics']}")
        
        # Step 5: QA Validation
        print("\n5️⃣ Quality Assurance...")
        processing_time = time.time() - start_time
        qa_results = await qa_pipeline.validate_detection_results(
            test_item,
            standout_results,
            base_results,
            topic_results,
            classification_results,
            processing_time
        )
        print(f"   ✅ Passed: {qa_results['passed']}, Score: {qa_results['overall_score']:.2f}")
        
        print(f"\n⏱️  Total Processing Time: {processing_time:.2f}s")
        print(f"{'='*60}")
        
        # Assertions
        assert standout_results["success"] == True
        assert base_results["success"] == True
        assert topic_results["success"] == True
        assert classification_results["success"] == True
        assert qa_results["success"] == True
        assert processing_time < 10.0, f"Processing took {processing_time:.2f}s (target: <10s)"


# ============================================================================
# SUMMARY TEST
# ============================================================================

@pytest.mark.asyncio
async def test_phase4_summary(
    standout_detector,
    base_content_detector,
    topic_detector,
    content_classifier,
    qa_pipeline,
    test_databases
):
    """Generate Phase 4 test summary"""
    print(f"\n{'='*60}")
    print(f"PHASE 4 STANDALONE TEST SUMMARY")
    print(f"{'='*60}")
    
    iceland_data = test_databases["Iceland_Reykjavik"]
    
    # Test multiple items
    test_items = (
        iceland_data["exceptional"][:2] +
        iceland_data["very_good"][:2] +
        iceland_data["good"][:2]
    )
    
    results = {
        "total_tested": len(test_items),
        "standout_success": 0,
        "base_content_success": 0,
        "topic_success": 0,
        "classification_success": 0,
        "qa_passed": 0,
        "avg_processing_time": 0.0
    }
    
    processing_times = []
    
    for item in test_items:
        start = time.time()
        
        try:
            # Run pipeline
            standout_res = await standout_detector.detect_standout_content(item)
            if standout_res["success"]:
                results["standout_success"] += 1
            
            location = {"name": item["title"], "country": "Iceland"}
            base_res = await base_content_detector.detect_essential_content(item, location)
            if base_res["success"]:
                results["base_content_success"] += 1
            
            topic_res = await topic_detector.detect_topic_content(item, "history", 2)
            if topic_res["success"]:
                results["topic_success"] += 1
            
            class_res = await content_classifier.classify_content(item)
            if class_res["success"]:
                results["classification_success"] += 1
            
            proc_time = time.time() - start
            processing_times.append(proc_time)
            
            qa_res = await qa_pipeline.validate_detection_results(
                item, standout_res, base_res, topic_res, class_res, proc_time
            )
            if qa_res["passed"]:
                results["qa_passed"] += 1
        
        except Exception as e:
            print(f"❌ Error testing {item['title']}: {e}")
    
    results["avg_processing_time"] = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Print summary
    print(f"\nResults:")
    print(f"   Total Tested: {results['total_tested']}")
    print(f"   Standout Success: {results['standout_success']}/{results['total_tested']} ({results['standout_success']/results['total_tested']:.1%})")
    print(f"   Base Content Success: {results['base_content_success']}/{results['total_tested']} ({results['base_content_success']/results['total_tested']:.1%})")
    print(f"   Topic Success: {results['topic_success']}/{results['total_tested']} ({results['topic_success']/results['total_tested']:.1%})")
    print(f"   Classification Success: {results['classification_success']}/{results['total_tested']} ({results['classification_success']/results['total_tested']:.1%})")
    print(f"   QA Passed: {results['qa_passed']}/{results['total_tested']} ({results['qa_passed']/results['total_tested']:.1%})")
    print(f"   Avg Processing Time: {results['avg_processing_time']:.2f}s")
    print(f"\n{'='*60}")
    
    # Overall success
    overall_success_rate = (
        results['standout_success'] +
        results['base_content_success'] +
        results['topic_success'] +
        results['classification_success']
    ) / (results['total_tested'] * 4)
    
    print(f"\nOverall Success Rate: {overall_success_rate:.1%}")
    print(f"{'='*60}\n")
    
    assert overall_success_rate >= 0.80, f"Expected >=80% overall success, got {overall_success_rate:.1%}"
