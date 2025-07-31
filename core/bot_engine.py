"""
Core Bot Engine with Smart Config Integration
Komplett neu erstellt - Clean, konsistent und schema-kompatibel
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

# Setup logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for bot data"""

    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables - Schema-kompatibel mit fix_database.py"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Projects table - Schema passend zu fix_database.py
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        language TEXT,
                        user_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data TEXT,
                        status TEXT DEFAULT 'active'
                    )
                ''')

                # Chat history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        message TEXT NOT NULL,
                        response TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        context TEXT,
                        session_id TEXT,
                        model_used TEXT
                    )
                ''')

                # User sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("✅ Database initialized successfully")

        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise

class ClaudeAPIEngine:
    """Main bot engine with Smart Config integration"""

    def __init__(self, api_key: str = None, model: str = None, max_tokens: int = 1000):
        """Initialize Claude API Engine with Smart Config support"""

        # Get configuration from Smart Config if available
        try:
            from config import get_claude_config, get_current_claude_model
            claude_config = get_claude_config()

            self.api_key = api_key or claude_config.get('api_key')
            self.model = model or claude_config.get('model') or get_current_claude_model()
            self.fallback_model = claude_config.get('fallback_model')
            self.max_tokens = max_tokens or claude_config.get('max_tokens', 1000)

            logger.info(f"✅ Smart Config: Using model {self.model}")
            if self.fallback_model:
                logger.info(f"✅ Smart Config: Fallback model {self.fallback_model}")

        except ImportError:
            # Fallback to direct parameters
            self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
            self.model = model or os.getenv('CLAUDE_MODEL', 'claude-opus-4-20250514')
            self.fallback_model = None
            self.max_tokens = max_tokens
            logger.info(f"✅ Basic Config: Using model {self.model}")

        # Initialize Claude client
        if not self.api_key:
            logger.warning("⚠️ No Claude API key provided, running in fallback mode")
            self.client = None
        else:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ Claude API client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Claude API: {e}")
                self.client = None

        self.db = DatabaseManager()
        self.message_count = 0
        self.user_context = {}
        self.session_cache = {}

    # =====================================
    # CHAT AND MESSAGE PROCESSING
    # =====================================

    def process_message(self, message: str, user_context: Dict = None) -> str:
        """Process user message with Claude API"""
        self.message_count += 1

        # Get user context
        context = user_context or self.user_context
        user_id = context.get('user_id', 'anonymous')
        mode = context.get('mode', 'programming')

        try:
            if self.client:
                # Use Claude API for intelligent responses
                response = self._process_with_claude(message, context, mode)
                current_model = self.model
            else:
                # Fallback to simple responses
                response = self._process_fallback(message, context, mode)
                current_model = "Fallback Mode"

            # Save to chat history
            self._save_chat_history(user_id, message, response, context.get('session_id'), mode, current_model)

            return response

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

            # Try fallback model if available
            if self.fallback_model and self.client:
                try:
                    logger.info(f"🔄 Trying fallback model: {self.fallback_model}")
                    old_model = self.model
                    self.model = self.fallback_model

                    response = self._process_with_claude(message, context, mode)
                    self._save_chat_history(user_id, message, response, context.get('session_id'), mode, self.fallback_model)

                    return response

                except Exception as fallback_error:
                    logger.error(f"❌ Fallback model also failed: {fallback_error}")
                    self.model = old_model

            # Ultimate fallback
            fallback_response = f"Entschuldigung, ich hatte ein Problem. Kannst du deine Nachricht wiederholen?"
            return fallback_response

    def _process_with_claude(self, message: str, context: Dict, mode: str) -> str:
        """Process message using Claude API"""
        try:
            # Build system prompt based on mode
            if mode == 'programming':
                system_prompt = """You are a helpful programming assistant. You can help with code review, debugging, explaining concepts, and providing solutions. Be concise but thorough."""
            elif mode == 'casual':
                system_prompt = """You are a friendly conversational AI. Be warm, engaging, and natural in your responses."""
            else:
                system_prompt = """You are a helpful AI assistant. Provide clear, accurate, and helpful responses."""

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": message}]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            raise

    def _process_fallback(self, message: str, context: Dict, mode: str) -> str:
        """Fallback processing when Claude API is unavailable"""
        message_lower = message.lower()
        user_name = context.get('display_name', 'Freund')

        if "hallo" in message_lower or "hi" in message_lower:
            return f"Hallo {user_name}! Wie kann ich dir helfen?"
        elif "projekt" in message_lower:
            return "Gerne helfe ich dir bei deinem Projekt! Was möchtest du erstellen?"
        elif "code" in message_lower:
            return "Ich kann dir bei der Code-Analyse und -Überprüfung helfen. Zeig mir deinen Code!"
        else:
            return f"Interessant! Erzähl mir mehr darüber, {user_name}."

    def _save_chat_history(self, user_id: str, message: str, response: str, session_id: str = None, context: str = None, model_used: str = None):
        """Save chat interaction to database"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_history (user_id, message, response, session_id, context, model_used) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, message, response, session_id or 'default', context or 'general', model_used or self.model)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error saving chat history: {e}")

    # =====================================
    # PROJECT MANAGEMENT - Schema-kompatibel
    # =====================================

    def get_user_projects(self, user_id: str) -> List[Dict]:
        """Get all projects for a specific user"""
        try:
            logger.info(f"🔍 Loading projects for user: {user_id}")

            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get projects for user
            cursor.execute('''
                SELECT id, name, description, language, user_id, created_at, updated_at, status
                FROM projects 
                WHERE user_id = ? OR user_id IS NULL
                ORDER BY created_at DESC
            ''', (user_id,))

            projects = []
            for row in cursor.fetchall():
                project = {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'] or '',
                    'language': row['language'] or 'python',
                    'status': row['status'] or 'active',
                    'created_at': row['created_at'] or datetime.now().isoformat(),
                    'updated_at': row['updated_at'] or datetime.now().isoformat()
                }
                projects.append(project)

            conn.close()
            logger.info(f"✅ Found {len(projects)} projects for user {user_id}")

            # If no projects exist, create a demo project
            if not projects:
                logger.info("📝 Creating demo project for new user...")
                demo_result = self.create_project(
                    user_id=user_id,
                    name="Python Calculator Demo",
                    description="Ein einfacher Taschenrechner zum Ausprobieren",
                    language="python"
                )
                if demo_result.get('success'):
                    projects = [demo_result['project']]

            return projects

        except Exception as e:
            logger.error(f"❌ Error loading projects: {e}", exc_info=True)
            return []

    def create_project(self, user_id: str, name: str, description: str = "", language: str = "python") -> Dict:
        """Create a new project - Schema-kompatibel mit TEXT ID"""
        try:
            logger.info(f"📝 Creating project '{name}' for user {user_id}")

            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            # Generate TEXT ID (passend zum Schema)
            project_id = f"project_{hashlib.md5(f'{user_id}_{name}_{datetime.now()}'.encode()).hexdigest()[:12]}"

            # Erstelle project_data für data-Feld
            project_data = {
                'id': project_id,
                'name': name,
                'description': description,
                'language': language,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'files': [],
                'status': 'active'
            }

            # Insert mit allen Feldern (passend zum Schema)
            cursor.execute('''
                INSERT INTO projects (id, name, description, language, user_id, status, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (project_id, name, description, language, user_id, 'active', json.dumps(project_data)))

            # Get the created project
            cursor.execute('SELECT id, name, description, language, status, created_at, updated_at FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()

            if row:
                project = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'language': row[3] or 'python',
                    'status': row[4] or 'active',
                    'created_at': row[5] or datetime.now().isoformat(),
                    'updated_at': row[6] or datetime.now().isoformat()
                }
            else:
                # Fallback
                project = {
                    'id': project_id,
                    'name': name,
                    'description': description,
                    'language': language,
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

            conn.commit()
            conn.close()

            logger.info(f"✅ Project created with ID: {project_id}")

            return {
                'success': True,
                'project': project,
                'message': f"Projekt '{name}' erfolgreich erstellt!"
            }

        except Exception as e:
            logger.error(f"❌ Error creating project: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Fehler beim Erstellen des Projekts: {str(e)}"
            }

    def update_project(self, project_id: str, user_id: str, **kwargs) -> Dict:
        """Update an existing project"""
        try:
            logger.info(f"📝 Updating project {project_id} for user {user_id}")

            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = []
            values = []

            for field in ['name', 'description', 'language', 'status']:
                if field in kwargs:
                    update_fields.append(f"{field} = ?")
                    values.append(kwargs[field])

            if not update_fields:
                return {'success': False, 'error': 'Keine Update-Felder angegeben'}

            # Add updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.extend([project_id, user_id])

            query = f'''
                UPDATE projects 
                SET {', '.join(update_fields)}
                WHERE id = ? AND user_id = ?
            '''

            cursor.execute(query, values)

            if cursor.rowcount == 0:
                conn.close()
                return {'success': False, 'error': 'Projekt nicht gefunden oder keine Berechtigung'}

            # Get updated project
            cursor.execute('SELECT id, name, description, language, status, created_at, updated_at FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id))
            row = cursor.fetchone()

            if row:
                project = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'language': row[3] or 'python',
                    'status': row[4] or 'active',
                    'created_at': row[5],
                    'updated_at': row[6]
                }
            else:
                project = None

            conn.commit()
            conn.close()

            logger.info(f"✅ Project {project_id} updated successfully")

            return {
                'success': True,
                'project': project,
                'message': 'Projekt erfolgreich aktualisiert!'
            }

        except Exception as e:
            logger.error(f"❌ Error updating project: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Fehler beim Aktualisieren: {str(e)}"
            }

    def delete_project(self, project_id: str, user_id: str) -> Dict:
        """Delete a project"""
        try:
            logger.info(f"🗑️ Deleting project {project_id} for user {user_id}")

            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            # Check if project exists and belongs to user
            cursor.execute('SELECT name FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return {'success': False, 'error': 'Projekt nicht gefunden oder keine Berechtigung'}

            project_name = row[0]

            # Delete project
            cursor.execute('DELETE FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id))

            conn.commit()
            conn.close()

            logger.info(f"✅ Project '{project_name}' deleted successfully")

            return {
                'success': True,
                'message': f"Projekt '{project_name}' erfolgreich gelöscht!"
            }

        except Exception as e:
            logger.error(f"❌ Error deleting project: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Fehler beim Löschen: {str(e)}"
            }

    # =====================================
    # CODE ANALYSIS
    # =====================================

    def analyze_code(self, code: str, language: str = "python") -> Dict:
        """Enhanced code analysis with Claude API"""
        try:
            if self.client:
                # Create structured prompt for code analysis
                prompt = f"""Analysiere den folgenden {language}-Code und gib eine strukturierte Bewertung zurück:

