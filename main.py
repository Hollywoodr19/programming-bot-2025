# main.py - Erweiterter Bot mit allen Features
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import hashlib
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path

# Core imports
from anthropic import Anthropic
import tiktoken
import git
from git import Repo
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# FastAPI imports
from fastapi import FastAPI, WebSocket, HTTPException, Depends, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Projekt imports
from config import Config
from visualizations import add_visualization_endpoints


# Erweiterte Datenmodelle
@dataclass
class CodeSnippet:
    id: str
    language: str
    code: str
    description: str
    timestamp: str
    tags: List[str]
    file_path: Optional[str] = None
    git_commit: Optional[str] = None
    embedding_id: Optional[str] = None


@dataclass
class Conversation:
    id: str
    messages: List[Dict[str, str]]
    summary: str
    timestamp: str
    tags: List[str]
    embedding_id: Optional[str] = None


class EnhancedProgrammingBot:
    """Erweiterter Programmier-Bot mit Web-UI, Git-Integration und Vektor-DB"""

    def __init__(self, api_key: str, db_path: str = "bot_memory.db",
                 repo_path: str = None, chroma_path: str = "./chroma_db"):
        self.client = Anthropic(api_key=api_key)
        self.db_path = db_path
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self.max_context_tokens = 100000

        # Git-Integration
        self.repo_path = repo_path
        self.repo = None
        if repo_path and os.path.exists(repo_path):
            try:
                self.repo = Repo(repo_path)
            except:
                print(f"Warnung: {repo_path} ist kein Git-Repository")

        # Vektor-Datenbank Setup
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Collections für verschiedene Datentypen
        self.code_collection = self.chroma_client.get_or_create_collection(
            name="code_snippets",
            metadata={"hnsw:space": "cosine"}
        )
        self.conv_collection = self.chroma_client.get_or_create_collection(
            name="conversations",
            metadata={"hnsw:space": "cosine"}
        )

        self.init_database()
        self.websocket_connections = []

    def init_database(self):
        """Erweiterte Datenbank-Initialisierung"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Erweiterte Code-Snippets Tabelle
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS code_snippets
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           language
                           TEXT,
                           code
                           TEXT,
                           description
                           TEXT,
                           timestamp
                           TEXT,
                           tags
                           TEXT,
                           file_path
                           TEXT,
                           git_commit
                           TEXT,
                           embedding_id
                           TEXT
                       )
                       ''')

        # Erweiterte Konversationen Tabelle
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS conversations
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           messages
                           TEXT,
                           summary
                           TEXT,
                           timestamp
                           TEXT,
                           tags
                           TEXT,
                           embedding_id
                           TEXT
                       )
                       ''')

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS project_context
                       (
                           key
                           TEXT
                           PRIMARY
                           KEY,
                           value
                           TEXT,
                           timestamp
                           TEXT
                       )
                       ''')

        # Git-Tracking Tabelle
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS git_tracking
                       (
                           commit_hash
                           TEXT
                           PRIMARY
                           KEY,
                           timestamp
                           TEXT,
                           message
                           TEXT,
                           files_changed
                           TEXT,
                           processed
                           BOOLEAN
                           DEFAULT
                           FALSE
                       )
                       ''')

        conn.commit()
        conn.close()

    def generate_id(self, content: str) -> str:
        """Generiert eine eindeutige ID basierend auf Inhalt und Zeit"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{content}{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def create_embedding(self, text: str) -> List[float]:
        """Erstellt Embedding für Text"""
        return self.embedding_model.encode(text).tolist()

    def save_code_snippet_with_embedding(self, code: str, language: str,
                                         description: str, tags: List[str] = None,
                                         file_path: str = None, git_commit: str = None):
        """Speichert Code-Snippet mit Vektor-Embedding"""
        snippet = CodeSnippet(
            id=self.generate_id(code),
            language=language,
            code=code,
            description=description,
            timestamp=datetime.now().isoformat(),
            tags=tags or [],
            file_path=file_path,
            git_commit=git_commit,
            embedding_id=None
        )

        # Erstelle Embedding
        embedding_text = f"{description}\n{code}"
        embedding = self.create_embedding(embedding_text)

        # Speichere in ChromaDB
        self.code_collection.add(
            embeddings=[embedding],
            documents=[embedding_text],
            metadatas=[{
                "language": language,
                "description": description,
                "tags": json.dumps(tags or []),
                "file_path": file_path or "",
                "git_commit": git_commit or ""
            }],
            ids=[snippet.id]
        )

        snippet.embedding_id = snippet.id

        # Speichere in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO code_snippets 
            (id, language, code, description, timestamp, tags, file_path, git_commit, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (snippet.id, snippet.language, snippet.code, snippet.description,
              snippet.timestamp, json.dumps(snippet.tags), snippet.file_path,
              snippet.git_commit, snippet.embedding_id))
        conn.commit()
        conn.close()

        return snippet.id

    def semantic_search_code(self, query: str, n_results: int = 5) -> List[CodeSnippet]:
        """Semantische Suche nach Code-Snippets"""
        query_embedding = self.create_embedding(query)

        results = self.code_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        if not results['ids'][0]:
            return []

        # Hole vollständige Snippets aus SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        snippets = []
        for snippet_id in results['ids'][0]:
            cursor.execute('SELECT * FROM code_snippets WHERE id = ?', (snippet_id,))
            row = cursor.fetchone()
            if row:
                snippets.append(CodeSnippet(
                    id=row[0],
                    language=row[1],
                    code=row[2],
                    description=row[3],
                    timestamp=row[4],
                    tags=json.loads(row[5]),
                    file_path=row[6],
                    git_commit=row[7],
                    embedding_id=row[8]
                ))

        conn.close()
        return snippets

    def track_git_changes(self):
        """Trackt Änderungen im Git-Repository"""
        if not self.repo:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hole bereits verarbeitete Commits
        cursor.execute('SELECT commit_hash FROM git_tracking')
        processed_commits = {row[0] for row in cursor.fetchall()}

        # Verarbeite neue Commits
        for commit in self.repo.iter_commits():
            if commit.hexsha in processed_commits:
                continue

            # Speichere Commit-Info
            files_changed = []
            for item in commit.diff(commit.parents[0] if commit.parents else None):
                files_changed.append({
                    'path': item.a_path or item.b_path,
                    'change_type': item.change_type
                })

            cursor.execute('''
                           INSERT INTO git_tracking
                               (commit_hash, timestamp, message, files_changed, processed)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (commit.hexsha, commit.committed_datetime.isoformat(),
                                 commit.message, json.dumps(files_changed), False))

            # Verarbeite geänderte Code-Dateien
            for item in commit.diff(commit.parents[0] if commit.parents else None):
                if item.change_type in ['A', 'M']:  # Added or Modified
                    file_path = item.a_path or item.b_path
                    if file_path.endswith(('.py', '.js', '.java', '.cpp', '.go')):
                        try:
                            # Lese Dateiinhalt
                            file_content = self.repo.odb.stream(item.a_blob.binsha).read().decode('utf-8')

                            # Extrahiere Funktionen/Klassen (vereinfacht)
                            language = file_path.split('.')[-1]
                            description = f"Code aus {file_path} (Commit: {commit.message[:50]})"

                            self.save_code_snippet_with_embedding(
                                code=file_content[:1000],  # Erste 1000 Zeichen
                                language=language,
                                description=description,
                                tags=["git", "auto-tracked"],
                                file_path=file_path,
                                git_commit=commit.hexsha
                            )
                        except Exception as e:
                            print(f"Fehler beim Verarbeiten von {file_path}: {e}")

            # Markiere als verarbeitet
            cursor.execute('UPDATE git_tracking SET processed = TRUE WHERE commit_hash = ?',
                           (commit.hexsha,))

        conn.commit()
        conn.close()

    def save_conversation(self, messages: List[Dict[str, str]], summary: str = None, tags: List[str] = None):
        """Speichert eine Konversation mit Embedding"""
        if not summary:
            # Automatische Zusammenfassung generieren
            summary = self.generate_summary(messages)

        conv = Conversation(
            id=self.generate_id(str(messages)),
            messages=messages,
            summary=summary,
            timestamp=datetime.now().isoformat(),
            tags=tags or [],
            embedding_id=None
        )

        # Erstelle Embedding für Konversation
        conv_text = summary + "\n" + "\n".join([f"{m['role']}: {m['content'][:200]}" for m in messages[-3:]])
        embedding = self.create_embedding(conv_text)

        # Speichere in ChromaDB
        self.conv_collection.add(
            embeddings=[embedding],
            documents=[conv_text],
            metadatas=[{
                "summary": summary,
                "timestamp": conv.timestamp,
                "tags": json.dumps(tags or [])
            }],
            ids=[conv.id]
        )

        conv.embedding_id = conv.id

        # Speichere in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO conversations 
            (id, messages, summary, timestamp, tags, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (conv.id, json.dumps(conv.messages), conv.summary,
              conv.timestamp, json.dumps(conv.tags), conv.embedding_id))
        conn.commit()
        conn.close()

        return conv.id

    def set_project_context(self, key: str, value: str):
        """Speichert Projekt-Kontext"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO project_context (key, value, timestamp)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_project_context(self) -> Dict[str, str]:
        """Holt den gesamten Projekt-Kontext"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM project_context')
        context = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return context

    def get_enhanced_context(self, query: str, max_tokens: int = 20000) -> str:
        """Erweiterte Kontext-Suche mit semantischer Suche"""
        context_parts = []
        current_tokens = 0

        # 1. Projekt-Kontext
        project_ctx = self.get_project_context()
        if project_ctx:
            ctx_str = "=== PROJEKT KONTEXT ===\n"
            for key, value in project_ctx.items():
                ctx_str += f"{key}: {value}\n"
            context_parts.append(ctx_str)
            current_tokens += len(self.encoder.encode(ctx_str))

        # 2. Semantische Code-Suche
        semantic_snippets = self.semantic_search_code(query, n_results=5)
        if semantic_snippets:
            ctx_str = "\n=== RELEVANTE CODE (Semantische Suche) ===\n"
            for snippet in semantic_snippets:
                snippet_str = f"**{snippet.description}**"
                if snippet.file_path:
                    snippet_str += f" (Datei: {snippet.file_path})"
                snippet_str += f"\n```{snippet.language}\n{snippet.code}\n```\n"

                snippet_tokens = len(self.encoder.encode(snippet_str))
                if current_tokens + snippet_tokens < max_tokens:
                    ctx_str += snippet_str
                    current_tokens += snippet_tokens
            context_parts.append(ctx_str)

        # 3. Semantische Konversationssuche
        query_embedding = self.create_embedding(query)
        conv_results = self.conv_collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        if conv_results['ids'][0]:
            ctx_str = "\n=== RELEVANTE DISKUSSIONEN (Semantische Suche) ===\n"
            for conv_id in conv_results['ids'][0]:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT summary FROM conversations WHERE id = ?', (conv_id,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    conv_str = f"- {result[0]}\n"
                    conv_tokens = len(self.encoder.encode(conv_str))
                    if current_tokens + conv_tokens < max_tokens:
                        ctx_str += conv_str
                        current_tokens += conv_tokens
            context_parts.append(ctx_str)

        return "\n".join(context_parts)

    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """Generiert eine Zusammenfassung einer Konversation"""
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])

        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"Fasse diese Programmier-Diskussion in 1-2 Sätzen zusammen:\n\n{conversation_text}"
            }]
        )

        return response.content[0].text

    def chat(self, user_input: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Hauptchat-Funktion mit Kontext-Integration"""
        if conversation_history is None:
            conversation_history = []

        # Hole relevanten Kontext
        context = self.get_enhanced_context(user_input)

        # Erstelle System-Prompt
        system_prompt = """Du bist ein hilfreicher Programmier-Assistent mit persistentem Gedächtnis. 
Du hast Zugriff auf frühere Konversationen, Code-Snippets und Projekt-Kontext.
Nutze dieses Wissen, um konsistente und kontextbezogene Hilfe zu leisten."""

        # Füge Kontext zum User-Input hinzu
        enhanced_input = user_input
        if context:
            enhanced_input = f"{context}\n\n=== AKTUELLE ANFRAGE ===\n{user_input}"

        # Erstelle Messages für API
        messages = conversation_history + [{"role": "user", "content": enhanced_input}]

        # API-Aufruf
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text

    def export_memory(self, filepath: str):
        """Exportiert das gesamte Gedächtnis als JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hole alle Daten
        cursor.execute('SELECT * FROM code_snippets')
        code_snippets = cursor.fetchall()

        cursor.execute('SELECT * FROM conversations')
        conversations = cursor.fetchall()

        cursor.execute('SELECT * FROM project_context')
        project_context = cursor.fetchall()

        conn.close()

        # Erstelle Export-Objekt
        export_data = {
            "export_date": datetime.now().isoformat(),
            "code_snippets": [
                {
                    "id": row[0],
                    "language": row[1],
                    "code": row[2],
                    "description": row[3],
                    "timestamp": row[4],
                    "tags": json.loads(row[5])
                } for row in code_snippets
            ],
            "conversations": [
                {
                    "id": row[0],
                    "messages": json.loads(row[1]),
                    "summary": row[2],
                    "timestamp": row[3],
                    "tags": json.loads(row[4])
                } for row in conversations
            ],
            "project_context": {row[0]: row[1] for row in project_context}
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"Gedächtnis exportiert nach: {filepath}")

    async def broadcast_update(self, message: dict):
        """Sendet Updates an alle verbundenen WebSocket-Clients"""
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)

        # Entferne getrennte Verbindungen
        for ws in disconnected:
            self.websocket_connections.remove(ws)


# FastAPI App
app = FastAPI(title="Programming Bot API")
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Bot-Instanz (wird beim Start initialisiert)
bot = None


# API Modelle
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class CodeSnippetRequest(BaseModel):
    code: str
    language: str
    description: str
    tags: List[str] = []


class ProjectContextRequest(BaseModel):
    key: str
    value: str


# API Endpoints
@app.on_event("startup")
async def startup_event():
    global bot
    Config.init_directories()
    bot = EnhancedProgrammingBot(
        api_key=Config.ANTHROPIC_API_KEY,
        db_path=Config.DB_PATH,
        repo_path=Config.GIT_REPO_PATH,
        chroma_path=Config.CHROMA_PATH
    )

    # Füge Visualisierungs-Endpoints hinzu
    add_visualization_endpoints(app, bot)

    # Starte Git-Tracking im Hintergrund
    asyncio.create_task(periodic_git_tracking())


async def periodic_git_tracking():
    """Periodisches Git-Tracking alle 5 Minuten"""
    while True:
        try:
            bot.track_git_changes()
        except Exception as e:
            print(f"Fehler beim Git-Tracking: {e}")
        await asyncio.sleep(300)  # 5 Minuten


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Programming Bot</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
        <script src="https://d3js.org/d3.v7.min.js"></script>
    </head>
    <body class="bg-gray-900 text-gray-100">
        <div class="container mx-auto p-4">
            <h1 class="text-3xl font-bold mb-6">🤖 Programming Bot mit Gedächtnis</h1>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <!-- Chat -->
                <div class="lg:col-span-2 bg-gray-800 rounded-lg p-4">
                    <h2 class="text-xl font-semibold mb-4">Chat</h2>
                    <div id="chat-messages" class="h-96 overflow-y-auto mb-4 p-4 bg-gray-700 rounded"></div>
                    <div class="flex gap-2">
                        <input type="text" id="chat-input" 
                            class="flex-1 p-2 bg-gray-700 rounded border border-gray-600 text-white"
                            placeholder="Stelle eine Frage...">
                        <button onclick="sendMessage()" 
                            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded">
                            Senden
                        </button>
                    </div>
                </div>

                <!-- Sidebar -->
                <div class="space-y-4">
                    <!-- Code Snippet Speichern -->
                    <div class="bg-gray-800 rounded-lg p-4">
                        <h3 class="text-lg font-semibold mb-2">Code Speichern</h3>
                        <textarea id="code-input" class="w-full p-2 bg-gray-700 rounded mb-2 text-white" 
                            rows="4" placeholder="Code hier einfügen..."></textarea>
                        <input type="text" id="code-lang" class="w-full p-2 bg-gray-700 rounded mb-2 text-white" 
                            placeholder="Sprache (z.B. python)">
                        <input type="text" id="code-desc" class="w-full p-2 bg-gray-700 rounded mb-2 text-white" 
                            placeholder="Beschreibung">
                        <button onclick="saveCode()" 
                            class="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded">
                            Speichern
                        </button>
                    </div>

                    <!-- Projekt Kontext -->
                    <div class="bg-gray-800 rounded-lg p-4">
                        <h3 class="text-lg font-semibold mb-2">Projekt Kontext</h3>
                        <input type="text" id="ctx-key" class="w-full p-2 bg-gray-700 rounded mb-2 text-white" 
                            placeholder="Key">
                        <input type="text" id="ctx-value" class="w-full p-2 bg-gray-700 rounded mb-2 text-white" 
                            placeholder="Value">
                        <button onclick="setContext()" 
                            class="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded">
                            Setzen
                        </button>
                    </div>

                    <!-- Suche -->
                    <div class="bg-gray-800 rounded-lg p-4">
                        <h3 class="text-lg font-semibold mb-2">Code Suchen</h3>
                        <input type="text" id="search-query" class="w-full p-2 bg-gray-700 rounded mb-2 text-white" 
                            placeholder="Suchbegriff...">
                        <button onclick="searchCode()" 
                            class="w-full px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded">
                            Suchen
                        </button>
                        <div id="search-results" class="mt-2 text-sm"></div>
                    </div>
                </div>
            </div>

            <!-- Visualisierungen -->
            <div class="mt-8">
                <h2 class="text-2xl font-bold mb-4">📈 Projekt-Visualisierungen</h2>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <button onclick="showDependencies()" 
                        class="p-4 bg-blue-600 hover:bg-blue-700 rounded-lg text-center">
                        <span class="text-3xl">🕸️</span><br>
                        Abhängigkeiten
                    </button>

                    <button onclick="showMetrics()" 
                        class="p-4 bg-green-600 hover:bg-green-700 rounded-lg text-center">
                        <span class="text-3xl">📊</span><br>
                        Code Metriken
                    </button>

                    <button onclick="showStructure()" 
                        class="p-4 bg-purple-600 hover:bg-purple-700 rounded-lg text-center">
                        <span class="text-3xl">🌳</span><br>
                        Projekt-Struktur
                    </button>
                </div>

                <div id="visualization-container" class="mt-4 bg-gray-800 rounded-lg p-4 hidden">
                    <div id="viz-content"></div>
                </div>
            </div>
        </div>

        <script>
            let ws = null;
            let conversationHistory = [];

            // WebSocket Verbindung - Port 8100!
            function connectWebSocket() {{
                ws = new WebSocket('ws://localhost:{Config.PORT}/ws');

                ws.onmessage = (event) => {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'chat_response') {{
                        addMessage('bot', data.content);
                    }} else if (data.type === 'update') {{
                        console.log('Update:', data);
                    }}
                }};

                ws.onclose = () => {{
                    console.log('WebSocket Verbindung geschlossen. Versuche Neuverbindung...');
                    setTimeout(connectWebSocket, 3000);
                }};

                ws.onerror = (error) => {{
                    console.error('WebSocket Fehler:', error);
                }};

                ws.onopen = () => {{
                    console.log('WebSocket verbunden auf Port {Config.PORT}');
                }};
            }}

            connectWebSocket();

            function addMessage(role, content) {{
                const messagesDiv = document.getElementById('chat-messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = role === 'user' ? 'mb-2 text-blue-400' : 'mb-2 text-green-400';
                messageDiv.innerHTML = `<strong>${{role === 'user' ? 'Du' : 'Bot'}}:</strong> ${{content}}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                conversationHistory.push({{role, content}});
            }}

            async function sendMessage() {{
                const input = document.getElementById('chat-input');
                const message = input.value.trim();
                if (!message) return;

                addMessage('user', message);
                input.value = '';

                const response = await fetch('/api/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message, conversation_history: conversationHistory}})
                }});

                const data = await response.json();
                addMessage('assistant', data.response);
            }}

            async function saveCode() {{
                const code = document.getElementById('code-input').value;
                const language = document.getElementById('code-lang').value;
                const description = document.getElementById('code-desc').value;

                const response = await fetch('/api/code', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{code, language, description}})
                }});

                if (response.ok) {{
                    alert('Code gespeichert!');
                    document.getElementById('code-input').value = '';
                    document.getElementById('code-lang').value = '';
                    document.getElementById('code-desc').value = '';
                }}
            }}

            async function setContext() {{
                const key = document.getElementById('ctx-key').value;
                const value = document.getElementById('ctx-value').value;

                const response = await fetch('/api/context', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{key, value}})
                }});

                if (response.ok) {{
                    alert('Kontext gesetzt!');
                    document.getElementById('ctx-key').value = '';
                    document.getElementById('ctx-value').value = '';
                }}
            }}

            async function searchCode() {{
                const query = document.getElementById('search-query').value;

                const response = await fetch(`/api/search?query=${{encodeURIComponent(query)}}`);
                const data = await response.json();

                const resultsDiv = document.getElementById('search-results');
                resultsDiv.innerHTML = '';

                data.results.forEach(snippet => {{
                    const div = document.createElement('div');
                    div.className = 'p-2 bg-gray-700 rounded mb-2';
                    div.innerHTML = `<strong>${{snippet.description}}</strong><br>
                        <code class="text-xs">${{snippet.language}}</code>`;
                    resultsDiv.appendChild(div);
                }});
            }}

            // Visualisierungs-Funktionen
            async function showDependencies() {{
                const container = document.getElementById('visualization-container');
                const content = document.getElementById('viz-content');

                container.classList.remove('hidden');
                content.innerHTML = '<p>Lade Abhängigkeits-Graph...</p>';

                const response = await fetch('/api/visualize/dependencies');
                const data = await response.json();

                content.innerHTML = '<iframe src="/static/dependency_graph.html" width="100%" height="600px" style="border:none;"></iframe>';
            }}

            async function showMetrics() {{
                const container = document.getElementById('visualization-container');
                const content = document.getElementById('viz-content');

                container.classList.remove('hidden');
                content.innerHTML = '<p>Lade Metriken-Dashboard...</p>';

                const response = await fetch('/api/visualize/metrics');
                const data = await response.json();

                content.innerHTML = '<iframe src="/static/metrics_dashboard.html" width="100%" height="800px" style="border:none;"></iframe>';
            }}

            async function showStructure() {{
                const container = document.getElementById('visualization-container');
                const content = document.getElementById('viz-content');

                container.classList.remove('hidden');
                content.innerHTML = '<p>Lade Projekt-Struktur...</p>';

                const response = await fetch('/api/visualize/structure');
                const treeData = await response.json();

                // D3.js Sunburst Visualization
                content.innerHTML = '<div id="sunburst" style="width: 100%; height: 600px;"></div>';

                const width = content.clientWidth;
                const height = 600;
                const radius = Math.min(width, height) / 2;

                const partition = d3.partition()
                    .size([2 * Math.PI, radius]);

                const arc = d3.arc()
                    .startAngle(d => d.x0)
                    .endAngle(d => d.x1)
                    .innerRadius(d => d.y0)
                    .outerRadius(d => d.y1);

                const svg = d3.select("#sunburst")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", `translate(${{width/2}},${{height/2}})`);

                const root = d3.hierarchy(treeData)
                    .sum(d => d.size || 1)
                    .sort((a, b) => b.value - a.value);

                partition(root);

                const color = d3.scaleOrdinal()
                    .domain(["python", "javascript", "folder"])
                    .range(["#3776ab", "#f7df1e", "#666"]);

                svg.selectAll("path")
                    .data(root.descendants())
                    .join("path")
                    .attr("d", arc)
                    .style("fill", d => color(d.data.language || "folder"))
                    .style("stroke", "#fff")
                    .append("title")
                    .text(d => `${{d.data.name}}\n${{d.value}} lines`);
            }}

            // Enter-Taste für Chat
            document.getElementById('chat-input').addEventListener('keypress', (e) => {{
                if (e.key === 'Enter') sendMessage();
            }});
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    bot.websocket_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # WebSocket Handler hier
    except:
        bot.websocket_connections.remove(websocket)


@app.post("/api/chat")
async def chat(message: ChatMessage):
    response = bot.chat(message.message)

    # Speichere Konversation
    conversation = [
        {"role": "user", "content": message.message},
        {"role": "assistant", "content": response}
    ]
    bot.save_conversation(conversation)

    return {"response": response}


@app.post("/api/code")
async def save_code(request: CodeSnippetRequest):
    snippet_id = bot.save_code_snippet_with_embedding(
        code=request.code,
        language=request.language,
        description=request.description,
        tags=request.tags
    )

    await bot.broadcast_update({
        "type": "code_saved",
        "snippet_id": snippet_id
    })

    return {"snippet_id": snippet_id}


@app.post("/api/context")
async def set_context(request: ProjectContextRequest):
    bot.set_project_context(request.key, request.value)
    return {"status": "success"}


@app.get("/api/search")
async def search_code(query: str):
    results = bot.semantic_search_code(query)
    return {
        "results": [
            {
                "id": s.id,
                "description": s.description,
                "language": s.language,
                "tags": s.tags
            } for s in results
        ]
    }


@app.post("/api/git/sync")
async def sync_git():
    bot.track_git_changes()
    return {"status": "synced"}


@app.get("/api/export")
async def export_memory():
    filepath = f"bot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    bot.export_memory(filepath)
    return {"filepath": filepath}


if __name__ == "__main__":
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)