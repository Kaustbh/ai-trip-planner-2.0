#!/usr/bin/env python3
"""
Basic Trip Planning Example

This example demonstrates how to use the AI Trip Planner system for basic trip planning.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents import PlanningAgent, ResearchAgent, BudgetAgent
from workflows import HybridWorkflow
from memory import VectorMemory, CustomMemory
from tools import SearchTool, SummarizeTool
from utils.logger import setup_logger


async def basic_trip_planning_example():
    """Basic trip planning example."""
    # Setup logging
    logger = setup_logger("trip_planning_example")
    
    try:
        # Initialize memory
        memory = VectorMemory({
            "memory_type": "semantic",
            "max_items": 1000,
            "ttl": 3600
        })
        
        # Initialize tools
        search_tool = SearchTool()
        summarize_tool = SummarizeTool()
        
        # Initialize agents
        planner = PlanningAgent()
        researcher = ResearchAgent()
        budget_agent = BudgetAgent()
        
        logger.info("Starting basic trip planning example")
        
        # Trip parameters
        destination = "Tokyo, Japan"
        duration = 7
        budget = 5000
        preferences = {
            "interests": ["culture", "food", "technology"],
            "accommodation": "hotel",
            "transportation": "flight"
        }
        
        logger.info(f"Planning trip to {destination} for {duration} days with budget ${budget}")
        
        # Step 1: Research destination
        logger.info("Step 1: Researching destination")
        research_result = await researcher.process_message({
            "message_type": "research_destination",
            "content": {
                "destination": destination,
                "depth": "comprehensive"
            }
        })
        
        if research_result.get("success"):
            logger.info("Destination research completed successfully")
            # Store research data in memory
            await memory.store(
                content=research_result["data"],
                memory_type="semantic",
                importance=0.8,
                tags=["research", "destination", destination.lower()]
            )
        else:
            logger.error(f"Destination research failed: {research_result.get('error')}")
            return
        
        # Step 2: Create trip plan
        logger.info("Step 2: Creating trip plan")
        plan_result = await planner.process_message({
            "message_type": "plan_trip",
            "content": {
                "destination": destination,
                "duration": duration,
                "budget": budget,
                "preferences": preferences
            }
        })
        
        if plan_result.get("success"):
            logger.info("Trip plan created successfully")
            trip_plan = plan_result["plan"]
            
            # Store trip plan in memory
            await memory.store(
                content=trip_plan,
                memory_type="episodic",
                importance=0.9,
                tags=["trip_plan", destination.lower()]
            )
            
            # Display trip plan
            print("\n" + "="*50)
            print("TRIP PLAN")
            print("="*50)
            print(f"Destination: {trip_plan['destination']}")
            print(f"Duration: {trip_plan['duration']} days")
            print(f"Budget: ${trip_plan['budget']}")
            print(f"Status: {trip_plan['status']}")
            
            # Display itinerary
            print("\nItinerary:")
            for day, day_plan in enumerate(trip_plan['itinerary'], 1):
                print(f"\nDay {day}:")
                print(f"  Morning: {', '.join(day_plan['morning'])}")
                print(f"  Afternoon: {', '.join(day_plan['afternoon'])}")
                print(f"  Evening: {', '.join(day_plan['evening'])}")
            
            # Display estimated costs
            print(f"\nEstimated Costs:")
            for category, cost in trip_plan['estimated_costs'].items():
                print(f"  {category.title()}: ${cost:.2f}")
            
        else:
            logger.error(f"Trip planning failed: {plan_result.get('error')}")
            return
        
        # Step 3: Budget analysis
        logger.info("Step 3: Analyzing budget")
        budget_result = await budget_agent.process_message({
            "message_type": "create_budget",
            "content": {
                "trip_id": trip_plan["trip_id"],
                "total_budget": budget,
                "currency": "USD"
            }
        })
        
        if budget_result.get("success"):
            logger.info("Budget analysis completed successfully")
            budget_data = budget_result["budget"]
            
            print(f"\nBudget Analysis:")
            print(f"  Total Budget: ${budget_data['total_budget']}")
            print(f"  Allocated by Category:")
            for category, amount in budget_data['allocated_amounts'].items():
                print(f"    {category.title()}: ${amount:.2f}")
        
        # Step 4: Search for activities
        logger.info("Step 4: Searching for activities")
        activities_result = await researcher.process_message({
            "message_type": "find_activities",
            "content": {
                "destination": destination,
                "interests": preferences["interests"],
                "budget": 100,
                "duration": 4
            }
        })
        
        if activities_result.get("success"):
            logger.info("Activity search completed successfully")
            activities = activities_result["activities"]
            
            print(f"\nRecommended Activities:")
            for activity in activities[:5]:  # Show top 5
                print(f"  - {activity['name']} ({activity['type']})")
                print(f"    Duration: {activity['duration']}")
                print(f"    Price: ${activity['price']}")
                print(f"    Rating: {activity['rating']}/5")
                print()
        
        # Step 5: Summarize trip
        logger.info("Step 5: Summarizing trip")
        trip_summary = f"""
        Trip to {destination} for {duration} days with a budget of ${budget}.
        Interests: {', '.join(preferences['interests'])}.
        Estimated total cost: ${trip_plan['estimated_costs']['total_estimated']:.2f}.
        """
        
        summary_result = await summarize_tool.run({
            "text": trip_summary,
            "operation": "summarize",
            "length": 3
        })
        
        if summary_result.success:
            print("Trip Summary:")
            print(summary_result.data["summary"])
        
        logger.info("Basic trip planning example completed successfully")
        
    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        raise


async def advanced_trip_planning_example():
    """Advanced trip planning with workflow orchestration."""
    logger = setup_logger("advanced_trip_planning")
    
    try:
        # Initialize workflow
        workflow = HybridWorkflow({
            "name": "Advanced Trip Planning",
            "description": "Comprehensive trip planning workflow",
            "execution_mode": "hybrid",
            "max_concurrent_tasks": 5
        })
        
        # Trip parameters
        destination = "Paris, France"
        duration = 10
        budget = 8000
        preferences = {
            "interests": ["art", "history", "food", "romance"],
            "accommodation": "boutique_hotel",
            "transportation": "flight",
            "group_size": 2
        }
        
        logger.info(f"Starting advanced trip planning for {destination}")
        
        # Define workflow tasks
        tasks = [
            {
                "id": "research_destination",
                "name": "Research Destination",
                "task_type": "research",
                "parameters": {
                    "destination": destination,
                    "depth": "comprehensive"
                }
            },
            {
                "id": "research_weather",
                "name": "Research Weather",
                "task_type": "research",
                "parameters": {
                    "destination": destination,
                    "dates": ["2024-06-01", "2024-06-10"]
                }
            },
            {
                "id": "create_itinerary",
                "name": "Create Itinerary",
                "task_type": "planning",
                "parameters": {
                    "destination": destination,
                    "duration": duration,
                    "budget": budget,
                    "preferences": preferences
                },
                "dependencies": ["research_destination"]
            },
            {
                "id": "budget_analysis",
                "name": "Budget Analysis",
                "task_type": "budget",
                "parameters": {
                    "destination": destination,
                    "duration": duration,
                    "budget": budget
                },
                "dependencies": ["create_itinerary"]
            },
            {
                "id": "find_activities",
                "name": "Find Activities",
                "task_type": "research",
                "parameters": {
                    "destination": destination,
                    "interests": preferences["interests"],
                    "budget": 200
                },
                "dependencies": ["research_destination"]
            }
        ]
        
        # Add tasks to workflow
        for task_data in tasks:
            await workflow.add_task(task_data)
        
        # Execute workflow
        logger.info("Executing advanced trip planning workflow")
        result = await workflow.execute()
        
        if result.get("success"):
            logger.info("Advanced trip planning completed successfully")
            print("\n" + "="*60)
            print("ADVANCED TRIP PLANNING RESULTS")
            print("="*60)
            print(f"Workflow Status: {result['status']}")
            print(f"Total Execution Time: {result['total_execution_time']:.2f} seconds")
            print(f"Tasks Completed: {result['task_stats']['completed']}")
            print(f"Tasks Failed: {result['task_stats']['failed']}")
        else:
            logger.error("Advanced trip planning failed")
        
    except Exception as e:
        logger.error(f"Advanced example failed: {str(e)}")
        raise


if __name__ == "__main__":
    print("AI Trip Planner - Examples")
    print("=" * 40)
    
    # Run basic example
    print("\n1. Basic Trip Planning Example")
    print("-" * 30)
    asyncio.run(basic_trip_planning_example())
    
    # Run advanced example
    print("\n2. Advanced Trip Planning Example")
    print("-" * 30)
    asyncio.run(advanced_trip_planning_example())
    
    print("\nExamples completed!")
