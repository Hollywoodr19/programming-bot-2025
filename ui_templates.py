# ui_templates.py - Login & Registration UI Templates

def get_login_template():
    """Login/Registration Screen"""
    return """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Programming Bot 2025 - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        /* Animated Background */
        .background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            z-index: -2;
        }

        .background::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
            animation: backgroundPulse 15s ease-in-out infinite;
        }

        @keyframes backgroundPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        /* Main Container */
        .auth-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            animation: slideUp 0.8s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .auth-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .auth-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }

        .auth-header p {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.1rem;
        }

        /* Form Styles */
        .auth-form {
            margin-bottom: 20px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }

        .form-group input {
            width: 100%;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 1rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .form-group input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }

        .form-group input:focus {
            outline: none;
            border-color: #00d4ff;
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            transform: translateY(-2px);
        }

        /* Buttons */
        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 15px;
            position: relative;
            overflow: hidden;
        }

        .btn-primary {
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            color: white;
            box-shadow: 0 10px 25px rgba(0, 212, 255, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0, 212, 255, 0.4);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }

        /* Loading Animation */
        .loading {
            display: none;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 2px solid white;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Tab System */
        .auth-tabs {
            display: flex;
            margin-bottom: 25px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            padding: 4px;
        }

        .auth-tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 500;
        }

        .auth-tab.active {
            background: rgba(0, 212, 255, 0.3);
            color: white;
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
        }

        .auth-tab:hover:not(.active) {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.9);
        }

        /* Error Messages */
        .error-message {
            background: rgba(255, 59, 48, 0.2);
            border: 1px solid rgba(255, 59, 48, 0.4);
            color: #ff6b6b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            text-align: center;
            animation: shake 0.5s ease-in-out;
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }

        .success-message {
            background: rgba(52, 199, 89, 0.2);
            border: 1px solid rgba(52, 199, 89, 0.4);
            color: #32d74b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            text-align: center;
        }

        /* Extra Options */
        .auth-extras {
            text-align: center;
            margin-top: 25px;
        }

        .auth-extras a {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.3s ease;
        }

        .auth-extras a:hover {
            color: #00d4ff;
        }

        .auth-extras .separator {
            margin: 0 15px;
            color: rgba(255, 255, 255, 0.5);
        }

        /* Hidden Forms */
        .auth-form-container {
            display: none;
        }

        .auth-form-container.active {
            display: block;
            animation: fadeIn 0.4s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Mobile Responsive */
        @media (max-width: 480px) {
            .auth-container {
                margin: 20px;
                padding: 30px 25px;
            }

            .auth-header h1 {
                font-size: 2rem;
            }
        }

        /* Guest Mode */
        .guest-mode {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .guest-mode p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            margin-bottom: 10px;
        }

        .btn-guest {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 10px 20px;
            width: auto;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="background"></div>

    <div class="auth-container">
        <div class="auth-header">
            <h1>🤖 Programming Bot</h1>
            <p>2025 AI Assistant</p>
        </div>

        <!-- Tab Navigation -->
        <div class="auth-tabs">
            <div class="auth-tab active" onclick="switchAuthTab('login')">Anmelden</div>
            <div class="auth-tab" onclick="switchAuthTab('register')">Registrieren</div>
        </div>

        <!-- Error/Success Messages -->
        <div id="message-container"></div>

        <!-- Login Form -->
        <div id="login-form" class="auth-form-container active">
            <form class="auth-form" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label for="login-username">👤 Benutzername oder E-Mail</label>
                    <input type="text" id="login-username" name="username" 
                           placeholder="Dein Username..." required>
                </div>

                <div class="form-group">
                    <label for="login-password">🔒 Passwort</label>
                    <input type="password" id="login-password" name="password" 
                           placeholder="Dein Passwort..." required>
                </div>

                <button type="submit" class="btn btn-primary" id="login-btn">
                    Anmelden
                </button>
                <div class="loading" id="login-loading"></div>
            </form>
        </div>

        <!-- Register Form -->
        <div id="register-form" class="auth-form-container">
            <form class="auth-form" onsubmit="handleRegister(event)">
                <div class="form-group">
                    <label for="reg-display-name">✨ Anzeigename</label>
                    <input type="text" id="reg-display-name" name="display_name" 
                           placeholder="Dein Name..." required>
                </div>

                <div class="form-group">
                    <label for="reg-username">👤 Benutzername</label>
                    <input type="text" id="reg-username" name="username" 
                           placeholder="Eindeutiger Username..." required minlength="3">
                </div>

                <div class="form-group">
                    <label for="reg-email">📧 E-Mail</label>
                    <input type="email" id="reg-email" name="email" 
                           placeholder="deine@email.de" required>
                </div>

                <div class="form-group">
                    <label for="reg-password">🔒 Passwort</label>
                    <input type="password" id="reg-password" name="password" 
                           placeholder="Sicheres Passwort..." required minlength="6">
                </div>

                <div class="form-group">
                    <label for="reg-password-confirm">🔒 Passwort bestätigen</label>
                    <input type="password" id="reg-password-confirm" name="password_confirm" 
                           placeholder="Passwort wiederholen..." required>
                </div>

                <button type="submit" class="btn btn-primary" id="register-btn">
                    Registrieren
                </button>
                <div class="loading" id="register-loading"></div>
            </form>
        </div>

        <!-- Guest Mode -->
        <div class="guest-mode">
            <p>🎭 Nur mal schnell testen?</p>
            <button class="btn btn-guest" onclick="guestLogin()">
                Als Gast fortfahren
            </button>
        </div>

        <!-- Extra Links -->
        <div class="auth-extras">
            <a href="#" onclick="showForgotPassword()">Passwort vergessen?</a>
            <span class="separator">|</span>
            <a href="#" onclick="showHelp()">Hilfe</a>
        </div>
    </div>

    <script>
        // Tab Switching
        function switchAuthTab(tab) {
            // Update tab appearance
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');

            // Show/hide forms
            document.querySelectorAll('.auth-form-container').forEach(f => f.classList.remove('active'));
            document.getElementById(tab + '-form').classList.add('active');

            // Clear messages
            clearMessages();
        }

        // Message Handling
        function showMessage(message, type = 'error') {
            const container = document.getElementById('message-container');
            container.innerHTML = `<div class="${type}-message">${message}</div>`;
        }

        function clearMessages() {
            document.getElementById('message-container').innerHTML = '';
        }

        // Login Handler
        async function handleLogin(event) {
            event.preventDefault();

            const btn = document.getElementById('login-btn');
            const loading = document.getElementById('login-loading');
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;

            // UI feedback
            btn.style.display = 'none';
            loading.style.display = 'block';
            clearMessages();

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password }),
                    credentials: 'include'
                });

                const result = await response.json();

                if (result.success) {
                    // Store session
                    localStorage.setItem('session_token', result.session_token);
                    localStorage.setItem('user_data', JSON.stringify(result.user));

                    showMessage(`✅ Willkommen zurück, ${result.user.display_name}!`, 'success');

                    // Redirect to main app
                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 1500);
                } else {
                    showMessage(result.error);
                }
            } catch (error) {
                showMessage('Verbindungsfehler. Bitte versuche es später erneut.');
            } finally {
                btn.style.display = 'block';
                loading.style.display = 'none';
            }
        }

        // Register Handler
        async function handleRegister(event) {
            event.preventDefault();

            const btn = document.getElementById('register-btn');
            const loading = document.getElementById('register-loading');

            // Get form data
            const formData = {
                display_name: document.getElementById('reg-display-name').value,
                username: document.getElementById('reg-username').value,
                email: document.getElementById('reg-email').value,
                password: document.getElementById('reg-password').value,
                password_confirm: document.getElementById('reg-password-confirm').value
            };

            // Validate passwords match
            if (formData.password !== formData.password_confirm) {
                showMessage('Passwörter stimmen nicht überein!');
                return;
            }

            // UI feedback
            btn.style.display = 'none';
            loading.style.display = 'block';
            clearMessages();

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData),
                    credentials: 'include'
                });

                const result = await response.json();

                if (result.success) {
                    showMessage(`✅ Registrierung erfolgreich! Du kannst dich jetzt anmelden.`, 'success');

                    // Switch to login tab
                    setTimeout(() => {
                        switchAuthTab('login');
                        document.getElementById('login-username').value = formData.username;
                    }, 2000);
                } else {
                    showMessage(result.error);
                }
            } catch (error) {
                showMessage('Registrierung fehlgeschlagen. Bitte versuche es später erneut.');
            } finally {
                btn.style.display = 'block';
                loading.style.display = 'none';
            }
        }

        // Guest Login
        function guestLogin() {
            localStorage.setItem('guest_mode', 'true');
            localStorage.setItem('user_data', JSON.stringify({
                username: 'guest',
                display_name: 'Gast',
                is_admin: false
            }));

            showMessage('✅ Als Gast angemeldet!', 'success');
            setTimeout(() => {
                window.location.href = '/app';
            }, 1000);
        }

        // Utility Functions
        function showForgotPassword() {
            showMessage('💡 Wende dich an den Administrator für ein neues Passwort.');
        }

        function showHelp() {
            showMessage('💬 Bei Problemen kontaktiere den Administrator oder nutze den Gast-Modus.');
        }

        // Auto-focus first input
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('login-username').focus();
        });
    </script>
</body>
</html>
"""