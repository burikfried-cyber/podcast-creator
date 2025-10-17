"""
Quality Assurance Pipeline
Validation checks and quality scoring for detected content
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class QualityAssurancePipeline:
    """
    Quality Assurance for Content Detection
    
    Validations:
    1. Completeness Check (>95% for base content)
    2. Accuracy Validation (standout detection consistency)
    3. Relevance Scoring (topic-content alignment)
    4. Quality Metrics (overall content quality)
    5. Performance Monitoring (<10s total processing)
    """
    
    def __init__(self):
        # Quality thresholds
        self.thresholds = {
            "completeness": 0.95,
            "accuracy": 0.80,
            "relevance": 0.85,
            "overall_quality": 0.75,
            "processing_time": 10.0  # seconds
        }
        
        # Validation weights
        self.validation_weights = {
            "completeness": 0.30,
            "accuracy": 0.25,
            "relevance": 0.25,
            "quality": 0.20
        }
    
    async def validate_detection_results(
        self,
        content: Dict[str, Any],
        standout_results: Optional[Dict[str, Any]] = None,
        base_content_results: Optional[Dict[str, Any]] = None,
        topic_results: Optional[Dict[str, Any]] = None,
        classification_results: Optional[Dict[str, Any]] = None,
        processing_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate all detection results
        
        Args:
            content: Original content
            standout_results: Standout detection results
            base_content_results: Base content detection results
            topic_results: Topic-specific detection results
            classification_results: Classification results
            processing_time: Total processing time in seconds
            
        Returns:
            Validation results with pass/fail and quality score
        """
        try:
            logger.info("qa_validation_started",
                       content_id=content.get("id"))
            
            validations = {}
            
            # 1. Completeness Check
            completeness_result = self._check_completeness(
                base_content_results
            )
            validations["completeness"] = completeness_result
            
            # 2. Accuracy Validation
            accuracy_result = self._validate_accuracy(
                standout_results,
                classification_results
            )
            validations["accuracy"] = accuracy_result
            
            # 3. Relevance Scoring
            relevance_result = self._score_relevance(
                content,
                topic_results,
                classification_results
            )
            validations["relevance"] = relevance_result
            
            # 4. Quality Metrics
            quality_result = self._assess_quality(
                content,
                standout_results,
                base_content_results,
                topic_results
            )
            validations["quality"] = quality_result
            
            # 5. Performance Check
            performance_result = self._check_performance(processing_time)
            validations["performance"] = performance_result
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(validations)
            
            # Determine pass/fail
            passed = self._determine_pass_fail(validations, overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(validations)
            
            logger.info("qa_validation_complete",
                       content_id=content.get("id"),
                       passed=passed,
                       score=overall_score)
            
            return {
                "success": True,
                "content_id": content.get("id"),
                "passed": passed,
                "overall_score": overall_score,
                "validations": validations,
                "recommendations": recommendations,
                "validated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("qa_validation_failed",
                        content_id=content.get("id"),
                        error=str(e))
            raise
    
    def _check_completeness(
        self,
        base_content_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check completeness of base content (target >95%)"""
        if not base_content_results:
            return {
                "score": 0.0,
                "passed": False,
                "message": "No base content results provided"
            }
        
        completeness_score = base_content_results.get("completeness_score", 0.0)
        passed = completeness_score >= self.thresholds["completeness"]
        
        return {
            "score": completeness_score,
            "passed": passed,
            "threshold": self.thresholds["completeness"],
            "message": f"Completeness: {completeness_score:.2%} (target: {self.thresholds['completeness']:.0%})"
        }
    
    def _validate_accuracy(
        self,
        standout_results: Optional[Dict[str, Any]],
        classification_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate accuracy of standout detection (target 80%)"""
        if not standout_results:
            return {
                "score": 0.0,
                "passed": False,
                "message": "No standout results provided"
            }
        
        # Check consistency between standout tier and classification
        tier = standout_results.get("tier", "average")
        
        # Estimate accuracy based on method scores
        method_scores = standout_results.get("method_scores", {})
        if method_scores:
            # Check if multiple methods agree
            high_scores = sum(1 for score in method_scores.values() if score > 7.0)
            total_methods = len(method_scores)
            
            if total_methods > 0:
                agreement_rate = high_scores / total_methods
                # Accuracy estimate based on method agreement
                accuracy_score = 0.6 + (agreement_rate * 0.4)
            else:
                accuracy_score = 0.5
        else:
            accuracy_score = 0.5
        
        passed = accuracy_score >= self.thresholds["accuracy"]
        
        return {
            "score": accuracy_score,
            "passed": passed,
            "threshold": self.thresholds["accuracy"],
            "tier": tier,
            "message": f"Accuracy: {accuracy_score:.2%} (target: {self.thresholds['accuracy']:.0%})"
        }
    
    def _score_relevance(
        self,
        content: Dict[str, Any],
        topic_results: Optional[Dict[str, Any]],
        classification_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Score relevance of topic detection (target >85%)"""
        if not topic_results or not classification_results:
            return {
                "score": 0.5,
                "passed": False,
                "message": "Insufficient data for relevance scoring"
            }
        
        # Check if detected topic matches classification
        detected_topic = topic_results.get("topic")
        classified_topics = classification_results.get("topic_classification", {}).get("primary_topics", [])
        
        if detected_topic in classified_topics:
            relevance_score = 0.9
        elif detected_topic:
            relevance_score = 0.7
        else:
            relevance_score = 0.5
        
        # Boost if confidence is high
        confidence = topic_results.get("confidence_score", 0.0)
        relevance_score = min(relevance_score + (confidence * 0.1), 1.0)
        
        passed = relevance_score >= self.thresholds["relevance"]
        
        return {
            "score": relevance_score,
            "passed": passed,
            "threshold": self.thresholds["relevance"],
            "detected_topic": detected_topic,
            "classified_topics": classified_topics,
            "message": f"Relevance: {relevance_score:.2%} (target: {self.thresholds['relevance']:.0%})"
        }
    
    def _assess_quality(
        self,
        content: Dict[str, Any],
        standout_results: Optional[Dict[str, Any]],
        base_content_results: Optional[Dict[str, Any]],
        topic_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess overall content quality"""
        quality_factors = []
        
        # Factor 1: Content length
        text = self._extract_text(content)
        word_count = len(text.split())
        if word_count > 100:
            quality_factors.append(0.8)
        elif word_count > 50:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.3)
        
        # Factor 2: Standout score
        if standout_results:
            standout_score = standout_results.get("base_score", 0.0)
            quality_factors.append(min(standout_score / 10.0, 1.0))
        
        # Factor 3: Base content completeness
        if base_content_results:
            completeness = base_content_results.get("completeness_score", 0.0)
            quality_factors.append(completeness)
        
        # Factor 4: Topic confidence
        if topic_results:
            confidence = topic_results.get("confidence_score", 0.0)
            quality_factors.append(confidence)
        
        # Calculate average
        if quality_factors:
            quality_score = sum(quality_factors) / len(quality_factors)
        else:
            quality_score = 0.5
        
        passed = quality_score >= self.thresholds["overall_quality"]
        
        return {
            "score": quality_score,
            "passed": passed,
            "threshold": self.thresholds["overall_quality"],
            "factors": {
                "word_count": word_count,
                "num_factors": len(quality_factors)
            },
            "message": f"Quality: {quality_score:.2%} (target: {self.thresholds['overall_quality']:.0%})"
        }
    
    def _check_performance(
        self,
        processing_time: Optional[float]
    ) -> Dict[str, Any]:
        """Check processing performance (target <10s)"""
        if processing_time is None:
            return {
                "score": 1.0,
                "passed": True,
                "message": "No processing time provided"
            }
        
        passed = processing_time < self.thresholds["processing_time"]
        
        # Score based on how close to threshold
        if processing_time < self.thresholds["processing_time"]:
            score = 1.0
        else:
            # Penalty for exceeding threshold
            score = max(0.0, 1.0 - ((processing_time - self.thresholds["processing_time"]) / 10.0))
        
        return {
            "score": score,
            "passed": passed,
            "processing_time": processing_time,
            "threshold": self.thresholds["processing_time"],
            "message": f"Processing: {processing_time:.2f}s (target: <{self.thresholds['processing_time']:.0f}s)"
        }
    
    def _calculate_overall_score(
        self,
        validations: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate weighted overall score"""
        weighted_scores = []
        
        for validation_type, weight in self.validation_weights.items():
            if validation_type in validations:
                score = validations[validation_type].get("score", 0.0)
                weighted_scores.append(score * weight)
        
        return sum(weighted_scores)
    
    def _determine_pass_fail(
        self,
        validations: Dict[str, Dict[str, Any]],
        overall_score: float
    ) -> bool:
        """Determine if content passes QA"""
        # Must pass critical validations
        critical_validations = ["completeness", "accuracy"]
        
        for validation in critical_validations:
            if validation in validations:
                if not validations[validation].get("passed", False):
                    return False
        
        # Overall score must be above threshold
        return overall_score >= 0.70
    
    def _generate_recommendations(
        self,
        validations: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        for validation_type, result in validations.items():
            if not result.get("passed", True):
                if validation_type == "completeness":
                    recommendations.append(
                        "Improve base content completeness by gathering more essential information"
                    )
                elif validation_type == "accuracy":
                    recommendations.append(
                        "Review standout detection methods for better accuracy"
                    )
                elif validation_type == "relevance":
                    recommendations.append(
                        "Ensure topic detection aligns with content classification"
                    )
                elif validation_type == "quality":
                    recommendations.append(
                        "Enhance content quality by adding more detailed information"
                    )
                elif validation_type == "performance":
                    recommendations.append(
                        "Optimize processing pipeline to reduce latency"
                    )
        
        if not recommendations:
            recommendations.append("All quality checks passed - content is ready")
        
        return recommendations
    
    def _extract_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from content"""
        text_parts = []
        
        for key, value in content.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend([str(v) for v in value if isinstance(v, str)])
        
        return " ".join(text_parts)
    
    async def generate_quality_report(
        self,
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed quality report"""
        return {
            "summary": {
                "passed": validation_results.get("passed", False),
                "overall_score": validation_results.get("overall_score", 0.0),
                "timestamp": validation_results.get("validated_at")
            },
            "details": validation_results.get("validations", {}),
            "recommendations": validation_results.get("recommendations", []),
            "thresholds": self.thresholds
        }


def get_qa_pipeline() -> QualityAssurancePipeline:
    """Get QA pipeline instance"""
    return QualityAssurancePipeline()
