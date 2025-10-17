"""
Content Detection Services
Standout detection, base content extraction, and topic-specific detection
"""
from app.services.detection.standout_detector import (
    EnhancedStandoutDetector,
    get_standout_detector
)
from app.services.detection.base_content_detector import (
    BaseContentDetector,
    get_base_content_detector
)
from app.services.detection.topic_specific_detector import (
    TopicSpecificDetector,
    get_topic_specific_detector
)
from app.services.detection.content_classifier import (
    ContentClassifier,
    get_content_classifier
)
from app.services.detection.quality_assurance import (
    QualityAssurancePipeline,
    get_qa_pipeline
)

__all__ = [
    "EnhancedStandoutDetector",
    "get_standout_detector",
    "BaseContentDetector",
    "get_base_content_detector",
    "TopicSpecificDetector",
    "get_topic_specific_detector",
    "ContentClassifier",
    "get_content_classifier",
    "QualityAssurancePipeline",
    "get_qa_pipeline"
]
