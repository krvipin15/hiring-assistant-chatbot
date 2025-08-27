import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Mock streamlit before it's imported by the app
import sys

sys.modules["streamlit"] = MagicMock()

from src.app import (
    check_environment,
    get_image_as_base64,
    initialize_session_state,
)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set all required environment variables."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("OPENROUTER_MODEL", "test_model")
    monkeypatch.setenv("ENCRYPTION_KEY", "a" * 44)  # Valid base64 key length


@pytest.fixture
def mock_st():
    """Fixture to get the mocked streamlit module."""
    return sys.modules["streamlit"]


class TestApp:
    def test_check_environment_success(self, mock_env_vars):
        """Test check_environment when all variables are set."""
        assert check_environment() is True

    def test_check_environment_failure(self, monkeypatch):
        """Test check_environment when variables are missing."""
        # Unset one of the required variables
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        assert check_environment() is False

    def test_get_image_as_base64(self, tmp_path):
        """Test the image to base64 encoding function."""
        # Create a dummy image file
        img_file = tmp_path / "test.png"
        img_content = b"fake-image-data"
        img_file.write_bytes(img_content)

        base64_str = get_image_as_base64(str(img_file))
        import base64

        assert base64.b64decode(base64_str) == img_content

    @patch("src.app.ConversationManager")
    def test_initialize_session_state_new_session(
        self, MockConversationManager, mock_st
    ):
        """Test initializing a new session state."""
        # Reset session_state for a clean test
        mock_st.session_state = {}
        mock_conversation_manager = MagicMock()
        mock_conversation_manager.handle_message.return_value = "Welcome!"
        MockConversationManager.return_value = mock_conversation_manager

        initialize_session_state()

        assert "conversation_manager" in mock_st.session_state
        assert "needs_response" in mock_st.session_state
        assert "messages" in mock_st.session_state
        assert len(mock_st.session_state.messages) == 1
        assert mock_st.session_state.messages[0]["content"] == "Welcome!"
        mock_conversation_manager.handle_message.assert_called_once_with("start")

    def test_initialize_session_state_with_old_messages(self, mock_st):
        """Test the fix for the old session state format."""
        # Simulate an old session state with integer timestamps
        mock_st.session_state = {
            "conversation_manager": MagicMock(),
            "messages": [{"role": "user", "content": "hi", "timestamp": 12345}],
        }

        initialize_session_state()

        # The messages list should be reset
        assert (
            len(mock_st.session_state.messages) == 1
        )  # It gets the initial welcome message

    def test_initialize_session_state_existing_manager(self, mock_st):
        """Test that an existing ConversationManager is not replaced."""
        existing_manager = MagicMock()
        mock_st.session_state = {
            "conversation_manager": existing_manager,
            "messages": [
                {"role": "assistant", "content": "Hello", "timestamp": MagicMock()}
            ],
        }

        initialize_session_state()

        assert mock_st.session_state.conversation_manager is existing_manager
