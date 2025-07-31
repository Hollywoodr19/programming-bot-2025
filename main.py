#!/usr/bin/env python3
"""
Programming Bot 2025 - Multi-User AI Assistant
Flask-Only Version ohne FastAPI Konflikte
"""

import os
import sys
import json
import logging
from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash
from datetime import datetime


def get_user_bot_engine(user_id: str):
    """Get or create bot engine for user - Fixed Version"""
    global bot_engine

    # For now, return the global bot_engine
    # In the future, this could return user-specific engines
    if bot_engine is None:
        logger.error("❌ Bot engine not available")

        # Return fallback engine
        class FallbackEngine:
            def get_user_projects(self, user_id):
                return [{
                    'id': 1,
                    'name': 'Demo Project',
                    'description': 'Fallback project',
                    'language': 'python',
                    'status': 'active',
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                }]

            def create_project(self, user_id, name, description="", language="python"):
                return {
                    'success': True,
                    'project': {
                        'id': 2,
                        'name': name,
                        'description': description,
                        'language': language,
                        'status': 'active',
                        'created_at': '2025-01-01T00:00:00',
                        'updated_at': '2025-01-01T00:00:00'
                    }
                }

        return FallbackEngine()

    return bot_engine


# Configure logging with Windows compatibility
if sys.platform == "win32":
    import locale

    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass


    # Windows-safe logging
    class WindowsSafeFormatter(logging.Formatter):
        def format(self, record):
            message = super().format(record)
            replacements = {
                '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARNING]', '🚀': '[START]',
                '📍': '[SERVER]', '💻': '[PROG]', '💬': '[CHAT]', '🔧': '[DEBUG]',
                '🤖': '[BOT]', '📊': '[DASH]', '📁': '[PROJ]', '🔍': '[REVIEW]'
            }
            for emoji, text in replacements.items():
                message = message.replace(emoji, text)
            return message


    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(WindowsSafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('programming_bot.log', encoding='utf-8'),
            handler
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('programming_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='web/static', static_url_path='/static')
app.secret_key = 'programming-bot-2025-secret-key-change-in-production'

# Global variables for modules
auth_system = None
bot_engine = None
config = None
session_manager = None


def load_session_manager():
    """Load session manager if available"""
    global session_manager
    try:
        from session_manager import get_session_manager
        session_manager = get_session_manager()
        logger.info("✅ Session Manager loaded successfully")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ Session Manager not found: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Session Manager failed to load: {e}")
        return False


def load_modules():
    """Load all required modules with Smart Config System"""
    global auth_system, bot_engine, config

    # Load session manager
    load_session_manager()

    # Load Smart Configuration System
    try:
        from config import get_config, get_current_claude_model, get_claude_config
        config = get_config()
        logger.info("✅ Smart Config System loaded successfully")

        # Print startup info with model status
        if hasattr(config, 'print_startup_info'):
            config.print_startup_info()

        # Show current Claude model from centralized system
        current_model = get_current_claude_model()
        logger.info(f"🤖 Using Claude Model: {current_model}")

    except ImportError as e:
        logger.warning(f"❌ Smart Config not found: {e}")

        # Create minimal config fallback
        class Config:
            DATABASE_PATH = "bot_data.db"
            CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
            CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-opus-4-20250514')
            SECRET_KEY = 'fallback-secret-key'
            HOST = '0.0.0.0'
            PORT = 8100
            DEBUG = False

            def get_claude_config(self):
                return {
                    'api_key': self.CLAUDE_API_KEY,
                    'model': self.CLAUDE_MODEL,
                    'max_tokens': 1000
                }

        config = Config()

    # Load authentication system
    try:
        from auth_system import AuthenticationSystem
        auth_system = AuthenticationSystem()
        logger.info("✅ Auth system loaded successfully")
    except ImportError as e:
        logger.warning(f"❌ Auth system not found, using fallback: {e}")
        from werkzeug.security import check_password_hash, generate_password_hash

        class SimpleAuthSystem:
            def __init__(self):
                self.users = {
                    'admin': {
                        'password_hash': generate_password_hash('admin123'),
                        'display_name': 'Administrator',
                        'role': 'admin'
                    }
                }

            def authenticate_user(self, username, password):
                user = self.users.get(username)
                if user and check_password_hash(user['password_hash'], password):
                    return {
                        'username': username,
                        'display_name': user['display_name'],
                        'role': user['role']
                    }
                return None

            def register_user(self, username, password, email=None, display_name=None):
                """Fallback register user method"""
                if username in self.users:
                    return {'success': False, 'error': 'Username bereits vergeben'}

                self.users[username] = {
                    'password_hash': generate_password_hash(password),
                    'display_name': display_name or username,
                    'role': 'user',
                    'email': email
                }

                return {
                    'success': True,
                    'user': {
                        'username': username,
                        'display_name': display_name or username,
                        'role': 'user'
                    }
                }

            def check_username_available(self, username):
                return username not in self.users

        auth_system = SimpleAuthSystem()

    # Load bot engine with Smart Config
    try:
        from core.bot_engine import ClaudeAPIEngine
        # Get Claude config from Smart Config System
        claude_config = config.get_claude_config() if hasattr(config, 'get_claude_config') else {
            'api_key': getattr(config, 'CLAUDE_API_KEY', None),
            'model': getattr(config, 'CLAUDE_MODEL', 'claude-opus-4-20250514'),
            'max_tokens': 1000
        }

        bot_engine = ClaudeAPIEngine(
            api_key=claude_config['api_key'],
            model=claude_config.get('model'),
            max_tokens=claude_config.get('max_tokens', 1000)
        )
        logger.info("✅ Claude API Bot Engine loaded with Smart Config")

    except ImportError as e:
        logger.warning(f"❌ Bot engine not found, using enhanced fallback: {e}")

        # Enhanced fallback bot engine
        class EnhancedFallbackEngine:
            def __init__(self):
                self.message_count = 0
                self.user_context = {}
                self.projects = {}
                self.chat_history = {}

            def process_message(self, message, user_context=None):
                self.message_count += 1
                context = user_context or self.user_context
                user_id = context.get('user_id', 'anonymous')
                mode = context.get('mode', 'programming')
                display_name = context.get('display_name', 'Freund')

                # Save message to history
                if user_id not in self.chat_history:
                    self.chat_history[user_id] = []

                message_lower = message.lower()

                # Enhanced responses based on mode
                if mode == 'casual' or mode == 'chat_only':
                    if any(word in message_lower for word in ["hallo", "hi", "hey"]):
                        response = f"Hallo {display_name}! Schön dich zu sehen! Wie geht es dir denn heute?"
                    elif any(word in message_lower for word in ["wie geht", "geht es"]):
                        response = "Mir geht es super, danke der Nachfrage! Wie geht es dir denn?"
                    elif "witz" in message_lower:
                        jokes = [
                            "Warum nehmen Geister keine Drogen? Weil sie schon high-spirited sind!",
                            "Was ist grün und klopft an der Tür? Ein Klopfsalat!",
                            "Warum können Geister so schlecht lügen? Weil man durch sie hindurchsehen kann!"
                        ]
                        import random
                        response = random.choice(jokes)
                    elif "claude" in message_lower and "verbunden" in message_lower:
                        current_model = getattr(config, 'CLAUDE_MODEL', 'Fallback Mode')
                        response = f"Ich verwende das Model: {current_model}. Leider läuft gerade der Fallback-Modus, da die Claude API nicht verfügbar ist."
                    else:
                        response = f"Das ist interessant, {display_name}! Erzähl mir mehr davon!"

                elif mode == 'help':
                    response = f"Gerne helfe ich dir dabei, {display_name}! Zu deiner Frage '{message}': Lass mich das für dich klären..."

                elif mode == 'learn':
                    response = f"Sehr gerne erkläre ich dir das, {display_name}! Das Thema '{message}' ist wirklich faszinierend. Lass uns das zusammen entdecken!"

                else:  # programming mode
                    if any(word in message_lower for word in ["def ", "function", "class ", "import"]):
                        response = "Das sieht nach Code aus! Gerne schaue ich mir das für dich an. Soll ich es analysieren?"
                    elif "projekt" in message_lower:
                        response = "Großartig! Lass uns ein neues Projekt starten. Was für eine Anwendung möchtest du erstellen?"
                    elif any(word in message_lower for word in ["hallo", "hi", "hey"]):
                        response = f"Hallo {display_name}! Wie kann ich dir beim Programmieren helfen?"
                    elif "claude" in message_lower and ("modell" in message_lower or "model" in message_lower):
                        current_model = getattr(config, 'CLAUDE_MODEL', 'Unbekannt')
                        response = f"Ich bin konfiguriert für das Claude Model: {current_model}. Derzeit läuft der Fallback-Modus."
                    else:
                        response = f"Interessant! Ich verstehe: '{message}'. Wie kann ich dir dabei helfen?"

                # Save to history
                self.chat_history[user_id].append({
                    'message': message,
                    'response': response,
                    'timestamp': datetime.now().isoformat(),
                    'mode': mode
                })

                return response

            def create_project(self, name, description, language, user_id):
                project_id = f"project_{hash(f'{user_id}_{name}')}"

                if user_id not in self.projects:
                    self.projects[user_id] = []

                project = {
                    'id': project_id,
                    'name': name,
                    'description': description,
                    'language': language,
                    'user_id': user_id,
                    'created_at': datetime.now().isoformat()
                }

                self.projects[user_id].append(project)
                return project_id

            def get_user_projects(self, user_id):
                return self.projects.get(user_id, [])

            def analyze_code(self, code, language="python"):
                lines = code.split('\n')
                return {
                    'success': True,
                    'analysis': f"Code-Analyse: {len(lines)} Zeilen {language} Code. Struktur sieht gut aus! (Fallback-Analyse)",
                    'quality_score': 75,
                    'suggestions': [
                        'Füge mehr Kommentare für bessere Dokumentation hinzu',
                        'Erwäge Error-Handling zu implementieren',
                        'Überprüfe Variablen-Namenskonventionen'
                    ]
                }

            def get_chat_history(self, user_id, limit=50):
                return self.chat_history.get(user_id, [])[-limit:]

            def get_metrics(self, user_id=None):
                if user_id:
                    history = self.chat_history.get(user_id, [])
                    projects = self.projects.get(user_id, [])
                    current_model = getattr(config, 'CLAUDE_MODEL', 'Fallback Mode')
                    return {
                        'user_messages': len(history),
                        'user_projects': len(projects),
                        'api_status': f'Fallback Mode (Configured: {current_model})'
                    }
                else:
                    total_messages = sum(len(h) for h in self.chat_history.values())
                    total_projects = sum(len(p) for p in self.projects.values())
                    return {
                        'total_messages': total_messages,
                        'total_projects': total_projects,
                        'active_users': len(self.chat_history),
                        'api_status': 'Fallback Mode',
                        'uptime': 'Running'
                    }

        bot_engine = EnhancedFallbackEngine()


# Create directories
os.makedirs('templates', exist_ok=True)
os.makedirs('web/static/js', exist_ok=True)
os.makedirs('web/static/css', exist_ok=True)
os.makedirs('data', exist_ok=True)


# Routes
@app.route('/')
def index():
    """Main landing page - login"""
    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return """
        <!DOCTYPE html>
        <html><head><title>Programming Bot 2025 - Login</title>
        <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .login-form { max-width: 300px; margin: 30px auto; }
        input { width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 10px; }
        button { width: 100%; padding: 15px; background: #00d4aa; color: white; border: none; border-radius: 10px; cursor: pointer; }
        </style></head>
        <body>
        <h1>🤖 Programming Bot 2025</h1>
        <p>Template not found. Using fallback login.</p>
        <form method="POST" action="/login" class="login-form">
            <input type="text" name="username" placeholder="Username: admin" required>
            <input type="password" name="password" placeholder="Password: admin123" required>
            <button type="submit">🚀 Login</button>
        </form>
        </body></html>
        """


# Replace the login route in your main.py with this version:

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login route with universal session recovery"""
    if request.method == 'GET':
        return redirect(url_for('index'))

    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return redirect(url_for('index'))

        user = auth_system.authenticate_user(username, password)

        if user:
            session['user'] = user
            session['logged_in'] = True
            logger.info(f"User {username} logged in successfully")

            # UNIVERSAL SESSION RECOVERY CHECK - For ALL users
            recovery_data = None
            show_session_recovery = False

            if session_manager:
                try:
                    logger.info(f"🔍 Checking session recovery for user: {username}")

                    # Get recent sessions with meaningful activity
                    recovery_data = session_manager.get_session_recovery_data(username)

                    if recovery_data:
                        logger.info(f"📊 Recovery data found: {recovery_data}")

                        # Check if there are meaningful sessions to recover
                        if recovery_data.get('has_sessions', False):
                            sessions = recovery_data.get('sessions', [])

                            # Filter for sessions with actual work
                            meaningful_sessions = []
                            for sess in sessions:
                                # Check if session has meaningful content
                                if (sess.get('messages_count', 0) > 1 or
                                        sess.get('project_id') or
                                        sess.get('code_reviews_count', 0) > 0 or
                                        sess.get('last_active')):
                                    meaningful_sessions.append(sess)

                            if meaningful_sessions:
                                show_session_recovery = True
                                recovery_data['meaningful_sessions'] = meaningful_sessions
                                recovery_data['session_count'] = len(meaningful_sessions)
                                logger.info(f"✅ Found {len(meaningful_sessions)} recoverable sessions")
                            else:
                                logger.info("ℹ️ No meaningful sessions found for recovery")
                        else:
                            logger.info("ℹ️ No sessions available for recovery")
                    else:
                        logger.info("ℹ️ No recovery data available")

                except Exception as e:
                    logger.error(f"❌ Session recovery check failed: {e}")

            # UNIVERSAL SESSION RECOVERY - Show for ALL users
            if not show_session_recovery:
                logger.info(f"🎭 Activating universal session recovery for user: {username}")

                # Create a session entry for this login if session manager available
                if session_manager:
                    try:
                        # Create a new session for this login
                        demo_session_id = session_manager.create_new_session(
                            username,
                            f"Session {datetime.now().strftime('%d.%m %H:%M')}",
                            "general"
                        )

                        # Add a welcome message to make it meaningful
                        session_manager.save_chat_message(
                            demo_session_id,
                            username,
                            "Hallo! Wie kann ich dir beim Programmieren helfen?",
                            f"Willkommen {user.get('display_name', username)}! Ich bin dein KI-Programmierassistent. Möchtest du ein neues Projekt starten oder hast du Fragen zum Programmieren?",
                            {'mode': 'welcome', 'timestamp': datetime.now().isoformat()}
                        )

                        logger.info(f"✅ Created welcome session: {demo_session_id}")

                    except Exception as e:
                        logger.error(f"❌ Failed to create welcome session: {e}")

                # ALWAYS show session recovery modal for better UX
                recovery_data = {
                    'has_sessions': False,  # No previous sessions
                    'show_welcome': True,  # Show welcome modal instead
                    'user_name': user.get('display_name', username),
                    'options': [
                        {
                            'type': 'new_project',
                            'title': 'Neues Projekt starten',
                            'description': 'Erstelle ein neues Programmierprojekt',
                            'icon': '✨',
                            'action': 'create_project'
                        },
                        {
                            'type': 'explore_projects',
                            'title': 'Projekte erkunden',
                            'description': 'Schaue dir deine bestehenden Projekte an',
                            'icon': '📁',
                            'action': 'show_projects'
                        },
                        {
                            'type': 'free_chat',
                            'title': 'Freier Chat',
                            'description': 'Stelle Fragen zum Programmieren',
                            'icon': '💬',
                            'action': 'start_chat'
                        }
                    ],
                    'welcome_message': f"Willkommen zurück, {user.get('display_name', username)}! Wie möchtest du heute starten?"
                }
                show_session_recovery = True
                logger.info("✅ Universal session recovery modal activated")

            # Store recovery data in session for app interface
            if show_session_recovery and recovery_data:
                session['show_session_recovery'] = True
                session['recovery_data'] = recovery_data
                logger.info("🔄 Session recovery will be shown")
                if recovery_data:
                    if recovery_data.get('has_sessions'):
                        logger.info(
                            f"📊 Recovery type: Previous sessions ({recovery_data.get('session_count', 0)} sessions)")
                    else:
                        logger.info(f"📊 Recovery type: Welcome modal")
            else:
                session['show_session_recovery'] = False
                session['recovery_data'] = None
                logger.info("➡️ No session recovery needed")

            redirect_to = request.args.get('redirect', '/app')
            return redirect(redirect_to)
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Login error: {e}")
        return redirect(url_for('index'))


@app.route('/app')
def app_interface():
    """Enhanced app interface with session recovery"""
    if 'user' not in session:
        return redirect(url_for('login', redirect='/app'))

    try:
        user = session['user']

        # Get recovery data from session (set during login)
        show_session_recovery = session.pop('show_session_recovery', False)
        recovery_data = session.pop('recovery_data', None)

        logger.info(f"🎨 Rendering app for {user['username']}")
        logger.info(f"🔄 Show recovery: {show_session_recovery}")
        logger.info(f"📊 Recovery data: {recovery_data is not None}")

        if recovery_data:
            logger.info(f"📊 Recovery sessions count: {recovery_data.get('session_count', 0)}")

        return render_template('app.html',
                               user=user,
                               mode='programming',
                               show_session_recovery=show_session_recovery,
                               recovery_data=recovery_data)
    except Exception as e:
        logger.error(f"App template error: {e}")
        return f"""
        <html><body style="font-family: Arial; padding: 20px;">
        <h1>Programming Bot - {session['user']['display_name']}</h1>
        <p>Template not found. Please create templates/app.html</p>
        <p>Error: {e}</p>
        <p>Show recovery: {session.get('show_session_recovery', False)}</p>
        <a href="/logout">Logout</a>
        </body></html>
        """


@app.route('/chat')
def chat_interface():
    """Chat-Only interface"""
    if 'user' not in session:
        return redirect(url_for('login', redirect='/chat'))

    try:
        user = type('User', (), session['user'])()
        return render_template('app.html', user=user, mode='chat_only')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"""
        <html><body style="font-family: Arial; padding: 20px;">
        <h1>Chat-Only Bot - {session['user']['display_name']}</h1>
        <p>Template not found. Please create templates/app.html</p>
        <p>Error: {e}</p>
        <a href="/logout">Logout</a>
        </body></html>
        """

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            email = request.form.get('email', '').strip()
            display_name = request.form.get('display_name', '').strip()

            # Basic validation
            error = None

            # Username validation
            if not username or len(username) < 3:
                error = "Benutzername muss mindestens 3 Zeichen haben"
            elif len(username) > 50:
                error = "Benutzername darf maximal 50 Zeichen haben"

            # Password validation
            elif not password or len(password) < 6:
                error = "Passwort muss mindestens 6 Zeichen haben"

            # Password confirmation
            elif password != confirm_password:
                error = "Passwörter stimmen nicht überein"

            # E-Mail validation (only if provided)
            elif email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    error = "Bitte geben Sie eine gültige E-Mail-Adresse ein"

            if not error:
                # Attempt registration
                result = auth_system.register_user(username, email, password, display_name)

                if result.get('success'):
                    logger.info(f"✅ New user registered: {username}")

                    # Auto-login after successful registration
                    # Use authenticate_user to get proper user dict
                    user_dict = auth_system.authenticate_user(username, password)

                    if user_dict:
                        session['user'] = user_dict
                        session['logged_in'] = True
                        logger.info(f"✅ Auto-login successful for: {username}")
                        return redirect(url_for('app_interface'))
                    else:
                        # Registration succeeded but auto-login failed
                        logger.warning(f"⚠️ Registration OK but auto-login failed for: {username}")
                        return redirect(url_for('index'))  # Go to login page
                else:
                    error = result.get('error', 'Registrierung fehlgeschlagen')

            # Return registration page with error
            try:
                return render_template('register.html', error=error,
                                     username=username, email=email, display_name=display_name)
            except:
                return f"""
                <!DOCTYPE html>
                <html><head><title>Registration Error</title>
                <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .register-form {{ max-width: 400px; margin: 30px auto; }}
                input {{ width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 10px; }}
                button {{ width: 100%; padding: 15px; background: #6c5ce7; color: white; border: none; border-radius: 10px; cursor: pointer; }}
                .error {{ color: #ff6b6b; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style></head>
                <body>
                <h1>🤖 Programming Bot - Registrierung</h1>
                <div class="error">{error}</div>
                <form method="POST" class="register-form">
                    <input type="text" name="username" placeholder="Benutzername (min. 3 Zeichen)" required minlength="3" value="{username}">
                    <input type="email" name="email" placeholder="E-Mail (optional)" value="{email}">
                    <input type="text" name="display_name" placeholder="Anzeigename (optional)" value="{display_name}">
                    <input type="password" name="password" placeholder="Passwort (min. 6 Zeichen)" required minlength="6">
                    <input type="password" name="confirm_password" placeholder="Passwort bestätigen" required minlength="6">
                    <button type="submit">✨ Registrieren</button>
                </form>
                <p><a href="/" style="color: #00d4aa;">Bereits ein Konto? Anmelden</a></p>
                </body></html>
                """

        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            error = "Ein unerwarteter Fehler ist aufgetreten"
            try:
                return render_template('register.html', error=error)
            except:
                return redirect(url_for('index'))

    # GET request - show registration form
    try:
        return render_template('register.html')
    except:
        return """
        <!DOCTYPE html>
        <html><head><title>Programming Bot - Registrierung</title>
        <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .register-form { max-width: 400px; margin: 30px auto; }
        input { width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 10px; }
        button { width: 100%; padding: 15px; background: #6c5ce7; color: white; border: none; border-radius: 10px; cursor: pointer; }
        </style></head>
        <body>
        <h1>🤖 Programming Bot - Registrierung</h1>
        <p>Erstelle einen neuen Account</p>
        <form method="POST" class="register-form">
            <input type="text" name="username" placeholder="Benutzername (min. 3 Zeichen)" required minlength="3">
            <input type="email" name="email" placeholder="E-Mail (optional)">
            <input type="text" name="display_name" placeholder="Anzeigename (optional)">
            <input type="password" name="password" placeholder="Passwort (min. 6 Zeichen)" required minlength="6">
            <input type="password" name="confirm_password" placeholder="Passwort bestätigen" required minlength="6">
            <button type="submit">✨ Registrieren</button>
        </form>
        <p><a href="/" style="color: #00d4aa;">Bereits ein Konto? Anmelden</a></p>
        </body></html>
        """


@app.route('/api/check-username', methods=['POST'])
def check_username():
    """API endpoint to check username availability"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()

        if len(username) < 3:
            return jsonify({'available': False, 'message': 'Username zu kurz'})

        available = auth_system.check_username_available(username)
        return jsonify({
            'available': available,
            'message': 'Username verfügbar' if available else 'Username bereits vergeben'
        })

    except Exception as e:
        logger.error(f"❌ Username check error: {e}")
        return jsonify({'available': False, 'message': 'Fehler bei der Prüfung'})


@app.route('/logout')
def logout():
    """Handle user logout"""
    username = session.get('user', {}).get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('index'))


# Debug Routes
@app.route('/debug/session-recovery')
def debug_session_recovery():
    """Debug Session Recovery System"""
    if 'user' not in session:
        return "Not logged in"

    user_id = session['user']['username']

    debug_info = {
        'user_id': user_id,
        'session_manager_available': session_manager is not None,
        'session_manager_type': type(session_manager).__name__ if session_manager else None
    }

    if session_manager:
        try:
            recovery_data = session_manager.get_session_recovery_data(user_id)
            debug_info['recovery_data'] = recovery_data
            debug_info['recovery_data_type'] = type(recovery_data).__name__
            debug_info['has_sessions'] = recovery_data.get('has_sessions', False) if recovery_data else False
        except Exception as e:
            debug_info['session_manager_error'] = str(e)

    return f"""
    <h1>🔍 Session Recovery Debug</h1>
    <pre>{json.dumps(debug_info, indent=2, default=str)}</pre>

    <h2>Test Session Recovery</h2>
    <button onclick="testSessionRecovery()">Test Recovery Check</button>

    <div id="test-result"></div>

    <script>
    function testSessionRecovery() {{
        fetch('/api/session-recovery', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}}
        }})
        .then(response => response.json())
        .then(data => {{
            document.getElementById('test-result').innerHTML = 
                '<h3>API Response:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }})
        .catch(error => {{
            document.getElementById('test-result').innerHTML = 
                '<h3>Error:</h3><pre>' + error + '</pre>';
        }});
    }}
    </script>
    """


# Session Management API Routes
@app.route('/api/session-recovery', methods=['POST'])
def api_session_recovery():
    """Get session recovery data for user"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        if not session_manager:
            return jsonify({'success': False, 'error': 'Session manager not available'})

        user_id = session['user']['username']
        recovery_data = session_manager.get_session_recovery_data(user_id)

        return jsonify({
            'success': True,
            'recovery_data': recovery_data
        })

    except Exception as e:
        logger.error(f"Session recovery API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/resume-session', methods=['POST'])
def api_resume_session():
    """Resume a specific session"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        if not session_manager:
            return jsonify({'success': False, 'error': 'Session manager not available'})

        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID required'})

        session_data = session_manager.resume_session(session_id)

        if session_data['success']:
            # Store current session in Flask session
            session['current_session_id'] = session_id

            return jsonify({
                'success': True,
                'message': 'Session erfolgreich wiederhergestellt!',
                'session_data': session_data
            })
        else:
            return jsonify(session_data)

    except Exception as e:
        logger.error(f"Resume session API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/create-session', methods=['POST'])
def api_create_session():
    """Create a new session"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        if not session_manager:
            return jsonify({'success': False, 'error': 'Session manager not available'})

        data = request.get_json()
        project_name = data.get('project_name', '').strip()
        project_type = data.get('project_type', 'general')

        if not project_name:
            return jsonify({'success': False, 'error': 'Project name required'})

        user_id = session['user']['username']
        session_id = session_manager.create_new_session(user_id, project_name, project_type)

        # Store current session in Flask session
        session['current_session_id'] = session_id

        return jsonify({
            'success': True,
            'message': f'Neues Projekt "{project_name}" erstellt!',
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Create session API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/smart-suggestions', methods=['POST'])
def api_smart_suggestions():
    """Get smart suggestions for current session"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        if not session_manager:
            return jsonify({'success': False, 'error': 'Session manager not available'})

        current_session_id = session.get('current_session_id')
        if not current_session_id:
            return jsonify({'success': False, 'error': 'No active session'})

        user_id = session['user']['username']
        suggestions = session_manager.generate_smart_suggestions(current_session_id, user_id)

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.error(f"Smart suggestions API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


# Basic API Routes
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Enhanced chat API with session tracking"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        data = request.get_json()
        message = data.get('message', '').strip()
        mode = data.get('mode', 'programming')

        if not message:
            return jsonify({'success': False, 'error': 'Empty message'})

        # Prepare user context
        user_context = {
            'user_id': session['user']['username'],
            'display_name': session['user']['display_name'],
            'mode': mode,
            'context': 'chat_only' if mode == 'chat_only' else 'programming'
        }

        # Get session context if available
        current_session_id = session.get('current_session_id')
        if session_manager and current_session_id:
            try:
                session_context = session_manager.get_session_context(current_session_id)
                user_context.update(session_context)
            except Exception as e:
                logger.warning(f"Failed to get session context: {e}")

        # Process message with bot engine
        response = bot_engine.process_message(message, user_context)

        # Save to session if session manager available
        if session_manager and current_session_id:
            try:
                session_manager.save_chat_message(
                    current_session_id,
                    session['user']['username'],
                    message,
                    response,
                    {'mode': mode, 'timestamp': datetime.now().isoformat()}
                )
            except Exception as e:
                logger.warning(f"Failed to save chat to session: {e}")

        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'session_id': current_session_id
        })

    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/projects', methods=['GET'])
def get_projects_api():
    """Get all projects for current user"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        user_id = session['user']['username']
        logger.info(f"📋 API: Getting projects for user {user_id}")

        # Get user's bot engine
        user_bot_engine = get_user_bot_engine(user_id)

        # Try to get projects from bot engine
        if hasattr(user_bot_engine, 'get_user_projects'):
            projects = user_bot_engine.get_user_projects(user_id)
        else:
            # Fallback to existing method
            projects = user_bot_engine.get_projects(user_id) if hasattr(user_bot_engine, 'get_projects') else []

        logger.info(f"📋 API: Found {len(projects)} projects")

        return jsonify({
            'success': True,
            'projects': projects
        })

    except Exception as e:
        logger.error(f"❌ API Error getting projects: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Laden der Projekte'
        }), 500


@app.route('/api/projects', methods=['POST'])
def create_project_api():
    """Create a new project"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        language = data.get('language', 'python').strip()

        if not name:
            return jsonify({'success': False, 'error': 'Projektname ist erforderlich'}), 400

        user_id = session['user']['username']
        logger.info(f"📝 API: Creating project '{name}' for user {user_id}")

        # Get user's bot engine
        user_bot_engine = get_user_bot_engine(user_id)

        # Try to create project
        if hasattr(user_bot_engine, 'create_project'):
            if hasattr(user_bot_engine, 'get_user_projects'):
                # New style method signature
                result = user_bot_engine.create_project(user_id, name, description, language)
            else:
                # Old style method signature
                project_id = user_bot_engine.create_project(name, description, language, user_id)
                result = {
                    'success': True,
                    'project': {
                        'id': project_id,
                        'name': name,
                        'description': description,
                        'language': language,
                        'status': 'active',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                }
        else:
            # Fallback
            result = {
                'success': True,
                'project': {
                    'id': f"fallback_{int(datetime.now().timestamp())}",
                    'name': name,
                    'description': description,
                    'language': language,
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            }

        if result.get('success'):
            logger.info(f"✅ API: Project created successfully")
            return jsonify(result)
        else:
            logger.error(f"❌ API: Project creation failed: {result.get('error')}")
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"❌ API Error creating project: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Fehler beim Erstellen des Projekts: {str(e)}'
        }), 500


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        data = request.get_json()

        logger.info(f"📝 API: Updating project {project_id} for user {user_id}")

        # Get user's bot engine
        bot_engine = get_user_bot_engine(user_id)
        result = bot_engine.update_project(project_id, user_id, **data)

        if result.get('success'):
            logger.info(f"✅ API: Project updated successfully")
            return jsonify(result)
        else:
            logger.error(f"❌ API: Project update failed: {result.get('error')}")
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"❌ API Error updating project: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Aktualisieren des Projekts'
        }), 500


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        logger.info(f"🗑️ API: Deleting project {project_id} for user {user_id}")

        # Get user's bot engine
        bot_engine = get_user_bot_engine(user_id)
        result = bot_engine.delete_project(project_id, user_id)

        if result.get('success'):
            logger.info(f"✅ API: Project deleted successfully")
            return jsonify(result)
        else:
            logger.error(f"❌ API: Project deletion failed: {result.get('error')}")
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"❌ API Error deleting project: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Löschen des Projekts'
        }), 500


@app.route('/api/code-review', methods=['POST'])
def api_code_review():
    """Enhanced code review API with session tracking"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        data = request.get_json()
        code = data.get('code', '').strip()
        language = data.get('language', 'python')

        if not code:
            return jsonify({'success': False, 'error': 'No code provided'})

        # Analyze code with bot engine
        analysis = bot_engine.analyze_code(code, language)

        # Save to session if session manager available
        current_session_id = session.get('current_session_id')
        if session_manager and current_session_id and analysis.get('success'):
            try:
                session_manager.save_code_review_result(
                    current_session_id,
                    session['user']['username'],
                    code,
                    language,
                    analysis
                )
            except Exception as e:
                logger.warning(f"Failed to save code review to session: {e}")

        return jsonify(analysis)

    except Exception as e:
        logger.error(f"Code review API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/metrics')
def api_metrics():
    """Metrics API"""
    try:
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})

        user_id = session['user']['username']
        metrics = bot_engine.get_metrics(user_id)

        return jsonify({
            'success': True,
            **metrics
        })

    except Exception as e:
        logger.error(f"Metrics API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


def main():
    """Main application entry point"""
    try:
        # Load all modules
        load_modules()

        # Validate configuration
        if not config:
            logger.error("Configuration could not be loaded")
            sys.exit(1)

        # Update app secret key
        if hasattr(config, 'SECRET_KEY') and config.SECRET_KEY:
            app.secret_key = config.SECRET_KEY

        # Get server configuration
        host = getattr(config, 'HOST', '0.0.0.0')
        port = getattr(config, 'PORT', 8100)
        debug = getattr(config, 'DEBUG', False)

        logger.info("🚀 Programming Bot 2025 starting...")
        logger.info(f"📍 Server: http://{host}:{port}")
        logger.info(f"💻 Programming Interface: http://{host}:{port}/app")
        logger.info(f"💬 Chat-Only Interface: http://{host}:{port}/chat")

        # Start Flask app
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()