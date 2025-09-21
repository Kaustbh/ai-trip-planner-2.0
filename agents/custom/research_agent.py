"""
Research Agent

Specialized agent for gathering information about destinations, activities, and travel requirements.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..base_agent import BaseAgent, AgentConfig, AgentRole, AgentCapabilities, AgentMessage


class ResearchAgent(BaseAgent):
    """
    Agent specialized in research and information gathering.
    
    Capabilities:
    - Research destinations and attractions
    - Gather weather and seasonal information
    - Find local events and activities
    - Research transportation options
    - Gather cultural and safety information
    - Find deals and discounts
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="Travel Researcher",
                role=AgentRole.RESEARCHER,
                capabilities=AgentCapabilities(
                    can_research=True,
                    can_learn=True,
                    max_concurrent_tasks=5
                ),
                model="gpt-4",
                temperature=0.3
            )
        super().__init__(config)
        
        # Research-specific attributes
        self.research_cache = {}
        self.data_sources = {}
        self.research_history = []
        self.knowledge_base = {}
    
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Process research requests."""
        try:
            self.status = AgentStatus.RUNNING
            
            if message.message_type == "research_destination":
                return await self._research_destination(message.content)
            elif message.message_type == "find_activities":
                return await self._find_activities(message.content)
            elif message.message_type == "research_weather":
                return await self._research_weather(message.content)
            elif message.message_type == "find_events":
                return await self._find_events(message.content)
            elif message.message_type == "research_transportation":
                return await self._research_transportation(message.content)
            elif message.message_type == "find_deals":
                return await self._find_deals(message.content)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}
                
        except Exception as e:
            await self.handle_error(e)
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research tasks."""
        task_type = task.get("type")
        
        if task_type == "comprehensive_research":
            return await self._comprehensive_research(task)
        elif task_type == "update_information":
            return await self._update_information(task)
        elif task_type == "validate_information":
            return await self._validate_information(task)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _research_destination(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Research comprehensive information about a destination."""
        destination = content.get("destination")
        research_depth = content.get("depth", "comprehensive")
        
        if not destination:
            return {"error": "Destination is required"}
        
        # Check cache first
        cache_key = f"destination_{destination}_{research_depth}"
        if cache_key in self.research_cache:
            cached_data = self.research_cache[cache_key]
            if self._is_cache_valid(cached_data):
                return {
                    "success": True,
                    "destination": destination,
                    "data": cached_data["data"],
                    "cached": True
                }
        
        # Perform research
        research_data = await self._gather_destination_data(destination, research_depth)
        
        # Cache the results
        self.research_cache[cache_key] = {
            "data": research_data,
            "timestamp": datetime.now(),
            "ttl": 3600  # 1 hour TTL
        }
        
        # Update knowledge base
        self.knowledge_base[destination] = research_data
        
        return {
            "success": True,
            "destination": destination,
            "data": research_data,
            "cached": False
        }
    
    async def _gather_destination_data(self, destination: str, depth: str) -> Dict[str, Any]:
        """Gather comprehensive data about a destination."""
        data = {
            "basic_info": await self._get_basic_info(destination),
            "attractions": await self._get_attractions(destination),
            "weather": await self._get_weather_info(destination),
            "culture": await self._get_cultural_info(destination),
            "transportation": await self._get_transportation_info(destination),
            "accommodation": await self._get_accommodation_info(destination),
            "safety": await self._get_safety_info(destination),
            "events": await self._get_local_events(destination),
            "dining": await self._get_dining_info(destination),
            "shopping": await self._get_shopping_info(destination)
        }
        
        if depth == "comprehensive":
            data.update({
                "history": await self._get_historical_info(destination),
                "language": await self._get_language_info(destination),
                "currency": await self._get_currency_info(destination),
                "visa_requirements": await self._get_visa_info(destination),
                "health_requirements": await self._get_health_info(destination)
            })
        
        return data
    
    async def _get_basic_info(self, destination: str) -> Dict[str, Any]:
        """Get basic information about the destination."""
        # Mock data - in reality would query external APIs
        await asyncio.sleep(0.1)
        
        return {
            "name": destination,
            "country": "Unknown",
            "region": "Unknown",
            "population": "Unknown",
            "timezone": "UTC",
            "coordinates": {"lat": 0, "lng": 0},
            "description": f"Beautiful destination with rich culture and history"
        }
    
    async def _get_attractions(self, destination: str) -> List[Dict[str, Any]]:
        """Get popular attractions for the destination."""
        await asyncio.sleep(0.2)
        
        return [
            {
                "name": "Main Attraction 1",
                "type": "landmark",
                "rating": 4.5,
                "description": "Famous landmark with historical significance",
                "price_range": "$10-20",
                "visit_duration": "2-3 hours"
            },
            {
                "name": "Cultural Museum",
                "type": "museum",
                "rating": 4.2,
                "description": "Local history and culture museum",
                "price_range": "$5-15",
                "visit_duration": "1-2 hours"
            }
        ]
    
    async def _get_weather_info(self, destination: str) -> Dict[str, Any]:
        """Get weather information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "current": {
                "temperature": 22,
                "condition": "sunny",
                "humidity": 65
            },
            "forecast": [
                {"date": "2024-01-15", "high": 25, "low": 18, "condition": "sunny"},
                {"date": "2024-01-16", "high": 23, "low": 16, "condition": "partly_cloudy"}
            ],
            "seasonal_info": {
                "best_time_to_visit": "Spring and Fall",
                "rainy_season": "Winter",
                "peak_tourist_season": "Summer"
            }
        }
    
    async def _get_cultural_info(self, destination: str) -> Dict[str, Any]:
        """Get cultural information about the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "languages": ["English", "Local Language"],
            "religions": ["Various"],
            "customs": ["Respect local traditions", "Dress modestly in religious sites"],
            "etiquette": ["Greet with handshake", "Remove shoes indoors"],
            "festivals": ["Annual Cultural Festival", "Spring Celebration"],
            "cuisine": ["Local specialties", "International options available"]
        }
    
    async def _get_transportation_info(self, destination: str) -> Dict[str, Any]:
        """Get transportation options for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "airports": [
                {
                    "name": "Main International Airport",
                    "code": "ABC",
                    "distance_from_city": "30 km",
                    "transport_to_city": ["taxi", "bus", "train"]
                }
            ],
            "public_transport": {
                "metro": "Available in city center",
                "bus": "Extensive network",
                "taxi": "Readily available",
                "ride_share": "Uber/Lyft available"
            },
            "car_rental": "Available at airport and city center",
            "walking": "City center is walkable"
        }
    
    async def _get_accommodation_info(self, destination: str) -> Dict[str, Any]:
        """Get accommodation information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "hotels": {
                "luxury": ["5-star hotels in city center"],
                "mid_range": ["3-4 star hotels throughout city"],
                "budget": ["Hostels and budget hotels available"]
            },
            "areas": {
                "city_center": "Most convenient, higher prices",
                "business_district": "Good for business travelers",
                "residential": "More local experience, lower prices"
            },
            "average_prices": {
                "luxury": "$200-500/night",
                "mid_range": "$80-200/night",
                "budget": "$30-80/night"
            }
        }
    
    async def _get_safety_info(self, destination: str) -> Dict[str, Any]:
        """Get safety information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "overall_safety": "Generally safe",
            "crime_rate": "Low to moderate",
            "areas_to_avoid": ["Certain neighborhoods at night"],
            "emergency_numbers": {
                "police": "911",
                "medical": "911",
                "fire": "911"
            },
            "travel_advisories": "Check government travel advisories",
            "health_risks": "Standard precautions recommended"
        }
    
    async def _get_local_events(self, destination: str) -> List[Dict[str, Any]]:
        """Get local events and activities."""
        await asyncio.sleep(0.1)
        
        return [
            {
                "name": "Cultural Festival",
                "date": "2024-02-15",
                "type": "festival",
                "description": "Annual cultural celebration",
                "price": "Free"
            },
            {
                "name": "Food Market",
                "date": "2024-01-20",
                "type": "market",
                "description": "Weekly local food market",
                "price": "Free entry"
            }
        ]
    
    async def _get_dining_info(self, destination: str) -> Dict[str, Any]:
        """Get dining information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "cuisine_types": ["Local", "International", "Fusion"],
            "price_ranges": {
                "budget": "$5-15 per meal",
                "mid_range": "$15-40 per meal",
                "fine_dining": "$40+ per meal"
            },
            "popular_dishes": ["Local specialty 1", "Local specialty 2"],
            "dining_times": {
                "breakfast": "7:00-10:00",
                "lunch": "12:00-14:00",
                "dinner": "18:00-22:00"
            }
        }
    
    async def _get_shopping_info(self, destination: str) -> Dict[str, Any]:
        """Get shopping information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "shopping_areas": ["City Center", "Market District"],
            "souvenirs": ["Local crafts", "Traditional items"],
            "markets": ["Local markets", "Flea markets"],
            "malls": ["Modern shopping centers"],
            "bargaining": "Common in markets"
        }
    
    async def _get_historical_info(self, destination: str) -> Dict[str, Any]:
        """Get historical information about the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "founded": "Unknown",
            "historical_periods": ["Ancient", "Medieval", "Modern"],
            "famous_events": ["Historical event 1", "Historical event 2"],
            "architectural_styles": ["Traditional", "Modern"],
            "historical_sites": ["Site 1", "Site 2"]
        }
    
    async def _get_language_info(self, destination: str) -> Dict[str, Any]:
        """Get language information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "primary_language": "Local Language",
            "secondary_languages": ["English", "Other"],
            "english_proficiency": "Moderate",
            "useful_phrases": ["Hello", "Thank you", "Where is...?"],
            "language_apps": ["Duolingo", "Google Translate"]
        }
    
    async def _get_currency_info(self, destination: str) -> Dict[str, Any]:
        """Get currency information for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "currency": "Local Currency",
            "exchange_rate": "1 USD = X Local Currency",
            "atms": "Widely available",
            "credit_cards": "Accepted in most places",
            "tipping": "10-15% in restaurants"
        }
    
    async def _get_visa_info(self, destination: str) -> Dict[str, Any]:
        """Get visa requirements for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "visa_required": "Check with embassy",
            "visa_types": ["Tourist", "Business"],
            "processing_time": "2-4 weeks",
            "cost": "Varies by nationality",
            "validity": "90 days"
        }
    
    async def _get_health_info(self, destination: str) -> Dict[str, Any]:
        """Get health requirements for the destination."""
        await asyncio.sleep(0.1)
        
        return {
            "vaccinations": "Check with doctor",
            "health_risks": "Standard precautions",
            "medical_facilities": "Available in major cities",
            "travel_insurance": "Recommended",
            "emergency_services": "Available"
        }
    
    async def _find_activities(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Find activities based on interests and preferences."""
        destination = content.get("destination")
        interests = content.get("interests", [])
        budget = content.get("budget", 100)
        duration = content.get("duration", 4)
        
        activities = await self._search_activities(destination, interests, budget, duration)
        
        return {
            "success": True,
            "destination": destination,
            "activities": activities,
            "total_found": len(activities)
        }
    
    async def _search_activities(self, destination: str, interests: List[str], 
                               budget: float, duration: int) -> List[Dict[str, Any]]:
        """Search for activities matching criteria."""
        await asyncio.sleep(0.2)
        
        # Mock activity search
        activities = []
        
        if "culture" in interests:
            activities.append({
                "name": "Museum Tour",
                "type": "cultural",
                "duration": "2-3 hours",
                "price": 25,
                "rating": 4.5,
                "description": "Guided tour of local museums"
            })
        
        if "adventure" in interests:
            activities.append({
                "name": "Hiking Adventure",
                "type": "adventure",
                "duration": "4-6 hours",
                "price": 50,
                "rating": 4.8,
                "description": "Scenic hiking trail with guide"
            })
        
        if "food" in interests:
            activities.append({
                "name": "Food Tour",
                "type": "culinary",
                "duration": "3-4 hours",
                "price": 75,
                "rating": 4.7,
                "description": "Local food and drink tasting tour"
            })
        
        # Filter by budget
        activities = [a for a in activities if a["price"] <= budget]
        
        return activities
    
    async def _research_weather(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Research weather information for a destination and dates."""
        destination = content.get("destination")
        dates = content.get("dates", [])
        
        weather_data = await self._get_weather_info(destination)
        
        return {
            "success": True,
            "destination": destination,
            "weather": weather_data
        }
    
    async def _find_events(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Find events happening during the trip dates."""
        destination = content.get("destination")
        dates = content.get("dates", [])
        
        events = await self._get_local_events(destination)
        
        return {
            "success": True,
            "destination": destination,
            "events": events
        }
    
    async def _research_transportation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Research transportation options between locations."""
        origin = content.get("origin")
        destination = content.get("destination")
        travel_date = content.get("travel_date")
        
        transport_options = await self._get_transportation_info(destination)
        
        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "transportation": transport_options
        }
    
    async def _find_deals(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Find deals and discounts for the destination."""
        destination = content.get("destination")
        category = content.get("category", "all")
        
        deals = await self._search_deals(destination, category)
        
        return {
            "success": True,
            "destination": destination,
            "deals": deals
        }
    
    async def _search_deals(self, destination: str, category: str) -> List[Dict[str, Any]]:
        """Search for deals and discounts."""
        await asyncio.sleep(0.1)
        
        # Mock deals search
        deals = [
            {
                "title": "Hotel Discount",
                "category": "accommodation",
                "discount": "20% off",
                "valid_until": "2024-02-28",
                "description": "Special promotion for selected hotels"
            },
            {
                "title": "Activity Package",
                "category": "activities",
                "discount": "15% off",
                "valid_until": "2024-03-15",
                "description": "Bundle deal for multiple activities"
            }
        ]
        
        if category != "all":
            deals = [d for d in deals if d["category"] == category]
        
        return deals
    
    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid."""
        if "timestamp" not in cached_data or "ttl" not in cached_data:
            return False
        
        age = (datetime.now() - cached_data["timestamp"]).total_seconds()
        return age < cached_data["ttl"]
    
    async def _comprehensive_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive research on a topic."""
        topic = task.get("topic")
        scope = task.get("scope", "full")
        
        # Mock comprehensive research
        return {
            "success": True,
            "topic": topic,
            "research_data": {},
            "sources": []
        }
    
    async def _update_information(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing information with new data."""
        return {"success": True, "updated": True}
    
    async def _validate_information(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate information accuracy."""
        return {"success": True, "valid": True, "confidence": 0.95}
