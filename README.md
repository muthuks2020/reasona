<p align="center">
  <img src="assets/reasona-logo.png" alt="Reasona" width="400"/>
</p>

<h1 align="center">Reasona</h1>

<p align="center">
  <strong>A Production-Grade Control Plane for AI Agent Orchestration</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/reasona/"><img src="https://img.shields.io/pypi/v/reasona.svg?color=brightgreen&label=PyPI&style=flat" alt="PyPI version"></a>
  <a href="https://github.com/reasona-ai/reasona/actions"><img src="https://github.com/reasona-ai/reasona/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat" alt="License: MIT"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="https://docs.reasona.dev">Documentation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="https://github.com/reasona-ai/reasona/tree/main/examples">Examples</a>
</p>

---

## What is Reasona?

Reasona is an open-source framework for building, deploying, and managing production-ready AI agents. It provides a unified control plane that handles agent orchestration, secure inter-agent communication, tool management, and deployment—all with a simple, Pythonic API.

**Reasona** is how you *build* intelligent agents. **Reasona Cloud** (coming soon) is how you *run* them at scale.

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| 🧠 **Conductor Pattern** | Intuitive agent creation with fluent builder API | ✅ |
| 🔗 **Synaptic Protocol** | Secure agent-to-agent communication (S2S) | ✅ |
| 🛠️ **HyperMCP** | Full ASGI-native MCP server with FastAPI integration | ✅ |
| 🔍 **Neural Tools** | Smart tool discovery and context-aware execution | ✅ |
| 🔐 **Vault Security** | Built-in OAuth 2.0, JWT, and fine-grained permissions | ✅ |
| 🚀 **One-Click Deploy** | Deploy to cloud with `reasona deploy` | 🔜 |
| 📊 **Observability** | Built-in tracing, metrics, and logging | ✅ |

## 🚀 Quick Start

### Installation

```bash
pip install reasona
```

### Create Your First Agent

```python
from reasona import Conductor
from reasona.tools import WebSearch, Calculator

# Create an intelligent agent in 5 lines
agent = Conductor(
    name="research-assistant",
    model="openai/gpt-4o",  # Works with any provider
    tools=[WebSearch(), Calculator()],
    instructions="You are a helpful research assistant."
)

# Run the agent
response = agent.think("What's the population of Tokyo multiplied by 2?")
print(response)
```

### Serve as an API

```python
# Add one line to expose your agent as a REST API
agent.serve(port=8000)
```

```bash
# Query your agent
curl -X POST http://localhost:8000/v1/think \
  -H "Content-Type: application/json" \
  -d '{"input": "Explain quantum computing"}'
```

## 🏗️ Architecture

Reasona uses a unique **Conductor Pattern** that separates concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     REASONA CONTROL PLANE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Conductor  │◄──►│  Synapse    │◄──►│  Conductor  │     │
│  │  (Agent A)  │    │  (S2S Bus)  │    │  (Agent B)  │     │
│  └──────┬──────┘    └─────────────┘    └──────┬──────┘     │
│         │                                      │            │
│         ▼                                      ▼            │
│  ┌─────────────┐                        ┌─────────────┐    │
│  │   Neural    │                        │   Neural    │    │
│  │   Tools     │                        │   Tools     │    │
│  └─────────────┘                        └─────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  HyperMCP Server │ Vault Security │ Trace Collector        │
└─────────────────────────────────────────────────────────────┘
```

## 📚 Core Concepts

### Conductor (Agent Builder)

The `Conductor` is your primary interface for creating AI agents:

```python
from reasona import Conductor

agent = Conductor(
    name="analyst",
    model="anthropic/claude-3-5-sonnet",
    instructions="Analyze data and provide insights.",
    temperature=0.3,
    max_tokens=4096
)
```

### Neural Tools

Tools are first-class citizens with automatic schema generation:

```python
from reasona.tools import NeuralTool

class StockPrice(NeuralTool):
    """Get real-time stock prices."""
    
    def execute(self, symbol: str) -> dict:
        # Your implementation
        return {"symbol": symbol, "price": 150.25}

agent = Conductor(
    name="trader",
    model="openai/gpt-4o",
    tools=[StockPrice()]
)
```

### Synaptic Protocol (Agent-to-Agent)

Enable seamless communication between agents:

```python
from reasona import Conductor, Synapse

# Create specialized agents
researcher = Conductor(name="researcher", model="openai/gpt-4o")
writer = Conductor(name="writer", model="anthropic/claude-3-5-sonnet")

