"""
Recommendation Services
Hybrid recommendation engine with multiple filtering strategies
"""
from app.services.recommendation.collaborative_filtering import (
    CollaborativeFilter,
    get_collaborative_filter
)
from app.services.recommendation.content_based_filtering import (
    ContentBasedFilter,
    get_content_filter
)
from app.services.recommendation.knowledge_based_filtering import (
    KnowledgeBasedFilter,
    get_knowledge_filter
)
from app.services.recommendation.demographic_filtering import (
    DemographicFilter,
    get_demographic_filter
)
from app.services.recommendation.hybrid_engine import (
    HybridRecommendationEngine,
    get_hybrid_engine
)

__all__ = [
    "CollaborativeFilter",
    "get_collaborative_filter",
    "ContentBasedFilter",
    "get_content_filter",
    "KnowledgeBasedFilter",
    "get_knowledge_filter",
    "DemographicFilter",
    "get_demographic_filter",
    "HybridRecommendationEngine",
    "get_hybrid_engine"
]
