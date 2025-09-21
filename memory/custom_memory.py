"""
Custom Memory Implementation

Specialized memory system for trip planning data and user preferences.
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
import json

from .base_memory import BaseMemory, MemoryConfig, MemoryType, MemoryItem, MemoryStatus


class CustomMemory(BaseMemory):
    """
    Custom memory implementation for trip planning specific data.
    
    Features:
    - Trip data storage
    - User preference tracking
    - Recommendation history
    - Booking data management
    - Travel pattern analysis
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        # Trip-specific storage
        self.trips = {}  # trip_id -> trip data
        self.user_preferences = {}  # user_id -> preferences
        self.recommendations = {}  # user_id -> recommendation history
        self.bookings = {}  # booking_id -> booking data
        self.travel_patterns = {}  # user_id -> travel patterns
        
        # Custom indexes
        self.destination_index = {}  # destination -> trip_ids
        self.date_index = {}  # date -> trip_ids
        self.user_index = {}  # user_id -> trip_ids
        
    async def store(self, content: Dict[str, Any], memory_type: MemoryType, 
                   importance: float = 0.5, tags: List[str] = None, 
                   metadata: Dict[str, Any] = None) -> str:
        """Store trip planning data."""
        memory_id = str(uuid.uuid4())
        
        # Extract trip-specific info
        data_type = content.get("type", "general")
        trip_id = content.get("trip_id")
        user_id = content.get("user_id")
        
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
                "data_type": data_type,
                "trip_id": trip_id,
                "user_id": user_id
            }
        )
        
        # Store item
        self.items[memory_id] = item
        
        # Update specialized indexes
        await self._update_trip_data(trip_id, memory_id, content)
        await self._update_user_data(user_id, memory_id, content)
        await self._update_destination_index(content)
        await self._update_date_index(content)
        
        # Update statistics
        self.stats["total_items"] += 1
        self.stats["active_items"] += 1
        
        return memory_id
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve trip data by ID."""
        if memory_id not in self.items:
            return None
        
        item = self.items[memory_id]
        await self._update_access(memory_id)
        
        return item
    
    async def search(self, query: str, memory_type: Optional[MemoryType] = None,
                    limit: int = 10, threshold: float = 0.0) -> List[MemoryItem]:
        """Search trip planning data."""
        results = []
        
        for item in self.items.values():
            if memory_type and item.memory_type != memory_type:
                continue
            
            # Search in content and metadata
            searchable_text = json.dumps(item.content, default=str).lower()
            searchable_text += " " + json.dumps(item.metadata, default=str).lower()
            query_lower = query.lower()
            
            if query_lower in searchable_text:
                # Calculate relevance based on keyword matches
                relevance = searchable_text.count(query_lower) / len(searchable_text.split())
                
                if relevance >= threshold:
                    results.append((item, relevance))
        
        # Sort by relevance and importance
        results.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
        
        # Return top results
        top_results = [item for item, _ in results[:limit]]
        
        # Update access statistics
        for item in top_results:
            await self._update_access(item.id)
        
        return top_results
    
    async def get_trip_data(self, trip_id: str) -> Dict[str, Any]:
        """Get complete trip data."""
        if trip_id not in self.trips:
            return {"trip_id": trip_id, "data": []}
        
        trip = self.trips[trip_id]
        trip_data = []
        
        for memory_id in trip.get("memory_ids", []):
            if memory_id in self.items:
                item = self.items[memory_id]
                trip_data.append({
                    "id": memory_id,
                    "content": item.content,
                    "type": item.metadata.get("data_type"),
                    "created_at": item.created_at.isoformat(),
                    "importance": item.importance
                })
        
        # Sort by creation time
        trip_data.sort(key=lambda x: x["created_at"])
        
        return {
            "trip_id": trip_id,
            "data": trip_data,
            "created_at": trip.get("created_at"),
            "last_updated": trip.get("last_updated"),
            "data_count": len(trip_data)
        }
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        if user_id not in self.user_preferences:
            return {"user_id": user_id, "preferences": {}}
        
        return self.user_preferences[user_id]
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "user_id": user_id,
                "preferences": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        
        user_data = self.user_preferences[user_id]
        user_data["preferences"].update(preferences)
        user_data["last_updated"] = datetime.now().isoformat()
        
        return True
    
    async def get_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user recommendation history."""
        if user_id not in self.recommendations:
            return []
        
        recommendations = self.recommendations[user_id]
        
        # Sort by timestamp
        recommendations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return recommendations[:limit]
    
    async def add_recommendation(self, user_id: str, recommendation: Dict[str, Any]) -> None:
        """Add a recommendation to user history."""
        if user_id not in self.recommendations:
            self.recommendations[user_id] = []
        
        recommendation["timestamp"] = datetime.now().isoformat()
        self.recommendations[user_id].append(recommendation)
    
    async def get_travel_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get user travel patterns."""
        if user_id not in self.travel_patterns:
            return {"user_id": user_id, "patterns": {}}
        
        return self.travel_patterns[user_id]
    
    async def analyze_travel_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user travel patterns."""
        if user_id not in self.user_index:
            return {"user_id": user_id, "patterns": {}}
        
        user_trips = self.user_index[user_id]
        patterns = {
            "total_trips": len(user_trips),
            "destinations": {},
            "travel_dates": [],
            "trip_durations": [],
            "budget_ranges": [],
            "accommodation_types": [],
            "activity_preferences": []
        }
        
        # Analyze each trip
        for trip_id in user_trips:
            trip_data = await self.get_trip_data(trip_id)
            
            for data_item in trip_data["data"]:
                content = data_item["content"]
                
                # Extract destination
                destination = content.get("destination")
                if destination:
                    patterns["destinations"][destination] = patterns["destinations"].get(destination, 0) + 1
                
                # Extract travel dates
                travel_date = content.get("travel_date")
                if travel_date:
                    patterns["travel_dates"].append(travel_date)
                
                # Extract trip duration
                duration = content.get("duration")
                if duration:
                    patterns["trip_durations"].append(duration)
                
                # Extract budget
                budget = content.get("budget")
                if budget:
                    patterns["budget_ranges"].append(budget)
                
                # Extract accommodation type
                accommodation = content.get("accommodation_type")
                if accommodation:
                    patterns["accommodation_types"].append(accommodation)
                
                # Extract activity preferences
                activities = content.get("activities", [])
                patterns["activity_preferences"].extend(activities)
        
        # Calculate statistics
        if patterns["trip_durations"]:
            patterns["average_duration"] = sum(patterns["trip_durations"]) / len(patterns["trip_durations"])
        
        if patterns["budget_ranges"]:
            patterns["average_budget"] = sum(patterns["budget_ranges"]) / len(patterns["budget_ranges"])
        
        # Most common destinations
        patterns["top_destinations"] = sorted(
            patterns["destinations"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Store patterns
        self.travel_patterns[user_id] = {
            "user_id": user_id,
            "patterns": patterns,
            "analyzed_at": datetime.now().isoformat()
        }
        
        return patterns
    
    async def search_by_destination(self, destination: str, limit: int = 10) -> List[MemoryItem]:
        """Search trips by destination."""
        if destination not in self.destination_index:
            return []
        
        trip_ids = self.destination_index[destination]
        results = []
        
        for trip_id in trip_ids:
            if trip_id in self.trips:
                memory_ids = self.trips[trip_id].get("memory_ids", [])
                for memory_id in memory_ids:
                    if memory_id in self.items:
                        results.append(self.items[memory_id])
        
        # Sort by importance and creation time
        results.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        
        return results[:limit]
    
    async def search_by_date_range(self, start_date: str, end_date: str, 
                                 limit: int = 10) -> List[MemoryItem]:
        """Search trips by date range."""
        results = []
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        for date_str, trip_ids in self.date_index.items():
            try:
                date_dt = datetime.fromisoformat(date_str)
                if start_dt <= date_dt <= end_dt:
                    for trip_id in trip_ids:
                        if trip_id in self.trips:
                            memory_ids = self.trips[trip_id].get("memory_ids", [])
                            for memory_id in memory_ids:
                                if memory_id in self.items:
                                    results.append(self.items[memory_id])
            except ValueError:
                continue
        
        # Sort by creation time
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        return results[:limit]
    
    async def _update_trip_data(self, trip_id: str, memory_id: str, content: Dict[str, Any]) -> None:
        """Update trip data tracking."""
        if not trip_id:
            return
        
        if trip_id not in self.trips:
            self.trips[trip_id] = {
                "trip_id": trip_id,
                "memory_ids": [],
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        
        trip = self.trips[trip_id]
        trip["memory_ids"].append(memory_id)
        trip["last_updated"] = datetime.now().isoformat()
    
    async def _update_user_data(self, user_id: str, memory_id: str, content: Dict[str, Any]) -> None:
        """Update user data tracking."""
        if not user_id:
            return
        
        if user_id not in self.user_index:
            self.user_index[user_id] = []
        
        # Get trip_id from content
        trip_id = content.get("trip_id")
        if trip_id and trip_id not in self.user_index[user_id]:
            self.user_index[user_id].append(trip_id)
    
    async def _update_destination_index(self, content: Dict[str, Any]) -> None:
        """Update destination index."""
        destination = content.get("destination")
        trip_id = content.get("trip_id")
        
        if destination and trip_id:
            if destination not in self.destination_index:
                self.destination_index[destination] = []
            
            if trip_id not in self.destination_index[destination]:
                self.destination_index[destination].append(trip_id)
    
    async def _update_date_index(self, content: Dict[str, Any]) -> None:
        """Update date index."""
        travel_date = content.get("travel_date")
        trip_id = content.get("trip_id")
        
        if travel_date and trip_id:
            if travel_date not in self.date_index:
                self.date_index[travel_date] = []
            
            if trip_id not in self.date_index[travel_date]:
                self.date_index[travel_date].append(trip_id)
    
    async def get_custom_stats(self) -> Dict[str, Any]:
        """Get custom memory statistics."""
        return {
            "total_trips": len(self.trips),
            "total_users": len(self.user_index),
            "total_destinations": len(self.destination_index),
            "total_dates": len(self.date_index),
            "user_preferences": len(self.user_preferences),
            "recommendations": sum(len(recs) for recs in self.recommendations.values()),
            "travel_patterns": len(self.travel_patterns)
        }
    
    async def cleanup_old_data(self, days: int = 90) -> int:
        """Clean up old trip data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for trip_id, trip in list(self.trips.items()):
            last_updated = trip.get("last_updated")
            if last_updated:
                last_updated_date = datetime.fromisoformat(last_updated)
                if last_updated_date < cutoff_date:
                    # Archive old trip data
                    for memory_id in trip.get("memory_ids", []):
                        if memory_id in self.items:
                            self.items[memory_id].status = MemoryStatus.ARCHIVED
                    
                    del self.trips[trip_id]
                    cleaned_count += 1
        
        return cleaned_count
