"""
Reasona CLI - Command-line interface for the Reasona framework.

Usage:
    reasona init [name]           - Initialize a new agent project
    reasona run [file]            - Run an agent from a file
    reasona serve [file] [--port] - Serve an agent via HTTP
    reasona chat [model]          - Interactive chat with a model
    reasona tools list            - List available tools
    reasona mcp serve [file]      - Start an MCP server
    reasona version               - Show version info
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from reasona import __version__
from reasona.core import Conductor, Synapse, Workflow
from reasona.core.config import ReasonaConfig
from reasona.tools import ToolRegistry, Calculator, DateTime, JsonParser

# Initialize CLI app and console
app = typer.Typer(
    name="reasona",
    help="Reasona - AI Agent Orchestration Framework",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

# Sub-command groups
tools_app = typer.Typer(help="Tool management commands")
mcp_app = typer.Typer(help="MCP server commands")
app.add_typer(tools_app, name="tools")
app.add_typer(mcp_app, name="mcp")


def print_banner():
    """Print the Reasona ASCII banner."""
    banner = """
╦═╗┌─┐┌─┐┌─┐┌─┐┌┐┌┌─┐
╠╦╝├┤ ├─┤└─┐│ ││││├─┤
╩╚═└─┘┴ ┴└─┘└─┘┘└┘┴ ┴
    """
    console.print(Panel(banner, title="[bold blue]Reasona[/bold blue]", subtitle=f"v{__version__}"))


@app.command()
def version():
    """Show version information."""
    print_banner()
    console.print(f"\n[bold]Version:[/bold] {__version__}")
    console.print(f"[bold]Python:[/bold] {sys.version.split()[0]}")
    console.print(f"[bold]Platform:[/bold] {sys.platform}")


@app.command()
def init(
    name: str = typer.Argument("my-agent", help="Name of the agent project"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template (basic, advanced, mcp)"),
):
    """Initialize a new Reasona agent project."""
    project_dir = Path(name)
    
    if project_dir.exists():
        console.print(f"[red]Error:[/red] Directory '{name}' already exists")
        raise typer.Exit(1)
    
    # Create project structure
    project_dir.mkdir(parents=True)
    (project_dir / "agents").mkdir()
    (project_dir / "tools").mkdir()
    (project_dir / "workflows").mkdir()
    
    # Create main agent file
    agent_content = f'''"""
{name} - A Reasona Agent

This agent was created using the Reasona CLI.
"""

from reasona import Conductor
from reasona.tools import Calculator, DateTime

# Create the agent
agent = Conductor(
    name="{name}",
    model="openai/gpt-4o",  # Change to your preferred model
    instructions="""You are a helpful AI assistant created with Reasona.
