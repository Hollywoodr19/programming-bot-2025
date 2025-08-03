"""
api_routes.py - Flask API Routes für Programming Bot 2025
Konvertiert von FastAPI zu Flask für Kompatibilität
"""

import logging
from functools import wraps
from flask import Blueprint, request, jsonify, session

# Holen Sie sich einen Logger für dieses Modul
logger = logging.getLogger(__name__)


def create_api_routes(bot_engine, auth_system):
    """Factory-Funktion zum Erstellen des API-Blueprints mit Abhängigkeiten."""

    api_bp = Blueprint('api', __name__, url_prefix='/api')

    # Dieser Decorator ist korrekt für die API, da er JSON zurückgibt.
    def require_api_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Wir verwenden hier die valid_session Methode aus dem übergebenen auth_system
            if not auth_system.validate_session():
                logger.warning("Unauthentifizierter API-Zugriff versucht für: %s", request.path)
                return jsonify({'success': False, 'error': 'AUTHENTICATION_REQUIRED',
                                'message': 'Authentifizierung erforderlich.'}), 401
            return f(*args, **kwargs)

        return decorated_function

    # =====================================
    # HELPER FUNCTIONS
    # =====================================

    def create_code_review_prompt(language: str, code: str) -> str:
        """Erstellt den Prompt für die Code-Review-Analyse"""
        return f"""
Analysiere diesen {language}-Code und gib eine detaillierte Code-Review:

```{language}
{code}
```

Bewerte folgende Aspekte:
1. 🔧 Funktionalität - Macht der Code was er soll?
2. 🎯 Code-Qualität - Lesbarkeit, Wartbarkeit, Struktur
3. 🔒 Sicherheit - Potentielle Sicherheitslücken
4. ⚡ Performance - Effizienz und Optimierungsmöglichkeiten
5. ✅ Best Practices - Folgt der Code etablierten Standards?

Gib eine ehrliche Bewertung von 0-100 Punkten und konkrete, umsetzbare Verbesserungsvorschläge.
Strukturiere deine Antwort so:

SCORE: [0-100]
ANALYSE: [Detaillierte Bewertung]
VORSCHLÄGE: [Konkrete Verbesserungen]
PROBLEME: [Gefundene Issues]
STÄRKEN: [Positive Aspekte]
"""

    def parse_code_review_response(ai_response: str, language: str) -> dict:
        """Parsed AI Code Review Response in strukturierte Daten"""
        try:
            # Extract score
            score = 75  # Default
            if "SCORE:" in ai_response:
                score_text = ai_response.split("SCORE:")[1].split("\n")[0].strip()
                try:
                    score = int(''.join(filter(str.isdigit, score_text))[:2])
                    score = max(0, min(100, score))
                except:
                    pass

            # Extract sections
            analysis = extract_section(ai_response, "ANALYSE:")
            suggestions = extract_list_section(ai_response, "VORSCHLÄGE:")
            issues = extract_list_section(ai_response, "PROBLEME:")
            strengths = extract_list_section(ai_response, "STÄRKEN:")

            return {
                'score': score,
                'analysis': analysis or ai_response[:500],
                'language': language,
                'suggestions': suggestions[:5],  # Max 5
                'issues_found': issues[:10],  # Max 10
                'strengths': strengths[:5]  # Max 5
            }

        except Exception as e:
            logger.error(f"Failed to parse code review response: {e}")
            return {
                'score': 70,
                'analysis': ai_response[:500],
                'language': language,
                'suggestions': ["Fehler beim Parsen der AI-Antwort"],
                'issues_found': [],
                'strengths': []
            }

    def extract_section(text: str, marker: str) -> str:
        """Extrahiert einen Textabschnitt nach einem Marker"""
        if marker not in text:
            return ""

        start = text.find(marker) + len(marker)
        end = text.find("\n\n", start)
        if end == -1:
            next_markers = ["VORSCHLÄGE:", "PROBLEME:", "STÄRKEN:", "SCORE:"]
            end = len(text)
            for next_marker in next_markers:
                pos = text.find(next_marker, start)
                if pos != -1 and pos < end:
                    end = pos

        return text[start:end].strip()

    def extract_list_section(text: str, marker: str) -> list:
        """Extrahiert eine Liste aus einem Textabschnitt"""
        section_text = extract_section(text, marker)
        if not section_text:
            return []

        items = []
        for line in section_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove list markers
            for prefix in ['- ', '• ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            if line:
                items.append(line)

        return items

    # =====================================
    # API ROUTES
    # =====================================

    @api_bp.route('/chat', methods=['POST'])
    @require_api_auth  # Verwenden Sie den API-Auth-Decorator
    def api_chat():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

            message = data.get('message')
            if not message:
                return jsonify({'success': False, 'error': 'Message is required'}), 400

            user = session['user']

            # User Context erweitern
            user_context = {
                'user_id': user.get('id'),
                'username': user.get('username'),
                'display_name': user.get('display_name'),
                'mode': data.get('mode', 'programming'),
                'session_id': data.get('session_id')
            }

            # Nachricht verarbeiten
            response = bot_engine.process_message(message, user_context=user_context)

            logger.info(f"Chat processed for user {user.get('username')}: {message[:50]}...")

            return jsonify({
                'success': True,
                'response': response,
                'session_id': data.get('session_id'),
                'mode': data.get('mode', 'programming'),
                'message': 'Nachricht erfolgreich verarbeitet'
            })

        except Exception as e:
            logger.error(f"Chat API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

        pass  # Platzhalter

    @api_bp.route('/code-review', methods=['POST'])
    @require_api_auth  # Verwenden Sie den API-Auth-Decorator
    def api_code_review():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

            code = data.get('code')
            language = data.get('language', 'python')

            if not code:
                return jsonify({'success': False, 'error': 'Code is required'}), 400

            user = session['user']

            # Erstelle strukturierten Review-Prompt
            review_prompt = create_code_review_prompt(language, code)

            # User Context für Review
            user_context = {
                'user_id': user.get('id'),
                'action': 'code_review',
                'language': language,
                'file_name': data.get('file_name')
            }

            # AI Review ausführen
            ai_response = bot_engine.process_message(review_prompt, user_context=user_context)

            # Parse AI Response zu strukturierten Daten
            parsed_result = parse_code_review_response(ai_response, language)

            logger.info(f"Code review completed for user {user.get('username')}, score: {parsed_result['score']}")

            return jsonify({
                'success': True,
                'score': parsed_result['score'],
                'analysis': parsed_result['analysis'],
                'language': language,
                'suggestions': parsed_result['suggestions'],
                'issues_found': parsed_result['issues_found'],
                'strengths': parsed_result['strengths'],
                'file_name': data.get('file_name'),
                'message': f"Code Review abgeschlossen - Score: {parsed_result['score']}/100"
            })

        except Exception as e:
            logger.error(f"Code review API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/projects', methods=['GET'])
    @require_api_auth
    def api_get_projects():
        """Get User Projects"""
        try:
            user = session['user']
            projects = bot_engine.get_user_projects(user.get('id'))

            logger.info(f"📋 API: Getting projects for user {user.get('username')}")

            return jsonify({
                'success': True,
                'projects': projects,
                'count': len(projects),
                'message': f"{len(projects)} Projekte gefunden"
            })

        except Exception as e:
            logger.error(f"Get projects API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/projects', methods=['POST'])
    @require_api_auth
    def api_create_project():
        """Create New Project"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

            name = data.get('name')
            if not name:
                return jsonify({'success': False, 'error': 'Project name is required'}), 400

            user = session['user']

            result = bot_engine.create_project(
                user_id=user.get('id'),
                name=name,
                description=data.get('description', ''),
                language=data.get('language', 'python')
            )

            if result.get('success'):
                logger.info(f"Project '{name}' created for user {user.get('username')}")
                return jsonify(result), 201
            else:
                return jsonify(result), 400

        except Exception as e:
            logger.error(f"Create project API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/metrics', methods=['GET'])
    @require_api_auth
    def api_metrics():
        """Dashboard Metrics API"""
        try:
            user = session['user']
            metrics = bot_engine.get_metrics(user.get('id'))

            return jsonify({
                'success': True,
                'metrics': metrics,
                'message': 'Metriken erfolgreich geladen'
            })

        except Exception as e:
            logger.error(f"Metrics API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/session-recovery', methods=['POST'])
    @require_api_auth
    def api_session_recovery():
        """Session Recovery API"""
        try:
            return jsonify({
                'success': True,
                'message': 'Session recovery data retrieved'
            })
        except Exception as e:
            logger.error(f"Session recovery API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/smart-suggestions', methods=['POST'])
    @require_api_auth
    def api_smart_suggestions():
        """Smart Suggestions API"""
        try:
            data = request.get_json()
            context = data.get('context', 'general') if data else 'general'

            # Simple suggestions based on context
            suggestions = {
                'programming': [
                    "Erstelle ein neues Python-Projekt",
                    "Code-Review für bestehenden Code",
                    "Erkläre ein Programmierkonzept"
                ],
                'general': [
                    "Starte ein neues Projekt",
                    "Überprüfe deine Projektliste",
                    "Frage nach Hilfe"
                ]
            }

            return jsonify({
                'success': True,
                'suggestions': suggestions.get(context, suggestions['general']),
                'message': 'Smart suggestions generated'
            })

        except Exception as e:
            logger.error(f"Smart suggestions API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/resume-session', methods=['POST'])
    @require_api_auth
    def api_resume_session():
        """Resume Session API"""
        try:
            data = request.get_json()
            session_id = data.get('session_id') if data else None

            if not session_id:
                return jsonify({'success': False, 'error': 'Session ID required'}), 400

            return jsonify({
                'success': True,
                'message': f'Session {session_id} resumed'
            })

        except Exception as e:
            logger.error(f"Resume session API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @api_bp.route('/check-username', methods=['POST'])
    @require_api_auth
    def api_check_username():
        """Check Username Availability"""
        try:
            data = request.get_json()
            username = data.get('username') if data else None

            if not username:
                return jsonify({'success': False, 'error': 'Username required'}), 400

            # Check with auth system
            available = auth_system.check_username_available(username)

            return jsonify({
                'success': True,
                'available': available,
                'message': 'Username checked'
            })

        except Exception as e:
            logger.error(f"Check username API error: {e}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    # =====================================
    # ERROR HANDLERS
    # =====================================

    @api_bp.errorhandler(404)
    def api_not_found(error):
        return jsonify({'success': False, 'error': 'API endpoint not found'}), 404

    @api_bp.errorhandler(500)
    def api_internal_error(error):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    return api_bp


def setup_exception_handlers(app):
    """Setup global exception handlers"""

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'success': False, 'error': 'Page not found'}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500