"""
Multi-Agent Collaboration Example
=================================

This example demonstrates how to create multiple agents that
communicate and collaborate using the Synapse protocol.
"""

import asyncio
from reasona import Conductor, Synapse


async def main():
    # Create specialized agents
    researcher = Conductor(
        name="researcher",
        model="openai/gpt-4o",
        instructions="""You are a research specialist. Your job is to:
        - Gather and analyze information
        - Identify key facts and insights
        - Provide well-structured research summaries
        When given a topic, provide a comprehensive research brief."""
    )
    
    writer = Conductor(
        name="writer",
        model="anthropic/claude-3-5-sonnet",
        instructions="""You are a creative writer. Your job is to:
        - Transform research into engaging content
        - Write clear, compelling prose
        - Maintain appropriate tone for the audience
        When given research, create polished written content."""
    )
    
    editor = Conductor(
        name="editor",
        model="openai/gpt-4o",
        instructions="""You are an expert editor. Your job is to:
        - Review content for clarity and accuracy
        - Improve flow and readability
        - Fix grammar and style issues
        - Provide constructive feedback
        When given content, provide your edited version and suggestions."""
    )
    
    # Create a Synapse for agent communication
    synapse = Synapse()
    
    # Connect all agents
    synapse.connect(researcher)
    synapse.connect(writer)
    synapse.connect(editor)
    
    print("=== Multi-Agent Content Pipeline ===\n")
    
    # Step 1: Research phase
    print("📚 Step 1: Researching topic...")
    research_result = await researcher.athink(
        "Research the topic: The impact of artificial intelligence on healthcare. "
        "Focus on recent developments, key benefits, and potential challenges."
    )
    print(f"Research complete.\n")
    
    # Step 2: Delegate writing to the writer
    print("✍️ Step 2: Writing article...")
    article_result = await synapse.delegate(
        from_agent=researcher,
        to_agent=writer,
        task=f"Based on this research, write a 300-word blog post:\n\n{research_result}"
    )
    print(f"Article draft complete.\n")
    
    # Step 3: Delegate editing
    print("📝 Step 3: Editing article...")
    final_result = await synapse.delegate(
        from_agent=writer,
        to_agent=editor,
        task=f"Edit and improve this article:\n\n{article_result}"
    )
    print(f"Editing complete.\n")
    
    # Print final result
    print("=" * 50)
    print("FINAL ARTICLE:")
    print("=" * 50)
    print(final_result)
    
    # Alternative: Use orchestrate for automatic coordination
    print("\n" + "=" * 50)
    print("=== Orchestrated Collaboration ===")
    print("=" * 50 + "\n")
    
    result = await synapse.orchestrate(
        task="Create a short blog post about sustainable energy solutions",
        lead=researcher,
        participants=[writer, editor]
    )
    
    print("Orchestrated result:")
    print(result)


async def broadcast_example():
    """Example of broadcasting messages to multiple agents."""
    
    # Create several agents
    agents = [
        Conductor(
            name=f"analyst_{i}",
            model="openai/gpt-4o",
            instructions=f"You are analyst {i}. Provide unique insights."
        )
        for i in range(3)
    ]
    
    synapse = Synapse()
    for agent in agents:
        synapse.connect(agent)
    
    # Broadcast a question to all agents
    print("=== Broadcasting Question ===\n")
    responses = await synapse.broadcast(
        message="What is the most important trend in AI for 2025?",
        agents=agents
    )
    
    for agent, response in zip(agents, responses):
        print(f"{agent.name}: {response[:200]}...\n")


if __name__ == "__main__":
    print("Running multi-agent collaboration example...\n")
    asyncio.run(main())
    
    print("\n" + "=" * 50)
    print("Running broadcast example...\n")
    asyncio.run(broadcast_example())
