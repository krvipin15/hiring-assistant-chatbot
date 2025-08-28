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
            logger.debug(f"Raw model response: {content}")
            return self._clean_output(content) if content else "I'm sorry, I couldn’t generate a response."


        except Exception as e:
            logger.exception(f"Error generating response: {e}")
            return "\n\nSomething went wrong while generating a response through API, please wait and restart the conversation!"

    def _clean_output(self, content: str) -> str:
        """
        Clean the raw model output to remove reasoning traces or meta text.
        Keeps only the assistant's final message.
        """
        if not content:
            return ""

        # Prefer content after "assistantfinal"
        if "assistantfinal" in content:
            content = content.split("assistantfinal", 1)[1]

        # Remove "analysis..." sections if present
        if "analysis" in content and "assistantfinal" not in content:
            parts = content.split("analysis", 1)
            content = parts[-1]

        # Strip quotes/whitespace
        return content.strip().strip('"').strip()

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
You are TalentScout’s AI hiring assistant. Your job is to run structured,
efficient, and professional technical screenings.

CORE RULES:
1. **Professional & Concise**: Use a warm but efficient tone. Responses must be
   1–3 sentences. Never include hidden reasoning, meta text, or formatting like
   'analysis' or 'assistantfinal'.
2. **One Step at a Time**: Ask exactly one question per turn. Never generate
   multiple questions at once.
3. **Tailored Questions**: Match technical questions to the candidate’s
   experience level and stated tech stack. Focus on practical concepts,
   definitions, or processes, not trivia.
4. **Clarity**: If the candidate’s response is unclear or off-topic, politely
   ask for clarification or redirect to the current stage.
5. **Security Assurance**: Remind candidates their information is private and
   secure if they show concern.
6. **Output Discipline**: Output only what should be said to the candidate.
   Do not include explanations of how you constructed the answer, chain-of-thought,
   or system notes. Generate only the final message you would send.
"""
