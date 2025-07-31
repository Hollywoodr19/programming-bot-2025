// Programming Bot 2025 - Enhanced JavaScript mit Session Recovery
console.log('Programming Bot 2025 Frontend loading...');

// =====================================
// SESSION RECOVERY FUNCTIONS
// =====================================

async function resumeSession(sessionId) {
    console.log('Resuming session:', sessionId);

    try {
        const response = await fetch('/api/resume-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId })
        });

        const result = await response.json();

        if (result.success) {
            // Hide recovery modal
            document.getElementById('session-recovery-modal').style.display = 'none';

            // Show success message
            addMessageToChat('🎉 ' + result.message, 'bot-message');

            // Load conversation history if available
            if (result.session_data && result.session_data.conversation_history) {
                loadConversationHistory(result.session_data.conversation_history);
            }

            // Load smart suggestions
            loadSmartSuggestions();

        } else {
            alert('Fehler beim Session-Resume: ' + (result.error || 'Unbekannter Fehler'));
        }

    } catch (error) {
        console.error('Resume session error:', error);
        alert('Verbindungsfehler beim Session-Resume');
    }
}

async function startNewProject() {
    console.log('Starting new project');

    // Hide recovery modal
    document.getElementById('session-recovery-modal').style.display = 'none';

    // Show project creation tab
    showTab('projects');

    // Focus on project name input
    setTimeout(() => {
        const projectNameInput = document.getElementById('project-name');
        if (projectNameInput) {
            projectNameInput.focus();
        }
    }, 300);
}

function skipRecovery() {
    console.log('Skipping session recovery');

    // Hide recovery modal
    document.getElementById('session-recovery-modal').style.display = 'none';

    // Show welcome message
    addMessageToChat('Willkommen zurück! Wie kann ich dir heute helfen?', 'bot-message');
}

async function loadSmartSuggestions() {
    try {
        const response = await fetch('/api/smart-suggestions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success && result.suggestions.length > 0) {
            displaySmartSuggestions(result.suggestions);
        }

    } catch (error) {
        console.error('Smart suggestions error:', error);
    }
}

function displaySmartSuggestions(suggestions) {
    const chatMessages = document.getElementById('chat-messages');

    let suggestionsHtml = '<div class="message bot-message" style="background: rgba(0, 212, 170, 0.2);">';
    suggestionsHtml += '<h4>💡 Smart Suggestions:</h4>';

    suggestions.forEach(suggestion => {
        const priorityIcon = suggestion.priority === 1 ? '🔥' : suggestion.priority === 2 ? '⭐' : '💡';
        suggestionsHtml += `
            <div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                <strong>${priorityIcon} ${suggestion.title}</strong><br>
                <small style="opacity: 0.8;">${suggestion.description}</small>
            </div>
        `;
    });

    suggestionsHtml += '</div>';
    chatMessages.innerHTML += suggestionsHtml;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function loadConversationHistory(history) {
    const chatMessages = document.getElementById('chat-messages');

    // Clear current messages except welcome
    const welcomeMessage = chatMessages.querySelector('.message');
    chatMessages.innerHTML = '';
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }

    // Add history messages
    history.forEach(msg => {
        if (msg.type === 'user') {
            addMessageToChat(msg.content, 'user-message');
        } else if (msg.type === 'assistant') {
            addMessageToChat(msg.content, 'bot-message');
        }
    });

    // Add separator
    addMessageToChat('--- Session wiederhergestellt ---', 'bot-message', 'font-style: italic; opacity: 0.7;');
}

// =====================================
// EXISTING FUNCTIONS (Enhanced)
// =====================================

// Global variables
let currentSessionId = null;

// Tab Management
function showTab(tabName) {
    console.log('showTab called with:', tabName);

    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.add('hidden'));

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));

    // Show selected tab content
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }

    // Add active class to clicked button
    const activeButton = [...tabButtons].find(btn =>
        btn.textContent.toLowerCase().includes(tabName.replace('-', ' '))
    );
    if (activeButton) {
        activeButton.classList.add('active');
    }

    // Load data for specific tabs
    if (tabName === 'dashboard') {
        loadDashboardMetrics();
    } else if (tabName === 'projects') {
        loadProjectsList();
    }
}

