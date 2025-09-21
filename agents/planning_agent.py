"""
Planning Agent

Responsible for creating initial trip plans and itineraries based on user preferences.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentCapabilities, AgentMessage


class PlanningAgent(BaseAgent):
    """
    Agent responsible for trip planning and itinerary creation.
    
    Capabilities:
    - Analyze user preferences and constraints
    - Create detailed trip itineraries
    - Optimize routes and schedules
    - Suggest activities and attractions
    - Handle date and time planning
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="Trip Planner",
                role=AgentRole.PLANNER,
                capabilities=AgentCapabilities(
                    can_plan=True,
                    can_research=True,
                    max_concurrent_tasks=3
                ),
                model="gpt-4",
                temperature=0.7
            )
        super().__init__(config)
        
        # Planning-specific attributes
        self.trip_templates = self._load_trip_templates()
        self.destination_knowledge = {}
        self.planning_constraints = {}
    
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Process incoming planning requests."""
        try:
            self.status = AgentStatus.RUNNING
            
            if message.message_type == "plan_trip":
                return await self._create_trip_plan(message.content)
            elif message.message_type == "optimize_itinerary":
                return await self._optimize_itinerary(message.content)
            elif message.message_type == "suggest_activities":
                return await self._suggest_activities(message.content)
            elif message.message_type == "update_plan":
                return await self._update_plan(message.content)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}
                
        except Exception as e:
            await self.handle_error(e)
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a planning task."""
        task_type = task.get("type", "unknown")
        
        if task_type == "create_itinerary":
            return await self._create_detailed_itinerary(task)
        elif task_type == "validate_plan":
            return await self._validate_plan(task)
        elif task_type == "generate_alternatives":
            return await self._generate_alternatives(task)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _create_trip_plan(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive trip plan."""
        destination = content.get("destination")
        duration = content.get("duration", 7)
        budget = content.get("budget", 5000)
        preferences = content.get("preferences", {})
        start_date = content.get("start_date")
        
        # Validate inputs
        if not destination:
            return {"error": "Destination is required"}
        
        # Create base plan structure
        plan = {
            "trip_id": f"trip_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "destination": destination,
            "duration": duration,
            "budget": budget,
            "preferences": preferences,
            "start_date": start_date,
            "created_at": datetime.now().isoformat(),
            "status": "planning",
            "itinerary": [],
            "accommodations": [],
            "transportation": [],
            "activities": [],
            "estimated_costs": {},
            "constraints": self._analyze_constraints(content)
        }
        
        # Generate itinerary
        itinerary = await self._generate_itinerary(destination, duration, preferences)
        plan["itinerary"] = itinerary
        
        # Estimate costs
        plan["estimated_costs"] = await self._estimate_costs(plan)
        
        # Store in memory
        self.update_memory({
            "type": "trip_plan_created",
            "trip_id": plan["trip_id"],
            "destination": destination,
            "duration": duration
        })
        
        return {
            "success": True,
            "plan": plan,
            "message": f"Trip plan created for {destination}"
        }
    
    async def _generate_itinerary(self, destination: str, duration: int, 
                                 preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a detailed itinerary."""
        itinerary = []
        
        # Get destination knowledge
        dest_info = await self._get_destination_info(destination)
        
        # Create daily plans
        for day in range(1, duration + 1):
            day_plan = {
                "day": day,
                "date": None,  # Will be filled when start_date is known
                "morning": [],
                "afternoon": [],
                "evening": [],
                "accommodation": None,
                "transportation": [],
                "meals": [],
                "notes": []
            }
            
            # Add activities based on preferences
            activities = await self._get_activities_for_day(
                destination, day, duration, preferences, dest_info
            )
            
            day_plan["morning"] = activities.get("morning", [])
            day_plan["afternoon"] = activities.get("afternoon", [])
            day_plan["evening"] = activities.get("evening", [])
            
            itinerary.append(day_plan)
        
        return itinerary
    
    async def _get_destination_info(self, destination: str) -> Dict[str, Any]:
        """Get information about the destination."""
        # In a real implementation, this would query external APIs
        # For now, return mock data
        return {
            "name": destination,
            "country": "Unknown",
            "climate": "Temperate",
            "currency": "USD",
            "language": "English",
            "timezone": "UTC",
            "popular_attractions": [],
            "local_cuisine": [],
            "transportation": [],
            "safety_notes": []
        }
    
    async def _get_activities_for_day(self, destination: str, day: int, 
                                    duration: int, preferences: Dict[str, Any],
                                    dest_info: Dict[str, Any]) -> Dict[str, List[str]]:
        """Get activities for a specific day."""
        interests = preferences.get("interests", [])
        
        # Mock activity suggestions based on interests
        activities = {
            "morning": [],
            "afternoon": [],
            "evening": []
        }
        
        if "culture" in interests:
            activities["morning"].append("Visit local museum")
            activities["afternoon"].append("Explore historical district")
        
        if "food" in interests:
            activities["morning"].append("Food market tour")
            activities["evening"].append("Traditional dinner")
        
        if "nature" in interests:
            activities["afternoon"].append("Nature walk or park visit")
        
        if "adventure" in interests:
            activities["morning"].append("Adventure activity")
        
        return activities
    
    async def _estimate_costs(self, plan: Dict[str, Any]) -> Dict[str, float]:
        """Estimate costs for the trip."""
        destination = plan["destination"]
        duration = plan["duration"]
        budget = plan["budget"]
        
        # Mock cost estimation
        daily_budget = budget / duration
        
        return {
            "accommodation": daily_budget * 0.4 * duration,
            "food": daily_budget * 0.3 * duration,
            "transportation": daily_budget * 0.2 * duration,
            "activities": daily_budget * 0.1 * duration,
            "total_estimated": budget,
            "daily_average": daily_budget
        }
    
    async def _analyze_constraints(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and extract planning constraints."""
        constraints = {
            "budget_limit": content.get("budget"),
            "time_constraints": {
                "duration": content.get("duration"),
                "start_date": content.get("start_date"),
                "end_date": content.get("end_date")
            },
            "accessibility": content.get("accessibility_requirements", []),
            "dietary": content.get("dietary_restrictions", []),
            "group_size": content.get("group_size", 1),
            "age_group": content.get("age_group", "adult")
        }
        
        return constraints
    
    async def _optimize_itinerary(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize an existing itinerary."""
        itinerary = content.get("itinerary", [])
        optimization_goals = content.get("goals", ["cost", "time"])
        
        # Mock optimization logic
        optimized = itinerary.copy()
        
        return {
            "success": True,
            "optimized_itinerary": optimized,
            "improvements": ["Reduced travel time", "Better activity grouping"]
        }
    
    async def _suggest_activities(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest activities for a destination."""
        destination = content.get("destination")
        interests = content.get("interests", [])
        budget = content.get("budget", 100)
        
        # Mock activity suggestions
        activities = [
            {
                "name": "City Walking Tour",
                "type": "sightseeing",
                "duration": "2-3 hours",
                "cost": 25,
                "rating": 4.5
            },
            {
                "name": "Local Food Experience",
                "type": "culinary",
                "duration": "3-4 hours",
                "cost": 75,
                "rating": 4.8
            }
        ]
        
        return {
            "success": True,
            "activities": activities,
            "destination": destination
        }
    
    async def _update_plan(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing trip plan."""
        trip_id = content.get("trip_id")
        updates = content.get("updates", {})
        
        # Mock plan update
        return {
            "success": True,
            "trip_id": trip_id,
            "updated_fields": list(updates.keys()),
            "message": "Plan updated successfully"
        }
    
    async def _create_detailed_itinerary(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed itinerary for a specific day or period."""
        return {"success": True, "itinerary": []}
    
    async def _validate_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a trip plan for feasibility."""
        return {"success": True, "valid": True, "issues": []}
    
    async def _generate_alternatives(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alternative plans."""
        return {"success": True, "alternatives": []}
    
    def _load_trip_templates(self) -> Dict[str, Any]:
        """Load trip planning templates."""
        return {
            "city_break": {
                "duration_range": (2, 5),
                "focus": ["culture", "food", "sightseeing"],
                "typical_activities": ["museums", "restaurants", "walking_tours"]
            },
            "beach_vacation": {
                "duration_range": (5, 14),
                "focus": ["relaxation", "water_activities"],
                "typical_activities": ["beach", "water_sports", "spa"]
            },
            "adventure": {
                "duration_range": (7, 21),
                "focus": ["outdoor_activities", "exploration"],
                "typical_activities": ["hiking", "climbing", "exploration"]
            }
        }
