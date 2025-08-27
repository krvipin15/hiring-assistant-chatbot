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
        mock_openai_client.chat.completions.create.assert_not_called() # Should not be called on init
        assert manager.client is not None

    def test_get_system_prompt(self, mock_env_vars):
        """Test that the system prompt is returned as expected."""
        manager = ModelManager()
        prompt = manager.get_system_prompt()
        assert isinstance(prompt, str)
        assert "TalentScout's AI hiring assistant" in prompt

    def test_generate_response_success(self, mock_openai_client, mock_env_vars):
        """Test a successful response generation."""
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "This is a test response."
        mock_openai_client.chat.completions.create.return_value = mock_completion

        manager = ModelManager()
        response = manager.generate_response("Hello")

        assert response == "This is a test response."
        mock_openai_client.chat.completions.create.assert_called_once()

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        assert len(messages) == 2 # System + User
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'Hello'

    def test_generate_response_with_history(self, mock_openai_client, mock_env_vars):
        """Test response generation with conversation history."""
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Follow-up response."
        mock_openai_client.chat.completions.create.return_value = mock_completion

        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"}
        ]

        manager = ModelManager()
        response = manager.generate_response("Second question", history=history)

        assert response == "Follow-up response."

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        assert len(messages) == 4 # System + History (user, assistant) + User
        assert messages[1]['content'] == "First question"
        assert messages[2]['content'] == "First answer"
        assert messages[3]['content'] == "Second question"

    def test_generate_response_api_error(self, mock_openai_client, mock_env_vars):
        """Test the handling of an API error from the client."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        manager = ModelManager()
        response = manager.generate_response("Hello")

        assert "Something went wrong" in response

@patch("src.core.model_manager.load_dotenv")
def test_generate_response_missing_model(self):
    """Test failure when the OPENROUTER_MODEL env var is not set."""
    with patch("src.core.model_manager.OpenAI") as mock_openai:
        with patch("src.core.model_manager.os.getenv") as mock_getenv:
            # Define the behavior of the mocked os.getenv
            def getenv_side_effect(key, default=None):
                if key == 'OPENROUTER_API_KEY':
                    return "test-api-key"
                if key == 'OPENROUTER_MODEL':
                    return None  # This should trigger the error handling
                return default

            mock_getenv.side_effect = getenv_side_effect
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            manager = ModelManager()

            # The error should be caught and returned as an error message
            response = manager.generate_response("test message")
            assert "Something went wrong" in response or "OPENROUTER_MODEL environment variable is not set" in response
