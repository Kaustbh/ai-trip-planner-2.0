"""
Weather Forecast Agent with LLM Integration
Fetches weather data and provides intelligent weather-based recommendations using AI.
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from ..state import WeatherData


class WeatherForecastInput(BaseModel):
    """Input schema for weather forecast."""
    location: str = Field(description="Location to get weather for")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")


@tool(args_schema=WeatherForecastInput)
def get_weather_forecast(location: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get weather forecast for a location using Open-Meteo API.
    
    Args:
        location: Location to get weather for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        List of weather data for each day
    """
    try:
        # First, get coordinates for the location
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocoding_params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        geocoding_response = requests.get(geocoding_url, params=geocoding_params)
        geocoding_response.raise_for_status()
        geocoding_data = geocoding_response.json()
        
        if not geocoding_data.get("results"):
            return []
        
        result = geocoding_data["results"][0]
        latitude = result["latitude"]
        longitude = result["longitude"]
        
        # Get weather forecast
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min", 
                "weather_code",
                "precipitation_sum",
                "wind_speed_10m_max",
                "relative_humidity_2m_max"
            ],
            "timezone": "auto"
        }
        
        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # Process weather data
        daily_data = weather_data.get("daily", {})
        dates = daily_data.get("time", [])
        weather_forecast = []
        
        for i, date_str in enumerate(dates):
            weather_code = daily_data.get("weather_code", [])[i]
            description = get_weather_description(weather_code)
            
            weather_day = {
                "date": date_str,
                "temperature_max": daily_data.get("temperature_2m_max", [])[i],
                "temperature_min": daily_data.get("temperature_2m_min", [])[i],
                "description": description,
                "humidity": daily_data.get("relative_humidity_2m_max", [])[i],
                "wind_speed": daily_data.get("wind_speed_10m_max", [])[i],
                "precipitation": daily_data.get("precipitation_sum", [])[i]
            }
            weather_forecast.append(weather_day)
        
        return weather_forecast
        
    except Exception as e:
        print(f"Error getting weather forecast: {str(e)}")
        return []


