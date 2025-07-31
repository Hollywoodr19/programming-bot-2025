/**
 * web/static/js/core.js - Basis JavaScript für alle Themes
 * REGEL: Nur grundlegende Funktionen, keine Theme-spezifischen Sachen!
 */

// ===========================
// GLOBALE VARIABLEN
// ===========================

window.BotCore = {
    config: {
        apiBase: '/api',
        statsUpdateInterval: 30000, // 30 Sekunden
        theme: window.THEME || 'modern'
    },
    state: {
        isProcessing: false,
        lastMessageId: null,
        websocket: null,
        statsInterval: null
    }
};

// ===========================
// API-FUNKTIONEN
// ===========================

const API = {
    /**
     * Chat-Nachricht senden
     */
    async sendMessage(message, projectId = null) {
        const response = await fetch(`${BotCore.config.apiBase}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                project_id: projectId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    },

    /**
     * Code-Review anfordern
     */
    async reviewCode(code, language = 'python') {
        const response = await fetch(`${BotCore.config.apiBase}/code-review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: language
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    },

    /**
     * Projekt erstellen
     */
    async createProject(name, description = '', language = 'python') {
        const response = await fetch(`${BotCore.config.apiBase}/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                description: description,
                language: language
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    },

    /**
     * System-Metriken abrufen
     */
    async getMetrics() {
        const response = await fetch(`${BotCore.config.apiBase}/metrics`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    },

    /**
     * Dashboard-Stats abrufen
     */
    async getDashboardStats() {
        const response = await fetch(`${BotCore.config.apiBase}/dashboard/stats`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }
};

// ===========================
// CHAT-FUNKTIONEN
// ===========================

const Chat = {
    /**
     * Nachricht zur UI hinzufügen
     */
    addMessage(message, type = 'bot', timestamp = null) {
        const container = document.getElementById('chat-messages') ||
                         document.querySelector('.chat-messages');

        if (!container) {
            console.warn('Chat-Container nicht gefunden');
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble ${type}`;

        // Message-Content formatieren
        bubbleDiv.innerHTML = this.formatMessage(message);

        // Timestamp hinzufügen
        if (timestamp) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-timestamp';
            timeDiv.textContent = new Date(timestamp).toLocaleTimeString();
            bubbleDiv.appendChild(timeDiv);
        }

        messageDiv.appendChild(bubbleDiv);
        container.appendChild(messageDiv);

        // Auto-Scroll
        this.scrollToBottom(container);

        // Animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';

        requestAnimationFrame(() => {
            messageDiv.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        });
    },

    /**
     * Message formatieren (einfaches Markdown)
     */
    formatMessage(message) {
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    },

    /**
     * Smooth Scroll zum Ende
     */
    scrollToBottom(container) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    },

    /**
     * Nachricht senden (Haupt-Funktion)
     */
    async sendMessage() {
        const input = document.getElementById('user-input') ||
                     document.querySelector('.chat-input');
        const sendButton = document.getElementById('send-button') ||
                          document.querySelector('.btn');

        if (!input || BotCore.state.isProcessing) return;

        const message = input.value.trim();
        if (!message) return;

        try {
            // Processing-State setzen
            BotCore.state.isProcessing = true;
            if (sendButton) {
                sendButton.disabled = true;
                sendButton.innerHTML = '<div class="loading-spinner"></div>';
            }

            // User-Message zur UI hinzufügen
            this.addMessage(message, 'user');

            // API-Call
            const response = await API.sendMessage(message);

            // Bot-Response zur UI hinzufügen
            this.addMessage(response.response, 'bot', response.timestamp);

            // Input zurücksetzen
            input.value = '';

            // Stats aktualisieren
            Stats.update();

        } catch (error) {
            console.error('Chat-Fehler:', error);
            this.addMessage(`❌ Fehler: ${error.message}`, 'bot');
        } finally {
            // Processing-State zurücksetzen
            BotCore.state.isProcessing = false;
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.innerHTML = '📤 Senden';
            }

            // Focus zurück auf Input
            input.focus();
        }
    }
};

// ===========================
// STATS-FUNKTIONEN
// ===========================

