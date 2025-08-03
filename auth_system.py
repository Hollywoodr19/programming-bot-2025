"""
Enhanced Authentication System for Programming Bot 2025 - V2
- Alle Code-Duplizierungen eliminiert
- Hardcodierte Werte in Config ausgelagert
- Spezifisches Logging mit sicheren User-Messages
- Bessere Exception Handling
- Production-Ready Security
"""
import threading
from flask import Blueprint, request, jsonify, session, current_app, flash, redirect, url_for, render_template
from werkzeug.local import LocalProxy
import os
import hashlib
import secrets
import bcrypt
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
from pathlib import Path

from flask import Blueprint

# Initialisieren Sie das Blueprint hier auf globaler Ebene
auth_bp = Blueprint('auth', __name__, template_folder='templates')


class SecurityConfig:
    """Zentrale Sicherheitskonfiguration mit Config-File Support"""

    # Environment Variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_TIMEOUT_HOURS = int(os.environ.get('SESSION_TIMEOUT_HOURS', '24'))
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5'))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', '12'))

    # Config File
    CONFIG_FILE = "security_config.json"

    @classmethod
    def _load_security_config(cls) -> Dict:
        """Lädt Security Config aus File"""
        try:
            if Path(cls.CONFIG_FILE).exists():
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load {cls.CONFIG_FILE}: {e}")

        # Default Config
        default_config = {
            "common_passwords": [
                "password", "123456789", "qwertz123", "admin123",
                "passwort", "admin", "test123", "welcome123",
                "password123", "123456", "qwerty", "abc123",
                "letmein", "monkey", "1234567890", "dragon"
            ],
            "default_admin": {
                "username": "admin",
                "password": "TempAdmin2025!@#$%",
                "force_change": True
            },
            "security_settings": {
                "min_password_entropy": 50,
                "lockout_duration_minutes": 15,
                "session_cleanup_hours": 168  # 1 week
            }
        }

        # Save default config
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"✅ Created default {cls.CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Could not create {cls.CONFIG_FILE}: {e}")

        return default_config

    @classmethod
    def get_security_config(cls) -> Dict:
        """Holt vollständige Security Config"""
        return cls._load_security_config()


    @classmethod
    def generate_secret_key(cls) -> str:
        """Generiert einen sicheren Secret Key"""
        return secrets.token_urlsafe(32)

    @classmethod
    def get_secret_key(cls) -> str:
        """Holt oder generiert Secret Key"""
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = cls.generate_secret_key()
            print("⚠️  WARNING: SECRET_KEY not in environment. Generated temporary key.")
            print("   For production, set SECRET_KEY environment variable!")
        return cls.SECRET_KEY

class AuthenticationError(Exception):
    """Authentication specific errors with secure logging"""
    def __init__(self, message: str, log_details: str = None, user_message: str = None):
        super().__init__(message)
        self.log_details = log_details or message
        self.user_message = user_message or "Authentifizierung fehlgeschlagen"

class PasswordValidationError(Exception):
    """Password validation errors"""
    def __init__(self, message: str, feedback: List[str] = None):
        super().__init__(message)
        self.feedback = feedback or []

class RateLimitError(Exception):
    """Rate limiting errors"""
    def __init__(self, username: str, retry_after_minutes: int = 15):
        self.username = username
        self.retry_after_minutes = retry_after_minutes
        super().__init__(f"Rate limit exceeded for {username}")

