# 🤖 Programming Bot mit Gedächtnis

Ein intelligenter Programmier-Assistent mit persistentem Gedächtnis, Git-Integration und Visualisierungen.

## 🚀 Features

- **Persistentes Gedächtnis**: Speichert Code-Snippets und Konversationen
- **Git-Integration**: Trackt automatisch Code-Änderungen
- **Semantische Suche**: Findet ähnlichen Code mit KI
- **Visualisierungen**: Dependency Graphs, Code Metriken, Projekt-Struktur
- **Web-Interface**: Modernes UI mit Live-Updates
- **Port 8100**: Läuft parallel zu anderen Services

## 📦 Installation

### 1. Clone oder erstelle das Projekt

```bash
mkdir programming-bot
cd programming-bot
```

### 2. Erstelle alle Dateien

Kopiere die Dateien aus den Artifacts:
- `main.py` - Hauptanwendung
- `visualizations.py` - Visualisierungs-Module
- `config.py` - Konfiguration

### 3. Virtual Environment erstellen

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

### 4. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 5. Konfiguration

```bash
cp .env.example .env
# Editiere .env und füge deinen ANTHROPIC_API_KEY ein
```

### 6. Bot starten

```bash
python main.py
```

Der Bot läuft jetzt auf: http://localhost:8100

## 🔧 Konfiguration

Alle Einstellungen in `.env`:

- `ANTHROPIC_API_KEY` - Dein Anthropic API Key (erforderlich)
- `GIT_REPO_PATH` - Pfad zum Git Repository (Standard: ./)
- `PORT` - Server Port (Standard: 8100)
- `HOST` - Server Host (Standard: 0.0.0.0)

## 📚 Verwendung

### Chat
- Stelle Fragen wie gewohnt
- Der Bot merkt sich Kontext aus früheren Gesprächen
- Nutzt semantische Suche für relevante Informationen

### Code speichern
- Füge wichtige Code-Snippets über das UI hinzu
- Werden automatisch mit Embeddings versehen
- Tags helfen bei der Organisation

### Visualisierungen
- **Abhängigkeiten**: Zeigt Datei-Abhängigkeiten als interaktiven Graph
- **Metriken**: Dashboard mit Code-Statistiken und Charts
- **Struktur**: Interaktive Projekt-Übersicht als Sunburst

### Git-Integration
- Automatisches Tracking alle 5 Minuten
- Analysiert Commits und speichert relevanten Code
- Verknüpft Code mit Git-History

## 🛠️ API Endpoints

- `POST /api/chat` - Chat mit dem Bot
- `POST /api/code` - Code-Snippet speichern
- `POST /api/context` - Projekt-Kontext setzen
- `GET /api/search?query=...` - Semantische Suche
- `GET /api/visualize/dependencies` - Dependency Graph
- `GET /api/visualize/metrics` - Metriken Dashboard
- `GET /api/visualize/structure` - Projekt-Struktur
- `POST /api/git/sync` - Git manuell synchronisieren
- `GET /api/export` - Gedächtnis exportieren

## 🐛 Troubleshooting

### Port bereits belegt?
```bash
lsof -i :8100
kill -9 <PID>
```

### ChromaDB Fehler?
```bash
rm -rf chroma_db/
# Neustart versuchen
```

### Git-Integration funktioniert nicht?
- Stelle sicher, dass `GIT_REPO_PATH` auf ein gültiges Git-Repo zeigt
- Prüfe Berechtigungen für den Ordner

### Module nicht gefunden?
```bash
# Stelle sicher, dass venv aktiviert ist
which python  # sollte auf venv/bin/python zeigen
pip list  # zeigt installierte Pakete
```

## 🔄 Updates

Um den Bot zu aktualisieren:
1. Stoppe den laufenden Bot (Ctrl+C)
2. Aktualisiere den Code
3. Installiere neue Dependencies: `pip install -r requirements.txt`
4. Starte neu: `python main.py`

## 💾 Backup

Wichtige Daten für Backup:
- `bot_memory.db` - SQLite Datenbank
- `chroma_db/` - Vektor-Datenbank
- `.env` - Deine Konfiguration

## 🤝 Beitragen

Feel free to:
- Bugs melden
- Features vorschlagen
- Pull Requests erstellen

## 📝 Lizenz

MIT License - siehe LICENSE Datei

---

Erstellt mit ❤️ für produktives Programmieren