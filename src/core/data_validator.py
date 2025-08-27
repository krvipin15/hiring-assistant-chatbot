#!/usr/bin/env python3
"""
data_validator.py

Provides utility functions for validating email addresses, international phone
numbers, and geographic locations.

- Email addresses are checked for proper format and deliverability using the
  `email_validator` library.
- Phone numbers are validated against international standards using the
  `phonenumbers` library.
- Locations are verified through the OpenStreetMap Nominatim API.

Functions
---------
validate_email(email : str) -> bool
    Returns True if the email address is syntactically valid and deliverable.
validate_phone(phone : str) -> bool
    Returns True if the phone number is valid according to international numbering plans.
validate_location(location : str) -> bool
    Returns True if the given location exists and is recognized by OpenStreetMap.

Examples
--------
>>> from validators import validate_email, validate_phone, validate_location
>>> validate_email("test@example.com")
True
>>> validate_phone("+14155552671")
True
>>> validate_location("Berlin, Germany")
True
"""

import requests
import phonenumbers
from loguru import logger
from email_validator import EmailNotValidError, validate_email as ev_validate


def validate_email(email: str) -> bool:
    """
    Validate an email address.
    """
    if not email:
        return False
    logger.info(f"Validating email: {email}")
    try:
        ev_validate(email)
        logger.info(f"Email validation successful for {email}")
        return True
    except EmailNotValidError as e:
        logger.warning(f"Email validation failed for {email}: {e}")
        return False


def validate_phone(phone: str) -> bool:
    """
    Validate an international phone number.
    """
    logger.info(f"Validating phone number: {phone}")
    try:
        parsed = phonenumbers.parse(phone, None)
        is_valid = phonenumbers.is_valid_number(parsed)
        if is_valid:
            logger.info(f"Phone number validation successful for {phone}")
        else:
            logger.warning(
                f"Phone number validation failed for {phone}: Not a valid number."
            )
        return is_valid
    except phonenumbers.NumberParseException as e:
        logger.warning(f"Phone number validation failed for {phone}: {e}")
        return False


def validate_location(location: str) -> bool:
    """
    Validate a geographic location.
    """
    logger.info(f"Validating location: {location}")
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    try:
        resp = requests.get(
            url,
            params=params,
            headers={"User-Agent": "hiring-assistant-chatbot"},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error(
                f"Nominatim API request failed with status {resp.status_code}: {resp.text}"
            )
            return False

        data = resp.json()
        if not data:
            logger.warning(f"Location '{location}' not found by Nominatim.")
            return False

        result = data[0]
        if "display_name" not in result or not result["display_name"]:
            logger.warning(
                f"Nominatim found a result for '{location}' but it has no display name."
            )
            return False

        importance = float(result.get("importance", 0))
        if importance < 0.2:
            logger.warning(
                f"Location '{location}' has a low importance score ({importance}), likely not a valid place."
            )
            return False

        logger.info(
            f"Location validation successful for '{location}'. Found: {result['display_name']}"
        )
        return True

    except requests.RequestException as e:
        logger.exception(
            f"An error occurred while validating location '{location}': {e}"
        )
        return False
