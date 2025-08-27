import os
import pytest
from cryptography.fernet import Fernet
from src.core.encryption_handler import EncryptionManager

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


class TestEncryptionManager:
    def test_init_success(self, mock_env_valid_key):
        """Test successful initialization with a valid key."""
        manager = EncryptionManager()
        assert isinstance(manager.cipher_suite, Fernet)

    def test_init_missing_key(self, mock_env_missing_key):
        """Test initialization failure when key is missing."""
        with pytest.raises(ValueError, match="ENCRYPTION_KEY not found"):
            EncryptionManager()

    def test_init_invalid_key(self, mock_env_invalid_key):
        """Test initialization failure with an invalid key."""
        with pytest.raises(ValueError, match="Invalid ENCRYPTION_KEY format"):
            EncryptionManager()

    def test_encrypt_success(self, mock_env_valid_key):
        """Test successful encryption."""
        manager = EncryptionManager()
        original_text = "my-secret-data"
        encrypted_text = manager.encrypt(original_text)
        assert encrypted_text != original_text
        assert isinstance(encrypted_text, str)

    def test_encrypt_empty_text(self, mock_env_valid_key):
        """Test encrypting an empty or None string."""
        manager = EncryptionManager()
        assert manager.encrypt(None) == ""
        assert manager.encrypt("") == ""

    def test_encryption_decryption_roundtrip(self, mock_env_valid_key):
        """Test a full encryption and decryption roundtrip."""
        manager = EncryptionManager()
        original_text = "super-secret-message"

        encrypted_text = manager.encrypt(original_text)

        # Decrypt using the cipher_suite directly to verify correctness
        decrypted_bytes = manager.cipher_suite.decrypt(encrypted_text.encode())
        decrypted_text = decrypted_bytes.decode()

        assert decrypted_text == original_text
