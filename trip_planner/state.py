"""
Trip Planning State Management
Defines the state structure for the multi-agent trip planning system.
"""

from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime, date as Date
from pydantic import BaseModel, Field


class Place(BaseModel):
    """Represents a tourist place with its details."""
    name: str = Field(description="Name of the place")
    description: str = Field(description="Description of the place")
    rating: Optional[float] = Field(default=None, description="Rating of the place")
    address: Optional[str] = Field(default=None, description="Address of the place")
    category: Optional[str] = Field(default=None, description="Category of the place")
    image_url: Optional[str] = Field(default=None, description="URL of the place image")
    coordinates: Optional[Dict[str, float]] = Field(default=None, description="Latitude and longitude")
    
    # AI-enhanced fields
    highlights: Optional[List[str]] = Field(default=None, description="Key highlights of the place")
    best_time_to_visit: Optional[str] = Field(default=None, description="Best time to visit")
    tips: Optional[List[str]] = Field(default=None, description="Visiting tips")
    visual_highlights: Optional[List[str]] = Field(default=None, description="Visual highlights for photography")
    photography_tips: Optional[List[str]] = Field(default=None, description="Photography tips")
    best_angles: Optional[List[str]] = Field(default=None, description="Best photography angles")
    image_caption: Optional[str] = Field(default=None, description="AI-generated image caption")


class WeatherData(BaseModel):
    """Represents weather information for a specific date."""
    date: Date = Field(description="Date of the weather forecast")
    temperature_max: float = Field(description="Maximum temperature in Celsius")
    temperature_min: float = Field(description="Minimum temperature in Celsius")
    description: str = Field(description="Weather description")
    humidity: Optional[float] = Field(default=None, description="Humidity percentage")
    wind_speed: Optional[float] = Field(default=None, description="Wind speed in km/h")
    precipitation: Optional[float] = Field(default=None, description="Precipitation in mm")


class ItineraryDay(BaseModel):
    """Represents a single day in the itinerary."""
    date: Date = Field(description="Date of the itinerary day")
    places: List[Place] = Field(description="Places to visit on this day")
    activities: List[str] = Field(description="Activities planned for this day")
    weather: Optional[WeatherData] = Field(default=None, description="Weather forecast for this day")
    notes: Optional[str] = Field(default=None, description="Additional notes for this day")


class TripPlanningState(TypedDict, total=False):
    """Main state for the trip planning workflow."""
    # User inputs
    destination: str
    start_date: Optional[Date]
    end_date: Optional[Date]
    duration_days: Optional[int]
    # budget: Optional[float]
    preferences: List[str]
    group_size: Optional[int]
    
    # Research data
    places: List[Place]
    place_images: Dict[str, str]
    weather_forecast: List[WeatherData]
    
    # Planning results
    itinerary: List[ItineraryDay]
    # budget_breakdown: Optional[Dict[str, float]]
    recommendations: List[str]
    
    # System state
    current_step: str
    errors: List[str]
    messages: List[Dict[str, Any]]
