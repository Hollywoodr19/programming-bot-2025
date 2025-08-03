/**
 * web/static/js/core.js - Refactored Core JavaScript
 * Beschreibung: Modulare und robuste Basis-Logik für die Bot-Anwendung.
 * Kapselt die gesamte Logik in einem IIFE, um den globalen Scope zu schützen.
 */

(function() {
    'use strict';

    // ===========================
    // 1. MODULE CONFIG & STATE
    // ===========================

    const config = {
        apiBase: '/api',
        statsUpdateInterval: 30000, // 30 Sekunden
        theme: window.THEME || 'modern',
        selectors: {
            chatContainer: '.chat-messages',
            chatInput: '.chat-input',
            sendButton: '.btn-primary[onclick*="sendMessage"]', // Anpassbarer Selektor
            statsContainer: '#stats-grid',
            statValue: '[data-stat]',
        }
    };

    const state = {
        isProcessing: false,
        statsIntervalId: null,
    };

    // Cache for frequently used DOM elements
    const DOM = {};

    // ===========================
    // 2. API ABSTRACTION
    // ===========================

    const API = {
        /**
         * Private helper for all API requests. Reduces boilerplate.
         * @param {string} endpoint - The API endpoint to call.
         * @param {object} options - Fetch options (method, body, etc.).
         * @returns {Promise<any>} - The parsed JSON response.
         */
        async _request(endpoint, options = {}) {
            const url = `${config.apiBase}${endpoint}`;
            const defaultOptions = {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            };

            const fetchOptions = { ...defaultOptions, ...options };

            if (fetchOptions.body) {
                fetchOptions.body = JSON.stringify(fetchOptions.body);
            }

            try {
                const response = await fetch(url, fetchOptions);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ message: response.statusText }));
                    throw new Error(errorData.message || `HTTP Error ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                console.error(`API Request Failed: ${error.message}`);
                // Re-throw the error to be handled by the caller
                throw error;
            }
        },

        sendMessage: (message, projectId = null) =>
            API._request('/chat', { method: 'POST', body: { message, project_id: projectId } }),

        reviewCode: (code, language = 'python') =>
            API._request('/code-review', { method: 'POST', body: { code, language } }),

        getMetrics: () => API._request('/metrics'),
    };

    // ===========================
    // 3. UI & CHAT MODULE
    // ===========================

    const Chat = {
        /**
         * Adds a message to the chat UI.
         * @param {string} content - The message content (HTML).
         * @param {'user'|'bot'} type - The type of the message.
         */
        addMessage(content, type) {
            if (!DOM.chatContainer) return;

            const messageEl = document.createElement('div');
            messageEl.className = `message message--${type}`;

            const bubbleEl = document.createElement('div');
            bubbleEl.className = 'message-bubble';
            bubbleEl.innerHTML = this._formatMessage(content);

            messageEl.appendChild(bubbleEl);
            DOM.chatContainer.appendChild(messageEl);

            // Trigger animation via CSS class
            requestAnimationFrame(() => messageEl.classList.add('message--visible'));

            this.scrollToBottom();
        },

        /**
         * Safely formats message content.
         * @param {string} text - The raw message text.
         * @returns {string} - HTML formatted string.
         */
        _formatMessage(text) {
            // Basic escaping to prevent simple HTML injection
            const escapedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

            // Simple Markdown to HTML
            return escapedText
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        },

        scrollToBottom() {
            if (DOM.chatContainer) {
                DOM.chatContainer.scrollTo({ top: DOM.chatContainer.scrollHeight, behavior: 'smooth' });
            }
        },

        setProcessing(isProcessing) {
            state.isProcessing = isProcessing;
            if (DOM.sendButton) {
                DOM.sendButton.disabled = isProcessing;
                DOM.sendButton.innerHTML = isProcessing ? '<div class="loading-spinner"></div>' : 'Senden';
            }
            if(DOM.chatInput) {
                DOM.chatInput.disabled = isProcessing;
            }
        }
    };

    // ===========================
    // 4. HANDLERS & INITIALIZATION
    // ===========================

    const App = {
        /**
         * Handles the primary action of sending a message.
         */
        async handleSendMessage() {
            if (state.isProcessing || !DOM.chatInput) return;
            const message = DOM.chatInput.value.trim();
            if (!message) return;

            Chat.setProcessing(true);
            Chat.addMessage(message, 'user');
            DOM.chatInput.value = '';

            try {
                const response = await API.sendMessage(message);
                Chat.addMessage(response.response, 'bot');
            } catch (error) {
                Chat.addMessage(`❌ Ein Fehler ist aufgetreten: ${error.message}`, 'bot');
            } finally {
                Chat.setProcessing(false);
                DOM.chatInput.focus();
            }
        },

        /**
         * Caches essential DOM elements for performance.
         */
        _cacheDomElements() {
            DOM.chatContainer = document.querySelector(config.selectors.chatContainer);
            DOM.chatInput = document.querySelector(config.selectors.chatInput);
            DOM.sendButton = document.querySelector(config.selectors.sendButton);
            // Cache more elements as needed
        },

        /**
         * Binds all necessary event listeners.
         */
        _bindEvents() {
            // Send message on button click
            if (DOM.sendButton) {
                DOM.sendButton.addEventListener('click', () => this.handleSendMessage());
            }

            // Send message on Enter key press
            if (DOM.chatInput) {
                DOM.chatInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.handleSendMessage();
                    }
                });
            }

            // Cleanup on page leave
            window.addEventListener('beforeunload', () => {
                if (state.statsIntervalId) clearInterval(state.statsIntervalId);
            });
        },

        /**
         * Initializes the application.
         */
        init() {
            console.log(`🚀 Core Bot Logic Initialized. Theme: ${config.theme}`);
            this._cacheDomElements();
            this._bindEvents();

            // Initial actions
            document.body.className = `theme-${config.theme}`;
            // Stats.startAutoUpdate(); // If stats module is present
        }
    };

    // ===========================
    // 5. BOOTSTRAP
    // ===========================

    // Expose a public API if needed for legacy compatibility or external calls
    window.BotCore = {
        sendMessage: App.handleSendMessage.bind(App),
        // Expose other functions as needed
    };

    // Start the application once the DOM is ready
    document.addEventListener('DOMContentLoaded', () => App.init());

})();