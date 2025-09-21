"""
Itinerary Planning Agent with LLM Integration
Creates intelligent, personalized itineraries using AI-powered planning and optimization.
"""

from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from ..state import ItineraryDay, Place, WeatherData


class ItineraryInput(BaseModel):
    """Input schema for itinerary planning."""
    places: List[Dict[str, Any]] = Field(description="List of places to include in itinerary")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    duration_days: int = Field(description="Number of days for the trip")
    preferences: List[str] = Field(default_factory=list, description="User preferences")
    weather_forecast: List[Dict[str, Any]] = Field(default_factory=list, description="Weather forecast data")


@tool(args_schema=ItineraryInput)
def create_itinerary(places: List[Dict[str, Any]], start_date: str, duration_days: int, 
                    preferences: List[str] = None, weather_forecast: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Create a detailed itinerary for the trip.
    
    Args:
        places: List of places to include in itinerary
        start_date: Start date in YYYY-MM-DD format
        duration_days: Number of days for the trip
        preferences: User preferences
        weather_forecast: Weather forecast data
    
    Returns:
        List of itinerary days
    """
    if preferences is None:
        preferences = []
    if weather_forecast is None:
        weather_forecast = []
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        itinerary = []
        
        # Group places by category for better distribution
        places_by_category = {}
        for place in places:
            category = place.get('category', 'general')
            if category not in places_by_category:
                places_by_category[category] = []
            places_by_category[category].append(place)
        
        # Distribute places across days
        places_per_day = max(1, len(places) // duration_days)
        remaining_places = places.copy()
        
        for day in range(duration_days):
            current_date = start_date_obj + timedelta(days=day)
            
            # Select places for this day
            day_places = []
            if remaining_places:
                # Take places based on preferences first
                preferred_places = []
                other_places = []
                
                for place in remaining_places:
                    place_category = place.get('category', '').lower()
                    place_name = place.get('name', '').lower()
                    
                    is_preferred = any(pref.lower() in place_category or pref.lower() in place_name 
                                     for pref in preferences)
                    
                    if is_preferred:
                        preferred_places.append(place)
                    else:
                        other_places.append(place)
                
                # Select places for this day
                day_places = preferred_places[:places_per_day] + other_places[:places_per_day - len(preferred_places[:places_per_day])]
                day_places = day_places[:places_per_day]  # Limit to places_per_day
                
                # Remove selected places from remaining
                for place in day_places:
                    if place in remaining_places:
                        remaining_places.remove(place)
            
            # Get weather for this day
            day_weather = None
            for weather in weather_forecast:
                if weather.get('date') == str(current_date):
                    day_weather = weather
                    break
            
            # Create activities based on places
            activities = []
            for place in day_places:
                place_name = place.get('name', '')
                place_category = place.get('category', '')
                
                if 'museum' in place_category.lower():
                    activities.append(f"Visit {place_name} and explore the exhibits")
                elif 'park' in place_category.lower() or 'garden' in place_category.lower():
                    activities.append(f"Stroll through {place_name} and enjoy nature")
                elif 'restaurant' in place_category.lower() or 'food' in place_category.lower():
                    activities.append(f"Dine at {place_name} and try local cuisine")
                else:
                    activities.append(f"Explore {place_name} and learn about its history")
            
            # Add general activities
            if day_weather:
                weather_desc = day_weather.get('description', '').lower()
                if 'rain' in weather_desc or 'storm' in weather_desc:
                    activities.append("Consider indoor activities due to weather")
                elif 'sunny' in weather_desc or 'clear' in weather_desc:
                    activities.append("Perfect weather for outdoor exploration")
            
            # Create itinerary day
            itinerary_day = {
                'date': str(current_date),
                'places': day_places,
                'activities': activities,
                'weather': day_weather,
                'notes': f"Day {day + 1} of your trip to {places[0].get('name', 'destination') if places else 'destination'}"
            }
            
            itinerary.append(itinerary_day)
        
        return itinerary
        
    except Exception as e:
        print(f"Error creating itinerary: {str(e)}")
        return []


class ItineraryOutput(BaseModel):
    """Output schema for LLM itinerary generation."""
    daily_itinerary: List[Dict[str, Any]] = Field(description="Day-by-day itinerary")
    total_estimated_cost: float = Field(description="Total estimated cost")
    recommendations: List[str] = Field(description="General recommendations")
    packing_tips: List[str] = Field(description="Packing recommendations")


class ActivityOutput(BaseModel):
    """Output schema for LLM activity generation."""
    activity_name: str = Field(description="Name of the activity")
    description: str = Field(description="Detailed activity description")
    duration_hours: float = Field(description="Duration in hours")
    best_time: str = Field(description="Best time of day for this activity")
    tips: List[str] = Field(description="Activity-specific tips")


class ItineraryPlanningAgent:
    """Agent responsible for creating intelligent, personalized itineraries with LLM integration."""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = [create_itinerary]
        
        # LLM prompts for different tasks
        self.itinerary_planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planner and local guide with deep knowledge of destinations worldwide.
            
            Create a detailed, personalized itinerary that considers:
            - User preferences and interests
            - Weather conditions and seasonal factors
            - Travel logistics and timing
            - Cultural and historical context
            - Budget considerations
            - Group size and dynamics
            
            Destination: {destination}
            Duration: {duration_days} days
            Group size: {group_size} people
            Preferences: {preferences}
            Budget level: {budget_level}
            
            Available places: {places_summary}
            Weather forecast: {weather_summary}
            
            Create a day-by-day itinerary that:
            1. Balances different types of activities (cultural, recreational, dining, relaxation)
            2. Considers weather conditions and provides alternatives
            3. Includes realistic travel times between locations
            4. Matches user preferences and interests
            5. Provides specific timing and duration for each activity
            6. Includes meal suggestions and dining recommendations
            7. Offers weather-appropriate alternatives
            8. Considers local customs and best practices
            9. Includes practical tips and recommendations
            10. Provides packing suggestions based on activities and weather
            
            Make the itinerary engaging, practical, and memorable."""),
            ("human", "Please create a comprehensive itinerary for this trip.")
        ])
        
        self.activity_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative travel activity planner and local expert.
            
            Generate specific, engaging activities for a place considering:
            - The place's unique characteristics and history
            - Weather conditions and time of day
            - Available time and group dynamics
            - Local customs and best practices
            - Safety and practical considerations
            
            Place: {place_name}
            Category: {place_category}
            Weather: {weather_condition}
            Time of day: {time_of_day}
            Duration: {duration_hours} hours
            Group size: {group_size} people
            
            Create activities that are:
            - Specific and actionable
            - Weather-appropriate
            - Engaging and memorable
            - Realistic for the time available
            - Include practical tips and recommendations
            - Consider local context and culture"""),
            ("human", "Generate detailed activities for this place and time slot.")
        ])
        
        self.route_optimization_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a logistics expert and local transportation specialist.
            
            Optimize the daily route for maximum efficiency and enjoyment considering:
            - Geographic proximity and travel times
            - Opening hours and availability
            - Traffic patterns and peak times
            - Transportation options and costs
            - Weather conditions
            - Group preferences and mobility
            
            Places to visit: {places_list}
            Starting location: {start_location}
            Ending location: {end_location}
            Available time: {available_hours} hours
            Transportation: {transportation_mode}
            Weather: {weather_condition}
            
            Create an optimized route that:
            1. Minimizes travel time and costs
            2. Groups nearby attractions logically
            3. Considers opening hours and availability
            4. Includes appropriate meal and rest breaks
            5. Allows buffer time for delays and exploration
            6. Provides alternative options for bad weather
            7. Considers group dynamics and preferences"""),
            ("human", "Optimize this route for maximum efficiency and enjoyment.")
        ])
        
        # Output parsers
        self.itinerary_parser = PydanticOutputParser(pydantic_object=ItineraryOutput)
        self.activity_parser = PydanticOutputParser(pydantic_object=ActivityOutput)
    
    def plan_itinerary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an intelligent, personalized itinerary using LLM.
        
        Args:
            state: Current trip planning state
            
        Returns:
            Updated state with AI-generated itinerary
        """
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
            
            # Prepare data for LLM
            places_summary = self._prepare_places_summary(places)
            weather_summary = self._prepare_weather_summary(weather_forecast)
            budget_level = self._determine_budget_level(budget, duration_days, group_size)
            
            # Use LLM to create intelligent itinerary
            itinerary_data = self._create_itinerary_with_llm(
                destination, duration_days, group_size, preferences, 
                budget_level, places_summary, weather_summary, places, start_date
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
                        'content': f'Created {len(itinerary)}-day AI-powered itinerary with {len(places)} places'
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
            if hasattr(place, 'highlights') and place.highlights:
                place_info += f" [Highlights: {', '.join(place.highlights)}]"
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
            if weather.humidity:
                weather_info += f", Humidity: {weather.humidity}%"
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
                                 places_summary: str, weather_summary: str, places: List[Place], start_date) -> List[Dict]:
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
            
            # Parse structured output
            try:
                parsed_output = self.itinerary_parser.parse(llm_response.content)
                return parsed_output.daily_itinerary
            except Exception as parse_error:
                print(f"Error parsing LLM itinerary response: {parse_error}")
                # Fallback to basic itinerary
                return self._create_basic_itinerary(places, duration_days, preferences, weather_summary, start_date)
            
        except Exception as e:
            print(f"Error creating itinerary with LLM: {str(e)}")
            # Fallback to basic itinerary
            return self._create_basic_itinerary(places, duration_days, preferences, weather_summary, start_date)
    
    def _create_basic_itinerary(self, places: List[Place], duration_days: int, 
                              preferences: List[str], weather_summary: str, start_date) -> List[Dict]:
        """Create basic itinerary as fallback."""
        itinerary = []
        
        if hasattr(start_date, 'strftime'):
            start_date_obj = start_date
        else:
            start_date_obj = datetime.now().date()
        
        places_per_day = max(1, len(places) // duration_days)
        
        for day in range(duration_days):
            current_date = start_date_obj + timedelta(days=day)
            day_places = places[day * places_per_day:(day + 1) * places_per_day]
            
            # Generate activities using LLM
            activities = []
            for i, place in enumerate(day_places):
                time_of_day = "morning" if i < len(day_places) // 2 else "afternoon"
                activity = self._generate_activity_with_llm(place, time_of_day, 2, 1)
                activities.append(activity)
            
            itinerary_day = {
                'date': str(current_date),
                'places': [place.dict() if hasattr(place, 'dict') else place for place in day_places],
                'activities': activities,
                'weather': None,  # Will be filled later
                'notes': f"Day {day + 1} of your trip to {places[0].name if places else 'destination'}"
            }
            itinerary.append(itinerary_day)
        
        return itinerary
    
    def _generate_activity_with_llm(self, place: Place, time_of_day: str, duration_hours: int, group_size: int) -> str:
        """Use LLM to generate specific activities for a place."""
        try:
            response = self.activity_generation_prompt.invoke({
                'place_name': place.name,
                'place_category': place.category or 'attraction',
                'weather_condition': 'sunny',  # Could be enhanced with actual weather
                'time_of_day': time_of_day,
                'duration_hours': duration_hours,
                'group_size': group_size
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse structured output
            try:
                parsed_output = self.activity_parser.parse(llm_response.content)
                return f"{parsed_output.activity_name}: {parsed_output.description}"
            except Exception as parse_error:
                print(f"Error parsing activity response: {parse_error}")
                return f"Explore {place.name} and learn about its history"
            
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
        return self.tools
