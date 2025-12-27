"""
Tests for Reasona core modules.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from reasona.core.message import Message, Role
from reasona.core.context import Context, UserContext, SessionContext
from reasona.core.config import ReasonaConfig
from reasona.core.conductor import Conductor
from reasona.core.synapse import Synapse, SynapticMessage, MessageType
from reasona.core.workflow import Workflow, Stage


class TestMessage:
    """Tests for the Message class."""
    
    def test_create_user_message(self):
        """Test creating a user message."""
        msg = Message(role=Role.USER, content="Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert msg.timestamp is not None
    
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = Message(role=Role.ASSISTANT, content="Hi there!")
        assert msg.role == Role.ASSISTANT
        assert msg.content == "Hi there!"
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message(role=Role.USER, content="Test")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Test"
    
    def test_message_with_tool_calls(self):
        """Test message with tool calls."""
        tool_calls = [{"id": "1", "name": "calculator", "arguments": {"expr": "2+2"}}]
        msg = Message(role=Role.ASSISTANT, content="", tool_calls=tool_calls)
        assert msg.tool_calls == tool_calls
        assert len(msg.tool_calls) == 1
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {"role": "user", "content": "Hello from dict"}
        msg = Message.from_dict(data)
        assert msg.role == Role.USER
        assert msg.content == "Hello from dict"


class TestContext:
    """Tests for the Context classes."""
    
    def test_user_context(self):
        """Test UserContext creation."""
        ctx = UserContext(user_id="user123", name="Test User")
        assert ctx.user_id == "user123"
        assert ctx.name == "Test User"
    
    def test_session_context(self):
        """Test SessionContext creation."""
        ctx = SessionContext(session_id="sess456")
        assert ctx.session_id == "sess456"
        assert ctx.started_at is not None
    
    def test_context_builder(self):
        """Test Context builder pattern."""
        ctx = (Context()
            .with_user(user_id="u1", name="Alice")
            .with_session(session_id="s1")
            .with_metadata(key="value"))
        
        assert ctx.user.user_id == "u1"
        assert ctx.session.session_id == "s1"
        assert ctx.metadata["key"] == "value"
    
    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        ctx = Context().with_user(user_id="u1")
        d = ctx.to_dict()
        assert "user" in d
        assert d["user"]["user_id"] == "u1"


class TestConfig:
    """Tests for ReasonaConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ReasonaConfig()
        assert config.default_model == "openai/gpt-4o"
        assert config.log_level == "INFO"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ReasonaConfig(
            default_model="anthropic/claude-3-5-sonnet",
            log_level="DEBUG"
        )
        assert config.default_model == "anthropic/claude-3-5-sonnet"
        assert config.log_level == "DEBUG"
    
    def test_set_api_key(self):
        """Test setting API key."""
        config = ReasonaConfig()
        config.set_api_key("openai", "sk-test123")
        assert config.get_provider_config("openai")["api_key"] == "sk-test123"
    
    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "default_model": "google/gemini-pro",
            "providers": {
                "google": {"api_key": "test-key"}
            }
        }
        config = ReasonaConfig.from_dict(data)
        assert config.default_model == "google/gemini-pro"


class TestConductor:
    """Tests for the Conductor class."""
    
    def test_conductor_creation(self):
        """Test creating a Conductor."""
        agent = Conductor(
            name="test-agent",
            model="openai/gpt-4o",
            instructions="You are helpful."
        )
        assert agent.name == "test-agent"
        assert agent.model == "openai/gpt-4o"
        assert agent.instructions == "You are helpful."
    
    def test_conductor_with_tools(self, sample_tools):
        """Test Conductor with tools."""
        agent = Conductor(
            name="tool-agent",
            model="openai/gpt-4o",
            tools=sample_tools
        )
        assert len(agent.tools) == 3
    
    def test_conductor_reset(self):
        """Test resetting conversation."""
        agent = Conductor(name="test", model="openai/gpt-4o")
        agent._messages = [Message(role=Role.USER, content="test")]
        agent.reset()
        assert len(agent._messages) == 0
    
    def test_conductor_add_tool(self, sample_tools):
        """Test adding a tool."""
        agent = Conductor(name="test", model="openai/gpt-4o")
        agent.add_tool(sample_tools[0])
        assert len(agent.tools) == 1
    
    def test_conductor_get_agent_card(self):
        """Test generating agent card."""
        agent = Conductor(
            name="card-test",
            model="openai/gpt-4o",
            instructions="Test agent"
        )
        card = agent.get_agent_card()
        assert card["name"] == "card-test"
        assert "capabilities" in card
        assert "synaptic" in card
    
    def test_conductor_from_dict(self):
        """Test creating Conductor from dictionary."""
        data = {
            "name": "dict-agent",
            "model": "anthropic/claude-3-5-sonnet",
            "instructions": "From dict"
        }
        agent = Conductor.from_dict(data)
        assert agent.name == "dict-agent"
        assert agent.model == "anthropic/claude-3-5-sonnet"


