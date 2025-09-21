"""
Execution Agent

Responsible for executing planned tasks and coordinating with external services.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentCapabilities, AgentMessage


class ExecutionAgent(BaseAgent):
    """
    Agent responsible for executing planned tasks and coordinating actions.
    
    Capabilities:
    - Execute booking operations
    - Coordinate with external APIs
    - Handle task dependencies
    - Manage execution workflows
    - Monitor task progress
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="Execution Coordinator",
                role=AgentRole.EXECUTOR,
                capabilities=AgentCapabilities(
                    can_execute=True,
                    can_monitor=True,
                    max_concurrent_tasks=5
                ),
                model="gpt-4",
                temperature=0.3
            )
        super().__init__(config)
        
        # Execution-specific attributes
        self.active_tasks = {}
        self.task_queue = asyncio.Queue()
        self.execution_history = []
        self.external_services = {}
    
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Process execution requests."""
        try:
            self.status = AgentStatus.RUNNING
            
            if message.message_type == "execute_task":
                return await self._execute_task(message.content)
            elif message.message_type == "execute_workflow":
                return await self._execute_workflow(message.content)
            elif message.message_type == "cancel_task":
                return await self._cancel_task(message.content)
            elif message.message_type == "get_status":
                return await self._get_task_status(message.content)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}
                
        except Exception as e:
            await self.handle_error(e)
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task."""
        task_id = task.get("task_id", f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        task_type = task.get("type")
        
        # Add to active tasks
        self.active_tasks[task_id] = {
            "task": task,
            "status": "running",
            "started_at": datetime.now(),
            "progress": 0
        }
        
        try:
            if task_type == "book_flight":
                result = await self._book_flight(task)
            elif task_type == "book_hotel":
                result = await self._book_hotel(task)
            elif task_type == "book_activity":
                result = await self._book_activity(task)
            elif task_type == "reserve_restaurant":
                result = await self._reserve_restaurant(task)
            elif task_type == "purchase_tickets":
                result = await self._purchase_tickets(task)
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            # Update task status
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.now()
            self.active_tasks[task_id]["result"] = result
            
            # Add to execution history
            self.execution_history.append({
                "task_id": task_id,
                "task_type": task_type,
                "status": "completed",
                "result": result,
                "executed_at": datetime.now()
            })
            
            return result
            
        except Exception as e:
            # Update task status to error
            self.active_tasks[task_id]["status"] = "error"
            self.active_tasks[task_id]["error"] = str(e)
            self.active_tasks[task_id]["failed_at"] = datetime.now()
            
            return {"error": str(e)}
    
    async def _execute_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task."""
        task = content.get("task", {})
        return await self.execute_task(task)
    
    async def _execute_workflow(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow of related tasks."""
        workflow = content.get("workflow", {})
        tasks = workflow.get("tasks", [])
        execution_mode = workflow.get("mode", "sequential")  # sequential, parallel, hybrid
        
        results = []
        
        if execution_mode == "sequential":
            for task in tasks:
                result = await self.execute_task(task)
                results.append(result)
                
                # Check if task failed and stop execution
                if "error" in result:
                    break
                    
        elif execution_mode == "parallel":
            # Execute all tasks in parallel
            task_coroutines = [self.execute_task(task) for task in tasks]
            results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
        elif execution_mode == "hybrid":
            # Execute tasks with dependencies
            results = await self._execute_hybrid_workflow(tasks)
        
        return {
            "success": True,
            "workflow_id": workflow.get("workflow_id"),
            "results": results,
            "execution_mode": execution_mode
        }
    
    async def _execute_hybrid_workflow(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tasks with dependencies in a hybrid mode."""
        results = []
        completed_tasks = set()
        
        while len(completed_tasks) < len(tasks):
            # Find tasks that can be executed (dependencies satisfied)
            ready_tasks = []
            for i, task in enumerate(tasks):
                if i in completed_tasks:
                    continue
                    
                dependencies = task.get("dependencies", [])
                if all(dep in completed_tasks for dep in dependencies):
                    ready_tasks.append((i, task))
            
            if not ready_tasks:
                # Circular dependency or error
                break
            
            # Execute ready tasks in parallel
            task_coroutines = []
            task_indices = []
            
            for idx, task in ready_tasks:
                task_coroutines.append(self.execute_task(task))
                task_indices.append(idx)
            
            task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            # Store results
            for idx, result in zip(task_indices, task_results):
                results.append(result)
                completed_tasks.add(idx)
        
        return results
    
    async def _cancel_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a running task."""
        task_id = content.get("task_id")
        
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            self.active_tasks[task_id]["cancelled_at"] = datetime.now()
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task cancelled successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }
    
    async def _get_task_status(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a task or all tasks."""
        task_id = content.get("task_id")
        
        if task_id:
            if task_id in self.active_tasks:
                return {
                    "success": True,
                    "task": self.active_tasks[task_id]
                }
            else:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
        else:
            return {
                "success": True,
                "active_tasks": self.active_tasks,
                "total_tasks": len(self.active_tasks)
            }
    
    # Specific execution methods for different task types
    
    async def _book_flight(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Book a flight."""
        # Mock flight booking
        flight_details = task.get("flight_details", {})
        
        # Simulate API call delay
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "booking_id": f"flight_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "confirmation_code": "ABC123",
            "flight_details": flight_details,
            "price": 450.00,
            "status": "confirmed"
        }
    
    async def _book_hotel(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Book a hotel."""
        hotel_details = task.get("hotel_details", {})
        
        # Simulate API call delay
        await asyncio.sleep(1.5)
        
        return {
            "success": True,
            "booking_id": f"hotel_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "confirmation_code": "HOT456",
            "hotel_details": hotel_details,
            "price": 120.00,
            "status": "confirmed"
        }
    
    async def _book_activity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Book an activity."""
        activity_details = task.get("activity_details", {})
        
        # Simulate API call delay
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "booking_id": f"activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "confirmation_code": "ACT789",
            "activity_details": activity_details,
            "price": 75.00,
            "status": "confirmed"
        }
    
    async def _reserve_restaurant(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Reserve a restaurant."""
        restaurant_details = task.get("restaurant_details", {})
        
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "reservation_id": f"rest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "confirmation_code": "RES012",
            "restaurant_details": restaurant_details,
            "status": "confirmed"
        }
    
    async def _purchase_tickets(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Purchase tickets for events or attractions."""
        ticket_details = task.get("ticket_details", {})
        
        # Simulate API call delay
        await asyncio.sleep(1.2)
        
        return {
            "success": True,
            "purchase_id": f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "confirmation_code": "TIC345",
            "ticket_details": ticket_details,
            "price": 35.00,
            "status": "confirmed"
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total_tasks = len(self.execution_history)
        successful_tasks = len([h for h in self.execution_history if h["status"] == "completed"])
        failed_tasks = total_tasks - successful_tasks
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "active_tasks": len(self.active_tasks),
            "average_execution_time": self._calculate_average_execution_time()
        }
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate average task execution time."""
        if not self.execution_history:
            return 0.0
        
        total_time = 0
        count = 0
        
        for task in self.execution_history:
            if "executed_at" in task and "started_at" in task:
                # This would need to be tracked properly in a real implementation
                total_time += 1.0  # Mock value
                count += 1
        
        return total_time / count if count > 0 else 0.0
