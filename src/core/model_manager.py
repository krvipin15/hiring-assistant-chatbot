#!/usr/bin/env python3
"""
model_manager.py

Provides the `ModelManager` class for managing prompt construction and
interfacing with the OpenRouter API for chat-based responses using
OpenAI-compatible models.

Classes
-------
ModelManager
    Handles the initialization of the OpenRouter client, constructs prompts,
    manages conversation history, and generates responses from chat models.

Functions
---------
generate_response(self, user_prompt: str, history: List[Dict[str, str]] = []) -> str
    Generates a response from the chat model based on the user's prompt and optional
    conversation history. Prepends a system prompt to guide the assistant's behavior.
    Handles errors gracefully and logs relevant information. Raises a ValueError if
    the `OPENROUTER_MODEL` environment variable is not set.

get_system_prompt(self) -> str
    Returns the system prompt string that defines the assistant's behavior, ensuring
    professionalism, efficiency, adaptability to candidate experience, and information
    security. This prompt is always prepended to the conversation.

Raises
------
ValueError
    If `OPENROUTER_MODEL` environment variable is not set.

Examples
--------
>>> from model_manager import ModelManager
>>> model = ModelManager()
>>> response = model.generate_response("Hello, who are you?")
>>> print(response)
"I’m TalentScout’s AI hiring assistant..."
"""

import os
from openai import OpenAI
from typing import List, Dict
from loguru import logger
from dotenv import load_dotenv
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

# Load environment variables
load_dotenv()


class ModelManager:
    """
    Manager for generating responses from OpenRouter chat models.

    Attributes
    ----------
    client : OpenAI
        OpenRouter client for sending chat completion requests.
    """

    def __init__(self) -> None:
        """
        Initialize the ModelManager with an OpenRouter client.

        Notes
        -----
        This constructor uses the environment variable `OPENROUTER_API_KEY`
        to authenticate with OpenRouter. Make sure it is set before instantiation.
        """
        logger.info("Initializing ModelManager.")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        logger.info("ModelManager initialized successfully.")

    def generate_response(
        self, user_prompt: str, history: List[Dict[str, str]] = []
    ) -> str:
        """
        Generate a model response based on a user prompt and optional conversation history.

        Parameters
        ----------
        user_prompt : str
            The latest message from the user.
        history : list of dict, optional
            A list of prior conversation messages. Each dictionary should contain:
            - "role": str, one of {"user", "assistant"}
            - "content": str, the message text

        Returns
        -------
        str
            The model-generated response text. Returns a fallback error message
            if response generation fails.

        Raises
        ------
        ValueError
            If the `OPENROUTER_MODEL` environment variable is not set.

        Notes
        -----
        - System messages are always prepended to guide the assistant's behavior.
        - Response generation uses `max_tokens=512` and `temperature=0.3`.
        """
        logger.info("Generating model response.")
        logger.debug(f"User prompt: {user_prompt}")
        try:
            messages: List = [
                ChatCompletionSystemMessageParam(
                    role="system", content=self.get_system_prompt()
                )
            ]

            if history:
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(
                            ChatCompletionUserMessageParam(
                                role="user", content=msg["content"]
                            )
                        )
                    elif msg["role"] == "assistant":
                        messages.append(
                            ChatCompletionAssistantMessageParam(
                                role="assistant", content=msg["content"]
                            )
                        )

            messages.append(
                ChatCompletionUserMessageParam(role="user", content=user_prompt)
            )

            model_name = os.getenv("OPENROUTER_MODEL")
            if not model_name:
                logger.error("OPENROUTER_MODEL environment variable is not set.")
                raise ValueError("OPENROUTER_MODEL environment variable is not set.")

            logger.info(f"Requesting completion from model: {model_name}")
            completion = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=512,
                temperature=0.3,
            )

            content = completion.choices[0].message.content
            logger.info("Successfully generated model response.")
            logger.debug(f"Model response: {content}")
            return (
                content.strip()
                if content
                else "I'm sorry, I couldn’t generate a response."
            )

        except Exception as e:
            logger.exception(f"Error generating response: {e}")
            return "Something went wrong while generating a response."

    def get_system_prompt(self) -> str:
        """
        Get the main system prompt for the AI model.

        Returns
        -------
        str
            The system prompt string that defines assistant behavior.

        Notes
        -----
        The system prompt ensures the assistant:
        - Maintains a professional and encouraging tone.
        - Adapts technical questions based on candidate experience.
        - Redirects off-topic responses.
        - Reassures candidates about information security.
        """
        return """
You are a professional and friendly TalentScout's AI hiring assistant.
Your primary goal is to conduct an efficient, positive, and structured initial screening for technical candidates.

KEY INSTRUCTIONS:
1.  **Be Professional & Efficient:** Maintain a warm, encouraging tone. Keep responses concise (1-3 sentences) and clear. Ask one question at a time.
2.  **Tailor Technical Questions:** Base questions on the candidate's specific experience and tech stack. Focus on real-world, practical problem-solving, not just trivia. Ask insightful follow-up questions to understand their thought process.
3.  **Guide the Candidate:** If a response is unclear, politely ask for clarification. If the conversation goes off-topic, gently redirect it back to the screening process.
4.  **Ensure Security:** Reassure candidates that their information is kept secure.

EXAMPLES OF GOOD RESPONSES:
- "Thanks for sharing that, [Name]! That sounds like an interesting project. Now, could you tell me..."
- "I can see you have solid experience with [technology]. Let's move on to..."
- "Great example! That shows good problem-solving skills. One more question..."
"""
