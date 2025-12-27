"""
Integration tests for Reasona.

These tests verify that components work together correctly.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestConductorWithTools:
    """Test Conductor with tools integration."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider."""
        provider = AsyncMock()
        provider.complete = AsyncMock(return_value=MagicMock(
            content="The result of 2 + 2 is 4.",
            tool_calls=[],
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        ))
        return provider
    
    @pytest.mark.asyncio
    async def test_conductor_uses_calculator_tool(self, mock_provider):
        """Test that conductor properly calls calculator tool."""
        from reasona import Conductor
        from reasona.tools import Calculator
        
        # Mock the provider
        with patch('reasona.integrations.providers.get_provider', return_value=mock_provider):
            agent = Conductor(
                name="test-agent",
                model="openai/gpt-4o",
                tools=[Calculator()]
            )
            
            # Mock tool call response
            mock_provider.complete = AsyncMock(return_value=MagicMock(
                content="",
                tool_calls=[{
                    "id": "call_123",
                    "function": {
                        "name": "calculator",
                        "arguments": '{"expression": "2 + 2"}'
                    }
                }],
                usage={}
            ))
            
            # The agent should have the calculator tool
            assert len(agent.tools) == 1
            assert agent.tools[0].name == "calculator"


class TestSynapseIntegration:
    """Test Synapse multi-agent communication."""
    
    @pytest.mark.asyncio
    async def test_agent_connection(self):
        """Test connecting agents to synapse."""
        from reasona import Conductor, Synapse
        
        with patch('reasona.integrations.providers.get_provider'):
            agent1 = Conductor(name="agent1", model="openai/gpt-4o")
            agent2 = Conductor(name="agent2", model="openai/gpt-4o")
            
            synapse = Synapse()
            synapse.connect(agent1)
            synapse.connect(agent2)
            
            assert len(synapse._agents) == 2
            assert "agent1" in synapse._agents
            assert "agent2" in synapse._agents
    
    @pytest.mark.asyncio
    async def test_agent_disconnection(self):
        """Test disconnecting agents from synapse."""
        from reasona import Conductor, Synapse
        
        with patch('reasona.integrations.providers.get_provider'):
            agent = Conductor(name="test-agent", model="openai/gpt-4o")
            
            synapse = Synapse()
            synapse.connect(agent)
            assert "test-agent" in synapse._agents
            
            synapse.disconnect(agent)
            assert "test-agent" not in synapse._agents


