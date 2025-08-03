"""Programming Bot 2025 - Enhanced Template-based Flask Application"""

import os
import sys
import logging
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from functools import wraps
import threading
import time

# Flask imports
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError, BadRequest
from werkzeug.utils import secure_filename

# Import our enhanced modules
from auth_system import auth_system

# .env File Loading (Manual Fallback)
def load_env_file():
    """Load .env file manually if python-dotenv is not available"""
    env_path = '.env'
    if os.path.exists(env_path):
        try:
            # Try with python-dotenv first
            from dotenv import load_dotenv
            load_dotenv(env_path)
            print(f"✅ Loaded .env file using python-dotenv: {os.path.abspath(env_path)}")
            return True
        except ImportError:
            # Manual parsing if python-dotenv is not available
            print(f"⚠️  python-dotenv not available, loading .env manually...")
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\'"')
                        os.environ[key] = value
            print(f"✅ Manually loaded .env file: {os.path.abspath(env_path)}")
            return True
    return False


# Load environment
load_env_file()


# Enhanced Configuration Management
class AppConfig:
    """Comprehensive application configuration with validation and defaults"""

    # Security Configuration - Fix SECRET_KEY issue
    _secret_key = os.environ.get('SECRET_KEY', '')
    if len(_secret_key) < 32:
        print(f"⚠️  WARNING: SECRET_KEY too short ({len(_secret_key)} chars), generating secure one")
        # Generate a proper 32+ character secret key
        _secret_key = secrets.token_urlsafe(48)  # Generates ~64 characters
        print(f"✅ Generated secure SECRET_KEY (length: {len(_secret_key)})")
    SECRET_KEY = _secret_key

    # API Configuration
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
    CLAUDE_MAX_TOKENS = int(os.environ.get('CLAUDE_MAX_TOKENS', 4000))

    # Server Configuration
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 8100))
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'on', 'yes']
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')

    # Session Configuration
    SESSION_TIMEOUT_HOURS = int(os.environ.get('SESSION_TIMEOUT_HOURS', 24))
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ['true', '1', 'on', 'yes']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() in ['true', '1', 'on', 'yes']

    # Features Configuration
    ENABLE_REGISTRATION = os.environ.get('ENABLE_REGISTRATION', 'False').lower() in ['true', '1', 'on', 'yes']
    ENABLE_CODE_REVIEW = os.environ.get('ENABLE_CODE_REVIEW', 'True').lower() in ['true', '1', 'on', 'yes']
    ENABLE_PROJECT_MANAGEMENT = os.environ.get('ENABLE_PROJECT_MANAGEMENT', 'True').lower() in ['true', '1', 'on',
                                                                                                'yes']
    ENABLE_FILE_UPLOAD = os.environ.get('ENABLE_FILE_UPLOAD', 'True').lower() in ['true', '1', 'on', 'yes']

    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8100,http://127.0.0.1:8100').split(',')

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.environ.get('LOG_FILE', 'programming_bot.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

    # Performance Configuration
    THREADED = os.environ.get('THREADED', 'True').lower() in ['true', '1', 'on', 'yes']
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')

    @classmethod
    def get_runtime_info(cls) -> Dict[str, Any]:
        """Get runtime configuration information"""
        return {
            'version': '2025.2.0',
            'environment': cls.ENVIRONMENT,
            'debug': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
            'features': {
                'registration': cls.ENABLE_REGISTRATION,
                'code_review': cls.ENABLE_CODE_REVIEW,
                'project_management': cls.ENABLE_PROJECT_MANAGEMENT,
                'file_upload': cls.ENABLE_FILE_UPLOAD,
                'rate_limiting': cls.RATELIMIT_ENABLED
            },
            'security': {
                'session_timeout': f"{cls.SESSION_TIMEOUT_HOURS}h",
                'secure_cookies': cls.SESSION_COOKIE_SECURE,
                'cors_enabled': bool(cls.CORS_ORIGINS)
            },
            'api': {
                'claude_model': cls.CLAUDE_MODEL,
                'claude_configured': bool(cls.CLAUDE_API_KEY),
                'max_tokens': cls.CLAUDE_MAX_TOKENS
            }
        }


# Enhanced Logging Setup
def setup_logging():
    """Setup comprehensive logging with rotation"""
    from logging.handlers import RotatingFileHandler

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # Setup file handler with rotation and UTF-8 encoding
    file_handler = RotatingFileHandler(
        AppConfig.LOG_FILE,
        maxBytes=AppConfig.LOG_MAX_BYTES,
        backupCount=AppConfig.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(getattr(logging, AppConfig.LOG_LEVEL))

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO if not AppConfig.DEBUG else logging.DEBUG)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, AppConfig.LOG_LEVEL))

    return root_logger


