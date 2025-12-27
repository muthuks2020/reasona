# API Reference

Complete API documentation for Reasona.

## reasona.Conductor

The main agent class.

### Constructor

```python
Conductor(
    name: str = "agent",
    model: str = "openai/gpt-4o",
    instructions: str | None = None,
    tools: list[NeuralTool] | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    top_p: float | None = None,
    context: Context | None = None,
    callbacks: list[Callback] | None = None,
    metadata: dict | None = None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"agent"` | Agent identifier |
| `model` | `str` | `"openai/gpt-4o"` | Model in format `provider/model` |
| `instructions` | `str` | `None` | System prompt |
| `tools` | `list` | `None` | List of NeuralTool instances |
| `temperature` | `float` | `0.7` | Sampling temperature |
| `max_tokens` | `int` | `None` | Maximum response tokens |
| `top_p` | `float` | `None` | Nucleus sampling parameter |
| `context` | `Context` | `None` | Execution context |
| `callbacks` | `list` | `None` | Event callbacks |
| `metadata` | `dict` | `None` | Custom metadata |

### Methods

#### think

```python
def think(self, message: str) -> str
```

Process a message synchronously.

**Example:**
```python
response = agent.think("What is 2 + 2?")
```

#### athink

```python
async def athink(self, message: str) -> str
```

Process a message asynchronously.

**Example:**
```python
response = await agent.athink("Explain gravity.")
```

#### stream

```python
async def stream(self, message: str) -> AsyncIterator[str]
```

Stream a response asynchronously.

**Example:**
```python
async for chunk in agent.stream("Write a story."):
    print(chunk, end="")
```

#### reset

```python
def reset(self) -> None
```

Clear conversation history.

#### add_tool

```python
def add_tool(self, tool: NeuralTool) -> Self
```

Add a tool to the agent. Returns self for chaining.

#### serve

```python
def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None
```

Start a REST API server.

#### from_markdown

```python
@classmethod
def from_markdown(cls, path: str) -> "Conductor"
```

Create an agent from a markdown file with YAML frontmatter.

#### get_discovery_card

```python
def get_discovery_card(self) -> dict
```

Get the agent's discovery card for the Synaptic Protocol.

---

## reasona.Synapse

Agent-to-agent communication.

### Constructor

```python
Synapse()
```

### Methods

#### connect

```python
def connect(self, agent: Conductor) -> Self
```

Connect an agent to the synapse.

#### disconnect

```python
def disconnect(self, agent: Conductor) -> Self
```

Disconnect an agent.

#### send

```python
async def send(
    self,
    from_agent: Conductor,
    to_agent: Conductor,
    message: str,
    message_type: MessageType = MessageType.REQUEST
) -> str
```

Send a message between agents.

#### broadcast

```python
async def broadcast(
    self,
    message: str,
    agents: list[Conductor] | None = None
) -> list[str]
```

Send a message to multiple agents.

#### delegate

```python
async def delegate(
    self,
    from_agent: Conductor,
    to_agent: Conductor,
    task: str
) -> str
```

Delegate a task from one agent to another.

#### orchestrate

```python
async def orchestrate(
    self,
    task: str,
    lead: Conductor,
    participants: list[Conductor] | None = None
) -> str
```

Coordinate a multi-agent task.

---

## reasona.Workflow

Declarative pipelines.

### Constructor

```python
Workflow(name: str)
```

### Methods

#### add_stage

```python
def add_stage(
    self,
    name: str,
    agent: Conductor,
    prompt_template: str,
    description: str | None = None,
    condition: Callable[[dict], bool] | None = None,
    transform: Callable[[str], str] | None = None,
    retries: int = 0,
    timeout: float | None = None
) -> Self
```

Add a stage to the workflow.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Stage identifier |
| `agent` | `Conductor` | Agent to execute the stage |
| `prompt_template` | `str` | Template with `{variable}` placeholders |
| `condition` | `Callable` | Function to determine if stage runs |
| `transform` | `Callable` | Post-process stage output |
| `retries` | `int` | Retry attempts on failure |
| `timeout` | `float` | Maximum execution time in seconds |

#### remove_stage

