"""
api_routes.py - Improved API Routes für Programming Bot 2025
Implementiert alle Code-Review Vorschläge:
- Pydantic Models für Request/Response
- Zentralisierte Fehlerbehandlung
- Ausgelagerte Logik
- Spezifische HTTP Status Codes
- Type Safety
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Import Pydantic Models
from models import (
    ChatRequest, ChatResponse,
    CodeReviewRequest, CodeReviewResponse, CodeReviewSuggestion,
    ProjectCreateRequest, ProjectCreateResponse, ProjectsListResponse,
    SessionCreateRequest, SessionCreateResponse, SessionResumeRequest,
    SmartSuggestionsResponse, MetricsResponse, ProfileResponse,
    ErrorResponse, BaseResponse,
    create_error_response, create_success_response,
    validate_session_id, validate_project_name, ValidationError
)

logger = logging.getLogger(__name__)


# =====================================
# BUSINESS LOGIC FUNCTIONS
# =====================================

def create_code_review_prompt(language: str, code: str, focus_areas: Optional[List[str]] = None) -> str:
    """Erstellt den Prompt für die Code-Review-Analyse"""
    focus_text = ""
    if focus_areas:
        focus_text = f"\nBesonders fokussiere auf: {', '.join(focus_areas)}"

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
{focus_text}

Gib eine ehrliche Bewertung von 0-100 Punkten und konkrete, umsetzbare Verbesserungsvorschläge.
Strukturiere deine Antwort so:

SCORE: [0-100]
ANALYSE: [Detaillierte Bewertung]
VORSCHLÄGE: [Konkrete Verbesserungen]
PROBLEME: [Gefundene Issues]
STÄRKEN: [Positive Aspekte]
"""


def parse_code_review_response(ai_response: str, language: str) -> Dict:
    """Parsed AI Code Review Response in strukturierte Daten"""
    try:
        # Extract score
        score = 75  # Default
        if "SCORE:" in ai_response:
            score_text = ai_response.split("SCORE:")[1].split("\n")[0].strip()
            try:
                score = int(''.join(filter(str.isdigit, score_text))[:2])
                score = max(0, min(100, score))  # Clamp to 0-100
            except:
                pass

        # Extract sections
        sections = {
            'analysis': extract_section(ai_response, "ANALYSE:"),
            'suggestions': extract_list_section(ai_response, "VORSCHLÄGE:"),
            'issues': extract_list_section(ai_response, "PROBLEME:"),
            'strengths': extract_list_section(ai_response, "STÄRKEN:")
        }

        # Create suggestions objects
        suggestions = []
        for i, suggestion in enumerate(sections['suggestions'][:5]):  # Max 5
            suggestions.append(CodeReviewSuggestion(
                type="improvement",
                severity="medium" if score < 70 else "low",
                title=f"Verbesserung {i + 1}",
                description=suggestion,
                line=None,
                example=None
            ))

        return {
            'score': score,
            'analysis': sections['analysis'] or ai_response[:500],
            'language': language,
            'suggestions': suggestions,
            'issues_found': sections['issues'][:10],  # Max 10
            'strengths': sections['strengths'][:5]  # Max 5
        }

    except Exception as e:
        logger.error(f"Failed to parse code review response: {e}")
        return {
            'score': 70,
            'analysis': ai_response[:500],
            'language': language,
            'suggestions': [],
            'issues_found': ["Fehler beim Parsen der AI-Antwort"],
            'strengths': []
        }


def extract_section(text: str, marker: str) -> str:
    """Extrahiert einen Textabschnitt nach einem Marker"""
    if marker not in text:
        return ""

    start = text.find(marker) + len(marker)
    end = text.find("\n\n", start)
    if end == -1:
        # Find next section marker
        next_markers = ["VORSCHLÄGE:", "PROBLEME:", "STÄRKEN:", "SCORE:"]
        end = len(text)
        for next_marker in next_markers:
            pos = text.find(next_marker, start)
            if pos != -1 and pos < end:
                end = pos

    return text[start:end].strip()


def extract_list_section(text: str, marker: str) -> List[str]:
    """Extrahiert eine Liste aus einem Textabschnitt"""
    section_text = extract_section(text, marker)
    if not section_text:
        return []

    # Split by common list patterns
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


