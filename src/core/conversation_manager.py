#!/usr/bin/env python3
"""
conversation_manager.py

Provides the `ConversationManager` class for managing multi-turn conversations
in the hiring assistant chatbot. This class orchestrates the conversation flow,
handles state management, validates user inputs, and saves candidate data.

The conversation follows a structured flow:
1. Introduction and basic information collection
2. Technical screening questions
3. Data validation and storage on exit

Classes
-------
ConversationManager
    Manages conversation state, flow, and data collection for candidate screening.

Examples
--------
>>> from conversation_manager import ConversationManager
>>> manager = ConversationManager()
>>> response = manager.handle_message("Hello")
>>> print(response)
"""

import re
from enum import Enum
from loguru import logger
from typing import Dict, List, Any, Optional
from src.core.model_manager import ModelManager
from src.core.database_manager import DatabaseManager
from src.core.data_validator import validate_email, validate_phone, validate_location


class ConversationState(Enum):
    """Enumeration of possible conversation states."""
    INTRODUCTION = "introduction"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_PHONE = "collecting_phone"
    COLLECTING_EMAIL = "collecting_email"
    COLLECTING_LOCATION = "collecting_location"
    COLLECTING_EXPERIENCE = "collecting_experience"
    COLLECTING_POSITIONS = "collecting_positions"
    COLLECTING_TECH_STACK = "collecting_tech_stack"
    TECHNICAL_SCREENING = "technical_screening"
    COMPLETED = "completed"