const Stats = {
    /**
     * Stats laden und anzeigen
     */
    async update() {
        try {
            const stats = await API.getMetrics();
            this.display(stats);
        } catch (error) {
            console.warn('Stats-Update fehlgeschlagen:', error);
        }
    },

    /**
     * Stats in UI anzeigen
     */
    display(stats) {
        const elements = {
            'messages_processed': stats.messages_processed || 0,
            'code_reviews_completed': stats.code_reviews_completed || 0,
            'projects_created': stats.projects_created || 0,
            'uptime_hours': (stats.uptime_hours || 0).toFixed(1) + 'h',
            'features_enabled': stats.features_enabled || 0
        };

        // Update einzelne Stat-Elemente
        Object.entries(elements).forEach(([key, value]) => {
            const element = document.getElementById(`stat-${key}`) ||
                           document.querySelector(`[data-stat="${key}"]`);

            if (element) {
                this.animateValue(element, element.textContent, value);
            }
        });

        // Stats-Grid aktualisieren (Fallback)
        const statsGrid = document.getElementById('stats');
        if (statsGrid && !statsGrid.querySelector('.stat')) {
            statsGrid.innerHTML = `
                <div class="stat">💬 ${elements.messages_processed} Nachrichten</div>
                <div class="stat">🔍 ${elements.code_reviews_completed} Reviews</div>
                <div class="stat">📁 ${elements.projects_created} Projekte</div>
                <div class="stat">⏱️ ${elements.uptime_hours} Laufzeit</div>
                <div class="stat">✨ ${elements.features_enabled} Features</div>
            `;
        }
    },

    /**
     * Animierte Wert-Änderung
     */
    animateValue(element, from, to) {
        const fromNum = parseFloat(from) || 0;
        const toNum = parseFloat(to) || 0;

        if (fromNum === toNum) return;

        const duration = 1000;
        const steps = 20;
        const stepValue = (toNum - fromNum) / steps;
        const stepDuration = duration / steps;

        let currentValue = fromNum;
        let step = 0;

        const interval = setInterval(() => {
            step++;
            currentValue += stepValue;

            if (step >= steps) {
                element.textContent = to;
                clearInterval(interval);
            } else {
                const displayValue = typeof to === 'string' && to.includes('h')
                    ? currentValue.toFixed(1) + 'h'
                    : Math.round(currentValue);
                element.textContent = displayValue;
            }
        }, stepDuration);
    },

    /**
     * Auto-Update starten
     */
    startAutoUpdate() {
        this.update(); // Sofort laden

        BotCore.state.statsInterval = setInterval(() => {
            this.update();
        }, BotCore.config.statsUpdateInterval);
    },

    /**
     * Auto-Update stoppen
     */
    stopAutoUpdate() {
        if (BotCore.state.statsInterval) {
            clearInterval(BotCore.state.statsInterval);
            BotCore.state.statsInterval = null;
        }
    }
};

// ===========================
// UTILITY-FUNKTIONEN
// ===========================

const Utils = {
    /**
     * Theme-Klasse am Body setzen
     */
    setTheme(themeName) {
        document.body.className = `theme-${themeName}`;
        BotCore.config.theme = themeName;
    },

    /**
     * Element-Sichtbarkeit prüfen
     */
    isElementVisible(element) {
        return element && element.offsetParent !== null;
    },

    /**
     * Debounce-Funktion
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * Local Storage Helper
     */
    storage: {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                return defaultValue;
            }
        },

        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                return false;
            }
        }
    }
};

// ===========================
// EVENT-LISTENERS
// ===========================

document.addEventListener('DOMContentLoaded', () => {
    console.log(`🚀 Bot Core geladen - Theme: ${BotCore.config.theme}`);

    // Theme setzen
    Utils.setTheme(BotCore.config.theme);

    // Stats-Auto-Update starten
    Stats.startAutoUpdate();

    // Enter-Taste für Chat
    const chatInput = document.getElementById('user-input') ||
                     document.querySelector('.chat-input');

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                Chat.sendMessage();
            }
        });
    }

    // Send-Button
    const sendButton = document.getElementById('send-button') ||
                      document.querySelector('[onclick*="sendMessage"]');

    if (sendButton) {
        sendButton.addEventListener('click', Chat.sendMessage);
    }
});

// Cleanup beim Verlassen
window.addEventListener('beforeunload', () => {
    Stats.stopAutoUpdate();
    if (BotCore.state.websocket) {
        BotCore.state.websocket.close();
    }
});

// ===========================
// GLOBALE FUNKTIONEN (für Legacy-Templates)
// ===========================

// Für Kompatibilität mit bestehenden Templates
window.sendMessage = Chat.sendMessage.bind(Chat);
window.loadStats = Stats.update.bind(Stats);

// API global verfügbar machen
window.API = API;
window.Chat = Chat;
window.Stats = Stats;
window.Utils = Utils;