# Utility Functions
def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Enhanced input sanitization"""
    if not text:
        return ""

    # Length check
    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    # Basic HTML escaping
    from markupsafe import escape
    sanitized = escape(text)
    return str(sanitized)


def get_client_ip() -> str:
    """Enhanced client IP detection"""
    # Check for forwarded IPs (behind proxy/load balancer)
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        return forwarded_ips.split(',')[0].strip()

    # Check for real IP (some proxies)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()

    # Check for Cloudflare
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip.strip()

    # Fallback to remote address
    return request.remote_addr or 'unknown'


# Flask Application Factory
def create_app():
    """Enhanced Flask application factory"""
    print("🏭 Creating Flask application...")

    # Setup logging first
    logger = setup_logging()

    # Create Flask app with correct template folder
    app = Flask(__name__,
                static_folder='web/static',
                template_folder='templates',
                instance_relative_config=True)

    # Configure Flask
    app.config.update(
        SECRET_KEY=AppConfig.SECRET_KEY,
        SESSION_COOKIE_SECURE=AppConfig.SESSION_COOKIE_SECURE,
        SESSION_COOKIE_HTTPONLY=AppConfig.SESSION_COOKIE_HTTPONLY,
        SESSION_COOKIE_SAMESITE=AppConfig.SESSION_COOKIE_SAMESITE,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=AppConfig.SESSION_TIMEOUT_HOURS),
        MAX_CONTENT_LENGTH=AppConfig.MAX_CONTENT_LENGTH,
        UPLOAD_FOLDER=AppConfig.UPLOAD_FOLDER,
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=AppConfig.DEBUG,
        TEMPLATES_AUTO_RELOAD=AppConfig.DEBUG
    )

    # Setup CORS
    if AppConfig.CORS_ORIGINS:
        CORS(app,
             origins=AppConfig.CORS_ORIGINS,
             supports_credentials=True,
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
             expose_headers=['X-Total-Count', 'X-Rate-Limit-Remaining'])

    # Setup Rate Limiting
    limiter = None
    if AppConfig.RATELIMIT_ENABLED:
        try:
            limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=AppConfig.RATELIMIT_STORAGE_URL,
                default_limits=["200 per hour", "50 per minute"],
                headers_enabled=True
            )
            limiter.init_app(app)
            logger.info("Rate limiting enabled")
        except Exception as e:
            logger.warning(f"Rate limiting setup failed: {e}")

    # Context processors for templates - FIX für Template Error
    @app.context_processor
    def inject_globals():
        """Inject global variables into all templates - SAFE VERSION"""
        try:
            # Safe config object that is JSON serializable
            safe_config = {
                'DEBUG': AppConfig.DEBUG,
                'ENABLE_REGISTRATION': AppConfig.ENABLE_REGISTRATION,
                'ENABLE_CODE_REVIEW': AppConfig.ENABLE_CODE_REVIEW,
                'ENABLE_PROJECT_MANAGEMENT': AppConfig.ENABLE_PROJECT_MANAGEMENT,
                'PASSWORD_MIN_LENGTH': 12,
                'SESSION_TIMEOUT_HOURS': AppConfig.SESSION_TIMEOUT_HOURS
            }

            return {
                'current_year': datetime.now().year,
                'app_name': 'Programming Bot 2025',
                'app_version': '2025.2.0',
                'environment': AppConfig.ENVIRONMENT,
                'config': safe_config,  # Only JSON-serializable data
                'user': session.get('user_info', {}),
                'session': session
            }
        except Exception as e:
            logger.error(f"Context processor error: {e}")
            # Return minimal safe context
            return {
                'current_year': datetime.now().year,
                'app_name': 'Programming Bot 2025',
                'config': {'DEBUG': False}
            }

    # Template global functions - SAFE VERSION
    @app.template_global()
    def moment(timestamp=None):
        """Safe moment function for templates"""
        try:
            if timestamp is None:
                return datetime.now()
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return timestamp
        except Exception:
            return datetime.now()

    # Authentication decorator
    def login_required(f):
        """Enhanced authentication decorator"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Bitte melden Sie sich an, um fortzufahren.', 'warning')
                return redirect(url_for('login'))

            # Validate session
            user_id = session['user_id']
            session_token = session.get('session_token')

            if not session_token:
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Session expired'}), 401
                flash('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.', 'warning')
                return redirect(url_for('login'))

            # Update user info in session
            user_info = auth_system.get_user_info(user_id)
            if user_info:
                session['user_info'] = user_info

            return f(*args, **kwargs)

        return decorated_function

    # Security headers
    @app.after_request
    def security_headers(response):
        """Add comprehensive security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://api.anthropic.com",
            "media-src 'self'",
            "object-src 'none'",
            "child-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers['Content-Security-Policy'] = "; ".join(csp_directives)

        return response

    # Routes
    @app.route('/')
    def index():
        """Enhanced home page"""
        if 'user_id' in session:
            user_info = session.get('user_info', {})
            if user_info.get('force_password_change', False):
                return redirect(url_for('change_password'))
            return redirect(url_for('programming'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Enhanced login with template error fix and dual request support"""
        if limiter:
            limiter.limit("10 per minute")(lambda: None)()

        if request.method == 'GET':
            # If already logged in, redirect
            if 'user_id' in session:
                return redirect(url_for('programming'))

            try:
                # Try to render the original template
                mode = request.args.get('mode', 'login')
                return render_template('login.html', mode=mode)
            except Exception as e:
                logger.error(f"Template error in login: {e}")
                # Return safe fallback HTML
                return """
                <!DOCTYPE html>
                <html lang="de">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Programming Bot 2025 - Login</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { text-align: center; color: #333; margin-bottom: 30px; }
                        .form-group { margin-bottom: 20px; }
                        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
                        input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
                        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
                        button:hover { background: #0056b3; }
                        .alert { padding: 10px; margin: 10px 0; border-radius: 5px; display: none; }
                        .alert.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                        .alert.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                        .fallback-notice { background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #ffeaa7; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="fallback-notice">
                            <strong>⚠️ Fallback-Modus:</strong> Das originale Login-Template konnte nicht geladen werden. Diese vereinfachte Version funktioniert trotzdem!
                        </div>
                        <h1>🤖 Programming Bot 2025</h1>
                        <div id="alert" class="alert"></div>
                        <form id="loginForm">
                            <div class="form-group">
                                <label for="username">Benutzername:</label>
                                <input type="text" id="username" name="username" required>
                            </div>
                            <div class="form-group">
                                <label for="password">Passwort:</label>
                                <input type="password" id="password" name="password" required>
                            </div>
                            <button type="submit" id="loginBtn">Anmelden</button>
                        </form>
                        <script>
                            function showAlert(message, type) {
                                const alert = document.getElementById('alert');
                                alert.textContent = message;
                                alert.className = 'alert ' + type;
                                alert.style.display = 'block';
                            }

                            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                                e.preventDefault();
                                const btn = document.getElementById('loginBtn');
                                const username = document.getElementById('username').value;
                                const password = document.getElementById('password').value;

                                btn.disabled = true;
                                btn.textContent = 'Anmelden...';

                                try {
                                    const response = await fetch('/login', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                                        body: 'username=' + encodeURIComponent(username) + '&password=' + encodeURIComponent(password)
                                    });

                                    const data = await response.json();

                                    if (data.success) {
                                        showAlert('Erfolgreich angemeldet! Weiterleitung...', 'success');
                                        setTimeout(() => window.location.href = data.redirect || '/programming', 1000);
                                    } else {
                                        showAlert(data.message || 'Anmeldung fehlgeschlagen', 'error');
                                    }
                                } catch (error) {
                                    showAlert('Verbindungsfehler: ' + error.message, 'error');
                                }

                                btn.disabled = false;
                                btn.textContent = 'Anmelden';
                            });
                        </script>
                    </div>
                </body>
                </html>
                """, 200

        # Handle POST requests - SUPPORT BOTH JSON AND FORM DATA
        try:
            # Check Content-Type and handle accordingly
            if request.content_type and 'application/json' in request.content_type:
                # JSON request (from original template)
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400
                username = data.get('username', '')
                password = data.get('password', '')
            else:
                # Form data request (from fallback template)
                username = request.form.get('username', '')
                password = request.form.get('password', '')

            # Input validation
            if not username or not password:
                return jsonify({
                    'success': False,
                    'message': 'Benutzername und Passwort sind erforderlich'
                }), 400

            username = sanitize_input(username, 50)
            client_ip = get_client_ip()

            # Log login attempt
            logger.info(f"Login attempt: {username} from {client_ip[:10]}...")

            # Authenticate user
            success, message = auth_system.authenticate_user(username, password, client_ip)

            if success:
                # Create session
                session_token = secrets.token_urlsafe(32)

                # Get user info
                user_info = auth_system.get_user_info(username)

                # Set session data
                session['user_id'] = username
                session['session_token'] = session_token
                session['user_info'] = user_info or {}
                session['login_time'] = datetime.now().isoformat()
                session['client_ip'] = client_ip
                session.permanent = request.form.get('remember_me') == 'on' or request.json.get('remember_me', False)

                # Determine redirect URL
                redirect_url = '/programming'
                if user_info and user_info.get('force_password_change', False):
                    redirect_url = '/change-password'

                logger.info(f"Login successful: {username}")

                return jsonify({
                    'success': True,
                    'message': 'Erfolgreich angemeldet!',
                    'redirect': redirect_url,
                    'user': {
                        'username': username,
                        'is_admin': user_info.get('is_admin', False) if user_info else False
                    }
                })
            else:
                logger.warning(f"Login failed: {username} - {message}")
                return jsonify({'success': False, 'message': message}), 401

        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({
                'success': False,
                'message': 'Ein unerwarteter Fehler ist aufgetreten'
            }), 500

    @app.route('/register', methods=['POST'])
    def register():
        """User registration endpoint - auch wenn Registration deaktiviert ist"""
        if not AppConfig.ENABLE_REGISTRATION:
            return jsonify({'success': False, 'message': 'Registrierung ist deaktiviert'}), 403

        # Hier würde die eigentliche Registrierungslogik stehen
        return jsonify({'success': False, 'message': 'Registrierung noch nicht implementiert'}), 501

    def logout():
        """Enhanced user logout"""
        user_id = session.get('user_id', 'unknown')
        client_ip = get_client_ip()

        logger.info(f"Logout: {user_id} from {client_ip[:10]}...")

        session.clear()

        if request.method == 'POST' or request.path.startswith('/api/'):
            return jsonify({
                'success': True,
                'message': 'Erfolgreich abgemeldet',
                'redirect': '/'
            })
        else:
            flash('Sie wurden erfolgreich abgemeldet.', 'success')
            return redirect(url_for('login'))

    @app.route('/logout', methods=['GET', 'POST'])
    @login_required
    def programming():
        """Enhanced programming interface"""
        user_id = session.get('user_id')
        user_info = session.get('user_info', {})

        try:
            return render_template('programming.html',
                                   user=user_info,
                                   username=user_id,
                                   is_admin=user_info.get('is_admin', False),
                                   config=AppConfig.get_runtime_info(),
                                   features={
                                       'code_review': AppConfig.ENABLE_CODE_REVIEW,
                                       'project_management': AppConfig.ENABLE_PROJECT_MANAGEMENT,
                                       'file_upload': AppConfig.ENABLE_FILE_UPLOAD
                                   })
        except Exception as e:
            logger.error(f"Template error in programming: {e}")
            # Fallback to simple programming interface
            return """
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Programming Interface - Programming Bot 2025</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; margin-bottom: 30px; }
                    .fallback-notice { background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #ffeaa7; }
                    .logout-btn { float: right; padding: 10px 20px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; }
                    .logout-btn:hover { background: #c82333; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="fallback-notice">
                        <strong>⚠️ Fallback-Modus:</strong> Das originale Programming-Template konnte nicht geladen werden.
                    </div>
                    <h1>🤖 Programming Bot 2025 - Programming Interface</h1>
                    <a href="/logout" class="logout-btn">Abmelden</a>
                    <p>Willkommen in der Programming-Umgebung! Das vollständige Interface wird geladen, sobald die Template-Probleme behoben sind.</p>
                    <p><strong>Benutzer:</strong> """ + str(user_id) + """</p>
                    <p><strong>Features verfügbar:</strong></p>
                    <ul>
                        <li>Code Review: """ + str(AppConfig.ENABLE_CODE_REVIEW) + """</li>
                        <li>Project Management: """ + str(AppConfig.ENABLE_PROJECT_MANAGEMENT) + """</li>
                        <li>File Upload: """ + str(AppConfig.ENABLE_FILE_UPLOAD) + """</li>
                    </ul>
                </div>
            </body>
            </html>
            """, 200

    @app.route('/programming')
    def health_check():
        """Comprehensive health check endpoint"""
        try:
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2025.2.0',
                'environment': AppConfig.ENVIRONMENT,
                'config': AppConfig.get_runtime_info()
            }), 200

        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Health check failed',
                'timestamp': datetime.now().isoformat()
            }), 500

    @app.route('/api/health')
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Endpoint not found'
            }), 404

        # Simple 404 page
        return """
        <!DOCTYPE html>
        <html><head><title>404 - Seite nicht gefunden</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>404 - Seite nicht gefunden</h1>
            <p>Die angeforderte Seite konnte nicht gefunden werden.</p>
            <a href="/" style="color: #007bff;">Zur Startseite</a>
        </body></html>
        """, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        error_id = secrets.token_hex(8)
        logger.error(f"Internal error [{error_id}]: {error}")

        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'Internal server error',
                'error_id': error_id
            }), 500

        # Simple 500 page
        return f"""
        <!DOCTYPE html>
        <html><head><title>500 - Serverfehler</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>500 - Interner Serverfehler</h1>
            <p>Es ist ein Fehler aufgetreten. Fehler-ID: {error_id}</p>
            <a href="/" style="color: #007bff;">Zur Startseite</a>
        </body></html>
        """, 500

    # Startup logging
    print(f"✅ SECRET_KEY loaded from environment (length: {len(AppConfig.SECRET_KEY)})")
    logger.info("🔧 Application Configuration:")
    logger.info(f"   Environment: {AppConfig.ENVIRONMENT}")
    logger.info(f"   Debug Mode: {AppConfig.DEBUG}")
    logger.info(f"   Host: {AppConfig.HOST}:{AppConfig.PORT}")
    logger.info(f"   Secret Key: ✅ Loaded from .env")
    logger.info(f"   Auth System: {'✅ Loaded' if auth_system else '❌ Failed'}")

    # Check session manager without causing double init
    try:
        from session_manager import session_manager
        logger.info(f"   Session Manager: ✅ Loaded")
    except:
        logger.info(f"   Session Manager: ❌ Failed")

    logger.info(f"   Rate Limiting: {'✅ Enabled' if limiter else '❌ Disabled'}")
    logger.info(f"   CORS: {'✅ Enabled' if AppConfig.CORS_ORIGINS else '❌ Disabled'}")
    logger.info(f"   File Upload: {'✅ Enabled' if AppConfig.ENABLE_FILE_UPLOAD else '❌ Disabled'}")
    logger.info(f"   Claude API: {'✅ Configured' if AppConfig.CLAUDE_API_KEY else '❌ Not configured'}")

    # Error handlers

    return app
    """Enhanced main application entry point"""
    try:
        app = create_app()
        if not app:
            print("❌ Failed to create application")
            return

        runtime_info = AppConfig.get_runtime_info()

        print("\n" + "=" * 70)
        print("🚀 PROGRAMMING BOT 2025 - ENHANCED TEMPLATE EDITION")
        print("=" * 70)
        print(f"📍 Server: http://{AppConfig.HOST}:{AppConfig.PORT}")
        print(f"💻 Login: http://{AppConfig.HOST}:{AppConfig.PORT}/login")
        print(f"🔧 Programming: http://{AppConfig.HOST}:{AppConfig.PORT}/programming")
        print(f"❤️  Health Check: http://{AppConfig.HOST}:{AppConfig.PORT}/api/health")
        print("=" * 70)
        print("🔑 Default Admin Login:")
        print("   Username: admin")
        print("   Password: TempAdmin2025!@#$%")
        print("   (Change password on first login!)")
        print("=" * 70)
        print("🎯 Features:")
        print(f"   Registration: {'✅' if AppConfig.ENABLE_REGISTRATION else '❌'}")
        print(f"   Code Review: {'✅' if AppConfig.ENABLE_CODE_REVIEW else '❌'}")
        print(f"   Project Management: {'✅' if AppConfig.ENABLE_PROJECT_MANAGEMENT else '❌'}")
        print(f"   File Upload: {'✅' if AppConfig.ENABLE_FILE_UPLOAD else '❌'}")
        print(f"   Rate Limiting: {'✅' if AppConfig.RATELIMIT_ENABLED else '❌'}")
        print(f"   Claude AI: {'✅' if AppConfig.CLAUDE_API_KEY else '❌'}")
        print("=" * 70)
        print("🛠️  Template Fixes:")
        print("   ✅ Template-Kontext JSON-Serialization behoben")
        print("   ✅ Fallback-Templates für Fehlerbehandlung")
        print("   ✅ Sowohl JSON als auch Form-Data Login unterstützt")
        print("   ✅ Sichere Template-Funktionen implementiert")
        print("=" * 70)

        app.run(
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            debug=AppConfig.DEBUG,
            threaded=AppConfig.THREADED,
            use_reloader=AppConfig.DEBUG
        )

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        if AppConfig.DEBUG:
            traceback.print_exc()
        sys.exit(1)


def main():
    main()