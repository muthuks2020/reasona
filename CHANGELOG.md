# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-01

### Added

- **Core Framework**
  - `Conductor` - Main agent builder with fluent API
  - `Synapse` - Agent-to-agent communication via Synaptic Protocol
  - `Workflow` - Declarative multi-agent pipelines
  - `Message` and `Context` - Structured conversation handling
  - `ReasonaConfig` - Centralized configuration management

- **LLM Provider Integrations**
  - OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo)
  - Anthropic (Claude 3.5, Claude 3)
  - Google (Gemini Pro, Gemini Flash)
  - Ollama (local models)
  - Support for custom providers

- **Tools System**
  - `NeuralTool` base class with automatic schema generation
  - `@tool` decorator for function-to-tool conversion
  - `ToolRegistry` for tool discovery and management
  - Built-in tools: Calculator, WebSearch, HttpRequest, FileReader, FileWriter, ShellCommand, DateTime, JsonParser

- **HyperMCP Server**
  - Native ASGI MCP server implementation
  - Decorators for tools, resources, and prompts
  - JSON-RPC 2.0 endpoint
  - Authentication support via context variables

- **REST API Server**
  - FastAPI-based server with streaming support
  - Agent discovery via `/.well-known/agent-card.json`
  - Multi-agent routing with `ConductorRouter`
  - Server-Sent Events for streaming responses

- **CLI**
  - `reasona run` - Run agents from markdown files
  - `reasona serve` - Start REST API server
  - `reasona chat` - Interactive chat mode
  - `reasona init` - Initialize new agent projects
  - `reasona tools` - Manage and list tools

- **Documentation**
  - Comprehensive README with examples
  - API documentation
  - Architecture overview
  - Getting started guide

### Security

- Safe math expression evaluation in Calculator tool
- Configurable shell command execution
- API key management via environment variables

---

[Unreleased]: https://github.com/reasona/reasona/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/reasona/reasona/releases/tag/v0.1.0
