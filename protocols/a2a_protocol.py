"""
A2A (Agent-to-Agent) Protocol Implementation

Direct communication protocol between AI agents without external servers.
"""

from typing import Dict, Any, List, Optional, Callable
import asyncio
import json
from datetime import datetime
from collections import defaultdict

from .base_protocol import BaseProtocol, ProtocolConfig, ProtocolType, ProtocolMessage, MessageStatus


class A2AConfig(ProtocolConfig):
    """Configuration for A2A protocol."""
    protocol_type: ProtocolType = ProtocolType.A2A
    discovery_enabled: bool = True
    discovery_interval: int = 30  # seconds
    heartbeat_interval: int = 10  # seconds
    max_agents: int = 100
    message_broadcast: bool = True
    encryption_key: Optional[str] = None
    compression_threshold: int = 1024  # bytes


class A2AProtocol(BaseProtocol):
    """
    Implementation of Agent-to-Agent communication protocol.
    
    Features:
    - Direct agent communication
    - Service discovery
    - Message broadcasting
    - Heartbeat monitoring
    - Encryption support
    """
    
    def __init__(self, config: A2AConfig):
        super().__init__(config)
        self.config: A2AConfig = config
        self.agent_registry = {}
        self.message_routing_table = defaultdict(list)
        self.heartbeat_monitor = {}
        self.discovery_service = None
        self.message_cache = {}
        self.encryption_enabled = config.encryption_key is not None
        
    async def start(self) -> None:
        """Start the A2A protocol."""
        self.is_running = True
        
        # Start discovery service if enabled
        if self.config.discovery_enabled:
            self.discovery_service = asyncio.create_task(self._discovery_loop())
        
        # Start heartbeat monitoring
        asyncio.create_task(self._heartbeat_loop())
        
        # Start message processing
        asyncio.create_task(self._message_processing_loop())
        
        print(f"A2A Protocol started: {self.config.name}")
    
    async def stop(self) -> None:
        """Stop the A2A protocol."""
        self.is_running = False
        
        # Stop discovery service
        if self.discovery_service:
            self.discovery_service.cancel()
        
        # Clear registries
        self.agent_registry.clear()
        self.message_routing_table.clear()
        self.heartbeat_monitor.clear()
        
        print(f"A2A Protocol stopped: {self.config.name}")
    
    async def send_message(self, message: ProtocolMessage) -> bool:
        """Send a message through A2A protocol."""
        try:
            if not await self.validate_message(message):
                return False
            
            # Check if recipient is registered
            if message.recipient not in self.agent_registry:
                # Try to discover agent
                discovered = await self._discover_agent(message.recipient)
                if not discovered:
                    message.status = MessageStatus.FAILED
                    return False
            
            # Encrypt message if encryption is enabled
            if self.encryption_enabled:
                message = await self._encrypt_message(message)
            
            # Compress message if it exceeds threshold
            if len(json.dumps(message.content)) > self.config.compression_threshold:
                message = await self._compress_message(message)
            
            # Route message
            success = await self._route_message(message)
            
            if success:
                message.status = MessageStatus.SENT
                self.stats["messages_sent"] += 1
            else:
                message.status = MessageStatus.FAILED
                self.stats["messages_failed"] += 1
            
            return success
            
        except Exception as e:
            print(f"Error sending A2A message: {str(e)}")
            message.status = MessageStatus.FAILED
            self.stats["messages_failed"] += 1
            return False
    
    async def receive_message(self, message: ProtocolMessage) -> None:
        """Receive a message through A2A protocol."""
        try:
            # Decompress message if needed
            if message.content.get("_compressed"):
                message = await self._decompress_message(message)
            
            # Decrypt message if encryption is enabled
            if self.encryption_enabled:
                message = await self._decrypt_message(message)
            
            # Process the message
            await self.process_message(message)
            
        except Exception as e:
            print(f"Error receiving A2A message: {str(e)}")
    
    async def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """Register an agent with the A2A protocol."""
        try:
            self.agent_registry[agent_id] = {
                "id": agent_id,
                "info": agent_info,
                "registered_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Update heartbeat monitor
            self.heartbeat_monitor[agent_id] = datetime.now()
            
            # Update routing table
            self._update_routing_table(agent_id, agent_info)
            
            print(f"Agent registered: {agent_id}")
            return True
            
        except Exception as e:
            print(f"Error registering agent {agent_id}: {str(e)}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the A2A protocol."""
        try:
            if agent_id in self.agent_registry:
                del self.agent_registry[agent_id]
            
            if agent_id in self.heartbeat_monitor:
                del self.heartbeat_monitor[agent_id]
            
            # Remove from routing table
            for route_list in self.message_routing_table.values():
                if agent_id in route_list:
                    route_list.remove(agent_id)
            
            print(f"Agent unregistered: {agent_id}")
            return True
            
        except Exception as e:
            print(f"Error unregistering agent {agent_id}: {str(e)}")
            return False
    
    async def _discovery_loop(self) -> None:
        """Main discovery loop for finding other agents."""
        while self.is_running:
            try:
                await self._discover_agents()
                await asyncio.sleep(self.config.discovery_interval)
            except Exception as e:
                print(f"Error in discovery loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def _discover_agents(self) -> None:
        """Discover other agents in the network."""
        # Mock discovery - in reality would use network discovery protocols
        # like mDNS, UPnP, or custom discovery mechanisms
        
        # Simulate discovering agents
        discovered_agents = [
            {"id": "agent_001", "type": "planner", "capabilities": ["planning"]},
            {"id": "agent_002", "type": "researcher", "capabilities": ["research"]},
            {"id": "agent_003", "type": "executor", "capabilities": ["execution"]}
        ]
        
        for agent_info in discovered_agents:
            agent_id = agent_info["id"]
            if agent_id not in self.agent_registry:
                await self.register_agent(agent_id, agent_info)
    
    async def _discover_agent(self, agent_id: str) -> bool:
        """Discover a specific agent."""
        # Mock agent discovery
        await asyncio.sleep(0.1)
        
        # Simulate finding the agent
        if agent_id.startswith("agent_"):
            agent_info = {
                "id": agent_id,
                "type": "unknown",
                "capabilities": []
            }
            return await self.register_agent(agent_id, agent_info)
        
        return False
    
    async def _heartbeat_loop(self) -> None:
        """Monitor agent heartbeats."""
        while self.is_running:
            try:
                await self._check_agent_heartbeats()
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                print(f"Error in heartbeat loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def _check_agent_heartbeats(self) -> None:
        """Check agent heartbeats and mark inactive agents."""
        current_time = datetime.now()
        inactive_agents = []
        
        for agent_id, last_heartbeat in self.heartbeat_monitor.items():
            time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
            
            if time_since_heartbeat > self.config.heartbeat_interval * 3:  # 3x heartbeat interval
                inactive_agents.append(agent_id)
        
        # Mark inactive agents
        for agent_id in inactive_agents:
            if agent_id in self.agent_registry:
                self.agent_registry[agent_id]["status"] = "inactive"
                print(f"Agent marked as inactive: {agent_id}")
    
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
                print(f"Error in A2A message processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _route_message(self, message: ProtocolMessage) -> bool:
        """Route message to the appropriate agent."""
        try:
            # Check if recipient is active
            if message.recipient not in self.agent_registry:
                return False
            
            agent_info = self.agent_registry[message.recipient]
            if agent_info["status"] != "active":
                return False
            
            # In a real implementation, this would route the message
            # through the network to the target agent
            print(f"Routing message from {message.sender} to {message.recipient}")
            
            # Simulate message delivery
            await asyncio.sleep(0.01)
            
            return True
            
        except Exception as e:
            print(f"Error routing message: {str(e)}")
            return False
    
    def _update_routing_table(self, agent_id: str, agent_info: Dict[str, Any]) -> None:
        """Update the message routing table."""
        # Add agent to routing table based on capabilities
        capabilities = agent_info.get("capabilities", [])
        for capability in capabilities:
            self.message_routing_table[capability].append(agent_id)
    
    async def _encrypt_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """Encrypt message content."""
        if not self.encryption_enabled:
            return message
        
        # Mock encryption - in reality would use proper encryption
        encrypted_content = {
            "_encrypted": True,
            "_data": json.dumps(message.content)
        }
        
        message.content = encrypted_content
        return message
    
    async def _decrypt_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """Decrypt message content."""
        if not self.encryption_enabled or not message.content.get("_encrypted"):
            return message
        
        # Mock decryption - in reality would use proper decryption
        try:
            decrypted_data = json.loads(message.content["_data"])
            message.content = decrypted_data
        except Exception as e:
            print(f"Error decrypting message: {str(e)}")
        
        return message
    
    async def _compress_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """Compress message content."""
        # Mock compression - in reality would use gzip or similar
        compressed_content = {
            "_compressed": True,
            "_data": json.dumps(message.content)
        }
        
        message.content = compressed_content
        return message
    
    async def _decompress_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """Decompress message content."""
        if not message.content.get("_compressed"):
            return message
        
        # Mock decompression - in reality would use proper decompression
        try:
            decompressed_data = json.loads(message.content["_data"])
            message.content = decompressed_data
        except Exception as e:
            print(f"Error decompressing message: {str(e)}")
        
        return message
    
    async def broadcast_to_capability(self, sender: str, capability: str, 
                                    content: Dict[str, Any], 
                                    message_type: str = "broadcast") -> List[bool]:
        """Broadcast message to all agents with specific capability."""
        if capability not in self.message_routing_table:
            return []
        
        target_agents = self.message_routing_table[capability]
        results = []
        
        for agent_id in target_agents:
            if agent_id != sender and self.agent_registry.get(agent_id, {}).get("status") == "active":
                message = self.create_message(sender, agent_id, content, message_type)
                result = await self.send_message(message)
                results.append(result)
        
        return results
    
    def get_agent_registry(self) -> Dict[str, Any]:
        """Get the agent registry."""
        return self.agent_registry.copy()
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agent IDs with specific capability."""
        return self.message_routing_table.get(capability, []).copy()
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get A2A protocol information."""
        return {
            "protocol_type": "A2A",
            "version": "1.0",
            "registered_agents": len(self.agent_registry),
            "active_agents": len([a for a in self.agent_registry.values() if a["status"] == "active"]),
            "discovery_enabled": self.config.discovery_enabled,
            "encryption_enabled": self.encryption_enabled,
            "routing_table_size": len(self.message_routing_table)
        }
