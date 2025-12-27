"""
Base classes for Reasona Neural Tools.

Neural Tools provide a consistent interface for defining tools
that agents can use. They support automatic schema generation,
type validation, and both sync/async execution.
"""

from __future__ import annotations

import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, get_type_hints, Union
from dataclasses import dataclass, field
from functools import wraps


def _python_type_to_json_schema(python_type: Any) -> dict[str, Any]:
    """Convert Python type annotation to JSON Schema."""
    # Handle None/NoneType
    if python_type is None or python_type is type(None):
        return {"type": "null"}
    
    # Handle basic types
    type_mapping = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    
    if python_type in type_mapping:
        return type_mapping[python_type]
    
    # Handle Optional types (Union with None)
    origin = getattr(python_type, "__origin__", None)
    
    if origin is Union:
        args = python_type.__args__
        # Check if it's Optional (Union with None)
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return _python_type_to_json_schema(non_none_args[0])
        return {"anyOf": [_python_type_to_json_schema(a) for a in args]}
    
    # Handle List[T]
    if origin is list:
        args = getattr(python_type, "__args__", None)
        if args:
            return {"type": "array", "items": _python_type_to_json_schema(args[0])}
        return {"type": "array"}
    
    # Handle Dict[K, V]
    if origin is dict:
        return {"type": "object"}
    
    # Default to string
    return {"type": "string"}


@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""
    
    name: str
    type: Any
    description: str = ""
    required: bool = True
    default: Any = None
    
    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema property."""
        schema = _python_type_to_json_schema(self.type)
        if self.description:
            schema["description"] = self.description
        return schema


class NeuralTool(ABC):
    """
    Base class for all Reasona tools.
    
    Subclass this to create custom tools with automatic schema
    generation and type validation.
    
    Example:
        >>> class WeatherTool(NeuralTool):
        ...     '''Get current weather for a location.'''
        ...     
        ...     def execute(self, location: str, units: str = "celsius") -> dict:
        ...         # Implementation here
        ...         return {"location": location, "temp": 22, "units": units}
        ...
        >>> tool = WeatherTool()
        >>> result = tool("London")
    """
    
    # Override these in subclasses
    name: Optional[str] = None
    description: Optional[str] = None
    
    def __init__(self) -> None:
        """Initialize the tool."""
        # Use class docstring as description if not provided
        if self.description is None:
            self.description = (self.__class__.__doc__ or "").strip()
        
        # Use class name as tool name if not provided
        if self.name is None:
            self.name = self._default_name()
        
        # Extract parameters from execute method
        self._parameters = self._extract_parameters()
    
    def _default_name(self) -> str:
        """Generate default tool name from class name."""
        name = self.__class__.__name__
        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)
    
    def _extract_parameters(self) -> list[ToolParameter]:
        """Extract parameters from the execute method."""
        sig = inspect.signature(self.execute)
        hints = get_type_hints(self.execute) if hasattr(self.execute, "__annotations__") else {}
        
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            # Determine if required
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default
            
            # Get type hint
            param_type = hints.get(param_name, str)
            
            # Get description from docstring (basic parsing)
            description = ""
            if self.__class__.__doc__:
                # Try to find parameter in docstring
                for line in self.__class__.__doc__.split("\n"):
                    if param_name in line and ":" in line:
                        description = line.split(":", 1)[-1].strip()
                        break
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=description,
                required=required,
                default=default,
            ))
        
        return parameters
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given arguments.
        
        Override this method in your tool subclass.
        
        Args:
            **kwargs: Tool arguments.
            
        Returns:
            The tool execution result.
        """
        raise NotImplementedError
    
    def to_schema(self) -> dict[str, Any]:
        """
        Generate JSON Schema for this tool.
        
        Returns:
            OpenAI-compatible function schema.
        """
        # Build properties
        properties = {}
        required = []
        
        for param in self._parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description or "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }
    
    def __call__(self, **kwargs: Any) -> Any:
        """Allow calling the tool directly."""
        return self.execute(**kwargs)
    
    def __repr__(self) -> str:
        return f"NeuralTool(name='{self.name}')"


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable:
    """
    Decorator to convert a function into a NeuralTool.
    
    Example:
        >>> @tool(description="Calculate the sum of two numbers")
        ... def add(a: int, b: int) -> int:
        ...     return a + b
        ...
        >>> agent = Conductor(name="calc", model="openai/gpt-4o", tools=[add])
    """
    def decorator(func: Callable) -> NeuralTool:
        # Create a dynamic NeuralTool subclass
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or "").strip()
        
        class FunctionTool(NeuralTool):
            def __init__(self):
                self.name = tool_name
                self.description = tool_description
                self._func = func
                self._parameters = self._extract_parameters()
            
            def _extract_parameters(self) -> list[ToolParameter]:
                sig = inspect.signature(func)
                hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
                
                parameters = []
                for param_name, param in sig.parameters.items():
                    required = param.default == inspect.Parameter.empty
                    default = None if required else param.default
                    param_type = hints.get(param_name, str)
                    
                    parameters.append(ToolParameter(
                        name=param_name,
                        type=param_type,
                        required=required,
                        default=default,
                    ))
                
                return parameters
            
            def execute(self, **kwargs: Any) -> Any:
                return self._func(**kwargs)
        
        return FunctionTool()
    
    return decorator


class ToolRegistry:
    """
    Registry for managing available tools.
    
    The registry provides tool discovery and lookup functionality.
    """
    
    def __init__(self) -> None:
        self._tools: dict[str, NeuralTool] = {}
    
    def register(self, tool: NeuralTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[NeuralTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def all(self) -> list[NeuralTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def search(self, query: str) -> list[NeuralTool]:
        """Search tools by name or description."""
        query_lower = query.lower()
        results = []
        
        for tool in self._tools.values():
            if query_lower in tool.name.lower():
                results.append(tool)
            elif tool.description and query_lower in tool.description.lower():
                results.append(tool)
        
        return results


# Global tool registry
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry
