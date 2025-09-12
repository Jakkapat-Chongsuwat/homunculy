"""
End-to-End tests for AI Agent REST API.

These tests verify the complete AI Agent API functionality from HTTP requests
to database persistence using real database containers.
"""

import json
from typing import Dict

import pytest
from httpx import AsyncClient

from models.ai_agent.ai_agent import AgentProvider


class TestAIAgentAPI:
    """E2E tests for AI Agent REST API endpoints."""

    @pytest.mark.asyncio
    async def test_create_agent_e2e(self, client: AsyncClient):
        """Test creating a new AI agent through the API."""
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "E2E Test Agent",
                "description": "Agent created during e2e testing",
                "traits": {"helpfulness": 0.9, "creativity": 0.8},
                "mood": "curious",
                "memory_context": "Testing AI agent API endpoints"
            },
            "system_prompt": "You are a helpful test assistant.",
            "temperature": 0.7,
            "max_tokens": 1000,
            "tools": ["web_search", "calculator"]
        }

        response = await client.post("/agents", json=agent_data)

        assert response.status_code == 201
        response_data = response.json()
        assert "agent_id" in response_data
        assert isinstance(response_data["agent_id"], str)

        # Store agent_id for other tests
        self.agent_id = response_data["agent_id"]

    @pytest.mark.asyncio
    async def test_chat_with_agent_e2e(self, client: AsyncClient):
        """Test chatting with an AI agent through the API."""
        # First create an agent
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Chat Test Agent",
                "description": "Agent for chat testing",
                "traits": {"helpfulness": 0.9},
                "mood": "friendly"
            },
            "system_prompt": "You are a friendly chat assistant.",
            "temperature": 0.7,
            "max_tokens": 500,
            "tools": []
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # Now chat with the agent
        chat_data = {
            "message": "Hello! How are you today?",
            "thread_id": None,
            "context": {"session_type": "test"}
        }

        response = await client.post(f"/agents/{agent_id}/chat", json=chat_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert "confidence" in response_data
        assert "status" in response_data
        assert response_data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_agent_personality_e2e(self, client: AsyncClient):
        """Test updating an agent's personality through the API."""
        # Create an agent first
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Personality Test Agent",
                "description": "Agent for personality update testing",
                "traits": {"helpfulness": 0.5},
                "mood": "neutral"
            },
            "system_prompt": "You are a test assistant.",
            "temperature": 0.7,
            "max_tokens": 500,
            "tools": []
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # Update personality
        update_data = {
            "personality": {
                "name": "Updated Personality Test Agent",
                "description": "Updated agent for personality testing",
                "traits": {"helpfulness": 0.9, "creativity": 0.8},
                "mood": "excited",
                "memory_context": "Updated personality for testing"
            }
        }

        response = await client.put(f"/agents/{agent_id}/personality", json=update_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "updated"

    @pytest.mark.asyncio
    async def test_get_agent_config_e2e(self, client: AsyncClient):
        """Test getting agent configuration through the API."""
        # Create an agent first
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Config Test Agent",
                "description": "Agent for configuration testing",
                "traits": {"accuracy": 0.9},
                "mood": "focused"
            },
            "system_prompt": "You are a precise assistant.",
            "temperature": 0.3,
            "max_tokens": 1000,
            "tools": ["calculator"]
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # Get configuration
        response = await client.get(f"/agents/{agent_id}/config")

        assert response.status_code == 200
        config_data = response.json()
        assert config_data["provider"] == "pydantic_ai"
        assert config_data["model_name"] == "gpt-4"
        assert config_data["personality"]["name"] == "Config Test Agent"
        assert config_data["personality"]["traits"]["accuracy"] == 0.9
        assert config_data["temperature"] == 0.3
        assert "calculator" in config_data["tools"]

    @pytest.mark.asyncio
    async def test_get_agent_status_e2e(self, client: AsyncClient):
        """Test getting agent status through the API."""
        # Create an agent first
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Status Test Agent",
                "description": "Agent for status testing",
                "traits": {"reliability": 0.8}
            }
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # Get status
        response = await client.get(f"/agents/{agent_id}/status")

        assert response.status_code == 200
        status_data = response.json()
        assert status_data["agent_id"] == agent_id
        assert status_data["status"] == "active"
        assert "thread_count" in status_data
        assert "message_count" in status_data

    @pytest.mark.asyncio
    async def test_list_providers_e2e(self, client: AsyncClient):
        """Test listing available AI providers through the API."""
        response = await client.get("/providers")

        assert response.status_code == 200
        providers_data = response.json()
        assert isinstance(providers_data, list)
        assert len(providers_data) > 0

        # Check that pydantic_ai is in the list
        provider_names = [p["name"] for p in providers_data]
        assert "pydantic_ai" in provider_names

    @pytest.mark.asyncio
    async def test_shutdown_agent_e2e(self, client: AsyncClient):
        """Test shutting down an agent through the API."""
        # Create an agent first
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Shutdown Test Agent",
                "description": "Agent for shutdown testing"
            }
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # Shutdown the agent
        response = await client.delete(f"/agents/{agent_id}")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "shutdown"

    @pytest.mark.asyncio
    async def test_agent_not_found_scenarios(self, client: AsyncClient):
        """Test API responses when agent is not found."""
        fake_agent_id = "non-existent-agent-id"

        # Test get config for non-existent agent
        response = await client.get(f"/agents/{fake_agent_id}/config")
        assert response.status_code == 200  # API returns 200 with error info
        config_data = response.json()
        assert "Agent not found" in config_data["personality"]["description"]

        # Test update personality for non-existent agent
        update_data = {
            "personality": {
                "name": "Updated Name",
                "description": "Updated description"
            }
        }
        response = await client.put(f"/agents/{fake_agent_id}/personality", json=update_data)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "Agent not found" in response_data["message"]

        # Test shutdown non-existent agent
        response = await client.delete(f"/agents/{fake_agent_id}")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "Agent not found" in response_data["message"]

    @pytest.mark.asyncio
    async def test_chat_with_thread_e2e(self, client: AsyncClient):
        """Test chatting with thread context through the API."""
        # Create an agent first
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Thread Test Agent",
                "description": "Agent for thread testing"
            }
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        thread_id = "test-thread-123"

        # First message
        chat_data1 = {
            "message": "My name is Alice.",
            "thread_id": thread_id,
            "context": {"user_name": "Alice"}
        }

        response1 = await client.post(f"/agents/{agent_id}/chat", json=chat_data1)
        assert response1.status_code == 200

        # Second message with same thread
        chat_data2 = {
            "message": "What's my name?",
            "thread_id": thread_id,
            "context": {"test_type": "memory"}
        }

        response2 = await client.post(f"/agents/{agent_id}/chat", json=chat_data2)
        assert response2.status_code == 200

        # Both responses should be successful
        assert response1.json()["status"] == "completed"
        assert response2.json()["status"] == "completed"


