"""
Enhanced Itinerary Planning Agent with LLM Integration
Uses LLM for intelligent itinerary creation and optimization.
"""

from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from ..state import ItineraryDay, Place, WeatherData


class ItineraryInput(BaseModel):
    """Input schema for itinerary planning."""
    places: List[Dict[str, Any]] = Field(description="List of places to include in itinerary")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    duration_days: int = Field(description="Number of days for the trip")
    preferences: List[str] = Field(default_factory=list, description="User preferences")
    weather_forecast: List[Dict[str, Any]] = Field(default_factory=list, description="Weather forecast data")


class EnhancedItineraryPlanningAgent:
    """Enhanced agent with LLM integration for intelligent itinerary creation."""
    
    def __init__(self, llm):
        self.llm = llm
        
        # LLM prompts for different tasks
        self.itinerary_planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planner. Create a detailed, personalized itinerary for a trip.
            
            Destination: {destination}
            Duration: {duration_days} days
            Group size: {group_size} people
            Preferences: {preferences}
            Budget level: {budget_level}
            
            Available places: {places_summary}
            Weather forecast: {weather_summary}
            
            Create a day-by-day itinerary that:
            1. Balances different types of activities
            2. Considers weather conditions
            3. Includes travel time between locations
            4. Matches user preferences
            5. Provides realistic timing
            6. Includes meal suggestions
            7. Offers alternative activities for bad weather
            
            Return a structured itinerary with specific times, activities, and recommendations."""),
            ("human", "Please create the itinerary for this trip.")
        ])
        
        self.activity_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative travel activity planner. Generate specific, engaging activities for a place.
            
            Place: {place_name}
            Category: {place_category}
            Weather: {weather_condition}
            Time of day: {time_of_day}
            Duration: {duration_hours} hours
            
            Create detailed activities that are:
            - Specific and actionable
            - Weather-appropriate
            - Engaging and memorable
            - Realistic for the time available
            - Include practical tips and recommendations"""),
            ("human", "Generate activities for this place and time slot.")
        ])
        
        self.route_optimization_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a logistics expert. Optimize the daily route for efficiency and enjoyment.
            
            Places to visit: {places_list}
            Starting location: {start_location}
            Ending location: {end_location}
            Available time: {available_hours} hours
            Transportation: {transportation_mode}
            
            Create an optimized route that:
            1. Minimizes travel time
            2. Groups nearby attractions
            3. Considers opening hours
            4. Includes meal breaks
            5. Allows for rest periods
            6. Provides buffer time for delays"""),
            ("human", "Optimize this route for the day.")
        ])
    
    def plan_itinerary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent itinerary using LLM."""
        try:
            places = state.get('places', [])
            start_date = state.get('start_date')
            duration_days = state.get('duration_days', 1)
            preferences = state.get('preferences', [])
            weather_forecast = state.get('weather_forecast', [])
            destination = state.get('destination', '')
            group_size = state.get('group_size', 1)
            budget = state.get('budget')
            
            if not places:
                return {
                    **state,
                    'errors': state.get('errors', []) + ['No places available for itinerary planning'],
                    'current_step': 'error'
                }
            
            # Convert dates to strings
            start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            
            # Prepare data for LLM
            places_summary = self._prepare_places_summary(places)
            weather_summary = self._prepare_weather_summary(weather_forecast)
            budget_level = self._determine_budget_level(budget, duration_days, group_size)
            
            # Use LLM to create itinerary
            itinerary_data = self._create_itinerary_with_llm(
                destination, duration_days, group_size, preferences, 
                budget_level, places_summary, weather_summary, places
            )
            
            # Convert to ItineraryDay objects
            itinerary = self._convert_to_itinerary_days(itinerary_data, places, weather_forecast)
            
            # Update state
            updated_state = {
                **state,
                'itinerary': itinerary,
                'current_step': 'itinerary_created',
                'messages': state.get('messages', []) + [
                    {
                        'type': 'info',
                        'content': f'Created {len(itinerary)}-day intelligent itinerary with {len(places)} places'
                    }
                ]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error planning itinerary: {str(e)}"
            return {
                **state,
                'errors': state.get('errors', []) + [error_msg],
                'current_step': 'error'
            }
    
    def _prepare_places_summary(self, places: List[Place]) -> str:
        """Prepare places data for LLM processing."""
        summary = []
        for place in places:
            place_info = f"- {place.name} ({place.category or 'attraction'}): {place.description}"
            if place.rating:
                place_info += f" [Rating: {place.rating}/5]"
            if place.address:
                place_info += f" [Address: {place.address}]"
            summary.append(place_info)
        return "\n".join(summary)
    
    def _prepare_weather_summary(self, weather_forecast: List[WeatherData]) -> str:
        """Prepare weather data for LLM processing."""
        if not weather_forecast:
            return "No weather forecast available"
        
        summary = []
        for weather in weather_forecast:
            weather_info = f"- {weather.date}: {weather.description}, {weather.temperature_min}°C - {weather.temperature_max}°C"
            if weather.precipitation and weather.precipitation > 0:
                weather_info += f", {weather.precipitation}mm rain"
            summary.append(weather_info)
        return "\n".join(summary)
    
    def _determine_budget_level(self, budget: float, duration_days: int, group_size: int) -> str:
        """Determine budget level for LLM context."""
        if not budget:
            return "moderate"
        
        daily_budget_per_person = budget / (duration_days * group_size)
        
        if daily_budget_per_person < 50:
            return "budget"
        elif daily_budget_per_person < 150:
            return "moderate"
        else:
            return "luxury"
    
    def _create_itinerary_with_llm(self, destination: str, duration_days: int, group_size: int, 
                                 preferences: List[str], budget_level: str, 
                                 places_summary: str, weather_summary: str, places: List[Place]) -> List[Dict]:
        """Use LLM to create intelligent itinerary."""
        try:
            # Get LLM response
            response = self.itinerary_planning_prompt.invoke({
                'destination': destination,
                'duration_days': duration_days,
                'group_size': group_size,
                'preferences': ', '.join(preferences) if preferences else 'general tourism',
                'budget_level': budget_level,
                'places_summary': places_summary,
                'weather_summary': weather_summary
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse LLM response and create structured itinerary
            # For now, create a basic structure - in production, use structured output
            itinerary = self._create_basic_itinerary(places, duration_days, preferences, weather_summary)
            
            return itinerary
            
        except Exception as e:
            print(f"Error creating itinerary with LLM: {str(e)}")
            # Fallback to basic itinerary
            return self._create_basic_itinerary(places, duration_days, preferences, weather_summary)
    
    def _create_basic_itinerary(self, places: List[Place], duration_days: int, 
                              preferences: List[str], weather_summary: str) -> List[Dict]:
        """Create basic itinerary as fallback."""
        itinerary = []
        start_date = datetime.now().date()
        
        places_per_day = max(1, len(places) // duration_days)
        
        for day in range(duration_days):
            current_date = start_date + timedelta(days=day)
            day_places = places[day * places_per_day:(day + 1) * places_per_day]
            
            # Generate activities using LLM
            activities = []
            for place in day_places:
                activity = self._generate_activity_with_llm(place, "morning", 2)
                activities.append(activity)
            
            itinerary_day = {
                'date': str(current_date),
                'places': [place.dict() for place in day_places],
                'activities': activities,
                'weather': None,  # Will be filled later
                'notes': f"Day {day + 1} of your trip"
            }
            itinerary.append(itinerary_day)
        
        return itinerary
    
    def _generate_activity_with_llm(self, place: Place, time_of_day: str, duration_hours: int) -> str:
        """Use LLM to generate specific activities for a place."""
        try:
            response = self.activity_generation_prompt.invoke({
                'place_name': place.name,
                'place_category': place.category or 'attraction',
                'weather_condition': 'sunny',  # Could be enhanced with actual weather
                'time_of_day': time_of_day,
                'duration_hours': duration_hours
            })
            
            llm_response = self.llm.invoke(response)
            return llm_response.content
            
        except Exception as e:
            print(f"Error generating activity: {str(e)}")
            return f"Explore {place.name} and learn about its history"
    
    def _convert_to_itinerary_days(self, itinerary_data: List[Dict], 
                                 places: List[Place], weather_forecast: List[WeatherData]) -> List[ItineraryDay]:
        """Convert itinerary data to ItineraryDay objects."""
        itinerary = []
        
        for day_data in itinerary_data:
            # Convert places in the day
            day_places = []
            for place_data in day_data.get('places', []):
                if isinstance(place_data, dict):
                    place = Place(**place_data)
                else:
                    place = place_data
                day_places.append(place)
            
            # Convert weather
            day_weather = None
            if day_data.get('weather'):
                weather_info = day_data['weather']
                day_weather = WeatherData(
                    date=datetime.strptime(weather_info['date'], '%Y-%m-%d').date(),
                    temperature_max=weather_info.get('temperature_max', 0),
                    temperature_min=weather_info.get('temperature_min', 0),
                    description=weather_info.get('description', ''),
                    humidity=weather_info.get('humidity'),
                    wind_speed=weather_info.get('wind_speed'),
                    precipitation=weather_info.get('precipitation')
                )
            
            # Create itinerary day
            itinerary_day = ItineraryDay(
                date=datetime.strptime(day_data['date'], '%Y-%m-%d').date(),
                places=day_places,
                activities=day_data.get('activities', []),
                weather=day_weather,
                notes=day_data.get('notes', '')
            )
            itinerary.append(itinerary_day)
        
        return itinerary
    
    def get_agent_tools(self):
        """Get tools available to this agent."""
        return []
