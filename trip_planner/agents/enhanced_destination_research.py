"""
Enhanced Destination Research Agent with LLM Integration
Uses LLM for intelligent place filtering and description generation.
"""

import os
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_community.utilities import SearchApiAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from ..state import Place, TripPlanningState


class DestinationSearchInput(BaseModel):
    """Input schema for destination search."""
    destination: str = Field(description="Destination to search for (city, country, or region)")
    preferences: List[str] = Field(default_factory=list, description="User preferences for places")


@tool(args_schema=DestinationSearchInput)
def search_tourist_places(destination: str, preferences: List[str] = None) -> List[Dict[str, Any]]:
    """Search for tourist places using SearchAPI."""
    if preferences is None:
        preferences = []
    
    try:
        search = SearchApiAPIWrapper(engine="google_maps")
        
        if preferences:
            pref_text = ", ".join(preferences)
            query = f"tourist places {destination} {pref_text}"
        else:
            query = f"tourist places {destination}"
        
        response = search.results(query)
        
        places = []
        for result in response.get('local_results', []):
            place_data = {
                'name': result.get('title', ''),
                'description': result.get('description', ''),
                'rating': result.get('rating'),
                'address': result.get('address', ''),
                'category': result.get('type', ''),
                'coordinates': {
                    'latitude': result.get('latitude'),
                    'longitude': result.get('longitude')
                } if result.get('latitude') and result.get('longitude') else None
            }
            
            if place_data['name']:
                places.append(place_data)
        
        return places[:20]
        
    except Exception as e:
        print(f"Error searching for places: {str(e)}")
        return []


class EnhancedDestinationResearchAgent:
    """Enhanced agent with LLM integration for intelligent place processing."""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = [search_tourist_places]
        
        # LLM prompts for different tasks
        self.place_filtering_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel advisor. Given a list of tourist places and user preferences, 
            filter and rank the places to provide the most relevant recommendations.
            
            User preferences: {preferences}
            Destination: {destination}
            
            Return a JSON list of the top places with enhanced descriptions and reasoning for selection."""),
            ("human", "Here are the places found: {places}")
        ])
        
        self.place_description_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel writer. Create engaging, informative descriptions for tourist places.
            Include what makes each place special, what visitors can expect, and why it's worth visiting.
            Keep descriptions concise but compelling (2-3 sentences)."""),
            ("human", "Create a description for: {place_name} in {destination}. Category: {category}")
        ])
    
    def research_destination(self, state: TripPlanningState) -> TripPlanningState:
        """Research destinations with LLM-enhanced processing."""
        try:
            destination = state.get('destination', '')
            preferences = state.get('preferences', [])
            
            if not destination:
                return {
                    **state,
                    'errors': state.get('errors', []) + ['No destination provided'],
                    'current_step': 'error'
                }
            
            # Step 1: Search for places using SearchAPI
            places_data = search_tourist_places.invoke({
                'destination': destination,
                'preferences': preferences
            })
            
            if not places_data:
                return {
                    **state,
                    'errors': state.get('errors', []) + ['No places found for destination'],
                    'current_step': 'error'
                }
            
            # Step 2: Use LLM to filter and rank places based on preferences
            filtered_places = self._filter_places_with_llm(
                places_data, destination, preferences
            )
            
            # Step 3: Use LLM to enhance place descriptions
            enhanced_places = self._enhance_place_descriptions(
                filtered_places, destination
            )
            
            # Convert to Place objects
            places = []
            for place_data in enhanced_places:
                place = Place(
                    name=place_data.get('name', ''),
                    description=place_data.get('enhanced_description', place_data.get('description', '')),
                    rating=place_data.get('rating'),
                    address=place_data.get('address'),
                    category=place_data.get('category'),
                    coordinates=place_data.get('coordinates')
                )
                places.append(place)
            
            # Update state
            updated_state = {
                **state,
                'places': places,
                'current_step': 'places_researched',
                'messages': state.get('messages', []) + [
                    {
                        'type': 'info',
                        'content': f'Found and filtered {len(places)} relevant places in {destination}'
                    }
                ]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error researching destination: {str(e)}"
            return {
                **state,
                'errors': state.get('errors', []) + [error_msg],
                'current_step': 'error'
            }
    
    def _filter_places_with_llm(self, places_data: List[Dict], destination: str, preferences: List[str]) -> List[Dict]:
        """Use LLM to filter and rank places based on preferences."""
        try:
            # Prepare places data for LLM
            places_text = "\n".join([
                f"- {place['name']} ({place.get('category', 'unknown')}): {place.get('description', 'No description')}"
                for place in places_data
            ])
            
            # Get LLM response
            response = self.place_filtering_prompt.invoke({
                'places': places_text,
                'destination': destination,
                'preferences': ', '.join(preferences) if preferences else 'general tourism'
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse LLM response (simplified - in production, use structured output)
            # For now, return top 10 places
            return places_data[:10]
            
        except Exception as e:
            print(f"Error filtering places with LLM: {str(e)}")
            return places_data[:10]  # Fallback to first 10
    
    def _enhance_place_descriptions(self, places_data: List[Dict], destination: str) -> List[Dict]:
        """Use LLM to enhance place descriptions."""
        enhanced_places = []
        
        for place in places_data:
            try:
                # Get enhanced description from LLM
                response = self.place_description_prompt.invoke({
                    'place_name': place['name'],
                    'destination': destination,
                    'category': place.get('category', 'attraction')
                })
                
                llm_response = self.llm.invoke(response)
                enhanced_description = llm_response.content
                
                # Add enhanced description to place data
                place['enhanced_description'] = enhanced_description
                enhanced_places.append(place)
                
            except Exception as e:
                print(f"Error enhancing description for {place['name']}: {str(e)}")
                enhanced_places.append(place)  # Use original description
        
        return enhanced_places
    
    def get_agent_tools(self):
        """Get tools available to this agent."""
        return self.tools