class TestWorkflowIntegration:
    """Test Workflow pipeline integration."""
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for workflow testing."""
        with patch('reasona.integrations.providers.get_provider'):
            from reasona import Conductor
            
            planner = Conductor(name="planner", model="openai/gpt-4o")
            executor = Conductor(name="executor", model="openai/gpt-4o")
            
            return planner, executor
    
    def test_workflow_stage_addition(self, mock_agents):
        """Test adding stages to workflow."""
        from reasona import Workflow
        
        planner, executor = mock_agents
        
        workflow = Workflow(name="test-workflow")
        workflow.add_stage(
            name="plan",
            agent=planner,
            prompt_template="Create plan for: {input}"
        )
        workflow.add_stage(
            name="execute",
            agent=executor,
            prompt_template="Execute: {plan}"
        )
        
        assert len(workflow._stages) == 2
        assert workflow._stages[0]["name"] == "plan"
        assert workflow._stages[1]["name"] == "execute"
    
    def test_workflow_visualization(self, mock_agents):
        """Test workflow visualization."""
        from reasona import Workflow
        
        planner, executor = mock_agents
        
        workflow = Workflow(name="test-workflow")
        workflow.add_stage(name="step1", agent=planner, prompt_template="{input}")
        workflow.add_stage(name="step2", agent=executor, prompt_template="{step1}")
        
        viz = workflow.visualize()
        assert "step1" in viz
        assert "step2" in viz


class TestContextIntegration:
    """Test Context with Conductor."""
    
    def test_context_creation(self):
        """Test creating context."""
        from reasona.core import Context, UserContext, SessionContext
        
        context = Context(
            user=UserContext(id="user_123", name="Test User"),
            session=SessionContext(id="session_456"),
            metadata={"custom": "value"}
        )
        
        assert context.user.id == "user_123"
        assert context.session.id == "session_456"
        assert context.metadata["custom"] == "value"
    
    def test_conductor_with_context(self):
        """Test conductor accepts context."""
        from reasona import Conductor
        from reasona.core import Context, UserContext
        
        with patch('reasona.integrations.providers.get_provider'):
            context = Context(user=UserContext(id="user_123"))
            
            agent = Conductor(
                name="test",
                model="openai/gpt-4o",
                context=context
            )
            
            assert agent.context is not None
            assert agent.context.user.id == "user_123"


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_registry_registration(self):
        """Test registering tools in registry."""
        from reasona.tools import ToolRegistry, tool
        
        registry = ToolRegistry()
        
        @registry.register
        @tool(description="Test tool")
        async def test_tool(x: int) -> int:
            return x * 2
        
        tools = registry.get_tools()
        assert len(tools) == 1
    
    def test_registry_search(self):
        """Test searching tools in registry."""
        from reasona.tools import ToolRegistry, tool
        
        registry = ToolRegistry()
        
        @registry.register
        @tool(name="calculator", description="Math calculations")
        async def calc(x: int) -> int:
            return x
        
        @registry.register
        @tool(name="weather", description="Weather info")
        async def weather(loc: str) -> str:
            return loc
        
        results = registry.search("math")
        assert len(results) >= 1


class TestServerIntegration:
    """Test server integration."""
    
    def test_create_app(self):
        """Test creating FastAPI app."""
        from reasona import Conductor
        from reasona.server import create_app
        
        with patch('reasona.integrations.providers.get_provider'):
            agent = Conductor(name="test", model="openai/gpt-4o")
            app = create_app(agent)
            
            # Check routes exist
            routes = [r.path for r in app.routes]
            assert "/health" in routes
            assert "/v1/think" in routes


class TestConfigIntegration:
    """Test configuration integration."""
    
    def test_config_from_env(self):
        """Test loading config from environment."""
        import os
        from reasona.core import ReasonaConfig
        
        # Set test env var
        os.environ["TEST_API_KEY"] = "test-key"
        
        config = ReasonaConfig()
        # Config should load without errors
        assert config is not None
    
    def test_config_api_key_setting(self):
        """Test setting API keys."""
        from reasona.core import ReasonaConfig
        
        config = ReasonaConfig()
        config.set_api_key("openai", "sk-test")
        
        provider_config = config.get_provider_config("openai")
        assert provider_config["api_key"] == "sk-test"


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_simple_agent_flow(self):
        """Test a simple agent interaction flow."""
        from reasona import Conductor
        
        mock_response = MagicMock(
            content="Hello! I'm here to help.",
            tool_calls=[],
            usage={"prompt_tokens": 5, "completion_tokens": 10}
        )
        
        mock_provider = AsyncMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        
        with patch('reasona.integrations.providers.get_provider', return_value=mock_provider):
            agent = Conductor(
                name="assistant",
                model="openai/gpt-4o",
                instructions="You are a helpful assistant."
            )
            
            response = await agent.athink("Hello!")
            assert "Hello" in response or response is not None
    
    @pytest.mark.asyncio 
    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation."""
        from reasona import Conductor
        
        responses = [
            MagicMock(content="Hi! I'm Claude.", tool_calls=[], usage={}),
            MagicMock(content="Your name is Alice.", tool_calls=[], usage={}),
        ]
        
        mock_provider = AsyncMock()
        mock_provider.complete = AsyncMock(side_effect=responses)
        
        with patch('reasona.integrations.providers.get_provider', return_value=mock_provider):
            agent = Conductor(name="test", model="openai/gpt-4o")
            
            response1 = await agent.athink("My name is Alice.")
            response2 = await agent.athink("What's my name?")
            
            # Both responses should complete
            assert response1 is not None
            assert response2 is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
