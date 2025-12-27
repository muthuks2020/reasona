"""
Tests for HyperMCP server.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from reasona.mcp.hypermcp import HyperMCP, get_token


class TestHyperMCP:
    """Tests for the HyperMCP server."""
    
    @pytest.fixture
    def mcp(self):
        """Create a test MCP server."""
        server = HyperMCP(
            name="test-mcp",
            version="1.0.0",
            description="Test MCP server"
        )
        
        # Add test tool
        @server.tool(description="Add two numbers")
        async def add(a: float, b: float) -> float:
            return a + b
        
        # Add test resource
        @server.resource("test://data", description="Test data")
        async def test_data() -> dict:
            return {"message": "Hello from resource"}
        
        # Add test prompt
        @server.prompt("greeting", description="Greeting prompt")
        async def greeting(name: str) -> str:
            return f"Hello, {name}!"
        
        return server
    
    @pytest.fixture
    def client(self, mcp):
        """Create test client."""
        app = mcp._build_app()
        return TestClient(app)
    
    def test_mcp_creation(self):
        """Test creating an MCP server."""
        mcp = HyperMCP(name="test", version="1.0.0")
        assert mcp.name == "test"
        assert mcp.version == "1.0.0"
    
    def test_server_info_endpoint(self, client):
        """Test server info endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "test-mcp"
        assert data["version"] == "1.0.0"
        assert "protocolVersion" in data
    
    def test_list_tools(self, client):
        """Test listing tools."""
        response = client.get("/tools")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        
        tool_names = [t["name"] for t in data["tools"]]
        assert "add" in tool_names
    
    def test_call_tool(self, client):
        """Test calling a tool."""
        response = client.post(
            "/tools/add",
            json={"arguments": {"a": 5, "b": 3}}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["result"] == 8
    
    def test_call_nonexistent_tool(self, client):
        """Test calling non-existent tool."""
        response = client.post(
            "/tools/nonexistent",
            json={"arguments": {}}
        )
        assert response.status_code == 404
    
    def test_list_resources(self, client):
        """Test listing resources."""
        response = client.get("/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "resources" in data
        
        uris = [r["uri"] for r in data["resources"]]
        assert "test://data" in uris
    
    def test_read_resource(self, client):
        """Test reading a resource."""
        response = client.get("/resources/test%3A%2F%2Fdata")
        assert response.status_code == 200
        
        data = response.json()
        assert "contents" in data
    
    def test_list_prompts(self, client):
        """Test listing prompts."""
        response = client.get("/prompts")
        assert response.status_code == 200
        
        data = response.json()
        assert "prompts" in data
        
        names = [p["name"] for p in data["prompts"]]
        assert "greeting" in names
    
    def test_get_prompt(self, client):
        """Test getting a prompt."""
        response = client.post(
            "/prompts/greeting",
            json={"arguments": {"name": "Alice"}}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "Hello, Alice!" in str(data)


class TestJSONRPC:
    """Tests for JSON-RPC endpoint."""
    
    @pytest.fixture
    def mcp(self):
        """Create test MCP server."""
        server = HyperMCP(name="rpc-test", version="1.0.0")
        
        @server.tool(description="Multiply numbers")
        async def multiply(x: int, y: int) -> int:
            return x * y
        
        return server
    
    @pytest.fixture
    def client(self, mcp):
        """Create test client."""
        app = mcp._build_app()
        return TestClient(app)
    
    def test_rpc_initialize(self, client):
        """Test initialize method."""
        response = client.post("/rpc", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
    
    def test_rpc_tools_list(self, client):
        """Test tools/list method."""
        response = client.post("/rpc", json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]
    
    def test_rpc_tools_call(self, client):
        """Test tools/call method."""
        response = client.post("/rpc", json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "multiply",
                "arguments": {"x": 6, "y": 7}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["content"][0]["text"] == "42"
    
    def test_rpc_method_not_found(self, client):
        """Test method not found error."""
        response = client.post("/rpc", json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "unknown/method",
            "params": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601
    
    def test_rpc_invalid_request(self, client):
        """Test invalid request error."""
        response = client.post("/rpc", json={
            "jsonrpc": "2.0",
            "id": 5
            # Missing method
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestToolDecorator:
    """Tests for the @mcp.tool decorator."""
    
    def test_tool_registration(self):
        """Test tool registration via decorator."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.tool(description="Test tool")
        async def test_tool(param: str) -> str:
            return param
        
        assert "test_tool" in mcp._tools
    
    def test_tool_schema_extraction(self):
        """Test automatic schema extraction."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.tool(description="Calculate something")
        async def calculate(a: int, b: int, operation: str = "add") -> int:
            return a + b
        
        tool_def = mcp._tools["calculate"]
        schema = tool_def["inputSchema"]
        
        assert "a" in schema["properties"]
        assert "b" in schema["properties"]
        assert "operation" in schema["properties"]
        assert schema["properties"]["a"]["type"] == "integer"


class TestResourceDecorator:
    """Tests for the @mcp.resource decorator."""
    
    def test_resource_registration(self):
        """Test resource registration."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.resource("config://app", description="App config")
        async def app_config() -> dict:
            return {"setting": "value"}
        
        assert "config://app" in mcp._resources
    
    @pytest.mark.asyncio
    async def test_resource_execution(self):
        """Test resource function execution."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.resource("data://test", description="Test data")
        async def test_data() -> dict:
            return {"key": "value"}
        
        result = await mcp._resources["data://test"]["handler"]()
        assert result == {"key": "value"}


class TestPromptDecorator:
    """Tests for the @mcp.prompt decorator."""
    
    def test_prompt_registration(self):
        """Test prompt registration."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.prompt("assistant", description="Assistant prompt")
        async def assistant(task: str) -> str:
            return f"Do: {task}"
        
        assert "assistant" in mcp._prompts
    
    @pytest.mark.asyncio
    async def test_prompt_execution(self):
        """Test prompt function execution."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.prompt("greeter", description="Greeting")
        async def greeter(name: str) -> str:
            return f"Hello, {name}!"
        
        result = await mcp._prompts["greeter"]["handler"](name="World")
        assert result == "Hello, World!"


class TestAuthentication:
    """Tests for MCP authentication."""
    
    def test_get_token_context(self):
        """Test get_token context variable."""
        # Token should be None when not in request context
        token = get_token()
        assert token is None
    
    def test_bearer_token_extraction(self):
        """Test bearer token extraction from headers."""
        mcp = HyperMCP(name="test", version="1.0.0")
        
        @mcp.tool(description="Auth test")
        async def auth_test() -> str:
            token = get_token()
            return f"Token: {token}"
        
        app = mcp._build_app()
        client = TestClient(app)
        
        response = client.post(
            "/tools/auth_test",
            json={"arguments": {}},
            headers={"Authorization": "Bearer test-token-123"}
        )
        
        assert response.status_code == 200


class TestMCPIntegration:
    """Integration tests for MCP server."""
    
    def test_full_workflow(self):
        """Test complete MCP workflow."""
        mcp = HyperMCP(
            name="integration-test",
            version="2.0.0",
            description="Integration test server"
        )
        
        # Register multiple tools
        @mcp.tool(description="Add numbers")
        async def add(a: float, b: float) -> float:
            return a + b
        
        @mcp.tool(description="Subtract numbers")
        async def subtract(a: float, b: float) -> float:
            return a - b
        
        # Register resource
        @mcp.resource("stats://operations", description="Operation stats")
        async def operation_stats() -> dict:
            return {"add_count": 0, "subtract_count": 0}
        
        # Build and test
        app = mcp._build_app()
        client = TestClient(app)
        
        # Test server info
        info = client.get("/").json()
        assert info["name"] == "integration-test"
        
        # Test tools
        tools = client.get("/tools").json()["tools"]
        assert len(tools) == 2
        
        # Call add
        result = client.post("/tools/add", json={"arguments": {"a": 10, "b": 5}}).json()
        assert result["result"] == 15
        
        # Call subtract
        result = client.post("/tools/subtract", json={"arguments": {"a": 10, "b": 3}}).json()
        assert result["result"] == 7
        
        # Read resource
        resource = client.get("/resources/stats%3A%2F%2Foperations").json()
        assert "contents" in resource
