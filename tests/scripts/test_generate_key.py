import os
import re
import base64
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.generate_key import (
    generate_key,
    read_env,
    write_env,
    insert_env_var,
    main,
    ENV_VAR_NAME,
    ENV_FILE,
)


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    return tmp_path / ".env"


def test_generate_key():
    """Test that a valid key is generated."""
    key = generate_key()
    assert isinstance(key, str)
    # Check if it's a valid base64 string
    try:
        base64.urlsafe_b64decode(key.encode("ascii"))
    except (ValueError, TypeError):
        pytest.fail("Generated key is not a valid URL-safe base64 string.")
    # Fernet keys are 32 bytes, which results in a 44-character base64 string
    assert len(base64.urlsafe_b64decode(key.encode("ascii"))) == 32


def test_read_write_env(temp_env_file):
    """Test reading from and writing to the .env file."""
    # Test reading a non-existent file
    assert read_env(temp_env_file) == ""

    # Test writing and then reading
    content = "TEST_KEY=TEST_VALUE\n"
    write_env(temp_env_file, content)
    assert read_env(temp_env_file) == content


def test_insert_env_var():
    """Test inserting and updating environment variables."""
    # Test inserting a new key
    content = ""
    new_content = insert_env_var(content, "NEW_KEY", "NEW_VALUE")
    assert "NEW_KEY=NEW_VALUE" in new_content

    # Test updating an existing key
    content = "EXISTING_KEY=OLD_VALUE\n"
    updated_content = insert_env_var(content, "EXISTING_KEY", "NEW_VALUE")
    assert "EXISTING_KEY=NEW_VALUE" in updated_content
    assert "OLD_VALUE" not in updated_content

    # Test inserting with existing content
    content = "FIRST_KEY=FIRST_VALUE\n"
    new_content = insert_env_var(content, "SECOND_KEY", "SECOND_VALUE")
    assert "FIRST_KEY=FIRST_VALUE" in new_content
    assert "SECOND_KEY=SECOND_VALUE" in new_content


@patch("scripts.generate_key.argparse.ArgumentParser")
def test_main_no_write(mock_argparse):
    """Test main function without --write argument."""
    mock_args = MagicMock()
    mock_args.write = False
    mock_args.force = False
    mock_argparse.return_value.parse_args.return_value = mock_args

    with (
        patch("scripts.generate_key.read_env") as mock_read_env,
        patch("scripts.generate_key.write_env") as mock_write_env,
    ):
        main()
        mock_read_env.assert_not_called()
        mock_write_env.assert_not_called()


@patch("scripts.generate_key.argparse.ArgumentParser")
@patch("scripts.generate_key.read_env", return_value="OPENROUTER_API_KEY=dummy\n")
@patch("scripts.generate_key.write_env")
def test_main_write_and_force(mock_write_env, mock_read_env, mock_argparse):
    """Test main function with --write and --force arguments."""
    mock_args = MagicMock()
    mock_args.write = True
    mock_args.force = True
    mock_argparse.return_value.parse_args.return_value = mock_args

    # Temporarily mock the ENV_FILE path to avoid creating a real file
    with patch("scripts.generate_key.ENV_FILE", Path("/tmp/fake.env")):
        main()
        mock_read_env.assert_called_once()
        mock_write_env.assert_called_once()

        # Check that the new key was written
        written_content = mock_write_env.call_args[0][1]
        assert f"{ENV_VAR_NAME}=" in written_content
