"""
Neural Tools - First-class tool support for Reasona agents.

Neural Tools are self-describing, type-safe functions that agents
can invoke to interact with external systems and perform actions.
"""

from reasona.tools.base import NeuralTool, tool
from reasona.tools.builtin import (
    Calculator,
    WebSearch,
    HttpRequest,
    FileReader,
    FileWriter,
    ShellCommand,
    DateTime,
    JsonParser,
)

__all__ = [
    "NeuralTool",
    "tool",
    "Calculator",
    "WebSearch",
    "HttpRequest",
    "FileReader",
    "FileWriter",
    "ShellCommand",
    "DateTime",
    "JsonParser",
]
