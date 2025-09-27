"""
Image Retrieval Agent with LLM Integration
Fetches images for tourist places and provides AI-powered image analysis and captions.
"""

import os
import requests
import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from ..state import Place


class ImageSearchInput(BaseModel):
    """Input schema for image search."""
    places: List[str] = Field(description="List of place names to search images for")


@tool(args_schema=ImageSearchInput)
def get_place_images(places: List[str]) -> Dict[str, str]:
    """
    Fetch images for tourist places using Serper API.
    
    Args:
        places: List of place names to search images for
    
    Returns:
        Dictionary mapping place names to image URLs
    """
    images = {}
    
    # Get API key from environment
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print("Warning: SERPER_API_KEY not found in environment variables")
        return {place: "No API key available" for place in places}
    
    url = "https://google.serper.dev/images"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    for place in places:
        try:
            payload = json.dumps({
                "q": f"{place}",
                "gl": "us",  # Country code
                "num": 1  # Get only the first image
            })
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            result = response.json()
            image_url = None
            
            # Look for Wikipedia image first (usually higher quality)
            # for img in result.get("images", []):
            #     if img.get("domain") == "en.wikipedia.org":
            #         image_url = img.get("imageUrl")
            #         break
            
            # If no Wikipedia image found, use the first available image
            if not image_url and result.get("images"):
                image_url = result["images"][0].get("imageUrl")
            
            if image_url:
                images[place] = image_url
            else:
                images[place] = "No image found"
                
        except Exception as e:
            print(f"Error fetching image for {place}: {str(e)}")
            images[place] = "Error retrieving image"
    
    return images


class ImageAnalysisOutput(BaseModel):
    """Output schema for LLM image analysis."""
    image_captions: Dict[str, str] = Field(description="AI-generated captions for each place")
    visual_highlights: Dict[str, List[str]] = Field(description="Visual highlights of each place")
    photography_tips: Dict[str, List[str]] = Field(description="Photography tips for each place")
    best_angles: Dict[str, List[str]] = Field(description="Best photography angles for each place")