class TestSynapse:
    """Tests for the Synapse class."""
    
    def test_synapse_creation(self):
        """Test creating a Synapse."""
        synapse = Synapse()
        assert synapse._agents == {}
        assert synapse._connections == []
    
    def test_synapse_connect(self):
        """Test connecting agents."""
        synapse = Synapse()
        agent1 = Conductor(name="agent1", model="openai/gpt-4o")
        agent2 = Conductor(name="agent2", model="openai/gpt-4o")
        
        synapse.connect(agent1).connect(agent2)
        
        assert "agent1" in synapse._agents
        assert "agent2" in synapse._agents
    
    def test_synapse_disconnect(self):
        """Test disconnecting agents."""
        synapse = Synapse()
        agent = Conductor(name="agent1", model="openai/gpt-4o")
        
        synapse.connect(agent)
        synapse.disconnect(agent)
        
        assert "agent1" not in synapse._agents
    
    def test_synaptic_message(self):
        """Test SynapticMessage creation."""
        msg = SynapticMessage(
            type=MessageType.REQUEST,
            sender="agent1",
            receiver="agent2",
            content="Hello"
        )
        assert msg.type == MessageType.REQUEST
        assert msg.sender == "agent1"
        assert msg.content == "Hello"
    
    def test_synaptic_message_to_dict(self):
        """Test converting SynapticMessage to dict."""
        msg = SynapticMessage(
            type=MessageType.RESPONSE,
            sender="a1",
            receiver="a2",
            content="data"
        )
        d = msg.to_dict()
        assert d["type"] == "RESPONSE"
        assert d["sender"] == "a1"


class TestWorkflow:
    """Tests for the Workflow class."""
    
    def test_workflow_creation(self):
        """Test creating a Workflow."""
        workflow = Workflow(name="test-workflow")
        assert workflow.name == "test-workflow"
        assert len(workflow.stages) == 0
    
    def test_workflow_add_stage(self):
        """Test adding stages to workflow."""
        workflow = Workflow(name="test")
        agent = Conductor(name="stage-agent", model="openai/gpt-4o")
        
        workflow.add_stage("step1", agent, "Process: {input}")
        
        assert len(workflow.stages) == 1
        assert workflow.stages[0].name == "step1"
    
    def test_workflow_remove_stage(self):
        """Test removing a stage."""
        workflow = Workflow(name="test")
        agent = Conductor(name="agent", model="openai/gpt-4o")
        
        workflow.add_stage("step1", agent, "Test")
        workflow.remove_stage("step1")
        
        assert len(workflow.stages) == 0
    
    def test_stage_creation(self):
        """Test Stage creation."""
        agent = Conductor(name="agent", model="openai/gpt-4o")
        stage = Stage(
            name="process",
            agent=agent,
            prompt_template="Do: {input}",
            timeout=30.0
        )
        assert stage.name == "process"
        assert stage.timeout == 30.0
    
    def test_workflow_visualize(self):
        """Test workflow visualization."""
        workflow = Workflow(name="viz-test")
        agent = Conductor(name="a", model="openai/gpt-4o")
        
        workflow.add_stage("s1", agent, "Step 1")
        workflow.add_stage("s2", agent, "Step 2")
        
        viz = workflow.visualize()
        assert "viz-test" in viz
        assert "s1" in viz
        assert "s2" in viz


class TestIntegration:
    """Integration tests (require mocking)."""
    
    @pytest.mark.asyncio
    async def test_conductor_athink_mock(self, mock_openai_response):
        """Test async think with mocked response."""
        agent = Conductor(
            name="test",
            model="openai/gpt-4o"
        )
        
        # Mock the provider
        mock_provider = AsyncMock()
        mock_provider.complete = AsyncMock(return_value=Mock(
            content="Mocked response",
            tool_calls=None
        ))
        
        with patch.object(agent, '_get_provider', return_value=mock_provider):
            response = await agent.athink("Hello")
            assert response == "Mocked response"
    
    @pytest.mark.asyncio
    async def test_synapse_send_mock(self):
        """Test synapse send with mocked agents."""
        synapse = Synapse()
        
        agent1 = Conductor(name="sender", model="openai/gpt-4o")
        agent2 = Conductor(name="receiver", model="openai/gpt-4o")
        
        # Mock athink
        agent2.athink = AsyncMock(return_value="Received!")
        
        synapse.connect(agent1).connect(agent2)
        
        response = await synapse.send("sender", "receiver", "Test message")
        assert response is not None
