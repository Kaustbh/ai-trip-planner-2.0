"""
Hybrid Workflow Implementation

Workflow that combines sequential and parallel execution based on task characteristics.
"""

from typing import Dict, Any, List, Optional, Set
import asyncio
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowConfig, WorkflowTask, WorkflowStatus, TaskStatus
from .sequential_workflow import SequentialWorkflow
from .parallel_workflow import ParallelWorkflow


class HybridWorkflow(BaseWorkflow):
    """
    Hybrid workflow implementation.
    
    Features:
    - Combines sequential and parallel execution
    - Intelligent task grouping
    - Dynamic execution mode switching
    - Advanced dependency management
    - Performance optimization
    """
    
    def __init__(self, config: WorkflowConfig):
        super().__init__(config)
        
        # Sub-workflows
        self.sequential_workflow = SequentialWorkflow(config)
        self.parallel_workflow = ParallelWorkflow(config)
        
        # Hybrid-specific attributes
        self.task_groups = {}  # group_id -> list of task_ids
        self.execution_plan = []  # List of execution phases
        self.current_phase = 0
        self.phase_results = {}
        
        # Task classification
        self.critical_tasks = set()
        self.parallel_tasks = set()
        self.sequential_tasks = set()
        
    async def execute(self) -> Dict[str, Any]:
        """Execute the hybrid workflow."""
        await self.start()
        
        try:
            # Analyze tasks and create execution plan
            await self._analyze_tasks()
            await self._create_execution_plan()
            
            # Execute phases
            for phase_index, phase in enumerate(self.execution_plan):
                if self.status != WorkflowStatus.RUNNING:
                    break
                
                self.current_phase = phase_index
                await self._execute_phase(phase)
            
            # Mark workflow as completed
            if self.status == WorkflowStatus.RUNNING:
                if any(task.status == TaskStatus.FAILED for task in self.tasks.values()) and not self.config.continue_on_failure:
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
        """Add a task to the hybrid workflow."""
        self.tasks[task.id] = task
        
        # Classify task
        await self._classify_task(task)
        
        return task.id
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove a task from the hybrid workflow."""
        if task_id not in self.tasks:
            return False
        
        # Remove from classification sets
        self.critical_tasks.discard(task_id)
        self.parallel_tasks.discard(task_id)
        self.sequential_tasks.discard(task_id)
        
        # Remove from task groups
        for group_id, task_ids in self.task_groups.items():
            if task_id in task_ids:
                task_ids.remove(task_id)
        
        # Remove task
        del self.tasks[task_id]
        
        # Update dependencies of remaining tasks
        for task in self.tasks.values():
            if task_id in task.dependencies:
                task.dependencies.remove(task_id)
        
        return True
    
    async def _analyze_tasks(self) -> None:
        """Analyze tasks to determine execution strategy."""
        for task in self.tasks.values():
            await self._classify_task(task)
        
        # Create task groups based on dependencies and characteristics
        await self._create_task_groups()
    
    async def _classify_task(self, task: WorkflowTask) -> None:
        """Classify a task for execution strategy."""
        # Critical tasks (must be sequential)
        if (task.task_type in ["critical", "safety", "validation"] or
            len(task.dependencies) > 2 or
            task.importance > 0.8):
            self.critical_tasks.add(task.id)
            self.sequential_tasks.add(task.id)
        
        # Parallel tasks (can run in parallel)
        elif (task.task_type in ["search", "research", "data_fetch"] or
              len(task.dependencies) == 0 or
              task.importance < 0.3):
            self.parallel_tasks.add(task.id)
        
        # Default to sequential
        else:
            self.sequential_tasks.add(task.id)
    
    async def _create_task_groups(self) -> None:
        """Create task groups for execution phases."""
        self.task_groups.clear()
        
        # Group tasks by dependencies and characteristics
        remaining_tasks = set(self.tasks.keys())
        group_id = 0
        
        while remaining_tasks:
            # Find tasks that can be executed in this group
            group_tasks = []
            
            for task_id in list(remaining_tasks):
                task = self.tasks[task_id]
                
                # Check if all dependencies are satisfied
                if await self._check_dependencies(task_id):
                    group_tasks.append(task_id)
            
            if not group_tasks:
                # No tasks can be executed - break to avoid infinite loop
                break
            
            # Create group
            group_id += 1
            self.task_groups[group_id] = group_tasks
            
            # Remove from remaining tasks
            for task_id in group_tasks:
                remaining_tasks.discard(task_id)
    
    async def _create_execution_plan(self) -> None:
        """Create the execution plan based on task groups."""
        self.execution_plan = []
        
        for group_id, task_ids in self.task_groups.items():
            # Determine execution mode for this group
            critical_count = len([tid for tid in task_ids if tid in self.critical_tasks])
            parallel_count = len([tid for tid in task_ids if tid in self.parallel_tasks])
            
            if critical_count > parallel_count:
                # Sequential execution
                phase = {
                    "phase_id": group_id,
                    "execution_mode": "sequential",
                    "task_ids": task_ids,
                    "description": f"Sequential phase {group_id}"
                }
            else:
                # Parallel execution
                phase = {
                    "phase_id": group_id,
                    "execution_mode": "parallel",
                    "task_ids": task_ids,
                    "description": f"Parallel phase {group_id}"
                }
            
            self.execution_plan.append(phase)
    
    async def _execute_phase(self, phase: Dict[str, Any]) -> None:
        """Execute a single phase of the workflow."""
        phase_id = phase["phase_id"]
        execution_mode = phase["execution_mode"]
        task_ids = phase["task_ids"]
        
        await self._log_event("phase_started", {
            "phase_id": phase_id,
            "execution_mode": execution_mode,
            "task_count": len(task_ids)
        })
        
        try:
            if execution_mode == "sequential":
                await self._execute_sequential_phase(task_ids)
            elif execution_mode == "parallel":
                await self._execute_parallel_phase(task_ids)
            
            await self._log_event("phase_completed", {
                "phase_id": phase_id,
                "execution_mode": execution_mode
            })
            
        except Exception as e:
            await self._log_event("phase_failed", {
                "phase_id": phase_id,
                "execution_mode": execution_mode,
                "error": str(e)
            })
            
            if not self.config.continue_on_failure:
                raise
    
    async def _execute_sequential_phase(self, task_ids: List[str]) -> None:
        """Execute tasks in sequential mode."""
        for task_id in task_ids:
            if self.status != WorkflowStatus.RUNNING:
                break
            
            task = self.tasks[task_id]
            await self._execute_task(task)
            
            # Check if task failed and we should stop
            if task.status == TaskStatus.FAILED and not self.config.continue_on_failure:
                self.status = WorkflowStatus.FAILED
                break
    
    async def _execute_parallel_phase(self, task_ids: List[str]) -> None:
        """Execute tasks in parallel mode."""
        # Create tasks for parallel execution
        coroutines = []
        
        for task_id in task_ids:
            task = self.tasks[task_id]
            coroutines.append(self._execute_task(task))
        
        # Execute in parallel
        await asyncio.gather(*coroutines, return_exceptions=True)
    
    async def get_hybrid_progress(self) -> Dict[str, Any]:
        """Get detailed hybrid execution progress."""
        total_phases = len(self.execution_plan)
        completed_phases = self.current_phase
        
        phase_progress = []
        for i, phase in enumerate(self.execution_plan):
            phase_info = {
                "phase_id": phase["phase_id"],
                "execution_mode": phase["execution_mode"],
                "task_count": len(phase["task_ids"]),
                "status": "completed" if i < completed_phases else "running" if i == completed_phases else "pending"
            }
            phase_progress.append(phase_info)
        
        # Calculate overall progress
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "current_phase": self.current_phase,
            "phase_progress": phase_progress,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": progress_percentage,
            "task_classification": {
                "critical_tasks": len(self.critical_tasks),
                "parallel_tasks": len(self.parallel_tasks),
                "sequential_tasks": len(self.sequential_tasks)
            }
        }
    
    async def get_execution_plan(self) -> List[Dict[str, Any]]:
        """Get the current execution plan."""
        return self.execution_plan.copy()
    
    async def get_task_classification(self) -> Dict[str, List[str]]:
        """Get task classification."""
        return {
            "critical_tasks": list(self.critical_tasks),
            "parallel_tasks": list(self.parallel_tasks),
            "sequential_tasks": list(self.sequential_tasks)
        }
    
    async def optimize_execution_plan(self) -> None:
        """Optimize the execution plan for better performance."""
        # Re-analyze tasks
        await self._analyze_tasks()
        
        # Recreate execution plan
        await self._create_execution_plan()
        
        await self._log_event("execution_plan_optimized", {
            "workflow_id": self.workflow_id,
            "new_plan": self.execution_plan
        })
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the hybrid workflow."""
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        
        # Calculate efficiency metrics
        parallel_efficiency = len(self.parallel_tasks) / total_tasks if total_tasks > 0 else 0
        sequential_efficiency = len(self.sequential_tasks) / total_tasks if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "parallel_efficiency": parallel_efficiency,
            "sequential_efficiency": sequential_efficiency,
            "total_phases": len(self.execution_plan),
            "current_phase": self.current_phase,
            "execution_time": self.total_execution_time
        }
