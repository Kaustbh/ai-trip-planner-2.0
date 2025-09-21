"""
Base Tool Class

Defines the common interface for all tools in the system.
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


class ToolType(Enum):
    """Tool type enumeration."""
    API = "api"
    DATABASE = "database"
    FUNCTION = "function"
    SEARCH = "search"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"


class ToolStatus(Enum):
    """Tool status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


class ToolCapability(Enum):
    """Tool capability enumeration."""
    READ = "read"
    WRITE = "write"
    SEARCH = "search"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    NOTIFY = "notify"


@dataclass
class ToolResult:
    """Result structure for tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    name: str
    tool_type: ToolType
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1
    rate_limit: Optional[int] = None  # requests per minute
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    capabilities: List[ToolCapability] = []
    parameters: Dict[str, Any] = {}


class BaseTool(ABC):
    """
    Base class for all tools in the system.
    
    Provides common functionality for:
    - Tool execution
    - Error handling
    - Rate limiting
    - Caching
    - Monitoring
    """
    
    def __init__(self, config: ToolConfig):
        self.config = config
        self.tool_id = str(uuid.uuid4())
        self.status = ToolStatus.IDLE
        self.execution_count = 0
        self.error_count = 0
        self.cache = {}
        self.rate_limiter = None
        self.last_execution = None
        self.execution_history = []
        
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            parameters: Tool-specific parameters
            
        Returns:
            ToolResult with execution results
        """
        pass
    
    @abstractmethod
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters before execution.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    async def run(self, parameters: Dict[str, Any]) -> ToolResult:
        """Run the tool with error handling and monitoring."""
        start_time = datetime.now()
        
        try:
            # Check if tool is enabled
            if not self.config.enabled:
                return ToolResult(
                    success=False,
                    error="Tool is disabled",
                    execution_time=0.0
                )
            
            # Check rate limiting
            if not await self._check_rate_limit():
                return ToolResult(
                    success=False,
                    error="Rate limit exceeded",
                    execution_time=0.0
                )
            
            # Validate parameters
            if not await self.validate_parameters(parameters):
                return ToolResult(
                    success=False,
                    error="Invalid parameters",
                    execution_time=0.0
                )
            
            # Check cache
            cache_key = self._generate_cache_key(parameters)
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if self._is_cache_valid(cached_result):
                    return ToolResult(
                        success=True,
                        data=cached_result["data"],
                        metadata=cached_result.get("metadata", {}),
                        execution_time=0.0
                    )
            
            # Execute tool
            self.status = ToolStatus.RUNNING
            result = await self._execute_with_timeout(parameters)
            
            # Update statistics
            self.execution_count += 1
            self.last_execution = datetime.now()
            
            if result.success:
                # Cache successful results
                self.cache[cache_key] = {
                    "data": result.data,
                    "metadata": result.metadata,
                    "timestamp": datetime.now()
                }
            else:
                self.error_count += 1
            
            # Update execution history
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            self.execution_history.append({
                "timestamp": datetime.now(),
                "parameters": parameters,
                "result": result,
                "execution_time": execution_time
            })
            
            # Keep only last 100 executions
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
            
            return result
            
        except asyncio.TimeoutError:
            self.error_count += 1
            return ToolResult(
                success=False,
                error="Tool execution timeout",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            self.error_count += 1
            return ToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        finally:
            self.status = ToolStatus.IDLE
    
    async def _execute_with_timeout(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute tool with timeout."""
        try:
            return await asyncio.wait_for(
                self.execute(parameters),
                timeout=self.config.timeout
            )
        except asyncio.TimeoutError:
            raise
    
    async def _check_rate_limit(self) -> bool:
        """Check if tool is within rate limits."""
        if not self.config.rate_limit:
            return True
        
        # Simple rate limiting - in reality would use more sophisticated algorithm
        current_time = datetime.now()
        if self.last_execution:
            time_since_last = (current_time - self.last_execution).total_seconds()
            if time_since_last < 60 / self.config.rate_limit:
                return False
        
        return True
    
    def _generate_cache_key(self, parameters: Dict[str, Any]) -> str:
        """Generate cache key from parameters."""
        # Sort parameters for consistent keys
        sorted_params = json.dumps(parameters, sort_keys=True)
        return f"{self.tool_id}_{hash(sorted_params)}"
    
    def _is_cache_valid(self, cached_result: Dict[str, Any], ttl: int = 300) -> bool:
        """Check if cached result is still valid."""
        if "timestamp" not in cached_result:
            return False
        
        age = (datetime.now() - cached_result["timestamp"]).total_seconds()
        return age < ttl
    
    def clear_cache(self) -> None:
        """Clear tool cache."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool statistics."""
        total_executions = self.execution_count
        success_rate = (total_executions - self.error_count) / total_executions if total_executions > 0 else 0
        
        return {
            "tool_id": self.tool_id,
            "name": self.config.name,
            "type": self.config.tool_type.value,
            "status": self.status.value,
            "execution_count": total_executions,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "cache_size": len(self.cache),
            "enabled": self.config.enabled
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def enable(self) -> None:
        """Enable the tool."""
        self.config.enabled = True
    
    def disable(self) -> None:
        """Disable the tool."""
        self.config.enabled = False
        self.status = ToolStatus.DISABLED
    
    def __str__(self) -> str:
        return f"{self.config.name} ({self.config.tool_type.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.tool_id}, name={self.config.name})>"
