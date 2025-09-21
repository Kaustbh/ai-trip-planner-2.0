"""
Base Memory Class

Defines the common interface for all memory implementations in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime
import json

from pydantic import BaseModel, Field


class MemoryType(Enum):
    """Memory type enumeration."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryStatus(Enum):
    """Memory status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"


@dataclass
class MemoryItem:
    """Base memory item structure."""
    id: str
    content: Dict[str, Any]
    memory_type: MemoryType
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    importance: float = 0.5  # 0.0 to 1.0
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class MemoryConfig(BaseModel):
    """Configuration for memory system."""
    memory_type: MemoryType
    max_items: int = 1000
    ttl: Optional[int] = None  # Time to live in seconds
    auto_cleanup: bool = True
    compression_enabled: bool = False
    encryption_enabled: bool = False
    indexing_enabled: bool = True
    search_enabled: bool = True


class BaseMemory(ABC):
    """
    Base class for all memory implementations.
    
    Provides common functionality for:
    - Memory storage and retrieval
    - Search and filtering
    - Memory management
    - Access tracking
    - Cleanup and archiving
    """
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.memory_id = str(uuid.uuid4())
        self.items = {}
        self.index = {}
        self.stats = {
            "total_items": 0,
            "active_items": 0,
            "archived_items": 0,
            "total_accesses": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
    @abstractmethod
    async def store(self, content: Dict[str, Any], memory_type: MemoryType, 
                   importance: float = 0.5, tags: List[str] = None, 
                   metadata: Dict[str, Any] = None) -> str:
        """
        Store a memory item.
        
        Args:
            content: The content to store
            memory_type: Type of memory
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags for categorization
            metadata: Optional metadata
            
        Returns:
            Memory item ID
        """
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            Memory item or None if not found
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, memory_type: Optional[MemoryType] = None,
                    limit: int = 10, threshold: float = 0.0) -> List[MemoryItem]:
        """
        Search for memory items.
        
        Args:
            query: Search query
            memory_type: Optional memory type filter
            limit: Maximum number of results
            threshold: Minimum relevance threshold
            
        Returns:
            List of matching memory items
        """
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory item.
        
        Args:
            memory_id: ID of the memory item
            updates: Updates to apply
            
        Returns:
            True if updated successfully
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            True if deleted successfully
        """
        pass
    
    async def store_multiple(self, items: List[Dict[str, Any]]) -> List[str]:
        """Store multiple memory items."""
        memory_ids = []
        for item in items:
            memory_id = await self.store(**item)
            memory_ids.append(memory_id)
        return memory_ids
    
    async def retrieve_multiple(self, memory_ids: List[str]) -> List[MemoryItem]:
        """Retrieve multiple memory items."""
        items = []
        for memory_id in memory_ids:
            item = await self.retrieve(memory_id)
            if item:
                items.append(item)
        return items
    
    async def search_by_tags(self, tags: List[str], memory_type: Optional[MemoryType] = None,
                           limit: int = 10) -> List[MemoryItem]:
        """Search memory items by tags."""
        results = []
        for item in self.items.values():
            if memory_type and item.memory_type != memory_type:
                continue
            
            if any(tag in item.tags for tag in tags):
                results.append(item)
        
        # Sort by importance and last accessed
        results.sort(key=lambda x: (x.importance, x.last_accessed), reverse=True)
        return results[:limit]
    
    async def get_recent(self, memory_type: Optional[MemoryType] = None, 
                        limit: int = 10) -> List[MemoryItem]:
        """Get recent memory items."""
        items = list(self.items.values())
        
        if memory_type:
            items = [item for item in items if item.memory_type == memory_type]
        
        # Sort by creation time
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
    
    async def get_frequent(self, memory_type: Optional[MemoryType] = None,
                          limit: int = 10) -> List[MemoryItem]:
        """Get frequently accessed memory items."""
        items = list(self.items.values())
        
        if memory_type:
            items = [item for item in items if item.memory_type == memory_type]
        
        # Sort by access count
        items.sort(key=lambda x: x.access_count, reverse=True)
        return items[:limit]
    
    async def cleanup(self) -> int:
        """Clean up expired or old memory items."""
        if not self.config.auto_cleanup:
            return 0
        
        cleaned_count = 0
        current_time = datetime.now()
        
        for memory_id, item in list(self.items.items()):
            should_cleanup = False
            
            # Check TTL
            if self.config.ttl:
                age = (current_time - item.created_at).total_seconds()
                if age > self.config.ttl:
                    should_cleanup = True
            
            # Check if item is marked for deletion
            if item.status == MemoryStatus.DELETED:
                should_cleanup = True
            
            # Check if item is expired
            if item.status == MemoryStatus.EXPIRED:
                should_cleanup = True
            
            if should_cleanup:
                await self._cleanup_item(memory_id)
                cleaned_count += 1
        
        return cleaned_count
    
    async def _cleanup_item(self, memory_id: str) -> None:
        """Clean up a specific memory item."""
        if memory_id in self.items:
            del self.items[memory_id]
            self.stats["total_items"] -= 1
            
            # Update index
            await self._update_index_remove(memory_id)
    
    async def archive(self, memory_id: str) -> bool:
        """Archive a memory item."""
        if memory_id not in self.items:
            return False
        
        item = self.items[memory_id]
        item.status = MemoryStatus.ARCHIVED
        item.last_accessed = datetime.now()
        
        self.stats["active_items"] -= 1
        self.stats["archived_items"] += 1
        
        return True
    
    async def restore(self, memory_id: str) -> bool:
        """Restore an archived memory item."""
        if memory_id not in self.items:
            return False
        
        item = self.items[memory_id]
        if item.status != MemoryStatus.ARCHIVED:
            return False
        
        item.status = MemoryStatus.ACTIVE
        item.last_accessed = datetime.now()
        
        self.stats["active_items"] += 1
        self.stats["archived_items"] -= 1
        
        return True
    
    async def _update_access(self, memory_id: str) -> None:
        """Update access statistics for a memory item."""
        if memory_id in self.items:
            item = self.items[memory_id]
            item.last_accessed = datetime.now()
            item.access_count += 1
            self.stats["total_accesses"] += 1
    
    async def _update_index_add(self, item: MemoryItem) -> None:
        """Update index when adding an item."""
        if not self.config.indexing_enabled:
            return
        
        # Add to memory type index
        if item.memory_type not in self.index:
            self.index[item.memory_type] = []
        self.index[item.memory_type].append(item.id)
        
        # Add to tag index
        for tag in item.tags:
            if tag not in self.index:
                self.index[tag] = []
            self.index[tag].append(item.id)
    
    async def _update_index_remove(self, memory_id: str) -> None:
        """Update index when removing an item."""
        if not self.config.indexing_enabled:
            return
        
        # Remove from all indexes
        for key, item_ids in self.index.items():
            if memory_id in item_ids:
                item_ids.remove(memory_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.config.memory_type.value,
            "stats": self.stats.copy(),
            "config": {
                "max_items": self.config.max_items,
                "ttl": self.config.ttl,
                "auto_cleanup": self.config.auto_cleanup,
                "indexing_enabled": self.config.indexing_enabled
            }
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        total_size = sum(len(json.dumps(item.content)) for item in self.items.values())
        
        return {
            "total_items": len(self.items),
            "total_size_bytes": total_size,
            "average_item_size": total_size / len(self.items) if self.items else 0,
            "memory_usage_percentage": (len(self.items) / self.config.max_items) * 100
        }
    
    def clear_all(self) -> None:
        """Clear all memory items."""
        self.items.clear()
        self.index.clear()
        self.stats = {
            "total_items": 0,
            "active_items": 0,
            "archived_items": 0,
            "total_accesses": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.config.memory_type.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.memory_id}, type={self.config.memory_type.value})>"