// Enhanced Chat Functions
async function sendMessage() {
    console.log('sendMessage called');

    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat(message, 'user-message');
    chatInput.value = '';

    // Show typing indicator
    const typingId = addMessageToChat('🤖 Tippt...', 'bot-message');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                mode: getMode()
            })
        });

        const result = await response.json();

        // Remove typing indicator
        removeMessage(typingId);

        if (result.success) {
            // Store session ID if provided
            if (result.session_id) {
                currentSessionId = result.session_id;
            }

            // Add bot response
            addMessageToChat(escapeHtml(result.response), 'bot-message');
        } else {
            addMessageToChat('❌ Fehler: ' + (result.error || 'Unbekannter Fehler'), 'bot-message');
        }

    } catch (error) {
        removeMessage(typingId);
        console.error('Chat error:', error);
        addMessageToChat('❌ Verbindungsfehler', 'bot-message');
    }
}

function addMessageToChat(message, className, extraStyle = '') {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

    messageDiv.id = messageId;
    messageDiv.className = `message ${className}`;
    if (extraStyle) {
        messageDiv.style.cssText = extraStyle;
    }
    messageDiv.innerHTML = message;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageId;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

function getMode() {
    // Detect mode from page context
    const modeIndicator = document.querySelector('[style*="Chat-Only Modus"]');
    return modeIndicator ? 'chat_only' : 'programming';
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Quick Reply Functions
function sendQuickReply(message) {
    const chatInput = document.getElementById('chat-input');
    chatInput.value = message;
    sendMessage();
}

// Enhanced Project Functions
async function createNewProject() {
    console.log('createNewProject called');

    const name = document.getElementById('project-name').value.trim();
    const description = document.getElementById('project-description').value.trim();
    const language = document.getElementById('project-language').value;

    if (!name) {
        alert('Bitte gib einen Projektnamen ein!');
        return;
    }

    try {
        // Try session manager first
        const sessionResponse = await fetch('/api/create-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_name: name,
                project_type: language
            })
        });

        const sessionResult = await sessionResponse.json();

        if (sessionResult.success) {
            // Session created successfully
            currentSessionId = sessionResult.session_id;
            alert(sessionResult.message);

            // Clear form
            document.getElementById('project-name').value = '';
            document.getElementById('project-description').value = '';

            // Switch to chat tab
            showTab('chat');
            addMessageToChat(`✨ Projekt "${name}" erstellt! Lass uns loslegen!`, 'bot-message');

            // Load projects list
            loadProjectsList();
            return;
        }

        // Fallback to regular project creation
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                description: description,
                language: language
            })
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);

            // Clear form
            document.getElementById('project-name').value = '';
            document.getElementById('project-description').value = '';

            // Reload projects list
            loadProjectsList();
        } else {
            alert('Fehler: ' + (result.error || 'Unbekannter Fehler'));
        }

    } catch (error) {
        console.error('Create project error:', error);
        alert('Verbindungsfehler beim Projekt erstellen');
    }
}

async function loadProjectsList() {
    try {
        const response = await fetch('/api/projects', {
            credentials: 'include'
        });

        const result = await response.json();

        const projectsList = document.getElementById('projects-list');

        if (result.success && result.projects.length > 0) {
            let projectsHtml = '';
            result.projects.forEach(project => {
                const createdDate = new Date(project.created_at).toLocaleDateString('de-DE');
                projectsHtml += `
                    <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                        <h4 style="margin-bottom: 8px;">${escapeHtml(project.name)}</h4>
                        <p style="margin-bottom: 8px; opacity: 0.8;">${escapeHtml(project.description || 'Keine Beschreibung')}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <small style="opacity: 0.6;">
                                ${project.language} • Erstellt: ${createdDate}
                            </small>
                            <button onclick="openProject('${project.id}')" 
                                    style="background: #00d4aa; color: white; border: none; padding: 5px 15px; border-radius: 5px; cursor: pointer;">
                                Öffnen
                            </button>
                        </div>
                    </div>
                `;
            });
            projectsList.innerHTML = projectsHtml;
        } else {
            projectsList.innerHTML = '<p style="opacity: 0.7; font-style: italic;">Noch keine Projekte erstellt. Erstelle dein erstes Projekt oben! 👆</p>';
        }

    } catch (error) {
        console.error('Load projects error:', error);
        document.getElementById('projects-list').innerHTML = '<p style="color: #ff6b6b;">❌ Fehler beim Laden der Projekte</p>';
    }
}

