"""
Cold Start Services
Solutions for new user onboarding and exploration
"""
from app.services.cold_start.cold_start_solver import (
    ColdStartSolver,
    get_cold_start_solver
)

__all__ = [
    "ColdStartSolver",
    "get_cold_start_solver"
]
