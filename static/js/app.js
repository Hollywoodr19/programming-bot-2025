// Programming Bot 2025 - Refactored Frontend Logic
console.log('Programming Bot 2025 Frontend loading...');

// =====================================
// 1. CONFIG & STATE
// =====================================
const config = {
    apiEndpoints: {
        chat: '/api/chat',
        projects: '/api/projects',
        codeReview: '/api/code-review',
        resumeSession: '/api/resume-session',
        createSession: '/api/create-session',
        smartSuggestions: '/api/smart-suggestions',
    },
    selectors: {
        chatMessages: '#chat-messages',
        chatInput: '#chat-input',
        projectsList: '#projects-list',
        codeAnalysisResult: '#analysis-result',
        sessionRecoveryModal: '#session-recovery-modal',
        notificationArea: '#notification-area',
        // Add other selectors here
    }
};

const state = {
    currentSessionId: null,
};

// =====================================
// 2. API ABSTRACTION LAYER
// =====================================
const api = {
    /**
     * Generic API request handler
     * @param {string} endpoint The API endpoint to call.
     * @param {object} options The options for the fetch request.
     * @returns {Promise<object>} The JSON response from the server.
     */
    async request(endpoint, options = {}) {
        const defaultHeaders = { 'Content-Type': 'application/json' };
        const config = {
            ...options,
            headers: { ...defaultHeaders, ...options.headers },
        };

        try {
            const response = await fetch(endpoint, config);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unbekannter Serverfehler' }));
                throw new Error(errorData.error || `HTTP-Status: ${response.status}`);
            }
            return response.json();
        } catch (error) {
            console.error(`API-Fehler am Endpunkt ${endpoint}:`, error);
            ui.showNotification(`Verbindungsfehler: ${error.message}`, 'error');
            throw error; // Re-throw to allow caller to handle it
        }
    },

    postChat: (message, mode) => api.request(config.apiEndpoints.chat, {
        method: 'POST',
        body: JSON.stringify({ message, mode }),
    }),

    getProjects: () => api.request(config.apiEndpoints.projects, { credentials: 'include' }),

    createProject: (name, description, language) => api.request(config.apiEndpoints.projects, {
        method: 'POST',
        body: JSON.stringify({ name, description, language }),
    }),

    postCodeReview: (code, language) => api.request(config.apiEndpoints.codeReview, {
        method: 'POST',
        body: JSON.stringify({ code, language }),
    }),

    resumeSession: (sessionId) => api.request(config.apiEndpoints.resumeSession, {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId })
    }),
};


