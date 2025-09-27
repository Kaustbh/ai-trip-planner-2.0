"""
Trip Planning Workflow
Main workflow orchestrator for the multi-agent trip planning system.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain.chat_models import init_chat_model
import os

from ..state import TripPlanningState
from ..agents import (
    DestinationResearchAgent,
    ImageRetrievalAgent,
    WeatherForecastAgent,
    ItineraryPlanningAgent,
    BudgetPlanningAgent
)


class TripPlanningWorkflow:
    """Main workflow orchestrator for trip planning."""
    
    def __init__(self, 
                 llm_provider: str = "groq",
                 llm_model: str = "llama3-8b-8192",
                 google_api_key: str = None):
        """
        Initialize the trip planning workflow.
        
        Args:
            llm_provider: LLM provider to use ("groq" or "google")
            llm_model: Model name to use
            google_api_key: Google API key for Gemini models
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        
        # Initialize LLM
        if llm_provider == "groq":
            self.llm = ChatGroq(model=llm_model)
        elif llm_provider == "google":
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
            self.llm = init_chat_model(model="google_genai:gemini-2.5-flash")
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        
        # Initialize agents
        self.destination_agent = DestinationResearchAgent(self.llm)
        self.image_agent = ImageRetrievalAgent(self.llm)
        self.weather_agent = WeatherForecastAgent(self.llm)
        self.itinerary_agent = ItineraryPlanningAgent(self.llm)
        # self.budget_agent = BudgetPlanningAgent(self.llm)
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(TripPlanningState)
        
        # Add nodes
        workflow.add_node("research_destination", self._research_destination_node)
        workflow.add_node("retrieve_images", self._retrieve_images_node)
        workflow.add_node("get_weather", self._get_weather_node)
        workflow.add_node("plan_itinerary", self._plan_itinerary_node)
        # workflow.add_node("plan_budget", self._plan_budget_node)
        workflow.add_node("finalize_plan", self._finalize_plan_node)
        
        # Define edges
        workflow.add_edge(START, "research_destination")
        workflow.add_edge("research_destination", "retrieve_images")
        workflow.add_edge("retrieve_images", "get_weather")
        workflow.add_edge("get_weather", "plan_itinerary")
        workflow.add_edge("plan_itinerary", "finalize_plan")
        # workflow.add_edge("plan_itinerary", "plan_budget")
        # workflow.add_edge("plan_budget", "finalize_plan")
        workflow.add_edge("finalize_plan", END)
        
        return workflow.compile()
    
    def _research_destination_node(self, state: TripPlanningState) -> TripPlanningState:
        """Node for researching destination."""
        return self.destination_agent.research_destination(state)
    
    def _retrieve_images_node(self, state: TripPlanningState) -> TripPlanningState:
        """Node for retrieving images."""
        return self.image_agent.retrieve_images(state)
    
    def _get_weather_node(self, state: TripPlanningState) -> TripPlanningState:
        """Node for getting weather forecast."""
        return self.weather_agent.get_weather_forecast(state)
    
    def _plan_itinerary_node(self, state: TripPlanningState) -> TripPlanningState:
        """Node for planning itinerary."""
        return self.itinerary_agent.plan_itinerary(state)
    
    # def _plan_budget_node(self, state: TripPlanningState) -> TripPlanningState:
    #     """Node for planning budget."""
    #     return self.budget_agent.plan_budget(state)
    
    def _finalize_plan_node(self, state: TripPlanningState) -> TripPlanningState:
        """Node for finalizing the trip plan."""
        try:
            # Add final recommendations
            recommendations = []
            
            # Check if we have all required data
            if not state.get('places'):
                recommendations.append("No places found for the destination")
            
            if not state.get('itinerary'):
                recommendations.append("Itinerary could not be created")
            
            if not state.get('weather_forecast'):
                recommendations.append("Weather forecast not available")
            
            # Add general recommendations
            recommendations.extend([
                "Book accommodations in advance",
                "Check visa requirements",
                "Purchase travel insurance",
                "Download offline maps",
                "Pack according to weather forecast"
            ])
            
            # Update state
            updated_state = {
                **state,
                'recommendations': recommendations,
                'current_step': 'completed',
                'messages': state.get('messages', []) + [
                    {
                        'type': 'success',
                        'content': 'Trip planning completed successfully!'
                    }
                ]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error finalizing plan: {str(e)}"
            return {
                **state,
                'errors': state.get('errors', []) + [error_msg],
                'current_step': 'error'
            }
    
    def plan_trip(self, 
                  destination: str,
                  start_date: str = None,
                  end_date: str = None,
                  duration_days: int = None,
                #   budget: float = None,
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
            preferences: List of preferences
            group_size: Number of people traveling
        
        Returns:
            Complete trip plan
        """
        if preferences is None:
            preferences = []
        
        # Create initial state
        initial_state = {
            'destination': destination,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': duration_days,
            # 'budget': budget,
            'preferences': preferences or [],
            'group_size': group_size,
            'places': [],
            'place_images': {},
            'weather_forecast': [],
            'itinerary': [],
            'budget_breakdown': None,
            'recommendations': [],
            'current_step': 'initialization',
            'errors': [],
            'messages': []
        }
        
        # Run workflow
        try:
            result = self.workflow.invoke(initial_state)
            return result
        except Exception as e:
            return {
                **initial_state,
                'errors': [f"Workflow execution error: {str(e)}"],
                'current_step': 'error'
            }
    
    def stream_planning(self, 
                       destination: str,
                       start_date: str = None,
                       end_date: str = None,
                       duration_days: int = None,
                    #    budget: float = None,
                       preferences: List[str] = None,
                       group_size: int = 1):
        """
        Stream the trip planning process.
        
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
        
        # Create initial state
        initial_state = {
            'destination': destination,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': duration_days,
            # 'budget': budget,
            'preferences': preferences or [],
            'group_size': group_size,
            'places': [],
            'place_images': {},
            'weather_forecast': [],
            'itinerary': [],
            'budget_breakdown': None,
            'recommendations': [],
            'current_step': 'initialization',
            'errors': [],
            'messages': []
        }
        
        # Stream workflow
        try:
            for event in self.workflow.stream(initial_state, stream_mode="values"):
                yield event
        except Exception as e:
            yield {
                **initial_state,
                'errors': [f"Workflow execution error: {str(e)}"],
                'current_step': 'error'
            }
    
    def get_workflow_graph(self):
        """Get the workflow graph for visualization."""
        return self.workflow.get_graph()
