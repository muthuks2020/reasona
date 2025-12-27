"""
Basic Agent Example

This example demonstrates creating a simple AI agent with tools.

Usage:
    python examples/basic_agent.py

Requirements:
    - Set OPENAI_API_KEY environment variable
"""

import asyncio
from reasona import Conductor
from reasona.tools import Calculator, DateTime

# Create a basic agent with tools
agent = Conductor(
    name="assistant",
    model="openai/gpt-4o",  # Can also use "anthropic/claude-3-5-sonnet"
    instructions="""You are a helpful AI assistant. You can perform calculations 
and tell the current time. Be concise and friendly in your responses.""",
    tools=[Calculator(), DateTime()],
    temperature=0.7,
)


def main():
    """Run interactive chat."""
    print(f"\n🤖 Agent '{agent.name}' is ready!")
    print("Type 'exit' to quit, 'reset' to clear history.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if user_input.lower() == "reset":
                agent.reset()
                print("Conversation reset.\n")
                continue
            
            # Get response
            response = agent.think(user_input)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


async def main_async():
    """Run async version with streaming."""
    print(f"\n🤖 Agent '{agent.name}' is ready! (Streaming mode)")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() == "exit":
                break
            
            # Stream response
            print("\nAssistant: ", end="", flush=True)
            async for chunk in agent.stream(user_input):
                print(chunk, end="", flush=True)
            print("\n")
            
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    # Run sync version
    main()
    
    # Or run async version with streaming:
    # asyncio.run(main_async())