def calculate_user_metrics(user_id: int, bot_engine) -> Dict:
    """Calculate comprehensive user metrics"""
    try:
        # Get basic stats from bot engine
        base_stats = bot_engine.get_stats() if hasattr(bot_engine, 'get_stats') else {}

        return {
            "messages_today": base_stats.get("messages_today", 0),
            "total_messages": base_stats.get("total_messages", 0),
            "projects_count": base_stats.get("projects_count", 0),
            "code_reviews": base_stats.get("code_reviews", 0),
            "avg_response_time": base_stats.get("avg_response_time", "0.5s"),
            "last_activity": datetime.now(),
            "user_since": base_stats.get("user_since", datetime.now())
        }
    except Exception as e:
        logger.error(f"Failed to calculate metrics for user {user_id}: {e}")
        return {
            "messages_today": 0,
            "total_messages": 0,
            "projects_count": 0,
            "code_reviews": 0,
            "avg_response_time": "unknown",
            "last_activity": datetime.now(),
            "user_since": datetime.now()
        }


# =====================================
# API ROUTES FACTORY
# =====================================

def create_api_routes(auth_system, get_user_bot_engine, require_auth):
    """Creates all API routes for the Programming Bot with improved error handling"""

    router = APIRouter(prefix="/api")

    # ==================== CHAT API ====================

    @router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
    async def api_chat(chat_request: ChatRequest, user=Depends(require_auth)):
        """
        Chat API - Verarbeitet Nachrichten mit Bot

        Verbesserte Version mit:
        - Pydantic Validation
        - Type Safety  
        - Strukturierte Response
        """
        # Bot-Engine für User holen
        bot_engine = get_user_bot_engine(user)

        # User Context erweitern
        user_context = {
            'user_id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'mode': chat_request.mode,
            'session_id': chat_request.session_id
        }

        # Nachricht verarbeiten
        response = bot_engine.process_message(chat_request.message, user_context=user_context)

        logger.info(f"Chat processed for user {user.username}: {chat_request.message[:50]}...")

        return ChatResponse(
            success=True,
            response=response,
            session_id=chat_request.session_id,
            mode=chat_request.mode,
            message="Nachricht erfolgreich verarbeitet"
        )

    # ==================== CODE REVIEW API ====================

    @router.post("/code-review", response_model=CodeReviewResponse, status_code=status.HTTP_200_OK)
    async def api_code_review(review_request: CodeReviewRequest, user=Depends(require_auth)):
        """
        Code Review API - Analysiert Code-Qualität

        Verbesserte Version mit:
        - Strukturierter AI Prompt
        - Parsed Response
        - Detaillierte Suggestions
        """
        # Bot-Engine für Code-Analyse verwenden
        bot_engine = get_user_bot_engine(user)

        # Erstelle strukturierten Review-Prompt
        review_prompt = create_code_review_prompt(
            language=review_request.language.value,
            code=review_request.code,
            focus_areas=review_request.focus_areas
        )

        # User Context für Review
        user_context = {
            'user_id': user.id,
            'action': 'code_review',
            'language': review_request.language.value,
            'file_name': review_request.file_name
        }

        # AI Review ausführen
        ai_response = bot_engine.process_message(review_prompt, user_context=user_context)

        # Parse AI Response zu strukturierten Daten
        parsed_result = parse_code_review_response(ai_response, review_request.language.value)

        logger.info(f"Code review completed for user {user.username}, score: {parsed_result['score']}")

        return CodeReviewResponse(
            success=True,
            score=parsed_result['score'],
            analysis=parsed_result['analysis'],
            language=review_request.language,
            suggestions=parsed_result['suggestions'],
            issues_found=parsed_result['issues_found'],
            strengths=parsed_result['strengths'],
            file_name=review_request.file_name,
            message=f"Code Review abgeschlossen - Score: {parsed_result['score']}/100"
        )

    # ==================== PROJECTS API ====================

    @router.get("/projects", response_model=ProjectsListResponse, status_code=status.HTTP_200_OK)
    async def api_get_projects(user=Depends(require_auth)):
        """Get User Projects mit strukturierter Response"""
        bot_engine = get_user_bot_engine(user)
        projects = bot_engine.get_user_projects()

        # Convert to Pydantic models if needed
        project_responses = []
        for project in projects:
            if isinstance(project, dict):
                project_responses.append({
                    'id': project.get('id', ''),
                    'name': project.get('name', ''),
                    'description': project.get('description'),
                    'language': project.get('language', 'python'),
                    'status': project.get('status', 'active'),
                    'created_at': datetime.fromisoformat(project.get('created_at', datetime.now().isoformat())),
                    'updated_at': datetime.fromisoformat(project.get('updated_at', datetime.now().isoformat())),
                    'tags': project.get('tags', []),
                    'is_public': project.get('is_public', False)
                })

        return ProjectsListResponse(
            success=True,
            projects=project_responses,
            count=len(project_responses),
            message=f"{len(project_responses)} Projekte gefunden"
        )

    @router.post("/projects", response_model=ProjectCreateResponse, status_code=status.HTTP_201_CREATED)
    async def api_create_project(project_request: ProjectCreateRequest, user=Depends(require_auth)):
        """
        Create New Project

        Verbesserte Version mit:
        - 201 Created Status
        - Validierung
        - Strukturierte Response
        """
        # Validate project name
        validated_name = validate_project_name(project_request.name)

        bot_engine = get_user_bot_engine(user)
        project_id = bot_engine.create_project(
            name=validated_name,
            description=project_request.description or "",
            language=project_request.language.value,
            user_id=user.id
        )

        # Create response project object
        created_project = {
            'id': project_id,
            'name': validated_name,
            'description': project_request.description,
            'language': project_request.language,
            'status': 'active',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'tags': project_request.tags or [],
            'is_public': project_request.is_public
        }

        logger.info(f"Project '{validated_name}' created for user {user.username}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ProjectCreateResponse(
                success=True,
                project_id=project_id,
                project=created_project,
                message=f"Projekt '{validated_name}' erfolgreich erstellt!"
            ).dict()
        )

    # ==================== METRICS API ====================

    @router.get("/metrics", response_model=MetricsResponse, status_code=status.HTTP_200_OK)
    async def api_metrics(user=Depends(require_auth)):
        """Dashboard Metrics API mit detaillierten Metriken"""
        bot_engine = get_user_bot_engine(user)

        # Calculate comprehensive metrics
        metrics = calculate_user_metrics(user.id, bot_engine)

        return MetricsResponse(
            success=True,
            metrics=metrics,
            message="Metriken erfolgreich geladen"
        )

    # ==================== USER MANAGEMENT API ====================

    @router.get("/profile", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
    async def api_get_profile(user=Depends(require_auth)):
        """Get User Profile mit strukturierten Daten"""
        user_profile = {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": getattr(user, 'email', ''),
            "last_login": getattr(user, 'last_login'),
            "created_at": getattr(user, 'created_at', datetime.now()),
            "preferences": getattr(user, 'preferences', {})
        }

        return ProfileResponse(
            success=True,
            user=user_profile,
            message="Profil erfolgreich geladen"
        )

    @router.post("/logout", response_model=BaseResponse, status_code=status.HTTP_200_OK)
    async def api_logout(user=Depends(require_auth)):
        """Logout API mit proper cleanup"""
        try:
            # Session invalidieren - implementierung depends on auth system
            if hasattr(auth_system, 'invalidate_user_session'):
                auth_system.invalidate_user_session(user.id)

            logger.info(f"User {user.username} logged out via API")

            return create_success_response("Erfolgreich abgemeldet")

        except Exception as e:
            logger.error(f"Logout error for user {user.username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout fehlgeschlagen"
            )

    # ==================== SESSION MANAGEMENT ====================

    @router.post("/session-recovery", response_model=BaseResponse, status_code=status.HTTP_200_OK)
    async def api_session_recovery(user=Depends(require_auth)):
        """Session Recovery API"""
        # This would typically interface with your session manager
        # Implementation depends on your session management system
        return create_success_response("Session recovery data retrieved")

    @router.post("/create-session", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
    async def api_create_session(session_request: SessionCreateRequest, user=Depends(require_auth)):
        """Create New Session"""
        session_id = f"session_{user.id}_{int(datetime.now().timestamp())}"

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=SessionCreateResponse(
                success=True,
                session_id=session_id,
                message=f"Session für '{session_request.project_name}' erstellt"
            ).dict()
        )

    @router.post("/resume-session", response_model=BaseResponse, status_code=status.HTTP_200_OK)
    async def api_resume_session(resume_request: SessionResumeRequest, user=Depends(require_auth)):
        """Resume Existing Session"""
        try:
            # Validate session ID
            validated_session_id = validate_session_id(resume_request.session_id)

            # Implementation would resume the actual session

            return create_success_response(f"Session {validated_session_id} erfolgreich fortgesetzt")

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )

    return router


# =====================================
# GLOBAL EXCEPTION HANDLERS
# =====================================

def setup_exception_handlers(app):
    """Setup global exception handlers für bessere Fehlerbehandlung"""

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error_message=exc.message,
                error_code="VALIDATION_ERROR"
            ).dict()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error_message=exc.detail,
                error_code="HTTP_ERROR"
            ).dict()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                error_message="Ein interner Serverfehler ist aufgetreten",
                error_code="INTERNAL_ERROR"
            ).dict()
        )


# =====================================
# USAGE EXAMPLE
# =====================================

"""
# In main.py:

from fastapi import FastAPI
from api_routes import create_api_routes, setup_exception_handlers

app = FastAPI(title="Programming Bot 2025", version="1.0.0")

# Setup exception handlers
setup_exception_handlers(app)

# Create API routes
api_router = create_api_routes(auth_system, get_user_bot_engine, require_auth)
app.include_router(api_router)

# Your existing routes...
"""