# Connect them via Synapse
synapse = Synapse()
synapse.connect(researcher, writer)

# Agents can now collaborate
result = synapse.orchestrate(
    task="Research AI trends and write a blog post",
    lead=researcher
)
```

### HyperMCP Server

Build MCP-compatible servers with native FastAPI integration:

```python
from reasona.mcp import HyperMCP

mcp = HyperMCP(name="my-tools", version="1.0.0")

@mcp.tool(description="Get weather for a location")
async def get_weather(location: str, units: str = "celsius") -> dict:
    return {"location": location, "temp": 22, "units": units}

@mcp.resource("config://app")
async def get_config() -> dict:
    return {"version": "1.0.0", "environment": "production"}

# Run standalone or integrate with FastAPI
mcp.serve(port=9000)
```

## 🔧 Provider Support

Reasona supports all major LLM providers with a unified interface:

| Provider | Models | Status |
|----------|--------|--------|
| OpenAI | GPT-4o, GPT-4, GPT-3.5 | ✅ |
| Anthropic | Claude 3.5, Claude 3 | ✅ |
| Google | Gemini 2.0, Gemini 1.5 | ✅ |
| Mistral | Mistral Large, Medium | ✅ |
| Groq | Llama 3, Mixtral | ✅ |
| Ollama | Any local model | ✅ |
| Azure OpenAI | All Azure models | ✅ |

```python
# Unified model syntax: provider/model-name
agent = Conductor(model="anthropic/claude-3-5-sonnet")
agent = Conductor(model="openai/gpt-4o")
agent = Conductor(model="google/gemini-2.0-flash")
agent = Conductor(model="ollama/llama3.2")
```

## 📖 Examples

### Multi-Agent Workflow

```python
from reasona import Conductor, Synapse, Workflow

# Define specialized agents
planner = Conductor(name="planner", model="openai/gpt-4o")
executor = Conductor(name="executor", model="anthropic/claude-3-5-sonnet")
reviewer = Conductor(name="reviewer", model="google/gemini-2.0-flash")

# Create a workflow
workflow = Workflow(name="content-pipeline")
workflow.add_stage("plan", planner)
workflow.add_stage("execute", executor)
workflow.add_stage("review", reviewer)

# Run the pipeline
result = await workflow.run("Create a marketing campaign for a new product")
```

### Agent from Markdown

```markdown
---
name: customer-support
model: openai/gpt-4o-mini
tools: [knowledge_base, ticket_system]
temperature: 0.2
---

You are a friendly customer support agent for TechCorp.
Always be helpful and professional.
```

```python
agent = Conductor.from_markdown("agent.md")
```

### Streaming Responses

```python
async for chunk in agent.stream("Tell me a story about AI"):
    print(chunk, end="", flush=True)
```

## 🔐 Security

Reasona includes enterprise-grade security features:

```python
from reasona.security import Vault

vault = Vault()

# Configure OAuth for integrations
vault.configure_oauth(
    provider="google",
    client_id="...",
    client_secret="...",
    scopes=["email", "calendar"]
)

# Use with agents
agent = Conductor(
    name="assistant",
    model="openai/gpt-4o",
    vault=vault
)
```

## 🚀 Deployment

### CLI Deploy (Coming Soon)

```bash
# Deploy to Reasona Cloud
reasona deploy

# Deploy to custom infrastructure
reasona deploy --target kubernetes --config k8s.yaml
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install reasona
CMD ["reasona", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Observability

Built-in tracing and metrics:

```python
from reasona import Conductor
from reasona.observability import Tracer

tracer = Tracer(endpoint="http://jaeger:4317")

agent = Conductor(
    name="traced-agent",
    model="openai/gpt-4o",
    tracer=tracer
)

# All operations are automatically traced
response = agent.think("Hello!")
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Clone the repository
git clone https://github.com/reasona-ai/reasona.git
cd reasona

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests
```

## 📄 License

Reasona is released under the [MIT License](LICENSE). You are free to use, modify, and distribute this software for any purpose.

## 🙏 Acknowledgments

Reasona builds on the shoulders of giants. Special thanks to:

- The [Model Context Protocol](https://modelcontextprotocol.io/) specification
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Pydantic](https://docs.pydantic.dev/) for data validation
- The open-source AI community

---

<p align="center">
  Made with ❤️ by the Reasona community
</p>

<p align="center">
  <a href="https://github.com/reasona-ai/reasona/stargazers">⭐ Star us on GitHub</a>
</p>