def get_weather_description(weather_code: int) -> str:
    """Convert weather code to description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy", 
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(weather_code, "Unknown")


class WeatherAnalysisOutput(BaseModel):
    """Output schema for LLM weather analysis."""
    activity_recommendations: Dict[str, List[str]] = Field(description="Weather-appropriate activities for each day")
    packing_suggestions: List[str] = Field(description="Packing recommendations based on weather")
    alternative_plans: Dict[str, List[str]] = Field(description="Alternative indoor activities for bad weather")
    weather_insights: List[str] = Field(description="Weather insights and patterns")
    safety_tips: List[str] = Field(description="Weather-related safety recommendations")


class WeatherForecastAgent:
    """Agent responsible for fetching weather forecasts and providing AI-powered weather insights."""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = [get_weather_forecast]
        
        # LLM prompts for different tasks
        self.weather_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a weather expert and travel advisor specializing in weather-based trip planning.
            
            Analyze the weather forecast and provide comprehensive recommendations:
            
            Destination: {destination}
            Weather forecast: {weather_data}
            Trip duration: {duration_days} days
            User preferences: {preferences}
            
            Provide detailed analysis including:
            1. Weather-appropriate activities for each day
            2. Specific packing recommendations based on weather conditions
            3. Alternative indoor activities for bad weather days
            4. Weather patterns and insights for the destination
            5. Safety tips and weather-related precautions
            6. Best times of day for outdoor activities
            7. Clothing and gear recommendations
            8. Weather-dependent itinerary adjustments
            
            Make your recommendations practical, specific, and tailored to the destination and user preferences."""),
            ("human", "Please provide comprehensive weather-based recommendations for this trip.")
        ])
        
        self.packing_recommendation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel packing expert and weather specialist.
            
            Create detailed packing recommendations based on:
            - Weather forecast for each day
            - Destination climate and seasonal patterns
            - Trip duration and activities planned
            - User preferences and travel style
            
            Weather forecast: {weather_data}
            Destination: {destination}
            Duration: {duration_days} days
            Activities: {activities}
            
            Provide specific recommendations for:
            1. Essential clothing items
            2. Weather-specific gear (umbrella, sunscreen, etc.)
            3. Footwear recommendations
            4. Accessories and extras
            5. Items to avoid bringing
            6. Packing tips and organization
            
            Make recommendations practical and space-efficient."""),
            ("human", "What should I pack for this trip based on the weather?")
        ])
        
        # Output parser
        self.weather_parser = PydanticOutputParser(pydantic_object=WeatherAnalysisOutput)
    
    def get_weather_forecast(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get weather forecast and provide AI-powered weather insights.
        
        Args:
            state: Current trip planning state
            
        Returns:
            Updated state with weather forecast and AI insights
        """
        try:
            destination = state.get('destination', '')
            start_date = state.get('start_date')
            end_date = state.get('end_date')
            duration_days = state.get('duration_days', 1)
            preferences = state.get('preferences', [])
            
            if not destination:
                return {
                    **state,
                    'errors': state.get('errors', []) + ['No destination provided for weather forecast'],
                    'current_step': 'error'
                }
            
            if not start_date or not end_date:
                return {
                    **state,
                    'messages': state.get('messages', []) + [
                        {
                            'type': 'warning',
                            'content': 'No dates provided, skipping weather forecast'
                        }
                    ]
                }
            
            # Convert dates to string format
            start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            end_date_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
            
            # Step 1: Get weather forecast
            weather_data = get_weather_forecast.invoke({
                'location': destination,
                'start_date': start_date_str,
                'end_date': end_date_str
            })
            
            # Convert to WeatherData objects
            weather_forecast = []
            for day_data in weather_data:
                weather_day = WeatherData(
                    date=datetime.strptime(day_data['date'], '%Y-%m-%d').date(),
                    temperature_max=day_data['temperature_max'],
                    temperature_min=day_data['temperature_min'],
                    description=day_data['description'],
                    humidity=day_data.get('humidity'),
                    wind_speed=day_data.get('wind_speed'),
                    precipitation=day_data.get('precipitation')
                )
                weather_forecast.append(weather_day)
            
            # Step 2: Use LLM to analyze weather and provide recommendations
            weather_insights = self._analyze_weather_with_llm(
                destination, weather_forecast, duration_days, preferences
            )
            
            # Step 3: Get packing recommendations
            packing_tips = self._get_packing_recommendations(
                destination, weather_forecast, duration_days, state.get('places', [])
            )
            
            # Update state
            updated_state = {
                **state,
                'weather_forecast': weather_forecast,
                'weather_insights': weather_insights,
                'packing_recommendations': packing_tips,
                'current_step': 'weather_forecasted',
                'messages': state.get('messages', []) + [
                    {
                        'type': 'info',
                        'content': f'Retrieved AI-enhanced weather forecast for {len(weather_forecast)} days'
                    }
                ]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error getting weather forecast: {str(e)}"
            return {
                **state,
                'errors': state.get('errors', []) + [error_msg],
                'current_step': 'error'
            }
    
    def _analyze_weather_with_llm(self, destination: str, weather_forecast: List[WeatherData], 
                                 duration_days: int, preferences: List[str]) -> Dict[str, Any]:
        """Use LLM to analyze weather and provide intelligent recommendations."""
        try:
            # Prepare weather data for LLM
            weather_summary = self._prepare_weather_summary_for_llm(weather_forecast)
            
            # Get LLM response
            response = self.weather_analysis_prompt.invoke({
                'destination': destination,
                'weather_data': weather_summary,
                'duration_days': duration_days,
                'preferences': ', '.join(preferences) if preferences else 'general tourism'
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse structured output
            try:
                parsed_output = self.weather_parser.parse(llm_response.content)
                return {
                    'activity_recommendations': parsed_output.activity_recommendations,
                    'packing_suggestions': parsed_output.packing_suggestions,
                    'alternative_plans': parsed_output.alternative_plans,
                    'weather_insights': parsed_output.weather_insights,
                    'safety_tips': parsed_output.safety_tips
                }
            except Exception as parse_error:
                print(f"Error parsing weather analysis: {parse_error}")
                # Fallback to basic analysis
                return self._create_basic_weather_analysis(weather_forecast, destination)
            
        except Exception as e:
            print(f"Error analyzing weather with LLM: {str(e)}")
            return self._create_basic_weather_analysis(weather_forecast, destination)
    
    def _get_packing_recommendations(self, destination: str, weather_forecast: List[WeatherData], 
                                   duration_days: int, places: List) -> List[str]:
        """Get packing recommendations from LLM."""
        try:
            weather_summary = self._prepare_weather_summary_for_llm(weather_forecast)
            activities = [place.name for place in places[:5]] if places else []
            
            response = self.packing_recommendation_prompt.invoke({
                'weather_data': weather_summary,
                'destination': destination,
                'duration_days': duration_days,
                'activities': ', '.join(activities)
            })
            
            llm_response = self.llm.invoke(response)
            
            # Extract packing tips from response
            tips = []
            content = llm_response.content
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    tip = line.lstrip('-•* ').strip()
                    if tip:
                        tips.append(tip)
            
            return tips[:15]  # Limit to top 15 tips
            
        except Exception as e:
            print(f"Error getting packing recommendations: {str(e)}")
            return ["Pack layers for varying temperatures", "Bring an umbrella for potential rain"]
    
    def _prepare_weather_summary_for_llm(self, weather_forecast: List[WeatherData]) -> str:
        """Prepare weather data for LLM processing."""
        summary = []
        for weather in weather_forecast:
            weather_info = f"Day {weather.date}: {weather.description}, {weather.temperature_min}°C - {weather.temperature_max}°C"
            if weather.precipitation and weather.precipitation > 0:
                weather_info += f", {weather.precipitation}mm rain"
            if weather.humidity:
                weather_info += f", Humidity: {weather.humidity}%"
            if weather.wind_speed:
                weather_info += f", Wind: {weather.wind_speed} km/h"
            summary.append(weather_info)
        return "\n".join(summary)
    
    def _create_basic_weather_analysis(self, weather_forecast: List[WeatherData], destination: str) -> Dict[str, Any]:
        """Create basic weather analysis as fallback."""
        return {
            'activity_recommendations': {
                'sunny': ['Outdoor sightseeing', 'Walking tours', 'Photography'],
                'rainy': ['Museums', 'Indoor attractions', 'Shopping'],
                'cold': ['Warm indoor activities', 'Hot drinks at cafes']
            },
            'packing_suggestions': [
                'Check weather forecast before packing',
                'Pack layers for temperature changes',
                'Bring weather-appropriate footwear'
            ],
            'alternative_plans': {
                'rainy': ['Visit museums', 'Go shopping', 'Try local cafes'],
                'hot': ['Early morning activities', 'Indoor attractions', 'Evening walks']
            },
            'weather_insights': [
                f'Weather patterns for {destination}',
                'Check local weather updates daily'
            ],
            'safety_tips': [
                'Stay hydrated in hot weather',
                'Seek shelter during storms',
                'Dress appropriately for conditions'
            ]
        }
    
    def get_agent_tools(self):
        """Get tools available to this agent."""
        return self.tools
