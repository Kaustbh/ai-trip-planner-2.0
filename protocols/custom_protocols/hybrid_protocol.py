"""
Hybrid Protocol Implementation

Combines MCP and A2A protocols for optimal communication in trip planning scenarios.
"""

from typing import Dict, Any, List, Optional, Callable
import asyncio
import json
from datetime import datetime

from ..base_protocol import BaseProtocol, ProtocolConfig, ProtocolType, ProtocolMessage, MessageStatus
from ..mcp_protocol import MCPProtocol, MCPConfig
from ..a2a_protocol import A2AProtocol, A2AConfig


class HybridConfig(ProtocolConfig):
    """Configuration for Hybrid protocol."""
    protocol_type: ProtocolType = ProtocolType.HYBRID
    mcp_config: Optional[MCPConfig] = None
    a2a_config: Optional[A2AConfig] = None
    routing_strategy: str = "intelligent"  # intelligent, mcp_first, a2a_first
    fallback_enabled: bool = True
    load_balancing: bool = True
    message_priority_threshold: int = 3  # Messages with priority >= this use MCP


class HybridProtocol(BaseProtocol):
    """
    Hybrid protocol that combines MCP and A2A for optimal communication.
    
    Features:
    - Intelligent message routing
    - Protocol fallback
    - Load balancing
    - Priority-based routing
    - Seamless protocol switching
    """
    
    def __init__(self, config: HybridConfig):
        super().__init__(config)
        self.config: HybridConfig = config
        
        # Initialize sub-protocols
        self.mcp_protocol = None
        self.a2a_protocol = None
        
        # Routing state
        self.routing_stats = {
            "mcp_messages": 0,
            "a2a_messages": 0,
            "fallback_messages": 0,
            "failed_routes": 0
        }
        
        # Load balancing
        self.protocol_loads = {
            "mcp": 0,
            "a2a": 0
        }
        
    async def start(self) -> None:
        """Start the hybrid protocol."""
        self.is_running = True
        
        # Initialize MCP protocol if configured
        if self.config.mcp_config:
            self.mcp_protocol = MCPProtocol(self.config.mcp_config)
            await self.mcp_protocol.start()
        
        # Initialize A2A protocol if configured
        if self.config.a2a_config:
            self.a2a_protocol = A2AProtocol(self.config.a2a_config)
            await self.a2a_protocol.start()
        
        # Start message processing
        asyncio.create_task(self._message_processing_loop())
        
        print(f"Hybrid Protocol started: {self.config.name}")
    
    async def stop(self) -> None:
        """Stop the hybrid protocol."""
        self.is_running = False
        
        # Stop sub-protocols
        if self.mcp_protocol:
            await self.mcp_protocol.stop()
        
        if self.a2a_protocol:
            await self.a2a_protocol.stop()
        
        print(f"Hybrid Protocol stopped: {self.config.name}")
    
    async def send_message(self, message: ProtocolMessage) -> bool:
        """Send a message using hybrid routing strategy."""
        try:
            if not await self.validate_message(message):
                return False
            
            # Determine best protocol for this message
            selected_protocol = await self._select_protocol(message)
            
            if not selected_protocol:
                message.status = MessageStatus.FAILED
                self.routing_stats["failed_routes"] += 1
                return False
            
            # Send message through selected protocol
            success = await self._send_via_protocol(message, selected_protocol)
            
            if success:
                message.status = MessageStatus.SENT
                self.stats["messages_sent"] += 1
                self.routing_stats[f"{selected_protocol}_messages"] += 1
            else:
                # Try fallback if enabled
                if self.config.fallback_enabled:
                    fallback_protocol = await self._get_fallback_protocol(selected_protocol)
                    if fallback_protocol:
                        success = await self._send_via_protocol(message, fallback_protocol)
                        if success:
                            message.status = MessageStatus.SENT
                            self.stats["messages_sent"] += 1
                            self.routing_stats["fallback_messages"] += 1
                        else:
                            message.status = MessageStatus.FAILED
                            self.stats["messages_failed"] += 1
                    else:
                        message.status = MessageStatus.FAILED
                        self.stats["messages_failed"] += 1
                else:
                    message.status = MessageStatus.FAILED
                    self.stats["messages_failed"] += 1
            
            return success
            
        except Exception as e:
            print(f"Error sending hybrid message: {str(e)}")
            message.status = MessageStatus.FAILED
            self.stats["messages_failed"] += 1
            return False
    
    async def receive_message(self, message: ProtocolMessage) -> None:
        """Receive a message through hybrid protocol."""
        try:
            # Process the message
            await self.process_message(message)
            
        except Exception as e:
            print(f"Error receiving hybrid message: {str(e)}")
    
    async def _select_protocol(self, message: ProtocolMessage) -> Optional[str]:
        """Select the best protocol for a message."""
        if self.config.routing_strategy == "intelligent":
            return await self._intelligent_routing(message)
        elif self.config.routing_strategy == "mcp_first":
            return await self._mcp_first_routing(message)
        elif self.config.routing_strategy == "a2a_first":
            return await self._a2a_first_routing(message)
        else:
            return await self._intelligent_routing(message)
    
    async def _intelligent_routing(self, message: ProtocolMessage) -> Optional[str]:
        """Intelligent routing based on message characteristics."""
        # Priority-based routing
        if message.priority.value >= self.config.message_priority_threshold:
            if self.mcp_protocol and self.mcp_protocol.is_running:
                return "mcp"
        
        # Message type routing
        if message.message_type in ["tool_call", "tool_response", "context_request"]:
            if self.mcp_protocol and self.mcp_protocol.is_running:
                return "mcp"
        
        # Load balancing
        if self.config.load_balancing:
            if self.protocol_loads["a2a"] < self.protocol_loads["mcp"]:
                if self.a2a_protocol and self.a2a_protocol.is_running:
                    return "a2a"
            else:
                if self.mcp_protocol and self.mcp_protocol.is_running:
                    return "mcp"
        
        # Default to available protocol
        if self.a2a_protocol and self.a2a_protocol.is_running:
            return "a2a"
        elif self.mcp_protocol and self.mcp_protocol.is_running:
            return "mcp"
        
        return None
    
    async def _mcp_first_routing(self, message: ProtocolMessage) -> Optional[str]:
        """MCP-first routing strategy."""
        if self.mcp_protocol and self.mcp_protocol.is_running:
            return "mcp"
        elif self.a2a_protocol and self.a2a_protocol.is_running:
            return "a2a"
        return None
    
    async def _a2a_first_routing(self, message: ProtocolMessage) -> Optional[str]:
        """A2A-first routing strategy."""
        if self.a2a_protocol and self.a2a_protocol.is_running:
            return "a2a"
        elif self.mcp_protocol and self.mcp_protocol.is_running:
            return "mcp"
        return None
    
    async def _send_via_protocol(self, message: ProtocolMessage, protocol: str) -> bool:
        """Send message via specific protocol."""
        try:
            if protocol == "mcp" and self.mcp_protocol:
                success = await self.mcp_protocol.send_message(message)
                if success:
                    self.protocol_loads["mcp"] += 1
                return success
            elif protocol == "a2a" and self.a2a_protocol:
                success = await self.a2a_protocol.send_message(message)
                if success:
                    self.protocol_loads["a2a"] += 1
                return success
            else:
                return False
        except Exception as e:
            print(f"Error sending via {protocol}: {str(e)}")
            return False
    
    async def _get_fallback_protocol(self, failed_protocol: str) -> Optional[str]:
        """Get fallback protocol when primary fails."""
        if failed_protocol == "mcp":
            if self.a2a_protocol and self.a2a_protocol.is_running:
                return "a2a"
        elif failed_protocol == "a2a":
            if self.mcp_protocol and self.mcp_protocol.is_running:
                return "mcp"
        
        return None
    
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
                
                # Update load balancing stats
                await self._update_load_balancing()
                
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in hybrid message processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _update_load_balancing(self) -> None:
        """Update load balancing statistics."""
        if self.mcp_protocol:
            mcp_stats = self.mcp_protocol.get_stats()
            self.protocol_loads["mcp"] = mcp_stats["stats"]["messages_sent"]
        
        if self.a2a_protocol:
            a2a_stats = self.a2a_protocol.get_stats()
            self.protocol_loads["a2a"] = a2a_stats["stats"]["messages_sent"]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], 
                       caller: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool using the best available protocol."""
        if self.mcp_protocol and self.mcp_protocol.is_running:
            return await self.mcp_protocol.call_tool(tool_name, parameters, caller, context)
        else:
            return {"error": "Tool calling not available - MCP protocol not running"}
    
    async def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """Register an agent with the hybrid protocol."""
        success = False
        
        if self.a2a_protocol and self.a2a_protocol.is_running:
            success = await self.a2a_protocol.register_agent(agent_id, agent_info)
        
        return success
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the hybrid protocol."""
        success = False
        
        if self.a2a_protocol and self.a2a_protocol.is_running:
            success = await self.a2a_protocol.unregister_agent(agent_id)
        
        return success
    
    async def broadcast_to_capability(self, sender: str, capability: str, 
                                    content: Dict[str, Any], 
                                    message_type: str = "broadcast") -> List[bool]:
        """Broadcast message to agents with specific capability."""
        if self.a2a_protocol and self.a2a_protocol.is_running:
            return await self.a2a_protocol.broadcast_to_capability(sender, capability, content, message_type)
        else:
            return []
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get available tools from MCP protocol."""
        if self.mcp_protocol and self.mcp_protocol.is_running:
            return self.mcp_protocol.get_available_tools()
        else:
            return {}
    
    def get_agent_registry(self) -> Dict[str, Any]:
        """Get agent registry from A2A protocol."""
        if self.a2a_protocol and self.a2a_protocol.is_running:
            return self.a2a_protocol.get_agent_registry()
        else:
            return {}
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get hybrid protocol information."""
        info = {
            "protocol_type": "Hybrid",
            "version": "1.0",
            "routing_strategy": self.config.routing_strategy,
            "fallback_enabled": self.config.fallback_enabled,
            "load_balancing": self.config.load_balancing,
            "routing_stats": self.routing_stats.copy(),
            "protocol_loads": self.protocol_loads.copy()
        }
        
        # Add sub-protocol info
        if self.mcp_protocol:
            info["mcp_protocol"] = self.mcp_protocol.get_protocol_info()
        
        if self.a2a_protocol:
            info["a2a_protocol"] = self.a2a_protocol.get_protocol_info()
        
        return info
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            "routing_stats": self.routing_stats.copy(),
            "protocol_loads": self.protocol_loads.copy(),
            "total_messages": sum(self.routing_stats.values()),
            "success_rate": self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        total_messages = sum(self.routing_stats.values())
        failed_messages = self.routing_stats["failed_routes"]
        
        if total_messages == 0:
            return 0.0
        
        return (total_messages - failed_messages) / total_messages
