/**
 * Programming Bot 2025 - Main JavaScript
 * Common utilities and functions used across all pages
 */

// Global Application State
window.ProgrammingBot = {
    config: window.APP_CONFIG || {},
    theme: localStorage.getItem('theme') || 'auto',
    user: null,
    csrf_token: null,

    // Initialize application
    init() {
        this.loadConfig();
        this.setupTheme();
        this.setupEventListeners();
        this.setupCSRF();
        this.setupAlerts();
        console.log('🤖 Programming Bot 2025 initialized');
    },

    // Load configuration from window.APP_CONFIG
    loadConfig() {
        if (window.APP_CONFIG) {
            this.config = window.APP_CONFIG;
            this.user = window.APP_CONFIG.user;
            this.csrf_token = window.APP_CONFIG.csrf_token;
        }
    },

    // Setup theme system
    setupTheme() {
        this.applyTheme(this.theme);

        // Listen for system theme changes
        if (this.theme === 'auto') {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (this.theme === 'auto') {
                    document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                }
            });
        }
    },

    // Apply theme
    applyTheme(theme) {
        this.theme = theme;
        localStorage.setItem('theme', theme);

        if (theme === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }

        // Update theme icon if exists
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            themeIcon.textContent = isDark ? '☀️' : '🌙';
        }
    },

    // Setup global event listeners
    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));

        // Handle clicks outside dropdowns
        document.addEventListener('click', this.handleOutsideClick.bind(this));

        // Handle form submissions
        document.addEventListener('submit', this.handleFormSubmit.bind(this));

        // Handle before unload
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    },

    // Setup CSRF protection
    setupCSRF() {
        if (this.csrf_token) {
            // Add CSRF token to all AJAX requests
            const originalFetch = window.fetch;
            window.fetch = function(url, options = {}) {
                if (options.method && options.method.toUpperCase() !== 'GET') {
                    options.headers = {
                        ...options.headers,
                        'X-CSRF-Token': ProgrammingBot.csrf_token
                    };
                }
                return originalFetch.call(this, url, options);
            };
        }
    },

    // Setup alert system
    setupAlerts() {
        // Auto-remove alerts after timeout
        const alerts = document.querySelectorAll('.alert.show');
        alerts.forEach(alert => {
            setTimeout(() => {
                this.hideAlert(alert);
            }, 5000);
        });
    },

    // Handle keyboard shortcuts
    handleKeyboard(e) {
        // Global shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case '/':
                    e.preventDefault();
                    this.focusSearch();
                    break;
                case 'k':
                    e.preventDefault();
                    this.showShortcuts();
                    break;
            }
        }

        // Escape key
        if (e.key === 'Escape') {
            this.closeModals();
            this.hideAlert();
        }
    },

    // Handle clicks outside elements
    handleOutsideClick(e) {
        // Close dropdowns
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target) && !dropdown.previousElementSibling?.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    },

    // Handle form submissions
    handleFormSubmit(e) {
        const form = e.target;
        if (form.dataset.ajax !== 'false') {
            // Prevent double submission
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && submitBtn.disabled) {
                e.preventDefault();
                return;
            }
        }
    },

    // Handle before unload
    handleBeforeUnload(e) {
        // Check for unsaved changes
        if (this.hasUnsavedChanges && this.hasUnsavedChanges()) {
            e.preventDefault();
            e.returnValue = 'Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?';
            return e.returnValue;
        }
    }
};