// =====================================
// 3. UI MANIPULATION
// =====================================
const ui = {
    /**
     * Creates a DOM element with given tag, classes, and content.
     * @param {string} tag - The HTML tag for the element.
     * @param {string|string[]} classes - A string or array of strings for CSS classes.
     * @param {string} [innerHTML] - Optional inner HTML content.
     * @returns {HTMLElement} The created DOM element.
     */
    createElement(tag, classes = [], innerHTML = '') {
        const el = document.createElement(tag);
        if (Array.isArray(classes)) {
            el.classList.add(...classes);
        } else if (classes) {
            el.classList.add(classes);
        }
        if (innerHTML) {
            // Use textContent for security unless HTML is required. For messages, we trust the source or escape it.
            el.innerHTML = innerHTML;
        }
        return el;
    },

    addMessage(content, type, isHtml = true) {
        const chatMessages = document.querySelector(config.selectors.chatMessages);
        const messageWrapper = ui.createElement('div', ['message', type]);
        const messageBubble = ui.createElement('div', 'message-bubble');

        if (isHtml) {
            messageBubble.innerHTML = content;
        } else {
            messageBubble.textContent = content;
        }

        messageWrapper.appendChild(messageBubble);
        chatMessages.appendChild(messageWrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageWrapper;
    },

    showTypingIndicator() {
        return this.addMessage('<div class="loading-spinner"></div>', 'bot');
    },

    clearProjectsList() {
        document.querySelector(config.selectors.projectsList).innerHTML = '';
    },

    renderProjects(projects) {
        this.clearProjectsList();
        const projectsList = document.querySelector(config.selectors.projectsList);

        if (projects.length === 0) {
            projectsList.innerHTML = '<p class="empty-list-info">Noch keine Projekte erstellt.</p>';
            return;
        }

        projects.forEach(project => {
            const card = this.createProjectCard(project);
            projectsList.appendChild(card);
        });
    },

    createProjectCard(project) {
        const createdDate = new Date(project.created_at).toLocaleDateString('de-DE');
        const card = ui.createElement('div', 'project-card');

        card.innerHTML = `
            <h4>${helpers.escapeHtml(project.name)}</h4>
            <p>${helpers.escapeHtml(project.description || 'Keine Beschreibung')}</p>
            <div class="project-card-footer">
                <small>${project.language} • Erstellt: ${createdDate}</small>
                <button class="btn btn-secondary btn-small" data-project-id="${project.id}">Öffnen</button>
            </div>
        `;

        card.querySelector('button').addEventListener('click', () => handlers.openProject(project.id));
        return card;
    },

    showNotification(message, type = 'info') { // type can be 'info', 'success', 'error'
        const notificationArea = document.querySelector(config.selectors.notificationArea);
        const notification = ui.createElement('div', ['notification', `notification-${type}`], message);

        notificationArea.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }
};

// =====================================
// 4. EVENT HANDLERS & LOGIC
// =====================================
const handlers = {
    async sendMessage() {
        const chatInput = document.querySelector(config.selectors.chatInput);
        const message = chatInput.value.trim();
        if (!message) return;

        ui.addMessage(helpers.escapeHtml(message), 'user', false);
        chatInput.value = '';

        const typingIndicator = ui.showTypingIndicator();

        try {
            const result = await api.postChat(message, 'programming'); // Mode can be dynamic
            if (result.session_id) {
                state.currentSessionId = result.session_id;
            }
            // Add bot response, assuming it's safe HTML or contains Markdown to be parsed
            ui.addMessage(result.response, 'bot');
        } catch (error) {
            // Error is already logged and notified by the api layer
        } finally {
            typingIndicator.remove();
        }
    },

    async loadProjects() {
        try {
            const result = await api.getProjects();
            if (result.success) {
                ui.renderProjects(result.projects);
            }
        } catch (error) {
            document.querySelector(config.selectors.projectsList).innerHTML = '<p class="error-message">Fehler beim Laden der Projekte.</p>';
        }
    },

    openProject(projectId) {
        console.log('Opening project:', projectId);
        // Implement project opening logic here
        ui.showNotification(`Feature "Projekt öffnen" (ID: ${projectId}) ist in Arbeit.`, 'info');
    },

    async handleSessionResume(sessionId) {
        try {
            const result = await api.resumeSession(sessionId);
            if (result.success) {
                document.querySelector(config.selectors.sessionRecoveryModal).style.display = 'none';
                ui.showNotification(result.message, 'success');
                // Logic to load conversation history etc.
            }
        } catch(error) {
            // Error handled by API layer
        }
    }
};

// =====================================
// 5. HELPERS
// =====================================
const helpers = {
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
};

// =====================================
// 6. INITIALIZATION
// =====================================
function init() {
    // Attach event listeners programmatically
    const sendButton = document.getElementById('send-button'); // Assuming you have a button with this ID
    const chatInput = document.querySelector(config.selectors.chatInput);

    if (sendButton) {
        sendButton.addEventListener('click', handlers.sendMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handlers.sendMessage();
            }
        });
    }

    // Load initial data
    handlers.loadProjects();
    // Check for session recovery, etc.
}

// Run initialization once the DOM is fully loaded
document.addEventListener('DOMContentLoaded', init);