class ConversationManager:
    """
    Manages conversation flow and state for the hiring assistant chatbot.

    Attributes
    ----------
    model_manager : ModelManager
        Handles AI model interactions for generating responses.
    db_manager : DatabaseManager
        Manages database operations for storing candidate data.
    state : ConversationState
        Current state of the conversation flow.
    candidate_data : dict
        Collected candidate information.
    technical_responses : dict
        Candidate's responses to technical questions.
    conversation_history : list
        History of conversation turns for context.
    tech_stack_list : list
        Parsed list of technologies from candidate's tech stack.
    current_tech_index : int
        Current technology being assessed (0-based index).
    current_tech_question_count : int
        Number of questions asked for current technology.
    tech_assessments : dict
        Detailed assessment data for each technology.
    """

    def __init__(self) -> None:
        """Initialize the ConversationManager with required components."""
        logger.info("Initializing ConversationManager.")
        self.model_manager = ModelManager()
        self.db_manager = DatabaseManager()
        self.state = ConversationState.INTRODUCTION
        self.candidate_data: Dict[str, Any] = {"name": "", "phone_number": "", "email": "", "current_location": "",
                                               "experience_years": 0, "desired_positions": "", "tech_stack": ""}
        self.technical_responses: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, str]] = []
        self.tech_stack_list: List[str] = []
        self.current_tech_index: int = 0
        self.technical_questions: List[str] = []
        self.current_tech_question_count: int = 0
        self.tech_assessments: Dict[str, Dict[str, Any]] = {}

    def handle_message(self, user_input: str) -> str:
        """
        Process user input and return appropriate response based on conversation state.

        Parameters
        ----------
        user_input : str
            The user's input message.

        Returns
        -------
        str
            The chatbot's response message.
        """
        logger.info(f"Handling message in state: {self.state.value}")
        logger.debug(f"User input: {user_input}")
        user_input = user_input.strip()

        # Handle exit commands - save data and end conversation
        if user_input.lower() in ["exit", "quit", "stop", "end", "goodbye", "bye", "done"]:
            return self._handle_exit()

        response = ""

        try:
            if self.state == ConversationState.INTRODUCTION:
                response = self._handle_introduction(user_input)
            elif self.state == ConversationState.COLLECTING_NAME:
                response = self._handle_name_collection(user_input)
            elif self.state == ConversationState.COLLECTING_PHONE:
                response = self._handle_phone_collection(user_input)
            elif self.state == ConversationState.COLLECTING_EMAIL:
                response = self._handle_email_collection(user_input)
            elif self.state == ConversationState.COLLECTING_LOCATION:
                response = self._handle_location_collection(user_input)
            elif self.state == ConversationState.COLLECTING_EXPERIENCE:
                response = self._handle_experience_collection(user_input)
            elif self.state == ConversationState.COLLECTING_POSITIONS:
                response = self._handle_positions_collection(user_input)
            elif self.state == ConversationState.COLLECTING_TECH_STACK:
                response = self._handle_tech_stack_collection(user_input)
            elif self.state == ConversationState.TECHNICAL_SCREENING:
                response = self._handle_technical_screening(user_input)
            elif self.state == ConversationState.COMPLETED:
                response = self._handle_completed_state(user_input)
            else:
                logger.error(f"Unhandled conversation state: {self.state}")
                response = "I'm sorry, something went wrong. Please refresh to try again. " \
                            "If the issue persists, please contact support."

        except Exception as e:
            logger.exception(f"Error handling message in state {self.state.value}: {e}")
            response = "I apologize, but I encountered an error. " \
            "Please contact support if you are not able to continue with the next question."

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response if response is not None else ""})
        logger.debug(f"Assistant response: {response}")

        return response if response is not None else ""

    def _handle_exit(self) -> str:
        """Handle exit command by saving data if possible."""
        logger.info("Exit command received. Attempting to save data.")
        self.state = ConversationState.COMPLETED
        try:
            # Only save if we have at least basic information
            if self.candidate_data.get("name") and any(self.candidate_data.values()):
                self.db_manager.save_candidate(self.candidate_data, self.technical_responses)
                logger.info("Candidate data saved successfully on exit.")
                return (
                    f"Thank you for your time {self.candidate_data['name']}! Your information has been saved securely. "
                    "Our team will review your responses and get back to you soon. "
                    "Have a great day!"
                )
            else:
                logger.info("No significant data collected, so nothing was saved.")
                return (
                    "Thank you for visiting! Since we didn't collect complete information, "
                    "nothing was saved. Feel free to return anytime to complete the screening. "
                    "Have a great day!"
                )
        except Exception as e:
            logger.exception(f"Error saving data on exit: {e}")
            return (
                "Thank you for your time! There was a technical issue while saving your data, "
                "but our team has been notified. Have a great day!"
            )

    def _handle_introduction(self, user_input: str) -> Optional[str]:
        """Handle the introduction phase."""
        if user_input.lower() in ["hello", "hi", "hey", "start", "begin"]:
            logger.info("Transitioning state from INTRODUCTION to COLLECTING_NAME")
            self.state = ConversationState.COLLECTING_NAME
            return "Hello and welcome to TalentScout! I'm here to run a short initial screening to collect a few details and " \
                "ask some technical questions tailored to your skills. This should take about 10-15 minutes. To start, " \
                "what's your full name?"

    def _handle_name_collection(self, user_input: str) -> str:
        """Handle name collection phase."""
        if not re.match(r"^[a-zA-Z][a-zA-Z\s'’-]+$", user_input):
            logger.warning(f"Invalid name format received: {user_input}")
            return "Please provide a valid full name using letters only. Such as 'John Doe'."

        name_parts = [part for part in user_input.split() if len(part) > 1]
        if len(name_parts) < 2:
            logger.warning(f"Incomplete name received: {user_input}")
            return "Please provide your full name (first and last name). For example, 'Mike Smith'."

        self.candidate_data["name"] = user_input.title()
        logger.info(f"Collected name: {self.candidate_data['name']}")
        self.state = ConversationState.COLLECTING_PHONE
        logger.info("Transitioning state to COLLECTING_PHONE")
        return f"Nice to meet you, {self.candidate_data['name']}! Please provide your phone number including the country code e.g., +91 1122334455."

    def _handle_phone_collection(self, user_input: str) -> str:
        """Handle phone number collection phase."""
        phone = re.sub(r'[^\d+\-\s\(\)]', '', user_input)

        if validate_phone(phone):
            self.candidate_data["phone_number"] = phone
            logger.info(f"Collected phone number: {phone}")
            self.state = ConversationState.COLLECTING_EMAIL
            logger.info("Transitioning state to COLLECTING_EMAIL")
            return "Great! Provide your deliverable email address e.g., mikesmith@gmail.com."
        else:
            logger.warning(f"Invalid phone number received: {user_input}")
            return (
                "Validation failed! Please provide a valid phone number with country code."
            )

    def _handle_email_collection(self, user_input: str) -> str:
        """Handle email collection phase."""
        email = user_input.lower()

        if validate_email(email):
            self.candidate_data["email"] = email
            logger.info(f"Collected email: {email}")
            self.state = ConversationState.COLLECTING_LOCATION
            logger.info("Transitioning state to COLLECTING_LOCATION")
            return "Perfect! Next, what's your current location? (City, Country)"
        else:
            logger.warning(f"Invalid email received: {user_input}")
            return "Invalid! Please provide a valid email address (e.g., john.doe@mail.com)."

    def _handle_location_collection(self, user_input: str) -> str:
        """Handle location collection phase."""
        if len(user_input) < 2:
            logger.warning(f"Invalid location received (too short): {user_input}")
            return "Please provide your current location e.g., New York, USA."

        if validate_location(user_input):
            self.candidate_data["current_location"] = user_input
            logger.info(f"Collected and validated location: {user_input}")
            self.state = ConversationState.COLLECTING_EXPERIENCE
            logger.info("Transitioning state to COLLECTING_EXPERIENCE")
            return "Location verified! How many years of professional experience do you have?"
        else:
            logger.warning(f"Location validation failed for: {user_input}")
            return (
                "I couldn't verify that location. Please provide a valid city and country "
                "e.g., 'New Delhi, India'."
            )

    def _handle_experience_collection(self, user_input: str) -> str:
        """Handle experience collection phase."""
        try:
            experience = int(user_input)
            if 0 <= experience <= 30:
                self.candidate_data["experience_years"] = experience
                logger.info(f"Collected experience: {experience} years")
                self.state = ConversationState.COLLECTING_POSITIONS
                logger.info("Transitioning state to COLLECTING_POSITIONS")
                return (
                    "Excellent! What type of positions are you interested in? "
                    "(e.g., Python Developer, Backend Developer, Frontend Developer, etc.)"
                )
            else:
                logger.warning(f"Unrealistic experience years received: {user_input}")
                return "Please provide a realistic number of years (0-30)."
        except ValueError:
            logger.warning(f"Invalid input for experience (not a number): {user_input}")
            return "Please provide a valid number for years of experience."

    def _handle_positions_collection(self, user_input: str) -> str:
        """Handle desired positions collection phase."""
        if len(user_input) < 3:
            logger.warning(f"Desired positions input too short: {user_input}")
            return "Please describe the type of positions you're interested in."

        self.candidate_data["desired_positions"] = user_input
        logger.info(f"Collected desired positions: {user_input}")
        self.state = ConversationState.COLLECTING_TECH_STACK
        logger.info("Transitioning state to COLLECTING_TECH_STACK")
        return (
            "Great! Please list the programming languages, frameworks, databases, and tools you are proficient in. "
            "(e.g., Python, JavaScript, React, Node.js, PostgreSQL, etc.)"
        )

    def _handle_tech_stack_collection(self, user_input: str) -> str:
        """Handle tech stack collection phase."""
        if len(user_input) < 3:
            logger.warning(f"Tech stack input too short: {user_input}")
            return "Please describe your technical skills and technologies you work with."

        self.candidate_data["tech_stack"] = user_input
        logger.info(f"Collected tech stack: {user_input}")

        self.tech_stack_list = self._parse_tech_stack(user_input)
        logger.info(f"Parsed tech stack: {self.tech_stack_list}")

        if not self.tech_stack_list:
            logger.warning("Could not parse any technologies from the input.")
            return "I couldn't identify specific technologies from your input. Please list them more clearly (e.g., Python, JavaScript, React, PostgreSQL)."

        for tech in self.tech_stack_list:
            self.tech_assessments[tech] = {
                "questions": [],
                "responses": [],
                "current_question": 0
            }

        self.state = ConversationState.TECHNICAL_SCREENING
        self.current_tech_index = 0
        self.current_tech_question_count = 0
        logger.info("Transitioning state to TECHNICAL_SCREENING")

        current_tech = self.tech_stack_list[0]
        question = self._generate_technical_question(current_tech, 1)

        return (
            f"Perfect! I can see you work with {', '.join(self.tech_stack_list)}. "
            f"Now let's dive into some technical questions to better understand your expertise.\n\n"
            f"Let's start with **{current_tech}**:\n\n{question}"
        )

    def _parse_tech_stack(self, tech_stack: str) -> List[str]:
        """
        Parse tech stack string into normalized list of technologies.
        """
        raw_tokens = re.split(r",|\band\b|/|&", tech_stack, flags=re.IGNORECASE)
        technologies = []
        for token in raw_tokens:
            tech = token.strip(" .;:- ").strip()
            if not tech:
                continue

            if tech.isupper():
                normalized = tech
            elif "." in tech:
                parts = tech.split(".")
                normalized = parts[0].capitalize() + "." + ".".join(parts[1:])
            else:
                normalized = tech.capitalize()
            technologies.append(normalized)

        seen = set()
        return [t for t in technologies if not (t in seen or seen.add(t))]

    def _generate_technical_question(self, technology: str, question_number: int) -> str:
        """
        Generate a technical question for a specific technology.
        """
        experience_years = self.candidate_data.get("experience_years", 0)
        experience_level = self._get_experience_level(experience_years)
        logger.info(f"Generating Q{question_number} for {technology} at {experience_level} level.")

        tech_assessment = self.tech_assessments.get(technology, {})
        previous_responses = tech_assessment.get("responses", [])

        context_prompt = f"""Generate a {experience_level}-level technical question about {technology} for someone with {experience_years} years of experience.

This is question #{question_number} out of 5 for {technology}.

Previous responses from candidate: {previous_responses[-2:] if len(previous_responses) >= 2 else previous_responses}

Question guidelines:
- Ask to explain a specific concept, definition or process instead of asking to write code
- Difficulty should match {experience_level} level ({experience_years} years experience)
- Focus on real-world application (40%) as well as theoretical knowledge (60%)
- Keep it concise but specific
- Should be answerable in 2-4 sentences

Generate only the question, no additional text."""

        try:
            question = self.model_manager.generate_response(context_prompt, self.conversation_history)
            logger.info(f"Generated question: {question}")
            return question.strip()
        except Exception as e:
            logger.exception(f"Error generating question for {technology}: {e}")
            return "Unable to generate question, please try contacting support."

    def _handle_technical_screening(self, user_input: str) -> str:
        """Handle technical screening questions with follow-up logic."""
        if not self.tech_stack_list:
            logger.error("Technical screening attempted with an empty tech stack list.")
            return "There was an error with the technical screening. Let me restart the process."

        current_tech = self.tech_stack_list[self.current_tech_index]
        tech_assessment = self.tech_assessments[current_tech]

        tech_assessment["responses"].append(user_input)
        response_key = f"{current_tech}_q{self.current_tech_question_count + 1}"
        self.technical_responses[response_key] = user_input
        logger.info(f"Stored response for {response_key}")

        self.current_tech_question_count += 1

        if self.current_tech_question_count < 5:
            needs_followup = self._assess_response_quality(user_input)
            if needs_followup and len(tech_assessment["responses"]) > 0:
                logger.info("Response quality warrants a follow-up question.")
                followup_question = self._generate_followup_question(current_tech, user_input)
                return f"That's interesting! Let me ask a follow-up:\n\n{followup_question}"
            elif self._is_skip_response(user_input):
                logger.info("AI classified this as a skip response.")
                question = self._generate_technical_question(current_tech, self.current_tech_question_count + 1)
                return f"No problem! Let's move on to the next question:\n\n{question}"
            else:
                logger.info("Proceeding to the next technical question.")
                question = self._generate_technical_question(current_tech, self.current_tech_question_count + 1)
                return f"Great! Next {current_tech} question:\n\n{question}"
        else:
            logger.info(f"Completed all questions for {current_tech}.")
            self.current_tech_index += 1
            self.current_tech_question_count = 0

            if self.current_tech_index < len(self.tech_stack_list):
                next_tech = self.tech_stack_list[self.current_tech_index]
                logger.info(f"Moving to next technology: {next_tech}")
                question = self._generate_technical_question(next_tech, 1)
                return (
                    f"Excellent work on {current_tech}! Now let's move to **{next_tech}**:\n\n{question}"
                )
            else:
                logger.info("All technologies assessed. Completing screening.")
                return self._complete_technical_screening()

    def _is_skip_response(self, user_input: str) -> bool:
        """
        Use AI to decide whether the response means 'skip / unable to answer'.
        """
        prompt = f"""
        Determine if the following candidate response indicates that they are skipping,
        unable to answer, or do not know the answer.

        Response: "{user_input}"

        Answer with ONLY 'yes' if it is a skip/unable-to-answer,
        or 'no' if it is a valid attempt at answering.
        """
        try:
            result = self.model_manager.generate_response(prompt, [])
            return result.strip().lower().startswith("y")
        except Exception as e:
            logger.exception(f"AI error while classifying skip response: {e}")
            # Fallback: assume it's not a skip
            return False

    def _assess_response_quality(self, response: str) -> bool:
        """
        Assess if a response warrants a follow-up question.
        """
        response_lower = response.lower()
        if len(response.split()) < 10:
            logger.info("Response is too short for a follow-up.")
            return False

        technical_indicators = [
            'implement', 'architecture', 'design', 'optimize', 'performance',
            'scale', 'database', 'api', 'framework', 'algorithm', 'solution',
            'challenge', 'problem', 'approach', 'method', 'strategy'
        ]
        indicator_count = sum(1 for indicator in technical_indicators if indicator in response_lower)
        logger.debug(f"Found {indicator_count} technical indicators in response.")
        return indicator_count >= 2

    def _generate_followup_question(self, technology: str, previous_response: str) -> str:
        """
        Generate a follow-up question based on the candidate's response.
        """
        logger.info(f"Generating follow-up question for {technology}.")
        context_prompt = f"""Based on this candidate's response about {technology}:

"{previous_response}"

Generate a relevant follow-up question that digs deeper into their technical understanding. The question should:
- Build upon what they just mentioned
- Ask for more specific technical details
- Explore implementation challenges or trade-offs
- Be concise and focused

Generate only the follow-up question, no additional text."""

        try:
            followup = self.model_manager.generate_response(context_prompt, self.conversation_history[-4:])
            logger.info(f"Generated follow-up: {followup}")
            return followup.strip()
        except Exception as e:
            logger.exception(f"Error generating follow-up for {technology}: {e}")
            return f"Can you elaborate more on the technical implementation details of what you just described?"

    def _complete_technical_screening(self) -> str:
        """Complete the technical screening and save data."""
        logger.info("Completing technical screening and saving data.")
        try:
            all_responses = {
                **self.technical_responses,
                "tech_assessments": self.tech_assessments
            }
            self.db_manager.save_candidate(self.candidate_data, all_responses)
            self.state = ConversationState.COMPLETED
            logger.info("Transitioning state to COMPLETED.")

            name = self.candidate_data.get("name", "")
            return (
                f"Outstanding work, {name}! You've completed the comprehensive technical screening "
                f"covering {', '.join(self.tech_stack_list)}.\n\n"
                f"Your responses have been saved securely and show strong technical knowledge across "
                f"multiple technologies. Our technical team will review your detailed responses and "
                f"get back to you within 2-3 business days.\n\n"
                f"Thank you for your time and thorough answers! Do you have any questions about "
                f"the role or our company?"
            )
        except Exception as e:
            logger.exception(f"Error saving candidate data at completion: {e}")
            return (
                "Thank you for completing the comprehensive technical screening! However, there was "
                "a technical issue saving your data. Please contact our HR team directly with your information."
            )

    def _handle_completed_state(self, user_input: str) -> str:
        """Handle messages after screening is completed."""
        logger.info(f"Handling post-completion message: {user_input}")
        context_prompt = (
            f"The candidate {self.candidate_data.get('name', '')} has completed their screening. "
            f"They are asking: '{user_input}'. Provide a helpful, professional response about "
            f"the hiring process, company information, or next steps. Keep it concise and friendly."
        )

        response = self.model_manager.generate_response(
            context_prompt,
            self.conversation_history[-6:] if self.conversation_history else []
        )
        return response + "\n\nIf you have any other questions, feel free to ask or contact our HR team directly!"

    def get_conversation_state(self) -> Dict[str, Any]:
        """
        Get current conversation state information.
        """
        return {
            "state": self.state.value,
            "candidate_data": self.candidate_data,
            "technical_responses": self.technical_responses,
            "completion_percentage": self._calculate_completion_percentage()
        }

    def _calculate_completion_percentage(self) -> int:
        """Calculate completion percentage of the screening process."""
        if self.state == ConversationState.COMPLETED:
            return 100
        elif self.state == ConversationState.TECHNICAL_SCREENING:
            base_percentage = 60
            if self.tech_stack_list:
                total_questions = len(self.tech_stack_list) * 5
                answered_questions = len(self.technical_responses)
                tech_percentage = (answered_questions / total_questions) * 40 if total_questions > 0 else 0
                return int(base_percentage + tech_percentage)
            else:
                return base_percentage
        else:
            total_fields = len(self.candidate_data)
            completed_fields = sum(1 for value in self.candidate_data.values() if value)
            return int((completed_fields / total_fields) * 60) if total_fields > 0 else 0

    def _get_experience_level(self, years: int) -> str:
        """Determine experience level based on years."""
        if years <= 2:
            return "Junior"
        elif years <= 5:
            return "Mid-Level"
        elif years <= 10:
            return "Senior"
        else:
            return "Principal/Staff"

    def get_technical_progress(self) -> Dict[str, Any]:
        """
        Get detailed technical screening progress.
        """
        if not self.tech_stack_list:
            return {"technologies": [], "current_tech": None, "progress": {}}

        progress = {}
        for i, tech in enumerate(self.tech_stack_list):
            tech_responses = [k for k in self.technical_responses.keys() if k.startswith(tech)]
            progress[tech] = {
                "completed": len(tech_responses),
                "total": 5,
                "is_current": i == self.current_tech_index,
                "is_completed": len(tech_responses) >= 5
            }

        current_tech = self.tech_stack_list[self.current_tech_index] if self.current_tech_index < len(self.tech_stack_list) else None
        return {
            "technologies": self.tech_stack_list,
            "current_tech": current_tech,
            "current_tech_index": self.current_tech_index,
            "progress": progress
        }
