"""
Message and Role definitions for Reasona conversations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid


class Role(str, Enum):
    """Conversation role enumeration."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class Message:
    """
    Represents a single message in a conversation.
    
    Attributes:
        role: The role of the message sender.
        content: The text content of the message.
        name: Optional name identifier.
        tool_call_id: Optional tool call identifier.
        tool_calls: Optional list of tool calls.
        metadata: Optional additional metadata.
        timestamp: When the message was created.
        id: Unique message identifier.
    """
    
    role: Role
    content: Optional[str] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for API calls."""
        result: dict[str, Any] = {"role": str(self.role)}
        
        if self.content is not None:
            result["content"] = self.content
        
        if self.name:
            result["name"] = self.name
        
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        
        return result
    
    @classmethod
    def system(cls, content: str) -> "Message":
        """Create a system message."""
        return cls(role=Role.SYSTEM, content=content)
    
    @classmethod
    def user(cls, content: str, name: Optional[str] = None) -> "Message":
        """Create a user message."""
        return cls(role=Role.USER, content=content, name=name)
    
    @classmethod
    def assistant(
        cls,
        content: Optional[str] = None,
        tool_calls: Optional[list[dict[str, Any]]] = None
    ) -> "Message":
        """Create an assistant message."""
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)
    
    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> "Message":
        """Create a tool response message."""
        return cls(role=Role.TOOL, content=content, tool_call_id=tool_call_id)


@dataclass
class Conversation:
    """
    Represents a complete conversation thread.
    
    Attributes:
        id: Unique conversation identifier.
        messages: List of messages in the conversation.
        metadata: Additional conversation metadata.
        created_at: When the conversation started.
        updated_at: When the conversation was last updated.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def clear(self) -> None:
        """Clear all messages except system messages."""
        self.messages = [m for m in self.messages if m.role == Role.SYSTEM]
        self.updated_at = datetime.utcnow()
    
    def to_list(self) -> list[dict[str, Any]]:
        """Convert conversation to list of dictionaries."""
        return [msg.to_dict() for msg in self.messages]
    
    @property
    def last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    def __len__(self) -> int:
        return len(self.messages)
    
    def __iter__(self):
        return iter(self.messages)
