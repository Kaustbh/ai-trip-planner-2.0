"""
Destination Research Agent with LLM Integration
Searches for tourist places using SearchAPI and Google Maps with AI-powered filtering and enhancement.
"""

import os
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.utilities import SearchApiAPIWrapper
from pydantic import BaseModel, Field
from ..state import Place, TripPlanningState


class DestinationSearchInput(BaseModel):
    """Input schema for destination search."""
    destination: str = Field(description="Destination to search for (city, country, or region)")
    preferences: List[str] = Field(default_factory=list, description="User preferences for places")


@tool(args_schema=DestinationSearchInput)
def search_tourist_places(destination: str, preferences: List[str] = None) -> List[Dict[str, Any]]:
    """
    Search for tourist places in a destination using SearchAPI and Google Maps.
    
    Args:
        destination: The destination to search for
        preferences: List of user preferences (e.g., museums, parks, restaurants)
    
    Returns:
        List of tourist places with their details
    """
    if preferences is None:
        preferences = []
    
    try:
        # Initialize SearchAPI with Google Maps engine
        search = SearchApiAPIWrapper(engine="google_maps")
        
        # Build search query based on preferences
        if preferences:
            pref_text = ", ".join(preferences)
            query = f"tourist places {destination} {pref_text}"
        else:
            query = f"tourist places {destination}"
        
        # Perform search
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
            
            # Only add places with valid names
            if place_data['name']:
                places.append(place_data)
        
        return places[:20]  # Limit to top 20 results
        
    except Exception as e:
        print(f"Error searching for places: {str(e)}")
        return []


class PlaceFilteringOutput(BaseModel):
    """Output schema for LLM place filtering."""
    filtered_places: List[Dict[str, Any]] = Field(description="Filtered and ranked places")
    reasoning: str = Field(description="Reasoning for place selection")
    recommendations: List[str] = Field(description="Additional recommendations")


class PlaceEnhancementOutput(BaseModel):
    """Output schema for LLM place enhancement."""
    enhanced_description: str = Field(description="Enhanced place description")
    highlights: List[str] = Field(description="Key highlights of the place")
    best_time_to_visit: str = Field(description="Best time to visit")
    tips: List[str] = Field(description="Visiting tips")


class DestinationResearchAgent:
    """Agent responsible for researching tourist destinations with LLM integration."""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = [search_tourist_places]
        
        # LLM prompts for different tasks
        self.place_filtering_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel advisor with deep knowledge of tourist destinations worldwide.
            
            Your task is to filter top(best) 10 tourist places based on user preferences and provide intelligent recommendations.
            
            User preferences: {preferences}
            Destination: {destination}
            Available places: {places_data}
            
            Analyze each place and:
            1. Filter out irrelevant or low-quality places
            2. Rank places by relevance to user preferences
            3. Consider factors like ratings, reviews, and uniqueness
            4. Provide reasoning for your selections
            5. Suggest additional recommendations
            
            Return the top 10 most relevant places with enhanced information."""),
            ("human", "Please filter and rank these places for the user.")
        ])
        
        self.place_enhancement_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional travel writer and local expert. Enhance the description of tourist places.
            
            Place: {place_name}
            Category: {place_category}
            Original description: {original_description}
            Destination: {destination}
            
            Create an engaging, informative description that includes:
            1. What makes this place special and unique
            2. What visitors can expect to see/do
            3. Historical or cultural significance
            4. Best time to visit
            5. Practical visiting tips
            6. Why it's worth visiting
            
            Keep descriptions concise but compelling (2-3 paragraphs)."""),
            ("human", "Please enhance this place description.")
        ])
        
        # Output parsers
        self.filtering_parser = PydanticOutputParser(pydantic_object=PlaceFilteringOutput)
        self.enhancement_parser = PydanticOutputParser(pydantic_object=PlaceEnhancementOutput)
    
    def research_destination(self, state: TripPlanningState) -> TripPlanningState:
        """
        Research tourist places for the given destination with LLM-powered filtering and enhancement.
        
        Args:
            state: Current trip planning state
            
        Returns:
            Updated state with discovered and enhanced places
        """
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
            
            # Step 2: Use LLM to filter and rank places
            filtered_places = self._filter_places_with_llm(places_data, destination, preferences)
            
            # Step 3: Use LLM to enhance place descriptions
            enhanced_places = self._enhance_places_with_llm(filtered_places, destination)
            
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
                        'content': f'Found and enhanced {len(places)} tourist places in {destination} using AI'
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
                f"- {place['name']} ({place.get('category', 'unknown')}): {place.get('description', 'No description')} [Rating: {place.get('rating', 'N/A')}]"
                for place in places_data
            ])
            
            # Get LLM response
            response = self.place_filtering_prompt.invoke({
                'places_data': places_text,
                'destination': destination,
                'preferences': ', '.join(preferences) if preferences else 'general tourism'
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse structured output
            try:
                parsed_output = self.filtering_parser.parse(llm_response.content)
                return parsed_output.filtered_places
            except Exception as parse_error:
                print(f"Error parsing LLM response: {parse_error}")
                # Fallback to top 10 places
                return places_data[:10]
            
        except Exception as e:
            print(f"Error filtering places with LLM: {str(e)}")
            return places_data[:10]  # Fallback to first 10
    
    def _enhance_places_with_llm(self, places_data: List[Dict], destination: str) -> List[Dict]:
        """Use LLM to enhance place descriptions."""
        enhanced_places = []
        
        for place in places_data:
            try:
                # Get enhanced description from LLM
                response = self.place_enhancement_prompt.invoke({
                    'place_name': place['name'],
                    'place_category': place.get('category', 'attraction'),
                    'original_description': place.get('description', ''),
                    'destination': destination
                })
                
                llm_response = self.llm.invoke(response)
                
                # Parse structured output
                try:
                    parsed_output = self.enhancement_parser.parse(llm_response.content)
                    place['enhanced_description'] = parsed_output.enhanced_description
                    place['highlights'] = parsed_output.highlights
                    place['best_time_to_visit'] = parsed_output.best_time_to_visit
                    place['tips'] = parsed_output.tips
                except Exception as parse_error:
                    print(f"Error parsing enhancement for {place['name']}: {parse_error}")
                    # Fallback to simple enhancement
                    place['enhanced_description'] = f"Discover {place['name']}, a fascinating {place.get('category', 'attraction')} in {destination}. {place.get('description', '')}"
                
                enhanced_places.append(place)
                
            except Exception as e:
                print(f"Error enhancing description for {place['name']}: {str(e)}")
                enhanced_places.append(place)  # Use original data
        
        return enhanced_places
    
    def get_agent_tools(self):
        """Get tools available to this agent."""
        return self.tools
