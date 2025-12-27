"""
Test configuration and fixtures for Reasona.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?",
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello! How can I help you?"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 25,
            "output_tokens": 20
        }
    }


@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    from reasona.tools import Calculator, DateTime, JsonParser
    return [Calculator(), DateTime(), JsonParser()]
