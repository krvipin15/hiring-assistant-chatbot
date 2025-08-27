#!/usr/bin/env python3
"""
generate_key.py

Generate a random, unique encryption key and optionally write it to a `.env` file.

- Uses 32 random bytes encoded with URL-safe base64 (Fernet-compatible).
- By default, prints the key to stdout.
- With `--write`, inserts or updates `ENCRYPTION_KEY` in `.env` (creates the file if missing).
- Respects existing keys unless `--force` is provided.

Usage
-----
Print key only:
    $ python3 -m scripts.generate_key

Write/update `.env` safely:
    $ python3 -m scripts.generate_key --write

Overwrite existing key:
    $ python3 -m scripts.generate_key --write --force
"""

import os
import re
import base64
import secrets
import argparse
from pathlib import Path
from loguru import logger

# Environment variable and file configuration
ENV_VAR_NAME = "ENCRYPTION_KEY"
ENV_FILE = Path(".env")


def generate_key() -> str:
    """
    Generate a random encryption key.

    The key is 32 random bytes, encoded with URL-safe base64,
    making it compatible with Fernet encryption.

    Returns
    -------
    str
        A random encryption key encoded as a URL-safe base64 string.
    """
    key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    logger.info(f"Generated new key: {key}")
    return key


def read_env(path: Path) -> str:
    """
    Read the contents of a `.env` file.

    Parameters
    ----------
    path : Path
        Path to the `.env` file.

    Returns
    -------
    str
        The contents of the `.env` file, or an empty string if the file does not exist.
    """
    if not path.exists():
        logger.warning(f".env file not found at {path}")
        return ""
    return path.read_text(encoding="utf-8")


def write_env(path: Path, content: str) -> None:
    """
    Write content to a `.env` file.

    Parameters
    ----------
    path : Path
        Path to the `.env` file.
    content : str
        The content to write to the file.

    Returns
    -------
    None
    """
    path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote content to {path}")
    return None


def insert_env_var(content: str, key: str, value: str) -> str:
    """
    Insert or update an environment variable in `.env` content.

    Parameters
    ----------
    content : str
        Existing `.env` file content.
    key : str
        The environment variable name to insert or update.
    value : str
        The value of the environment variable.

    Returns
    -------
    str
        Updated `.env` file content with the key/value inserted or replaced.
    """
    pattern = re.compile(rf"^(?:\s*export\s+)?{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(content):
        logger.info(f"Updating existing key '{key}' in .env content.")
        return pattern.sub(line, content, count=1)

    logger.info(f"Inserting new key '{key}' into .env content.")
    if content and not content.endswith("\n"):
        content += "\n"
    return content + line + "\n"


def main() -> None:
    """
    Main entry point for the script.

    Parses command-line arguments, generates a new encryption key,
    and optionally writes/updates the `.env` file.

    Command-line Arguments
    ----------------------
    --write : bool, optional
        Write/update the key in `.env`.
    --force : bool, optional
        Overwrite the key in `.env` if it already exists.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(description="Generate and manage encryption key")
    parser.add_argument("--write", action="store_true", help="Write/update key in .env")
    parser.add_argument("--force", action="store_true", help="Overwrite existing key in .env")
    args = parser.parse_args()

    key = generate_key()
    print(key)  # Still print the key to stdout for piping

    if not args.write:
        return

    env_content = read_env(ENV_FILE)

    existing_match = re.search(
        rf"^(?:\s*export\s+)?{re.escape(ENV_VAR_NAME)}=(.+)$",
        env_content,
        re.MULTILINE,
    )

    if existing_match and not args.force:
        logger.warning(f"{ENV_VAR_NAME} already present in {ENV_FILE}. Use --force to overwrite.")
        return

    new_content = insert_env_var(env_content, ENV_VAR_NAME, key)

    if "OPENROUTER_API_KEY=" not in new_content:
        logger.info("Adding placeholder for OPENROUTER_API_KEY.")
        new_content += "OPENROUTER_API_KEY=Enter_your_openrouter_api_key_here\n"
    if "OPENROUTER_MODEL=" not in new_content:
        logger.info("Adding placeholder for OPENROUTER_MODEL.")
        new_content += "OPENROUTER_MODEL=Enter_your_openrouter_model_here\n"
    if "DATABASE_URL=" not in new_content:
        logger.info("Adding placeholder for DATABASE_URL.")
        new_content += "DATABASE_URL=sqlite:///candidates.db\n"

    if not ENV_FILE.exists():
        logger.info(f"{ENV_FILE} does not exist. Creating it with restrictive permissions.")
        os.umask(0)
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        try:
            os.chmod(ENV_FILE, 0o600)
            logger.info(f"Set permissions for {ENV_FILE} to 600.")
        except Exception as e:
            logger.warning(f"Could not set permissions for {ENV_FILE}: {e}")
    else:
        write_env(ENV_FILE, new_content)

    logger.info(f"Wrote {ENV_VAR_NAME} to {ENV_FILE}{' (overwritten)' if existing_match else ''}.")


if __name__ == "__main__":
    logger.add("key_generation.log", rotation="10 MB", level="INFO")
    logger.info("Starting key generation script.")
    try:
        main()
        logger.info("Key generation script finished successfully.")
    except Exception as e:
        logger.exception("An error occurred during key generation.")
