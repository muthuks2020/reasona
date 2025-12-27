"""
Conductor - The primary interface for creating and managing AI agents.

The Conductor pattern provides a fluent, intuitive API for building
intelligent agents that can reason, use tools, and communicate with
other agents.
"""

from __future__ import annotations

import json
import asyncio
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterator, Optional, Union
from dataclasses import dataclass, field

import yaml
from pydantic import BaseModel, Field

from reasona.core.message import Message, Role
from reasona.core.context import Context
from reasona.core.config import ReasonaConfig
from reasona.tools.base import NeuralTool
from reasona.integrations.providers import get_provider, LLMProvider


class AgentCard(BaseModel):
    """Agent discovery card for Synaptic protocol."""
    
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    capabilities: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    endpoint: Optional[str] = None
    protocols: list[str] = Field(default_factory=lambda: ["synaptic/1.0", "jsonrpc/2.0"])


@dataclass
class ConductorState:
    """Internal state management for Conductor."""
    
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Conductor:
    """
    The Conductor class orchestrates AI agent behavior.
    
    A Conductor represents an intelligent agent capable of reasoning,
    using tools, and communicating with other agents via the Synaptic
    protocol.
    
    Example:
        >>> from reasona import Conductor
        >>> from reasona.tools import WebSearch
        >>> 
        >>> agent = Conductor(
        ...     name="researcher",
        ...     model="openai/gpt-4o",
        ...     tools=[WebSearch()],
        ...     instructions="You are a research assistant."
        ... )
        >>> response = agent.think("What are the latest AI trends?")
    """
    
    def __init__(
        self,
        name: str,
        model: str = "openai/gpt-4o-mini",
        instructions: Optional[str] = None,
        tools: Optional[list[NeuralTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        config: Optional[ReasonaConfig] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a new Conductor (AI agent).
        
        Args:
            name: Unique identifier for this agent.
            model: LLM model in format "provider/model-name".
            instructions: System prompt defining agent behavior.
            tools: List of NeuralTool instances the agent can use.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in response.
            config: Optional ReasonaConfig for advanced settings.
            metadata: Optional metadata dictionary.
        """
        self.name = name
        self.model = model
        self.instructions = instructions or self._default_instructions()
        self.tools = tools or []
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.config = config or ReasonaConfig()
        self.metadata = metadata or {}
        
        # Internal state
        self._state = ConductorState()
        self._provider: Optional[LLMProvider] = None
        self._server = None
        
        # Generate agent card for discovery
        self._card = self._generate_card()
    
    def _default_instructions(self) -> str:
        """Generate default system instructions."""
        return f"""You are {self.name}, an intelligent AI assistant powered by Reasona.
You are helpful, harmless, and honest. You think step-by-step when solving problems.
If you're unsure about something, say so rather than making things up."""
    
    def _generate_card(self) -> AgentCard:
        """Generate agent discovery card."""
        return AgentCard(
            name=self.name,
            description=self.instructions[:200] if self.instructions else None,
            capabilities=[
                "reasoning",
                "tool_use" if self.tools else None,
                "streaming",
            ],
            skills=[tool.name for tool in self.tools] if self.tools else [],
        )
    
    @property
    def provider(self) -> LLMProvider:
        """Lazy-load the LLM provider."""
        if self._provider is None:
            self._provider = get_provider(self.model, self.config)
        return self._provider
    
    def _build_messages(self, user_input: str) -> list[dict[str, Any]]:
        """Build message list for LLM API call."""
        messages = [{"role": "system", "content": self.instructions}]
        
        # Add conversation history
        for msg in self._state.messages:
            messages.append(msg.to_dict())
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _build_tools_schema(self) -> Optional[list[dict[str, Any]]]:
        """Build tool schemas for LLM API call."""
        if not self.tools:
            return None
        
        return [tool.to_schema() for tool in self.tools]
    
    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        for tool in self.tools:
            if tool.name == tool_name:
                if asyncio.iscoroutinefunction(tool.execute):
                    return await tool.execute(**arguments)
                return tool.execute(**arguments)
        
        raise ValueError(f"Tool '{tool_name}' not found")
    
    def think(self, input: str, context: Optional[Context] = None) -> str:
        """
        Process input and generate a response (synchronous).
        
        Args:
            input: User input or query.
            context: Optional context with additional information.
            
        Returns:
            The agent's response as a string.
        """
        return asyncio.get_event_loop().run_until_complete(
            self.athink(input, context)
        )
    
    async def athink(self, input: str, context: Optional[Context] = None) -> str:
        """
        Process input and generate a response (asynchronous).
        
        Args:
            input: User input or query.
            context: Optional context with additional information.
            
        Returns:
            The agent's response as a string.
        """
        messages = self._build_messages(input)
        tools_schema = self._build_tools_schema()
        
        # Make initial LLM call
        response = await self.provider.complete(
            messages=messages,
            tools=tools_schema,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        # Handle tool calls if present
        while response.tool_calls:
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_result = await self._execute_tool(
                    tool_call["name"],
                    tool_call["arguments"]
                )
                
                # Add tool result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result
                })
            
            # Get next response
            response = await self.provider.complete(
                messages=messages,
                tools=tools_schema,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        
        # Store in conversation history
        self._state.messages.append(Message(role=Role.USER, content=input))
        self._state.messages.append(Message(role=Role.ASSISTANT, content=response.content))
        
        return response.content
    
    async def stream(self, input: str, context: Optional[Context] = None) -> AsyncIterator[str]:
        """
        Stream a response token by token.
        
        Args:
            input: User input or query.
            context: Optional context with additional information.
            
        Yields:
            Response tokens as they are generated.
        """
        messages = self._build_messages(input)
        tools_schema = self._build_tools_schema()
        
        full_response = []
        
        async for chunk in self.provider.stream(
            messages=messages,
            tools=tools_schema,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ):
            full_response.append(chunk)
            yield chunk
        
        # Store completed response
        self._state.messages.append(Message(role=Role.USER, content=input))
        self._state.messages.append(Message(role=Role.ASSISTANT, content="".join(full_response)))
    
    def reset(self) -> None:
        """Clear conversation history and reset state."""
        self._state = ConductorState()
    
    def add_tool(self, tool: NeuralTool) -> "Conductor":
        """
        Add a tool to this agent (fluent API).
        
        Args:
            tool: The NeuralTool instance to add.
            
        Returns:
            Self for method chaining.
        """
        self.tools.append(tool)
        self._card.skills.append(tool.name)
        return self
    
    def with_instructions(self, instructions: str) -> "Conductor":
        """
        Update instructions (fluent API).
        
        Args:
            instructions: New system instructions.
            
        Returns:
            Self for method chaining.
        """
        self.instructions = instructions
        return self
    
    def with_temperature(self, temperature: float) -> "Conductor":
        """
        Update temperature (fluent API).
        
        Args:
            temperature: New sampling temperature.
            
        Returns:
            Self for method chaining.
        """
        self.temperature = temperature
        return self
    
    @classmethod
    def from_markdown(cls, path: Union[str, Path]) -> "Conductor":
        """
        Create a Conductor from a markdown file with YAML frontmatter.
        
        Args:
            path: Path to the markdown file.
            
        Returns:
            A new Conductor instance.
            
        Example:
            ```markdown
            ---
            name: assistant
            model: openai/gpt-4o
            temperature: 0.7
            ---
            
            You are a helpful assistant.
            ```
        """
        path = Path(path)
        content = path.read_text()
        
        # Parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                instructions = parts[2].strip()
            else:
                frontmatter = {}
                instructions = content
        else:
            frontmatter = {}
            instructions = content
        
        return cls(
            name=frontmatter.get("name", path.stem),
            model=frontmatter.get("model", "openai/gpt-4o-mini"),
            instructions=instructions,
            temperature=frontmatter.get("temperature", 0.7),
            max_tokens=frontmatter.get("max_tokens", 4096),
        )
    
    def to_card(self) -> dict[str, Any]:
        """Export agent card for discovery."""
        return self._card.model_dump()
    
    def serve(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False,
    ) -> None:
        """
        Serve this agent as a REST API.
        
        Args:
            host: Host to bind to.
            port: Port to listen on.
            reload: Enable auto-reload for development.
        """
        from reasona.server.api import create_app
        import uvicorn
        
        app = create_app(self)
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
        )
    
    def __repr__(self) -> str:
        return f"Conductor(name='{self.name}', model='{self.model}', tools={len(self.tools)})"
