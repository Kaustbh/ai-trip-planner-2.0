"""
Sequential Workflow Implementation

Workflow that executes tasks in sequential order, one after another.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowConfig, WorkflowTask, WorkflowStatus, TaskStatus


class SequentialWorkflow(BaseWorkflow):
    """
    Sequential workflow implementation.
    
    Features:
    - Tasks execute one after another
    - Dependency management
    - Error handling and retry logic
    - Progress tracking
    """
    
    def __init__(self, config: WorkflowConfig):
        super().__init__(config)
        self.current_task_index = 0
        self.execution_order = []
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the sequential workflow."""
        await self.start()
        
        try:
            # Build execution order based on dependencies
            await self._build_execution_order()
            
            # Execute tasks in order
            for task_id in self.execution_order:
                if self.status != WorkflowStatus.RUNNING:
                    break
                
                task = self.tasks[task_id]
                await self._execute_task(task)
                
                # Check if task failed and we should stop
                if task.status == TaskStatus.FAILED and not self.config.continue_on_failure:
                    self.status = WorkflowStatus.FAILED
                    break
            
            # Mark workflow as completed if all tasks finished successfully
            if self.status == WorkflowStatus.RUNNING:
                self.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            await self._log_event("workflow_failed", {
                "error": str(e),
                "workflow_id": self.workflow_id
            })
        
        finally:
            self.completed_at = datetime.now()
            if self.started_at:
                self.total_execution_time = (self.completed_at - self.started_at).total_seconds()
            
            await self._log_event("workflow_completed", {
                "workflow_id": self.workflow_id,
                "status": self.status.value,
                "total_execution_time": self.total_execution_time
            })
        
        return await self.get_results()
    
    async def add_task(self, task: WorkflowTask) -> str:
        """Add a task to the sequential workflow."""
        self.tasks[task.id] = task
        
        # Rebuild execution order
        await self._build_execution_order()
        
        return task.id
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove a task from the sequential workflow."""
        if task_id not in self.tasks:
            return False
        
        # Remove task
        del self.tasks[task_id]
        
        # Update dependencies of remaining tasks
        for task in self.tasks.values():
            if task_id in task.dependencies:
                task.dependencies.remove(task_id)
        
        # Rebuild execution order
        await self._build_execution_order()
        
        return True
    
    async def _build_execution_order(self) -> None:
        """Build the execution order based on task dependencies."""
        self.execution_order = []
        visited = set()
        temp_visited = set()
        
        def visit(task_id: str) -> None:
            if task_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving task {task_id}")
            
            if task_id in visited:
                return
            
            temp_visited.add(task_id)
            
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for dep_id in task.dependencies:
                    visit(dep_id)
            
            temp_visited.remove(task_id)
            visited.add(task_id)
            self.execution_order.append(task_id)
        
        # Visit all tasks
        for task_id in self.tasks.keys():
            if task_id not in visited:
                visit(task_id)
    
    async def get_next_task(self) -> Optional[WorkflowTask]:
        """Get the next task to execute."""
        if self.current_task_index >= len(self.execution_order):
            return None
        
        task_id = self.execution_order[self.current_task_index]
        task = self.tasks[task_id]
        
        # Check if task is ready to execute
        if await self._check_dependencies(task_id):
            return task
        
        return None
    
    async def complete_current_task(self) -> None:
        """Mark current task as completed and move to next."""
        if self.current_task_index < len(self.execution_order):
            self.current_task_index += 1
    
    async def get_execution_progress(self) -> Dict[str, Any]:
        """Get detailed execution progress."""
        total_tasks = len(self.execution_order)
        completed_tasks = self.current_task_index
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "current_task_index": self.current_task_index,
            "progress_percentage": progress_percentage,
            "execution_order": self.execution_order,
            "current_task": self.execution_order[self.current_task_index] if self.current_task_index < len(self.execution_order) else None
        }
    
    async def skip_current_task(self) -> bool:
        """Skip the current task and move to next."""
        if self.current_task_index >= len(self.execution_order):
            return False
        
        task_id = self.execution_order[self.current_task_index]
        task = self.tasks[task_id]
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.SKIPPED
            task.completed_at = datetime.now()
            
            await self._log_event("task_skipped", {
                "task_id": task_id,
                "task_name": task.name
            })
            
            self.current_task_index += 1
            return True
        
        return False
    
    async def retry_current_task(self) -> bool:
        """Retry the current task."""
        if self.current_task_index >= len(self.execution_order):
            return False
        
        task_id = self.execution_order[self.current_task_index]
        task = self.tasks[task_id]
        
        if task.status == TaskStatus.FAILED and task.retry_attempts > 0:
            task.retry_attempts -= 1
            task.status = TaskStatus.PENDING
            task.error = None
            task.started_at = None
            task.completed_at = None
            task.execution_time = 0.0
            
            await self._log_event("task_retry", {
                "task_id": task_id,
                "remaining_attempts": task.retry_attempts
            })
            
            return True
        
        return False
    
    async def jump_to_task(self, task_id: str) -> bool:
        """Jump to a specific task in the execution order."""
        if task_id not in self.execution_order:
            return False
        
        # Find task index
        task_index = self.execution_order.index(task_id)
        
        # Skip all tasks before this one
        for i in range(self.current_task_index, task_index):
            skip_task_id = self.execution_order[i]
            skip_task = self.tasks[skip_task_id]
            
            if skip_task.status == TaskStatus.PENDING:
                skip_task.status = TaskStatus.SKIPPED
                skip_task.completed_at = datetime.now()
                
                await self._log_event("task_skipped", {
                    "task_id": skip_task_id,
                    "reason": "jumped_to_later_task"
                })
        
        self.current_task_index = task_index
        return True
    
    async def get_task_dependencies(self, task_id: str) -> List[str]:
        """Get dependencies for a specific task."""
        if task_id not in self.tasks:
            return []
        
        return self.tasks[task_id].dependencies.copy()
    
    async def add_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Add a dependency to a task."""
        if task_id not in self.tasks or dependency_id not in self.tasks:
            return False
        
        if dependency_id not in self.tasks[task_id].dependencies:
            self.tasks[task_id].dependencies.append(dependency_id)
            await self._build_execution_order()
            return True
        
        return False
    
    async def remove_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Remove a dependency from a task."""
        if task_id not in self.tasks:
            return False
        
        if dependency_id in self.tasks[task_id].dependencies:
            self.tasks[task_id].dependencies.remove(dependency_id)
            await self._build_execution_order()
            return True
        
        return False
    
    def get_execution_order(self) -> List[str]:
        """Get the current execution order."""
        return self.execution_order.copy()
    
    def get_current_task_id(self) -> Optional[str]:
        """Get the current task ID."""
        if self.current_task_index < len(self.execution_order):
            return self.execution_order[self.current_task_index]
        return None
