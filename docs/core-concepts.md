# Core Concepts

Understanding Reasona's architecture and core concepts.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                     Workflow                          │  │
│  │  (Declarative multi-stage pipelines)                 │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Orchestration Layer                       │
│  ┌─────────────┐    Synapse    ┌─────────────┐            │
│  │  Conductor  │◄─────────────►│  Conductor  │            │
│  │   (Agent)   │   Protocol    │   (Agent)   │            │
│  └─────────────┘               └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                       Tools Layer                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │Calculator │ │ DateTime  │ │HttpRequest│ │  Custom   │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Provider Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  OpenAI  │ │Anthropic │ │  Google  │ │  Ollama  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Conductor

The **Conductor** is the main agent class in Reasona. It manages:

- LLM communication
- Tool execution
- Conversation state
- Response generation

### Creating a Conductor

```python
from reasona import Conductor

agent = Conductor(
    name="my-agent",
    model="openai/gpt-4o",
    instructions="You are a helpful assistant.",
    tools=[],
    temperature=0.7
)
```

### Key Methods

| Method | Description |
|--------|-------------|
| `think(message)` | Synchronous message processing |
| `athink(message)` | Async message processing |
| `stream(message)` | Async streaming response |
| `reset()` | Clear conversation history |
| `add_tool(tool)` | Add a tool to the agent |
| `serve(port)` | Start REST API server |

### Conversation Management

```python
# Messages persist across calls
response1 = agent.think("My name is Alice.")
response2 = agent.think("What's my name?")  # Remembers "Alice"

# Reset to clear history
agent.reset()
```

## NeuralTool

**NeuralTool** is the base class for agent tools. Tools extend agent capabilities with specific functions.

### Creating Tools

**Class-based approach:**

```python
from reasona.tools import NeuralTool

class WeatherTool(NeuralTool):
    name = "get_weather"
    description = "Get weather for a location"
    
    async def execute(self, location: str) -> dict:
        return {"location": location, "temp": 22}
```

**Decorator approach:**

```python
from reasona.tools import tool

@tool(description="Add two numbers")
async def add(a: int, b: int) -> int:
    return a + b
```

### Built-in Tools

| Tool | Description |
|------|-------------|
| `Calculator` | Safe math evaluation |
| `DateTime` | Time and date operations |
| `HttpRequest` | HTTP API calls |
| `FileReader` | Read file contents |
| `FileWriter` | Write to files |
| `ShellCommand` | Execute shell commands |
| `JsonParser` | Parse and extract JSON |
| `WebSearch` | Web search (requires API) |

## Synapse

**Synapse** enables agent-to-agent communication using the Synaptic Protocol.

### Connecting Agents

```python
from reasona import Conductor, Synapse

agent1 = Conductor(name="researcher", model="openai/gpt-4o")
agent2 = Conductor(name="writer", model="anthropic/claude-3-5-sonnet")

synapse = Synapse()
synapse.connect(agent1)
synapse.connect(agent2)
```

### Communication Patterns

**Delegation:**
```python
# One agent delegates to another
result = await synapse.delegate(
    from_agent=agent1,
    to_agent=agent2,
    task="Write a blog post about AI"
)
```

**Broadcasting:**
```python
# Send to multiple agents
responses = await synapse.broadcast(
    message="Analyze this data",
    agents=[agent1, agent2, agent3]
)
```

**Orchestration:**
```python
# Coordinated multi-agent task
result = await synapse.orchestrate(
    task="Research and write a report",
    lead=agent1,
    participants=[agent2, agent3]
)
```

### Message Types

| Type | Purpose |
|------|---------|
| `REQUEST` | Ask an agent to perform a task |
| `RESPONSE` | Reply to a request |
| `NOTIFICATION` | One-way information sharing |
| `ERROR` | Report an error |
| `HANDSHAKE` | Initial connection |
| `HEARTBEAT` | Keep connection alive |

## Workflow

**Workflow** enables declarative multi-stage pipelines.

### Creating Workflows

```python
from reasona import Workflow, Conductor

planner = Conductor(name="planner", model="openai/gpt-4o")
executor = Conductor(name="executor", model="openai/gpt-4o")

workflow = Workflow(name="task-pipeline")

workflow.add_stage(
    name="plan",
    agent=planner,
    prompt_template="Create a plan for: {input}"
)

workflow.add_stage(
    name="execute",
    agent=executor,
    prompt_template="Execute this plan: {plan}"
)
```

### Running Workflows

```python
result = await workflow.run(input="Build a website")

print(result["plan"])    # Output from planning stage
print(result["execute"]) # Output from execution stage
```

### Conditional Stages

```python
workflow.add_stage(
    name="review",
    agent=reviewer,
    prompt_template="Review: {execute}",
    condition=lambda ctx: ctx.get("needs_review", False)
)
```

### Stage Options

| Option | Description |
|--------|-------------|
| `prompt_template` | Template with `{variable}` placeholders |
| `condition` | Function to determine if stage runs |
| `retries` | Number of retry attempts |
| `timeout` | Maximum execution time |
| `transform` | Post-process stage output |

## Context

**Context** provides structured information to agents.

### Context Types

```python
from reasona.core import Context, UserContext, SessionContext

context = Context(
    user=UserContext(
        id="user_123",
        name="Alice",
        preferences={"language": "en"}
    ),
    session=SessionContext(
        id="session_456",
        started_at=datetime.now()
    ),
    metadata={"custom": "data"}
)

agent = Conductor(context=context, ...)
```

## Message

**Message** represents a single conversation turn.

```python
from reasona.core import Message, Role

message = Message(
    role=Role.USER,
    content="Hello!",
    metadata={"source": "web"}
)
```

### Roles

| Role | Description |
|------|-------------|
| `SYSTEM` | System instructions |
| `USER` | User messages |
| `ASSISTANT` | Agent responses |
| `TOOL` | Tool execution results |

## Configuration

**ReasonaConfig** manages settings and API keys.

```python
from reasona.core import ReasonaConfig

config = ReasonaConfig()

# Set API keys
config.set_api_key("openai", "sk-...")
config.set_api_key("anthropic", "sk-ant-...")

# Get provider configuration
openai_config = config.get_provider_config("openai")
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google AI API key |
| `OLLAMA_HOST` | Ollama server URL |

## HyperMCP

**HyperMCP** is Reasona's MCP server implementation.

```python
from reasona.mcp import HyperMCP

mcp = HyperMCP(name="my-tools", version="1.0.0")

@mcp.tool(description="Get weather")
async def get_weather(location: str) -> dict:
    return {"location": location, "temp": 22}

mcp.serve(port=9000)
```

### MCP Concepts

| Concept | Description |
|---------|-------------|
| **Tools** | Functions the LLM can call |
| **Resources** | Data the LLM can read |
| **Prompts** | Template prompts |

## Next Steps

- [API Reference](api-reference.md) - Detailed API documentation
- [Examples](../examples/README.md) - Working code examples