You can perform calculations and tell the current time.""",
    tools=[Calculator(), DateTime()],
)

if __name__ == "__main__":
    # Run interactively or serve via HTTP
    import sys
    if "--serve" in sys.argv:
        agent.serve(port=8000)
    else:
        # Interactive mode
        print(f"Agent '{{agent.name}}' ready. Type 'exit' to quit.\\n")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ("exit", "quit"):
                    break
                response = agent.think(user_input)
                print(f"\\nAgent: {{response}}\\n")
            except KeyboardInterrupt:
                break
'''
    
    (project_dir / "agent.py").write_text(agent_content)
    
    # Create config file
    config_content = '''# Reasona Configuration
# See https://github.com/reasona/reasona for documentation

[reasona]
default_model = "openai/gpt-4o"
log_level = "INFO"

[providers.openai]
# api_key = "sk-..."  # Or set OPENAI_API_KEY env var

[providers.anthropic]
# api_key = "sk-ant-..."  # Or set ANTHROPIC_API_KEY env var

[server]
host = "0.0.0.0"
port = 8000
cors_origins = ["*"]
'''
    (project_dir / "reasona.toml").write_text(config_content)
    
    # Create .env template
    env_content = '''# Environment Variables for Reasona
# Copy this to .env and fill in your API keys

OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
'''
    (project_dir / ".env.example").write_text(env_content)
    
    # Create .gitignore
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# Reasona
.reasona/
logs/
'''
    (project_dir / ".gitignore").write_text(gitignore_content)
    
    # Create README
    readme_content = f'''# {name}

A Reasona-powered AI agent.

## Setup

1. Install dependencies:
   ```bash
   pip install reasona
   ```

2. Configure your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run the agent:
   ```bash
   python agent.py
   ```

4. Or serve via HTTP:
   ```bash
   python agent.py --serve
   ```

## Documentation

See the [Reasona documentation](https://github.com/reasona/reasona) for more information.
'''
    (project_dir / "README.md").write_text(readme_content)
    
    console.print(f"\n[green]✓[/green] Created project '{name}' with template '{template}'")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  cd {name}")
    console.print(f"  cp .env.example .env  # Add your API keys")
    console.print(f"  python agent.py")


@app.command()
def run(
    file: Path = typer.Argument(..., help="Path to agent file (.py or .md)"),
    input_text: Optional[str] = typer.Option(None, "--input", "-i", help="Input to send to the agent"),
):
    """Run an agent from a file."""
    if not file.exists():
        console.print(f"[red]Error:[/red] File '{file}' not found")
        raise typer.Exit(1)
    
    # Load agent based on file type
    if file.suffix == ".py":
        # Execute Python file and get agent
        import importlib.util
        spec = importlib.util.spec_from_file_location("agent_module", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find Conductor instance
        agent = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, Conductor):
                agent = obj
                break
        
        if agent is None:
            console.print("[red]Error:[/red] No Conductor agent found in file")
            raise typer.Exit(1)
    
    elif file.suffix == ".md":
        # Load from markdown definition
        agent = Conductor.from_file(str(file))
    
    else:
        console.print(f"[red]Error:[/red] Unsupported file type '{file.suffix}'")
        raise typer.Exit(1)
    
    console.print(f"[green]✓[/green] Loaded agent: {agent.name}")
    
    if input_text:
        # Single input mode
        response = agent.think(input_text)
        console.print(f"\n[bold]Response:[/bold]\n{response}")
    else:
        # Interactive mode
        console.print("\nEntering interactive mode. Type 'exit' to quit.\n")
        while True:
            try:
                user_input = Prompt.ask("[bold blue]You[/bold blue]")
                if user_input.lower() in ("exit", "quit"):
                    break
                response = agent.think(user_input)
                console.print(f"\n[bold green]{agent.name}[/bold green]: {response}\n")
            except KeyboardInterrupt:
                break


@app.command()
def serve(
    file: Path = typer.Argument(..., help="Path to agent file"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve on"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Serve an agent via HTTP API."""
    if not file.exists():
        console.print(f"[red]Error:[/red] File '{file}' not found")
        raise typer.Exit(1)
    
    # Load agent
    if file.suffix == ".py":
        import importlib.util
        spec = importlib.util.spec_from_file_location("agent_module", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        agent = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, Conductor):
                agent = obj
                break
        
        if agent is None:
            console.print("[red]Error:[/red] No Conductor agent found in file")
            raise typer.Exit(1)
    elif file.suffix == ".md":
        agent = Conductor.from_file(str(file))
    else:
        console.print(f"[red]Error:[/red] Unsupported file type")
        raise typer.Exit(1)
    
    console.print(f"[green]✓[/green] Starting server for agent: {agent.name}")
    console.print(f"[bold]URL:[/bold] http://{host}:{port}")
    console.print(f"[bold]Docs:[/bold] http://{host}:{port}/docs")
    console.print(f"[bold]Agent Card:[/bold] http://{host}:{port}/.well-known/agent-card.json\n")
    
    agent.serve(host=host, port=port)


@app.command()
def chat(
    model: str = typer.Argument("openai/gpt-4o", help="Model to use (provider/model)"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Temperature"),
):
    """Start an interactive chat session with a model."""
    print_banner()
    
    # Create a simple agent
    agent = Conductor(
        name="chat",
        model=model,
        instructions=system or "You are a helpful AI assistant.",
        temperature=temperature,
    )
    
    console.print(f"\n[bold]Model:[/bold] {model}")
    console.print(f"[bold]Temperature:[/bold] {temperature}")
    console.print("\nType 'exit' to quit, '/reset' to clear history, '/help' for commands.\n")
    
    while True:
        try:
            user_input = Prompt.ask("[bold blue]You[/bold blue]")
            
            if user_input.lower() in ("exit", "quit"):
                break
            elif user_input == "/reset":
                agent.reset()
                console.print("[yellow]Conversation reset.[/yellow]\n")
                continue
            elif user_input == "/help":
                console.print("""
[bold]Commands:[/bold]
  /reset  - Clear conversation history
  /help   - Show this help
  exit    - Exit chat
""")
                continue
            elif not user_input.strip():
                continue
            
            # Get response with streaming
            console.print(f"\n[bold green]Assistant[/bold green]: ", end="")
            
            async def stream_response():
                full_response = ""
                async for chunk in agent.stream(user_input):
                    console.print(chunk, end="")
                    full_response += chunk
                console.print("\n")
            
            asyncio.run(stream_response())
            
        except KeyboardInterrupt:
            console.print("\n")
            break
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}\n")


