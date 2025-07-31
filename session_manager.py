"""
Session Manager - Complete Integration für Programming Bot
Kombiniert SessionStorage mit High-Level Session Management
"""

from session_storage import SessionStorage
import json
import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """
    High-Level Session Management für Programming Bot
    Verwendet SessionStorage als Backend
    """

    def __init__(self, storage_path: str = "data/sessions.db"):
        self.storage = SessionStorage(storage_path)
        logger.info("✅ Session Manager initialized")

    def get_session_recovery_data(self, user_id: str) -> Dict:
        """
        Get session recovery data für Login Modal
        Exactly wie in den vorigen Anweisungen geplant
        """
        try:
            # Get recent sessions
            sessions = self.storage.get_user_sessions_for_recovery(user_id, limit=5)

            if not sessions:
                return {
                    'has_sessions': False,
                    'message': 'Keine vorherigen Sessions gefunden',
                    'action': 'new_project'
                }

            # Single active session
            if len(sessions) == 1:
                session = sessions[0]
                return {
                    'has_sessions': True,
                    'single_session': True,
                    'session': {
                        'id': session['session_id'],
                        'name': session['session_name'],
                        'project': session['project_id'],
                        'last_active': session['last_active'],
                        'last_action': session['last_significant_action'],
                        'summary': session['session_summary']
                    },
                    'message': f"Session '{session['session_name']}' fortsetzen?",
                    'action': 'resume_single'
                }

            # Multiple sessions
            return {
                'has_sessions': True,
                'single_session': False,
                'sessions': [
                    {
                        'id': s['session_id'],
                        'name': s['session_name'],
                        'project': s['project_id'],
                        'last_active': s['last_active'],
                        'last_action': s['last_significant_action'],
                        'priority': s['recovery_priority'],
                        'health_score': s['session_health_score']
                    } for s in sessions
                ],
                'message': f"{len(sessions)} aktive Sessions gefunden",
                'action': 'choose_multiple'
            }

        except Exception as e:
            logger.error(f"❌ Session recovery error: {e}")
            return {
                'has_sessions': False,
                'error': str(e),
                'action': 'new_project'
            }

    def resume_session(self, session_id: str) -> Dict:
        """
        Resume a specific session mit complete context
        """
        try:
            # Get conversation history
            conversation = self.storage.get_conversation_history(session_id, limit=20)

            # Get recent code reviews
            code_reviews = self.storage.get_recent_code_reviews(session_id, limit=5)

            # Update session activity
            self.storage.update_session_activity(
                session_id,
                "Session resumed",
                {"resumed_at": datetime.datetime.now().isoformat()}
            )

            return {
                'success': True,
                'session_id': session_id,
                'conversation_history': conversation,
                'code_reviews': code_reviews,
                'context_loaded': True,
                'message': 'Session erfolgreich wiederhergestellt!'
            }

        except Exception as e:
            logger.error(f"❌ Resume session error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_smart_suggestions(self, session_id: str, user_id: str) -> List[Dict]:
        """
        Generate proactive suggestions basierend auf Session History
        """
        try:
            suggestions = []

            # Get recent code reviews for suggestions
            code_reviews = self.storage.get_recent_code_reviews(session_id, limit=3)

            for review in code_reviews:
                if not review['is_resolved'] and review['score'] < 90:
                    suggestions.append({
                        'type': 'code_improvement',
                        'title': f"Code Quality verbessern (Score: {review['score']}/100)",
                        'description': f"Offene Verbesserungen in {review['file_name'] or 'Code'}",
                        'priority': 2,
                        'action': 'review_suggestions',
                        'context': {
                            'file': review['file_name'],
                            'language': review['language'],
                            'suggestions': review['suggestions'][:3]  # Top 3
                        }
                    })

            # Get conversation context for next steps
            conversation = self.storage.get_conversation_history(session_id, limit=5)

            if conversation:
                last_messages = [msg['content'] for msg in conversation[-3:]]
                last_context = ' '.join(last_messages)

                # Simple heuristics für smart suggestions
                if 'error' in last_context.lower() or 'fehler' in last_context.lower():
                    suggestions.append({
                        'type': 'debugging',
                        'title': '🔧 Error-Handling verbessern',
                        'description': 'Robuste Fehlerbehandlung implementieren',
                        'priority': 1,
                        'action': 'add_error_handling'
                    })

                if 'test' in last_context.lower():
                    suggestions.append({
                        'type': 'testing',
                        'title': '🧪 Unit Tests erstellen',
                        'description': 'Automatisierte Tests für bessere Code-Qualität',
                        'priority': 2,
                        'action': 'create_tests'
                    })

                if 'deploy' in last_context.lower() or 'production' in last_context.lower():
                    suggestions.append({
                        'type': 'deployment',
                        'title': '🚀 Deployment vorbereiten',
                        'description': 'Production-ready Konfiguration erstellen',
                        'priority': 1,
                        'action': 'prepare_deployment'
                    })

            # Default suggestions wenn keine spezifischen gefunden
            if not suggestions:
                suggestions = [
                    {
                        'type': 'general',
                        'title': '📊 Code Review durchführen',
                        'description': 'Aktuellen Code analysieren und verbessern',
                        'priority': 3,
                        'action': 'code_review'
                    },
                    {
                        'type': 'general',
                        'title': '📝 Dokumentation erweitern',
                        'description': 'README und Code-Kommentare hinzufügen',
                        'priority': 3,
                        'action': 'add_documentation'
                    }
                ]

            # Sort by priority (1 = highest)
            suggestions.sort(key=lambda x: x['priority'])

            return suggestions[:5]  # Top 5 suggestions

        except Exception as e:
            logger.error(f"❌ Smart suggestions error: {e}")
            return []

    def create_new_session(self, user_id: str, project_name: str, project_type: str = "general") -> str:
        """
        Create a completely new session
        """
        try:
            session_context = {
                'project_type': project_type,
                'created_via': 'session_recovery',
                'user_preferences': {}
            }

            session_id = self.storage.create_session(user_id, project_name, session_context)

            # Add initial conversation
            self.storage.save_conversation_message(
                session_id, user_id, "system",
                f"Neues Projekt '{project_name}' gestartet. Wie kann ich dir helfen?",
                {'project_type': project_type}
            )

            logger.info(f"✅ Created new session {session_id} for project {project_name}")
            return session_id

        except Exception as e:
            logger.error(f"❌ Create session error: {e}")
            raise

    def save_chat_message(self, session_id: str, user_id: str, message: str, response: str, context: Dict = None):
        """
        Save chat conversation to session
        """
        try:
            # Save user message
            self.storage.save_conversation_message(
                session_id, user_id, "user", message, context
            )

            # Save assistant response
            self.storage.save_conversation_message(
                session_id, user_id, "assistant", response, context
            )

            # Update session activity
            self.storage.update_session_activity(
                session_id,
                "Chat message exchanged",
                {"last_message_preview": message[:100]}
            )

        except Exception as e:
            logger.error(f"❌ Save chat message error: {e}")

    def save_code_review_result(self, session_id: str, user_id: str, code: str, language: str, review_result: Dict):
        """
        Save code review result to session
        """
        try:
            review_id = self.storage.save_code_review(
                session_id, user_id, code, language, review_result
            )

            # Update session activity
            self.storage.update_session_activity(
                session_id,
                f"Code review completed (Score: {review_result.get('score', '?')}/100)",
                {
                    "review_id": review_id,
                    "language": language,
                    "score": review_result.get('score')
                }
            )

            return review_id

        except Exception as e:
            logger.error(f"❌ Save code review error: {e}")
            return None

    def get_session_context(self, session_id: str) -> Dict:
        """
        Get full session context for bot intelligence
        """
        try:
            # Get recent conversation (for context)
            conversation = self.storage.get_conversation_history(session_id, limit=10)

            # Get recent code reviews (for awareness of code quality)
            code_reviews = self.storage.get_recent_code_reviews(session_id, limit=3)

            return {
                'conversation_context': conversation,
                'code_review_context': code_reviews,
                'session_active': True
            }

        except Exception as e:
            logger.error(f"❌ Get session context error: {e}")
            return {}

# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get singleton session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager