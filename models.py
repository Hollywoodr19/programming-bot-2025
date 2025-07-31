"""
Pydantic Models für Programming Bot 2025 API
Definiert alle Request/Response Schemas für type safety und validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# =====================================
# ENUMS
# =====================================

class ProgrammingLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    HTML = "html"
    CSS = "css"

class ProjectStatus(str, Enum):
    """Project status options"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"

class ChatMode(str, Enum):
    """Chat mode options"""
    PROGRAMMING = "programming"
    CHAT_ONLY = "chat_only"
    HELP = "help"
    LEARN = "learn"

# =====================================
# REQUEST MODELS
# =====================================

class ChatRequest(BaseModel):
    """Request model for chat API"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Die Nachricht des Benutzers"
    )
    mode: ChatMode = Field(
        default=ChatMode.PROGRAMMING,
        description="Chat-Modus für kontextuelle Antworten"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optionale Session-ID für Kontext"
    )

    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Nachricht darf nicht leer sein')
        return v.strip()

class CodeReviewRequest(BaseModel):
    """Request model for code review API"""
    code: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Der zu analysierende Code"
    )
    language: ProgrammingLanguage = Field(
        default=ProgrammingLanguage.PYTHON,
        description="Programmiersprache des Codes"
    )
    file_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional: Name der Datei"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Spezifische Bereiche für Review-Focus"
    )

    @validator('code')
    def code_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Code darf nicht leer sein')
        return v.strip()

class ProjectCreateRequest(BaseModel):
    """Request model for project creation"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name des Projekts"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Beschreibung des Projekts"
    )
    language: ProgrammingLanguage = Field(
        default=ProgrammingLanguage.PYTHON,
        description="Hauptprogrammiersprache"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags für Kategorisierung"
    )
    is_public: bool = Field(
        default=False,
        description="Öffentlich sichtbar"
    )

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Projektname darf nicht leer sein')
        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError('Maximal 10 Tags erlaubt')
        return v

class SessionCreateRequest(BaseModel):
    """Request model for session creation"""
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name des Projekts für die Session"
    )
    project_type: ProgrammingLanguage = Field(
        default=ProgrammingLanguage.PYTHON,
        description="Typ/Sprache des Projekts"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Zusätzlicher Kontext für die Session"
    )

class SessionResumeRequest(BaseModel):
    """Request model for session resume"""
    session_id: str = Field(
        ...,
        min_length=1,
        description="ID der zu fortsetzenden Session"
    )

# =====================================
# RESPONSE MODELS
# =====================================

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(description="Erfolg der Operation")
    message: Optional[str] = Field(None, description="Nachricht für den User")
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = Field(default=False)
    error: str = Field(description="Fehlerbeschreibung")
    error_code: Optional[str] = Field(None, description="Fehlercode")

class ChatResponse(BaseResponse):
    """Response model for chat API"""
    response: str = Field(description="Antwort des Bots")
    session_id: Optional[str] = Field(None, description="Aktuelle Session-ID")
    mode: ChatMode = Field(description="Verwendeter Chat-Modus")

class CodeReviewSuggestion(BaseModel):
    """Single code review suggestion"""
    type: str = Field(description="Art der Verbesserung")
    line: Optional[int] = Field(None, description="Betroffene Zeile")
    severity: str = Field(description="Schweregrad: low, medium, high, critical")
    title: str = Field(description="Kurzer Titel")
    description: str = Field(description="Detaillierte Beschreibung")
    example: Optional[str] = Field(None, description="Beispiel-Code")

class CodeReviewResponse(BaseResponse):
    """Response model for code review API"""
    score: int = Field(ge=0, le=100, description="Qualitäts-Score 0-100")
    analysis: str = Field(description="Detaillierte Analyse")
    language: ProgrammingLanguage = Field(description="Analysierte Sprache")
    suggestions: List[CodeReviewSuggestion] = Field(description="Verbesserungsvorschläge")
    issues_found: List[str] = Field(description="Gefundene Probleme")
    strengths: List[str] = Field(description="Stärken des Codes")
    file_name: Optional[str] = Field(None, description="Name der analysierten Datei")

class ProjectResponse(BaseModel):
    """Single project response"""
    id: str = Field(description="Projekt-ID")
    name: str = Field(description="Projektname")
    description: Optional[str] = Field(description="Beschreibung")
    language: ProgrammingLanguage = Field(description="Programmiersprache")
    status: ProjectStatus = Field(description="Status")
    created_at: datetime = Field(description="Erstellungsdatum")
    updated_at: datetime = Field(description="Letzte Änderung")
    tags: List[str] = Field(default=[], description="Tags")
    is_public: bool = Field(description="Öffentlich")

class ProjectsListResponse(BaseResponse):
    """Response model for projects list"""
    projects: List[ProjectResponse] = Field(description="Liste der Projekte")
    count: int = Field(description="Anzahl Projekte")

