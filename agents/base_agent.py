"""
Base Agent Class

Defines the common interface and functionality for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from langchain.schema import BaseMessage


class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentRole(Enum):
    """Agent role enumeration."""
    PLANNER = "planner"
    RESEARCHER = "researcher"
    EXECUTOR = "executor"
    MONITOR = "monitor"
    BUDGET = "budget"
    BOOKER = "booker"


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    id: str
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: datetime
    message_type: str
    priority: int = 1


class AgentCapabilities(BaseModel):
    """Defines what an agent can do."""
    can_plan: bool = False
    can_research: bool = False
    can_execute: bool = False
    can_monitor: bool = False
    can_budget: bool = False
    can_book: bool = False
    can_learn: bool = False
    max_concurrent_tasks: int = 1
    supported_languages: List[str] = ["en"]


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    role: AgentRole
    capabilities: AgentCapabilities
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_attempts: int = 3
    memory_enabled: bool = True
    learning_enabled: bool = False


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides common functionality for:
    - Message handling
    - State management
    - Error handling
    - Memory management
    - Tool integration
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.IDLE
        self.memory = []
        self.tools = {}
        self.message_queue = asyncio.Queue()
        self.current_task = None
        self.error_count = 0
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Process an incoming message and return a response.
        
        Args:
            message: The message to process
            
        Returns:
            Response dictionary
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task.
        
        Args:
            task: Task definition
            
        Returns:
            Task result
        """
        pass
    
    async def send_message(self, recipient: str, content: Dict[str, Any], 
                          message_type: str = "task", priority: int = 1) -> str:
        """Send a message to another agent."""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient=recipient,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            priority=priority
        )
        
        # In a real implementation, this would go through a message broker
        # For now, we'll simulate it
        return message.id
    
    async def receive_message(self, message: AgentMessage) -> None:
        """Receive and queue a message for processing."""
        await self.message_queue.put(message)
        self.last_activity = datetime.now()
    
    async def start(self) -> None:
        """Start the agent's main processing loop."""
        self.status = AgentStatus.RUNNING
        while self.status == AgentStatus.RUNNING:
            try:
                # Process messages from queue
                if not self.message_queue.empty():
                    message = await asyncio.wait_for(
                        self.message_queue.get(), 
                        timeout=1.0
                    )
                    await self.process_message(message)
                
                # Process current task if any
                if self.current_task:
                    await self.execute_task(self.current_task)
                    
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                await self.handle_error(e)
    
    async def stop(self) -> None:
        """Stop the agent."""
        self.status = AgentStatus.IDLE
        self.current_task = None
    
    async def handle_error(self, error: Exception) -> None:
        """Handle errors that occur during agent operation."""
        self.error_count += 1
        self.status = AgentStatus.ERROR
        
        # Log error
        print(f"Agent {self.agent_id} error: {str(error)}")
        
        # Implement retry logic
        if self.error_count < self.config.retry_attempts:
            await asyncio.sleep(2 ** self.error_count)  # Exponential backoff
            self.status = AgentStatus.RUNNING
        else:
            # Max retries exceeded, stop agent
            await self.stop()
    
    def add_tool(self, name: str, tool: Any) -> None:
        """Add a tool to the agent's toolkit."""
        self.tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def update_memory(self, content: Dict[str, Any]) -> None:
        """Update agent memory with new information."""
        if self.config.memory_enabled:
            self.memory.append({
                "timestamp": datetime.now(),
                "content": content
            })
    
    def get_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memory entries."""
        return self.memory[-limit:] if self.memory else []
    
    def clear_memory(self) -> None:
        """Clear agent memory."""
        self.memory.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "role": self.config.role.value,
            "status": self.status.value,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "memory_size": len(self.memory),
            "tools": list(self.tools.keys())
        }
    
    def __str__(self) -> str:
        return f"{self.config.name} ({self.config.role.value}) - {self.status.value}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, role={self.config.role.value})>"
