#!/usr/bin/env python3
"""
decrypt_database.py

This script reads candidate records from the encrypted database (`candidates.db`),
decrypts sensitive fields using the Fernet key defined in the environment
variable `ENCRYPTION_KEY`, and saves the fully decrypted records into a new
SQLite database (`decrypt_candidates.db`).

Functions
---------
decrypt(text: str | None) -> str
    Decrypts the given text and returns the decrypted string.
migrate_data() -> None
    Reads from the source database, decrypts sensitive fields, and inserts
    the records into the target database.

Raises
------
ValueError
    If the decryption key is invalid or if there is an error during decryption.
"""

import os
import sqlite3
from loguru import logger
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()


class DecryptionManager:
    """
    Handles decryption of sensitive data using Fernet symmetric encryption.
    """

    def __init__(self) -> None:
        """
        Initialize the DecryptionManager with the encryption key from
        environment variables.

        Raises
        ------
        ValueError
            If `ENCRYPTION_KEY` is missing or invalid.
        """
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            logger.error("ENCRYPTION_KEY not found in environment variables")
            raise ValueError("ENCRYPTION_KEY not found in environment variables")

        try:
            self.cipher_suite = Fernet(key.encode())
        except Exception as e:
            logger.exception(
                "Invalid ENCRYPTION_KEY format. Must be a 32-byte base64 URL-safe string."
            )
            raise ValueError(
                "Invalid ENCRYPTION_KEY format. Must be a 32-byte base64 URL-safe string."
            ) from e

    def decrypt(self, text: str | None) -> str:
        """
        Decrypt a given text string.

        Parameters
        ----------
        text : str or None
            The text to decrypt. If None or empty, an empty string is returned.

        Returns
        -------
        str
            The decrypted string. If decryption fails, the original text is returned.

        Notes
        -----
        This method logs a warning if decryption fails.
        """
        if not text:
            return ""
        try:
            decrypted_text = self.cipher_suite.decrypt(text.encode())
            return decrypted_text.decode()
        except Exception as e:
            logger.warning(
                f"Decryption failed for text: {text}. Returning original text. Error: {e}"
            )
            return text


class DatabaseDecryptor:
    """
    Manages the decryption and migration of candidate data from an encrypted
    SQLite database to a new decrypted database.
    """

    def __init__(
        self, source_db: str = "candidates.db", target_db: str = "decrypt_candidates.db"
    ) -> None:
        """
        Initialize the DatabaseDecryptor.

        Parameters
        ----------
        source_db : str, optional
            Path to the source encrypted database (default is "candidates.db").
        target_db : str, optional
            Path to the target decrypted database (default is "decrypt_candidates.db").
        """
        logger.info(
            f"Initializing DatabaseDecryptor with source '{source_db}' and target '{target_db}'."
        )
        self.source_db = source_db
        self.target_db = target_db
        self.decryption_manager = DecryptionManager()
        self._create_target_table()

    def _create_target_table(self) -> None:
        """
        Create the `candidates` table in the target database if it does not exist.

        The table schema matches the source but stores decrypted values for
        sensitive fields.
        """
        logger.info(
            f"Creating table 'candidates' in target database '{self.target_db}' if it doesn't exist."
        )
        with sqlite3.connect(self.target_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_time TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    email TEXT NOT NULL,
                    current_location TEXT NOT NULL,
                    experience_years INTEGER NOT NULL,
                    desired_positions TEXT NOT NULL,
                    tech_stack TEXT NOT NULL,
                    technical_responses_json TEXT NOT NULL
                )
                """
            )
            conn.commit()
        logger.info("Table 'candidates' created successfully.")

    def migrate_data(self) -> None:
        """
        Migrate and decrypt candidate records from the source to the target database.

        The method reads rows from the source database, decrypts sensitive fields
        (phone number, email, and current location), and inserts them into the
        target database.

        Notes
        -----
        - Non-sensitive fields are copied as-is.
        - Logs the total number of records migrated.
        """
        logger.info(
            f"Starting data migration from '{self.source_db}' to '{self.target_db}'."
        )
        with (
            sqlite3.connect(self.source_db) as source_conn,
            sqlite3.connect(self.target_db) as target_conn,
        ):
            source_cursor = source_conn.cursor()
            target_cursor = target_conn.cursor()

            source_cursor.execute("SELECT * FROM candidates")
            rows = source_cursor.fetchall()
            logger.info(f"Found {len(rows)} records to migrate.")

            for row in rows:
                (
                    id,
                    date_time,
                    name,
                    phone_number,
                    email,
                    current_location,
                    experience_years,
                    desired_positions,
                    tech_stack,
                    technical_responses_json,
                ) = row

                # Decrypt sensitive fields
                decrypted_phone = self.decryption_manager.decrypt(phone_number)
                decrypted_email = self.decryption_manager.decrypt(email)
                decrypted_location = self.decryption_manager.decrypt(current_location)

                # Insert into new DB
                target_cursor.execute(
                    """
                    INSERT INTO candidates
                    (date_time, name, phone_number, email, current_location,
                     experience_years, desired_positions, tech_stack, technical_responses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        date_time,
                        name,
                        decrypted_phone,
                        decrypted_email,
                        decrypted_location,
                        experience_years,
                        desired_positions,
                        tech_stack,
                        technical_responses_json,
                    ),
                )

            target_conn.commit()
        logger.info("Data migration completed successfully.")


def main() -> None:
    """
    Main entry point for the script.
    Initializes logging and runs the database decryption process.
    """
    logger.add("decryption.log", rotation="10 MB", level="INFO")
    logger.info("Starting database decryption process.")
    try:
        decryptor = DatabaseDecryptor()
        decryptor.migrate_data()
        logger.info("Decryption complete. New database created: decrypt_candidates.db")
    except Exception as e:
        logger.exception("An error occurred during the decryption process.")


if __name__ == "__main__":
    main()
