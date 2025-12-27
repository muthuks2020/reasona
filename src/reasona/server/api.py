"""
REST API server for Reasona agents.

This module provides a FastAPI-based server for exposing
Conductor agents as REST APIs with streaming support.
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse


class ThinkRequest(BaseModel):
    """Request model for /v1/think endpoint."""
    
    input: str = Field(..., description="The input prompt for the agent")
    stream: bool = Field(default=False, description="Whether to stream the response")
    context: Optional[dict[str, Any]] = Field(default=None, description="Optional context")


class ThinkResponse(BaseModel):
    """Response model for /v1/think endpoint."""
    
    output: str = Field(..., description="The agent's response")
    conversation_id: Optional[str] = Field(default=None)
    model: str
    usage: Optional[dict[str, int]] = None


class AgentInfoResponse(BaseModel):
    """Response model for agent information."""
    
    name: str
    model: str
    description: Optional[str] = None
    tools: list[str] = Field(default_factory=list)
    version: str = "1.0.0"
    status: str = "active"


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = "healthy"
    timestamp: str
    version: str


def create_app(conductor: Any) -> FastAPI:
    """
    Create a FastAPI application for a Conductor agent.
    
    Args:
        conductor: The Conductor instance to serve.
        
    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title=f"Reasona Agent: {conductor.name}",
        description=f"REST API for {conductor.name} agent",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
        )
    
    @app.get("/v1/agent", response_model=AgentInfoResponse, tags=["Agent"])
    async def get_agent_info():
        """Get agent information."""
        return AgentInfoResponse(
            name=conductor.name,
            model=conductor.model,
            description=conductor.instructions[:200] if conductor.instructions else None,
            tools=[tool.name for tool in conductor.tools],
        )
    
    @app.get("/.well-known/agent-card.json", tags=["Discovery"])
    async def get_agent_card():
        """Get agent discovery card (Synaptic Protocol)."""
        return conductor.to_card()
    
    @app.post("/v1/think", response_model=ThinkResponse, tags=["Agent"])
    async def think(request: ThinkRequest):
        """
        Process input and generate a response.
        
        If stream=True, returns a Server-Sent Events stream.
        """
        if request.stream:
            async def event_generator():
                async for chunk in conductor.stream(request.input):
                    yield {"data": chunk}
            
            return EventSourceResponse(event_generator())
        
        try:
            response = await conductor.athink(request.input)
            
            return ThinkResponse(
                output=response,
                conversation_id=conductor._state.conversation_id,
                model=conductor.model,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/v1/chat", tags=["Agent"])
    async def chat(request: ThinkRequest):
        """Alias for /v1/think (compatibility)."""
        return await think(request)
    
    @app.post("/v1/reset", tags=["Agent"])
    async def reset_conversation():
        """Reset the conversation history."""
        conductor.reset()
        return {"status": "ok", "message": "Conversation reset"}
    
    @app.get("/v1/tools", tags=["Tools"])
    async def list_tools():
        """List available tools."""
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.to_schema(),
                }
                for tool in conductor.tools
            ]
        }
    
    return app


class ConductorRouter:
    """
    FastAPI router for mounting multiple Conductor agents.
    
    Example:
        >>> from fastapi import FastAPI
        >>> from reasona import Conductor
        >>> from reasona.server import ConductorRouter
        >>> 
        >>> app = FastAPI()
        >>> router = ConductorRouter()
        >>> router.add_agent(Conductor(name="agent1", model="openai/gpt-4o"))
        >>> router.add_agent(Conductor(name="agent2", model="anthropic/claude-3-5-sonnet"))
        >>> app.include_router(router.build(), prefix="/agents")
    """
    
    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}
    
    def add_agent(self, conductor: Any) -> "ConductorRouter":
        """Add an agent to the router."""
        self._agents[conductor.name] = conductor
        return self
    
    def remove_agent(self, name: str) -> "ConductorRouter":
        """Remove an agent from the router."""
        if name in self._agents:
            del self._agents[name]
        return self
    
    def build(self):
        """Build the FastAPI router."""
        from fastapi import APIRouter
        
        router = APIRouter()
        
        @router.get("/", tags=["Agents"])
        async def list_agents():
            """List all available agents."""
            return {
                "agents": [
                    {
                        "name": name,
                        "model": agent.model,
                        "tools": len(agent.tools),
                    }
                    for name, agent in self._agents.items()
                ]
            }
        
        @router.post("/{agent_name}/think", tags=["Agents"])
        async def agent_think(agent_name: str, request: ThinkRequest):
            """Send a message to a specific agent."""
            if agent_name not in self._agents:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
            agent = self._agents[agent_name]
            
            if request.stream:
                async def event_generator():
                    async for chunk in agent.stream(request.input):
                        yield {"data": chunk}
                
                return EventSourceResponse(event_generator())
            
            try:
                response = await agent.athink(request.input)
                return ThinkResponse(
                    output=response,
                    conversation_id=agent._state.conversation_id,
                    model=agent.model,
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/{agent_name}/card", tags=["Agents"])
        async def get_agent_card(agent_name: str):
            """Get agent card for a specific agent."""
            if agent_name not in self._agents:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
            return self._agents[agent_name].to_card()
        
        return router