# Tools subcommands
@tools_app.command("list")
def tools_list():
    """List all available built-in tools."""
    from reasona.tools.builtin import (
        Calculator, WebSearch, HttpRequest, FileReader, 
        FileWriter, ShellCommand, DateTime, JsonParser
    )
    
    table = Table(title="Available Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Parameters", style="yellow")
    
    tools = [
        Calculator(),
        WebSearch(),
        HttpRequest(),
        FileReader(),
        FileWriter(),
        ShellCommand(),
        DateTime(),
        JsonParser(),
    ]
    
    for tool in tools:
        schema = tool.get_schema()
        params = ", ".join(schema.get("parameters", {}).get("properties", {}).keys())
        table.add_row(tool.name, tool.description, params or "-")
    
    console.print(table)


@tools_app.command("info")
def tools_info(name: str = typer.Argument(..., help="Tool name")):
    """Show detailed information about a tool."""
    from reasona.tools.builtin import (
        Calculator, WebSearch, HttpRequest, FileReader,
        FileWriter, ShellCommand, DateTime, JsonParser
    )
    
    tools_map = {
        "calculator": Calculator,
        "web_search": WebSearch,
        "http_request": HttpRequest,
        "file_reader": FileReader,
        "file_writer": FileWriter,
        "shell_command": ShellCommand,
        "datetime": DateTime,
        "json_parser": JsonParser,
    }
    
    tool_class = tools_map.get(name.lower())
    if not tool_class:
        console.print(f"[red]Error:[/red] Tool '{name}' not found")
        raise typer.Exit(1)
    
    tool = tool_class()
    schema = tool.get_schema()
    
    console.print(Panel(f"[bold]{tool.name}[/bold]", subtitle=tool.description))
    console.print("\n[bold]Schema:[/bold]")
    console.print(Syntax(json.dumps(schema, indent=2), "json"))


# MCP subcommands
@mcp_app.command("serve")
def mcp_serve(
    file: Path = typer.Argument(..., help="Path to MCP server file"),
    port: int = typer.Option(9000, "--port", "-p", help="Port to serve on"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
):
    """Start an MCP server from a file."""
    if not file.exists():
        console.print(f"[red]Error:[/red] File '{file}' not found")
        raise typer.Exit(1)
    
    # Import and run the MCP server
    import importlib.util
    from reasona.mcp import HyperMCP
    
    spec = importlib.util.spec_from_file_location("mcp_module", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find HyperMCP instance
    mcp = None
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, HyperMCP):
            mcp = obj
            break
    
    if mcp is None:
        console.print("[red]Error:[/red] No HyperMCP server found in file")
        raise typer.Exit(1)
    
    console.print(f"[green]✓[/green] Starting MCP server: {mcp.name}")
    console.print(f"[bold]URL:[/bold] http://{host}:{port}")
    console.print(f"[bold]Tools:[/bold] http://{host}:{port}/tools")
    console.print(f"[bold]Resources:[/bold] http://{host}:{port}/resources\n")
    
    mcp.serve(host=host, port=port)


@mcp_app.command("init")
def mcp_init(
    name: str = typer.Argument("my-mcp-server", help="Name of the MCP server"),
):
    """Initialize a new MCP server project."""
    file_path = Path(f"{name}.py")
    
    if file_path.exists():
        console.print(f"[red]Error:[/red] File '{file_path}' already exists")
        raise typer.Exit(1)
    
    content = f'''"""
{name} - A HyperMCP Server

Created with: reasona mcp init {name}
"""

from reasona.mcp import HyperMCP, get_token

# Create the MCP server
mcp = HyperMCP(
    name="{name}",
    version="1.0.0",
    description="A custom MCP server built with Reasona",
)


# Define tools
@mcp.tool(description="Add two numbers together")
async def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool(description="Get a greeting message")
async def greet(name: str) -> str:
    """Generate a greeting."""
    return f"Hello, {{name}}! Welcome to {{mcp.name}}."


# Define resources
@mcp.resource("config://settings", description="Server configuration")
async def get_settings() -> dict:
    """Return server settings."""
    return {{
        "name": mcp.name,
        "version": mcp.version,
        "features": ["tools", "resources", "prompts"],
    }}


# Define prompts
@mcp.prompt("assistant", description="A helpful assistant prompt")
async def assistant_prompt(task: str) -> str:
    """Generate an assistant prompt."""
    return f"""You are a helpful assistant.

Your task: {{task}}

Please complete this task to the best of your ability."""


if __name__ == "__main__":
    mcp.serve(port=9000)
'''
    
    file_path.write_text(content)
    
    console.print(f"[green]✓[/green] Created MCP server: {file_path}")
    console.print(f"\n[bold]Run with:[/bold] reasona mcp serve {file_path}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
