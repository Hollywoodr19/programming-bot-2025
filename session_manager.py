"""
Enhanced Session Manager for Programming Bot 2025
FIXED: Prevents immediate exit by controlling cleanup thread lifecycle
"""

import json
import os
import uuid
import hashlib
import threading
import time
import atexit
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pathlib import Path

class SessionManager:
    """Enhanced Session Manager with controlled thread lifecycle"""

    def __init__(self, session_file: str = "data/sessions.json", auto_cleanup: bool = True):
        self.session_file = Path(session_file)
        self.sessions: Dict[str, Dict] = {}
        self.cleanup_interval_minutes = 60
        self.cleanup_thread = None
        self.cleanup_running = False
        self._shutdown_requested = False

        # Ensure data directory exists
        self.session_file.parent.mkdir(exist_ok=True)

        # Load existing sessions
        self._load_sessions()

        # Only start cleanup thread if auto_cleanup is True AND we're in main thread
        if auto_cleanup and threading.current_thread() is threading.main_thread():
            self._start_cleanup_thread()

        print(f"✅ Enhanced Session Manager initialized")
        print(f"   Session File: {self.session_file}")
        print(f"   Loaded Sessions: {len(self.sessions)}")
        print(f"   Cleanup Interval: {self.cleanup_interval_minutes}min")

        # Register cleanup only if we started the cleanup thread
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            atexit.register(self._safe_shutdown)

    def _load_sessions(self):
        """Load sessions from JSON file with improved error handling"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        # Validate session data structure
                        if isinstance(data, dict):
                            # Filter out invalid sessions during load
                            valid_sessions = {}
                            for session_id, session_data in data.items():
                                if self._is_valid_session_data(session_data):
                                    valid_sessions[session_id] = session_data

                            self.sessions = valid_sessions
                            print(f"✅ Sessions loaded from {self.session_file}")
                            return

            print(f"📝 No existing sessions found, starting fresh")
            self.sessions = {}

        except json.JSONDecodeError as e:
            print(f"⚠️  Error loading sessions from {self.session_file}: Invalid JSON")
            self._try_load_backup()
        except Exception as e:
            print(f"⚠️  Error loading sessions from {self.session_file}: {e}")
            self._try_load_backup()

    def _is_valid_session_data(self, session_data: Any) -> bool:
        """Validate session data structure"""
        if not isinstance(session_data, dict):
            return False

        required_fields = ['user_id', 'created_at']
        return all(field in session_data for field in required_fields)

    def _try_load_backup(self):
        """Try to load from backup files"""
        for i in range(1, 4):  # Try backup1, backup2, backup3
            backup_file = Path(f"{self.session_file}.backup{i}")
            if backup_file.exists():
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            if isinstance(data, dict):
                                valid_sessions = {}
                                for session_id, session_data in data.items():
                                    if self._is_valid_session_data(session_data):
                                        valid_sessions[session_id] = session_data

                                if valid_sessions:
                                    self.sessions = valid_sessions
                                    print(f"✅ Sessions restored from backup: {backup_file}")
                                    return
                except Exception as e:
                    print(f"⚠️  Error loading backup {backup_file}: {e}")
                    continue

        # If all backups fail, start fresh
        print(f"📝 No valid backups found, starting fresh")
        self.sessions = {}

    def _save_sessions(self):
        """Save sessions to JSON file with backup"""
        try:
            # Create backup before saving
            if self.session_file.exists():
                backup_file = Path(f"{self.session_file}.backup1")
                if backup_file.exists():
                    # Rotate backups: backup1 -> backup2 -> backup3
                    for i in range(3, 1, -1):
                        src = Path(f"{self.session_file}.backup{i-1}")
                        dst = Path(f"{self.session_file}.backup{i}")
                        if src.exists():
                            if dst.exists():
                                dst.unlink()
                            src.rename(dst)

                # Create new backup1
                import shutil
                shutil.copy2(self.session_file, backup_file)

            # Save current sessions
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️  Error saving sessions: {e}")

    def _start_cleanup_thread(self):
        """Start the cleanup thread with proper lifecycle management"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return  # Already running

        self.cleanup_running = True
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="SessionCleanup",
            daemon=True  # Important: Make it a daemon thread
        )
        self.cleanup_thread.start()
        print(f"🧹 Session cleanup thread started (interval: {self.cleanup_interval_minutes}min)")

    def _cleanup_loop(self):
        """Background cleanup loop with proper exit handling"""
        while self.cleanup_running and not self._shutdown_requested:
            try:
                # Use smaller sleep intervals to allow faster shutdown
                for _ in range(self.cleanup_interval_minutes * 60):  # 60 seconds per minute
                    if self._shutdown_requested:
                        break
                    time.sleep(1)

                if not self._shutdown_requested:
                    self._cleanup_expired_sessions()

            except Exception as e:
                print(f"⚠️  Session cleanup error: {e}")
                # Continue the loop even if cleanup fails
                time.sleep(60)  # Wait a minute before retrying

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            now = datetime.now()
            expired_sessions = []

            for session_id, session_data in self.sessions.items():
                try:
                    expires_at_str = session_data.get('expires_at')
                    if expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if now > expires_at:
                            expired_sessions.append(session_id)
                except (ValueError, TypeError):
                    # Invalid date format, mark for removal
                    expired_sessions.append(session_id)

            # Remove expired sessions
            for session_id in expired_sessions:
                del self.sessions[session_id]

            if expired_sessions:
                print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
                self._save_sessions()

        except Exception as e:
            print(f"⚠️  Error during session cleanup: {e}")

    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())

        # Add session metadata
        session_data.update({
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'ip_hash': session_data.get('ip_hash', ''),
            'user_agent_hash': hashlib.sha256(
                session_data.get('user_agent', '').encode()
            ).hexdigest()[:16]
        })

        self.sessions[session_id] = session_data
        self._save_sessions()

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]

            # Check if session is expired
            try:
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    del self.sessions[session_id]
                    self._save_sessions()
                    return None
            except (KeyError, ValueError):
                # Invalid expiration date, remove session
                del self.sessions[session_id]
                self._save_sessions()
                return None

            # Update last accessed time
            session_data['last_accessed'] = datetime.now().isoformat()
            self._save_sessions()

            return session_data

        return None

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]['last_accessed'] = datetime.now().isoformat()
            self._save_sessions()
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        user_sessions = []
        for session_data in self.sessions.values():
            if session_data.get('user_id') == user_id:
                user_sessions.append(session_data)
        return user_sessions

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions (admin only)"""
        return self.sessions.copy()

    def _safe_shutdown(self):
        """Safely shutdown the session manager"""
        if self._shutdown_requested:
            return  # Already shutting down

        print("🛑 Shutting down Session Manager...")
        self._shutdown_requested = True
        self.cleanup_running = False

        # Wait for cleanup thread to finish (with timeout)
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2.0)

        # Final save
        try:
            self._save_sessions()
            print("✅ Final session save completed")
        except Exception as e:
            print(f"⚠️  Error during final save: {e}")

    def __del__(self):
        """Destructor - only run safe shutdown if we haven't already"""
        if not self._shutdown_requested:
            self._safe_shutdown()


