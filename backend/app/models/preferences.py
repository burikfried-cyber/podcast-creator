"""
User Preference Models
Multi-dimensional user preference tracking with behavioral learning
"""
from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db.base import Base
from app.db.types import UUID, JSONB, ARRAY


class UserTopicPreference(Base):
    """
    User topic preferences with exponential moving average updates
    Tracks 10 primary categories × 120 subcategories
    """
    
    __tablename__ = "user_topic_preferences"
    
    # Composite primary key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_category = Column(String(50), primary_key=True, nullable=False)
    subcategory = Column(String(100), primary_key=True, nullable=False)
    
    # Preference metrics
    preference_weight = Column(DECIMAL(4, 3), nullable=False, default=0.500)  # 0.000 to 1.000
    confidence_score = Column(DECIMAL(3, 2), nullable=False, default=0.50)  # 0.00 to 1.00
    
    # Learning metadata
    interaction_count = Column(Integer, default=0, nullable=False)
    last_interaction = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_user_topic_weight', 'user_id', 'preference_weight'),
        Index('idx_topic_category', 'topic_category', 'subcategory'),
    )
    
    # Relationship
    user = relationship("User", back_populates="topic_preferences")
    
    def __repr__(self) -> str:
        return f"<UserTopicPreference(user={self.user_id}, category={self.topic_category}, weight={self.preference_weight})>"


class UserDepthPreference(Base):
    """
    User depth preferences with Bayesian optimization
    6-level scale: Surface, Light, Moderate, Detailed, Deep, Academic
    """
    
    __tablename__ = "user_depth_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Depth level preferences (0-5 scale)
    surface_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)  # Level 0
    light_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)    # Level 1
    moderate_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167) # Level 2
    detailed_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167) # Level 3
    deep_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)     # Level 4
    academic_weight = Column(DECIMAL(4, 3), nullable=False, default=0.165) # Level 5
    
    # Current preferred depth (0-5)
    preferred_depth = Column(Integer, nullable=False, default=2)
    
    # Bayesian optimization parameters
    alpha_prior = Column(DECIMAL(5, 2), nullable=False, default=1.0)
    beta_prior = Column(DECIMAL(5, 2), nullable=False, default=1.0)
    
    # Confidence
    confidence_score = Column(DECIMAL(3, 2), nullable=False, default=0.50)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="depth_preference")
    
    def __repr__(self) -> str:
        return f"<UserDepthPreference(user={self.user_id}, preferred={self.preferred_depth})>"


class UserSurprisePreference(Base):
    """
    User surprise tolerance with reinforcement learning
    6-level psychological scale: Predictable to Radical
    """
    
    __tablename__ = "user_surprise_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Surprise level preferences (0-5 scale)
    predictable_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)  # Level 0
    familiar_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)     # Level 1
    balanced_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)     # Level 2
    adventurous_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)  # Level 3
    exploratory_weight = Column(DECIMAL(4, 3), nullable=False, default=0.167)  # Level 4
    radical_weight = Column(DECIMAL(4, 3), nullable=False, default=0.165)      # Level 5
    
    # Current surprise tolerance (0-5)
    surprise_tolerance = Column(Integer, nullable=False, default=2)
    
    # Reinforcement learning parameters
    exploration_rate = Column(DECIMAL(3, 2), nullable=False, default=0.40)  # Epsilon
    learning_rate = Column(DECIMAL(4, 3), nullable=False, default=0.010)
    
    # Q-values for each surprise level
    q_values = Column(JSONB, nullable=False, default=dict)
    
    # Confidence
    confidence_score = Column(DECIMAL(3, 2), nullable=False, default=0.50)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="surprise_preference")
    
    def __repr__(self) -> str:
        return f"<UserSurprisePreference(user={self.user_id}, tolerance={self.surprise_tolerance})>"


class UserContextualPreference(Base):
    """
    Contextual preferences with multi-armed bandit selection
    Tracks time, device, location, mood contexts
    """
    
    __tablename__ = "user_contextual_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Context dimensions
    context_type = Column(String(50), nullable=False)  # time, device, location, mood
    context_value = Column(String(100), nullable=False)  # morning, mobile, home, relaxed
    
    # Preference weights for this context
    topic_adjustments = Column(JSONB, nullable=False, default=dict)  # Topic weight adjustments
    depth_adjustment = Column(Integer, nullable=False, default=0)  # -2 to +2
    surprise_adjustment = Column(Integer, nullable=False, default=0)  # -2 to +2
    
    # Multi-armed bandit parameters
    arm_pulls = Column(Integer, default=0, nullable=False)
    total_reward = Column(DECIMAL(10, 4), nullable=False, default=0.0)
    ucb_score = Column(DECIMAL(10, 4), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        Index('idx_user_context', 'user_id', 'context_type', 'context_value', unique=True),
    )
    
    # Relationship
    user = relationship("User", back_populates="contextual_preferences")
    
    def __repr__(self) -> str:
        return f"<UserContextualPreference(user={self.user_id}, type={self.context_type}, value={self.context_value})>"


