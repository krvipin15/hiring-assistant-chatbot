import pytest
from unittest.mock import patch, MagicMock
from src.core.conversation_manager import ConversationManager, ConversationState


@pytest.fixture
def mock_model_manager():
    with patch("src.core.conversation_manager.ModelManager") as mock_mm:
        mock_instance = MagicMock()
        mock_instance.generate_response.return_value = "Mocked AI Response"
        mock_mm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_db_manager():
    with patch("src.core.conversation_manager.DatabaseManager") as mock_dm:
        mock_instance = MagicMock()
        mock_dm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_validators():
    with (
        patch("src.core.conversation_manager.validate_email", return_value=True),
        patch("src.core.conversation_manager.validate_phone", return_value=True),
        patch("src.core.conversation_manager.validate_location", return_value=True),
    ):
        yield


@pytest.fixture
def manager(mock_model_manager, mock_db_manager, mock_validators):
    """Fixture to get a ConversationManager instance with mocked dependencies."""
    return ConversationManager()


class TestConversationManager:
    def test_init(self, manager):
        assert manager.state == ConversationState.INTRODUCTION
        assert manager.candidate_data["name"] == ""

    def test_handle_message_introduction(self, manager):
        response = manager.handle_message("start")
        assert manager.state == ConversationState.COLLECTING_NAME
        assert "what's your full name?" in response.lower()

    def test_full_information_collection_flow(self, manager):
        # Name
        manager.state = ConversationState.COLLECTING_NAME
        response = manager.handle_message("John Doe")
        assert manager.state == ConversationState.COLLECTING_PHONE
        assert manager.candidate_data["name"] == "John Doe"
        assert "phone number" in response

        # Phone
        response = manager.handle_message("+1234567890")
        assert manager.state == ConversationState.COLLECTING_EMAIL
        assert manager.candidate_data["phone_number"] == "+1234567890"
        assert "email address" in response

        # Email
        response = manager.handle_message("john.doe@example.com")
        assert manager.state == ConversationState.COLLECTING_LOCATION
        assert manager.candidate_data["email"] == "john.doe@example.com"
        assert "current location" in response

        # Location
        response = manager.handle_message("New York, USA")
        assert manager.state == ConversationState.COLLECTING_EXPERIENCE
        assert manager.candidate_data["current_location"] == "New York, USA"
        assert "experience" in response

        # Experience
        response = manager.handle_message("5")
        assert manager.state == ConversationState.COLLECTING_POSITIONS
        assert manager.candidate_data["experience_years"] == 5
        assert "positions" in response

        # Positions
        response = manager.handle_message("Backend Developer")
        assert manager.state == ConversationState.COLLECTING_TECH_STACK
        assert manager.candidate_data["desired_positions"] == "Backend Developer"
        assert "programming languages" in response

        # Tech Stack
        manager.model_manager.generate_response.return_value = "Generated Question 1"
        response = manager.handle_message("Python, SQL")
        assert manager.state == ConversationState.TECHNICAL_SCREENING
        assert manager.candidate_data["tech_stack"] == "Python, SQL"
        assert "Generated Question 1" in response
        assert "Let's start with **Python**" in response

    def test_invalid_name(self, manager):
        manager.state = ConversationState.COLLECTING_NAME
        response = manager.handle_message("J")  # Invalid name
        assert manager.state == ConversationState.COLLECTING_NAME
        assert "full name" in response

    @patch("src.core.conversation_manager.ConversationManager._is_skip_response", return_value=False)
    @patch("src.core.conversation_manager.ConversationManager._assess_response_quality", return_value=False)
    def test_technical_screening_flow(self, mock_assess, mock_skip, manager):
        # Setup state for technical screening
        manager.state = ConversationState.TECHNICAL_SCREENING
        manager.tech_stack_list = ["Python", "Java"]
        manager.candidate_data["experience_years"] = 3
        manager.tech_assessments = {
            "Python": {"questions": [], "responses": [], "current_question": 0},
            "Java": {"questions": [], "responses": [], "current_question": 0},
        }
        manager.model_manager.generate_response.side_effect = [
            "Python Q1", "Python Q2", "Python Q3", "Python Q4", "Python Q5",
            "Java Q1", "Java Q2", "Java Q3", "Java Q4", "Java Q5",
            "Final Summary"
        ]

        # This test needs to be more realistic about the conversation flow
        # 1. User provides tech stack, which generates the first question
        manager.state = ConversationState.COLLECTING_TECH_STACK
        response = manager.handle_message("Python, Java")
        assert "Let's start with **Python**" in response
        assert "Python Q1" in response # First question is generated here

        # 2. Now, we are in the technical screening state
        assert manager.state == ConversationState.TECHNICAL_SCREENING

        # 3. Loop through the remaining Python questions
        for i in range(1, 5):
            response = manager.handle_message(f"Answer to Python Q{i}")
            assert f"Next Python question" in response
            assert f"Python Q{i+1}" in response
        
        # 4. Answer the last Python question
        response = manager.handle_message("Answer to Python Q5")
        assert "Excellent work on Python!" in response
        assert "Now let's move to **Java**" in response
        assert "Java Q1" in response

        # Check state after Python questions
        assert manager.current_tech_index == 1
        assert manager.current_tech_question_count == 0

        # Go through 5 questions for Java
        for i in range(5):
            response = manager.handle_message(f"Answer to Java Q{i+1}")
            if i < 4:
                assert f"Next Java question" in response
                assert f"Java Q{i+2}" in response
            else:
                # Last Java question, should complete the screening
                assert (
                    "You've completed the comprehensive technical screening" in response
                )

        assert manager.state == ConversationState.COMPLETED
        manager.db_manager.save_candidate.assert_called_once()

    def test_handle_exit_command(self, manager, mock_db_manager):
        manager.candidate_data["name"] = "Test User"
        response = manager.handle_message("exit")
        assert "Your information has been saved" in response
        assert manager.state == ConversationState.COMPLETED
        mock_db_manager.save_candidate.assert_called_once()

    @pytest.mark.parametrize(
        "tech_stack_input, expected_list",
        [
            ("Python, JavaScript, React", ["Python", "Javascript", "React"]),
            ("Java and Spring", ["Java", "Spring"]),
            ("C++ / C#", ["C++", "C#"]),
            ("  Go; Rust  ", ["Go", "Rust"]),
        ],
    )
    def test_parse_tech_stack(self, manager, tech_stack_input, expected_list):
        assert manager._parse_tech_stack(tech_stack_input) == expected_list