class PasswordValidator:
    """Erweiterte Password Validation mit Config-Support"""

    def __init__(self, config: Dict):
        self.config = config
        self.common_passwords = set(
            pwd.lower() for pwd in config.get('common_passwords', [])
        )
        self.min_entropy = config.get('security_settings', {}).get('min_password_entropy', 50)

    def validate_password(self, password: str) -> Tuple[bool, str, List[str]]:
        """Erweiterte Password Validation mit detailliertem Feedback"""
        feedback = []
        score = 0

        # Length check
        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            feedback.append(f"Mindestens {SecurityConfig.PASSWORD_MIN_LENGTH} Zeichen erforderlich")
            return False, f"Passwort muss mindestens {SecurityConfig.PASSWORD_MIN_LENGTH} Zeichen haben", feedback

        # Character variety checks
        checks = [
            (r'[A-Z]', "Großbuchstaben fehlen", "Mindestens einen Großbuchstaben"),
            (r'[a-z]', "Kleinbuchstaben fehlen", "Mindestens einen Kleinbuchstaben"),
            (r'\d', "Zahlen fehlen", "Mindestens eine Zahl"),
            (r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'\/~`]', "Sonderzeichen fehlen", "Mindestens ein Sonderzeichen")
        ]

        for pattern, missing_msg, requirement in checks:
            if re.search(pattern, password):
                score += 1
            else:
                feedback.append(requirement)

        # Common password check
        if password.lower() in self.common_passwords:
            feedback.append("Passwort ist zu häufig verwendet")
            return False, "Passwort ist zu häufig verwendet", feedback

        # Sequential characters check
        if self._has_sequential_chars(password):
            feedback.append("Vermeiden Sie aufeinanderfolgende Zeichen (123, abc)")

        # Repeated characters check
        if self._has_repeated_chars(password):
            feedback.append("Zu viele wiederholte Zeichen")

        # Minimum requirements check
        if score < 4:
            return False, "Passwort erfüllt nicht alle Anforderungen", feedback

        return True, "Passwort ist sicher", []

    @staticmethod
    def _has_sequential_chars(s: str) -> bool:
        """Prüft auf einfache Tastatursequenzen."""
        sequences = ['123', '234', '345', '456', '567', '678', '789',
                     'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'qwe', 'wer']
        # Korrektur: s anstelle von password verwenden
        return any(seq in s.lower() for seq in sequences)

    @staticmethod
    def _has_repeated_chars(s: str) -> bool:
        """Prüft auf mehr als zwei identische, aufeinanderfolgende Zeichen."""
        # Korrektur: s anstelle von password verwenden
        if len(s) < 3:
            return False
        for i in range(len(s) - 2):
            if s[i] == s[i + 1] == s[i + 2]:
                return True
        return False


def get_password_strength(self, password: str) -> Dict[str, any]:
        """Erweiterte Password Strength Berechnung"""
        score = 0
        feedback = []
        max_score = 8

        # Length scoring (0-2 points)
        if len(password) >= 16:
            score += 2
        elif len(password) >= 12:
            score += 1
        else:
            feedback.append("Zu kurz")

        # Character variety (0-4 points)
        char_checks = [
            (r'[A-Z]', "Großbuchstaben fehlen"),
            (r'[a-z]', "Kleinbuchstaben fehlen"),
            (r'\d', "Zahlen fehlen"),
            (r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'\/~`]', "Sonderzeichen fehlen")
        ]

        for pattern, msg in char_checks:
            if re.search(pattern, password):
                score += 1
            else:
                feedback.append(msg)

        # Bonus points (0-2 points)
        if len(password) >= 20:
            score += 1  # Extra length bonus

        if not self._has_repeated_chars(password) and not self._has_sequential_chars(password):
            score += 1  # Pattern avoidance bonus

        # Strength calculation
        percentage = min(100, (score / max_score) * 100)

        if score >= 7:
            strength = "Sehr stark"
            color = "green"
        elif score >= 5:
            strength = "Stark"
            color = "lightgreen"
        elif score >= 3:
            strength = "Mittel"
            color = "orange"
        else:
            strength = "Schwach"
            color = "red"

        return {
            'score': score,
            'max_score': max_score,
            'strength': strength,
            'color': color,
            'feedback': feedback,
            'percentage': percentage
        }

class SecurityLogger:
    """Erweiterte Sicherheits-Logging mit strukturierten Events"""

    def __init__(self, log_file: str = "security.log"):
        self.log_file = log_file

    def _log_event(self, level: str, event_type: str, details: Dict):
        """Strukturiertes Logging mit JSON Format"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'event_type': event_type,
            'details': details
        }

        # Console output
        print(f"{self._get_emoji(event_type)} {level}: {event_type} - {details}")

        # File logging
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"⚠️  Logging error: {e}")

    @staticmethod
    def _get_emoji(event_type: str) -> str:
        """Liefert ein passendes Emoji für einen Event-Typ."""
        emojis = {
            'LOGIN_SUCCESS': '✅',
            'LOGIN_FAILURE': '❌',  # Geändert von FAILED zu FAILURE
            'RATE_LIMIT_TRIGGERED': '🚫',  # Angepasst an tatsächliche Events
            'SESSION_CREATED': '🆕',
            'SESSION_EXPIRED': '⏰',
            'SESSION_INVALID': '🚨',
            'USER_REGISTERED': '👤',
            'PASSWORD_CHANGED': '🔑',
            'PASSWORD_CHANGE_FAILED': '🔐',  # Hinzugefügt
            'IP_CHANGE': '🌐',
            # Allgemeine Events
            'INFO': 'ℹ️',
            'WARN': '⚠️',
            'ERROR': '🔥',
        }
        # Korrektur: event_type anstelle von der alten, falschen Variable
        # '📝' als Standard-Emoji für unbekannte Typen
        return emojis.get(event_type, '📝')

    def log_access_denied(self, username: str, requested_url: str):
        """Protokolliert einen verweigerten Zugriff, weil eine Anmeldung erforderlich war."""
        self._log_event(
            level='WARN',  # Korrekte Reihenfolge: Level zuerst
            event_type='ACCESS_DENIED',  # Dann der Event-Typ
            details={  # Und die Details als Dictionary
                'username': username or 'Nicht angemeldet',
                'requested_url': requested_url,
                'message': "Zugriff verweigert, da keine gültige Sitzung vorlag."
            }
        )

    def log_login_attempt(self, username: str, success: bool, ip_address: str = "unknown", details: str = ""):
        """Loggt Login Versuche mit Details"""
        event_type = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:10]

        log_details = {
            'username': username,
            'ip_hash': ip_hash,
            'success': success,
            'additional_details': details
        }

        self._log_event('INFO' if success else 'WARNING', event_type, log_details)

    def log_session_event(self, event_type: str, user_id: int, session_id: str, details: str = ""):
        """Loggt Session-Ereignisse mit Details."""
        log_details = {
            'user_id': user_id,
            'session_id': session_id[:8] + "...",
            'details': details
        }
        self._log_event('INFO', event_type, log_details)

    def log_security_event(self, event_type: str, details: Dict):
        """Loggt allgemeine Sicherheitsereignisse"""
        self._log_event('WARNING', event_type, details)


class EnhancedAuthSystem:
    def __init__(self, session_manager, user_data_file: str):
        self.sessions = session_manager  # Die Abhängigkeit speichern
        self.user_data_file = user_data_file  # GELÖST: Der Pfad wird jetzt hier übergeben

        # self.secret_key = os.environ.get('SECRET_KEY') # HINWEIS: Diese Zeile wird von der nächsten überschrieben
        self.config = SecurityConfig.get_security_config()
        self.secret_key = SecurityConfig.get_secret_key()

        self.password_validator = PasswordValidator(self.config)
        self.security_logger = SecurityLogger()
        self.login_attempts: Dict[str, List[datetime]] = {}

        # Load user data
        self.users = self._load_users()

        print(f"✅ Enhanced Auth System V2 initialized")
        print(f"   Secret Key: {'*' * 20} (length: {len(self.secret_key)})")
        print(f"   Session Timeout: {SecurityConfig.SESSION_TIMEOUT_HOURS}h")
        print(f"   Common Passwords: {len(self.config.get('common_passwords', []))} entries")

    def _load_users(self) -> Dict:
        """Lädt User Daten mit verbessertem Default Admin"""
        try:
            if os.path.exists(self.user_data_file):
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    return self._migrate_user_data(users)
        except Exception as e:
            self.security_logger.log_security_event('USER_DATA_LOAD_ERROR', {'error': str(e)})

        # Create default admin from config
        admin_config = self.config.get('default_admin', {})
        default_password = admin_config.get('password', 'TempAdmin2025!@#$%')

        default_users = {
            admin_config.get('username', 'admin'): {
                "password_hash": self._hash_password(default_password),
                "created_at": datetime.now().isoformat(),
                "is_admin": True,
                "login_count": 0,
                "last_login": None,
                "force_password_change": admin_config.get('force_change', True),
                "account_version": "2.0"
            }
        }

        self._save_users(default_users)

        if admin_config.get('force_change', True):
            print("🚨 WICHTIG: Default Admin Account erstellt!")
            print(f"   Username: {admin_config.get('username', 'admin')}")
            print(f"   Passwort: {default_password}")
            print("   ÄNDERN SIE DAS PASSWORT BEIM ERSTEN LOGIN!")

        return default_users

    def _migrate_user_data(self, users: Dict) -> Dict:
        """Migriert alte User Daten zu neuer Version"""
        migrated = False

        for username, user_data in users.items():
            if user_data.get('account_version') != '2.0':
                # Add new fields
                user_data.setdefault('force_password_change', False)
                user_data.setdefault('login_count', 0)
                user_data.setdefault('account_version', '2.0')
                migrated = True

        if migrated:
            self._save_users(users)
            print("✅ User data migrated to version 2.0")

        return users

    def _save_users(self, users: Dict = None):
        """Speichert User Daten mit Backup"""
        if users is None:
            users = self.users

        try:
            # Create backup
            if os.path.exists(self.user_data_file):
                backup_file = f"{self.user_data_file}.backup"
                import shutil
                shutil.copy2(self.user_data_file, backup_file)

            # Save new data
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.security_logger.log_security_event('USER_DATA_SAVE_ERROR', {'error': str(e)})
            raise Exception(f"Failed to save user data: {e}")

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash Password mit bcrypt - zentralisierte Methode"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verifiziert Password - zentralisierte Methode"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            self.security_logger.log_security_event('PASSWORD_VERIFICATION_ERROR', {'error': str(e)})
            return False

    def _verify_user_password(self, username: str, password: str) -> Tuple[bool, str]:
        """Zentralisierte User Password Verification - eliminiert Duplizierung"""
        if username not in self.users:
            # Log specific, return generic
            self.security_logger.log_security_event('LOGIN_USER_NOT_FOUND', {'username': username})
            return False, "Ungültige Anmeldedaten"

        user = self.users[username]
        if not self._verify_password(password, user["password_hash"]):
            # Log specific, return generic
            self.security_logger.log_security_event('LOGIN_WRONG_PASSWORD', {'username': username})
            return False, "Ungültige Anmeldedaten"

        return True, "Password verified"

    def _is_rate_limited(self, username: str) -> bool:
        """Rate Limiting Check - erweitert"""
        now = datetime.now()
        lockout_minutes = self.config.get('security_settings', {}).get('lockout_duration_minutes', 15)
        cutoff = now - timedelta(minutes=lockout_minutes)

        if username not in self.login_attempts:
            self.login_attempts[username] = []

        # Remove old attempts
        self.login_attempts[username] = [
            attempt for attempt in self.login_attempts[username]
            if attempt > cutoff
        ]

        # Check limit
        is_limited = len(self.login_attempts[username]) >= SecurityConfig.MAX_LOGIN_ATTEMPTS

        if is_limited:
            self.security_logger.log_security_event('RATE_LIMIT_TRIGGERED', {
                'username': username,
                'attempts': len(self.login_attempts[username]),
                'lockout_minutes': lockout_minutes
            })

        return is_limited

    def _record_login_attempt(self, username: str):
        """Zeichnet Login Versuch auf"""
        if username not in self.login_attempts:
            self.login_attempts[username] = []

        self.login_attempts[username].append(datetime.now())

    def _update_user_login_success(self, username: str):
        """Aktualisiert User Daten bei erfolgreichem Login - eliminiert Duplizierung"""
        user = self.users[username]
        user["login_count"] = user.get("login_count", 0) + 1
        user["last_login"] = datetime.now().isoformat()

        # Clear failed attempts
        if username in self.login_attempts:
            del self.login_attempts[username]

        self._save_users()

    def register_user(self, username: str, password: str, ip_address: str = "unknown") -> Tuple[bool, str]:
        """Registriert neuen User mit umfassender Validation"""
        try:
            # Username validation
            if not self._validate_username(username):
                return False, "Username muss 3-20 Zeichen haben und darf nur Buchstaben, Zahlen, _ und - enthalten"

            if username in self.users:
                self.security_logger.log_security_event('REGISTRATION_USERNAME_EXISTS', {'username': username})
                return False, "Username bereits vergeben"

            # Password validation
            is_valid, message, feedback = self.password_validator.validate_password(password)
            if not is_valid:
                return False, message

            # Rate limiting check
            if self._is_rate_limited(username):
                raise RateLimitError(username)

            # Create user
            password_hash = self._hash_password(password)

            self.users[username] = {
                "password_hash": password_hash,
                "created_at": datetime.now().isoformat(),
                "is_admin": False,
                "login_count": 0,
                "last_login": None,
                "registration_ip": hashlib.sha256(ip_address.encode()).hexdigest(),
                "force_password_change": False,
                "account_version": "2.0"
            }

            self._save_users()

            self.security_logger.log_security_event('USER_REGISTERED', {
                'username': username,
                'ip_hash': hashlib.sha256(ip_address.encode()).hexdigest()[:10]
            })

            return True, "Registrierung erfolgreich"

        except RateLimitError as e:
            return False, f"Zu viele Registrierungsversuche. Bitte warten Sie {e.retry_after_minutes} Minuten."
        except Exception as e:
            self.security_logger.log_security_event('REGISTRATION_ERROR', {'error': str(e)})
            return False, "Registrierung fehlgeschlagen"

    @staticmethod
    def _validate_username(username: str) -> bool:
        """Validiert Username Format"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

    def authenticate_user(self, username: str, password: str, ip_address: str = "unknown") -> Tuple[bool, str]:
        """Authentifiziert User mit Security Features - nutzt zentralisierte Methoden"""
        try:
            # Rate limiting
            if self._is_rate_limited(username):
                raise RateLimitError(username)

            # Record attempt
            self._record_login_attempt(username)

            # Verify password (using centralized method)
            password_valid, verification_message = self._verify_user_password(username, password)

            if not password_valid:
                self.security_logger.log_login_attempt(username, False, ip_address, verification_message)
                return False, "Ungültige Anmeldedaten"

            # Success - update user (using centralized method)
            self._update_user_login_success(username)

            self.security_logger.log_login_attempt(username, True, ip_address, "Login successful")
            return True, "Anmeldung erfolgreich"

        except RateLimitError as e:
            self.security_logger.log_login_attempt(username, False, ip_address, f"Rate limited: {e.retry_after_minutes}min")
            return False, f"Zu viele Login-Versuche. Bitte warten Sie {e.retry_after_minutes} Minuten."
        except Exception as e:
            self.security_logger.log_security_event('AUTHENTICATION_ERROR', {'error': str(e)})
            return False, "Anmeldung fehlgeschlagen"

    def create_secure_session(self, username: str, ip_address: str = "unknown") -> Tuple[str, Dict]:
        """Erstellt sichere Session mit erweiterten Features"""
        session_id = secrets.token_urlsafe(32)

        session_data = {
            'username': username,
            'user_id': self._get_user_id(username),
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=SecurityConfig.SESSION_TIMEOUT_HOURS)).isoformat(),
            'security_token': secrets.token_urlsafe(16),
            'ip_hash': hashlib.sha256(ip_address.encode()).hexdigest(),
            'is_admin': self.users[username].get('is_admin', False),
            'force_password_change': self.users[username].get('force_password_change', False),
            'session_version': '2.0'
        }

        self.security_logger.log_session_event('SESSION_CREATED', session_data['user_id'], session_id)

        return session_id, session_data

    def validate_session(self, session_id: str, session_data: Dict, ip_address: str = "unknown") -> bool:
        """Validiert Session mit erweiterten Security Checks"""
        if not session_data:
            self.security_logger.log_session_event('SESSION_INVALID', 0, session_id, "No session data")
            return False

        # Check expiration
        try:
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                self.security_logger.log_session_event('SESSION_EXPIRED',
                    session_data.get('user_id', 0), session_id, "Session expired")
                return False
        except Exception as e:
            self.security_logger.log_session_event('SESSION_INVALID',
                session_data.get('user_id', 0), session_id, f"Invalid expiration: {e}")
            return False

        # IP consistency check (log but don't fail for mobile users)
        current_ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
        if session_data.get('ip_hash') != current_ip_hash:
            self.security_logger.log_security_event('IP_CHANGE', {
                'session_hash': session_id[:8] + "...",
                'user_id': session_data.get('user_id', 0),
                'original_ip_hash': session_data.get('ip_hash', 'unknown')[:10],
                'current_ip_hash': current_ip_hash[:10]
            })

        # Check if user still exists
        username = session_data.get('username')
        if username not in self.users:
            self.security_logger.log_session_event('SESSION_INVALID',
                session_data.get('user_id', 0), session_id, "User no longer exists")
            return False

        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Ändert User Password - nutzt zentralisierte Methoden"""
        try:
            # Verify old password (using centralized method)
            password_valid, verification_message = self._verify_user_password(username, old_password)

            if not password_valid:
                self.security_logger.log_security_event('PASSWORD_CHANGE_FAILED', {
                    'username': username,
                    'reason': 'Invalid old password'
                })
                return False, "Altes Passwort ungültig"

            # Validate new password - HIER war wahrscheinlich der Fehler
            is_valid, message, feedback = self.password_validator.validate_password(new_password)
            if not is_valid:
                return False, message

            # Check if new password is different
            if self._verify_password(new_password, self.users[username]["password_hash"]):
                return False, "Neues Passwort muss sich vom aktuellen unterscheiden"

            # Update password
            self.users[username]["password_hash"] = self._hash_password(new_password)
            self.users[username]["force_password_change"] = False
            self.users[username]["password_changed_at"] = datetime.now().isoformat()
            self._save_users()

            self.security_logger.log_security_event('PASSWORD_CHANGED', {'username': username})

            return True, "Passwort erfolgreich geändert"

        except Exception as e:
            self.security_logger.log_security_event('PASSWORD_CHANGE_ERROR', {
                'username': username,
                'error': str(e)
            })
            return False, "Passwort konnte nicht geändert werden"

    @staticmethod
    def _get_user_id(username: str) -> int:
        """Generiert eine User ID (simuliert)"""
        # Diese Methode benötigt keinen Zugriff auf 'self', daher machen wir sie statisch.
        return abs(hash(username)) % (10 ** 8)

    def get_user_info(self, username: str) -> Dict:
        """Holt sichere User Informationen"""
        if username not in self.users:
            return {}

        user = self.users[username].copy()
        # Remove sensitive data
        sensitive_fields = ['password_hash', 'registration_ip', 'security_token']
        for field in sensitive_fields:
            user.pop(field, None)

        return user

    def cleanup_expired_sessions(self):
        """Cleanup Methode für alte Session Daten"""
        cleanup_hours = self.config.get('security_settings', {}).get('session_cleanup_hours', 168)
        cutoff = datetime.now() - timedelta(hours=cleanup_hours)

        cleaned_count = 0
        for username in list(self.login_attempts.keys()):
            self.login_attempts[username] = [
                attempt for attempt in self.login_attempts[username]
                if attempt > cutoff
            ]
            if not self.login_attempts[username]:
                del self.login_attempts[username]
                cleaned_count += 1

        if cleaned_count > 0:
            self.security_logger.log_security_event('SESSION_CLEANUP', {
                'cleaned_users': cleaned_count,
                'cutoff_hours': cleanup_hours
            })

# Instance für Import
auth_system = LocalProxy(lambda: getattr(current_app, 'auth_system', None))
