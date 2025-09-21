"""
Vector Memory Implementation

Memory system using vector embeddings for semantic search and similarity matching.
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
import numpy as np
from datetime import datetime
import json

from .base_memory import BaseMemory, MemoryConfig, MemoryType, MemoryItem, MemoryStatus


class VectorMemory(BaseMemory):
    """
    Memory implementation using vector embeddings for semantic search.
    
    Features:
    - Vector embeddings for content
    - Semantic similarity search
    - Clustering and categorization
    - Similarity-based retrieval
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        # Vector storage
        self.embeddings = {}  # memory_id -> embedding vector
        self.embedding_dim = 384  # Default embedding dimension
        self.similarity_threshold = 0.7
        
        # Index for fast similarity search
        self.vector_index = None
        self.index_built = False
        
    async def store(self, content: Dict[str, Any], memory_type: MemoryType, 
                   importance: float = 0.5, tags: List[str] = None, 
                   metadata: Dict[str, Any] = None) -> str:
        """Store a memory item with vector embedding."""
        memory_id = str(uuid.uuid4())
        
        # Create memory item
        item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Generate embedding
        embedding = await self._generate_embedding(content)
        self.embeddings[memory_id] = embedding
        
        # Store item
        self.items[memory_id] = item
        
        # Update statistics
        self.stats["total_items"] += 1
        self.stats["active_items"] += 1
        
        # Update index
        await self._update_index_add(item)
        
        # Rebuild vector index if needed
        if not self.index_built:
            await self._build_vector_index()
        
        return memory_id
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID."""
        if memory_id not in self.items:
            return None
        
        item = self.items[memory_id]
        await self._update_access(memory_id)
        
        return item
    
    async def search(self, query: str, memory_type: Optional[MemoryType] = None,
                    limit: int = 10, threshold: float = 0.0) -> List[MemoryItem]:
        """Search memory items using semantic similarity."""
        if not self.embeddings:
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embedding({"text": query})
        
        # Calculate similarities
        similarities = []
        for memory_id, embedding in self.embeddings.items():
            if memory_id not in self.items:
                continue
            
            item = self.items[memory_id]
            
            # Filter by memory type if specified
            if memory_type and item.memory_type != memory_type:
                continue
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            
            if similarity >= threshold:
                similarities.append((item, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = [item for item, _ in similarities[:limit]]
        
        # Update access statistics
        for item in results:
            await self._update_access(item.id)
        
        return results
    
    async def find_similar(self, memory_id: str, limit: int = 5, 
                          threshold: float = 0.7) -> List[MemoryItem]:
        """Find similar memory items to a given item."""
        if memory_id not in self.embeddings:
            return []
        
        target_embedding = self.embeddings[memory_id]
        similarities = []
        
        for other_id, embedding in self.embeddings.items():
            if other_id == memory_id:
                continue
            
            if other_id not in self.items:
                continue
            
            similarity = self._cosine_similarity(target_embedding, embedding)
            
            if similarity >= threshold:
                item = self.items[other_id]
                similarities.append((item, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, _ in similarities[:limit]]
    
    async def cluster(self, memory_type: Optional[MemoryType] = None, 
                     num_clusters: int = 5) -> Dict[int, List[MemoryItem]]:
        """Cluster memory items by similarity."""
        if not self.embeddings:
            return {}
        
        # Get embeddings for clustering
        embeddings_list = []
        memory_ids = []
        
        for memory_id, embedding in self.embeddings.items():
            if memory_id not in self.items:
                continue
            
            item = self.items[memory_id]
            if memory_type and item.memory_type != memory_type:
                continue
            
            embeddings_list.append(embedding)
            memory_ids.append(memory_id)
        
        if len(embeddings_list) < num_clusters:
            return {}
        
        # Simple clustering using k-means
        clusters = await self._kmeans_clustering(embeddings_list, num_clusters)
        
        # Group items by cluster
        result = {}
        for i, cluster_id in enumerate(clusters):
            memory_id = memory_ids[i]
            item = self.items[memory_id]
            
            if cluster_id not in result:
                result[cluster_id] = []
            result[cluster_id].append(item)
        
        return result
    
    async def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory item and regenerate embedding if needed."""
        if memory_id not in self.items:
            return False
        
        item = self.items[memory_id]
        
        # Update content if provided
        if "content" in updates:
            item.content.update(updates["content"])
            
            # Regenerate embedding
            new_embedding = await self._generate_embedding(item.content)
            self.embeddings[memory_id] = new_embedding
            
            # Rebuild index
            await self._build_vector_index()
        
        # Update other fields
        if "importance" in updates:
            item.importance = updates["importance"]
        
        if "tags" in updates:
            item.tags = updates["tags"]
            await self._update_index_remove(memory_id)
            await self._update_index_add(item)
        
        if "metadata" in updates:
            item.metadata.update(updates["metadata"])
        
        item.last_accessed = datetime.now()
        return True
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item."""
        if memory_id not in self.items:
            return False
        
        # Remove from storage
        del self.items[memory_id]
        
        if memory_id in self.embeddings:
            del self.embeddings[memory_id]
        
        # Update statistics
        self.stats["total_items"] -= 1
        self.stats["active_items"] -= 1
        
        # Update index
        await self._update_index_remove(memory_id)
        
        # Rebuild vector index
        await self._build_vector_index()
        
        return True
    
    async def _generate_embedding(self, content: Dict[str, Any]) -> np.ndarray:
        """Generate vector embedding for content."""
        # Mock embedding generation - in reality would use sentence transformers or similar
        text = json.dumps(content, sort_keys=True)
        
        # Simple hash-based embedding for demonstration
        hash_value = hash(text) % (2**32)
        
        # Convert to embedding vector
        embedding = np.random.normal(0, 1, self.embedding_dim)
        embedding[0] = hash_value / (2**32)  # Use hash as first dimension
        
        return embedding
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _build_vector_index(self) -> None:
        """Build vector index for fast similarity search."""
        if not self.embeddings:
            self.index_built = False
            return
        
        # Simple index - in reality would use FAISS or similar
        self.vector_index = list(self.embeddings.keys())
        self.index_built = True
    
    async def _kmeans_clustering(self, embeddings: List[np.ndarray], 
                                num_clusters: int) -> List[int]:
        """Simple k-means clustering implementation."""
        if len(embeddings) < num_clusters:
            return [0] * len(embeddings)
        
        # Initialize centroids randomly
        centroids = []
        for _ in range(num_clusters):
            centroid = np.random.normal(0, 1, self.embedding_dim)
            centroids.append(centroid)
        
        # Assign points to clusters
        clusters = [0] * len(embeddings)
        
        for _ in range(10):  # Max iterations
            # Assign each point to closest centroid
            for i, embedding in enumerate(embeddings):
                similarities = [self._cosine_similarity(embedding, centroid) 
                              for centroid in centroids]
                clusters[i] = similarities.index(max(similarities))
            
            # Update centroids
            new_centroids = []
            for cluster_id in range(num_clusters):
                cluster_embeddings = [embeddings[i] for i, c in enumerate(clusters) 
                                    if c == cluster_id]
                if cluster_embeddings:
                    centroid = np.mean(cluster_embeddings, axis=0)
                    new_centroids.append(centroid)
                else:
                    new_centroids.append(centroids[cluster_id])
            
            centroids = new_centroids
        
        return clusters
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        if not self.embeddings:
            return {"total_embeddings": 0, "embedding_dimension": self.embedding_dim}
        
        return {
            "total_embeddings": len(self.embeddings),
            "embedding_dimension": self.embedding_dim,
            "index_built": self.index_built,
            "similarity_threshold": self.similarity_threshold
        }
    
    def set_similarity_threshold(self, threshold: float) -> None:
        """Set similarity threshold for search."""
        self.similarity_threshold = max(0.0, min(1.0, threshold))
    
    def set_embedding_dimension(self, dimension: int) -> None:
        """Set embedding dimension."""
        self.embedding_dim = dimension
