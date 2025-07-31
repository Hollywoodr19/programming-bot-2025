#!/usr/bin/env python3
"""
auth_system.py - Fixed Authentication System
Fügt fehlende authenticate_user Methode hinzu
"""

import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import bcrypt
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class User:
    id: int
    username: str
    email: str
    display_name: str
    created_at: str
    last_login: Optional[str] = None
    preferences: Optional[Dict] = None
    is_admin: bool = False


@dataclass
class Project:
    id: int
    user_id: int
    name: str
    description: str
    language: str
    status: str
    created_at: str
    updated_at: str
    config: Optional[Dict] = None


@dataclass
class Session:
    user_id: int
    session_token: str
    expires_at: str
    ip_address: str


class AuthenticationSystem:
    """Vollständiges Multi-User Authentication System mit fehlender authenticate_user Methode"""

    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = db_path
        self.init_database()

    def check_username_available(self, username):
        """
        Check if a username is available for registration

        Args:
            username (str): Username to check

        Returns:
            bool: True if username is available, False if taken
        """
        try:
            # Clean the username
            username = username.strip().lower()

            # Check minimum length
            if len(username) < 3:
                print(f"❌ Username '{username}' too short")
                return False

            # Check maximum length
            if len(username) > 50:
                print(f"❌ Username '{username}' too long")
                return False

            # Create a new connection for this check (like other methods do)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if username already exists in database
                cursor.execute(
                    "SELECT username FROM users WHERE LOWER(username) = ?",
                    (username,)
                )

                result = cursor.fetchone()

                # Return True if no user found (username available)
                available = result is None

                if available:
                    print(f"✅ Username '{username}' is available")
                else:
                    print(f"❌ Username '{username}' is already taken")

                return available

        except Exception as e:
            print(f"❌ Error checking username availability: {e}")
            # Return True on error to allow registration attempt
            return True

    def get_user_count(self):
        """
        Get total number of registered users

        Returns:
            int: Number of users in database
        """
        try:
            # Create a new connection for this check
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            print(f"❌ Error getting user count: {e}")
            return 0

            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            print(f"❌ Error getting user count: {e}")
            return 0

    def init_database(self):
        """Initialisiert Auth-Datenbank mit allen Tabellen"""
        try:
            # Ensure data directory exists
            import os
            os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Users Tabelle
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS users
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   username
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   email
                                   TEXT
                                   UNIQUE,
                                   password_hash
                                   TEXT
                                   NOT
                                   NULL,
                                   display_name
                                   TEXT
                                   NOT
                                   NULL,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   last_login
                                   TIMESTAMP,
                                   is_admin
                                   BOOLEAN
                                   DEFAULT
                                   FALSE,
                                   is_active
                                   BOOLEAN
                                   DEFAULT
                                   TRUE,
                                   preferences
                                   JSON
                                   DEFAULT
                                   '{}',
                                   avatar_url
                                   TEXT,
                                   bio
                                   TEXT
                               )
                               ''')

                # Projects Tabelle
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS projects
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   user_id
                                   INTEGER
                                   NOT
                                   NULL,
                                   name
                                   TEXT
                                   NOT
                                   NULL,
                                   description
                                   TEXT,
                                   language
                                   TEXT
                                   DEFAULT
                                   'python',
                                   status
                                   TEXT
                                   DEFAULT
                                   'active',
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   updated_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   config
                                   JSON
                                   DEFAULT
                                   '{}',
                                   is_public
                                   BOOLEAN
                                   DEFAULT
                                   FALSE,
                                   tags
                                   TEXT,
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               ) ON DELETE CASCADE
                                   )
                               ''')

                # Sessions Tabelle
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS user_sessions
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   user_id
                                   INTEGER
                                   NOT
                                   NULL,
                                   session_token
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   expires_at
                                   TIMESTAMP
                                   NOT
                                   NULL,
                                   ip_address
                                   TEXT,
                                   user_agent
                                   TEXT,
                                   is_active
                                   BOOLEAN
                                   DEFAULT
                                   TRUE,
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               ) ON DELETE CASCADE
                                   )
                               ''')

                # Chat History (user-spezifisch)
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS user_conversations
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   user_id
                                   INTEGER
                                   NOT
                                   NULL,
                                   project_id
                                   INTEGER,
                                   message
                                   TEXT
                                   NOT
                                   NULL,
                                   response
                                   TEXT,
                                   timestamp
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   session_id
                                   TEXT,
                                   metadata
                                   JSON
                                   DEFAULT
                                   '{}',
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               ) ON DELETE CASCADE,
                                   FOREIGN KEY
                               (
                                   project_id
                               ) REFERENCES projects
                               (
                                   id
                               )
                                 ON DELETE SET NULL
                                   )
                               ''')

                # User Preferences/Settings
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS user_settings
                               (
                                   user_id
                                   INTEGER
                                   PRIMARY
                                   KEY,
                                   theme
                                   TEXT
                                   DEFAULT
                                   'modern',
                                   language
                                   TEXT
                                   DEFAULT
                                   'de',
                                   notifications
                                   BOOLEAN
                                   DEFAULT
                                   TRUE,
                                   auto_save
                                   BOOLEAN
                                   DEFAULT
                                   TRUE,
                                   code_style
                                   TEXT
                                   DEFAULT
                                   'pep8',
                                   editor_theme
                                   TEXT
                                   DEFAULT
                                   'dark',
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               ) ON DELETE CASCADE
                                   )
                               ''')

                conn.commit()
                logger.info("✅ Auth-Datenbank initialisiert")

                # Erstelle Admin-User falls nicht vorhanden
                self._create_default_admin()

        except Exception as e:
            logger.error(f"❌ Fehler bei Datenbank-Initialisierung: {e}")
            raise

    def _create_default_admin(self):
        """Erstellt Standard-Admin-User"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prüfe ob Admin existiert
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
                admin_count = cursor.fetchone()[0]

                if admin_count == 0:
                    # Erstelle Admin-User
                    admin_password = self._hash_password("admin123")  # Später ändern!
                    cursor.execute('''
                                   INSERT INTO users (username, email, password_hash, display_name, is_admin)
                                   VALUES (?, ?, ?, ?, ?)
                                   ''', ("admin", "admin@localhost", admin_password, "Administrator", True))

                    admin_id = cursor.lastrowid

                    # Standard-Settings für Admin
                    cursor.execute('''
                                   INSERT INTO user_settings (user_id)
                                   VALUES (?)
                                   ''', (admin_id,))

                    conn.commit()
                    logger.info("👑 Standard-Admin erstellt (username: admin, password: admin123)")
                    logger.warning("⚠️ WICHTIG: Admin-Passwort nach erstem Login ändern!")

        except Exception as e:
            logger.error(f"❌ Fehler beim Admin-Erstellen: {e}")

    def _hash_password(self, password: str) -> str:
        """Hash Passwort mit bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifiziert Passwort gegen Hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    # =====================================
    # FEHLENDE METHODE FÜR FLASK MAIN.PY
    # =====================================

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authentifiziert User und gibt User-Dict zurück (Flask-kompatibel)
        Diese Methode fehlte und verursachte den Fehler!
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # User finden
                cursor.execute('''
                               SELECT id, username, email, password_hash, display_name, is_admin, is_active
                               FROM users
                               WHERE username = ?
                                  OR email = ?
                               ''', (username, username))

                user_data = cursor.fetchone()
                if not user_data:
                    logger.warning(f"User not found: {username}")
                    return None

                user_id, db_username, email, password_hash, display_name, is_admin, is_active = user_data

                if not is_active:
                    logger.warning(f"Inactive user tried to login: {username}")
                    return None

                # Passwort prüfen
                if not self._verify_password(password, password_hash):
                    logger.warning(f"Wrong password for user: {username}")
                    return None

                # Last login aktualisieren
                cursor.execute('''
                               UPDATE users
                               SET last_login = CURRENT_TIMESTAMP
                               WHERE id = ?
                               ''', (user_id,))

                conn.commit()

                # Flask-kompatibles User-Dict zurückgeben
                user_dict = {
                    'id': user_id,
                    'username': db_username,
                    'email': email,
                    'display_name': display_name,
                    'role': 'admin' if is_admin else 'user',
                    'is_admin': bool(is_admin)
                }

                logger.info(f"✅ User authenticated: {db_username}")
                return user_dict

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return None

    def register_user(self, username: str, email: str, password: str,
                      display_name: str, created_by_admin: bool = False) -> Dict:
        """Registriert neuen User"""
        try:
            # Validierungen
            if len(username) < 3:
                return {"success": False, "error": "Username muss mindestens 3 Zeichen haben"}

            if len(password) < 6:
                return {"success": False, "error": "Passwort muss mindestens 6 Zeichen haben"}

            if "@" not in email:
                return {"success": False, "error": "Ungültige E-Mail-Adresse"}

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prüfe ob Username/Email bereits existiert
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?",
                               (username, email))
                if cursor.fetchone()[0] > 0:
                    return {"success": False, "error": "Username oder E-Mail bereits vergeben"}

                # Hash Passwort
                password_hash = self._hash_password(password)

                # User erstellen
                cursor.execute('''
                               INSERT INTO users (username, email, password_hash, display_name, is_admin)
                               VALUES (?, ?, ?, ?, ?)
                               ''', (username, email, password_hash, display_name, created_by_admin))

                user_id = cursor.lastrowid

                # Standard-Settings erstellen
                cursor.execute('''
                               INSERT INTO user_settings (user_id)
                               VALUES (?)
                               ''', (user_id,))

                conn.commit()

                logger.info(f"✅ User registriert: {username} ({display_name})")
                return {
                    "success": True,
                    "user_id": user_id,
                    "message": f"User {display_name} erfolgreich registriert!"
                }

        except Exception as e:
            logger.error(f"❌ Registrierung fehlgeschlagen: {e}")
            return {"success": False, "error": f"Registrierung fehlgeschlagen: {str(e)}"}

    def login_user(self, username: str, password: str, ip_address: str = "unknown") -> Dict:
        """User Login mit Session-Erstellung"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # User finden
                cursor.execute('''
                               SELECT id, username, email, password_hash, display_name, is_admin, is_active
                               FROM users
                               WHERE username = ?
                                  OR email = ?
                               ''', (username, username))

                user_data = cursor.fetchone()
                if not user_data:
                    return {"success": False, "error": "User nicht gefunden"}

                user_id, db_username, email, password_hash, display_name, is_admin, is_active = user_data

                if not is_active:
                    return {"success": False, "error": "Account deaktiviert"}

                # Passwort prüfen
                if not self._verify_password(password, password_hash):
                    return {"success": False, "error": "Falsches Passwort"}

                # Session erstellen
                session_token = secrets.token_urlsafe(64)
                expires_at = datetime.now() + timedelta(days=7)  # 7 Tage Session

                cursor.execute('''
                               INSERT INTO user_sessions
                                   (user_id, session_token, expires_at, ip_address)
                               VALUES (?, ?, ?, ?)
                               ''', (user_id, session_token, expires_at, ip_address))

                # Last login aktualisieren
                cursor.execute('''
                               UPDATE users
                               SET last_login = CURRENT_TIMESTAMP
                               WHERE id = ?
                               ''', (user_id,))

                conn.commit()

                logger.info(f"✅ Login erfolgreich: {db_username} ({display_name})")

                return {
                    "success": True,
                    "session_token": session_token,
                    "user": {
                        "id": user_id,
                        "username": db_username,
                        "email": email,
                        "display_name": display_name,
                        "is_admin": bool(is_admin)
                    },
                    "expires_at": expires_at.isoformat()
                }

        except Exception as e:
            logger.error(f"❌ Login fehlgeschlagen: {e}")
            return {"success": False, "error": f"Login fehlgeschlagen: {str(e)}"}

    def validate_session(self, session_token: str) -> Optional[User]:
        """Validiert Session und gibt User zurück"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT u.id,
                                      u.username,
                                      u.email,
                                      u.display_name,
                                      u.created_at,
                                      u.last_login,
                                      u.preferences,
                                      u.is_admin
                               FROM users u
                                        JOIN user_sessions s ON u.id = s.user_id
                               WHERE s.session_token = ?
                                 AND s.expires_at > CURRENT_TIMESTAMP
                                 AND s.is_active = TRUE
                                 AND u.is_active = TRUE
                               ''', (session_token,))

                user_data = cursor.fetchone()
                if user_data:
                    return User(
                        id=user_data[0],
                        username=user_data[1],
                        email=user_data[2],
                        display_name=user_data[3],
                        created_at=user_data[4],
                        last_login=user_data[5],
                        preferences=json.loads(user_data[6] or "{}"),
                        is_admin=bool(user_data[7])
                    )
                return None

        except Exception as e:
            logger.error(f"❌ Session-Validierung fehlgeschlagen: {e}")
            return None

    def logout_user(self, session_token: str) -> bool:
        """Logged User aus (deaktiviert Session)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE user_sessions
                               SET is_active = FALSE
                               WHERE session_token = ?
                               ''', (session_token,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Logout fehlgeschlagen: {e}")
            return False

    def get_user_projects(self, user_id: int) -> List[Project]:
        """Holt alle Projekte eines Users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                               SELECT id, user_id, name, description, language, status, created_at, updated_at, config
                               FROM projects
                               WHERE user_id = ?
                               ORDER BY updated_at DESC
                               ''', (user_id,))

                projects = []
                for row in cursor.fetchall():
                    projects.append(Project(
                        id=row[0], user_id=row[1], name=row[2],
                        description=row[3], language=row[4], status=row[5],
                        created_at=row[6], updated_at=row[7],
                        config=json.loads(row[8] or "{}")
                    ))
                return projects

        except Exception as e:
            logger.error(f"❌ Projekt-Abruf fehlgeschlagen: {e}")
            return []

    def create_project(self, user_id: int, name: str, description: str = "",
                       language: str = "python") -> Dict:
        """Erstellt neues Projekt für User"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prüfe ob Projektname bereits existiert
                cursor.execute('''
                               SELECT COUNT(*)
                               FROM projects
                               WHERE user_id = ?
                                 AND name = ?
                               ''', (user_id, name))

                if cursor.fetchone()[0] > 0:
                    return {"success": False, "error": "Projekt-Name bereits vergeben"}

                # Projekt erstellen
                cursor.execute('''
                               INSERT INTO projects (user_id, name, description, language)
                               VALUES (?, ?, ?, ?)
                               ''', (user_id, name, description, language))

                project_id = cursor.lastrowid
                conn.commit()

                logger.info(f"✅ Projekt erstellt: {name} für User {user_id}")
                return {"success": True, "project_id": project_id}

        except Exception as e:
            logger.error(f"❌ Projekt-Erstellung fehlgeschlagen: {e}")
            return {"success": False, "error": str(e)}

    def get_user_stats(self, user_id: int) -> Dict:
        """Holt User-Statistiken"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Projekt-Stats
                cursor.execute('''
                               SELECT COUNT(*)                                         as total,
                                      COUNT(CASE WHEN status = 'active' THEN 1 END)    as active,
                                      COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                               FROM projects
                               WHERE user_id = ?
                               ''', (user_id,))
                project_stats = cursor.fetchone()

                # Chat-Stats
                cursor.execute('''
                               SELECT COUNT(*)
                               FROM user_conversations
                               WHERE user_id = ?
                               ''', (user_id,))
                chat_count = cursor.fetchone()[0]

                # Letztes Login
                cursor.execute('''
                               SELECT last_login
                               FROM users
                               WHERE id = ?
                               ''', (user_id,))
                last_login = cursor.fetchone()[0]

                return {
                    "projects": {
                        "total": project_stats[0],
                        "active": project_stats[1],
                        "completed": project_stats[2]
                    },
                    "conversations": chat_count,
                    "last_login": last_login
                }

        except Exception as e:
            logger.error(f"❌ Stats-Abruf fehlgeschlagen: {e}")
            return {}


# Quick Test Funktion
def test_auth_system():
    """Testet das Auth-System"""
    auth = AuthenticationSystem("test_auth.db")

    print("🧪 Teste Authentication System...")

    # Test authenticate_user (für Flask)
    result = auth.authenticate_user("admin", "admin123")
    print(f"Flask authenticate_user: {result}")

    # Test Registration
    reg_result = auth.register_user("testuser", "test@example.com", "password123", "Test User")
    print(f"Registration: {reg_result}")

    # Test Login
    login_result = auth.login_user("testuser", "password123")
    print(f"Login: {login_result}")

    if login_result["success"]:
        token = login_result["session_token"]

        # Test Session Validation
        user = auth.validate_session(token)
        print(f"Session Valid: {user.display_name if user else 'Invalid'}")

        # Test Project Creation
        project_result = auth.create_project(user.id, "Test Project", "Mein erstes Projekt")
        print(f"Project Creation: {project_result}")

        # Test User Stats
        stats = auth.get_user_stats(user.id)
        print(f"User Stats: {stats}")

    print("✅ Auth-System Test abgeschlossen!")


if __name__ == "__main__":
    test_auth_system()