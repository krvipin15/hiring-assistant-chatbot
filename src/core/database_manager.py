#!/usr/bin/env python3
"""
database_manager.py

Provides the `DatabaseManager` class for securely managing candidate data in a
SQLite database. Sensitive fields (phone number, email, and location) are
encrypted using the `EncryptionManager` before storage.

The class creates a `candidates` table if it does not already exist and allows
insertion of candidate records with encrypted fields and serialized technical
responses.

Classes
-------
DatabaseManager
    Handles SQLite operations for candidate records with encryption support.

Raises
------
RuntimeError
    If saving a candidate record fails due to encryption or database errors.

Examples
--------
>>> from database_manager import DatabaseManager
>>> db = DatabaseManager()
>>> db.save_candidate(
...     {
...         "name": "Alice Smith",
...         "phone_number": "+15551234567",
...         "email": "alice.smith@example.com",
...         "current_location": "San Francisco",
...         "experience_years": 4,
...         "desired_positions": "Backend Developer",
...         "tech_stack": "Python, FastAPI, PostgreSQL"
...     },
...     {"coding_challenge": "Passed", "system_design": "Pending"}
... )
"""

import json
import sqlite3
from loguru import logger
from typing import Dict, Any
from datetime import datetime
from src.core.encryption_handler import EncryptionManager


class DatabaseManager:
    """
    Manager for candidate database operations with encryption for sensitive fields.
    """

    def __init__(self, db_path: str = "candidates.db") -> None:
        """
        Initialize the DatabaseManager and ensure the candidates table exists.
        """
        logger.info(f"Initializing DatabaseManager with db_path: {db_path}")
        self.db_path = db_path
        self.encryption_manager = EncryptionManager()
        self._create_table()

    def _create_table(self) -> None:
        """
        Create the candidates table if it does not already exist.
        """
        logger.info(f"Ensuring 'candidates' table exists in {self.db_path}")
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                logger.info("Table 'candidates' is ready.")
        except sqlite3.Error as e:
            logger.exception(f"Error creating table in {self.db_path}: {e}")
            raise

    def save_candidate(
        self, candidate_data: Dict[str, Any], technical_responses: Dict[str, Any]
    ) -> None:
        """
        Save candidate data to the database, encrypting sensitive fields.
        """
        candidate_name = candidate_data.get("name", "N/A")
        logger.info(f"Attempting to save candidate data for: {candidate_name}")
        try:
            encrypted_phone = self.encryption_manager.encrypt(
                candidate_data.get("phone_number", "")
            )
            encrypted_email = self.encryption_manager.encrypt(
                candidate_data.get("email", "")
            )
            encrypted_location = self.encryption_manager.encrypt(
                candidate_data.get("current_location", "")
            )

            data = (
                datetime.now().isoformat(),
                candidate_data.get("name", ""),
                encrypted_phone,
                encrypted_email,
                encrypted_location,
                int(candidate_data.get("experience_years", 0)),
                candidate_data.get("desired_positions", ""),
                candidate_data.get("tech_stack", ""),
                json.dumps(technical_responses),
            )

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO candidates
                    (date_time, name, phone_number, email, current_location, experience_years,
                     desired_positions, tech_stack, technical_responses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    data,
                )
                conn.commit()
                logger.info(f"Successfully saved candidate: {candidate_name}")

        except Exception as e:
            logger.exception(f"Error saving candidate {candidate_name}: {e}")
            raise RuntimeError(f"Error saving candidate: {e}") from e
