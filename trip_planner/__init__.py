"""
AI Trip Planner - Multi-Agent System
A comprehensive trip planning system using LangGraph with multiple specialized AI agents.
"""

__version__ = "1.0.0"
__author__ = "AI Trip Planner Team"

from .main import TripPlanner
from .agents import (
    DestinationResearchAgent,
    ImageRetrievalAgent,
    WeatherForecastAgent,
    ItineraryPlanningAgent,
    BudgetPlanningAgent
)
from .workflows import TripPlanningWorkflow
from .state import TripPlanningState

__all__ = [
    "TripPlanner",
    "DestinationResearchAgent",
    "ImageRetrievalAgent", 
    "WeatherForecastAgent",
    "ItineraryPlanningAgent",
    "BudgetPlanningAgent",
    "TripPlanningWorkflow",
    "TripPlanningState"
]
