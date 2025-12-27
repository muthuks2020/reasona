"""
Markdown Agent Definition Example
==================================

This example shows how to define agents using markdown files
with YAML frontmatter for declarative agent configuration.
"""

import asyncio
import tempfile
from pathlib import Path
from reasona import Conductor


# Example markdown agent definition
AGENT_MARKDOWN = '''---
name: research-assistant
model: openai/gpt-4o
temperature: 0.7
max_tokens: 2000
tools:
  - calculator
  - datetime
  - web_search
---

# Research Assistant

You are an expert research assistant specializing in gathering and synthesizing information.

## Core Capabilities

- **Information Gathering**: Search the web and compile relevant data
- **Analysis**: Break down complex topics into understandable components
- **Synthesis**: Combine information from multiple sources
- **Fact-Checking**: Verify claims and identify reliable sources

## Guidelines

1. Always cite your sources when possible
2. Present information objectively
3. Acknowledge uncertainty when appropriate
4. Ask clarifying questions if the research scope is unclear

## Response Format

Structure your responses with:
- **Summary**: Brief overview of findings
- **Key Points**: Main discoveries or facts
- **Details**: In-depth information
- **Sources**: References used
'''


async def main():
    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(AGENT_MARKDOWN)
        agent_file = f.name
    
    try:
        # Load agent from markdown file
        print("=== Loading Agent from Markdown ===")
        agent = Conductor.from_markdown(agent_file)
        
        print(f"Agent Name: {agent.name}")
        print(f"Model: {agent.model}")
        print(f"Tools: {[t.name if hasattr(t, 'name') else type(t).__name__ for t in agent.tools]}")
        print()
        
        # Use the agent
        print("=== Running Agent ===")
        response = await agent.athink(
            "What are the key benefits and challenges of renewable energy?"
        )
        print(f"Response:\n{response}")
        
        # Get the agent's discovery card
        print("\n=== Agent Discovery Card ===")
        card = agent.get_discovery_card()
        import json
        print(json.dumps(card, indent=2))
        
    finally:
        # Clean up
        Path(agent_file).unlink()


def create_agent_library():
    """Create a library of markdown agent definitions."""
    
    agents_dir = Path("agents")
    agents_dir.mkdir(exist_ok=True)
    
    # Customer support agent
    (agents_dir / "support.md").write_text('''---
name: customer-support
model: anthropic/claude-3-5-sonnet
temperature: 0.3
---

# Customer Support Agent

You are a friendly and helpful customer support representative.

## Tone
- Professional yet warm
- Patient and understanding
- Solution-oriented

## Process
1. Acknowledge the customer's concern
2. Ask clarifying questions if needed
3. Provide clear solutions or next steps
4. Confirm the customer's satisfaction
''')
    
    # Code reviewer agent
    (agents_dir / "reviewer.md").write_text('''---
name: code-reviewer
model: openai/gpt-4o
temperature: 0.2
tools:
  - shell_command
---

# Code Review Agent

You are an expert code reviewer focused on quality and best practices.

## Review Criteria
- Code correctness and logic
- Performance considerations
- Security vulnerabilities
- Code style and readability
- Test coverage

## Feedback Style
- Be constructive and specific
- Provide examples when suggesting changes
- Prioritize issues by severity
''')
    
    # Creative writer agent
    (agents_dir / "writer.md").write_text('''---
name: creative-writer
model: anthropic/claude-3-5-sonnet
temperature: 0.9
max_tokens: 4000
---

# Creative Writer

You are a versatile creative writer who can adapt to any style or genre.

## Capabilities
- Fiction: Short stories, novels, scripts
- Non-fiction: Articles, essays, blog posts
- Marketing: Copy, slogans, campaigns
- Technical: Documentation, guides

## Process
1. Understand the audience and purpose
2. Establish tone and style
3. Create engaging content
4. Refine and polish
''')
    
    print(f"Created agent library in {agents_dir.absolute()}")
    print("Files:")
    for f in agents_dir.glob("*.md"):
        print(f"  - {f.name}")
    
    return agents_dir


async def load_agent_library():
    """Load and use agents from the library."""
    
    agents_dir = create_agent_library()
    
    # Load all agents
    agents = {}
    for agent_file in agents_dir.glob("*.md"):
        agent = Conductor.from_markdown(str(agent_file))
        agents[agent.name] = agent
        print(f"Loaded: {agent.name}")
    
    print()
    
    # Use an agent
    if "creative-writer" in agents:
        writer = agents["creative-writer"]
        response = await writer.athink("Write a haiku about programming")
        print(f"Creative Writer says:\n{response}")


if __name__ == "__main__":
    print("=== Markdown Agent Example ===\n")
    asyncio.run(main())
    
    print("\n" + "=" * 50 + "\n")
    print("=== Agent Library Example ===\n")
    asyncio.run(load_agent_library())