function openProject(projectId) {
    console.log('Opening project:', projectId);
    // TODO: Implement project opening logic
    alert('Projekt öffnen Feature kommt bald!');
}

// Enhanced Code Review Functions
async function analyzeCode() {
    console.log('analyzeCode called');

    const code = document.getElementById('code-input').value.trim();
    const language = document.getElementById('review-language').value;

    if (!code) {
        alert('Bitte füge Code zum Analysieren ein!');
        return;
    }

    const resultDiv = document.getElementById('analysis-result');
    resultDiv.innerHTML = '<div style="color: #00d4aa;">🔍 Analysiere Code...</div>';

    try {
        const response = await fetch('/api/code-review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                language: language
            })
        });

        const result = await response.json();

        if (result.success) {
            const score = result.quality_score || result.score || 75;
            const scoreColor = score >= 90 ? '#00d4aa' : score >= 70 ? '#ffd93d' : '#ff6b6b';

            let analysisHtml = `
                <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-top: 20px;">
                    <h4 style="margin-bottom: 15px;">📊 Code-Analyse Ergebnis</h4>
                    <div style="margin-bottom: 15px;">
                        <strong>Qualitäts-Score: 
                            <span style="color: ${scoreColor}; font-size: 1.2em;">${score}/100</span>
                        </strong>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <strong>Analyse:</strong><br>
                        <p style="margin-top: 8px;">${escapeHtml(result.analysis || 'Code-Analyse abgeschlossen.')}</p>
                    </div>
            `;

            if (result.suggestions && result.suggestions.length > 0) {
                analysisHtml += '<div style="margin-bottom: 15px;"><strong>💡 Verbesserungsvorschläge:</strong><ul style="margin-top: 8px;">';
                result.suggestions.forEach(suggestion => {
                    analysisHtml += `<li style="margin-bottom: 5px;">${escapeHtml(suggestion)}</li>`;
                });
                analysisHtml += '</ul></div>';
            }

            analysisHtml += '</div>';
            resultDiv.innerHTML = analysisHtml;

        } else {
            resultDiv.innerHTML = '<div style="color: #ff6b6b;">❌ Fehler bei der Code-Analyse: ' + (result.error || 'Unbekannter Fehler') + '</div>';
        }

    } catch (error) {
        console.error('Code analysis error:', error);
        resultDiv.innerHTML = '<div style="color: #ff6b6b;">❌ Verbindungsfehler bei der Code-Analyse</div>';
    }
}

// Dashboard Functions
async function loadDashboardMetrics() {
    try {
        const response = await fetch('/api/metrics', {
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success || result.user_messages !== undefined) {
            // Update metrics display
            const messageCount = result.user_messages || result.messages_today || 0;
            const projectCount = result.user_projects || result.projects_count || 0;
            const apiStatus = result.api_status || 'Unknown';

            document.getElementById('message-count').textContent = messageCount;
            document.getElementById('project-count').textContent = projectCount;

            // Color-code API status
            const statusElement = document.getElementById('api-status');
            statusElement.textContent = apiStatus;

            if (apiStatus.includes('Claude API') || apiStatus.includes('Connected')) {
                statusElement.style.color = '#00d4aa';
            } else if (apiStatus.includes('Fallback')) {
                statusElement.style.color = '#ffd93d';
            } else {
                statusElement.style.color = '#ff6b6b';
            }

        } else {
            // Error state
            document.getElementById('message-count').textContent = '?';
            document.getElementById('project-count').textContent = '?';
            document.getElementById('api-status').textContent = 'Error';
            document.getElementById('api-status').style.color = '#ff6b6b';
        }

    } catch (error) {
        console.error('Dashboard metrics error:', error);
        document.getElementById('message-count').textContent = 'Error';
        document.getElementById('project-count').textContent = 'Error';
        document.getElementById('api-status').textContent = 'Offline';
        document.getElementById('api-status').style.color = '#ff6b6b';
    }
}

// Keyboard Event Handlers
function setupKeyboardHandlers() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
        console.log('Chat input keyboard handler attached');
    }

    // Global keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Enter for quick send
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            sendMessage();
        }

        // Escape to close modals
        if (event.key === 'Escape') {
            const modal = document.getElementById('session-recovery-modal');
            if (modal && modal.style.display !== 'none') {
                skipRecovery();
            }
        }
    });
}

