# Reasona Documentation

Welcome to the Reasona documentation. Reasona is a powerful framework for building, orchestrating, and deploying AI agents.

## Quick Links

- [Getting Started](getting-started.md) - Install and create your first agent
- [Core Concepts](core-concepts.md) - Understand the architecture
- [API Reference](api-reference.md) - Detailed API documentation
- [Examples](../examples/README.md) - Working code examples

## Overview

Reasona provides a complete toolkit for AI agent development:

### Core Components

| Component | Description |
|-----------|-------------|
| **Conductor** | Main agent builder with fluent API |
| **Synapse** | Agent-to-agent communication protocol |
| **Workflow** | Declarative multi-agent pipelines |
| **NeuralTool** | Tool creation and management |
| **HyperMCP** | MCP server implementation |

### Supported Providers

| Provider | Models |
|----------|--------|
| OpenAI | GPT-4, GPT-4o, GPT-3.5-turbo |
| Anthropic | Claude 3.5, Claude 3 |
| Google | Gemini Pro, Gemini Flash |
| Ollama | Llama, Mistral, CodeLlama |
| Azure | OpenAI models on Azure |
| Groq | Fast inference models |

## Installation

```bash
pip install reasona
```

With all optional dependencies:

```bash
pip install "reasona[all]"
```

## Quick Start

```python
from reasona import Conductor

agent = Conductor(
    name="assistant",
    model="openai/gpt-4o",
    instructions="You are a helpful assistant."
)

response = agent.think("Hello, how can you help me?")
print(response)
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Your Application                │
├─────────────────────────────────────────────────┤
│    Conductor ←──Synapse──→ Conductor            │
│        │                       │                 │
│   NeuralTools              NeuralTools          │
├─────────────────────────────────────────────────┤
│              LLM Providers                       │
│   (OpenAI, Anthropic, Google, Ollama, ...)     │
└─────────────────────────────────────────────────┘
```

## License

Reasona is released under the MIT License. See [LICENSE](../LICENSE) for details.
