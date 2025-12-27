"""
Reasona - A Production-Grade Control Plane for AI Agent Orchestration

Reasona provides a unified framework for building, deploying, and managing
AI agents with secure inter-agent communication and tool management.

Basic usage:
    >>> from reasona import Conductor
    >>> agent = Conductor(name="assistant", model="openai/gpt-4o")
    >>> response = agent.think("Hello, world!")
"""

from reasona.core.conductor import Conductor
from reasona.core.synapse import Synapse
from reasona.core.workflow import Workflow
from reasona.core.config import ReasonaConfig

__version__ = "0.1.0"
__author__ = "Reasona Contributors"
__license__ = "MIT"

__all__ = [
    "Conductor",
    "Synapse",
    "Workflow",
    "ReasonaConfig",
    "__version__",
]
