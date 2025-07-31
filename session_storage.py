"""
Session Storage System - SQLite Backend für Session Management
"""

import sqlite3
import json
import datetime
from typing import Dict, List, Optional, Any
import os
import logging

logger = logging.getLogger(__name__)

class SessionStorage:
    """
    Professional Session & Recovery Storage System
    Speichert:
    - User Sessions mit Context
    - Project Continuity Data
    - Code Review History
    - Smart Suggestions History
    - Cross-Session Learning Data
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        """Initialize session storage with SQLite database"""
        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)

        # Initialize database schema
        self._init_database()

    # MINIMALER FIX: Ersetze nur diese _init_database Method in deiner session_storage.py

    def _init_database(self):
        """Create all necessary tables for session management - FIXED INDEX SYNTAX"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 1. USER SESSIONS TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS user_sessions
                           (
                               session_id
                               TEXT
                               PRIMARY
                               KEY,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               project_id
                               TEXT,
                               session_name
                               TEXT,
                               created_at
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               last_active
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               is_active
                               BOOLEAN
                               DEFAULT
                               1,
                               session_context
                               TEXT,
                               session_summary
                               TEXT
                           )
                           """)

            # 2. CONVERSATION HISTORY TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS conversation_history
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               session_id
                               TEXT
                               NOT
                               NULL,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               message_type
                               TEXT
                               NOT
                               NULL,
                               message_content
                               TEXT
                               NOT
                               NULL,
                               timestamp
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               message_context
                               TEXT,
                               FOREIGN
                               KEY
                           (
                               session_id
                           ) REFERENCES user_sessions
                           (
                               session_id
                           )
                               )
                           """)

            # 3. CODE REVIEW HISTORY TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS code_reviews
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               session_id
                               TEXT
                               NOT
                               NULL,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               file_name
                               TEXT,
                               file_path
                               TEXT,
                               language
                               TEXT
                               NOT
                               NULL,
                               original_code
                               TEXT
                               NOT
                               NULL,
                               review_score
                               INTEGER,
                               review_feedback
                               TEXT,
                               suggestions
                               TEXT,
                               issues_found
                               TEXT,
                               improvements_made
                               TEXT,
                               review_timestamp
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               is_resolved
                               BOOLEAN
                               DEFAULT
                               0,
                               FOREIGN
                               KEY
                           (
                               session_id
                           ) REFERENCES user_sessions
                           (
                               session_id
                           )
                               )
                           """)

            # 4. PROJECT PROGRESS TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS project_progress
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               session_id
                               TEXT
                               NOT
                               NULL,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               project_name
                               TEXT
                               NOT
                               NULL,
                               milestone_name
                               TEXT,
                               task_description
                               TEXT,
                               task_status
                               TEXT
                               DEFAULT
                               'open',
                               priority
                               INTEGER
                               DEFAULT
                               3,
                               estimated_hours
                               REAL,
                               actual_hours
                               REAL,
                               completion_percentage
                               INTEGER
                               DEFAULT
                               0,
                               created_at
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               completed_at
                               DATETIME,
                               task_context
                               TEXT,
                               FOREIGN
                               KEY
                           (
                               session_id
                           ) REFERENCES user_sessions
                           (
                               session_id
                           )
                               )
                           """)

            # 5. SMART SUGGESTIONS TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS smart_suggestions
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               session_id
                               TEXT,
                               suggestion_type
                               TEXT
                               NOT
                               NULL,
                               suggestion_title
                               TEXT
                               NOT
                               NULL,
                               suggestion_description
                               TEXT,
                               suggestion_priority
                               INTEGER
                               DEFAULT
                               3,
                               relevance_score
                               REAL
                               DEFAULT
                               0.5,
                               generated_at
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               applied_at
                               DATETIME,
                               is_applied
                               BOOLEAN
                               DEFAULT
                               0,
                               suggestion_context
                               TEXT
                           )
                           """)

            # 6. USER LEARNING PATTERNS TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS user_learning_patterns
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               pattern_type
                               TEXT
                               NOT
                               NULL,
                               pattern_key
                               TEXT
                               NOT
                               NULL,
                               pattern_value
                               TEXT,
                               confidence_score
                               REAL
                               DEFAULT
                               0.5,
                               observation_count
                               INTEGER
                               DEFAULT
                               1,
                               first_observed
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               last_observed
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               UNIQUE
                           (
                               user_id,
                               pattern_type,
                               pattern_key
                           )
                               )
                           """)

            # 7. SESSION RECOVERY METADATA TABLE - ENTFERNE INDEX() ZEILEN
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS session_recovery_metadata
                           (
                               session_id
                               TEXT
                               PRIMARY
                               KEY,
                               user_id
                               TEXT
                               NOT
                               NULL,
                               recovery_priority
                               INTEGER
                               DEFAULT
                               3,
                               last_significant_action
                               TEXT,
                               next_suggested_actions
                               TEXT,
                               session_health_score
                               REAL
                               DEFAULT
                               1.0,
                               recovery_context
                               TEXT,
                               updated_at
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               FOREIGN
                               KEY
                           (
                               session_id
                           ) REFERENCES user_sessions
                           (
                               session_id
                           )
                               )
                           """)

            # CREATE INDEXES SEPARATELY (OPTIONAL - for performance)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation_history(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_reviews_session_id ON code_reviews(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_progress_session_id ON project_progress(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_smart_suggestions_user_id ON smart_suggestions(user_id)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_recovery_metadata_user_id ON session_recovery_metadata(user_id)")

            conn.commit()
            logger.info("✅ Session storage database initialized successfully")

    # =====================================
    # SESSION MANAGEMENT METHODS
    # =====================================

    def create_session(self, user_id: str, project_name: str = None, session_context: Dict = None) -> str:
        """Create a new user session"""
        import uuid

        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session_name = project_name or f"Session {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create session
            cursor.execute("""
                INSERT INTO user_sessions 
                (session_id, user_id, project_id, session_name, session_context, session_summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                project_name,
                session_name,
                json.dumps(session_context or {}),
                f"Neues Projekt: {project_name}" if project_name else "Neue Programming Session"
            ))

            # Create recovery metadata
            cursor.execute("""
                INSERT INTO session_recovery_metadata
                (session_id, user_id, last_significant_action, recovery_context)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                "Session erstellt",
                json.dumps({
                    "project_name": project_name,
                    "created_at": datetime.datetime.now().isoformat(),
                    "session_type": "new_project" if project_name else "general_programming"
                })
            ))

            conn.commit()

        logger.info(f"✅ Created new session {session_id} for user {user_id}")
        return session_id

    def update_session_activity(self, session_id: str, activity_type: str, activity_data: Dict = None):
        """Update session with latest activity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Update session timestamp
            cursor.execute("""
                UPDATE user_sessions 
                SET last_active = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (session_id,))

            # Update recovery metadata
            cursor.execute("""
                UPDATE session_recovery_metadata
                SET last_significant_action = ?,
                    recovery_context = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (
                activity_type,
                json.dumps(activity_data or {}),
                session_id
            ))

            conn.commit()

    def get_user_sessions_for_recovery(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent sessions for recovery display"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.session_id,
                    s.session_name,
                    s.project_id,
                    s.last_active,
                    s.session_summary,
                    r.recovery_priority,
                    r.last_significant_action,
                    r.next_suggested_actions,
                    r.session_health_score
                FROM user_sessions s
                LEFT JOIN session_recovery_metadata r ON s.session_id = r.session_id
                WHERE s.user_id = ? AND s.is_active = 1
                ORDER BY r.recovery_priority ASC, s.last_active DESC
                LIMIT ?
            """, (user_id, limit))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'session_name': row[1],
                    'project_id': row[2],
                    'last_active': row[3],
                    'session_summary': row[4],
                    'recovery_priority': row[5] or 3,
                    'last_significant_action': row[6],
                    'next_suggested_actions': json.loads(row[7] or '[]'),
                    'session_health_score': row[8] or 1.0
                })

            return sessions

    # =====================================
    # CONVERSATION HISTORY METHODS
    # =====================================

    def save_conversation_message(self, session_id: str, user_id: str, message_type: str,
                                content: str, context: Dict = None):
        """Save a conversation message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_history
                (session_id, user_id, message_type, message_content, message_context)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                message_type,
                content,
                json.dumps(context or {})
            ))
            conn.commit()

    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_type, message_content, timestamp, message_context
                FROM conversation_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'type': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'context': json.loads(row[3] or '{}')
                })

            return list(reversed(messages))  # Return in chronological order

    # =====================================
    # CODE REVIEW STORAGE METHODS
    # =====================================

    def save_code_review(self, session_id: str, user_id: str, code: str, language: str,
                        review_result: Dict) -> int:
        """Save a code review result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO code_reviews
                (session_id, user_id, language, original_code, review_score, 
                 review_feedback, suggestions, issues_found)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                language,
                code,
                review_result.get('score', 70),
                review_result.get('feedback', ''),
                json.dumps(review_result.get('suggestions', [])),
                json.dumps(review_result.get('issues', []))
            ))

            review_id = cursor.lastrowid
            conn.commit()
            return review_id

    def get_recent_code_reviews(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent code reviews for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_name, language, review_score, review_feedback, 
                       suggestions, review_timestamp, is_resolved
                FROM code_reviews
                WHERE session_id = ?
                ORDER BY review_timestamp DESC
                LIMIT ?
            """, (session_id, limit))

            reviews = []
            for row in cursor.fetchall():
                reviews.append({
                    'file_name': row[0],
                    'language': row[1],
                    'score': row[2],
                    'feedback': row[3],
                    'suggestions': json.loads(row[4] or '[]'),
                    'timestamp': row[5],
                    'is_resolved': bool(row[6])
                })

            return reviews