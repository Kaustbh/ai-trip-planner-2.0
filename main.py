"""
AI Trip Planner - Main Entry Point
A comprehensive multi-agent trip planning system using LangGraph.
"""

from dotenv import load_dotenv
from trip_planner import TripPlanner

# Load environment variables
load_dotenv()

def main():
    """Main function to demonstrate the trip planner."""
    print("🚀 AI Trip Planner - Multi-Agent System")
    print("=" * 50)
    
    # Initialize the trip planner
    planner = TripPlanner(
        llm_provider="groq",  # or "google"
        llm_model="llama3-8b-8192"
    )
    
    # Example trip planning
    print("Planning a trip to New York City...")
    
    trip_plan = planner.plan_trip(
        destination="New York City",
        duration_days=3,
        preferences=["museums", "parks", "restaurants"],
        group_size=2,
        budget=2000
    )
    
    # Print the trip summary
    planner.print_trip_summary(trip_plan)

if __name__ == "__main__":
    main()
