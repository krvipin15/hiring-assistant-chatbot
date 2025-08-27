import os
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

from scripts.decrypt_database import DecryptionManager, DatabaseDecryptor

# Generate a valid Fernet key for testing
TEST_KEY = Fernet.generate_key().decode()


@pytest.fixture
def mock_env_valid_key(monkeypatch):
    """Mock environment with a valid encryption key."""
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_KEY)


@pytest.fixture
def mock_env_invalid_key(monkeypatch):
    """Mock environment with an invalid encryption key."""
    monkeypatch.setenv("ENCRYPTION_KEY", "invalid-key")


@pytest.fixture
def mock_env_missing_key(monkeypatch):
    """Mock environment with a missing encryption key."""
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)


class TestDecryptionManager:
    def test_init_success(self, mock_env_valid_key):
        """Test successful initialization with a valid key."""
        manager = DecryptionManager()
        assert isinstance(manager.cipher_suite, Fernet)

    def test_init_missing_key(self, mock_env_missing_key):
        """Test initialization failure when key is missing."""
        with pytest.raises(ValueError, match="ENCRYPTION_KEY not found"):
            DecryptionManager()

    def test_init_invalid_key(self, mock_env_invalid_key):
        """Test initialization failure with an invalid key."""
        with pytest.raises(ValueError, match="Invalid ENCRYPTION_KEY format"):
            DecryptionManager()

    def test_decrypt_success(self, mock_env_valid_key):
        """Test successful decryption."""
        manager = DecryptionManager()
        original_text = "my-secret-data"
        encrypted_text = manager.cipher_suite.encrypt(original_text.encode()).decode()
        decrypted_text = manager.decrypt(encrypted_text)
        assert decrypted_text == original_text

    def test_decrypt_failure(self, mock_env_valid_key):
        """Test decryption failure with invalid data, returning original text."""
        manager = DecryptionManager()
        invalid_text = "not-encrypted-text"
        decrypted_text = manager.decrypt(invalid_text)
        assert decrypted_text == invalid_text

    def test_decrypt_empty_text(self, mock_env_valid_key):
        """Test decrypting an empty or None string."""
        manager = DecryptionManager()
        assert manager.decrypt(None) == ""
        assert manager.decrypt("") == ""


@pytest.fixture
def mock_db(tmp_path):
    """Create in-memory SQLite databases for testing."""
    source_db_path = tmp_path / "source.db"
    target_db_path = tmp_path / "target.db"

    # Setup source database
    with sqlite3.connect(source_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE candidates (
                id INTEGER PRIMARY KEY, date_time TEXT, name TEXT, phone_number TEXT,
                email TEXT, current_location TEXT, experience_years INTEGER,
                desired_positions TEXT, tech_stack TEXT, technical_responses_json TEXT
            )
            """
        )
    return str(source_db_path), str(target_db_path)


@patch("scripts.decrypt_database.DecryptionManager")
def test_database_decryptor_init(MockDecryptionManager, mock_db, mock_env_valid_key):
    """Test DatabaseDecryptor initialization and table creation."""
    source_db, target_db = mock_db
    decryptor = DatabaseDecryptor(source_db=source_db, target_db=target_db)

    MockDecryptionManager.assert_called_once()
    assert decryptor.source_db == source_db
    assert decryptor.target_db == target_db

    # Check if the target table was created
    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'"
        )
        assert cursor.fetchone() is not None


@patch("scripts.decrypt_database.DecryptionManager")
def test_migrate_data(MockDecryptionManager, mock_db, mock_env_valid_key):
    """Test data migration and decryption logic."""
    source_db, target_db = mock_db

    # Mock the decryption manager
    mock_decrypt_manager = MagicMock()
    mock_decrypt_manager.decrypt.side_effect = lambda x: x.replace("encrypted_", "")
    MockDecryptionManager.return_value = mock_decrypt_manager

    # Insert encrypted data into the source database
    with sqlite3.connect(source_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                1,
                "2023-01-01",
                "John Doe",
                "encrypted_phone",
                "encrypted_email",
                "encrypted_location",
                5,
                "Dev",
                "Python",
                "{}",
            ),
        )
        conn.commit()

    # Run migration
    decryptor = DatabaseDecryptor(source_db=source_db, target_db=target_db)
    decryptor.migrate_data()

    # Verify decrypted data in the target database
    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE id = 1")
        row = cursor.fetchone()
        assert row is not None
        assert row[3] == "phone"  # phone_number
        assert row[4] == "email"  # email
        assert row[5] == "location"  # current_location
