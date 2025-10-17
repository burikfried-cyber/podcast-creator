"""
User Preference Services
Multi-dimensional preference modeling and behavioral learning
"""
from app.services.preferences.user_preference_model import (
    UserPreferenceModel,
    get_preference_model
)

__all__ = [
    "UserPreferenceModel",
    "get_preference_model"
]
