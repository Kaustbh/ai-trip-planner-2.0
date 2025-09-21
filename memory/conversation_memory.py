"""
Conversation Memory Implementation

Memory system specialized for storing and retrieving conversation history and context.
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
import json

from .base_memory import BaseMemory, MemoryConfig, MemoryType, MemoryItem, MemoryStatus


class ConversationMemory(BaseMemory):
    """
    Memory implementation specialized for conversation history.
    
    Features:
    - Conversation thread management
    - Context tracking
    - Message threading
    - Conversation summarization
    - Context-aware retrieval
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        # Conversation-specific storage
        self.conversations = {}  # conversation_id -> conversation data
        self.message_threads = {}  # thread_id -> list of message_ids
        self.context_cache = {}  # conversation_id -> context data
        
        # Conversation settings
        self.max_conversation_length = 100
        self.context_window = 10  # Number of recent messages to keep in context
        self.auto_summarize_threshold = 50  # Auto-summarize after N messages
        
    async def store(self, content: Dict[str, Any], memory_type: MemoryType, 
                   importance: float = 0.5, tags: List[str] = None, 
                   metadata: Dict[str, Any] = None) -> str:
        """Store a conversation message."""
        memory_id = str(uuid.uuid4())
        
        # Extract conversation info
        conversation_id = content.get("conversation_id", "default")
        thread_id = content.get("thread_id", conversation_id)
        message_type = content.get("message_type", "user")
        sender = content.get("sender", "unknown")
        timestamp = content.get("timestamp", datetime.now().isoformat())
        
        # Create memory item
        item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            importance=importance,
            tags=tags or [],
            metadata={
                **(metadata or {}),
                "conversation_id": conversation_id,
                "thread_id": thread_id,
                "message_type": message_type,
                "sender": sender,
                "timestamp": timestamp
            }
        )
        
        # Store item
        self.items[memory_id] = item
        
        # Update conversation tracking
        await self._update_conversation(conversation_id, memory_id, content)
        await self._update_thread(thread_id, memory_id)
        
        # Update statistics
        self.stats["total_items"] += 1
        self.stats["active_items"] += 1
        
        # Check if auto-summarization is needed
        if len(self.conversations.get(conversation_id, {}).get("messages", [])) > self.auto_summarize_threshold:
            await self._auto_summarize_conversation(conversation_id)
        
        return memory_id
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a conversation message by ID."""
        if memory_id not in self.items:
            return None
        
        item = self.items[memory_id]
        await self._update_access(memory_id)
        
        return item
    
    async def search(self, query: str, memory_type: Optional[MemoryType] = None,
                    limit: int = 10, threshold: float = 0.0) -> List[MemoryItem]:
        """Search conversation messages."""
        results = []
        
        for item in self.items.values():
            if memory_type and item.memory_type != memory_type:
                continue
            
            # Simple text search in content
            content_text = json.dumps(item.content, default=str).lower()
            query_lower = query.lower()
            
            if query_lower in content_text:
                # Calculate simple relevance score
                relevance = content_text.count(query_lower) / len(content_text.split())
                
                if relevance >= threshold:
                    results.append((item, relevance))
        
        # Sort by relevance and timestamp
        results.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
        
        # Return top results
        top_results = [item for item, _ in results[:limit]]
        
        # Update access statistics
        for item in top_results:
            await self._update_access(item.id)
        
        return top_results
    
    async def get_conversation(self, conversation_id: str, 
                             include_context: bool = True) -> Dict[str, Any]:
        """Get a complete conversation."""
        if conversation_id not in self.conversations:
            return {"conversation_id": conversation_id, "messages": []}
        
        conversation = self.conversations[conversation_id]
        messages = []
        
        for message_id in conversation.get("messages", []):
            if message_id in self.items:
                item = self.items[message_id]
                message_data = {
                    "id": message_id,
                    "content": item.content,
                    "sender": item.metadata.get("sender"),
                    "message_type": item.metadata.get("message_type"),
                    "timestamp": item.metadata.get("timestamp"),
                    "created_at": item.created_at.isoformat()
                }
                messages.append(message_data)
        
        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        result = {
            "conversation_id": conversation_id,
            "messages": messages,
            "message_count": len(messages),
            "created_at": conversation.get("created_at"),
            "last_activity": conversation.get("last_activity")
        }
        
        if include_context:
            result["context"] = await self._get_conversation_context(conversation_id)
        
        return result
    
    async def get_conversation_context(self, conversation_id: str, 
                                     window_size: int = None) -> Dict[str, Any]:
        """Get conversation context for a specific conversation."""
        window_size = window_size or self.context_window
        
        if conversation_id not in self.conversations:
            return {"context": [], "summary": None}
        
        conversation = self.conversations[conversation_id]
        recent_messages = conversation.get("messages", [])[-window_size:]
        
        context = []
        for message_id in recent_messages:
            if message_id in self.items:
                item = self.items[message_id]
                context.append({
                    "id": message_id,
                    "content": item.content,
                    "sender": item.metadata.get("sender"),
                    "timestamp": item.metadata.get("timestamp")
                })
        
        # Get conversation summary if available
        summary = conversation.get("summary")
        
        return {
            "context": context,
            "summary": summary,
            "window_size": len(context)
        }
    
    async def get_thread_messages(self, thread_id: str) -> List[MemoryItem]:
        """Get all messages in a thread."""
        if thread_id not in self.message_threads:
            return []
        
        messages = []
        for message_id in self.message_threads[thread_id]:
            if message_id in self.items:
                messages.append(self.items[message_id])
        
        # Sort by creation time
        messages.sort(key=lambda x: x.created_at)
        return messages
    
    async def summarize_conversation(self, conversation_id: str) -> str:
        """Generate a summary of a conversation."""
        if conversation_id not in self.conversations:
            return "No conversation found"
        
        conversation = self.conversations[conversation_id]
        messages = conversation.get("messages", [])
        
        if not messages:
            return "Empty conversation"
        
        # Get message contents
        message_texts = []
        for message_id in messages:
            if message_id in self.items:
                item = self.items[message_id]
                content = item.content.get("text", "")
                sender = item.metadata.get("sender", "Unknown")
                message_texts.append(f"{sender}: {content}")
        
        # Simple summarization - in reality would use AI summarization
        total_messages = len(message_texts)
        participants = set()
        
        for message_id in messages:
            if message_id in self.items:
                sender = self.items[message_id].metadata.get("sender")
                if sender:
                    participants.add(sender)
        
        summary = f"Conversation with {len(participants)} participants, {total_messages} messages"
        
        # Store summary
        conversation["summary"] = summary
        conversation["summarized_at"] = datetime.now().isoformat()
        
        return summary
    
    async def _update_conversation(self, conversation_id: str, message_id: str, 
                                 content: Dict[str, Any]) -> None:
        """Update conversation tracking."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
        
        conversation = self.conversations[conversation_id]
        conversation["messages"].append(message_id)
        conversation["last_activity"] = datetime.now().isoformat()
        
        # Trim conversation if too long
        if len(conversation["messages"]) > self.max_conversation_length:
            # Keep only recent messages
            conversation["messages"] = conversation["messages"][-self.max_conversation_length:]
    
    async def _update_thread(self, thread_id: str, message_id: str) -> None:
        """Update message thread tracking."""
        if thread_id not in self.message_threads:
            self.message_threads[thread_id] = []
        
        self.message_threads[thread_id].append(message_id)
    
    async def _get_conversation_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation context."""
        if conversation_id not in self.conversations:
            return []
        
        conversation = self.conversations[conversation_id]
        recent_messages = conversation.get("messages", [])[-self.context_window:]
        
        context = []
        for message_id in recent_messages:
            if message_id in self.items:
                item = self.items[message_id]
                context.append({
                    "id": message_id,
                    "content": item.content,
                    "sender": item.metadata.get("sender"),
                    "timestamp": item.metadata.get("timestamp")
                })
        
        return context
    
    async def _auto_summarize_conversation(self, conversation_id: str) -> None:
        """Automatically summarize a long conversation."""
        try:
            summary = await self.summarize_conversation(conversation_id)
            print(f"Auto-summarized conversation {conversation_id}: {summary}")
        except Exception as e:
            print(f"Auto-summarization failed for {conversation_id}: {str(e)}")
    
    async def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        total_conversations = len(self.conversations)
        total_threads = len(self.message_threads)
        
        # Calculate average conversation length
        avg_length = 0
        if total_conversations > 0:
            total_messages = sum(len(conv.get("messages", [])) for conv in self.conversations.values())
            avg_length = total_messages / total_conversations
        
        return {
            "total_conversations": total_conversations,
            "total_threads": total_threads,
            "average_conversation_length": avg_length,
            "max_conversation_length": self.max_conversation_length,
            "context_window": self.context_window
        }
    
    async def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up conversations older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for conversation_id, conversation in list(self.conversations.items()):
            last_activity = conversation.get("last_activity")
            if last_activity:
                last_activity_date = datetime.fromisoformat(last_activity)
                if last_activity_date < cutoff_date:
                    # Archive old conversation
                    for message_id in conversation.get("messages", []):
                        if message_id in self.items:
                            self.items[message_id].status = MemoryStatus.ARCHIVED
                    
                    del self.conversations[conversation_id]
                    cleaned_count += 1
        
        return cleaned_count
    
    def set_max_conversation_length(self, length: int) -> None:
        """Set maximum conversation length."""
        self.max_conversation_length = length
    
    def set_context_window(self, window_size: int) -> None:
        """Set context window size."""
        self.context_window = window_size
    
    def set_auto_summarize_threshold(self, threshold: int) -> None:
        """Set auto-summarization threshold."""
        self.auto_summarize_threshold = threshold
