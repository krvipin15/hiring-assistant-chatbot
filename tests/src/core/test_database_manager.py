import pytest
import sqlite3
import json
from unittest.mock import patch, MagicMock
from src.core.database_manager import DatabaseManager


@pytest.fixture
def db_path(tmp_path):
    """Provide a path to a temporary database file."""
    return tmp_path / "test_candidates.db"


@pytest.fixture
def mock_encryption_manager():
    """Fixture to mock the EncryptionManager."""
    with patch("src.core.database_manager.EncryptionManager") as mock_em:
        mock_instance = MagicMock()
        # Make the mock encrypt function return a predictable value
        mock_instance.encrypt.side_effect = lambda text: f"encrypted_{text}"
        mock_em.return_value = mock_instance
        yield mock_instance


class TestDatabaseManager:
    def test_init_and_create_table(self, db_path, mock_encryption_manager):
        """Test that the database is initialized and the table is created."""
        db_manager = DatabaseManager(db_path=str(db_path))

        # Check if the table was created
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'"
            )
            assert cursor.fetchone() is not None, "Table 'candidates' was not created."

    def test_save_candidate_success(self, db_path, mock_encryption_manager):
        """Test successfully saving a candidate's data."""
        db_manager = DatabaseManager(db_path=str(db_path))

        candidate_data = {
            "name": "Jane Doe",
            "phone_number": "1234567890",
            "email": "jane.doe@example.com",
            "current_location": "New York",
            "experience_years": 5,
            "desired_positions": "Software Engineer",
            "tech_stack": "Python, Docker",
        }
        technical_responses = {"q1": "ans1"}

        db_manager.save_candidate(candidate_data, technical_responses)

        # Verify the data was saved correctly
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE name = ?", ("Jane Doe",))
            row = cursor.fetchone()
            assert row is not None
            assert row[2] == "Jane Doe"
            assert row[3] == "encrypted_1234567890"  # Check encrypted phone
            assert row[4] == "encrypted_jane.doe@example.com"  # Check encrypted email
            assert row[5] == "encrypted_New York"  # Check encrypted location
            assert row[6] == 5  # Experience
            assert row[9] == json.dumps(technical_responses)

    def test_save_candidate_encryption_called(self, db_path, mock_encryption_manager):
        """Verify that the encrypt method is called for sensitive fields."""
        db_manager = DatabaseManager(db_path=str(db_path))

        candidate_data = {
            "name": "Jane Doe",
            "phone_number": "1234567890",
            "email": "jane.doe@example.com",
            "current_location": "New York",
            "experience_years": 5,
            "desired_positions": "Software Engineer",
            "tech_stack": "Python, Docker",
        }
        technical_responses = {}

        db_manager.save_candidate(candidate_data, technical_responses)

        # Check that encrypt was called with the correct values
        mock_encryption_manager.encrypt.assert_any_call("1234567890")
        mock_encryption_manager.encrypt.assert_any_call("jane.doe@example.com")
        mock_encryption_manager.encrypt.assert_any_call("New York")
        assert mock_encryption_manager.encrypt.call_count == 3

    @patch("sqlite3.connect")
    def test_save_candidate_db_error(
        self, mock_sql_connect, db_path, mock_encryption_manager
    ):
        """Test the behavior when a database error occurs."""
        # Force the database connection to raise an error
        mock_sql_connect.side_effect = sqlite3.Error("Test DB Error")

        db_manager = DatabaseManager(db_path=str(db_path))

        candidate_data = {"name": "Jane Doe"}
        technical_responses = {}

        with pytest.raises(RuntimeError, match="Error saving candidate: Test DB Error"):
            db_manager.save_candidate(candidate_data, technical_responses)
