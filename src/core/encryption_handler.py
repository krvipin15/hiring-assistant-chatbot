#!/usr/bin/env python3
"""
Manager for symmetric encryption of text using Fernet.

Attributes
----------
cipher_suite : Fernet
    Fernet cipher object initialized with the environment key.

Raises
------
ValueError
    If `ENCRYPTION_KEY` is missing or invalid.

Examples
--------
>>> from encryption_manager import EncryptionManager
>>> manager = EncryptionManager()
>>> ciphertext = manager.encrypt("hello world")
>>> print(ciphertext)
gAAAAABk...
"""

import os
from loguru import logger
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()


class EncryptionManager:
    """
    Manager for symmetric encryption and decryption of text using Fernet.
    """

    def __init__(self) -> None:
        """
        Initialize the EncryptionManager with a Fernet cipher suite.

        Notes
        -----
        - Uses the `ENCRYPTION_KEY` environment variable.
        - The key must be a 32-byte, base64 URL-safe string.
        - Raises an error if the key is missing or invalid.
        """
        logger.info("Initializing EncryptionManager.")
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            logger.error("ENCRYPTION_KEY not found in environment variables.")
            raise ValueError("ENCRYPTION_KEY not found in environment variables")

        try:
            self.cipher_suite = Fernet(key.encode())
            logger.info("EncryptionManager initialized successfully.")
        except Exception as e:
            logger.exception("Invalid ENCRYPTION_KEY format.")
            raise ValueError(
                "Invalid ENCRYPTION_KEY format. Must be a 32-byte base64 URL-safe string."
            ) from e

    def encrypt(self, text: str | None) -> str:
        """
        Encrypt text and return a base64-encoded string.

        Parameters
        ----------
        text : str or None
            The plaintext string to encrypt. If `None` or empty, returns an empty string.

        Returns
        -------
        str
            The encrypted text, encoded as a UTF-8 base64 string.

        Raises
        ------
        Exception
            If encryption fails for any reason.

        Notes
        -----
        - Fernet provides both encryption and authentication, ensuring ciphertext
          cannot be modified without detection.
        """
        if not text:
            return ""

        logger.debug("Encrypting text.")
        try:
            encrypted_text = self.cipher_suite.encrypt(text.encode())
            logger.debug("Text encrypted successfully.")
            return encrypted_text.decode()
        except Exception as e:
            logger.exception("An error occurred during encryption.")
            raise