class ProjectCreateResponse(BaseResponse):
    """Response model for project creation"""
    project_id: str = Field(description="ID des erstellten Projekts")
    project: ProjectResponse = Field(description="Erstelltes Projekt")

class UserMetrics(BaseModel):
    """User metrics model"""
    messages_today: int = Field(ge=0, description="Nachrichten heute")
    total_messages: int = Field(ge=0, description="Gesamte Nachrichten")
    projects_count: int = Field(ge=0, description="Anzahl Projekte")
    code_reviews: int = Field(ge=0, description="Durchgeführte Code-Reviews")
    avg_response_time: str = Field(description="Durchschnittliche Antwortzeit")
    last_activity: datetime = Field(description="Letzte Aktivität")
    user_since: datetime = Field(description="Mitglied seit")

class MetricsResponse(BaseResponse):
    """Response model for metrics API"""
    metrics: UserMetrics = Field(description="Benutzer-Metriken")

class UserProfile(BaseModel):
    """User profile model"""
    id: int = Field(description="User-ID")
    username: str = Field(description="Benutzername")
    display_name: str = Field(description="Anzeigename")
    email: Optional[str] = Field(description="E-Mail-Adresse")
    last_login: Optional[datetime] = Field(description="Letzter Login")
    created_at: datetime = Field(description="Registrierungsdatum")
    preferences: Optional[Dict[str, Any]] = Field(description="Benutzer-Einstellungen")

class ProfileResponse(BaseResponse):
    """Response model for profile API"""
    user: UserProfile = Field(description="Benutzerprofil")

class SessionData(BaseModel):
    """Session data model"""
    session_id: str = Field(description="Session-ID")
    session_name: str = Field(description="Session-Name")
    project_id: Optional[str] = Field(description="Projekt-ID")
    last_active: datetime = Field(description="Letzte Aktivität")
    last_action: str = Field(description="Letzte Aktion")
    summary: str = Field(description="Session-Zusammenfassung")

class SessionRecoveryData(BaseModel):
    """Session recovery data model"""
    has_sessions: bool = Field(description="Sessions verfügbar")
    single_session: bool = Field(description="Nur eine Session")
    session: Optional[SessionData] = Field(description="Einzelne Session")
    sessions: Optional[List[SessionData]] = Field(description="Mehrere Sessions")
    message: str = Field(description="Nachricht für User")
    action: str = Field(description="Empfohlene Aktion")

class SessionRecoveryResponse(BaseResponse):
    """Response model for session recovery"""
    recovery_data: SessionRecoveryData = Field(description="Recovery-Daten")

class SessionCreateResponse(BaseResponse):
    """Response model for session creation"""
    session_id: str = Field(description="Erstellte Session-ID")

class SmartSuggestion(BaseModel):
    """Smart suggestion model"""
    type: str = Field(description="Art der Suggestion")
    title: str = Field(description="Titel")
    description: str = Field(description="Beschreibung")
    priority: int = Field(ge=1, le=5, description="Priorität 1-5")
    action: str = Field(description="Empfohlene Aktion")
    context: Optional[Dict[str, Any]] = Field(description="Zusätzlicher Kontext")

class SmartSuggestionsResponse(BaseResponse):
    """Response model for smart suggestions"""
    suggestions: List[SmartSuggestion] = Field(description="Intelligente Vorschläge")

# =====================================
# HELPER FUNCTIONS
# =====================================

def create_error_response(error_message: str, error_code: Optional[str] = None) -> ErrorResponse:
    """Helper function to create error responses"""
    return ErrorResponse(
        error=error_message,
        error_code=error_code,
        message="Ein Fehler ist aufgetreten"
    )

def create_success_response(message: str = "Operation erfolgreich") -> BaseResponse:
    """Helper function to create success responses"""
    return BaseResponse(
        success=True,
        message=message
    )

# =====================================
# VALIDATION HELPERS
# =====================================

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def validate_session_id(session_id: str) -> str:
    """Validate session ID format"""
    if not session_id.startswith('session_'):
        raise ValidationError("Session ID muss mit 'session_' beginnen", "session_id")
    if len(session_id) < 10:
        raise ValidationError("Session ID zu kurz", "session_id")
    return session_id

def validate_project_name(name: str) -> str:
    """Validate project name"""
    name = name.strip()
    if not name:
        raise ValidationError("Projektname darf nicht leer sein", "name")
    if len(name) > 100:
        raise ValidationError("Projektname zu lang (max 100 Zeichen)", "name")
    # Verbiete gefährliche Zeichen
    forbidden_chars = ['<', '>', '"', "'", '&', '/']
    if any(char in name for char in forbidden_chars):
        raise ValidationError("Projektname enthält ungültige Zeichen", "name")
    return name

def validate_code_length(code: str, max_length: int = 50000) -> str:
    """Validate code length"""
    if len(code) > max_length:
        raise ValidationError(f"Code zu lang (max {max_length} Zeichen)", "code")
    return code