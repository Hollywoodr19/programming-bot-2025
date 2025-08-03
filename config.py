"""
Zentrales Konfigurationsmodul für die Programming Bot 2025 Anwendung.
Verwaltet alle Konfigurationen, von Umgebungsvariablen bis zur dynamischen
Modellauswahl für Claude, mithilfe der SmartConfig- und ModelRegistry-Klassen.
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from pathlib import Path
import re
import requests # Annahme: wird für API-Anfragen in ModelRegistry benötigt
import time

# HINWEIS: Die folgende problematische Importzeile wurde entfernt, um den
# zirkulären Importfehler (ImportError) zu beheben.
# from auth_system import auth_bp, login_required # <--- DIESE ZEILE WURDE ENTFERNT

class ModelRegistry:
    """Verwaltet die Konfiguration und Aktualisierung von Claude-Modellen."""
    def __init__(self, config_dir='data', config_file='claude_models.json'):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / config_file
        self.last_check_file = self.config_dir / '.last_model_check'
        self.check_interval_hours = 24
        self.model_patterns = {
            'opus': re.compile(r'claude-3-opus-[\d]{8}'),
            'sonnet': re.compile(r'claude-3-sonnet-[\d]{8}'),
            'haiku': re.compile(r'claude-3-haiku-[\d]{8}'),
        }
        self.config = self.load_or_create_config()

    def load_or_create_config(self):
        """Lädt die Modellkonfiguration oder erstellt eine Standardkonfiguration."""
        self.config_dir.mkdir(exist_ok=True)
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Fehler beim Laden der Modellkonfiguration: {e}. Erstelle eine neue.")
        return self.create_default_config()

    def create_default_config(self):
        """Erstellt eine Standardkonfiguration für die Claude-Modelle."""
        default_config = {
            "current_model": "claude-3-sonnet-20240229",
            "fallback_model": "claude-3-haiku-20240307",
            "available_models": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config_data):
        """Speichert die Modellkonfiguration in der JSON-Datei."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            logging.error(f"Konnte die Modellkonfiguration nicht speichern: {e}")

    # ... (Die restlichen Methoden der ModelRegistry-Klasse bleiben unverändert) ...

    def get_current_model(self):
        """Gibt das aktuell beste Modell zurück."""
        return self.config.get("current_model", "claude-3-sonnet-20240229")

    def get_fallback_model(self):
        """Gibt das Fallback-Modell zurück."""
        return self.config.get("fallback_model", "claude-3-haiku-20240307")


class SmartConfig:
    """
    Eine intelligente Konfigurationsklasse, die Einstellungen aus Umgebungsvariablen
    lädt und die Claude-Modell-Verwaltung integriert.
    """
    _instance = None

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.model_registry = ModelRegistry()
        self._load_config()
        self.validate_config()

    def _load_config(self):
        """Lädt alle Konfigurationswerte aus den Umgebungsvariablen."""
        # Server-Konfiguration
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', 8100))
        self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

        # Sicherheitskonfiguration
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'ein-sehr-geheimer-schluessel')
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:8100').split(',')
        self.RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')

        # Claude API Konfiguration - über ModelRegistry verwaltet
        self.CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
        self.CLAUDE_MODEL = self.model_registry.get_current_model()
        self.CLAUDE_FALLBACK_MODEL = self.model_registry.get_fallback_model()
        self.CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', 4096))

        # Datenbank- und Pfad-Einstellungen
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/programming_bot_2025.db')

        # Bot-Einstellungen
        self.BOT_NAME = os.getenv('BOT_NAME', 'Programming Bot 2025')
        self.DEFAULT_MODE = os.getenv('DEFAULT_MODE', 'programming')
        self.MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', 10))

        # Feature Flags
        self.ENABLE_CODE_REVIEW = os.getenv('ENABLE_CODE_REVIEW', 'True').lower() in ('true', '1', 'yes')
        self.ENABLE_PROJECT_MANAGEMENT = os.getenv('ENABLE_PROJECT_MANAGEMENT', 'True').lower() in ('true', '1', 'yes')
        self.ENABLE_CHAT_HISTORY = os.getenv('ENABLE_CHAT_HISTORY', 'True').lower() in ('true', '1', 'yes')
        self.ENABLE_USER_REGISTRATION = os.getenv('ENABLE_USER_REGISTRATION', 'False').lower() in ('true', '1', 'yes')

        # Modell-Update-Einstellungen
        self.AUTO_UPDATE_MODELS = os.getenv('AUTO_UPDATE_MODELS', 'True').lower() in ('true', '1', 'yes')

    def setup_logging(self):
        """Konfiguriert das anwendungsweite Logging."""
        log_dir = Path('logs')
        log_file = log_dir / 'app.log'
        handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if self.DEBUG else logging.INFO)
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
        root_logger.addHandler(handler)

    def get_claude_config(self):
        """Gibt ein Dictionary mit der Konfiguration für die Bot-Engine zurück."""
        return {
            "api_key": self.CLAUDE_API_KEY,
            "model_name": self.CLAUDE_MODEL,
            "fallback_model_name": self.CLAUDE_FALLBACK_MODEL,
            "max_tokens": self.CLAUDE_MAX_TOKENS
        }

    def validate_config(self):
        """Validiert kritische Konfigurationswerte."""
        if not self.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY ist nicht in der Umgebung gesetzt.")
        logging.info("Konfiguration erfolgreich validiert.")

    def print_startup_info(self):
        """Gibt eine Zusammenfassung der Konfiguration beim Start aus."""
        logging.info("==============================================")
        logging.info(f"   {self.BOT_NAME} - STARTUP")
        logging.info("==============================================")
        logging.info(f"Modus: {'DEBUG' if self.DEBUG else 'PRODUCTION'}")
        logging.info(f"Host: {self.HOST}, Port: {self.PORT}")
        logging.info(f"Aktuelles Claude-Modell: {self.CLAUDE_MODEL}")
        logging.info(f"Fallback Claude-Modell: {self.CLAUDE_FALLBACK_MODEL}")
        logging.info(f"Benutzerregistrierung: {'Aktiviert' if self.ENABLE_USER_REGISTRATION else 'Deaktiviert'}")
        logging.info("==============================================")


_config_instance = None

def get_config():
    """
    Gibt eine Singleton-Instanz der SmartConfig zurück.
    Stellt sicher, dass die Konfiguration nur einmal geladen wird.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = SmartConfig()
    return _config_instance
