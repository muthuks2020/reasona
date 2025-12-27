# Reasona Examples

This directory contains example scripts demonstrating various features of the Reasona framework.

## Prerequisites

Before running the examples, install Reasona:

```bash
pip install reasona
# or for development
pip install -e ".[dev]"
```

Set up your API keys:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
# Optional
export GOOGLE_API_KEY="..."
```

## Examples

### 01. Basic Agent (`01_basic_agent.py`)

Learn the fundamentals of creating and using agents.

```bash
python examples/01_basic_agent.py
```

Topics covered:
- Creating a Conductor agent
- Synchronous and asynchronous operations
- Streaming responses
- Using built-in tools

### 02. Custom Tools (`02_custom_tools.py`)

Create your own tools for agents to use.

```bash
python examples/02_custom_tools.py
```

Topics covered:
- Class-based tools (NeuralTool)
- Decorator-based tools (@tool)
- Tool registry
- Type hints and schema generation

### 03. Multi-Agent Collaboration (`03_multi_agent.py`)

Connect multiple agents for complex tasks.

```bash
python examples/03_multi_agent.py
```

Topics covered:
- Creating specialized agents
- Synapse communication protocol
- Agent delegation
- Orchestrated collaboration
- Broadcasting messages

### 04. Workflow Pipelines (`04_workflow.py`)

Build declarative multi-stage workflows.

```bash
python examples/04_workflow.py
```

Topics covered:
- Workflow creation
- Stage definitions
- Conditional execution
- Retry logic and timeouts
- Workflow visualization

### 05. REST API Server (`05_rest_api.py`)

Serve agents via HTTP APIs.

```bash
# Single agent
python examples/05_rest_api.py single

# Multiple agents
python examples/05_rest_api.py multi

# With streaming
python examples/05_rest_api.py stream
```

Topics covered:
- FastAPI integration
- Single and multi-agent servers
- Streaming responses
- Agent discovery cards

### 06. HyperMCP Server (`06_hypermcp.py`)

Create MCP servers for Claude Desktop integration.

```bash
python examples/06_hypermcp.py
```

Topics covered:
- MCP tool definitions
- Resources and prompts
- Authentication
- JSON-RPC endpoint
- Claude Desktop configuration

### 07. Markdown Agents (`07_markdown_agents.py`)

Define agents declaratively using markdown files.

```bash
python examples/07_markdown_agents.py
```

Topics covered:
- YAML frontmatter configuration
- Markdown-based instructions
- Agent libraries
- Discovery cards

## Running All Examples

```bash
# Run each example
for f in examples/*.py; do
    echo "Running $f..."
    python "$f"
    echo
done
```

## Getting Help

- [Documentation](https://reasona.dev/docs)
- [GitHub Issues](https://github.com/reasona-ai/reasona/issues)
- [API Reference](https://reasona.dev/api)
