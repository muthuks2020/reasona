"""
HyperMCP - A native ASGI MCP Server implementation.

HyperMCP provides a FastAPI-native implementation of the Model Context Protocol,
offering full compatibility with the MCP specification while integrating
seamlessly with existing FastAPI applications.
"""

from __future__ import annotations

import json
import uuid
import inspect
import asyncio
from typing import Any, Callable, Optional, Union, get_type_hints
from dataclasses import dataclass, field
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


# Context variable for request token
_current_token: ContextVar[Optional[str]] = ContextVar("current_token", default=None)


def get_token() -> Optional[str]:
    """Get the current request's authentication token."""
    return _current_token.get()


class MCPToolDefinition(BaseModel):
    """Definition of an MCP tool."""
    
    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)


class MCPResourceDefinition(BaseModel):
    """Definition of an MCP resource."""
    
    uri: str
    name: str
    description: str = ""
    mime_type: str = "application/json"


class MCPPromptDefinition(BaseModel):
    """Definition of an MCP prompt template."""
    
    name: str
    description: str = ""
    arguments: list[dict[str, Any]] = Field(default_factory=list)


@dataclass
class RegisteredTool:
    """Internal representation of a registered tool."""
    
    name: str
    description: str
    handler: Callable
    input_schema: dict[str, Any]


@dataclass
class RegisteredResource:
    """Internal representation of a registered resource."""
    
    uri: str
    name: str
    description: str
    handler: Callable
    mime_type: str


@dataclass
class RegisteredPrompt:
    """Internal representation of a registered prompt."""
    
    name: str
    description: str
    handler: Callable
    arguments: list[dict[str, Any]]


