import os
from pathlib import Path
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()


class Config:
    """Zentrale Konfigurationsdatei für den Programming Bot"""

    # Server Konfiguration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8100))

    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_API_KEY")

    # Pfade
    PROJECT_ROOT = Path(__file__).parent
    GIT_REPO_PATH = os.getenv("GIT_REPO_PATH", str(PROJECT_ROOT))
    DB_PATH = os.getenv("DB_PATH", "bot_memory.db")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
    STATIC_PATH = PROJECT_ROOT / "static"
    TEMPLATES_PATH = PROJECT_ROOT / "templates"

    # WebSocket URL für Frontend
    WS_URL = f"ws://localhost:{PORT}/ws"

    # Erstelle notwendige Verzeichnisse
    @classmethod
    def init_directories(cls):
        cls.STATIC_PATH.mkdir(exist_ok=True)
        cls.TEMPLATES_PATH.mkdir(exist_ok=True)
        Path(cls.CHROMA_PATH).mkdir(exist_ok=True)