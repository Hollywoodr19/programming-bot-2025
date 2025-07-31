"""
Database Migration Fix
Fügt fehlende Spalten zur bestehenden Datenbank hinzu
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def migrate_database(db_path: str = "bot_data.db"):
    """
    Migriert bestehende Datenbank zu neuem Schema
    Fügt fehlende Spalten hinzu ohne Datenverlust
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if model_used column exists in chat_history
            cursor.execute("PRAGMA table_info(chat_history)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'model_used' not in columns:
                logger.info("🔄 Adding model_used column to chat_history table...")
                cursor.execute("ALTER TABLE chat_history ADD COLUMN model_used TEXT DEFAULT 'unknown'")
                logger.info("✅ Added model_used column")

            # Check if session_id column exists in chat_history
            if 'session_id' not in columns:
                logger.info("🔄 Adding session_id column to chat_history table...")
                cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT DEFAULT 'default'")
                logger.info("✅ Added session_id column")

            # Check if context column exists in chat_history
            if 'context' not in columns:
                logger.info("🔄 Adding context column to chat_history table...")
                cursor.execute("ALTER TABLE chat_history ADD COLUMN context TEXT DEFAULT 'general'")
                logger.info("✅ Added context column")

            conn.commit()
            logger.info("✅ Database migration completed successfully")

    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise


def fix_claude_model_config():
    """
    Fixed Claude Model Configuration
    Stellt sicher, dass gültige Models verwendet werden
    """
    try:
        # Try to import Smart Config
        from config import get_current_claude_model, update_model_config

        current_model = get_current_claude_model()
        logger.info(f"Current model: {current_model}")

        # Valid Claude 4 models (as of August 2025)
        valid_models = [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250514",
            "claude-3-5-sonnet-20241022"  # Fallback to Claude 3.5
        ]

        if current_model not in valid_models:
            logger.warning(f"⚠️ Invalid model detected: {current_model}")
            logger.info("🔄 Updating to valid model...")

            # Update to a valid model
            new_model = "claude-sonnet-4-20250514"  # Most balanced option
            update_model_config(new_model)
            logger.info(f"✅ Updated to valid model: {new_model}")

    except ImportError:
        logger.warning("⚠️ Smart Config not available for model fix")
        logger.info("💡 Please check your .env file and ensure CLAUDE_MODEL is set to a valid model")
    except Exception as e:
        logger.error(f"❌ Model config fix failed: {e}")


def run_complete_fix():
    """
    Runs complete fix for all detected issues
    """
    print("🔧 Starting Programming Bot Database Fix...")

    # 1. Fix database schema
    print("\n1. Migrating database schema...")
    migrate_database()

    # 2. Fix Claude model config
    print("\n2. Fixing Claude model configuration...")
    fix_claude_model_config()

    print("\n✅ All fixes applied successfully!")
    print("🚀 Restart your bot with: python main.py")


if __name__ == "__main__":
    run_complete_fix()