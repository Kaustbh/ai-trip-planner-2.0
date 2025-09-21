#!/usr/bin/env python3
"""
AI Trip Planner CLI
Command-line interface for the AI Trip Planner system.
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trip_planner import TripPlanner


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI Trip Planner - Plan your perfect trip with AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python trip_planner_cli.py "New York City" --duration 3 --budget 2000
  python trip_planner_cli.py "Paris" --start-date 2024-06-01 --end-date 2024-06-05
  python trip_planner_cli.py "Tokyo" --preferences museums,parks,food --group-size 2
  python trip_planner_cli.py "Prague" --budget 800 --preferences budget,history
        """
    )
    
    # Required arguments
    parser.add_argument(
        "destination",
        help="Destination to visit (city, country, or region)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format (default: today)"
    )
    
    parser.add_argument(
        "--end-date", 
        help="End date in YYYY-MM-DD format"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        help="Trip duration in days (default: 3)"
    )
    
    parser.add_argument(
        "--budget",
        type=float,
        help="Budget in USD"
    )
    
    parser.add_argument(
        "--preferences",
        help="Comma-separated preferences (e.g., museums,parks,food)"
    )
    
    parser.add_argument(
        "--group-size",
        type=int,
        default=1,
        help="Number of people traveling (default: 1)"
    )
    
    parser.add_argument(
        "--llm-provider",
        choices=["groq", "google"],
        default="groq",
        help="LLM provider to use (default: groq)"
    )
    
    parser.add_argument(
        "--llm-model",
        default="llama-3.1-8b-instant",
        help="LLM model to use (default: llama-3.1-8b-instant)"
    )
    
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the planning process for real-time updates"
    )
    
    parser.add_argument(
        "--output",
        help="Output file to save trip plan (JSON format)"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Validate required environment variables
    required_vars = ["GROQ_API_KEY", "SERPER_API_KEY"]
    if args.llm_provider == "google":
        required_vars.append("GOOGLE_API_KEY")
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment.")
        return 1
    
    # Process preferences
    preferences = []
    if args.preferences:
        preferences = [p.strip() for p in args.preferences.split(',')]
    
    # Calculate dates if needed
    start_date = args.start_date
    end_date = args.end_date
    duration = args.duration
    
    if start_date and end_date and not duration:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        duration = (end - start).days + 1
    elif start_date and duration and not end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = start + timedelta(days=duration - 1)
        end_date = end.strftime('%Y-%m-%d')
    elif not start_date and not end_date and not duration:
        start_date = datetime.now().strftime('%Y-%m-%d')
        duration = 3
        end_date = (datetime.now() + timedelta(days=duration - 1)).strftime('%Y-%m-%d')
    elif not duration:
        duration = 3
    
    # Initialize trip planner
    try:
        planner = TripPlanner(
            llm_provider=args.llm_provider,
            llm_model=args.llm_model
        )
    except Exception as e:
        print(f"❌ Error initializing trip planner: {str(e)}")
        return 1
    
    # Plan the trip
    try:
        print(f"🗺️  Planning trip to {args.destination}...")
        print(f"📅 Duration: {duration} days")
        if args.budget:
            print(f"💰 Budget: ${args.budget:,.2f}")
        if preferences:
            print(f"🎯 Preferences: {', '.join(preferences)}")
        print()
        
        if args.stream:
            # Stream planning process
            for step in planner.stream_planning(
                destination=args.destination,
                start_date=start_date,
                end_date=end_date,
                duration_days=duration,
                budget=args.budget,
                preferences=preferences,
                group_size=args.group_size
            ):
                current_step = step.get('current_step', 'unknown')
                places_count = len(step.get('places', []))
                print(f"📌 {current_step} - Found {places_count} places")
            
            # Get final result
            trip_plan = step
        else:
            # Regular planning
            trip_plan = planner.plan_trip(
                destination=args.destination,
                start_date=start_date,
                end_date=end_date,
                duration_days=duration,
                budget=args.budget,
                preferences=preferences,
                group_size=args.group_size
            )
        
        # Print summary
        planner.print_trip_summary(trip_plan)
        
        # Save to file if requested
        if args.output:
            import json
            # Convert objects to dictionaries for JSON serialization
            trip_dict = {}
            for key, value in trip_plan.items():
                if hasattr(value, 'dict'):
                    trip_dict[key] = value.dict()
                elif isinstance(value, list):
                    trip_dict[key] = []
                    for item in value:
                        if hasattr(item, 'dict'):
                            trip_dict[key].append(item.dict())
                        else:
                            trip_dict[key].append(item)
                else:
                    trip_dict[key] = value
            
            with open(args.output, 'w') as f:
                json.dump(trip_dict, f, indent=2, default=str)
            print(f"\n💾 Trip plan saved to {args.output}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Planning cancelled by user.")
        return 0
    except Exception as e:
        print(f"\n❌ Error planning trip: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
