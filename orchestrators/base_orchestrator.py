"""
Base Orchestrator Class

Defines the common interface for all orchestrator implementations in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid
from datetime import datetime
import json

from pydantic import BaseModel, Field


class OrchestratorType(Enum):
    """Orchestrator type enumeration."""
    LANGGRAPH = "langgraph"
    CREWAI = "crewai"
    CUSTOM = "custom"
    HYBRID = "hybrid"


class OrchestratorStatus(Enum):
    """Orchestrator status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentTask:
    """Agent task definition."""
    id: str
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: int = 30
    retry_attempts: int = 3
    dependencies: List[str] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now()


class OrchestratorConfig(BaseModel):
    """Configuration for an orchestrator."""
    orchestrator_type: OrchestratorType
    name: str
    description: str
    max_concurrent_agents: int = 10
    task_timeout: int = 300
    retry_attempts: int = 3
    monitoring_enabled: bool = True
    logging_enabled: bool = True
    auto_scaling: bool = False
    load_balancing: bool = True


class BaseOrchestrator(ABC):
    """
    Base class for all orchestrator implementations.
    
    Provides common functionality for:
    - Agent management
    - Task distribution
    - Load balancing
    - Monitoring
    - Error handling
    """
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.orchestrator_id = str(uuid.uuid4())
        self.status = OrchestratorStatus.IDLE
        self.agents = {}
        self.active_tasks = {}
        self.task_queue = asyncio.Queue()
        self.completed_tasks = []
        self.failed_tasks = []
        self.metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_agents": 0,
            "average_task_time": 0.0
        }
        
    @abstractmethod
    async def start(self) -> None:
        """Start the orchestrator."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the orchestrator."""
        pass
    
    @abstractmethod
    async def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_info: Agent configuration and capabilities
            
        Returns:
            True if registration successful
        """
        pass
    
    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the orchestrator.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if unregistration successful
        """
        pass
    
    @abstractmethod
    async def submit_task(self, task: AgentTask) -> str:
        """
        Submit a task to the orchestrator.
        
        Args:
            task: Task to execute
            
        Returns:
            Task ID
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status information
        """
        pass
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            "agent_id": agent_id,
            "status": agent.get("status", "unknown"),
            "capabilities": agent.get("capabilities", []),
            "active_tasks": agent.get("active_tasks", 0),
            "total_tasks": agent.get("total_tasks", 0),
            "last_activity": agent.get("last_activity")
        }
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get overall orchestrator status."""
        return {
            "orchestrator_id": self.orchestrator_id,
            "status": self.status.value,
            "config": self.config.dict(),
            "metrics": self.metrics.copy(),
            "registered_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks)
        }
    
    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents."""
        available_agents = []
        
        for agent_id, agent_info in self.agents.items():
            if agent_info.get("status") == "available":
                available_agents.append({
                    "agent_id": agent_id,
                    "capabilities": agent_info.get("capabilities", []),
                    "load": agent_info.get("active_tasks", 0)
                })
        
        return available_agents
    
    async def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get capabilities of a specific agent."""
        if agent_id not in self.agents:
            return []
        
        return self.agents[agent_id].get("capabilities", [])
    
    async def find_agents_by_capability(self, capability: str) -> List[str]:
        """Find agents that have a specific capability."""
        matching_agents = []
        
        for agent_id, agent_info in self.agents.items():
            capabilities = agent_info.get("capabilities", [])
            if capability in capabilities:
                matching_agents.append(agent_id)
        
        return matching_agents
    
    async def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task execution history."""
        all_tasks = self.completed_tasks + self.failed_tasks
        all_tasks.sort(key=lambda x: x.get("completed_at", x.get("created_at", "")), reverse=True)
        return all_tasks[:limit]
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        total_tasks = self.metrics["total_tasks"]
        completed_tasks = self.metrics["completed_tasks"]
        failed_tasks = self.metrics["failed_tasks"]
        
        success_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0
        failure_rate = (failed_tasks / total_tasks) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_task_time": self.metrics["average_task_time"],
            "active_agents": self.metrics["active_agents"],
            "task_throughput": completed_tasks / max(1, self._get_uptime_seconds())
        }
    
    def _get_uptime_seconds(self) -> float:
        """Get orchestrator uptime in seconds."""
        # This would be calculated based on start time
        return 3600.0  # Mock value
    
    async def _update_metrics(self, task: AgentTask) -> None:
        """Update orchestrator metrics."""
        self.metrics["total_tasks"] += 1
        
        if task.status == "completed":
            self.metrics["completed_tasks"] += 1
            self.completed_tasks.append({
                "task_id": task.id,
                "agent_id": task.agent_id,
                "task_type": task.task_type,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "execution_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else 0
            })
        elif task.status == "failed":
            self.metrics["failed_tasks"] += 1
            self.failed_tasks.append({
                "task_id": task.id,
                "agent_id": task.agent_id,
                "task_type": task.task_type,
                "error": task.error,
                "created_at": task.created_at.isoformat(),
                "failed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        
        # Update average task time
        if task.completed_at and task.started_at:
            execution_time = (task.completed_at - task.started_at).total_seconds()
            current_avg = self.metrics["average_task_time"]
            total_completed = self.metrics["completed_tasks"]
            
            if total_completed > 0:
                self.metrics["average_task_time"] = ((current_avg * (total_completed - 1)) + execution_time) / total_completed
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log orchestrator event."""
        if not self.config.logging_enabled:
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator_id": self.orchestrator_id,
            "event_type": event_type,
            "data": data
        }
        
        # In a real implementation, this would write to a log file or database
        print(f"ORCHESTRATOR EVENT: {event_type} - {json.dumps(data)}")
    
    def __str__(self) -> str:
        return f"{self.config.name} ({self.status.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.orchestrator_id}, status={self.status.value})>"
