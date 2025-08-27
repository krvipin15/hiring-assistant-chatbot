import pytest
from unittest.mock import patch, MagicMock
from src.core.data_validator import validate_email, validate_phone, validate_location


# Test cases for email validation
@pytest.mark.parametrize(
    "email, expected",
    [
        ("test@example.com", True),
        ("test.name@example.co.uk", True),
        ("invalid-email", False),
        ("test@.com", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_email(email, expected):
    assert validate_email(email) == expected


# Test cases for phone number validation
@pytest.mark.parametrize(
    "phone, expected",
    [
        ("+14155552671", True),  # Valid US number
        ("+442071838750", True),  # Valid UK number
        ("+919876543210", True),  # Valid Indian number
        ("12345", False),  # Invalid number
        ("not a phone", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_phone(phone, expected):
    assert validate_phone(phone) == expected


# --- Tests for location validation with mocking --- #


@patch("requests.get")
def test_validate_location_valid(mock_get):
    """Test a valid location that returns a proper API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"display_name": "New York, USA", "importance": 0.9}
    ]
    mock_get.return_value = mock_response

    assert validate_location("New York, USA") is True
    mock_get.assert_called_once()


@patch("requests.get")
def test_validate_location_not_found(mock_get):
    """Test a location that is not found by the API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response

    assert validate_location("NonExistentPlace") is False


@patch("requests.get")
def test_validate_location_api_error(mock_get):
    """Test handling of an API error (e.g., 500 status code)."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    assert validate_location("Anywhere") is False


@patch("requests.get")
def test_validate_location_low_importance(mock_get):
    """Test that a location with a very low importance score is rejected."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"display_name": "A random road", "importance": 0.1}
    ]
    mock_get.return_value = mock_response

    assert validate_location("A random road") is False


@patch(
    "requests.get", side_effect=requests.exceptions.RequestException("Connection error")
)
def test_validate_location_request_exception(mock_get):
    """Test handling of a requests library exception."""
    assert validate_location("Some Place") is False