# Factory function for creating session manager
def create_session_manager(session_file: str = "data/sessions.json", auto_cleanup: bool = None) -> SessionManager:
    """
    Factory function to create session manager with smart auto_cleanup detection

    Args:
        session_file: Path to session file
        auto_cleanup: Override auto cleanup behavior. If None, auto-detect based on context

    Returns:
        SessionManager instance
    """

    # Smart auto-cleanup detection
    if auto_cleanup is None:
        # Only enable auto-cleanup if we're running in the main application
        # This prevents cleanup threads when importing for testing or debugging
        import sys
        main_module = sys.modules.get('__main__')

        if main_module and hasattr(main_module, '__file__'):
            main_file = Path(main_module.__file__).name
            # Enable auto-cleanup only for main.py or app.py
            auto_cleanup = main_file in ['main.py', 'app.py']
        else:
            auto_cleanup = False

    return SessionManager(session_file, auto_cleanup)


# Export for backward compatibility
SessionManager = SessionManager

# For direct imports, create a default instance without auto-cleanup
# This prevents immediate shutdown when importing from other modules
if __name__ != '__main__':
    # When imported, create without auto-cleanup to prevent thread issues
    default_session_manager = create_session_manager(auto_cleanup=False)
else:
    # When run directly, create with auto-cleanup enabled
    default_session_manager = create_session_manager(auto_cleanup=True)