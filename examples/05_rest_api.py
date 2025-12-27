"""
REST API Server Example
=======================

This example demonstrates how to serve agents via REST API
with FastAPI integration.
"""

import uvicorn
from reasona import Conductor
from reasona.server import create_app, ConductorRouter
from reasona.tools import Calculator, DateTime, HttpRequest


def single_agent_server():
    """Run a single agent as a REST API server."""
    
    # Create an agent
    agent = Conductor(
        name="api-assistant",
        model="openai/gpt-4o",
        instructions="""You are a helpful API assistant. You can:
        - Answer questions
        - Perform calculations
        - Tell the time
        - Make HTTP requests""",
        tools=[Calculator(), DateTime(), HttpRequest()]
    )
    
    # Create FastAPI app
    app = create_app(agent)
    
    # The app now has these endpoints:
    # GET  /health                    - Health check
    # GET  /v1/agent                  - Agent info
    # GET  /.well-known/agent-card.json - Discovery card
    # POST /v1/think                  - Send message
    # POST /v1/chat                   - Alias for think
    # POST /v1/reset                  - Reset conversation
    # GET  /v1/tools                  - List tools
    
    print("Starting single agent server...")
    print("Endpoints:")
    print("  POST http://localhost:8000/v1/think")
    print("  GET  http://localhost:8000/.well-known/agent-card.json")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


def multi_agent_server():
    """Run multiple agents behind a single API."""
    
    # Create specialized agents
    math_agent = Conductor(
        name="math",
        model="openai/gpt-4o",
        instructions="You are a mathematics expert. Solve math problems step by step.",
        tools=[Calculator()]
    )
    
    writing_agent = Conductor(
        name="writer",
        model="anthropic/claude-3-5-sonnet",
        instructions="You are a creative writer. Help with writing tasks."
    )
    
    code_agent = Conductor(
        name="coder",
        model="openai/gpt-4o",
        instructions="You are a programming expert. Help with coding questions."
    )
    
    # Create router with multiple agents
    router = ConductorRouter()
    router.add_agent(math_agent)
    router.add_agent(writing_agent)
    router.add_agent(code_agent)
    
    # Build the combined app
    app = router.build()
    
    # The app now has these endpoints for each agent:
    # GET  /                         - List all agents
    # POST /{agent_name}/think       - Send message to specific agent
    # GET  /{agent_name}/card        - Get agent discovery card
    
    print("Starting multi-agent server...")
    print("Endpoints:")
    print("  GET  http://localhost:8000/")
    print("  POST http://localhost:8000/math/think")
    print("  POST http://localhost:8000/writer/think")
    print("  POST http://localhost:8000/coder/think")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


def streaming_server():
    """Server with streaming responses."""
    
    agent = Conductor(
        name="streaming-agent",
        model="openai/gpt-4o",
        instructions="You are a helpful assistant."
    )
    
    app = create_app(agent)
    
    # To use streaming, send request with stream=true:
    # curl -X POST http://localhost:8000/v1/think \
    #   -H "Content-Type: application/json" \
    #   -d '{"input": "Write a poem", "stream": true}'
    
    print("Starting streaming server...")
    print("Example streaming request:")
    print('  curl -X POST http://localhost:8000/v1/think \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"input": "Write a haiku", "stream": true}\'')
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"
    
    if mode == "single":
        single_agent_server()
    elif mode == "multi":
        multi_agent_server()
    elif mode == "stream":
        streaming_server()
    else:
        print("Usage: python 05_rest_api.py [single|multi|stream]")