```{language}
{code}
```

Bewerte folgende Aspekte:
1. Funktionalität und Korrektheit
2. Code-Qualität und Lesbarkeit
3. Potentielle Probleme oder Bugs
4. Verbesserungsvorschläge

Gib einen Score zwischen 0-100 und konkrete Verbesserungsvorschläge."""

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )

                analysis_text = response.content[0].text

                # Extract score (simple pattern matching)
                score = 75  # Default
                score_patterns = [r'score.*?(\d{1,3})', r'bewertung.*?(\d{1,3})', r'(\d{1,3})\s*/\s*100']
                for pattern in score_patterns:
                    match = re.search(pattern, analysis_text.lower())
                    if match:
                        score = max(0, min(100, int(match.group(1))))
                        break

                return {
                    'success': True,
                    'analysis': analysis_text,
                    'quality_score': score,
                    'suggestions': [
                        "Code-Analyse mit Claude API durchgeführt",
                        "Detaillierte Bewertung im Analysis-Text"
                    ],
                    'model_used': self.model
                }
            else:
                # Fallback analysis
                return self._create_fallback_analysis(code, language)

        except Exception as e:
            logger.error(f"❌ Code analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': "Fehler bei der Code-Analyse",
                'fallback_analysis': self._create_fallback_analysis(code, language)
            }

    def _create_fallback_analysis(self, code: str, language: str) -> Dict:
        """Create fallback analysis when Claude API is unavailable"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Basic metrics
        total_lines = len(lines)
        code_lines = len(non_empty_lines)
        comment_lines = len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')])

        # Simple quality score
        comment_ratio = comment_lines / max(code_lines, 1)
        base_score = 70
        if comment_ratio > 0.1:
            base_score += 10
        if code_lines < 50:
            base_score += 5

        quality_score = max(50, min(95, base_score))

        return {
            'success': True,
            'analysis': f"Fallback-Analyse: {code_lines} Zeilen {language} Code analysiert. Code-Struktur erscheint {'gut organisiert' if quality_score > 75 else 'verbesserungsfähig'}.",
            'quality_score': quality_score,
            'suggestions': [
                'Mehr Kommentare hinzufügen' if comment_ratio < 0.1 else 'Dokumentation ist angemessen',
                'Code-Struktur überprüfen',
                'Error-Handling implementieren'
            ],
            'model_used': 'Fallback-Analyse'
        }

    # =====================================
    # UTILITY METHODS
    # =====================================

    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for a user"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT message, response, timestamp, context, model_used FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (user_id, limit)
                )

                history = []
                for row in cursor.fetchall():
                    history.append({
                        'message': row[0],
                        'response': row[1],
                        'timestamp': row[2],
                        'context': row[3],
                        'model_used': row[4]
                    })

                return list(reversed(history))

        except Exception as e:
            logger.error(f"❌ Error getting chat history: {e}")
            return []

    def get_metrics(self, user_id: str = None) -> Dict:
        """Get bot usage metrics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                if user_id:
                    # User-specific metrics
                    cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (user_id,))
                    user_messages = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = ?", (user_id,))
                    user_projects = cursor.fetchone()[0]

                    return {
                        'user_messages': user_messages,
                        'user_projects': user_projects,
                        'api_status': "Connected" if self.client else "Fallback Mode",
                        'current_model': self.model
                    }
                else:
                    # Global metrics
                    cursor.execute("SELECT COUNT(*) FROM chat_history")
                    total_messages = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM projects")
                    total_projects = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM chat_history")
                    active_users = cursor.fetchone()[0]

                    return {
                        'total_messages': total_messages,
                        'total_projects': total_projects,
                        'active_users': active_users,
                        'api_status': "Connected" if self.client else "Fallback Mode",
                        'current_model': self.model
                    }

        except Exception as e:
            logger.error(f"❌ Error getting metrics: {e}")
            return {
                'error': str(e),
                'api_status': 'Error',
                'current_model': self.model
            }

# Compatibility layer for existing code
class BotEngine(ClaudeAPIEngine):
    """Compatibility wrapper for existing code"""
    pass

# Factory function for easy initialization
def create_bot_engine(api_key: str = None, model: str = None, max_tokens: int = 1000) -> ClaudeAPIEngine:
    """Create and return a bot engine instance with Smart Config support"""
    return ClaudeAPIEngine(api_key=api_key, model=model, max_tokens=max_tokens)