class ImageRetrievalAgent:
    """Agent responsible for retrieving images and providing AI-powered image analysis."""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = [get_place_images]
        
        # LLM prompts for different tasks
        self.image_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional travel photographer and visual content expert.
            
            Analyze the tourist places and provide comprehensive visual insights:
            
            Places: {places_data}
            Destination: {destination}
            User preferences: {preferences}
            
            Provide detailed analysis including:
            1. Engaging captions for each place that highlight its unique features
            2. Visual highlights and key features to look for
            3. Photography tips and techniques for each location
            4. Best angles and viewpoints for photos
            5. Lighting recommendations for different times of day
            6. Composition suggestions for memorable photos
            7. Instagram-worthy spots and photo opportunities
            8. Equipment recommendations for photography
            
            Make your recommendations specific, practical, and tailored to each place's unique characteristics."""),
            ("human", "Please provide comprehensive visual analysis for these tourist places.")
        ])
        
        self.caption_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative travel writer and social media expert.
            
            Create engaging, informative captions for tourist places that are perfect for:
            - Social media posts
            - Travel blogs
            - Photo albums
            - Travel guides
            
            Place: {place_name}
            Category: {place_category}
            Description: {place_description}
            Destination: {destination}
            
            Create captions that:
            1. Highlight the place's unique features and appeal
            2. Include interesting facts or historical context
            3. Are engaging and shareable
            4. Include relevant hashtags
            5. Encourage others to visit
            6. Are appropriate for different social media platforms
            
            Provide 3-5 different caption styles (casual, informative, poetic, etc.)."""),
            ("human", "Create engaging captions for this place.")
        ])
        
        # Output parser
        self.image_parser = PydanticOutputParser(pydantic_object=ImageAnalysisOutput)
    
    def retrieve_images(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve images and provide AI-powered visual analysis.
        
        Args:
            state: Current trip planning state
            
        Returns:
            Updated state with images and AI analysis
        """
        try:
            places = state.get('places', [])
            
            if not places:
                return {
                    **state,
                    'messages': state.get('messages', []) + [
                        {
                            'type': 'warning',
                            'content': 'No places available for image retrieval'
                        }
                    ]
                }
            
            # Extract place names
            place_names = [place.name if hasattr(place, 'name') else str(place) for place in places]
            
            # Step 1: Get images
            images = get_place_images.invoke({'places': place_names})
            
            # Step 2: Use LLM to analyze places and generate visual content
            # visual_analysis = self._analyze_places_with_llm(
            #     places, state.get('destination', ''), state.get('preferences', [])
            # )
            
            # Step 3: Generate captions for each place
            # enhanced_places = self._enhance_places_with_captions(places, images, visual_analysis)
            
            # Update state
            updated_state = {
                **state,
                # 'places': enhanced_places,
                'place_images': images,
                # 'visual_analysis': visual_analysis,
                'current_step': 'images_retrieved',
                'messages': state.get('messages', []) + [
                    {
                        'type': 'info',
                        'content': f'Retrieved images and AI analysis for {len(images)} places'
                    }
                ]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error retrieving images: {str(e)}"
            return {
                **state,
                'errors': state.get('errors', []) + [error_msg],
                'current_step': 'error'
            }
    
    def _analyze_places_with_llm(self, places: List[Place], destination: str, preferences: List[str]) -> Dict[str, Any]:
        """Use LLM to analyze places and provide visual insights."""
        try:
            # Prepare places data for LLM
            places_data = []
            for place in places:
                place_info = f"- {place.name} ({place.category or 'attraction'}): {place.description}"
                if hasattr(place, 'rating') and place.rating:
                    place_info += f" [Rating: {place.rating}/5]"
                places_data.append(place_info)
            
            places_text = "\n".join(places_data)
            
            # Get LLM response
            response = self.image_analysis_prompt.invoke({
                'places_data': places_text,
                'destination': destination,
                'preferences': ', '.join(preferences) if preferences else 'general tourism'
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse structured output
            try:
                parsed_output = self.image_parser.parse(llm_response.content)
                return {
                    'image_captions': parsed_output.image_captions,
                    'visual_highlights': parsed_output.visual_highlights,
                    'photography_tips': parsed_output.photography_tips,
                    'best_angles': parsed_output.best_angles
                }
            except Exception as parse_error:
                print(f"Error parsing image analysis: {parse_error}")
                # Fallback to basic analysis
                return self._create_basic_visual_analysis(places)
            
        except Exception as e:
            print(f"Error analyzing places with LLM: {str(e)}")
            return self._create_basic_visual_analysis(places)
    
    def _enhance_places_with_captions(self, places: List[Place], place_images: Dict[str, str], 
                                    visual_analysis: Dict[str, Any]) -> List[Place]:
        """Enhance places with AI-generated captions and visual insights."""
        enhanced_places = []
        
        for place in places:
            try:
                # Generate specific captions for this place
                caption = self._generate_place_caption(place, place_images.get(place.name, ''))
                
                # Add visual analysis to place
                place.visual_highlights = visual_analysis.get('visual_highlights', {}).get(place.name, [])
                place.photography_tips = visual_analysis.get('photography_tips', {}).get(place.name, [])
                place.best_angles = visual_analysis.get('best_angles', {}).get(place.name, [])
                place.image_caption = caption
                
                # Update image URL
                if place.name in place_images:
                    place.image_url = place_images[place.name]
                
                enhanced_places.append(place)
                
            except Exception as e:
                print(f"Error enhancing place {place.name}: {str(e)}")
                enhanced_places.append(place)  # Use original place
        
        return enhanced_places
    
    def _generate_place_caption(self, place: Place, image_url: str) -> str:
        """Generate AI-powered caption for a specific place."""
        try:
            response = self.caption_generation_prompt.invoke({
                'place_name': place.name,
                'place_category': place.category or 'attraction',
                'place_description': place.description,
                'destination': 'destination'  # Could be enhanced with actual destination
            })
            
            llm_response = self.llm.invoke(response)
            
            # Extract the first caption from the response
            content = llm_response.content
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 20:
                    return line
            
            # Fallback caption
            return f"Discover {place.name}, a fascinating {place.category or 'attraction'} worth visiting!"
            
        except Exception as e:
            print(f"Error generating caption for {place.name}: {str(e)}")
            return f"Explore {place.name} and capture amazing memories!"
    
    def _create_basic_visual_analysis(self, places: List[Place]) -> Dict[str, Any]:
        """Create basic visual analysis as fallback."""
        analysis = {
            'image_captions': {},
            'visual_highlights': {},
            'photography_tips': {},
            'best_angles': {}
        }
        
        for place in places:
            analysis['image_captions'][place.name] = f"Beautiful view of {place.name}"
            analysis['visual_highlights'][place.name] = ['Architecture', 'Scenic views', 'Unique features']
            analysis['photography_tips'][place.name] = ['Use natural lighting', 'Try different angles', 'Capture details']
            analysis['best_angles'][place.name] = ['Front view', 'Side angle', 'Close-up details']
        
        return analysis
    
    def get_agent_tools(self):
        """Get tools available to this agent."""
        return self.tools
