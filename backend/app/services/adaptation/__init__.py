"""
Adaptation Services
Real-time preference adaptation and drift detection
"""
from app.services.adaptation.real_time_adapter import (
    RealTimeAdapter,
    get_real_time_adapter
)

__all__ = [
    "RealTimeAdapter",
    "get_real_time_adapter"
]
