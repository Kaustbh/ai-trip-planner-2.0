#!/usr/bin/env python3
"""
Run Agent Script

CLI script to run and interact with AI Trip Planner agents.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents import PlanningAgent, ResearchAgent, ExecutionAgent, MonitoringAgent, BudgetAgent, BookingAgent
from protocols import HybridProtocol
from workflows import HybridWorkflow
from orchestrators import CustomOrchestrator
from memory import VectorMemory, ConversationMemory, CustomMemory
from tools import SearchTool, DatabaseTool, SummarizeTool
from services import LLMService
from utils.logger import setup_logger
from utils.config_loader import load_config


class TripPlannerCLI:
    """Command-line interface for AI Trip Planner."""
    
    def __init__(self):
        self.logger = setup_logger("trip_planner_cli")
        self.agents = {}
        self.orchestrator = None
        self.memory = None
        self.tools = {}
        
    async def initialize(self, config_path: Optional[str] = None):
        """Initialize the trip planner system."""
        try:
            # Load configuration
            config = load_config(config_path)
            
            # Initialize memory
            self.memory = VectorMemory(config.get("memory", {}))
            
            # Initialize tools
            self.tools["search"] = SearchTool()
            self.tools["database"] = DatabaseTool()
            self.tools["summarize"] = SummarizeTool()
            
            # Initialize agents
            self.agents["planner"] = PlanningAgent()
            self.agents["researcher"] = ResearchAgent()
            self.agents["executor"] = ExecutionAgent()
            self.agents["monitor"] = MonitoringAgent()
            self.agents["budget"] = BudgetAgent()
            self.agents["booker"] = BookingAgent()
            
            # Initialize orchestrator
            self.orchestrator = CustomOrchestrator()
            
            # Start orchestrator
            await self.orchestrator.start()
            
            # Register agents
            for agent_id, agent in self.agents.items():
                await self.orchestrator.register_agent(agent_id, {
                    "name": agent.config.name,
                    "capabilities": list(agent.config.capabilities.__dict__.keys()),
                    "status": "available"
                })
            
            self.logger.info("Trip planner system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {str(e)}")
            raise
    
    async def plan_trip(self, destination: str, duration: int, budget: float, 
                       preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a trip using the agent system."""
        try:
            # Create trip planning workflow
            workflow = HybridWorkflow({
                "name": "Trip Planning",
                "description": "Plan a complete trip",
                "execution_mode": "hybrid",
                "max_concurrent_tasks": 5
            })
            
            # Add tasks to workflow
            tasks = [
                {
                    "id": "research_destination",
                    "name": "Research Destination",
                    "task_type": "research",
                    "agent_id": "researcher",
                    "parameters": {
                        "destination": destination,
                        "duration": duration,
                        "preferences": preferences
                    }
                },
                {
                    "id": "create_itinerary",
                    "name": "Create Itinerary",
                    "task_type": "planning",
                    "agent_id": "planner",
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
                    "agent_id": "budget",
                    "parameters": {
                        "destination": destination,
                        "duration": duration,
                        "budget": budget
                    },
                    "dependencies": ["create_itinerary"]
                },
                {
                    "id": "book_accommodations",
                    "name": "Book Accommodations",
                    "task_type": "booking",
                    "agent_id": "booker",
                    "parameters": {
                        "destination": destination,
                        "duration": duration,
                        "budget": budget
                    },
                    "dependencies": ["budget_analysis"]
                }
            ]
            
            # Add tasks to workflow
            for task_data in tasks:
                await workflow.add_task(task_data)
            
            # Execute workflow
            result = await workflow.execute()
            
            return {
                "success": True,
                "workflow_result": result,
                "trip_plan": result.get("results", {})
            }
            
        except Exception as e:
            self.logger.error(f"Trip planning failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def monitor_trip(self, trip_id: str) -> Dict[str, Any]:
        """Monitor an existing trip."""
        try:
            # Get monitoring agent
            monitor = self.agents["monitor"]
            
            # Start monitoring
            result = await monitor.process_message({
                "message_type": "start_monitoring",
                "content": {
                    "trip_id": trip_id,
                    "type": "trip"
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Trip monitoring failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recommendations(self, destination: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations for a destination."""
        try:
            # Get research agent
            researcher = self.agents["researcher"]
            
            # Get recommendations
            result = await researcher.process_message({
                "message_type": "find_activities",
                "content": {
                    "destination": destination,
                    "interests": preferences.get("interests", []),
                    "budget": preferences.get("budget", 100),
                    "duration": preferences.get("duration", 4)
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Getting recommendations failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.orchestrator:
                await self.orchestrator.stop()
            
            for agent in self.agents.values():
                await agent.stop()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="AI Trip Planner CLI")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--destination", required=True, help="Trip destination")
    parser.add_argument("--duration", type=int, default=7, help="Trip duration in days")
    parser.add_argument("--budget", type=float, default=5000, help="Trip budget")
    parser.add_argument("--interests", nargs="+", default=["culture", "food"], help="Travel interests")
    parser.add_argument("--action", choices=["plan", "monitor", "recommend"], default="plan", help="Action to perform")
    parser.add_argument("--trip-id", help="Trip ID for monitoring")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = TripPlannerCLI()
    
    try:
        # Initialize system
        await cli.initialize(args.config)
        
        # Prepare preferences
        preferences = {
            "interests": args.interests,
            "budget": args.budget,
            "duration": args.duration
        }
        
        # Execute action
        if args.action == "plan":
            result = await cli.plan_trip(args.destination, args.duration, args.budget, preferences)
        elif args.action == "monitor":
            if not args.trip_id:
                print("Error: --trip-id is required for monitoring")
                sys.exit(1)
            result = await cli.monitor_trip(args.trip_id)
        elif args.action == "recommend":
            result = await cli.get_recommendations(args.destination, preferences)
        
        # Output result
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Result saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
