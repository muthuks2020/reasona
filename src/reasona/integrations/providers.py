"""
LLM Provider abstractions for Reasona.

This module provides a unified interface for interacting with
different LLM providers (OpenAI, Anthropic, Google, etc.).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    
    content: str
    model: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw: Optional[Any] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion token by token."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> None:
        self.model = model
        
        from openai import AsyncOpenAI
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        )
    
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using OpenAI API."""
        
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            request_kwargs["tools"] = tools
        
        request_kwargs.update(kwargs)
        
        response = await self.client.chat.completions.create(**request_kwargs)
        
        # Extract tool calls
        tool_calls = []
        if response.choices[0].message.tool_calls:
            for tc in response.choices[0].message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })
        
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason,
            raw=response,
        )
    
    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using OpenAI API."""
        
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        if tools:
            request_kwargs["tools"] = tools
        
        request_kwargs.update(kwargs)
        
        stream = await self.client.chat.completions.create(**request_kwargs)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> None:
        self.model = model
        
        from anthropic import AsyncAnthropic
        
        self.client = AsyncAnthropic(api_key=api_key)
    
    def _convert_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> tuple[Optional[str], list[dict[str, Any]]]:
        """Convert OpenAI-style messages to Anthropic format."""
        system_prompt = None
        converted = []
        
        for msg in messages:
            role = msg["role"]
            content = msg.get("content")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                converted.append({"role": "user", "content": content})
            elif role == "assistant":
                converted.append({"role": "assistant", "content": content or ""})
            elif role == "tool":
                converted.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id"),
                            "content": content,
                        }
                    ]
                })
        
        return system_prompt, converted
    
    def _convert_tools(
        self,
        tools: Optional[list[dict[str, Any]]]
    ) -> Optional[list[dict[str, Any]]]:
        """Convert OpenAI-style tools to Anthropic format."""
        if not tools:
            return None
        
        converted = []
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                converted.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })
        
        return converted
    
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Anthropic API."""
        
        system_prompt, converted_messages = self._convert_messages(messages)
        converted_tools = self._convert_tools(tools)
        
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
        }
        
        if system_prompt:
            request_kwargs["system"] = system_prompt
        
        if converted_tools:
            request_kwargs["tools"] = converted_tools
        
        response = await self.client.messages.create(**request_kwargs)
        
        # Extract content and tool calls
        content_parts = []
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })
        
        return LLMResponse(
            content="".join(content_parts),
            model=response.model,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            raw=response,
        )
    
    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using Anthropic API."""
        
        system_prompt, converted_messages = self._convert_messages(messages)
        converted_tools = self._convert_tools(tools)
        
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
        }
        
        if system_prompt:
            request_kwargs["system"] = system_prompt
        
        if converted_tools:
            request_kwargs["tools"] = converted_tools
        
        async with self.client.messages.stream(**request_kwargs) as stream:
            async for text in stream.text_stream:
                yield text


class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
    ) -> None:
        self.model = model
        
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        self.genai = genai
        self.client = genai.GenerativeModel(model)
    
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Google Gemini API."""
        
        # Convert messages to Gemini format
        history = []
        current_content = None
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                history.append({"role": "user", "parts": [content]})
                current_content = content
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
        
        # Create chat session
        chat = self.client.start_chat(history=history[:-1] if history else [])
        
        # Generate response
        response = await chat.send_message_async(
            current_content or "",
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        
        return LLMResponse(
            content=response.text,
            model=self.model,
            tool_calls=[],
            usage={},
            finish_reason="stop",
            raw=response,
        )
    
    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using Google Gemini API."""
        
        # For simplicity, fall back to non-streaming
        response = await self.complete(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        # Simulate streaming by yielding chunks
        chunk_size = 20
        content = response.content
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.base_url = base_url
        
        import httpx
        self.client = httpx.AsyncClient(base_url=base_url, timeout=120.0)
    
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Ollama API."""
        
        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            },
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["message"]["content"],
            model=self.model,
            tool_calls=[],
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            finish_reason="stop",
            raw=data,
        )
    
    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using Ollama API."""
        
        async with self.client.stream(
            "POST",
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]


def get_provider(model: str, config: Any = None) -> LLMProvider:
    """
    Get the appropriate LLM provider for a model string.
    
    Model format: "provider/model-name"
    
    Examples:
        - "openai/gpt-4o"
        - "anthropic/claude-3-5-sonnet"
        - "google/gemini-2.0-flash"
        - "ollama/llama3.2"
    """
    from reasona.core.config import ReasonaConfig
    
    config = config or ReasonaConfig()
    
    # Parse model string
    if "/" in model:
        provider_name, model_name = model.split("/", 1)
    else:
        # Default to OpenAI
        provider_name = "openai"
        model_name = model
    
    provider_name = provider_name.lower()
    
    # Get provider config
    provider_config = config.get_provider_config(provider_name)
    
    # Create provider instance
    if provider_name == "openai":
        if not provider_config.api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAIProvider(
            api_key=provider_config.api_key,
            model=model_name,
            base_url=provider_config.base_url,
            organization=provider_config.organization,
        )
    
    elif provider_name == "anthropic":
        if not provider_config.api_key:
            raise ValueError("Anthropic API key not configured")
        return AnthropicProvider(
            api_key=provider_config.api_key,
            model=model_name,
        )
    
    elif provider_name in ["google", "gemini"]:
        if not provider_config.api_key:
            raise ValueError("Google API key not configured")
        return GoogleProvider(
            api_key=provider_config.api_key,
            model=model_name,
        )
    
    elif provider_name == "ollama":
        return OllamaProvider(
            model=model_name,
            base_url=provider_config.base_url or "http://localhost:11434",
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
