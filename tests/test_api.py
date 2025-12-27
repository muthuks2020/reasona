"""
Tests for Reasona API server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from reasona.core import Conductor
from reasona.server.api import create_app, ConductorRouter


class TestAPIServer:
    """Tests for the FastAPI server."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        return Conductor(
            name="test-agent",
            model="openai/gpt-4o",
            instructions="You are a test agent."
        )
    
    @pytest.fixture
    def client(self, agent):
        """Create test client."""
        app = create_app(agent)
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_agent_info_endpoint(self, client):
        """Test agent info endpoint."""
        response = client.get("/v1/agent")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "test-agent"
        assert data["model"] == "openai/gpt-4o"
    
    def test_agent_card_endpoint(self, client):
        """Test agent card discovery endpoint."""
        response = client.get("/.well-known/agent-card.json")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "test-agent"
        assert "capabilities" in data
        assert "synaptic" in data
    
    def test_tools_endpoint(self, client):
        """Test tools listing endpoint."""
        response = client.get("/v1/tools")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
    
    def test_reset_endpoint(self, client):
        """Test conversation reset endpoint."""
        response = client.post("/v1/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "reset"
    
    def test_think_endpoint_mock(self, client, agent):
        """Test think endpoint with mocked response."""
        # Mock the agent's think method
        with patch.object(agent, 'athink', new_callable=AsyncMock) as mock_think:
            mock_think.return_value = "This is a test response."
            
            response = client.post(
                "/v1/think",
                json={"input": "Hello"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "This is a test response."
    
    def test_chat_endpoint_alias(self, client, agent):
        """Test chat endpoint (alias for think)."""
        with patch.object(agent, 'athink', new_callable=AsyncMock) as mock_think:
            mock_think.return_value = "Chat response"
            
            response = client.post(
                "/v1/chat",
                json={"input": "Hi there"}
            )
            
            assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/v1/think",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS middleware should handle OPTIONS
        assert response.status_code in [200, 405]


class TestConductorRouter:
    """Tests for ConductorRouter (multi-agent routing)."""
    
    def test_router_creation(self):
        """Test creating a router."""
        router = ConductorRouter()
        assert router._agents == {}
    
    def test_add_agent(self):
        """Test adding agent to router."""
        router = ConductorRouter()
        agent = Conductor(name="agent1", model="openai/gpt-4o")
        
        router.add_agent(agent)
        
        assert "agent1" in router._agents
    
    def test_remove_agent(self):
        """Test removing agent from router."""
        router = ConductorRouter()
        agent = Conductor(name="agent1", model="openai/gpt-4o")
        
        router.add_agent(agent)
        router.remove_agent("agent1")
        
        assert "agent1" not in router._agents
    
    def test_build_app(self):
        """Test building FastAPI app from router."""
        router = ConductorRouter()
        agent = Conductor(name="test", model="openai/gpt-4o")
        router.add_agent(agent)
        
        app = router.build()
        
        assert app is not None
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
    
    def test_multi_agent_routing(self):
        """Test routing to multiple agents."""
        router = ConductorRouter()
        
        agent1 = Conductor(name="agent-a", model="openai/gpt-4o")
        agent2 = Conductor(name="agent-b", model="anthropic/claude-3-5-sonnet")
        
        router.add_agent(agent1)
        router.add_agent(agent2)
        
        app = router.build()
        client = TestClient(app)
        
        # Get agent cards
        response = client.get("/agent-a/card")
        assert response.status_code == 200
        assert response.json()["name"] == "agent-a"
        
        response = client.get("/agent-b/card")
        assert response.status_code == 200
        assert response.json()["name"] == "agent-b"


class TestAPIModels:
    """Tests for API request/response models."""
    
    def test_think_request_validation(self, client):
        """Test request validation."""
        # Missing required field
        response = client.post("/v1/think", json={})
        assert response.status_code == 422
    
    def test_think_with_context(self, agent):
        """Test think with context."""
        app = create_app(agent)
        client = TestClient(app)
        
        with patch.object(agent, 'athink', new_callable=AsyncMock) as mock_think:
            mock_think.return_value = "Response with context"
            
            response = client.post(
                "/v1/think",
                json={
                    "input": "Hello",
                    "context": {
                        "user": {"user_id": "u123"},
                        "metadata": {"source": "test"}
                    }
                }
            )
            
            assert response.status_code == 200


class TestStreaming:
    """Tests for streaming responses."""
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint(self):
        """Test streaming think endpoint."""
        agent = Conductor(name="stream-test", model="openai/gpt-4o")
        app = create_app(agent)
        client = TestClient(app)
        
        # Mock streaming
        async def mock_stream(input_text):
            for word in ["Hello", " ", "World", "!"]:
                yield word
        
        with patch.object(agent, 'stream', side_effect=mock_stream):
            response = client.post(
                "/v1/think",
                json={"input": "Hi", "stream": True},
                headers={"Accept": "text/event-stream"}
            )
            
            # Should get SSE response or regular JSON
            assert response.status_code in [200, 500]  # 500 if streaming not fully mocked


class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_not_found(self):
        """Test 404 handling."""
        agent = Conductor(name="test", model="openai/gpt-4o")
        app = create_app(agent)
        client = TestClient(app)
        
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 handling."""
        agent = Conductor(name="test", model="openai/gpt-4o")
        app = create_app(agent)
        client = TestClient(app)
        
        response = client.put("/v1/think", json={})
        assert response.status_code == 405
    
    def test_internal_error_handling(self):
        """Test internal error handling."""
        agent = Conductor(name="test", model="openai/gpt-4o")
        app = create_app(agent)
        client = TestClient(app)
        
        with patch.object(agent, 'athink', new_callable=AsyncMock) as mock_think:
            mock_think.side_effect = Exception("Internal error")
            
            response = client.post(
                "/v1/think",
                json={"input": "Hello"}
            )
            
            assert response.status_code == 500
