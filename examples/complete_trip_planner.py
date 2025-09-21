"""
Complete Trip Planner Example
Demonstrates the full capabilities of the AI Trip Planner system.
"""

import os
from dotenv import load_dotenv
from trip_planner import TripPlanner

# Load environment variables
load_dotenv()

def main():
    """Main example function."""
    print("🚀 AI Trip Planner - Complete Example")
    print("=" * 50)
    
    # Initialize the trip planner
    # You can use either "groq" or "google" as LLM provider
    planner = TripPlanner(
        llm_provider="groq",  # or "google"
        llm_model="llama3-8b-8192"  # or "gemini-2.5-flash" for Google
    )
    
    # Example 1: Basic trip planning
    print("\n📋 Example 1: Basic Trip Planning")
    print("-" * 30)
    
    basic_trip = planner.plan_trip(
        destination="New York City",
        duration_days=3,
        preferences=["museums", "parks", "restaurants"],
        group_size=2,
        budget=2000
    )
    
    planner.print_trip_summary(basic_trip)
    
    # Example 2: Stream planning process
    print("\n\n📋 Example 2: Stream Planning Process")
    print("-" * 30)
    
    print("Planning trip to Paris...")
    for step in planner.stream_planning(
        destination="Paris",
        start_date="2024-06-01",
        end_date="2024-06-05",
        preferences=["art", "history", "food"],
        group_size=1,
        budget=1500
    ):
        current_step = step.get('current_step', 'unknown')
        places_count = len(step.get('places', []))
        print(f"Step: {current_step} - Found {places_count} places")
    
    # Example 3: International destination
    print("\n\n📋 Example 3: International Destination")
    print("-" * 30)
    
    international_trip = planner.plan_trip(
        destination="Tokyo, Japan",
        duration_days=5,
        preferences=["temples", "gardens", "technology", "food"],
        group_size=1,
        budget=3000
    )
    
    planner.print_trip_summary(international_trip)
    
    # Example 4: Budget-focused trip
    print("\n\n📋 Example 4: Budget-Focused Trip")
    print("-" * 30)
    
    budget_trip = planner.plan_trip(
        destination="Prague, Czech Republic",
        duration_days=4,
        preferences=["budget", "history", "architecture"],
        group_size=2,
        budget=800
    )
    
    planner.print_trip_summary(budget_trip)
    
    # Example 5: Luxury trip
    print("\n\n📋 Example 5: Luxury Trip")
    print("-" * 30)
    
    luxury_trip = planner.plan_trip(
        destination="Dubai, UAE",
        duration_days=4,
        preferences=["luxury", "shopping", "beaches", "fine dining"],
        group_size=2,
        budget=5000
    )
    
    planner.print_trip_summary(luxury_trip)

def interactive_planning():
    """Interactive trip planning session."""
    print("\n🎯 Interactive Trip Planning")
    print("=" * 50)
    
    planner = TripPlanner()
    
    # Get user input
    destination = input("Enter your destination: ").strip()
    if not destination:
        print("No destination provided. Exiting.")
        return
    
    duration = input("Enter trip duration in days (default 3): ").strip()
    duration = int(duration) if duration.isdigit() else 3
    
    budget = input("Enter your budget in USD (optional): ").strip()
    budget = float(budget) if budget.replace('.', '').isdigit() else None
    
    preferences_input = input("Enter your preferences (comma-separated, e.g., museums, parks, food): ").strip()
    preferences = [p.strip() for p in preferences_input.split(',')] if preferences_input else []
    
    group_size = input("Enter group size (default 1): ").strip()
    group_size = int(group_size) if group_size.isdigit() else 1
    
    # Plan the trip
    print(f"\nPlanning your trip to {destination}...")
    
    try:
        trip_plan = planner.plan_trip(
            destination=destination,
            duration_days=duration,
            budget=budget,
            preferences=preferences,
            group_size=group_size
        )
        
        planner.print_trip_summary(trip_plan)
        
    except Exception as e:
        print(f"Error planning trip: {str(e)}")

if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ["GROQ_API_KEY", "SERPER_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment.")
        print("Example .env file:")
        print("GROQ_API_KEY=your_groq_api_key_here")
        print("SERPER_API_KEY=your_serper_api_key_here")
        print("GOOGLE_API_KEY=your_google_api_key_here  # Optional, for Gemini models")
        return
    
    # Run examples
    try:
        main()
        
        # Ask if user wants interactive planning
        response = input("\nWould you like to try interactive planning? (y/n): ").strip().lower()
        if response == 'y':
            interactive_planning()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check your API keys and try again.")
