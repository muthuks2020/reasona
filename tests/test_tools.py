"""
Tests for Reasona tools.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, Mock

from reasona.tools.base import NeuralTool, tool, ToolRegistry
from reasona.tools.builtin import (
    Calculator, 
    WebSearch, 
    HttpRequest, 
    FileReader, 
    FileWriter,
    ShellCommand,
    DateTime,
    JsonParser
)


class TestNeuralTool:
    """Tests for the NeuralTool base class."""
    
    def test_custom_tool_creation(self):
        """Test creating a custom tool."""
        class MyTool(NeuralTool):
            name = "my_tool"
            description = "A custom tool"
            
            async def execute(self, param1: str, param2: int = 10) -> str:
                return f"{param1}-{param2}"
        
        tool = MyTool()
        assert tool.name == "my_tool"
        assert tool.description == "A custom tool"
    
    def test_tool_schema_generation(self):
        """Test automatic schema generation."""
        class TestTool(NeuralTool):
            name = "test_tool"
            description = "Test"
            
            async def execute(self, text: str, count: int, flag: bool = False) -> dict:
                return {}
        
        tool = TestTool()
        schema = tool.get_schema()
        
        assert schema["name"] == "test_tool"
        assert "parameters" in schema
        props = schema["parameters"]["properties"]
        
        assert "text" in props
        assert props["text"]["type"] == "string"
        assert "count" in props
        assert props["count"]["type"] == "integer"
        assert "flag" in props
        assert props["flag"]["type"] == "boolean"
    
    def test_required_parameters(self):
        """Test required parameters in schema."""
        class RequiredTool(NeuralTool):
            name = "req_tool"
            description = "Test"
            
            async def execute(self, required_param: str, optional_param: str = "default") -> str:
                return ""
        
        tool = RequiredTool()
        schema = tool.get_schema()
        
        assert "required_param" in schema["parameters"]["required"]
        assert "optional_param" not in schema["parameters"]["required"]


class TestToolDecorator:
    """Tests for the @tool decorator."""
    
    def test_sync_function_tool(self):
        """Test decorating a sync function."""
        @tool(name="add", description="Add numbers")
        def add_numbers(a: int, b: int) -> int:
            return a + b
        
        assert add_numbers.name == "add"
        assert add_numbers.description == "Add numbers"
    
    def test_async_function_tool(self):
        """Test decorating an async function."""
        @tool(name="async_tool", description="Async operation")
        async def async_operation(data: str) -> str:
            return data.upper()
        
        assert async_operation.name == "async_tool"
    
    @pytest.mark.asyncio
    async def test_decorated_tool_execution(self):
        """Test executing a decorated tool."""
        @tool(name="multiply", description="Multiply")
        async def multiply(x: float, y: float) -> float:
            return x * y
        
        result = await multiply.execute(x=3.0, y=4.0)
        assert result == 12.0


class TestToolRegistry:
    """Tests for the ToolRegistry."""
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        
        class CustomTool(NeuralTool):
            name = "custom"
            description = "Custom tool"
            async def execute(self) -> str:
                return "done"
        
        tool = CustomTool()
        registry.register(tool)
        
        assert "custom" in registry._tools
    
    def test_get_tool(self):
        """Test getting a tool from registry."""
        registry = ToolRegistry()
        tool = Calculator()
        registry.register(tool)
        
        retrieved = registry.get("calculator")
        assert retrieved is tool
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register(Calculator())
        registry.register(DateTime())
        
        tools = registry.list()
        assert len(tools) == 2
    
    def test_search_tools(self):
        """Test searching tools."""
        registry = ToolRegistry()
        registry.register(Calculator())
        registry.register(DateTime())
        registry.register(JsonParser())
        
        results = registry.search("time")
        assert any(t.name == "datetime" for t in results)


class TestCalculator:
    """Tests for the Calculator tool."""
    
    @pytest.mark.asyncio
    async def test_simple_addition(self):
        """Test simple addition."""
        calc = Calculator()
        result = await calc.execute(expression="2 + 3")
        assert result["result"] == 5
    
    @pytest.mark.asyncio
    async def test_complex_expression(self):
        """Test complex expression."""
        calc = Calculator()
        result = await calc.execute(expression="(10 + 5) * 2 - 3")
        assert result["result"] == 27
    
    @pytest.mark.asyncio
    async def test_float_operations(self):
        """Test float operations."""
        calc = Calculator()
        result = await calc.execute(expression="3.14 * 2")
        assert abs(result["result"] - 6.28) < 0.01
    
    @pytest.mark.asyncio
    async def test_power_operation(self):
        """Test power operation."""
        calc = Calculator()
        result = await calc.execute(expression="2 ** 10")
        assert result["result"] == 1024
    
    @pytest.mark.asyncio
    async def test_invalid_expression(self):
        """Test invalid expression handling."""
        calc = Calculator()
        result = await calc.execute(expression="invalid")
        assert "error" in result
    
    def test_calculator_schema(self):
        """Test Calculator schema."""
        calc = Calculator()
        schema = calc.get_schema()
        assert schema["name"] == "calculator"
        assert "expression" in schema["parameters"]["properties"]


class TestDateTime:
    """Tests for the DateTime tool."""
    
    @pytest.mark.asyncio
    async def test_current_time(self):
        """Test getting current time."""
        dt = DateTime()
        result = await dt.execute(action="now")
        assert "datetime" in result
        assert "timezone" in result
    
    @pytest.mark.asyncio
    async def test_format_date(self):
        """Test formatting date."""
        dt = DateTime()
        result = await dt.execute(
            action="format",
            date="2024-01-15",
            format="%B %d, %Y"
        )
        assert result["formatted"] == "January 15, 2024"
    
    @pytest.mark.asyncio
    async def test_add_days(self):
        """Test adding days."""
        dt = DateTime()
        result = await dt.execute(
            action="add",
            date="2024-01-01",
            days=10
        )
        assert "2024-01-11" in result["result"]


class TestJsonParser:
    """Tests for the JsonParser tool."""
    
    @pytest.mark.asyncio
    async def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        parser = JsonParser()
        result = await parser.execute(
            action="parse",
            data='{"name": "test", "value": 42}'
        )
        assert result["parsed"]["name"] == "test"
        assert result["parsed"]["value"] == 42
    
    @pytest.mark.asyncio
    async def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        parser = JsonParser()
        result = await parser.execute(
            action="parse",
            data="not valid json"
        )
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_validate_json(self):
        """Test JSON validation."""
        parser = JsonParser()
        result = await parser.execute(
            action="validate",
            data='{"valid": true}'
        )
        assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_extract_path(self):
        """Test extracting JSON path."""
        parser = JsonParser()
        result = await parser.execute(
            action="extract",
            data='{"user": {"name": "Alice", "age": 30}}',
            path="user.name"
        )
        assert result["value"] == "Alice"


class TestHttpRequest:
    """Tests for the HttpRequest tool."""
    
    @pytest.mark.asyncio
    async def test_get_request_mock(self):
        """Test GET request with mock."""
        http = HttpRequest()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"data": "test"}'
        mock_response.json.return_value = {"data": "test"}
        
        with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            result = await http.execute(
                method="GET",
                url="https://api.example.com/data"
            )
            
            assert result["status_code"] == 200
            assert result["body"]["data"] == "test"
    
    def test_http_request_schema(self):
        """Test HttpRequest schema."""
        http = HttpRequest()
        schema = http.get_schema()
        
        props = schema["parameters"]["properties"]
        assert "method" in props
        assert "url" in props
        assert "headers" in props


class TestFileOperations:
    """Tests for file operation tools."""
    
    @pytest.mark.asyncio
    async def test_file_reader(self, tmp_path):
        """Test FileReader."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        reader = FileReader()
        result = await reader.execute(path=str(test_file))
        
        assert result["content"] == "Hello, World!"
        assert result["size"] > 0
    
    @pytest.mark.asyncio
    async def test_file_writer(self, tmp_path):
        """Test FileWriter."""
        test_file = tmp_path / "output.txt"
        
        writer = FileWriter()
        result = await writer.execute(
            path=str(test_file),
            content="Test content"
        )
        
        assert result["success"] is True
        assert test_file.read_text() == "Test content"
    
    @pytest.mark.asyncio
    async def test_file_reader_not_found(self):
        """Test FileReader with non-existent file."""
        reader = FileReader()
        result = await reader.execute(path="/nonexistent/file.txt")
        assert "error" in result


class TestShellCommand:
    """Tests for ShellCommand tool."""
    
    @pytest.mark.asyncio
    async def test_echo_command(self):
        """Test simple echo command."""
        shell = ShellCommand()
        result = await shell.execute(command="echo 'Hello'")
        
        assert "Hello" in result["stdout"]
        assert result["returncode"] == 0
    
    @pytest.mark.asyncio
    async def test_failed_command(self):
        """Test failed command."""
        shell = ShellCommand()
        result = await shell.execute(command="exit 1")
        
        assert result["returncode"] == 1


class TestWebSearch:
    """Tests for WebSearch tool."""
    
    def test_web_search_schema(self):
        """Test WebSearch schema."""
        search = WebSearch()
        schema = search.get_schema()
        
        assert schema["name"] == "web_search"
        assert "query" in schema["parameters"]["properties"]
    
    @pytest.mark.asyncio
    async def test_web_search_placeholder(self):
        """Test WebSearch placeholder response."""
        search = WebSearch()
        result = await search.execute(query="test query")
        
        # Should return a placeholder since no API is configured
        assert "results" in result or "error" in result or "message" in result
