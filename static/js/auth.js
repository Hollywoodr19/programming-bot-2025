/**
 * Authentication JavaScript
 * Handles login, registration, password validation
 */

class AuthManager {
    constructor() {
        this.passwordStrengthCache = new Map();
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupFormValidation();
        this.initPasswordStrength();
    }

    bindEvents() {
        // Login/Register form switching
        const switchBtns = document.querySelectorAll('.auth-switch-btn');
        switchBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchAuthMode(btn.dataset.mode);
            });
        });

        // Form submissions
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Real-time password validation
        const passwordInputs = document.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            input.addEventListener('input', (e) => this.validatePasswordRealtime(e));
            input.addEventListener('focus', (e) => this.showPasswordStrength(e));
            input.addEventListener('blur', (e) => this.hidePasswordStrength(e));
        });

        // Show/hide password toggles
        const toggleBtns = document.querySelectorAll('.password-toggle');
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.togglePasswordVisibility(e));
        });

        // Enter key handling
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                const activeForm = document.querySelector('.auth-form:not(.hidden)');
                if (activeForm) {
                    e.preventDefault();
                    activeForm.querySelector('button[type="submit"]').click();
                }
            }
        });
    }

    switchAuthMode(mode) {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const title = document.querySelector('.auth-title');

        if (mode === 'register') {
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            title.textContent = 'Account erstellen';

            // Focus first input
            setTimeout(() => {
                registerForm.querySelector('input').focus();
            }, 100);
        } else {
            registerForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
            title.textContent = 'Anmelden';

            // Focus first input
            setTimeout(() => {
                loginForm.querySelector('input').focus();
            }, 100);
        }

        // Update URL without refresh
        const newUrl = mode === 'register' ? '?mode=register' : '?mode=login';
        window.history.replaceState({}, '', newUrl);
    }

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type="submit"]');
        const username = form.username.value.trim();
        const password = form.password.value;

        if (!this.validateLoginForm(username, password)) {
            return;
        }

        this.setLoading(btn, true);

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    remember_me: form.remember_me?.checked || false
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage('Erfolgreich angemeldet! 🎉', 'success');

                // Redirect after short delay
                setTimeout(() => {
                    window.location.href = data.redirect || '/programming';
                }, 1000);
            } else {
                this.showMessage(data.message || 'Anmeldung fehlgeschlagen', 'error');

                // Clear password on error
                form.password.value = '';
                form.password.focus();
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showMessage('Verbindungsfehler. Bitte versuchen Sie es erneut.', 'error');
        } finally {
            this.setLoading(btn, false);
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type="submit"]');
        const username = form.username.value.trim();
        const password = form.password.value;
        const confirmPassword = form.confirm_password.value;

        if (!this.validateRegisterForm(username, password, confirmPassword)) {
            return;
        }

        this.setLoading(btn, true);

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    confirm_password: confirmPassword
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage('Account erfolgreich erstellt! 🎉', 'success');

                // Switch to login form
                setTimeout(() => {
                    this.switchAuthMode('login');
                    document.getElementById('loginForm').username.value = username;
                    document.getElementById('loginForm').password.focus();
                }, 1500);
            } else {
                this.showMessage(data.message || 'Registrierung fehlgeschlagen', 'error');
            }
        } catch (error) {
            console.error('Register error:', error);
            this.showMessage('Verbindungsfehler. Bitte versuchen Sie es erneut.', 'error');
        } finally {
            this.setLoading(btn, false);
        }
    }

    validateLoginForm(username, password) {
        if (!username) {
            this.showMessage('Benutzername ist erforderlich', 'error');
            return false;
        }
        if (!password) {
            this.showMessage('Passwort ist erforderlich', 'error');
            return false;
        }
        return true;
    }

    validateRegisterForm(username, password, confirmPassword) {
        if (!username) {
            this.showMessage('Benutzername ist erforderlich', 'error');
            return false;
        }
        if (username.length < 3) {
            this.showMessage('Benutzername muss mindestens 3 Zeichen lang sein', 'error');
            return false;
        }
        if (!password) {
            this.showMessage('Passwort ist erforderlich', 'error');
            return false;
        }
        if (password !== confirmPassword) {
            this.showMessage('Passwörter stimmen nicht überein', 'error');
            return false;
        }

        const strength = this.calculatePasswordStrength(password);
        if (strength.score < 4) {
            this.showMessage('Passwort ist zu schwach. Mindestens 4/8 Punkte erforderlich.', 'error');
            return false;
        }

        return true;
    }

    setupFormValidation() {
        // Real-time username validation
        const usernameInputs = document.querySelectorAll('input[name="username"]');
        usernameInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = e.target.value.trim();
                const feedback = input.parentNode.querySelector('.field-feedback');

                if (value.length > 0 && value.length < 3) {
                    this.setFieldFeedback(feedback, 'Mindestens 3 Zeichen', 'error');
                } else if (value.length >= 3) {
                    this.setFieldFeedback(feedback, 'Gültig ✓', 'success');
                } else {
                    this.setFieldFeedback(feedback, '', '');
                }
            });
        });

        // Confirm password validation
        const confirmInputs = document.querySelectorAll('input[name="confirm_password"]');
        confirmInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const password = document.querySelector('input[name="password"]').value;
                const confirmPassword = e.target.value;
                const feedback = input.parentNode.querySelector('.field-feedback');

                if (confirmPassword.length > 0) {
                    if (password === confirmPassword) {
                        this.setFieldFeedback(feedback, 'Passwörter stimmen überein ✓', 'success');
                    } else {
                        this.setFieldFeedback(feedback, 'Passwörter stimmen nicht überein', 'error');
                    }
                } else {
                    this.setFieldFeedback(feedback, '', '');
                }
            });
        });
    }

    initPasswordStrength() {
        const passwordInputs = document.querySelectorAll('input[name="password"]');
        passwordInputs.forEach(input => {
            // Create strength indicator if it doesn't exist
            let strengthIndicator = input.parentNode.querySelector('.password-strength');
            if (!strengthIndicator) {
                strengthIndicator = document.createElement('div');
                strengthIndicator.className = 'password-strength hidden';
                strengthIndicator.innerHTML = `
                    <div class="strength-bar">
                        <div class="strength-fill"></div>
                    </div>
                    <div class="strength-text">Passwortstärke: <span class="strength-score">0/8</span></div>
                    <div class="strength-tips"></div>
                `;
                input.parentNode.appendChild(strengthIndicator);
            }
        });
    }

    validatePasswordRealtime(e) {
        const password = e.target.value;
        const strengthIndicator = e.target.parentNode.querySelector('.password-strength');

        if (!strengthIndicator) return;

        const strength = this.calculatePasswordStrength(password);
        this.updatePasswordStrength(strengthIndicator, strength);
    }

    calculatePasswordStrength(password) {
        let score = 0;
        const tips = [];

        // Length check
        if (password.length >= 8) {
            score += 1;
        } else {
            tips.push('Mindestens 8 Zeichen');
        }

        if (password.length >= 12) {
            score += 1;
        } else if (password.length >= 8) {
            tips.push('12+ Zeichen für höhere Sicherheit');
        }

        // Character variety
        if (/[a-z]/.test(password)) {
            score += 1;
        } else {
            tips.push('Kleinbuchstaben (a-z)');
        }

        if (/[A-Z]/.test(password)) {
            score += 1;
        } else {
            tips.push('Großbuchstaben (A-Z)');
        }

        if (/[0-9]/.test(password)) {
            score += 1;
        } else {
            tips.push('Zahlen (0-9)');
        }

        if (/[^a-zA-Z0-9]/.test(password)) {
            score += 1;
        } else {
            tips.push('Sonderzeichen (!@#$%...)');
        }

        // Pattern checks
        if (!/(.)\1{2,}/.test(password)) {
            score += 1;
        } else {
            tips.push('Keine sich wiederholenden Zeichen');
        }

        if (!/123|abc|qwe|asd|zxc/i.test(password)) {
            score += 1;
        } else {
            tips.push('Keine einfachen Muster');
        }

        return { score, tips, percentage: (score / 8) * 100 };
    }

    updatePasswordStrength(indicator, strength) {
        const fill = indicator.querySelector('.strength-fill');
        const scoreSpan = indicator.querySelector('.strength-score');
        const tipsDiv = indicator.querySelector('.strength-tips');

        // Update score
        scoreSpan.textContent = `${strength.score}/8`;

        // Update bar
        fill.style.width = `${strength.percentage}%`;

        // Color based on strength
        let color = '#e74c3c'; // Red
        if (strength.score >= 6) color = '#27ae60'; // Green
        else if (strength.score >= 4) color = '#f39c12'; // Orange
        else if (strength.score >= 2) color = '#e67e22'; // Dark orange

        fill.style.backgroundColor = color;

        // Update tips
        if (strength.tips.length > 0) {
            tipsDiv.innerHTML = `
                <div class="tips-title">Verbesserungen:</div>
                <ul>${strength.tips.map(tip => `<li>${tip}</li>`).join('')}</ul>
            `;
        } else {
            tipsDiv.innerHTML = '<div class="tips-success">✓ Starkes Passwort!</div>';
        }
    }

    showPasswordStrength(e) {
        const strengthIndicator = e.target.parentNode.querySelector('.password-strength');
        if (strengthIndicator) {
            strengthIndicator.classList.remove('hidden');
        }
    }

    hidePasswordStrength(e) {
        // Only hide if password is empty
        if (e.target.value === '') {
            const strengthIndicator = e.target.parentNode.querySelector('.password-strength');
            if (strengthIndicator) {
                strengthIndicator.classList.add('hidden');
            }
        }
    }

    togglePasswordVisibility(e) {
        e.preventDefault();
        const btn = e.target.closest('.password-toggle');
        const input = btn.parentNode.querySelector('input');
        const icon = btn.querySelector('i') || btn;

        if (input.type === 'password') {
            input.type = 'text';
            icon.textContent = '👁️‍🗨️';
            btn.title = 'Passwort verstecken';
        } else {
            input.type = 'password';
            icon.textContent = '👁️';
            btn.title = 'Passwort anzeigen';
        }
    }

    setFieldFeedback(element, message, type) {
        if (!element) return;

        element.textContent = message;
        element.className = `field-feedback ${type}`;

        if (!message) {
            element.classList.add('hidden');
        } else {
            element.classList.remove('hidden');
        }
    }

    setLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = '<i class="loading-spinner"></i> Lädt...';
            button.classList.add('loading');
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || button.textContent;
            button.classList.remove('loading');
        }
    }

    showMessage(message, type = 'info') {
        // Use the global showMessage function from main.js
        if (window.showMessage) {
            window.showMessage(message, type);
        } else {
            // Fallback
            alert(message);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});

// Handle page load with mode parameter
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');

    if (mode === 'register') {
        const authManager = new AuthManager();
        authManager.switchAuthMode('register');
    }
});