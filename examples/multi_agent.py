"""
Multi-Agent Collaboration Example

This example demonstrates how multiple AI agents can work together
using the Synapse protocol for agent-to-agent communication.

Usage:
    python examples/multi_agent.py

Requirements:
    - Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY environment variables
"""

import asyncio
from reasona import Conductor, Synapse
from reasona.tools import WebSearch, Calculator


# Create specialized agents
researcher = Conductor(
    name="researcher",
    model="openai/gpt-4o",
    instructions="""You are a research specialist. Your job is to:
1. Analyze research requests
2. Break them down into key topics
3. Provide structured research findings
Be thorough but concise.""",
    tools=[WebSearch()],
)

analyst = Conductor(
    name="analyst",
    model="openai/gpt-4o",
    instructions="""You are a data analyst. Your job is to:
1. Take research findings and analyze them
2. Identify patterns and insights
3. Provide numerical analysis when relevant
Be analytical and precise.""",
    tools=[Calculator()],
)

writer = Conductor(
    name="writer",
    model="anthropic/claude-3-5-sonnet",  # Use Claude for writing
    instructions="""You are a professional writer. Your job is to:
1. Take analyzed information
2. Create well-structured, engaging content
3. Ensure clarity and readability
Write in a professional but accessible style.""",
)

editor = Conductor(
    name="editor",
    model="anthropic/claude-3-5-sonnet",
    instructions="""You are an editor. Your job is to:
1. Review written content
2. Improve clarity and flow
3. Fix any errors
4. Provide the final polished version
Be meticulous and constructive.""",
)


async def run_synapse_collaboration():
    """Demonstrate Synapse-based agent collaboration."""
    print("\n🔗 Synapse Collaboration Demo\n")
    print("=" * 50)
    
    # Create synapse network
    synapse = Synapse()
    
    # Connect all agents
    synapse.connect(researcher)
    synapse.connect(analyst)
    synapse.connect(writer)
    synapse.connect(editor)
    
    # Task to accomplish
    task = """Research the current state of renewable energy adoption worldwide.
    Focus on solar and wind energy growth in the last 5 years.
    Create a brief executive summary suitable for business stakeholders."""
    
    print(f"📋 Task: {task}\n")
    print("=" * 50)
    
    # Use orchestrate to coordinate agents
    # The lead agent (researcher) will coordinate with others
    result = await synapse.orchestrate(
        task=task,
        lead=researcher,
    )
    
    print("\n📝 Final Result:")
    print("-" * 50)
    print(result)
    
    return result


async def run_direct_delegation():
    """Demonstrate direct agent-to-agent delegation."""
    print("\n🎯 Direct Delegation Demo\n")
    print("=" * 50)
    
    synapse = Synapse()
    synapse.connect(researcher)
    synapse.connect(writer)
    
    # Direct message from researcher to writer
    research_output = """Key findings on AI in healthcare:
    1. AI diagnostics accuracy: 94% for certain conditions
    2. Cost reduction: 30% in administrative tasks
    3. Adoption rate: Growing 40% year-over-year
    4. Main challenges: Data privacy, regulatory compliance"""
    
    print(f"📊 Research output being sent to writer...\n")
    
    # Delegate task to writer
    result = await synapse.delegate(
        from_agent="researcher",
        to_agent="writer",
        task=f"Write a 2-paragraph summary based on this research:\n{research_output}"
    )
    
    print("📝 Writer's output:")
    print("-" * 50)
    print(result)
    
    return result


async def run_broadcast():
    """Demonstrate broadcasting to multiple agents."""
    print("\n📢 Broadcast Demo\n")
    print("=" * 50)
    
    synapse = Synapse()
    synapse.connect(analyst)
    synapse.connect(writer)
    synapse.connect(editor)
    
    message = "The project deadline has been moved to next Friday. Please adjust your outputs accordingly."
    
    print(f"Broadcasting: {message}\n")
    
    responses = await synapse.broadcast(
        sender="system",
        message=message
    )
    
    print("📥 Responses received:")
    for agent_name, response in responses.items():
        print(f"\n{agent_name}: {response[:100]}...")
    
    return responses


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("    REASONA MULTI-AGENT COLLABORATION EXAMPLES")
    print("=" * 60)
    
    # Note: These require API keys to actually run
    # Uncomment to run:
    
    # await run_synapse_collaboration()
    # await run_direct_delegation()
    # await run_broadcast()
    
    print("\n💡 To run these examples, uncomment the function calls")
    print("   and ensure your API keys are set.\n")
    
    # Show agent info instead
    print("📋 Registered Agents:")
    for agent in [researcher, analyst, writer, editor]:
        print(f"  - {agent.name}: {agent.model}")


if __name__ == "__main__":
    asyncio.run(main())
