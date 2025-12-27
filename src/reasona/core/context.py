"""
Context management for Reasona agent execution.

The Context provides a structured way to pass additional information
to agents during execution, including user preferences, session data,
and runtime configuration.
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class UserContext:
    """Information about the current user."""
    
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    preferences: dict[str, Any] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    """Information about the current session."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.utcnow)
    variables: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RuntimeContext:
    """Runtime configuration and flags."""
    
    debug: bool = False
    trace: bool = False
    timeout: Optional[float] = None
    max_iterations: int = 10
    allow_tool_use: bool = True
    allow_streaming: bool = True
    custom_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class Context:
    """
    Unified context for agent execution.
    
    The Context object provides a structured way to pass information
    to agents during execution, including user data, session state,
    and runtime configuration.
    
    Example:
        >>> context = Context(
        ...     user=UserContext(id="user-123", name="John"),
        ...     runtime=RuntimeContext(debug=True)
        ... )
        >>> response = agent.think("Hello", context=context)
    """
    
    user: Optional[UserContext] = None
    session: SessionContext = field(default_factory=SessionContext)
    runtime: RuntimeContext = field(default_factory=RuntimeContext)
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a variable in the context."""
        self.variables[key] = value
    
    def update(self, **kwargs: Any) -> "Context":
        """Update context variables (fluent API)."""
        self.variables.update(kwargs)
        return self
    
    def with_user(self, **kwargs: Any) -> "Context":
        """Set user context (fluent API)."""
        if self.user is None:
            self.user = UserContext(**kwargs)
        else:
            for key, value in kwargs.items():
                setattr(self.user, key, value)
        return self
    
    def with_runtime(self, **kwargs: Any) -> "Context":
        """Set runtime context (fluent API)."""
        for key, value in kwargs.items():
            setattr(self.runtime, key, value)
        return self
    
    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        result: dict[str, Any] = {
            "session_id": self.session.id,
            "variables": self.variables,
            "metadata": self.metadata,
        }
        
        if self.user:
            result["user"] = {
                "id": self.user.id,
                "name": self.user.name,
                "preferences": self.user.preferences,
            }
        
        return result
    
    @classmethod
    def create(cls, **kwargs: Any) -> "Context":
        """Factory method to create a context with common defaults."""
        return cls(variables=kwargs)


# Convenience function for creating contexts
def context(**kwargs: Any) -> Context:
    """Create a new Context with the given variables."""
    return Context.create(**kwargs)
