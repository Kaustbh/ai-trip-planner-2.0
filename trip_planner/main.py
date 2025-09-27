"""
Main Trip Planner Interface
Entry point for the AI Trip Planner system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

from .workflows import TripPlanningWorkflow
from .state import TripPlanningState


class TripPlanner:
    """Main interface for the AI Trip Planner system."""
    
    def __init__(self, 
                 llm_provider: str = "groq",
                 llm_model: str = "llama-3.1-8b-instant",
                 google_api_key: str = None):
        """
        Initialize the Trip Planner.
        
        Args:
            llm_provider: LLM provider to use ("groq" or "google")
            llm_model: Model name to use
            google_api_key: Google API key for Gemini models
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize workflow
        self.workflow = TripPlanningWorkflow(
            llm_provider=llm_provider,
            llm_model=llm_model,
            google_api_key=google_api_key
        )
    
    def plan_trip(self, 
                  destination: str,
                  start_date: str = None,
                  end_date: str = None,
                  duration_days: int = None,
                  budget: float = None,
                  preferences: List[str] = None,
                  group_size: int = 1) -> Dict[str, Any]:
        """
        Plan a complete trip.
        
        Args:
            destination: Destination to visit
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            duration_days: Number of days for the trip
            budget: Budget for the trip
            preferences: List of preferences (e.g., ["museums", "parks", "restaurants"])
            group_size: Number of people traveling
        
        Returns:
            Complete trip plan with places, itinerary, weather, and budget
        """
        if preferences is None:
            preferences = []
        
        # Validate inputs
        if not destination:
            raise ValueError("Destination is required")
        
        # Calculate duration if not provided
        if start_date and end_date and not duration_days:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            duration_days = (end - start).days + 1
        elif not duration_days:
            duration_days = 3  # Default to 3 days
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = start + timedelta(days=duration_days - 1)
            end_date = end.strftime('%Y-%m-%d')
        
        # Plan the trip
        result = self.workflow.plan_trip(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            # budget=budget,
            preferences=preferences,
            group_size=group_size
        )
        
        return result
    
    def stream_planning(self, 
                       destination: str,
                       start_date: str = None,
                       end_date: str = None,
                       duration_days: int = None,
                    #       budget: float = None,
                       preferences: List[str] = None,
                       group_size: int = 1):
        """
        Stream the trip planning process for real-time updates.
        
        Args:
            destination: Destination to visit
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            duration_days: Number of days for the trip
            budget: Budget for the trip
            preferences: List of preferences
            group_size: Number of people traveling
        
        Yields:
            State updates during planning
        """
        if preferences is None:
            preferences = []
        
        # Validate inputs
        if not destination:
            raise ValueError("Destination is required")
        
        # Calculate duration if not provided
        if start_date and end_date and not duration_days:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            duration_days = (end - start).days + 1
        elif not duration_days:
            duration_days = 3  # Default to 3 days
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = start + timedelta(days=duration_days - 1)
            end_date = end.strftime('%Y-%m-%d')
        
        # Stream the planning process
        for event in self.workflow.stream_planning(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            # budget=budget,
            preferences=preferences,
            group_size=group_size
        ):
            yield event
    
    def get_workflow_graph(self):
        """Get the workflow graph for visualization."""
        return self.workflow.get_workflow_graph()
    
    def print_trip_summary(self, trip_plan: Dict[str, Any]):
        """Print a formatted summary of the trip plan."""
        print("=" * 60)
        print("🗺️  AI TRIP PLANNER - TRIP SUMMARY")
        print("=" * 60)
        
        # Basic info
        print(f"📍 Destination: {trip_plan.get('destination', 'N/A')}")
        print(f"📅 Duration: {trip_plan.get('duration_days', 'N/A')} days")
        print(f"👥 Group Size: {trip_plan.get('group_size', 'N/A')} people")
        
        # Places
        places = trip_plan.get('places', [])
        if places:
            print(f"\n🏛️  Places Found ({len(places)}):")
            for i, place in enumerate(places[:5], 1):  # Show top 5
                name = place.name if hasattr(place, 'name') else place.get('name', 'Unknown')
                print(f"  {i}. {name}")
            if len(places) > 5:
                print(f"  ... and {len(places) - 5} more")
        
        # Itinerary
        itinerary = trip_plan.get('itinerary', [])
        if itinerary:
            print(f"\n📋 Itinerary ({len(itinerary)} days):")
            for day in itinerary:
                date_str = day.date if hasattr(day, 'date') else day.get('date', 'Unknown')
                places_count = len(day.places) if hasattr(day, 'places') else len(day.get('places', []))
                print(f"  Day {date_str}: {places_count} places planned")
        
        # Budget
        # budget = trip_plan.get('budget_breakdown')
        # if budget:
        #     print(f"\n💰 Budget Estimate:")
        #     print(f"  Total: ${budget.get('total_estimated', 0):,.2f}")
        #     print(f"  Per Day: ${budget.get('daily_average', 0):,.2f}")
        #     print(f"  Per Person: ${budget.get('per_person', 0):,.2f}")
        
        # Weather
        weather = trip_plan.get('weather_forecast', [])
        if weather:
            print(f"\n🌤️  Weather Forecast ({len(weather)} days):")
            for day_weather in weather[:3]:  # Show first 3 days
                date_str = day_weather.date if hasattr(day_weather, 'date') else day_weather.get('date', 'Unknown')
                desc = day_weather.description if hasattr(day_weather, 'description') else day_weather.get('description', 'Unknown')
                temp_max = day_weather.temperature_max if hasattr(day_weather, 'temperature_max') else day_weather.get('temperature_max', 'N/A')
                print(f"  {date_str}: {desc}, Max: {temp_max}°C")
        
        # Recommendations
        recommendations = trip_plan.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:5]:  # Show top 5
                print(f"  • {rec}")
        
        # Errors
        errors = trip_plan.get('errors', [])
        if errors:
            print(f"\n❌ Errors:")
            for error in errors:
                print(f"  • {error}")
        
        print("=" * 60)
