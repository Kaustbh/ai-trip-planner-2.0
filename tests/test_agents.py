"""
Tests for AI Trip Planner Agents
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from agents import PlanningAgent, ResearchAgent, ExecutionAgent, MonitoringAgent, BudgetAgent, BookingAgent
from agents.base_agent import AgentConfig, AgentRole, AgentCapabilities


class TestPlanningAgent:
    """Test cases for PlanningAgent."""
    
    @pytest.fixture
    def planning_agent(self):
        """Create a PlanningAgent instance for testing."""
        return PlanningAgent()
    
    @pytest.mark.asyncio
    async def test_create_trip_plan(self, planning_agent):
        """Test creating a trip plan."""
        content = {
            "destination": "Tokyo, Japan",
            "duration": 7,
            "budget": 5000,
            "preferences": {
                "interests": ["culture", "food"],
                "accommodation": "hotel"
            }
        }
        
        result = await planning_agent.process_message({
            "message_type": "plan_trip",
            "content": content
        })
        
        assert result["success"] is True
        assert "plan" in result
        assert result["plan"]["destination"] == "Tokyo, Japan"
        assert result["plan"]["duration"] == 7
        assert result["plan"]["budget"] == 5000
    
    @pytest.mark.asyncio
    async def test_optimize_itinerary(self, planning_agent):
        """Test optimizing an itinerary."""
        content = {
            "itinerary": [
                {"day": 1, "activities": ["morning", "afternoon"]},
                {"day": 2, "activities": ["morning", "afternoon"]}
            ],
            "goals": ["cost", "time"]
        }
        
        result = await planning_agent.process_message({
            "message_type": "optimize_itinerary",
            "content": content
        })
        
        assert result["success"] is True
        assert "optimized_itinerary" in result


class TestResearchAgent:
    """Test cases for ResearchAgent."""
    
    @pytest.fixture
    def research_agent(self):
        """Create a ResearchAgent instance for testing."""
        return ResearchAgent()
    
    @pytest.mark.asyncio
    async def test_research_destination(self, research_agent):
        """Test researching a destination."""
        content = {
            "destination": "Paris, France",
            "depth": "comprehensive"
        }
        
        result = await research_agent.process_message({
            "message_type": "research_destination",
            "content": content
        })
        
        assert result["success"] is True
        assert "data" in result
        assert result["destination"] == "Paris, France"
    
    @pytest.mark.asyncio
    async def test_find_activities(self, research_agent):
        """Test finding activities."""
        content = {
            "destination": "Barcelona, Spain",
            "interests": ["culture", "food"],
            "budget": 100,
            "duration": 4
        }
        
        result = await research_agent.process_message({
            "message_type": "find_activities",
            "content": content
        })
        
        assert result["success"] is True
        assert "activities" in result
        assert len(result["activities"]) > 0


class TestExecutionAgent:
    """Test cases for ExecutionAgent."""
    
    @pytest.fixture
    def execution_agent(self):
        """Create an ExecutionAgent instance for testing."""
        return ExecutionAgent()
    
    @pytest.mark.asyncio
    async def test_execute_task(self, execution_agent):
        """Test executing a task."""
        task = {
            "type": "book_flight",
            "flight_details": {
                "origin": "NYC",
                "destination": "LAX",
                "date": "2024-06-01",
                "passengers": 1
            }
        }
        
        result = await execution_agent.execute_task(task)
        
        assert result["success"] is True
        assert "booking_id" in result
        assert "confirmation_code" in result
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, execution_agent):
        """Test executing a workflow."""
        content = {
            "workflow": {
                "workflow_id": "test_workflow",
                "mode": "sequential",
                "tasks": [
                    {
                        "type": "book_flight",
                        "flight_details": {"origin": "NYC", "destination": "LAX"}
                    },
                    {
                        "type": "book_hotel",
                        "hotel_details": {"location": "LAX", "nights": 3}
                    }
                ]
            }
        }
        
        result = await execution_agent.process_message({
            "message_type": "execute_workflow",
            "content": content
        })
        
        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) == 2


class TestMonitoringAgent:
    """Test cases for MonitoringAgent."""
    
    @pytest.fixture
    def monitoring_agent(self):
        """Create a MonitoringAgent instance for testing."""
        return MonitoringAgent()
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitoring_agent):
        """Test starting monitoring."""
        content = {
            "trip_id": "trip_123",
            "type": "trip"
        }
        
        result = await monitoring_agent.process_message({
            "message_type": "start_monitoring",
            "content": content
        })
        
        assert result["success"] is True
        assert result["trip_id"] == "trip_123"
    
    @pytest.mark.asyncio
    async def test_health_check(self, monitoring_agent):
        """Test performing health check."""
        content = {
            "component": "all"
        }
        
        result = await monitoring_agent.process_message({
            "message_type": "health_check",
            "content": content
        })
        
        assert result["success"] is True
        assert "health_check" in result


class TestBudgetAgent:
    """Test cases for BudgetAgent."""
    
    @pytest.fixture
    def budget_agent(self):
        """Create a BudgetAgent instance for testing."""
        return BudgetAgent()
    
    @pytest.mark.asyncio
    async def test_create_budget(self, budget_agent):
        """Test creating a budget."""
        content = {
            "trip_id": "trip_123",
            "total_budget": 5000,
            "currency": "USD"
        }
        
        result = await budget_agent.process_message({
            "message_type": "create_budget",
            "content": content
        })
        
        assert result["success"] is True
        assert "budget" in result
        assert result["budget"]["total_budget"] == 5000
    
    @pytest.mark.asyncio
    async def test_track_expense(self, budget_agent):
        """Test tracking an expense."""
        # First create a budget
        await budget_agent.process_message({
            "message_type": "create_budget",
            "content": {
                "trip_id": "trip_123",
                "total_budget": 5000,
                "currency": "USD"
            }
        })
        
        # Then track an expense
        content = {
            "trip_id": "trip_123",
            "category": "accommodation",
            "amount": 200,
            "description": "Hotel booking"
        }
        
        result = await budget_agent.process_message({
            "message_type": "track_expense",
            "content": content
        })
        
        assert result["success"] is True
        assert "expense" in result
        assert result["expense"]["amount"] == 200


class TestBookingAgent:
    """Test cases for BookingAgent."""
    
    @pytest.fixture
    def booking_agent(self):
        """Create a BookingAgent instance for testing."""
        return BookingAgent()
    
    @pytest.mark.asyncio
    async def test_book_item(self, booking_agent):
        """Test booking an item."""
        content = {
            "item_type": "flight",
            "booking_details": {
                "origin": "NYC",
                "destination": "LAX",
                "date": "2024-06-01",
                "passengers": 1
            },
            "payment_info": {
                "card_number": "1234567890123456",
                "expiry_date": "12/25",
                "cvv": "123"
            }
        }
        
        result = await booking_agent.process_message({
            "message_type": "book_item",
            "content": content
        })
        
        assert result["success"] is True
        assert "booking" in result
        assert result["booking"]["item_type"] == "flight"
    
    @pytest.mark.asyncio
    async def test_cancel_booking(self, booking_agent):
        """Test cancelling a booking."""
        # First create a booking
        book_result = await booking_agent.process_message({
            "message_type": "book_item",
            "content": {
                "item_type": "hotel",
                "booking_details": {"location": "LAX", "nights": 3}
            }
        })
        
        booking_id = book_result["booking"]["booking_id"]
        
        # Then cancel it
        content = {
            "booking_id": booking_id,
            "reason": "User requested"
        }
        
        result = await booking_agent.process_message({
            "message_type": "cancel_booking",
            "content": content
        })
        
        assert result["success"] is True
        assert result["booking_id"] == booking_id


class TestBaseAgent:
    """Test cases for BaseAgent functionality."""
    
    def test_agent_config(self):
        """Test agent configuration."""
        config = AgentConfig(
            name="Test Agent",
            role=AgentRole.PLANNER,
            capabilities=AgentCapabilities(can_plan=True)
        )
        
        assert config.name == "Test Agent"
        assert config.role == AgentRole.PLANNER
        assert config.capabilities.can_plan is True
    
    def test_agent_status(self):
        """Test agent status management."""
        from agents.base_agent import AgentStatus
        
        agent = PlanningAgent()
        
        assert agent.status == AgentStatus.IDLE
        assert agent.agent_id is not None
        assert agent.config.name == "Trip Planner"
    
    @pytest.mark.asyncio
    async def test_agent_memory(self):
        """Test agent memory functionality."""
        agent = PlanningAgent()
        
        # Update memory
        agent.update_memory({
            "type": "test",
            "data": "test_data"
        })
        
        # Get memory
        memory = agent.get_memory()
        assert len(memory) == 1
        assert memory[0]["content"]["type"] == "test"
    
    @pytest.mark.asyncio
    async def test_agent_tools(self):
        """Test agent tool management."""
        agent = PlanningAgent()
        
        # Add tool
        mock_tool = Mock()
        agent.add_tool("test_tool", mock_tool)
        
        # Get tool
        retrieved_tool = agent.get_tool("test_tool")
        assert retrieved_tool == mock_tool
        
        # Get non-existent tool
        non_existent = agent.get_tool("non_existent")
        assert non_existent is None


if __name__ == "__main__":
    pytest.main([__file__])