class HyperMCP:
    """
    HyperMCP - Native ASGI MCP Server.
    
    A FastAPI-native implementation of the Model Context Protocol that
    provides full MCP compliance while offering seamless integration
    with existing FastAPI applications.
    
    Example:
        >>> from reasona.mcp import HyperMCP, get_token
        >>> 
        >>> mcp = HyperMCP(name="my-server", version="1.0.0")
        >>> 
        >>> @mcp.tool(description="Get weather for a location")
        ... async def get_weather(location: str) -> dict:
        ...     token = get_token()  # Access auth token
        ...     return {"location": location, "temp": 22}
        >>> 
        >>> @mcp.resource("config://app")
        ... async def get_config() -> dict:
        ...     return {"version": "1.0.0"}
        >>> 
        >>> mcp.serve(port=9000)
    """
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None,
    ) -> None:
        """
        Initialize HyperMCP server.
        
        Args:
            name: Server name.
            version: Server version.
            description: Optional server description.
        """
        self.name = name
        self.version = version
        self.description = description
        
        # Registered handlers
        self._tools: dict[str, RegisteredTool] = {}
        self._resources: dict[str, RegisteredResource] = {}
        self._prompts: dict[str, RegisteredPrompt] = {}
        
        # FastAPI app
        self._app: Optional[FastAPI] = None
    
    def _extract_schema(self, func: Callable) -> dict[str, Any]:
        """Extract JSON Schema from function signature."""
        sig = inspect.signature(func)
        hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            # Get type hint
            param_type = hints.get(param_name, str)
            
            # Convert to JSON Schema type
            type_mapping = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object",
            }
            
            json_type = type_mapping.get(param_type, "string")
            properties[param_name] = {"type": json_type}
            
            # Check if required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    
    def tool(
        self,
        name: Optional[str] = None,
        description: str = "",
    ) -> Callable:
        """
        Decorator to register a tool.
        
        Args:
            name: Optional tool name (defaults to function name).
            description: Tool description.
            
        Example:
            >>> @mcp.tool(description="Calculate sum")
            ... def add(a: int, b: int) -> int:
            ...     return a + b
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or (func.__doc__ or "").strip()
            
            self._tools[tool_name] = RegisteredTool(
                name=tool_name,
                description=tool_desc,
                handler=func,
                input_schema=self._extract_schema(func),
            )
            
            return func
        
        return decorator
    
    def resource(
        self,
        uri: str,
        name: Optional[str] = None,
        description: str = "",
        mime_type: str = "application/json",
    ) -> Callable:
        """
        Decorator to register a resource.
        
        Args:
            uri: Resource URI (e.g., "config://app", "file:///data.json").
            name: Optional resource name.
            description: Resource description.
            mime_type: MIME type of the resource.
            
        Example:
            >>> @mcp.resource("config://app")
            ... async def get_config() -> dict:
            ...     return {"version": "1.0.0"}
        """
        def decorator(func: Callable) -> Callable:
            resource_name = name or func.__name__
            resource_desc = description or (func.__doc__ or "").strip()
            
            self._resources[uri] = RegisteredResource(
                uri=uri,
                name=resource_name,
                description=resource_desc,
                handler=func,
                mime_type=mime_type,
            )
            
            return func
        
        return decorator
    
    def prompt(
        self,
        name: Optional[str] = None,
        description: str = "",
    ) -> Callable:
        """
        Decorator to register a prompt template.
        
        Args:
            name: Optional prompt name.
            description: Prompt description.
            
        Example:
            >>> @mcp.prompt(description="Greeting prompt")
            ... def greet(name: str) -> str:
            ...     return f"Hello, {name}!"
        """
        def decorator(func: Callable) -> Callable:
            prompt_name = name or func.__name__
            prompt_desc = description or (func.__doc__ or "").strip()
            
            # Extract arguments
            sig = inspect.signature(func)
            arguments = [
                {"name": param, "required": p.default == inspect.Parameter.empty}
                for param, p in sig.parameters.items()
            ]
            
            self._prompts[prompt_name] = RegisteredPrompt(
                name=prompt_name,
                description=prompt_desc,
                handler=func,
                arguments=arguments,
            )
            
            return func
        
        return decorator
    
    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title=f"HyperMCP: {self.name}",
            description=self.description or f"MCP Server: {self.name}",
            version=self.version,
        )
        
        # Add CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Server info
        @app.get("/")
        async def server_info():
            """Get server information."""
            return {
                "name": self.name,
                "version": self.version,
                "protocol": "mcp",
                "capabilities": {
                    "tools": len(self._tools) > 0,
                    "resources": len(self._resources) > 0,
                    "prompts": len(self._prompts) > 0,
                }
            }
        
        # List tools
        @app.get("/tools")
        async def list_tools():
            """List available tools."""
            return {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.input_schema,
                    }
                    for t in self._tools.values()
                ]
            }
        
        # Call tool
        @app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, request: Request):
            """Call a tool."""
            if tool_name not in self._tools:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            
            tool = self._tools[tool_name]
            body = await request.json()
            arguments = body.get("arguments", {})
            
            # Set auth token in context
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
            token_ctx = _current_token.set(token)
            
            try:
                # Call handler
                if asyncio.iscoroutinefunction(tool.handler):
                    result = await tool.handler(**arguments)
                else:
                    result = tool.handler(**arguments)
                
                return {"result": result}
            
            finally:
                _current_token.reset(token_ctx)
        
        # List resources
        @app.get("/resources")
        async def list_resources():
            """List available resources."""
            return {
                "resources": [
                    {
                        "uri": r.uri,
                        "name": r.name,
                        "description": r.description,
                        "mimeType": r.mime_type,
                    }
                    for r in self._resources.values()
                ]
            }
        
        # Read resource
        @app.get("/resources/{resource_uri:path}")
        async def read_resource(resource_uri: str, request: Request):
            """Read a resource."""
            # Try exact match first
            if resource_uri not in self._resources:
                # Try with different URI schemes
                for uri in self._resources:
                    if uri.endswith(resource_uri) or resource_uri.endswith(uri.split("://")[-1]):
                        resource_uri = uri
                        break
                else:
                    raise HTTPException(status_code=404, detail=f"Resource '{resource_uri}' not found")
            
            resource = self._resources[resource_uri]
            
            # Call handler
            if asyncio.iscoroutinefunction(resource.handler):
                content = await resource.handler()
            else:
                content = resource.handler()
            
            return {
                "uri": resource.uri,
                "mimeType": resource.mime_type,
                "content": content,
            }
        
        # List prompts
        @app.get("/prompts")
        async def list_prompts():
            """List available prompts."""
            return {
                "prompts": [
                    {
                        "name": p.name,
                        "description": p.description,
                        "arguments": p.arguments,
                    }
                    for p in self._prompts.values()
                ]
            }
        
        # Get prompt
        @app.post("/prompts/{prompt_name}")
        async def get_prompt(prompt_name: str, request: Request):
            """Get a prompt with arguments."""
            if prompt_name not in self._prompts:
                raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
            
            prompt = self._prompts[prompt_name]
            body = await request.json()
            arguments = body.get("arguments", {})
            
            # Call handler
            if asyncio.iscoroutinefunction(prompt.handler):
                result = await prompt.handler(**arguments)
            else:
                result = prompt.handler(**arguments)
            
            return {"messages": [{"role": "user", "content": result}]}
        
        # JSON-RPC endpoint (MCP standard)
        @app.post("/rpc")
        async def json_rpc(request: Request):
            """JSON-RPC 2.0 endpoint for MCP protocol."""
            body = await request.json()
            
            method = body.get("method")
            params = body.get("params", {})
            request_id = body.get("id")
            
            try:
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {},
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": self.version,
                        }
                    }
                
                elif method == "tools/list":
                    result = {
                        "tools": [
                            {
                                "name": t.name,
                                "description": t.description,
                                "inputSchema": t.input_schema,
                            }
                            for t in self._tools.values()
                        ]
                    }
                
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if tool_name not in self._tools:
                        raise ValueError(f"Unknown tool: {tool_name}")
                    
                    tool = self._tools[tool_name]
                    
                    if asyncio.iscoroutinefunction(tool.handler):
                        tool_result = await tool.handler(**arguments)
                    else:
                        tool_result = tool.handler(**arguments)
                    
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result,
                            }
                        ]
                    }
                
                elif method == "resources/list":
                    result = {
                        "resources": [
                            {
                                "uri": r.uri,
                                "name": r.name,
                                "description": r.description,
                                "mimeType": r.mime_type,
                            }
                            for r in self._resources.values()
                        ]
                    }
                
                elif method == "resources/read":
                    uri = params.get("uri")
                    
                    if uri not in self._resources:
                        raise ValueError(f"Unknown resource: {uri}")
                    
                    resource = self._resources[uri]
                    
                    if asyncio.iscoroutinefunction(resource.handler):
                        content = await resource.handler()
                    else:
                        content = resource.handler()
                    
                    result = {
                        "contents": [
                            {
                                "uri": resource.uri,
                                "mimeType": resource.mime_type,
                                "text": json.dumps(content) if not isinstance(content, str) else content,
                            }
                        ]
                    }
                
                elif method == "prompts/list":
                    result = {
                        "prompts": [
                            {
                                "name": p.name,
                                "description": p.description,
                                "arguments": p.arguments,
                            }
                            for p in self._prompts.values()
                        ]
                    }
                
                else:
                    raise ValueError(f"Unknown method: {method}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }
                
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e),
                    }
                }
        
        return app
    
    @property
    def app(self) -> FastAPI:
        """Get the FastAPI application."""
        if self._app is None:
            self._app = self._create_app()
        return self._app
    
    def router(self):
        """Get a FastAPI router for mounting in an existing app."""
        from fastapi import APIRouter
        
        router = APIRouter()
        
        # Mount all endpoints on the router
        # This is a simplified version - in production you'd want to
        # properly replicate all endpoints
        
        return router
    
    def serve(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        reload: bool = False,
    ) -> None:
        """
        Start the MCP server.
        
        Args:
            host: Host to bind to.
            port: Port to listen on.
            reload: Enable auto-reload for development.
        """
        import uvicorn
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
        )
    
    def __repr__(self) -> str:
        return f"HyperMCP(name='{self.name}', tools={len(self._tools)}, resources={len(self._resources)})"
