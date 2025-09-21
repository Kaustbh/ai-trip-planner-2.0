"""
Base Protocol Class

Defines the common interface for all communication protocols in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid
from datetime import datetime
import json

from pydantic import BaseModel, Field


class ProtocolType(Enum):
    """Protocol type enumeration."""
    MCP = "mcp"
    A2A = "a2a"
    CUSTOM = "custom"
    HYBRID = "hybrid"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageStatus(Enum):
    """Message status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    PROCESSED = "processed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ProtocolMessage:
    """Base message structure for protocol communication."""
    id: str
    sender: str
    recipient: str
    content: Dict[str, Any]
    message_type: str
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = None
    status: MessageStatus = MessageStatus.PENDING
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ProtocolConfig(BaseModel):
    """Configuration for a communication protocol."""
    protocol_type: ProtocolType
    name: str
    enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1
    max_message_size: int = 1024 * 1024  # 1MB
    compression_enabled: bool = False
    encryption_enabled: bool = False
    message_ordering: bool = True
    delivery_guarantee: str = "at_least_once"  # at_least_once, exactly_once, at_most_once


class BaseProtocol(ABC):
    """
    Base class for all communication protocols.
    
    Provides common functionality for:
    - Message routing
    - Error handling
    - Retry logic
    - Message validation
    - Protocol management
    """
    
    def __init__(self, config: ProtocolConfig):
        self.config = config
        self.protocol_id = str(uuid.uuid4())
        self.message_handlers = {}
        self.message_queue = asyncio.Queue()
        self.active_connections = {}
        self.message_history = []
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "average_latency": 0.0
        }
        self.is_running = False
        
    @abstractmethod
    async def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send a message through the protocol.
        
        Args:
            message: The message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def receive_message(self, message: ProtocolMessage) -> None:
        """
        Receive a message through the protocol.
        
        Args:
            message: The received message
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the protocol."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the protocol."""
        pass
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def unregister_handler(self, message_type: str, handler: Callable) -> None:
        """Unregister a message handler."""
        if message_type in self.message_handlers:
            if handler in self.message_handlers[message_type]:
                self.message_handlers[message_type].remove(handler)
    
    async def process_message(self, message: ProtocolMessage) -> None:
        """Process a received message by calling registered handlers."""
        try:
            message.status = MessageStatus.PROCESSED
            self.stats["messages_received"] += 1
            
            # Call registered handlers
            handlers = self.message_handlers.get(message.message_type, [])
            for handler in handlers:
                try:
                    await handler(message)
                except Exception as e:
                    print(f"Error in message handler: {str(e)}")
            
            # Update message history
            self.message_history.append(message)
            
        except Exception as e:
            message.status = MessageStatus.FAILED
            self.stats["messages_failed"] += 1
            print(f"Error processing message: {str(e)}")
    
    async def validate_message(self, message: ProtocolMessage) -> bool:
        """Validate a message before processing."""
        if not message.id:
            return False
        
        if not message.sender or not message.recipient:
            return False
        
        if not message.content:
            return False
        
        # Check message size
        message_size = len(json.dumps(message.content))
        if message_size > self.config.max_message_size:
            return False
        
        # Check TTL
        if message.ttl:
            age = (datetime.now() - message.timestamp).total_seconds()
            if age > message.ttl:
                return False
        
        return True
    
    async def retry_message(self, message: ProtocolMessage) -> bool:
        """Retry sending a failed message."""
        for attempt in range(self.config.retry_attempts):
            try:
                success = await self.send_message(message)
                if success:
                    return True
                
                # Wait before retry
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                
            except Exception as e:
                print(f"Retry attempt {attempt + 1} failed: {str(e)}")
        
        message.status = MessageStatus.FAILED
        self.stats["messages_failed"] += 1
        return False
    
    def create_message(self, sender: str, recipient: str, content: Dict[str, Any], 
                      message_type: str = "default", priority: MessagePriority = MessagePriority.NORMAL,
                      correlation_id: Optional[str] = None, reply_to: Optional[str] = None,
                      ttl: Optional[int] = None) -> ProtocolMessage:
        """Create a new protocol message."""
        return ProtocolMessage(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            content=content,
            message_type=message_type,
            priority=priority,
            correlation_id=correlation_id,
            reply_to=reply_to,
            ttl=ttl
        )
    
    async def broadcast_message(self, sender: str, content: Dict[str, Any], 
                              message_type: str = "broadcast", 
                              exclude: Optional[List[str]] = None) -> List[bool]:
        """Broadcast a message to all connected agents."""
        exclude = exclude or []
        results = []
        
        for agent_id in self.active_connections:
            if agent_id not in exclude and agent_id != sender:
                message = self.create_message(sender, agent_id, content, message_type)
                result = await self.send_message(message)
                results.append(result)
        
        return results
    
    async def send_request(self, sender: str, recipient: str, content: Dict[str, Any],
                          message_type: str = "request", timeout: Optional[int] = None) -> Optional[ProtocolMessage]:
        """Send a request and wait for a response."""
        correlation_id = str(uuid.uuid4())
        timeout = timeout or self.config.timeout
        
        # Create request message
        request = self.create_message(
            sender=sender,
            recipient=recipient,
            content=content,
            message_type=message_type,
            correlation_id=correlation_id
        )
        
        # Send request
        success = await self.send_message(request)
        if not success:
            return None
        
        # Wait for response
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check for response in message history
            for message in self.message_history:
                if (message.correlation_id == correlation_id and 
                    message.sender == recipient and 
                    message.recipient == sender):
                    return message
            
            await asyncio.sleep(0.1)
        
        return None  # Timeout
    
    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            "protocol_id": self.protocol_id,
            "protocol_type": self.config.protocol_type.value,
            "is_running": self.is_running,
            "active_connections": len(self.active_connections),
            "stats": self.stats.copy(),
            "message_history_size": len(self.message_history)
        }
    
    def get_message_history(self, limit: int = 100) -> List[ProtocolMessage]:
        """Get recent message history."""
        return self.message_history[-limit:] if self.message_history else []
    
    def clear_message_history(self) -> None:
        """Clear message history."""
        self.message_history.clear()
    
    def __str__(self) -> str:
        return f"{self.config.name} ({self.config.protocol_type.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.protocol_id}, type={self.config.protocol_type.value})>"
