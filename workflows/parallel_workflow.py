"""
Parallel Workflow Implementation

Workflow that executes tasks in parallel when possible, respecting dependencies.
"""

from typing import Dict, Any, List, Optional, Set
import asyncio
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowConfig, WorkflowTask, WorkflowStatus, TaskStatus


class ParallelWorkflow(BaseWorkflow):
    """
    Parallel workflow implementation.
    
    Features:
    - Tasks execute in parallel when dependencies allow
    - Dependency management
    - Concurrency control
    - Error handling and retry logic
    - Progress tracking
    """
    
    def __init__(self, config: WorkflowConfig):
        super().__init__(config)
        self.running_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()
        self.task_semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the parallel workflow."""
        await self.start()
        
        try:
            # Execute tasks in parallel
            await self._execute_parallel()
            
            # Mark workflow as completed if all tasks finished successfully
            if self.status == WorkflowStatus.RUNNING:
                if self.failed_tasks and not self.config.continue_on_failure:
                    self.status = WorkflowStatus.FAILED
                else:
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
        """Add a task to the parallel workflow."""
        self.tasks[task.id] = task
        return task.id
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove a task from the parallel workflow."""
        if task_id not in self.tasks:
            return False
        
        # Remove task
        del self.tasks[task_id]
        
        # Update dependencies of remaining tasks
        for task in self.tasks.values():
            if task_id in task.dependencies:
                task.dependencies.remove(task_id)
        
        # Remove from tracking sets
        self.running_tasks.discard(task_id)
        self.completed_tasks.discard(task_id)
        self.failed_tasks.discard(task_id)
        
        return True
    
    async def _execute_parallel(self) -> None:
        """Execute tasks in parallel with dependency management."""
        while self.status == WorkflowStatus.RUNNING:
            # Get tasks that are ready to execute
            ready_tasks = await self._get_ready_tasks()
            
            if not ready_tasks:
                # Check if all tasks are completed or failed
                if len(self.completed_tasks) + len(self.failed_tasks) >= len(self.tasks):
                    break
                
                # Wait a bit before checking again
                await asyncio.sleep(0.1)
                continue
            
            # Execute ready tasks in parallel
            tasks_to_execute = ready_tasks[:self.config.max_concurrent_tasks - len(self.running_tasks)]
            
            if tasks_to_execute:
                # Create tasks for parallel execution
                coroutines = [self._execute_task_with_semaphore(task) for task in tasks_to_execute]
                await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Check if we should stop due to failures
            if self.failed_tasks and not self.config.continue_on_failure:
                self.status = WorkflowStatus.FAILED
                break
    
    async def _execute_task_with_semaphore(self, task: WorkflowTask) -> None:
        """Execute a task with semaphore control."""
        async with self.task_semaphore:
            await self._execute_task(task)
    
    async def _get_ready_tasks(self) -> List[WorkflowTask]:
        """Get tasks that are ready to execute (dependencies satisfied and not running)."""
        ready_tasks = []
        
        for task in self.tasks.values():
            if (task.status == TaskStatus.PENDING and 
                task.id not in self.running_tasks and
                await self._check_dependencies(task.id)):
                ready_tasks.append(task)
        
        return ready_tasks
    
    async def _execute_task(self, task: WorkflowTask) -> Any:
        """Execute a single task with parallel workflow tracking."""
        # Mark as running
        self.running_tasks.add(task.id)
        
        try:
            # Call parent implementation
            result = await super()._execute_task(task)
            
            # Update tracking sets
            self.running_tasks.discard(task.id)
            
            if task.status == TaskStatus.COMPLETED:
                self.completed_tasks.add(task.id)
            elif task.status == TaskStatus.FAILED:
                self.failed_tasks.add(task.id)
            
            return result
            
        except Exception as e:
            # Update tracking sets
            self.running_tasks.discard(task.id)
            self.failed_tasks.add(task.id)
            raise
    
    async def get_parallel_progress(self) -> Dict[str, Any]:
        """Get detailed parallel execution progress."""
        total_tasks = len(self.tasks)
        completed_count = len(self.completed_tasks)
        running_count = len(self.running_tasks)
        failed_count = len(self.failed_tasks)
        pending_count = total_tasks - completed_count - running_count - failed_count
        
        progress_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "running_tasks": running_count,
            "failed_tasks": failed_count,
            "pending_tasks": pending_count,
            "progress_percentage": progress_percentage,
            "max_concurrent": self.config.max_concurrent_tasks,
            "current_concurrent": running_count,
            "completed_task_ids": list(self.completed_tasks),
            "running_task_ids": list(self.running_tasks),
            "failed_task_ids": list(self.failed_tasks)
        }
    
    async def get_running_tasks(self) -> List[WorkflowTask]:
        """Get currently running tasks."""
        running_tasks = []
        for task_id in self.running_tasks:
            if task_id in self.tasks:
                running_tasks.append(self.tasks[task_id])
        return running_tasks
    
    async def get_completed_tasks(self) -> List[WorkflowTask]:
        """Get completed tasks."""
        completed_tasks = []
        for task_id in self.completed_tasks:
            if task_id in self.tasks:
                completed_tasks.append(self.tasks[task_id])
        return completed_tasks
    
    async def get_failed_tasks(self) -> List[WorkflowTask]:
        """Get failed tasks."""
        failed_tasks = []
        for task_id in self.failed_tasks:
            if task_id in self.tasks:
                failed_tasks.append(self.tasks[task_id])
        return failed_tasks
    
    async def retry_failed_tasks(self) -> int:
        """Retry all failed tasks."""
        retry_count = 0
        
        for task_id in list(self.failed_tasks):
            task = self.tasks[task_id]
            
            if task.retry_attempts > 0:
                task.retry_attempts -= 1
                task.status = TaskStatus.PENDING
                task.error = None
                task.started_at = None
                task.completed_at = None
                task.execution_time = 0.0
                
                self.failed_tasks.discard(task_id)
                retry_count += 1
                
                await self._log_event("task_retry", {
                    "task_id": task_id,
                    "remaining_attempts": task.retry_attempts
                })
        
        return retry_count
    
    async def cancel_running_tasks(self) -> int:
        """Cancel all running tasks."""
        cancelled_count = 0
        
        for task_id in list(self.running_tasks):
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                
                self.running_tasks.discard(task_id)
                cancelled_count += 1
                
                await self._log_event("task_cancelled", {
                    "task_id": task_id,
                    "reason": "workflow_cancelled"
                })
        
        return cancelled_count
    
    async def get_task_dependency_graph(self) -> Dict[str, Any]:
        """Get the task dependency graph."""
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for task_id, task in self.tasks.items():
            node = {
                "id": task_id,
                "name": task.name,
                "status": task.status.value,
                "type": task.task_type
            }
            graph["nodes"].append(node)
        
        # Add edges (dependencies)
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                edge = {
                    "from": dep_id,
                    "to": task_id
                }
                graph["edges"].append(edge)
        
        return graph
    
    async def get_critical_path(self) -> List[str]:
        """Get the critical path through the dependency graph."""
        # Simple critical path calculation
        # In reality, this would use more sophisticated algorithms
        
        critical_path = []
        visited = set()
        
        def find_longest_path(task_id: str, path: List[str]) -> List[str]:
            if task_id in visited:
                return path
            
            visited.add(task_id)
            current_path = path + [task_id]
            
            # Find tasks that depend on this one
            dependent_tasks = []
            for tid, task in self.tasks.items():
                if task_id in task.dependencies:
                    dependent_tasks.append(tid)
            
            if not dependent_tasks:
                return current_path
            
            # Find longest path from dependent tasks
            longest_path = current_path
            for dep_task_id in dependent_tasks:
                dep_path = find_longest_path(dep_task_id, current_path)
                if len(dep_path) > len(longest_path):
                    longest_path = dep_path
            
            return longest_path
        
        # Start from tasks with no dependencies
        root_tasks = [tid for tid, task in self.tasks.items() if not task.dependencies]
        
        for root_task_id in root_tasks:
            path = find_longest_path(root_task_id, [])
            if len(path) > len(critical_path):
                critical_path = path
        
        return critical_path
    
    def get_concurrency_stats(self) -> Dict[str, Any]:
        """Get concurrency statistics."""
        return {
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "current_running": len(self.running_tasks),
            "total_completed": len(self.completed_tasks),
            "total_failed": len(self.failed_tasks),
            "utilization_percentage": (len(self.running_tasks) / self.config.max_concurrent_tasks) * 100
        }
