import os
import pytest
from unittest.mock import patch, MagicMock
from src.core.model_manager import ModelManager


@pytest.fixture
def mock_openai_client():
    """Fixture to mock the OpenAI client."""
    with patch("src.core.model_manager.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables required by ModelManager."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model")


class TestModelManager:
    def test_init(self, mock_openai_client, mock_env_vars):
        """Test that the OpenAI client is initialized correctly."""
        manager = ModelManager()
        mock_openai_client.chat.completions.create.assert_not_called()  # Should not be called on init
        # Check that the client was instantiated
        assert manager.client is not None

    def test_get_system_prompt(self, mock_env_vars):
        """Test that the system prompt is returned as expected."""
        manager = ModelManager()
        prompt = manager.get_system_prompt()
        assert isinstance(prompt, str)
        assert "TalentScout's AI hiring assistant" in prompt

    def test_generate_response_success(self, mock_openai_client, mock_env_vars):
        """Test a successful response generation."""
        # Configure the mock client to return a mock completion
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "This is a test response."
        mock_openai_client.chat.completions.create.return_value = mock_completion

        manager = ModelManager()
        response = manager.generate_response("Hello")

        assert response == "This is a test response."
        mock_openai_client.chat.completions.create.assert_called_once()

        # Verify the messages passed to the API
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2  # System + User
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_generate_response_with_history(self, mock_openai_client, mock_env_vars):
        """Test response generation with conversation history."""
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Follow-up response."
        mock_openai_client.chat.completions.create.return_value = mock_completion

        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]

        manager = ModelManager()
        response = manager.generate_response("Second question", history=history)

        assert response == "Follow-up response."

        # Verify the messages passed to the API
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 4  # System + History (user, assistant) + User
        assert messages[1]["content"] == "First question"
        assert messages[2]["content"] == "First answer"
        assert messages[3]["content"] == "Second question"

    def test_generate_response_missing_model(self, monkeypatch, mock_openai_client):
        """Test failure when the OPENROUTER_MODEL env var is not set."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        manager = ModelManager()
        with pytest.raises(
            ValueError, match="OPENROUTER_MODEL environment variable is not set"
        ):
            manager.generate_response("test")

    def test_generate_response_api_error(self, mock_openai_client, mock_env_vars):
        """Test the handling of an API error from the client."""
        # Configure the mock client to raise an exception
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        manager = ModelManager()
        response = manager.generate_response("Hello")

        assert "Something went wrong" in response
