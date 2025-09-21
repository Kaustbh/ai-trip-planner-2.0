"""
Base Workflow Class

Defines the common interface for all workflow implementations in the system.
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


class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """Workflow execution mode."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


@dataclass
class WorkflowTask:
    """Workflow task definition."""
    id: str
    name: str
    task_type: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class WorkflowConfig(BaseModel):
    """Configuration for a workflow."""
    name: str
    description: str
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    timeout: int = 300  # 5 minutes
    max_concurrent_tasks: int = 5
    retry_failed_tasks: bool = True
    continue_on_failure: bool = False
    auto_cleanup: bool = True
    logging_enabled: bool = True


class BaseWorkflow(ABC):
    """
    Base class for all workflow implementations.
    
    Provides common functionality for:
    - Task management
    - Execution control
    - Error handling
    - Progress tracking
    - Result aggregation
    """
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.workflow_id = str(uuid.uuid4())
        self.status = WorkflowStatus.PENDING
        self.tasks = {}
        self.task_dependencies = {}
        self.execution_log = []
        self.results = {}
        self.errors = {}
        self.started_at = None
        self.completed_at = None
        self.total_execution_time = 0.0
        
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Returns:
            Workflow execution results
        """
        pass
    
    @abstractmethod
    async def add_task(self, task: WorkflowTask) -> str:
        """
        Add a task to the workflow.
        
        Args:
            task: Task definition
            
        Returns:
            Task ID
        """
        pass
    
    @abstractmethod
    async def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the workflow.
        
        Args:
            task_id: ID of the task to remove
            
        Returns:
            True if removed successfully
        """
        pass
    
    async def start(self) -> None:
        """Start workflow execution."""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()
        
        # Log workflow start
        await self._log_event("workflow_started", {
            "workflow_id": self.workflow_id,
            "config": self.config.dict()
        })
    
    async def pause(self) -> None:
        """Pause workflow execution."""
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.PAUSED
            await self._log_event("workflow_paused", {"workflow_id": self.workflow_id})
    
    async def resume(self) -> None:
        """Resume paused workflow."""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            await self._log_event("workflow_resumed", {"workflow_id": self.workflow_id})
    
    async def cancel(self) -> None:
        """Cancel workflow execution."""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.now()
        
        # Cancel all pending tasks
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
        
        await self._log_event("workflow_cancelled", {"workflow_id": self.workflow_id})
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        task_stats = {
            "total": len(self.tasks),
            "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "running": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED])
        }
        
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "config": self.config.dict(),
            "task_stats": task_stats,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_execution_time": self.total_execution_time,
            "progress_percentage": self._calculate_progress()
        }
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "task_id": task_id,
            "name": task.name,
            "status": task.status.value,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "execution_time": task.execution_time,
            "error": task.error
        }
    
    async def get_results(self) -> Dict[str, Any]:
        """Get workflow results."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "results": self.results.copy(),
            "errors": self.errors.copy(),
            "execution_log": self.execution_log[-100:]  # Last 100 events
        }
    
    async def _execute_task(self, task: WorkflowTask) -> Any:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # Log task start
            await self._log_event("task_started", {
                "task_id": task.id,
                "task_name": task.name,
                "task_type": task.task_type
            })
            
            # Execute task based on type
            result = await self._run_task(task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            task.execution_time = (task.completed_at - task.started_at).total_seconds()
            
            # Store result
            self.results[task.id] = result
            
            # Log task completion
            await self._log_event("task_completed", {
                "task_id": task.id,
                "execution_time": task.execution_time
            })
            
            return result
            
        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            task.execution_time = (task.completed_at - task.started_at).total_seconds()
            
            # Store error
            self.errors[task.id] = str(e)
            
            # Log task failure
            await self._log_event("task_failed", {
                "task_id": task.id,
                "error": str(e)
            })
            
            if not self.config.continue_on_failure:
                raise
            
            return None
    
    async def _run_task(self, task: WorkflowTask) -> Any:
        """Run a specific task based on its type."""
        # This is a placeholder - subclasses should implement specific task execution
        await asyncio.sleep(0.1)  # Simulate task execution
        
        return {
            "task_id": task.id,
            "task_type": task.task_type,
            "status": "completed",
            "result": f"Mock result for {task.name}"
        }
    
    async def _check_dependencies(self, task_id: str) -> bool:
        """Check if all task dependencies are satisfied."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _get_ready_tasks(self) -> List[WorkflowTask]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready_tasks = []
        
        for task in self.tasks.values():
            if (task.status == TaskStatus.PENDING and 
                await self._check_dependencies(task.id)):
                ready_tasks.append(task)
        
        return ready_tasks
    
    def _calculate_progress(self) -> float:
        """Calculate workflow progress percentage."""
        if not self.tasks:
            return 0.0
        
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        total_tasks = len(self.tasks)
        
        return (completed_tasks / total_tasks) * 100
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log workflow event."""
        if not self.config.logging_enabled:
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": self.workflow_id,
            "event_type": event_type,
            "data": data
        }
        
        self.execution_log.append(event)
    
    async def _cleanup(self) -> None:
        """Clean up workflow resources."""
        if not self.config.auto_cleanup:
            return
        
        # Clear completed task results after some time
        # This is a placeholder for cleanup logic
        pass
    
    def __str__(self) -> str:
        return f"{self.config.name} ({self.status.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.workflow_id}, status={self.status.value})>"
