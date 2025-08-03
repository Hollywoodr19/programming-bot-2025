"""
Core Bot Engine
"""

import json
import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import uuid
import anthropic
import re

# Setup a module-level logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Creates and returns a new database connection."""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initializes the database and creates tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Create tables for chat history, projects, etc.
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_message TEXT NOT NULL,
                        bot_response TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        project_name TEXT NOT NULL,
                        description TEXT,
                        UNIQUE(user_id, project_name)
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise

class ClaudeAPIEngine:
    """
    Core engine for processing user messages using the Claude API.
    """
    def __init__(self, api_key: str, model: str, fallback_model: Optional[str] = None, max_tokens: int = 4096):
        if not api_key:
            raise ValueError("API key cannot be empty.")

        # Assume 'anthropic' is the client library for Claude API
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.error("The 'anthropic' library is not installed. Please install it with 'pip install anthropic'.")
            raise

        self.model = model
        self.fallback_model = fallback_model
        self.max_tokens = max_tokens
        self.db = DatabaseManager('programming_bot.db')
        self.user_context: Dict[str, Any] = {}
        self.message_count: int = 0
        self.session_cache: Dict[str, Any] = {}

    def process_message(self, user_message: str, session_id: str) -> str:
        """
        Processes a user message, either with the primary model or a fallback.
        """
        self.message_count += 1
        logger.info(f"Processing message {self.message_count} for session {session_id}")
        try:
            return self._process_with_claude(user_message, self.model)
        except Exception as e:
            logger.error(f"Error processing with primary model '{self.model}': {e}")
            if self.fallback_model:
                logger.info(f"Attempting to use fallback model '{self.fallback_model}'")
                return self._process_fallback(user_message)
            else:
                return "Es tut mir leid, es ist ein Fehler aufgetreten."

    def _process_with_claude(self, message: str, model: str) -> str:
        """Helper to send a request to the Claude API."""
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": message}]
            )
            bot_response = response.content[0].text
            self._save_chat_history("user_session", message, bot_response)
            return bot_response
        except Exception as e:
            logger.error(f"Claude API call failed for model {model}: {e}")
            raise

    def _process_fallback(self, message: str) -> str:
        """Processes a message using the fallback model."""
        if not self.fallback_model:
            return "Kein Fallback-Modell konfiguriert."
        try:
            return self._process_with_claude(message, self.fallback_model)
        except Exception as e:
            logger.error(f"Fallback model '{self.fallback_model}' also failed: {e}")
            return "Der Fallback-Mechanismus ist leider auch fehlgeschlagen."

    def _save_chat_history(self, session_id: str, user_message: str, bot_response: str):
        """Saves a chat interaction to the database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_history (session_id, user_message, bot_response) VALUES (?, ?, ?)",
                    (session_id, user_message, bot_response)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save chat history for session {session_id}: {e}")

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyzes a given code snippet for improvements."""
        prompt = f"Bitte analysiere den folgenden Code und gib Verbesserungsvorschläge:\n\n```python\n{code}\n```"
        try:
            analysis = self._process_with_claude(prompt, self.model)
            return {"status": "success", "analysis": analysis}
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return self._create_fallback_analysis()

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Provides a fallback response for code analysis."""
        return {
            "status": "error",
            "analysis": "Die Code-Analyse konnte nicht durchgeführt werden. Bitte versuchen Sie es später erneut."
        }

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves chat history for a given session."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT user_message, bot_response, timestamp FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC",
                    (session_id,)
                )
                return [{"user": row[0], "bot": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Could not retrieve chat history for session {session_id}: {e}")
            return []


class BotEngine:
    """
    Abstract base class for different bot engine implementations.
    This provides a common interface for the application.
    """
    def process_message(self, user_message: str, session_id: str) -> str:
        raise NotImplementedError


def create_bot_engine(config: Dict[str, Any]) -> ClaudeAPIEngine:
    """
    Factory function to create an instance of the bot engine.
    """
    api_key = config.get("CLAUDE_API_KEY")
    model = config.get("CLAUDE_MODEL", "claude-3-opus-20240229")
    fallback_model = config.get("CLAUDE_FALLBACK_MODEL")
    max_tokens = config.get("MAX_TOKENS", 4096)

    return ClaudeAPIEngine(
        api_key=api_key,
        model=model,
        fallback_model=fallback_model,
        max_tokens=max_tokens
    )