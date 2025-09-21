#!/usr/bin/env python3
"""
Agent Communication Example

This example demonstrates how agents communicate with each other using different protocols.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents import PlanningAgent, ResearchAgent, ExecutionAgent, MonitoringAgent
from protocols import MCPProtocol, A2AProtocol, HybridProtocol
from memory import ConversationMemory
from utils.logger import setup_logger


async def agent_communication_example():
    """Demonstrate agent communication patterns."""
    logger = setup_logger("agent_communication")
    
    try:
        # Initialize memory for conversation tracking
        memory = ConversationMemory({
            "memory_type": "episodic",
            "max_items": 1000
        })
        
        # Initialize agents
        planner = PlanningAgent()
        researcher = ResearchAgent()
        executor = ExecutionAgent()
        monitor = MonitoringAgent()
        
        # Initialize protocols
        mcp_protocol = MCPProtocol({
            "name": "MCP Protocol",
            "server_url": "http://localhost:8000",
            "timeout": 30
        })
        
        a2a_protocol = A2AProtocol({
            "name": "A2A Protocol",
            "discovery_enabled": True,
            "heartbeat_interval": 10
        })
        
        hybrid_protocol = HybridProtocol({
            "name": "Hybrid Protocol",
            "mcp_config": mcp_protocol.config,
            "a2a_config": a2a_protocol.config,
            "routing_strategy": "intelligent"
        })
        
        # Start protocols
        await mcp_protocol.start()
        await a2a_protocol.start()
        await hybrid_protocol.start()
        
        # Register agents with protocols
        await a2a_protocol.register_agent("planner", {
            "name": "Trip Planner",
            "capabilities": ["planning", "research"],
            "status": "available"
        })
        
        await a2a_protocol.register_agent("researcher", {
            "name": "Travel Researcher",
            "capabilities": ["research", "search"],
            "status": "available"
        })
        
        await a2a_protocol.register_agent("executor", {
            "name": "Execution Agent",
            "capabilities": ["execution", "booking"],
            "status": "available"
        })
        
        await a2a_protocol.register_agent("monitor", {
            "name": "Monitoring Agent",
            "capabilities": ["monitoring", "alerting"],
            "status": "available"
        })
        
        logger.info("Agent communication example started")
        
        # Example 1: Direct agent-to-agent communication
        print("\n" + "="*50)
        print("EXAMPLE 1: Direct Agent Communication")
        print("="*50)
        
        # Planner requests research from researcher
        research_request = {
            "message_type": "research_destination",
            "content": {
                "destination": "Barcelona, Spain",
                "depth": "comprehensive"
            }
        }
        
        print("Planner requesting research from Researcher...")
        research_result = await researcher.process_message(research_request)
        
        if research_result.get("success"):
            print("✓ Research completed successfully")
            print(f"  Found {len(research_result['data'])} data categories")
        else:
            print(f"✗ Research failed: {research_result.get('error')}")
        
        # Example 2: Protocol-based communication
        print("\n" + "="*50)
        print("EXAMPLE 2: Protocol-Based Communication")
        print("="*50)
        
        # Send message through A2A protocol
        message = a2a_protocol.create_message(
            sender="planner",
            recipient="researcher",
            content={
                "message_type": "find_activities",
                "destination": "Barcelona, Spain",
                "interests": ["culture", "food", "architecture"]
            },
            message_type="research_request"
        )
        
        print("Sending message through A2A protocol...")
        success = await a2a_protocol.send_message(message)
        
        if success:
            print("✓ Message sent successfully through A2A protocol")
        else:
            print("✗ Failed to send message through A2A protocol")
        
        # Example 3: Tool calling through MCP protocol
        print("\n" + "="*50)
        print("EXAMPLE 3: Tool Calling Through MCP Protocol")
        print("="*50)
        
        # Call search tool through MCP
        tool_result = await mcp_protocol.call_tool(
            tool_name="search",
            parameters={
                "query": "Barcelona attractions",
                "limit": 5
            },
            caller="researcher"
        )
        
        if tool_result.get("success"):
            print("✓ Tool call successful through MCP protocol")
            print(f"  Found {len(tool_result.get('result', []))} search results")
        else:
            print(f"✗ Tool call failed: {tool_result.get('error')}")
        
        # Example 4: Broadcast communication
        print("\n" + "="*50)
        print("EXAMPLE 4: Broadcast Communication")
        print("="*50)
        
        # Broadcast message to all agents with research capability
        broadcast_result = await a2a_protocol.broadcast_to_capability(
            sender="planner",
            capability="research",
            content={
                "message_type": "research_update",
                "destination": "Barcelona, Spain",
                "status": "completed"
            },
            message_type="broadcast"
        )
        
        print(f"Broadcast sent to {len(broadcast_result)} agents")
        print(f"Success rate: {sum(broadcast_result) / len(broadcast_result) * 100:.1f}%")
        
        # Example 5: Hybrid protocol routing
        print("\n" + "="*50)
        print("EXAMPLE 5: Hybrid Protocol Routing")
        print("="*50)
        
        # Send high-priority message through hybrid protocol
        priority_message = hybrid_protocol.create_message(
            sender="planner",
            recipient="executor",
            content={
                "message_type": "urgent_booking",
                "booking_type": "flight",
                "urgency": "high"
            },
            message_type="booking_request",
            priority=3  # High priority
        )
        
        print("Sending high-priority message through hybrid protocol...")
        success = await hybrid_protocol.send_message(priority_message)
        
        if success:
            print("✓ High-priority message routed successfully")
        else:
            print("✗ Failed to route high-priority message")
        
        # Example 6: Conversation memory tracking
        print("\n" + "="*50)
        print("EXAMPLE 6: Conversation Memory Tracking")
        print("="*50)
        
        # Store conversation in memory
        conversation_data = {
            "conversation_id": "trip_planning_001",
            "participants": ["planner", "researcher", "executor"],
            "topic": "Barcelona trip planning",
            "messages": [
                {
                    "sender": "planner",
                    "content": "I need research on Barcelona",
                    "timestamp": "2024-01-15T10:00:00Z"
                },
                {
                    "sender": "researcher",
                    "content": "Research completed, found 15 attractions",
                    "timestamp": "2024-01-15T10:05:00Z"
                }
            ]
        }
        
        memory_id = await memory.store(
            content=conversation_data,
            memory_type="episodic",
            importance=0.8,
            tags=["conversation", "barcelona", "trip_planning"]
        )
        
        print(f"✓ Conversation stored in memory with ID: {memory_id}")
        
        # Retrieve conversation
        retrieved_conversation = await memory.get_conversation("trip_planning_001")
        print(f"✓ Retrieved conversation with {len(retrieved_conversation['messages'])} messages")
        
        # Example 7: Protocol statistics
        print("\n" + "="*50)
        print("EXAMPLE 7: Protocol Statistics")
        print("="*50)
        
        # Get protocol statistics
        mcp_stats = mcp_protocol.get_stats()
        a2a_stats = a2a_protocol.get_stats()
        hybrid_stats = hybrid_protocol.get_stats()
        
        print("MCP Protocol Stats:")
        print(f"  Messages sent: {mcp_stats['stats']['messages_sent']}")
        print(f"  Messages received: {mcp_stats['stats']['messages_received']}")
        print(f"  Messages failed: {mcp_stats['stats']['messages_failed']}")
        
        print("\nA2A Protocol Stats:")
        print(f"  Messages sent: {a2a_stats['stats']['messages_sent']}")
        print(f"  Active connections: {a2a_stats['active_connections']}")
        print(f"  Registered agents: {len(a2a_protocol.get_agent_registry())}")
        
        print("\nHybrid Protocol Stats:")
        print(f"  MCP messages: {hybrid_stats['routing_stats']['mcp_messages']}")
        print(f"  A2A messages: {hybrid_stats['routing_stats']['a2a_messages']}")
        print(f"  Fallback messages: {hybrid_stats['routing_stats']['fallback_messages']}")
        
        # Cleanup
        await mcp_protocol.stop()
        await a2a_protocol.stop()
        await hybrid_protocol.stop()
        
        logger.info("Agent communication example completed successfully")
        
    except Exception as e:
        logger.error(f"Agent communication example failed: {str(e)}")
        raise


if __name__ == "__main__":
    print("AI Trip Planner - Agent Communication Example")
    print("=" * 50)
    
    asyncio.run(agent_communication_example())
    
    print("\nAgent communication example completed!")
