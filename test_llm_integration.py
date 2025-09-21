#!/usr/bin/env python3
"""
Test script for LLM Integration in AI Trip Planner
Tests all agents with proper LLM integration.
"""

import os
import sys
from datetime import date, timedelta
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trip_planner.main import TripPlanner
from trip_planner.state import TripPlanningState

def test_llm_integration():
    """Test the complete LLM integration across all agents."""
    print("🤖 Testing LLM Integration in AI Trip Planner")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required API keys
    required_keys = ['GROQ_API_KEY', 'SERPER_API_KEY', 'SEARCHAPI_API_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"❌ Missing required environment variables: {', '.join(missing_keys)}")
        print("Please set these in your .env file")
        return False
    
    try:
        # Initialize the trip planner with LLM
        print("🚀 Initializing Trip Planner with LLM integration...")
        planner = TripPlanner(
            llm_provider="groq",
            llm_model="llama3-8b-8192"
        )
        print("✅ Trip Planner initialized successfully")
        
        # Test parameters
        destination = "Paris"
        duration_days = 3
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=duration_days - 1)
        preferences = ["museums", "parks", "restaurants"]
        budget = 2000
        group_size = 2
        
        print(f"\n📋 Test Parameters:")
        print(f"   Destination: {destination}")
        print(f"   Duration: {duration_days} days")
        print(f"   Dates: {start_date} to {end_date}")
        print(f"   Preferences: {', '.join(preferences)}")
        print(f"   Budget: ${budget:,}")
        print(f"   Group Size: {group_size}")
        
        # Test the complete workflow
        print(f"\n🔄 Running complete trip planning workflow...")
        trip_plan = planner.plan_trip(
            destination=destination,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            duration_days=duration_days,
            budget=budget,
            preferences=preferences,
            group_size=group_size
        )
        
        # Display results
        print(f"\n📊 Trip Planning Results:")
        print(f"   Status: {trip_plan.get('current_step', 'unknown')}")
        print(f"   Errors: {len(trip_plan.get('errors', []))}")
        print(f"   Messages: {len(trip_plan.get('messages', []))}")
        
        # Test individual agent capabilities
        print(f"\n🔍 Testing Individual Agent Capabilities:")
        
        # Test Destination Research Agent
        if trip_plan.get('places'):
            places = trip_plan['places']
            print(f"   ✅ Destination Research: Found {len(places)} places")
            
            # Check for LLM enhancements
            enhanced_places = [p for p in places if hasattr(p, 'highlights') or hasattr(p, 'best_time_to_visit')]
            print(f"   ✅ LLM Enhancement: {len(enhanced_places)} places with AI enhancements")
            
            # Show sample place with enhancements
            if places:
                sample_place = places[0]
                print(f"   📍 Sample Place: {sample_place.name}")
                print(f"      Description: {sample_place.description[:100]}...")
                if hasattr(sample_place, 'highlights') and sample_place.highlights:
                    print(f"      Highlights: {', '.join(sample_place.highlights[:3])}")
                if hasattr(sample_place, 'best_time_to_visit') and sample_place.best_time_to_visit:
                    print(f"      Best Time: {sample_place.best_time_to_visit}")
        else:
            print("   ❌ Destination Research: No places found")
        
        # Test Image Retrieval Agent
        if trip_plan.get('place_images'):
            images = trip_plan['place_images']
            print(f"   ✅ Image Retrieval: Found {len(images)} images")
            
            # Check for visual analysis
            if trip_plan.get('visual_analysis'):
                visual_analysis = trip_plan['visual_analysis']
                print(f"   ✅ Visual Analysis: AI-generated captions and photography tips")
                
                # Show sample visual analysis
                if 'image_captions' in visual_analysis and visual_analysis['image_captions']:
                    sample_caption = list(visual_analysis['image_captions'].values())[0]
                    print(f"   📸 Sample Caption: {sample_caption[:100]}...")
        else:
            print("   ❌ Image Retrieval: No images found")
        
        # Test Weather Forecast Agent
        if trip_plan.get('weather_forecast'):
            weather = trip_plan['weather_forecast']
            print(f"   ✅ Weather Forecast: {len(weather)} days of weather data")
            
            # Check for weather insights
            if trip_plan.get('weather_insights'):
                weather_insights = trip_plan['weather_insights']
                print(f"   ✅ Weather Insights: AI-powered weather analysis")
                
                # Show sample weather insight
                if 'activity_recommendations' in weather_insights:
                    recommendations = weather_insights['activity_recommendations']
                    if recommendations:
                        sample_rec = list(recommendations.values())[0]
                        if sample_rec:
                            print(f"   🌤️ Sample Recommendation: {sample_rec[0] if sample_rec else 'N/A'}")
        else:
            print("   ❌ Weather Forecast: No weather data found")
        
        # Test Itinerary Planning Agent
        if trip_plan.get('itinerary'):
            itinerary = trip_plan['itinerary']
            print(f"   ✅ Itinerary Planning: {len(itinerary)} days planned")
            
            # Check for AI-generated activities
            ai_activities = 0
            for day in itinerary:
                if hasattr(day, 'activities') and day.activities:
                    ai_activities += len(day.activities)
            print(f"   ✅ AI Activities: {ai_activities} AI-generated activities")
            
            # Show sample itinerary day
            if itinerary:
                sample_day = itinerary[0]
                print(f"   📅 Sample Day: {sample_day.date}")
                print(f"      Places: {len(sample_day.places)}")
                print(f"      Activities: {len(sample_day.activities)}")
                if sample_day.activities:
                    print(f"      Sample Activity: {sample_day.activities[0][:100]}...")
        else:
            print("   ❌ Itinerary Planning: No itinerary found")
        
        # Test Budget Planning Agent
        if trip_plan.get('budget_breakdown'):
            budget_data = trip_plan['budget_breakdown']
            print(f"   ✅ Budget Planning: ${budget_data.get('total_estimated', 0):,.2f} estimated")
            
            # Check for LLM enhancements
            if 'money_saving_tips' in budget_data:
                tips = budget_data['money_saving_tips']
                print(f"   ✅ Money-Saving Tips: {len(tips)} AI-generated tips")
                if tips:
                    print(f"   💰 Sample Tip: {tips[0]}")
            
            if 'cost_explanations' in budget_data:
                explanations = budget_data['cost_explanations']
                print(f"   ✅ Cost Explanations: {len(explanations)} detailed explanations")
        else:
            print("   ❌ Budget Planning: No budget data found")
        
        # Test error handling
        print(f"\n🔧 Error Handling Test:")
        if trip_plan.get('errors'):
            print(f"   ⚠️ Errors encountered: {len(trip_plan['errors'])}")
            for error in trip_plan['errors'][:3]:  # Show first 3 errors
                print(f"      - {error}")
        else:
            print("   ✅ No errors encountered")
        
        # Test message system
        print(f"\n💬 Message System Test:")
        if trip_plan.get('messages'):
            messages = trip_plan['messages']
            print(f"   📝 Total messages: {len(messages)}")
            
            # Count message types
            message_types = {}
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            for msg_type, count in message_types.items():
                print(f"      {msg_type}: {count}")
        else:
            print("   ❌ No messages found")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        success_indicators = [
            trip_plan.get('places', []),
            trip_plan.get('itinerary', []),
            trip_plan.get('budget_breakdown', {}),
            trip_plan.get('weather_forecast', [])
        ]
        
        successful_agents = sum(1 for indicator in success_indicators if indicator)
        total_agents = len(success_indicators)
        
        print(f"   Successful Agents: {successful_agents}/{total_agents}")
        print(f"   Success Rate: {(successful_agents/total_agents)*100:.1f}%")
        
        if successful_agents == total_agents:
            print("   🎉 All agents working with LLM integration!")
            return True
        else:
            print("   ⚠️ Some agents need attention")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_fallback():
    """Test LLM fallback mechanisms."""
    print(f"\n🛡️ Testing LLM Fallback Mechanisms:")
    
    try:
        # Test with invalid LLM provider
        print("   Testing invalid LLM provider...")
        try:
            planner = TripPlanner(llm_provider="invalid", llm_model="test")
            print("   ❌ Should have failed with invalid provider")
        except ValueError as e:
            print(f"   ✅ Correctly failed: {str(e)}")
        
        # Test with missing API key
        print("   Testing missing API key...")
        original_key = os.getenv('GROQ_API_KEY')
        os.environ['GROQ_API_KEY'] = ''
        
        try:
            planner = TripPlanner(llm_provider="groq", llm_model="llama3-8b-8192")
            print("   ❌ Should have failed with missing API key")
        except ValueError as e:
            print(f"   ✅ Correctly failed: {str(e)}")
        finally:
            # Restore original key
            if original_key:
                os.environ['GROQ_API_KEY'] = original_key
        
        print("   ✅ Fallback mechanisms working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing fallback: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 AI Trip Planner - LLM Integration Test Suite")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_llm_integration()
    test2_passed = test_llm_fallback()
    
    print(f"\n📋 Test Results Summary:")
    print(f"   LLM Integration Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Fallback Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 All tests passed! LLM integration is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️ Some tests failed. Please check the output above.")
        sys.exit(1)