// Alert System
window.AlertSystem = {
    container: null,

    init() {
        this.container = document.getElementById('alert-container') || this.createContainer();
    },

    createContainer() {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.className = 'alert-container';
        container.setAttribute('role', 'alert');
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
        return container;
    },

    show(message, type = 'info', duration = 5000) {
        if (!this.container) this.init();

        const alert = this.createAlert(message, type);
        this.container.appendChild(alert);

        // Trigger animation
        setTimeout(() => alert.classList.add('show'), 10);

        // Auto-remove
        if (duration > 0) {
            setTimeout(() => this.hide(alert), duration);
        }

        return alert;
    },

    createAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.setAttribute('role', 'alert');

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        alert.innerHTML = `
            <span class="alert-icon">${icons[type] || icons.info}</span>
            <span class="alert-message">${this.escapeHtml(message)}</span>
            <button type="button" class="alert-close" onclick="AlertSystem.hide(this.parentElement)" aria-label="Alert schließen">×</button>
        `;

        return alert;
    },

    hide(alert) {
        if (!alert) return;

        alert.classList.remove('show');
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 300);
    },

    hideAll() {
        const alerts = this.container?.querySelectorAll('.alert') || [];
        alerts.forEach(alert => this.hide(alert));
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Loading System
window.LoadingSystem = {
    overlay: null,

    show(message = 'Loading...') {
        this.hide(); // Remove any existing loader

        this.overlay = document.createElement('div');
        this.overlay.id = 'loading-indicator';
        this.overlay.className = 'loading-indicator';
        this.overlay.innerHTML = `
            <div class="loading-spinner"></div>
            <span class="loading-text">${this.escapeHtml(message)}</span>
        `;

        document.body.appendChild(this.overlay);
        setTimeout(() => this.overlay.style.display = 'flex', 10);
    },

    hide() {
        if (this.overlay) {
            this.overlay.style.display = 'none';
            setTimeout(() => {
                if (this.overlay && this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                }
                this.overlay = null;
            }, 300);
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Progress Bar System
window.ProgressBar = {
    bar: null,

    show() {
        this.hide(); // Remove any existing bar

        this.bar = document.createElement('div');
        this.bar.id = 'progress-bar';
        this.bar.className = 'progress-bar';
        document.body.appendChild(this.bar);

        setTimeout(() => this.bar.style.display = 'block', 10);
    },

    hide() {
        if (this.bar) {
            this.bar.style.display = 'none';
            setTimeout(() => {
                if (this.bar && this.bar.parentNode) {
                    this.bar.parentNode.removeChild(this.bar);
                }
                this.bar = null;
            }, 300);
        }
    }
};

// HTTP Utilities
window.HTTP = {
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            ProgressBar.show();
            const response = await fetch(url, mergedOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error('HTTP Request failed:', error);
            throw error;
        } finally {
            ProgressBar.hide();
        }
    },

    async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    },

    async post(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async put(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
};

// Form Utilities
window.FormUtils = {
    serialize(form) {
        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (arrays)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }

        return data;
    },

    validate(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });

        return isValid;
    },

    validateInput(input) {
        const value = input.value.trim();
        const rules = this.parseValidationRules(input);
        let isValid = true;
        let message = '';

        // Required check
        if (rules.required && !value) {
            isValid = false;
            message = rules.requiredMessage || 'This field is required';
        }

        // Length checks
        if (value && rules.minLength && value.length < rules.minLength) {
            isValid = false;
            message = `Minimum ${rules.minLength} characters required`;
        }

        if (value && rules.maxLength && value.length > rules.maxLength) {
            isValid = false;
            message = `Maximum ${rules.maxLength} characters allowed`;
        }

        // Pattern check
        if (value && rules.pattern && !rules.pattern.test(value)) {
            isValid = false;
            message = rules.patternMessage || 'Invalid format';
        }

        // Update UI
        this.updateInputValidation(input, isValid, message);

        return isValid;
    },

    parseValidationRules(input) {
        try {
            return JSON.parse(input.dataset.validation || '{}');
        } catch {
            return {};
        }
    },

    updateInputValidation(input, isValid, message) {
        // Update input classes
        input.classList.remove('is-invalid', 'is-valid');
        input.classList.add(isValid ? 'is-valid' : 'is-invalid');

        // Update feedback
        const feedback = input.parentNode.querySelector('.form-feedback') ||
                        this.createFeedbackElement(input);

        if (message) {
            feedback.textContent = message;
            feedback.className = `form-feedback ${isValid ? 'valid' : 'invalid'} show`;
        } else {
            feedback.classList.remove('show');
        }
    },

    createFeedbackElement(input) {
        const feedback = document.createElement('div');
        feedback.className = 'form-feedback';
        input.parentNode.appendChild(feedback);
        return feedback;
    },

    setLoading(button, loading = true, text = null) {
        if (loading) {
            button.disabled = true;
            button.classList.add('loading');
            const spinner = button.querySelector('.btn-spinner');
            const textEl = button.querySelector('.btn-text');

            if (spinner) spinner.style.display = 'inline-block';
            if (textEl && text) textEl.textContent = text;
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            const spinner = button.querySelector('.btn-spinner');

            if (spinner) spinner.style.display = 'none';
        }
    }
};

// Theme Management
window.ThemeManager = {
    toggle() {
        const currentTheme = ProgrammingBot.theme;
        let newTheme;

        if (currentTheme === 'light') {
            newTheme = 'dark';
        } else if (currentTheme === 'dark') {
            newTheme = 'auto';
        } else {
            newTheme = 'light';
        }

        ProgrammingBot.applyTheme(newTheme);
        return newTheme;
    },

    set(theme) {
        ProgrammingBot.applyTheme(theme);
    },

    get() {
        return ProgrammingBot.theme;
    }
};

// Utility Functions
window.Utils = {
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    formatDateTime(dateString, format = 'DD.MM.YYYY HH:mm') {
        try {
            const date = new Date(dateString);
            const pad = (num) => num.toString().padStart(2, '0');

            const formats = {
                'DD': pad(date.getDate()),
                'MM': pad(date.getMonth() + 1),
                'YYYY': date.getFullYear(),
                'HH': pad(date.getHours()),
                'mm': pad(date.getMinutes()),
                'ss': pad(date.getSeconds())
            };

            return format.replace(/DD|MM|YYYY|HH|mm|ss/g, match => formats[match]);
        } catch {
            return dateString;
        }
    },

    timeAgo(dateString) {
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diff = now - date;

            const units = [
                { name: 'Jahr', value: 365 * 24 * 60 * 60 * 1000, plural: 'Jahren' },
                { name: 'Monat', value: 30 * 24 * 60 * 60 * 1000, plural: 'Monaten' },
                { name: 'Tag', value: 24 * 60 * 60 * 1000, plural: 'Tagen' },
                { name: 'Stunde', value: 60 * 60 * 1000, plural: 'Stunden' },
                { name: 'Minute', value: 60 * 1000, plural: 'Minuten' }
            ];

            for (const unit of units) {
                const count = Math.floor(diff / unit.value);
                if (count > 0) {
                    return `vor ${count} ${count === 1 ? unit.name : unit.plural}`;
                }
            }

            return 'gerade eben';
        } catch {
            return '';
        }
    },

    copyToClipboard(text) {
        return navigator.clipboard.writeText(text).then(() => {
            AlertSystem.show('In Zwischenablage kopiert!', 'success', 2000);
            return true;
        }).catch(error => {
            console.error('Copy failed:', error);
            AlertSystem.show('Kopieren fehlgeschlagen', 'error');
            return false;
        });
    },

    downloadFile(content, filename, mimeType = 'text/plain') {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');

        a.href = url;
        a.download = filename;
        a.click();

        window.URL.revokeObjectURL(url);
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    parseJson(str, fallback = null) {
        try {
            return JSON.parse(str);
        } catch {
            return fallback;
        }
    }
};

// Global Functions (for backward compatibility and template use)
function showAlert(message, type = 'info', duration = 5000) {
    return AlertSystem.show(message, type, duration);
}

function hideAlert(alert = null) {
    if (alert) {
        AlertSystem.hide(alert);
    } else {
        AlertSystem.hideAll();
    }
}

function toggleTheme() {
    return ThemeManager.toggle();
}

function closeAlert(alert) {
    AlertSystem.hide(alert);
}

function closeModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ProgrammingBot.init();
    AlertSystem.init();

    console.log('🚀 Programming Bot 2025 ready!');
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    if (ProgrammingBot.config?.debug) {
        AlertSystem.show(`JavaScript Error: ${e.message}`, 'error');
    }
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    if (ProgrammingBot.config?.debug) {
        AlertSystem.show(`Promise Error: ${e.reason}`, 'error');
    }
});