// Global Error Handler
window.addEventListener('error', function(event) {
    console.error('Global error caught:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
});

// Unhandled Promise Rejection Handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// Mode Detection
function detectMode() {
    const modeIndicator = document.querySelector('[style*="Chat-Only Modus"]');
    const mode = modeIndicator ? 'chat_only' : 'programming';
    console.log('Programming mode detected:', mode);
    return mode;
}

// Initialize Everything
document.addEventListener('DOMContentLoaded', function() {
    console.log('Programming Bot 2025 Frontend loading...');

    // Setup keyboard handlers
    setupKeyboardHandlers();

    // Detect mode
    const mode = detectMode();

    // Load initial data for active tab
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab) {
        const tabText = activeTab.textContent.toLowerCase();
        if (tabText.includes('dashboard')) {
            loadDashboardMetrics();
        } else if (tabText.includes('projekte')) {
            loadProjectsList();
        }
    }

    // Auto-load session recovery if not shown already
    const recoveryModal = document.getElementById('session-recovery-modal');
    if (!recoveryModal) {
        // Try to load session recovery data via API
        loadSessionRecoveryIfNeeded();
    }

    console.log('Programming Bot 2025 Frontend loaded successfully');
});

// Auto Session Recovery Loader
async function loadSessionRecoveryIfNeeded() {
    try {
        const response = await fetch('/api/session-recovery', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success && result.recovery_data && result.recovery_data.has_sessions) {
            // Create and show recovery modal dynamically
            createSessionRecoveryModal(result.recovery_data);
        }

    } catch (error) {
        console.log('No session recovery needed or error:', error);
    }
}

function createSessionRecoveryModal(recoveryData) {
    // Only create if not already exists
    if (document.getElementById('session-recovery-modal')) {
        return;
    }

    const modal = document.createElement('div');
    modal.id = 'session-recovery-modal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.7); backdrop-filter: blur(10px);
        display: flex; justify-content: center; align-items: center;
        z-index: 1000;
    `;

    let modalContent = `
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px; padding: 40px; max-width: 600px; width: 90%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.2);
            color: white; text-align: center;
        ">
            <h2 style="margin-bottom: 20px;">🧠 Session Recovery</h2>
            <p style="margin-bottom: 30px; opacity: 0.9;">${recoveryData.message}</p>
    `;

    if (recoveryData.single_session) {
        modalContent += `
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                <h3>${recoveryData.session.name}</h3>
                <p><strong>Letzter Fortschritt:</strong> ${recoveryData.session.last_action}</p>
                <p><strong>Zuletzt aktiv:</strong> ${recoveryData.session.last_active}</p>
            </div>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <button onclick="resumeSession('${recoveryData.session.id}')" 
                        style="background: #00d4aa; color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer;">
                    🔄 Session fortsetzen
                </button>
                <button onclick="startNewProject()" 
                        style="background: rgba(255,255,255,0.2); color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer;">
                    ✨ Neues Projekt
                </button>
            </div>
        `;
    } else {
        modalContent += '<div style="max-height: 300px; overflow-y: auto; margin-bottom: 20px;">';
        recoveryData.sessions.forEach(session => {
            modalContent += `
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px; text-align: left;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4>${session.name}</h4>
                            <p style="margin: 5px 0; opacity: 0.8;">${session.last_action}</p>
                            <small style="opacity: 0.7;">${session.last_active}</small>
                        </div>
                        <button onclick="resumeSession('${session.id}')" 
                                style="background: #00d4aa; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                            Fortsetzen
                        </button>
                    </div>
                </div>
            `;
        });
        modalContent += `
            </div>
            <button onclick="startNewProject()" 
                    style="background: rgba(255,255,255,0.2); color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer;">
                ✨ Neues Projekt starten
            </button>
        `;
    }

    modalContent += `
            <div style="margin-top: 20px;">
                <button onclick="skipRecovery()" 
                        style="background: transparent; color: rgba(255,255,255,0.7); border: 1px solid rgba(255,255,255,0.3); padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                    Überspringen
                </button>
            </div>
        </div>
    `;

    modal.innerHTML = modalContent;
    document.body.appendChild(modal);
}