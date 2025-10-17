"""
Cold Start Solver
Solutions for new user onboarding with interactive questionnaire and exploration
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preferences import (
    UserColdStartData,
    UserTopicPreference,
    UserDepthPreference,
    UserSurprisePreference
)
from app.services.preferences import get_preference_model
from app.services.recommendation import get_demographic_filter

logger = structlog.get_logger()


class ColdStartSolver:
    """
    Cold Start Problem Solver
    
    Features:
    - Interactive questionnaire with adaptive questions
    - Demographic clustering for initial preferences
    - Epsilon-greedy exploration strategy
    - Active learning with uncertainty sampling
    - Information gain maximization
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.preference_model = get_preference_model(db)
        self.demographic_filter = get_demographic_filter(db)
        
        # Exploration parameters
        self.initial_epsilon = 0.4
        self.epsilon_decay = 0.05
        self.min_epsilon = 0.1
        
        # Questionnaire design
        self.questionnaire = self._design_questionnaire()
    
    def _design_questionnaire(self) -> Dict[str, Any]:
        """
        Design adaptive questionnaire for cold start
        
        Returns:
            Questionnaire structure
        """
        return {
            "sections": [
                {
                    "id": "topics",
                    "title": "What topics interest you?",
                    "type": "multi_select_intensity",
                    "questions": [
                        {
                            "id": "topic_interests",
                            "text": "Select topics you'd like to learn about:",
                            "options": [
                                {"value": "history", "label": "History & Culture"},
                                {"value": "science", "label": "Science & Nature"},
                                {"value": "technology", "label": "Technology & Innovation"},
                                {"value": "arts", "label": "Arts & Creativity"},
                                {"value": "philosophy", "label": "Philosophy & Ideas"},
                                {"value": "business", "label": "Business & Economics"},
                                {"value": "culture", "label": "Society & Culture"},
                                {"value": "nature", "label": "Environment & Nature"},
                                {"value": "society", "label": "Politics & Society"},
                                {"value": "personal", "label": "Personal Development"}
                            ],
                            "intensity_scale": [1, 2, 3, 4, 5],
                            "min_selections": 3,
                            "max_selections": 7
                        }
                    ]
                },
                {
                    "id": "depth",
                    "title": "How deep should we go?",
                    "type": "slider_with_examples",
                    "questions": [
                        {
                            "id": "depth_preference",
                            "text": "Choose your preferred content depth:",
                            "scale": [0, 1, 2, 3, 4, 5],
                            "labels": [
                                "Surface - Quick overviews (5-15 min)",
                                "Light - Easy explanations (15-30 min)",
                                "Moderate - Standard depth (30-45 min)",
                                "Detailed - In-depth analysis (45-60 min)",
                                "Deep - Expert level (60-90 min)",
                                "Academic - Research level (90+ min)"
                            ],
                            "examples": {
                                0: "TED Talk style - key ideas only",
                                2: "NPR style - balanced coverage",
                                4: "University lecture style - comprehensive",
                                5: "Academic paper style - exhaustive"
                            }
                        }
                    ]
                },
                {
                    "id": "surprise",
                    "title": "How adventurous are you?",
                    "type": "scenario_based",
                    "questions": [
                        {
                            "id": "surprise_tolerance",
                            "text": "Which content pair appeals to you more?",
                            "scenarios": [
                                {
                                    "option_a": {
                                        "title": "The History of Ancient Rome",
                                        "description": "Classic historical content",
                                        "surprise_level": 0
                                    },
                                    "option_b": {
                                        "title": "How Roman Engineering Influences Modern AI",
                                        "description": "Unexpected connection",
                                        "surprise_level": 4
                                    }
                                },
                                {
                                    "option_a": {
                                        "title": "Introduction to Python Programming",
                                        "description": "Standard tech topic",
                                        "surprise_level": 1
                                    },
                                    "option_b": {
                                        "title": "The Philosophy of Code: Programming as Poetry",
                                        "description": "Creative perspective",
                                        "surprise_level": 3
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "demographics",
                    "title": "Tell us about yourself (optional)",
                    "type": "demographic",
                    "questions": [
                        {
                            "id": "age_range",
                            "text": "Age range:",
                            "type": "select",
                            "options": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
                            "optional": True
                        },
                        {
                            "id": "education_level",
                            "text": "Education level:",
                            "type": "select",
                            "options": ["high_school", "some_college", "bachelors", "masters", "doctorate"],
                            "optional": True
                        },
                        {
                            "id": "occupation",
                            "text": "Occupation:",
                            "type": "text",
                            "optional": True
                        }
                    ]
                }
            ],
            "adaptive_rules": {
                "skip_demographics_if_confident": True,
                "add_refinement_questions": True,
                "max_total_questions": 15
            }
        }
    
    async def start_onboarding(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Start cold start onboarding for new user
        
        Args:
            user_id: User ID
            
        Returns:
            Onboarding session info with first questions
        """
        try:
            # Create cold start data record
            cold_start = UserColdStartData(
                user_id=user_id,
                questionnaire_responses={},
                exploration_rate=self.initial_epsilon,
                questions_answered=0,
                onboarding_complete=0
            )
            self.db.add(cold_start)
            await self.db.commit()
            
            # Get first section of questions
            first_section = self.questionnaire["sections"][0]
            
            logger.info("onboarding_started", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "session_id": str(cold_start.id),
                "current_section": first_section,
                "progress": {
                    "current": 0,
                    "total": len(self.questionnaire["sections"])
                }
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("onboarding_start_failed", user_id=user_id, error=str(e))
            raise
    
    async def submit_answers(
        self,
        user_id: str,
        section_id: str,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit answers for a questionnaire section
        
        Args:
            user_id: User ID
            section_id: Section ID
            answers: User answers
            
        Returns:
            Next section or completion status
        """
        try:
            # Get cold start data
            result = await self.db.execute(
                select(UserColdStartData).where(
                    UserColdStartData.user_id == user_id
                )
            )
            cold_start = result.scalar_one_or_none()
            
            if not cold_start:
                return {"success": False, "error": "Onboarding not started"}
            
            # Store answers
            responses = cold_start.questionnaire_responses
            responses[section_id] = answers
            cold_start.questionnaire_responses = responses
            cold_start.questions_answered += len(answers)
            
            # Process answers based on section
            if section_id == "topics":
                await self._process_topic_answers(user_id, answers)
            elif section_id == "depth":
                await self._process_depth_answers(user_id, answers)
            elif section_id == "surprise":
                await self._process_surprise_answers(user_id, answers)
            elif section_id == "demographics":
                await self._process_demographic_answers(user_id, cold_start, answers)
            
            # Determine next section
            current_idx = next(
                (i for i, s in enumerate(self.questionnaire["sections"]) if s["id"] == section_id),
                -1
            )
            
            if current_idx < len(self.questionnaire["sections"]) - 1:
                # More sections
                next_section = self.questionnaire["sections"][current_idx + 1]
                
                await self.db.commit()
                
                return {
                    "success": True,
                    "completed": False,
                    "next_section": next_section,
                    "progress": {
                        "current": current_idx + 1,
                        "total": len(self.questionnaire["sections"])
                    }
                }
            else:
                # Onboarding complete
                cold_start.onboarding_complete = 1
                cold_start.completed_at = datetime.utcnow()
                
                # Apply demographic clustering if demographics provided
                if "demographics" in responses:
                    await self._apply_demographic_clustering(user_id, cold_start)
                
                await self.db.commit()
                
                logger.info("onboarding_completed", user_id=user_id)
                
                return {
                    "success": True,
                    "completed": True,
                    "message": "Onboarding complete!",
                    "exploration_strategy": await self._get_exploration_strategy(user_id)
                }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("answer_submission_failed", user_id=user_id, error=str(e))
            raise
    
    async def _process_topic_answers(
        self,
        user_id: str,
        answers: Dict[str, Any]
    ) -> None:
        """Process topic interest answers"""
        topic_interests = answers.get("topic_interests", {})
        
        # Convert to topic preferences
        topic_signals = {}
        for topic, intensity in topic_interests.items():
            # Normalize intensity (1-5 -> 0.2-1.0)
            normalized = intensity / 5.0
            
            # Add to all subcategories of this topic
            if topic in self.preference_model.TOPIC_CATEGORIES:
                for subcategory in self.preference_model.TOPIC_CATEGORIES[topic]:
                    key = f"{topic}.{subcategory}"
                    topic_signals[key] = normalized
        
        # Initialize topic preferences
        if topic_signals:
            await self.preference_model.update_topic_preferences(
                user_id,
                topic_signals,
                learning_rate=0.3  # Higher learning rate for cold start
            )
    
    async def _process_depth_answers(
        self,
        user_id: str,
        answers: Dict[str, Any]
    ) -> None:
        """Process depth preference answers"""
        depth_level = answers.get("depth_preference", 2)
        
        # Initialize depth preference
        await self.preference_model.update_depth_preference(
            user_id,
            depth_level,
            satisfaction_score=0.8  # Assume high satisfaction for explicit choice
        )
    
    async def _process_surprise_answers(
        self,
        user_id: str,
        answers: Dict[str, Any]
    ) -> None:
        """Process surprise tolerance answers"""
        # Calculate surprise tolerance from scenario choices
        scenario_choices = answers.get("scenario_choices", [])
        
        if scenario_choices:
            # Average surprise level from choices
            avg_surprise = sum(choice.get("surprise_level", 2) for choice in scenario_choices) / len(scenario_choices)
            surprise_level = int(round(avg_surprise))
        else:
            surprise_level = 2  # Default balanced
        
        # Initialize surprise preference
        await self.preference_model.update_surprise_preference(
            user_id,
            surprise_level,
            reward=0.8  # High reward for explicit choice
        )
    
    async def _process_demographic_answers(
        self,
        user_id: str,
        cold_start: UserColdStartData,
        answers: Dict[str, Any]
    ) -> None:
        """Process demographic answers"""
        cold_start.age_range = answers.get("age_range")
        cold_start.education_level = answers.get("education_level")
        cold_start.occupation = answers.get("occupation")
    
    async def _apply_demographic_clustering(
        self,
        user_id: str,
        cold_start: UserColdStartData
    ) -> None:
        """Apply demographic clustering to initialize preferences"""
        demographics = {
            "age_range": cold_start.age_range,
            "education_level": cold_start.education_level,
            "occupation": cold_start.occupation
        }
        
        # Assign to cluster
        cluster_id = await self.demographic_filter._assign_user_to_cluster(user_id)
        
        if cluster_id is not None:
            cold_start.cluster_id = cluster_id
            cold_start.cluster_confidence = 0.7  # Initial confidence
            
            logger.info("user_clustered",
                       user_id=user_id,
                       cluster_id=cluster_id)
    
    async def _get_exploration_strategy(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get exploration strategy for new user
        
        Args:
            user_id: User ID
            
        Returns:
            Exploration strategy
        """
        result = await self.db.execute(
            select(UserColdStartData).where(
                UserColdStartData.user_id == user_id
            )
        )
        cold_start = result.scalar_one_or_none()
        
        if not cold_start:
            return {}
        
        epsilon = float(cold_start.exploration_rate)
        
        return {
            "strategy": "epsilon_greedy",
            "epsilon": epsilon,
            "decay_rate": self.epsilon_decay,
            "min_epsilon": self.min_epsilon,
            "description": f"Will explore {int(epsilon * 100)}% of the time, exploit {int((1 - epsilon) * 100)}%"
        }
    
    async def get_exploration_recommendations(
        self,
        user_id: str,
        candidate_items: List[str],
        n_recommendations: int = 10
    ) -> List[str]:
        """
        Get recommendations with exploration strategy
        
        Args:
            user_id: User ID
            candidate_items: Candidate items
            n_recommendations: Number of recommendations
            
        Returns:
            List of item IDs with exploration
        """
        try:
            # Get cold start data
            result = await self.db.execute(
                select(UserColdStartData).where(
                    UserColdStartData.user_id == user_id
                )
            )
            cold_start = result.scalar_one_or_none()
            
            if not cold_start:
                # Random exploration for completely new users
                return list(np.random.choice(
                    candidate_items,
                    size=min(n_recommendations, len(candidate_items)),
                    replace=False
                ))
            
            epsilon = float(cold_start.exploration_rate)
            
            # Epsilon-greedy: explore with probability epsilon
            n_explore = int(n_recommendations * epsilon)
            n_exploit = n_recommendations - n_explore
            
            # Exploit: use best known items (would come from recommendation engine)
            # For cold start, use cluster-based or random
            exploit_items = list(np.random.choice(
                candidate_items,
                size=min(n_exploit, len(candidate_items)),
                replace=False
            ))
            
            # Explore: random diverse items
            remaining = [item for item in candidate_items if item not in exploit_items]
            explore_items = list(np.random.choice(
                remaining,
                size=min(n_explore, len(remaining)),
                replace=False
            ))
            
            # Combine and shuffle
            recommendations = exploit_items + explore_items
            np.random.shuffle(recommendations)
            
            # Decay epsilon
            new_epsilon = max(self.min_epsilon, epsilon * (1 - self.epsilon_decay))
            cold_start.exploration_rate = new_epsilon
            await self.db.commit()
            
            return recommendations[:n_recommendations]
            
        except Exception as e:
            logger.error("exploration_recommendations_failed",
                        user_id=user_id,
                        error=str(e))
            return []
    
    def get_questionnaire(self) -> Dict[str, Any]:
        """Get full questionnaire structure"""
        return self.questionnaire
    
    async def get_onboarding_status(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get onboarding status for user
        
        Args:
            user_id: User ID
            
        Returns:
            Onboarding status
        """
        try:
            result = await self.db.execute(
                select(UserColdStartData).where(
                    UserColdStartData.user_id == user_id
                )
            )
            cold_start = result.scalar_one_or_none()
            
            if not cold_start:
                return {
                    "started": False,
                    "completed": False
                }
            
            return {
                "started": True,
                "completed": bool(cold_start.onboarding_complete),
                "questions_answered": cold_start.questions_answered,
                "exploration_rate": float(cold_start.exploration_rate),
                "cluster_id": cold_start.cluster_id,
                "completed_at": cold_start.completed_at.isoformat() if cold_start.completed_at else None
            }
            
        except Exception as e:
            logger.error("get_onboarding_status_failed",
                        user_id=user_id,
                        error=str(e))
            return {"error": str(e)}


def get_cold_start_solver(db: AsyncSession) -> ColdStartSolver:
    """Get cold start solver instance"""
    return ColdStartSolver(db)
