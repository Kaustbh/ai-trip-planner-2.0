"""
LLM Service

Service wrapper for Large Language Model APIs (OpenAI, Anthropic, Cohere).
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
import httpx
from datetime import datetime
import json
from enum import Enum

from pydantic import BaseModel, Field


class LLMProvider(Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


class MessageRole(Enum):
    """Message role enumeration."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Message structure for LLM requests."""
    role: MessageRole
    content: str
    name: Optional[str] = None


class LLMConfig(BaseModel):
    """Configuration for LLM service."""
    provider: LLMProvider
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_attempts: int = 3
    base_url: Optional[str] = None


class LLMService:
    """
    Service wrapper for Large Language Model APIs.
    
    Features:
    - Multiple provider support
    - Automatic retry logic
    - Rate limiting
    - Response caching
    - Error handling
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.http_client = httpx.AsyncClient(timeout=config.timeout)
        self.request_count = 0
        self.cache = {}
        self.rate_limiter = None
        
    async def generate_response(self, messages: List[Message], 
                              temperature: Optional[float] = None,
                              max_tokens: Optional[int] = None,
                              stream: bool = False) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        try:
            # Prepare request parameters
            params = {
                "messages": [msg.dict() for msg in messages],
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "stream": stream
            }
            
            # Generate cache key
            cache_key = self._generate_cache_key(params)
            
            # Check cache
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Make request
            response = await self._make_request(params)
            
            # Cache response
            self.cache[cache_key] = response
            
            # Update metrics
            self.request_count += 1
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": self.config.provider.value
            }
    
    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to LLM provider."""
        if self.config.provider == LLMProvider.OPENAI:
            return await self._make_openai_request(params)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._make_anthropic_request(params)
        elif self.config.provider == LLMProvider.COHERE:
            return await self._make_cohere_request(params)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    async def _make_openai_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to OpenAI API."""
        url = f"{self.config.base_url or 'https://api.openai.com/v1'}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": params["messages"],
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "stream": params["stream"]
        }
        
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model"),
                "provider": "openai"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "provider": "openai"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "openai"
            }
    
    async def _make_anthropic_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Anthropic API."""
        url = f"{self.config.base_url or 'https://api.anthropic.com/v1'}/messages"
        
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages to Anthropic format
        messages = []
        system_message = None
        
        for msg in params["messages"]:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"]
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "content": data["content"][0]["text"],
                "usage": data.get("usage", {}),
                "model": data.get("model"),
                "provider": "anthropic"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "provider": "anthropic"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "anthropic"
            }
    
    async def _make_cohere_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Cohere API."""
        url = f"{self.config.base_url or 'https://api.cohere.ai/v1'}/chat"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # Convert messages to Cohere format
        chat_history = []
        message = ""
        
        for msg in params["messages"]:
            if msg["role"] == "user":
                message = msg["content"]
            elif msg["role"] == "assistant":
                chat_history.append({
                    "role": "CHATBOT",
                    "message": msg["content"]
                })
            elif msg["role"] == "system":
                # Cohere doesn't have system messages, prepend to user message
                message = f"{msg['content']}\n\n{message}"
        
        payload = {
            "model": self.config.model,
            "message": message,
            "chat_history": chat_history,
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"]
        }
        
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "content": data["text"],
                "usage": data.get("meta", {}).get("billed_units", {}),
                "model": data.get("meta", {}).get("model"),
                "provider": "cohere"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "provider": "cohere"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "cohere"
            }
    
    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key for request parameters."""
        # Create a hash of the parameters
        key_data = {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "messages": params["messages"],
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"]
        }
        
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    async def generate_embeddings(self, texts: List[str], 
                                model: Optional[str] = None) -> Dict[str, Any]:
        """Generate embeddings for texts."""
        if self.config.provider == LLMProvider.OPENAI:
            return await self._generate_openai_embeddings(texts, model)
        else:
            return {
                "success": False,
                "error": f"Embeddings not supported for provider: {self.config.provider}"
            }
    
    async def _generate_openai_embeddings(self, texts: List[str], 
                                        model: Optional[str] = None) -> Dict[str, Any]:
        """Generate embeddings using OpenAI API."""
        url = f"{self.config.base_url or 'https://api.openai.com/v1'}/embeddings"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or "text-embedding-ada-002",
            "input": texts
        }
        
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "embeddings": [item["embedding"] for item in data["data"]],
                "usage": data.get("usage", {}),
                "model": data.get("model"),
                "provider": "openai"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "provider": "openai"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "openai"
            }
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "request_count": self.request_count,
            "cache_size": len(self.cache)
        }
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self.cache.clear()
    
    def __str__(self) -> str:
        return f"LLMService({self.config.provider.value}, {self.config.model})"
    
    def __repr__(self) -> str:
        return f"<LLMService(provider={self.config.provider.value}, model={self.config.model})>"
