"""
Search Tool

Tool for performing various types of searches (web, local, semantic).
"""

from typing import Dict, Any, List, Optional
import asyncio
import httpx
from datetime import datetime

from .base_tool import BaseTool, ToolConfig, ToolType, ToolCapability, ToolResult


class SearchTool(BaseTool):
    """
    Tool for performing searches across different sources.
    
    Capabilities:
    - Web search (Google, Bing, etc.)
    - Local database search
    - Semantic search
    - Image search
    - News search
    """
    
    def __init__(self, config: Optional[ToolConfig] = None):
        if config is None:
            config = ToolConfig(
                name="Search Tool",
                tool_type=ToolType.SEARCH,
                description="Multi-source search tool",
                capabilities=[ToolCapability.SEARCH, ToolCapability.READ],
                timeout=30,
                rate_limit=60
            )
        super().__init__(config)
        
        # Search providers
        self.search_providers = {
            "google": {
                "enabled": True,
                "api_key": None,
                "search_engine_id": None,
                "base_url": "https://www.googleapis.com/customsearch/v1"
            },
            "bing": {
                "enabled": True,
                "api_key": None,
                "base_url": "https://api.bing.microsoft.com/v7.0/search"
            },
            "duckduckgo": {
                "enabled": True,
                "api_key": None,
                "base_url": "https://api.duckduckgo.com"
            }
        }
        
        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute search with given parameters."""
        search_type = parameters.get("type", "web")
        query = parameters.get("query", "")
        limit = parameters.get("limit", 10)
        provider = parameters.get("provider", "google")
        
        if not query:
            return ToolResult(
                success=False,
                error="Search query is required"
            )
        
        try:
            if search_type == "web":
                results = await self._web_search(query, limit, provider)
            elif search_type == "images":
                results = await self._image_search(query, limit, provider)
            elif search_type == "news":
                results = await self._news_search(query, limit, provider)
            elif search_type == "local":
                results = await self._local_search(query, limit)
            elif search_type == "semantic":
                results = await self._semantic_search(query, limit)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported search type: {search_type}"
                )
            
            return ToolResult(
                success=True,
                data=results,
                metadata={
                    "search_type": search_type,
                    "provider": provider,
                    "query": query,
                    "result_count": len(results)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate search parameters."""
        required_fields = ["query"]
        for field in required_fields:
            if field not in parameters:
                return False
        
        # Validate search type
        valid_types = ["web", "images", "news", "local", "semantic"]
        search_type = parameters.get("type", "web")
        if search_type not in valid_types:
            return False
        
        # Validate limit
        limit = parameters.get("limit", 10)
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            return False
        
        return True
    
    async def _web_search(self, query: str, limit: int, provider: str) -> List[Dict[str, Any]]:
        """Perform web search."""
        if provider == "google":
            return await self._google_search(query, limit)
        elif provider == "bing":
            return await self._bing_search(query, limit)
        elif provider == "duckduckgo":
            return await self._duckduckgo_search(query, limit)
        else:
            # Default to mock search
            return await self._mock_search(query, limit)
    
    async def _google_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform Google search."""
        if not self.search_providers["google"]["api_key"]:
            return await self._mock_search(query, limit)
        
        try:
            params = {
                "key": self.search_providers["google"]["api_key"],
                "cx": self.search_providers["google"]["search_engine_id"],
                "q": query,
                "num": min(limit, 10)
            }
            
            response = await self.http_client.get(
                self.search_providers["google"]["base_url"],
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "provider": "google"
                })
            
            return results
            
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return await self._mock_search(query, limit)
    
    async def _bing_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform Bing search."""
        if not self.search_providers["bing"]["api_key"]:
            return await self._mock_search(query, limit)
        
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.search_providers["bing"]["api_key"]
            }
            
            params = {
                "q": query,
                "count": min(limit, 50)
            }
            
            response = await self.http_client.get(
                self.search_providers["bing"]["base_url"],
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "provider": "bing"
                })
            
            return results
            
        except Exception as e:
            print(f"Bing search error: {str(e)}")
            return await self._mock_search(query, limit)
    
    async def _duckduckgo_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform DuckDuckGo search."""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = await self.http_client.get(
                self.search_providers["duckduckgo"]["base_url"],
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("results", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("abstract", ""),
                    "provider": "duckduckgo"
                })
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {str(e)}")
            return await self._mock_search(query, limit)
    
    async def _image_search(self, query: str, limit: int, provider: str) -> List[Dict[str, Any]]:
        """Perform image search."""
        # Mock image search - in reality would use image search APIs
        await asyncio.sleep(0.5)
        
        results = []
        for i in range(min(limit, 5)):
            results.append({
                "title": f"Image result {i+1} for '{query}'",
                "url": f"https://example.com/image{i+1}.jpg",
                "thumbnail": f"https://example.com/thumb{i+1}.jpg",
                "provider": provider,
                "type": "image"
            })
        
        return results
    
    async def _news_search(self, query: str, limit: int, provider: str) -> List[Dict[str, Any]]:
        """Perform news search."""
        # Mock news search - in reality would use news APIs
        await asyncio.sleep(0.3)
        
        results = []
        for i in range(min(limit, 5)):
            results.append({
                "title": f"News article {i+1} about '{query}'",
                "url": f"https://news.example.com/article{i+1}",
                "snippet": f"Latest news about {query}...",
                "published_date": datetime.now().isoformat(),
                "provider": provider,
                "type": "news"
            })
        
        return results
    
    async def _local_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform local database search."""
        # Mock local search - in reality would query local database
        await asyncio.sleep(0.2)
        
        results = []
        for i in range(min(limit, 3)):
            results.append({
                "title": f"Local result {i+1} for '{query}'",
                "url": f"local://document{i+1}",
                "snippet": f"Local content about {query}...",
                "provider": "local",
                "type": "local"
            })
        
        return results
    
    async def _semantic_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings."""
        # Mock semantic search - in reality would use vector database
        await asyncio.sleep(0.4)
        
        results = []
        for i in range(min(limit, 4)):
            results.append({
                "title": f"Semantic result {i+1} for '{query}'",
                "url": f"semantic://result{i+1}",
                "snippet": f"Semantically related content about {query}...",
                "similarity_score": 0.9 - (i * 0.1),
                "provider": "semantic",
                "type": "semantic"
            })
        
        return results
    
    async def _mock_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mock search results for testing."""
        await asyncio.sleep(0.1)
        
        results = []
        for i in range(min(limit, 5)):
            results.append({
                "title": f"Mock result {i+1} for '{query}'",
                "url": f"https://mock.example.com/result{i+1}",
                "snippet": f"This is a mock search result for '{query}'...",
                "provider": "mock",
                "type": "web"
            })
        
        return results
    
    def configure_provider(self, provider: str, api_key: str, **kwargs) -> None:
        """Configure a search provider."""
        if provider in self.search_providers:
            self.search_providers[provider]["api_key"] = api_key
            self.search_providers[provider].update(kwargs)
    
    def enable_provider(self, provider: str) -> None:
        """Enable a search provider."""
        if provider in self.search_providers:
            self.search_providers[provider]["enabled"] = True
    
    def disable_provider(self, provider: str) -> None:
        """Disable a search provider."""
        if provider in self.search_providers:
            self.search_providers[provider]["enabled"] = False
    
    def get_providers_status(self) -> Dict[str, bool]:
        """Get status of all search providers."""
        return {
            provider: config["enabled"] 
            for provider, config in self.search_providers.items()
        }
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