```python
def remove_stage(self, name: str) -> Self
```

Remove a stage from the workflow.

#### run

```python
async def run(self, **kwargs) -> dict[str, str]
```

Execute the workflow with the given inputs.

**Returns:** Dictionary mapping stage names to their outputs.

#### visualize

```python
def visualize(self) -> str
```

Get a text visualization of the workflow.

#### reset

```python
def reset(self) -> None
```

Clear execution history.

---

## reasona.tools.NeuralTool

Base class for tools.

### Class Attributes

```python
class MyTool(NeuralTool):
    name: str = "my_tool"
    description: str = "Tool description"
```

### Methods

#### execute

```python
async def execute(self, **kwargs) -> Any
```

Execute the tool. Must be implemented by subclasses.

#### get_schema

```python
def get_schema(self) -> dict
```

Get the JSON schema for the tool.

---

## reasona.tools.tool

Decorator for creating tools from functions.

```python
@tool(name: str | None = None, description: str | None = None)
def my_tool(arg: str) -> str:
    ...
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Tool name (defaults to function name) |
| `description` | `str` | Tool description (defaults to docstring) |

---

## reasona.tools.ToolRegistry

Tool discovery and management.

### Methods

#### register

```python
def register(self, tool: NeuralTool) -> NeuralTool
```

Register a tool. Can be used as a decorator.

#### get_tools

```python
def get_tools(self) -> list[NeuralTool]
```

Get all registered tools.

#### get_tool

```python
def get_tool(self, name: str) -> NeuralTool | None
```

Get a tool by name.

#### search

```python
def search(self, query: str) -> list[NeuralTool]
```

Search tools by name or description.

---

## reasona.mcp.HyperMCP

MCP server implementation.

### Constructor

```python
HyperMCP(
    name: str,
    version: str = "1.0.0",
    description: str | None = None
)
```

### Decorators

#### tool

```python
@mcp.tool(description: str, requires_auth: bool = False)
async def my_tool(**kwargs) -> Any:
    ...
```

#### resource

```python
@mcp.resource(uri: str, description: str | None = None)
async def my_resource(**kwargs) -> Any:
    ...
```

#### prompt

```python
@mcp.prompt(name: str, description: str | None = None)
async def my_prompt(**kwargs) -> str:
    ...
```

### Methods

#### serve

```python
def serve(self, host: str = "0.0.0.0", port: int = 9000) -> None
```

Start the MCP server.

---

## reasona.server.create_app

Create a FastAPI app for an agent.

```python
from reasona.server import create_app

app = create_app(agent: Conductor) -> FastAPI
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/v1/agent` | Agent info |
| GET | `/.well-known/agent-card.json` | Discovery card |
| POST | `/v1/think` | Process message |
| POST | `/v1/chat` | Alias for think |
| POST | `/v1/reset` | Reset conversation |
| GET | `/v1/tools` | List tools |

---

## reasona.server.ConductorRouter

Mount multiple agents.

### Constructor

```python
ConductorRouter()
```

### Methods

#### add_agent

```python
def add_agent(self, agent: Conductor) -> Self
```

#### remove_agent

```python
def remove_agent(self, name: str) -> Self
```

#### build

```python
def build(self) -> FastAPI
```

---

## reasona.core.Message

Conversation message.

```python
Message(
    role: Role,
    content: str,
    tool_calls: list[dict] | None = None,
    metadata: dict | None = None
)
```

## reasona.core.Role

Message roles.

```python
class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
```

## reasona.core.Context

Execution context.

```python
Context(
    user: UserContext | None = None,
    session: SessionContext | None = None,
    runtime: RuntimeContext | None = None,
    metadata: dict | None = None
)
```

## reasona.core.ReasonaConfig

Configuration management.

### Methods

#### get_provider_config

```python
def get_provider_config(self, provider: str) -> dict
```

#### set_api_key

```python
def set_api_key(self, provider: str, key: str) -> None
```

#### from_file

```python
@classmethod
def from_file(cls, path: str) -> "ReasonaConfig"
```

#### from_dict

```python
@classmethod
def from_dict(cls, data: dict) -> "ReasonaConfig"
```