class UserLearningState(Base):
    """
    Behavioral learning states for HMM, LSTM, and Bandits
    Stores model states for online learning
    """
    
    __tablename__ = "user_learning_states"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Hidden Markov Model state
    hmm_states = Column(JSONB, nullable=False, default=dict)
    # Structure: {
    #   "current_state": "engaged",
    #   "transition_matrix": [[...], [...], ...],
    #   "emission_matrix": [[...], [...], ...],
    #   "state_probabilities": [0.25, 0.25, 0.25, 0.25]
    # }
    
    # LSTM model state
    lstm_model_state = Column(JSONB, nullable=False, default=dict)
    # Structure: {
    #   "hidden_state": [...],
    #   "cell_state": [...],
    #   "sequence_history": [...],
    #   "model_version": "1.0"
    # }
    
    # Multi-armed bandit data
    bandit_arms_data = Column(JSONB, nullable=False, default=dict)
    # Structure: {
    #   "arms": {
    #     "arm_id": {
    #       "pulls": 10,
    #       "rewards": 7.5,
    #       "ucb": 0.85
    #     }
    #   },
    #   "total_pulls": 100
    # }
    
    # Learning confidence
    learning_confidence = Column(DECIMAL(3, 2), nullable=False, default=0.50)
    
    # Model performance metrics
    hmm_accuracy = Column(DECIMAL(3, 2), nullable=True)
    lstm_accuracy = Column(DECIMAL(3, 2), nullable=True)
    bandit_regret = Column(DECIMAL(10, 4), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="learning_state")
    
    def __repr__(self) -> str:
        return f"<UserLearningState(user={self.user_id}, confidence={self.learning_confidence})>"


class UserBehavioralSignal(Base):
    """
    User behavioral signals for preference learning
    Tracks both explicit and implicit feedback
    """
    
    __tablename__ = "user_behavioral_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    podcast_id = Column(UUID(as_uuid=True), nullable=True)  # If related to specific podcast
    
    # Signal type
    signal_type = Column(String(50), nullable=False)  # explicit, implicit
    signal_category = Column(String(50), nullable=False)  # rating, completion, playback, etc.
    
    # Signal data
    signal_value = Column(DECIMAL(5, 3), nullable=False)  # Normalized 0-1
    signal_weight = Column(DECIMAL(3, 2), nullable=False)  # Importance weight
    
    # Context at time of signal
    context_data = Column(JSONB, nullable=False, default=dict)
    # Structure: {
    #   "time_of_day": "morning",
    #   "device": "mobile",
    #   "location": "home",
    #   "session_duration": 1800
    # }
    
    # Raw signal details
    raw_data = Column(JSONB, nullable=True)
    
    # Processing status
    processed = Column(Integer, default=0, nullable=False)  # 0=pending, 1=processed
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_signal_type', 'user_id', 'signal_type', 'created_at'),
        Index('idx_signal_processing', 'processed', 'created_at'),
    )
    
    # Relationship
    user = relationship("User", back_populates="behavioral_signals")
    
    def __repr__(self) -> str:
        return f"<UserBehavioralSignal(user={self.user_id}, type={self.signal_category}, value={self.signal_value})>"


class UserColdStartData(Base):
    """
    Cold start data for new users
    Stores questionnaire responses and initial clustering
    """
    
    __tablename__ = "user_cold_start_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Questionnaire responses
    questionnaire_responses = Column(JSONB, nullable=False, default=dict)
    # Structure: {
    #   "topic_interests": [...],
    #   "depth_preference": 2,
    #   "surprise_tolerance": 3,
    #   "content_examples": [...]
    # }
    
    # Demographic data
    age_range = Column(String(20), nullable=True)
    education_level = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    
    # Clustering results
    cluster_id = Column(Integer, nullable=True)
    cluster_confidence = Column(DECIMAL(3, 2), nullable=True)
    
    # Cold start strategy
    exploration_rate = Column(DECIMAL(3, 2), nullable=False, default=0.40)
    questions_answered = Column(Integer, default=0, nullable=False)
    onboarding_complete = Column(Integer, default=0, nullable=False)  # 0=incomplete, 1=complete
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="cold_start_data")
    
    def __repr__(self) -> str:
        return f"<UserColdStartData(user={self.user_id}, cluster={self.cluster_id}, complete={self.onboarding_complete})>"