class TestAIAgentAPIIntegration:
    """Integration tests combining multiple API operations."""

    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle_e2e(self, client: AsyncClient):
        """Test complete agent lifecycle through API: create -> chat -> update -> status -> shutdown."""
        # 1. Create agent
        agent_data = {
            "provider": "pydantic_ai",
            "model_name": "gpt-4",
            "personality": {
                "name": "Lifecycle Test Agent",
                "description": "Agent for complete lifecycle testing",
                "traits": {"helpfulness": 0.9},
                "mood": "enthusiastic"
            },
            "system_prompt": "You are an enthusiastic assistant.",
            "temperature": 0.8,
            "max_tokens": 800,
            "tools": ["web_search"]
        }

        create_response = await client.post("/agents", json=agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # 2. Get initial config
        config_response = await client.get(f"/agents/{agent_id}/config")
        assert config_response.status_code == 200
        initial_config = config_response.json()
        assert initial_config["personality"]["mood"] == "enthusiastic"

        # 3. Chat with agent
        chat_response = await client.post(
            f"/agents/{agent_id}/chat",
            json={"message": "Hello! Tell me about yourself."}
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["status"] == "completed"

        # 4. Update personality
        update_response = await client.put(
            f"/agents/{agent_id}/personality",
            json={
                "personality": {
                    "name": "Updated Lifecycle Agent",
                    "description": "Updated agent after chat",
                    "traits": {"helpfulness": 0.8, "wisdom": 0.7},
                    "mood": "wise",
                    "memory_context": "Has chatted with user about introduction"
                }
            }
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "updated"

        # 5. Verify personality update
        updated_config_response = await client.get(f"/agents/{agent_id}/config")
        assert updated_config_response.status_code == 200
        updated_config = updated_config_response.json()
        assert updated_config["personality"]["mood"] == "wise"
        assert updated_config["personality"]["traits"]["wisdom"] == 0.7

        # 6. Check status
        status_response = await client.get(f"/agents/{agent_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "active"

        # 7. Shutdown agent
        shutdown_response = await client.delete(f"/agents/{agent_id}")
        assert shutdown_response.status_code == 200
        assert shutdown_response.json()["status"] == "shutdown"

        # 8. Verify agent is gone (config should return not found)
        final_config_response = await client.get(f"/agents/{agent_id}/config")
        assert final_config_response.status_code == 200
        final_config = final_config_response.json()
        assert "Agent not found" in final_config["personality"]["description"]