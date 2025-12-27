# Getting Started

This guide will help you get up and running with Reasona in minutes.

## Installation

### Using pip

```bash
pip install reasona
```

### From source

```bash
git clone https://github.com/reasona/reasona.git
cd reasona
pip install -e ".[dev]"
```

### Optional dependencies

```bash
# All providers and features
pip install "reasona[all]"

# Development tools
pip install "reasona[dev]"

# Documentation tools
pip install "reasona[docs]"
```

## Configuration

### API Keys

Set your API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google (optional)
export GOOGLE_API_KEY="..."

# Ollama (optional, for local models)
export OLLAMA_HOST="http://localhost:11434"
```

Or use a `.env` file:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Reasona automatically loads `.env` files from the current directory.

## Creating Your First Agent

### Basic Agent

```python
from reasona import Conductor

# Create an agent
agent = Conductor(
    name="my-assistant",
    model="openai/gpt-4o",  # or "anthropic/claude-3-5-sonnet"
    instructions="You are a helpful assistant."
)

# Send a message
response = agent.think("Hello! What can you do?")
print(response)
```

### With Tools

```python
from reasona import Conductor
from reasona.tools import Calculator, DateTime

agent = Conductor(
    name="math-assistant",
    model="openai/gpt-4o",
    instructions="You help with calculations and time questions.",
    tools=[Calculator(), DateTime()]
)

# The agent can now use tools
response = agent.think("What is 15% of 250?")
print(response)
```

### Async Operations

```python
import asyncio
from reasona import Conductor

async def main():
    agent = Conductor(
        name="async-assistant",
        model="openai/gpt-4o"
    )
    
    # Async thinking
    response = await agent.athink("Explain quantum computing.")
    print(response)

asyncio.run(main())
```

### Streaming Responses

```python
import asyncio
from reasona import Conductor

async def main():
    agent = Conductor(
        name="streaming-assistant",
        model="openai/gpt-4o"
    )
    
    # Stream the response
    async for chunk in agent.stream("Write a short story."):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

## Model Selection

Specify models using the format `provider/model-name`:

```python
# OpenAI models
agent = Conductor(model="openai/gpt-4o")
agent = Conductor(model="openai/gpt-4-turbo")
agent = Conductor(model="openai/gpt-3.5-turbo")

# Anthropic models
agent = Conductor(model="anthropic/claude-3-5-sonnet")
agent = Conductor(model="anthropic/claude-3-opus")
agent = Conductor(model="anthropic/claude-3-haiku")

# Google models
agent = Conductor(model="google/gemini-pro")
agent = Conductor(model="google/gemini-1.5-flash")

# Local models via Ollama
agent = Conductor(model="ollama/llama2")
agent = Conductor(model="ollama/mistral")
agent = Conductor(model="ollama/codellama")
```

## Configuration Options

```python
agent = Conductor(
    name="configured-agent",
    model="openai/gpt-4o",
    instructions="Custom system prompt here.",
    
    # Generation parameters
    temperature=0.7,
    max_tokens=2000,
    top_p=0.9,
    
    # Tools
    tools=[Calculator()],
    
    # Callbacks for monitoring
    callbacks=[],
    
    # Custom metadata
    metadata={"version": "1.0"}
)
```

## Using the CLI

Reasona includes a command-line interface:

```bash
# Interactive chat
reasona chat --model openai/gpt-4o

# Run an agent from markdown file
reasona run agent.md

# Start a REST API server
reasona serve agent.md --port 8000

# Initialize a new project
reasona init my-project

# List available tools
reasona tools list
```

## Next Steps

- [Core Concepts](core-concepts.md) - Understand the architecture
- [Custom Tools](api-reference.md#tools) - Create your own tools
- [Multi-Agent](api-reference.md#synapse) - Connect multiple agents
- [Examples](../examples/README.md) - Working code examples
