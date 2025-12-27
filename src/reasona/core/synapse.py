"""
Synapse - The Synaptic Protocol for Agent-to-Agent Communication.

Synapse enables secure, standardized communication between Reasona agents,
allowing them to collaborate on complex tasks through message passing
and shared context.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Callable, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of messages in the Synaptic protocol."""
    
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    HANDSHAKE = "handshake"
    HEARTBEAT = "heartbeat"


class TaskStatus(str, Enum):
    """Status of a task in the Synaptic protocol."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SynapticMessage(BaseModel):
    """A message in the Synaptic protocol."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    source: str
    target: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """Represents a task being processed by agents."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class AgentConnection:
    """Represents a connection to an agent in the Synapse network."""
    
    agent_name: str
    agent: Any  # Conductor instance
    capabilities: list[str] = field(default_factory=list)
    is_active: bool = True
    connected_at: datetime = field(default_factory=datetime.utcnow)


class Synapse:
    """
    The Synapse class manages agent-to-agent communication.
    
    Synapse implements the Synaptic Protocol, enabling secure and
    standardized communication between Reasona agents for collaborative
    task execution.
    
    Example:
        >>> from reasona import Conductor, Synapse
        >>> 
        >>> researcher = Conductor(name="researcher", model="openai/gpt-4o")
        >>> writer = Conductor(name="writer", model="anthropic/claude-3-5-sonnet")
        >>> 
        >>> synapse = Synapse()
        >>> synapse.connect(researcher)
        >>> synapse.connect(writer)
        >>> 
        >>> result = await synapse.orchestrate(
        ...     task="Research AI trends and write a blog post",
        ...     lead=researcher
        ... )
    """
    
    def __init__(
        self,
        name: str = "synapse-network",
        enable_logging: bool = True,
    ) -> None:
        """
        Initialize a new Synapse network.
        
        Args:
            name: Name for this Synapse network.
            enable_logging: Whether to log messages.
        """
        self.name = name
        self.enable_logging = enable_logging
        
        # Connected agents
        self._connections: dict[str, AgentConnection] = {}
        
        # Message handlers
        self._handlers: dict[str, list[Callable]] = {}
        
        # Task registry
        self._tasks: dict[str, Task] = {}
        
        # Message queue
        self._queue: asyncio.Queue[SynapticMessage] = asyncio.Queue()
    
    def connect(self, agent: Any, capabilities: Optional[list[str]] = None) -> "Synapse":
        """
        Connect an agent to this Synapse network.
        
        Args:
            agent: A Conductor instance to connect.
            capabilities: Optional list of agent capabilities.
            
        Returns:
            Self for method chaining.
        """
        connection = AgentConnection(
            agent_name=agent.name,
            agent=agent,
            capabilities=capabilities or [],
        )
        self._connections[agent.name] = connection
        
        if self.enable_logging:
            print(f"[Synapse] Connected agent: {agent.name}")
        
        return self
    
    def disconnect(self, agent_name: str) -> "Synapse":
        """
        Disconnect an agent from this Synapse network.
        
        Args:
            agent_name: Name of the agent to disconnect.
            
        Returns:
            Self for method chaining.
        """
        if agent_name in self._connections:
            self._connections[agent_name].is_active = False
            del self._connections[agent_name]
            
            if self.enable_logging:
                print(f"[Synapse] Disconnected agent: {agent_name}")
        
        return self
    
    def get_agent(self, name: str) -> Optional[Any]:
        """Get a connected agent by name."""
        conn = self._connections.get(name)
        return conn.agent if conn else None
    
    @property
    def agents(self) -> list[str]:
        """Get list of connected agent names."""
        return list(self._connections.keys())
    
    async def send(
        self,
        target: str,
        payload: dict[str, Any],
        source: str = "synapse",
        message_type: MessageType = MessageType.REQUEST,
    ) -> SynapticMessage:
        """
        Send a message to a connected agent.
        
        Args:
            target: Name of the target agent.
            payload: Message payload.
            source: Name of the source agent.
            message_type: Type of message.
            
        Returns:
            The sent message.
        """
        message = SynapticMessage(
            type=message_type,
            source=source,
            target=target,
            payload=payload,
        )
        
        await self._queue.put(message)
        
        if self.enable_logging:
            print(f"[Synapse] {source} -> {target}: {message_type.value}")
        
        return message
    
    async def broadcast(
        self,
        payload: dict[str, Any],
        source: str = "synapse",
        exclude: Optional[list[str]] = None,
    ) -> list[SynapticMessage]:
        """
        Broadcast a message to all connected agents.
        
        Args:
            payload: Message payload.
            source: Name of the source agent.
            exclude: Optional list of agent names to exclude.
            
        Returns:
            List of sent messages.
        """
        exclude = exclude or []
        messages = []
        
        for agent_name in self._connections:
            if agent_name not in exclude:
                msg = await self.send(
                    target=agent_name,
                    payload=payload,
                    source=source,
                    message_type=MessageType.NOTIFICATION,
                )
                messages.append(msg)
        
        return messages
    
    async def delegate(
        self,
        agent_name: str,
        task: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Delegate a task to a specific agent.
        
        Args:
            agent_name: Name of the agent to delegate to.
            task: Task description.
            context: Optional additional context.
            
        Returns:
            The agent's response.
        """
        connection = self._connections.get(agent_name)
        if not connection:
            raise ValueError(f"Agent '{agent_name}' not connected")
        
        # Build prompt with context
        prompt = task
        if context:
            prompt = f"Context: {json.dumps(context)}\n\nTask: {task}"
        
        # Execute task
        response = await connection.agent.athink(prompt)
        
        if self.enable_logging:
            print(f"[Synapse] Delegated to {agent_name}: {task[:50]}...")
        
        return response
    
    async def orchestrate(
        self,
        task: str,
        lead: Optional[Any] = None,
        participants: Optional[list[str]] = None,
        max_rounds: int = 5,
    ) -> dict[str, Any]:
        """
        Orchestrate a collaborative task among connected agents.
        
        Args:
            task: The task description.
            lead: The lead agent (Conductor) to coordinate.
            participants: Optional list of participant agent names.
            max_rounds: Maximum rounds of collaboration.
            
        Returns:
            Dictionary with task results and artifacts.
        """
        # Create task record
        task_obj = Task(description=task)
        self._tasks[task_obj.id] = task_obj
        task_obj.status = TaskStatus.RUNNING
        
        # Determine participants
        if participants:
            active_agents = [
                self._connections[name]
                for name in participants
                if name in self._connections
            ]
        else:
            active_agents = list(self._connections.values())
        
        # Use lead agent or first available
        if lead:
            lead_agent = lead
        elif active_agents:
            lead_agent = active_agents[0].agent
        else:
            raise ValueError("No agents available for orchestration")
        
        # Build collaboration context
        agent_list = ", ".join([a.agent_name for a in active_agents])
        
        orchestration_prompt = f"""You are coordinating a collaborative task among multiple AI agents.

Available agents: {agent_list}

Task: {task}

Please analyze the task and provide:
1. A step-by-step plan for completing the task
2. Which agent should handle each step
3. Your initial contribution to the task

Format your response clearly with sections for Plan, Agent Assignments, and Your Contribution."""

        try:
            # Get initial plan from lead
            plan_response = await lead_agent.athink(orchestration_prompt)
            task_obj.artifacts.append({
                "type": "plan",
                "agent": lead_agent.name,
                "content": plan_response,
            })
            
            # Execute collaboration rounds
            current_context = plan_response
            
            for round_num in range(max_rounds):
                # Delegate to other agents
                for conn in active_agents:
                    if conn.agent.name != lead_agent.name:
                        continuation_prompt = f"""Previous context:
{current_context}

Based on the above, please provide your contribution to the task: {task}

Focus on your unique perspective and capabilities."""
                        
                        contribution = await conn.agent.athink(continuation_prompt)
                        task_obj.artifacts.append({
                            "type": "contribution",
                            "agent": conn.agent_name,
                            "round": round_num,
                            "content": contribution,
                        })
                        current_context += f"\n\n[{conn.agent_name}]: {contribution}"
            
            # Final synthesis by lead
            synthesis_prompt = f"""Based on all contributions:

{current_context}

Please provide a final synthesis and conclusion for the task: {task}"""
            
            final_response = await lead_agent.athink(synthesis_prompt)
            task_obj.artifacts.append({
                "type": "synthesis",
                "agent": lead_agent.name,
                "content": final_response,
            })
            
            # Complete task
            task_obj.status = TaskStatus.COMPLETED
            task_obj.result = final_response
            task_obj.completed_at = datetime.utcnow()
            
            return {
                "task_id": task_obj.id,
                "status": task_obj.status.value,
                "result": task_obj.result,
                "artifacts": task_obj.artifacts,
            }
            
        except Exception as e:
            task_obj.status = TaskStatus.FAILED
            task_obj.error = str(e)
            raise
    
    def on(self, event: str, handler: Callable) -> "Synapse":
        """
        Register an event handler.
        
        Args:
            event: Event name to listen for.
            handler: Handler function.
            
        Returns:
            Self for method chaining.
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
        return self
    
    def __repr__(self) -> str:
        return f"Synapse(name='{self.name}', agents={len(self._connections)})"
