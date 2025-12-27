"""
Basic Agent Example
===================

This example demonstrates how to create a simple AI agent
using Reasona's Conductor class.
"""

import asyncio
from reasona import Conductor
from reasona.tools import Calculator, DateTime


def sync_example():
    """Synchronous agent example."""
    
    # Create an agent with tools
    agent = Conductor(
        name="assistant",
        model="openai/gpt-4o",  # or "anthropic/claude-3-5-sonnet"
        instructions="You are a helpful assistant that can perform calculations and tell the time.",
        tools=[Calculator(), DateTime()]
    )
    
    # Send a message and get a response
    response = agent.think("What is 15 * 23 + 7?")
    print(f"Response: {response}")
    
    # Continue the conversation
    response = agent.think("What time is it now?")
    print(f"Response: {response}")
    
    # Reset conversation
    agent.reset()


async def async_example():
    """Asynchronous agent example."""
    
    agent = Conductor(
        name="async-assistant",
        model="openai/gpt-4o",
        instructions="You are a helpful assistant."
    )
    
    # Async thinking
    response = await agent.athink("Explain quantum computing in simple terms.")
    print(f"Response: {response}")


async def streaming_example():
    """Streaming response example."""
    
    agent = Conductor(
        name="streaming-assistant",
        model="openai/gpt-4o",
        instructions="You are a helpful assistant."
    )
    
    # Stream the response
    print("Streaming response: ", end="")
    async for chunk in agent.stream("Write a haiku about programming."):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    print("=== Sync Example ===")
    sync_example()
    
    print("\n=== Async Example ===")
    asyncio.run(async_example())
    
    print("\n=== Streaming Example ===")
    asyncio.run(streaming_example())
