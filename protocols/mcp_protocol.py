"""
MCP (Model Context Protocol) Implementation

Protocol for communication between AI models and external tools/contexts.
"""

from typing import Dict, Any, List, Optional, Callable
import asyncio
import json
from datetime import datetime

from .base_protocol import BaseProtocol, ProtocolConfig, ProtocolType, ProtocolMessage, MessageStatus


class MCPConfig(ProtocolConfig):
    """Configuration for MCP protocol."""
    protocol_type: ProtocolType = ProtocolType.MCP
    server_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    model_name: str = "gpt-4"
    context_window: int = 8192
    max_tokens: int = 2048
    temperature: float = 0.7
    tools_enabled: bool = True
    streaming_enabled: bool = False


class MCPProtocol(BaseProtocol):
    """
    Implementation of Model Context Protocol for AI agent communication.
    
    Features:
    - Tool calling and execution
    - Context management
    - Streaming responses
    - Model-specific optimizations
    """
    
    def __init__(self, config: MCPConfig):
        super().__init__(config)
        self.config: MCPConfig = config
        self.available_tools = {}
        self.context_store = {}
        self.active_sessions = {}
        self.tool_executors = {}
        
    async def start(self) -> None:
        """Start the MCP protocol."""
        self.is_running = True
        
        # Initialize MCP server connection
        await self._initialize_server_connection()
        
        # Load available tools
        await self._load_available_tools()
        
        # Start message processing loop
        asyncio.create_task(self._message_processing_loop())
        
        print(f"MCP Protocol started: {self.config.name}")
    
    async def stop(self) -> None:
        """Stop the MCP protocol."""
        self.is_running = False
        
        # Close server connections
        await self._close_server_connections()
        
        # Clear active sessions
        self.active_sessions.clear()
        
        print(f"MCP Protocol stopped: {self.config.name}")
    
    async def send_message(self, message: ProtocolMessage) -> bool:
        """Send a message through MCP protocol."""
        try:
            if not await self.validate_message(message):
                return False
            
            # Convert to MCP format
            mcp_message = await self._convert_to_mcp_format(message)
            
            # Send via MCP server
            success = await self._send_mcp_message(mcp_message)
            
            if success:
                message.status = MessageStatus.SENT
                self.stats["messages_sent"] += 1
            else:
                message.status = MessageStatus.FAILED
                self.stats["messages_failed"] += 1
            
            return success
            
        except Exception as e:
            print(f"Error sending MCP message: {str(e)}")
            message.status = MessageStatus.FAILED
            self.stats["messages_failed"] += 1
            return False
    
    async def receive_message(self, message: ProtocolMessage) -> None:
        """Receive a message through MCP protocol."""
        try:
            # Convert from MCP format
            protocol_message = await self._convert_from_mcp_format(message)
            
            # Process the message
            await self.process_message(protocol_message)
            
        except Exception as e:
            print(f"Error receiving MCP message: {str(e)}")
    
    async def _initialize_server_connection(self) -> None:
        """Initialize connection to MCP server."""
        # Mock server connection - in reality would use HTTP/WebSocket
        print(f"Connecting to MCP server at {self.config.server_url}")
        await asyncio.sleep(0.1)  # Simulate connection delay
        print("MCP server connection established")
    
    async def _close_server_connections(self) -> None:
        """Close connections to MCP server."""
        print("Closing MCP server connections")
        await asyncio.sleep(0.1)  # Simulate cleanup delay
    
    async def _load_available_tools(self) -> None:
        """Load available tools from MCP server."""
        # Mock tool loading
        self.available_tools = {
            "search": {
                "name": "search",
                "description": "Search for information",
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "integer", "default": 10}
                }
            },
            "get_weather": {
                "name": "get_weather",
                "description": "Get weather information",
                "parameters": {
                    "location": {"type": "string", "required": True},
                    "date": {"type": "string", "required": False}
                }
            },
            "book_flight": {
                "name": "book_flight",
                "description": "Book a flight",
                "parameters": {
                    "origin": {"type": "string", "required": True},
                    "destination": {"type": "string", "required": True},
                    "date": {"type": "string", "required": True},
                    "passengers": {"type": "integer", "default": 1}
                }
            }
        }
        
        print(f"Loaded {len(self.available_tools)} tools from MCP server")
    
    async def _message_processing_loop(self) -> None:
        """Main message processing loop."""
        while self.is_running:
            try:
                # Process messages from queue
                if not self.message_queue.empty():
                    message = await asyncio.wait_for(
                        self.message_queue.get(), 
                        timeout=1.0
                    )
                    await self.process_message(message)
                
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in MCP message processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _convert_to_mcp_format(self, message: ProtocolMessage) -> Dict[str, Any]:
        """Convert protocol message to MCP format."""
        mcp_message = {
            "id": message.id,
            "type": "message",
            "sender": message.sender,
            "recipient": message.recipient,
            "content": message.content,
            "message_type": message.message_type,
            "priority": message.priority.value,
            "timestamp": message.timestamp.isoformat(),
            "correlation_id": message.correlation_id
        }
        
        # Add MCP-specific fields
        if message.message_type == "tool_call":
            mcp_message["tool"] = message.content.get("tool")
            mcp_message["parameters"] = message.content.get("parameters", {})
        
        return mcp_message
    
    async def _convert_from_mcp_format(self, mcp_message: Dict[str, Any]) -> ProtocolMessage:
        """Convert MCP message to protocol format."""
        return ProtocolMessage(
            id=mcp_message.get("id", ""),
            sender=mcp_message.get("sender", ""),
            recipient=mcp_message.get("recipient", ""),
            content=mcp_message.get("content", {}),
            message_type=mcp_message.get("message_type", "default"),
            priority=mcp_message.get("priority", 2),
            timestamp=datetime.fromisoformat(mcp_message.get("timestamp", datetime.now().isoformat())),
            correlation_id=mcp_message.get("correlation_id")
        )
    
    async def _send_mcp_message(self, mcp_message: Dict[str, Any]) -> bool:
        """Send message to MCP server."""
        try:
            # Mock MCP server communication
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # In reality, this would make HTTP/WebSocket request to MCP server
            print(f"Sending MCP message: {mcp_message['message_type']} from {mcp_message['sender']} to {mcp_message['recipient']}")
            
            return True
            
        except Exception as e:
            print(f"Error sending to MCP server: {str(e)}")
            return False
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], 
                       caller: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool through MCP protocol."""
        if tool_name not in self.available_tools:
            return {"error": f"Tool '{tool_name}' not available"}
        
        tool_spec = self.available_tools[tool_name]
        
        # Validate parameters
        validation_result = await self._validate_tool_parameters(tool_spec, parameters)
        if not validation_result["valid"]:
            return {"error": f"Invalid parameters: {validation_result['errors']}"}
        
        # Create tool call message
        tool_call_message = self.create_message(
            sender=caller,
            recipient="mcp_server",
            content={
                "tool": tool_name,
                "parameters": parameters,
                "context": context or {}
            },
            message_type="tool_call",
            priority=2
        )
        
        # Send tool call
        success = await self.send_message(tool_call_message)
        if not success:
            return {"error": "Failed to send tool call"}
        
        # Wait for tool response
        response = await self._wait_for_tool_response(tool_call_message.id)
        
        return response or {"error": "Tool call timeout"}
    
    async def _validate_tool_parameters(self, tool_spec: Dict[str, Any], 
                                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool parameters against specification."""
        errors = []
        tool_params = tool_spec.get("parameters", {})
        
        # Check required parameters
        for param_name, param_spec in tool_params.items():
            if param_spec.get("required", False) and param_name not in parameters:
                errors.append(f"Required parameter '{param_name}' missing")
        
        # Check parameter types
        for param_name, param_value in parameters.items():
            if param_name in tool_params:
                expected_type = tool_params[param_name].get("type")
                if expected_type and not self._check_parameter_type(param_value, expected_type):
                    errors.append(f"Parameter '{param_name}' has wrong type, expected {expected_type}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _check_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if not expected_python_type:
            return True  # Unknown type, assume valid
        
        return isinstance(value, expected_python_type)
    
    async def _wait_for_tool_response(self, message_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for tool response."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check for response in message history
            for message in self.message_history:
                if (message.correlation_id == message_id and 
                    message.message_type == "tool_response"):
                    return message.content
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get context by ID."""
        return self.context_store.get(context_id)
    
    async def set_context(self, context_id: str, context: Dict[str, Any]) -> None:
        """Set context by ID."""
        self.context_store[context_id] = {
            "id": context_id,
            "data": context,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
    
    async def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing context."""
        if context_id not in self.context_store:
            return False
        
        self.context_store[context_id]["data"].update(updates)
        self.context_store[context_id]["last_accessed"] = datetime.now().isoformat()
        return True
    
    async def delete_context(self, context_id: str) -> bool:
        """Delete context by ID."""
        if context_id in self.context_store:
            del self.context_store[context_id]
            return True
        return False
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools."""
        return self.available_tools.copy()
    
    def register_tool_executor(self, tool_name: str, executor: Callable) -> None:
        """Register a tool executor function."""
        self.tool_executors[tool_name] = executor
    
    async def execute_tool_locally(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool locally if executor is registered."""
        if tool_name not in self.tool_executors:
            return {"error": f"No local executor for tool '{tool_name}'"}
        
        try:
            executor = self.tool_executors[tool_name]
            result = await executor(parameters)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get MCP protocol information."""
        return {
            "protocol_type": "MCP",
            "version": "1.0",
            "server_url": self.config.server_url,
            "model_name": self.config.model_name,
            "tools_available": len(self.available_tools),
            "contexts_stored": len(self.context_store),
            "active_sessions": len(self.active_sessions)
        }
