/**
 * Programming Interface JavaScript
 * Handles code editor, chat, AI interactions
 */

class ProgrammingInterface {
    constructor() {
        this.currentLanguage = 'python';
        this.autoSaveInterval = null;
        this.chatHistory = [];
        this.codeHistory = [];
        this.isTyping = false;
        this.sessionId = this.generateSessionId();

        this.init();
    }

    init() {
        this.setupCodeEditor();
        this.setupChat();
        this.setupKeyboardShortcuts();
        this.setupAutoSave();
        this.setupLanguageSelector();
        this.setupThemeToggle();
        this.loadSessionData();
        this.bindEvents();
    }

    bindEvents() {
        // Code editor events
        const codeEditor = document.getElementById('codeEditor');
        if (codeEditor) {
            codeEditor.addEventListener('input', () => this.onCodeChange());
            codeEditor.addEventListener('keydown', (e) => this.handleCodeEditorKeys(e));
        }

        // Chat events
        const chatForm = document.getElementById('chatForm');
        const chatInput = document.getElementById('chatInput');

        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.sendMessage(e));
        }

        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => this.handleChatKeys(e));
            chatInput.addEventListener('input', () => this.adjustChatInputHeight());
        }

        // Language selector
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => this.changeLanguage(e.target.value));
        }

        // Action buttons
        this.bindActionButtons();

        // Window events
        window.addEventListener('beforeunload', () => this.saveSessionData());
        window.addEventListener('resize', () => this.adjustLayout());
    }

    bindActionButtons() {
        // Run code button
        const runBtn = document.getElementById('runCode');
        if (runBtn) {
            runBtn.addEventListener('click', () => this.runCode());
        }

        // Clear output button
        const clearBtn = document.getElementById('clearOutput');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearOutput());
        }

        // Export code button
        const exportBtn = document.getElementById('exportCode');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportCode());
        }

        // Import code button
        const importBtn = document.getElementById('importCode');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importCode());
        }

        // Clear chat button
        const clearChatBtn = document.getElementById('clearChat');
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => this.clearChat());
        }

        // Settings button
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.toggleSettings());
        }
    }

    setupCodeEditor() {
        const editor = document.getElementById('codeEditor');
        if (!editor) return;

        // Load saved code
        const savedCode = this.getStoredCode();
        if (savedCode) {
            editor.value = savedCode;
        } else {
            // Set default code based on language
            editor.value = this.getDefaultCode(this.currentLanguage);
        }

        // Setup syntax highlighting (basic)
        this.updateSyntaxHighlighting();
    }

    setupChat() {
        // Load chat history
        this.loadChatHistory();
        this.scrollChatToBottom();
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveCode();
                this.showMessage('Code gespeichert! 💾', 'success');
            }

            // Ctrl/Cmd + R: Run code
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.runCode();
            }

            // Ctrl/Cmd + /: Toggle comment
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.toggleComment();
            }

            // Ctrl/Cmd + D: Duplicate line
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                this.duplicateLine();
            }

            // F5: Run code
            if (e.key === 'F5') {
                e.preventDefault();
                this.runCode();
            }

            // Escape: Focus chat input
            if (e.key === 'Escape') {
                const chatInput = document.getElementById('chatInput');
                if (chatInput) {
                    chatInput.focus();
                }
            }
        });
    }

    setupAutoSave() {
        // Auto-save every 30 seconds
        this.autoSaveInterval = setInterval(() => {
            this.saveCode();
        }, 30000);
    }

    setupLanguageSelector() {
        const selector = document.getElementById('languageSelect');
        if (selector) {
            selector.value = this.currentLanguage;
        }
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    handleCodeEditorKeys(e) {
        const editor = e.target;

        // Tab for indentation
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = editor.selectionStart;
            const end = editor.selectionEnd;

            if (e.shiftKey) {
                // Shift+Tab: Decrease indentation
                this.decreaseIndentation(editor, start, end);
            } else {
                // Tab: Increase indentation
                this.insertIndentation(editor, start, end);
            }
        }

        // Auto-close brackets and quotes
        if (['(', '[', '{', '"', "'"].includes(e.key)) {
            this.autoCloseBrackets(editor, e);
        }

        // Enter: Smart indentation
        if (e.key === 'Enter') {
            this.handleSmartIndentation(editor, e);
        }
    }

    handleChatKeys(e) {
        // Ctrl/Cmd + Enter: Send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.sendMessage(e);
        }

        // Shift + Enter: New line
        if (e.shiftKey && e.key === 'Enter') {
            // Allow default behavior (new line)
            return;
        }

        // Enter without modifiers: Send message
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage(e);
        }
    }

    onCodeChange() {
        // Mark as changed
        const editor = document.getElementById('codeEditor');
        if (editor) {
            editor.dataset.changed = 'true';
        }

        // Update syntax highlighting
        this.updateSyntaxHighlighting();

        // Clear auto-save timer and set new one
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }

        this.autoSaveTimeout = setTimeout(() => {
            this.saveCode();
        }, 2000); // Save 2 seconds after user stops typing
    }

    adjustChatInputHeight() {
        const input = document.getElementById('chatInput');
        if (!input) return;

        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    }

    adjustLayout() {
        // Responsive layout adjustments
        const container = document.querySelector('.programming-container');
        if (!container) return;

        if (window.innerWidth < 768) {
            container.classList.add('mobile-layout');
        } else {
            container.classList.remove('mobile-layout');
        }
    }

    changeLanguage(language) {
        this.currentLanguage = language;

        // Update editor placeholder and default code
        const editor = document.getElementById('codeEditor');
        if (editor && !editor.value.trim()) {
            editor.value = this.getDefaultCode(language);
        }

        // Update syntax highlighting
        this.updateSyntaxHighlighting();

        // Save preference
        localStorage.setItem('programmingLanguage', language);

        this.showMessage(`Sprache zu ${language.toUpperCase()} geändert! 🚀`, 'success');
    }

    getDefaultCode(language) {
        const defaults = {
            python: `# Python Code
print("Hallo Welt!")

def greet(name):
    return f"Hallo, {name}!"

result = greet("Claude")
print(result)`,

            javascript: `// JavaScript Code
console.log("Hallo Welt!");

function greet(name) {
    return \`Hallo, \${name}!\`;
}

const result = greet("Claude");
console.log(result);`,

            html: `<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meine Webseite</title>
</head>
<body>
    <h1>Hallo Welt!</h1>
    <p>Willkommen bei Claude!</p>
</body>
</html>`,

            css: `/* CSS Styles */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

h1 {
    color: white;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}`,

            java: `// Java Code
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hallo Welt!");
        
        String name = "Claude";
        String greeting = greet(name);
        System.out.println(greeting);
    }
    
    public static String greet(String name) {
        return "Hallo, " + name + "!";
    }
}`,

            cpp: `// C++ Code
#include <iostream>
#include <string>

using namespace std;

string greet(const string& name) {
    return "Hallo, " + name + "!";
}

int main() {
    cout << "Hallo Welt!" << endl;
    
    string name = "Claude";
    string greeting = greet(name);
    cout << greeting << endl;
    
    return 0;
}`,

            sql: `-- SQL Code
-- Datenbank erstellen
CREATE DATABASE IF NOT EXISTS programming_bot;
USE programming_bot;

-- Tabelle für Benutzer
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Beispieldaten einfügen
INSERT INTO users (username, email) VALUES 
('claude', 'claude@example.com'),
('admin', 'admin@example.com');

-- Benutzer abfragen
SELECT * FROM users WHERE username = 'claude';`
        };

        return defaults[language] || `// ${language.toUpperCase()} Code\n// Beginnen Sie hier zu programmieren...`;
    }

    updateSyntaxHighlighting() {
        // Basic syntax highlighting (would be enhanced with a proper library like Prism.js)
        const editor = document.getElementById('codeEditor');
        if (!editor) return;

        // Add language class for CSS styling
        editor.className = `code-editor language-${this.currentLanguage}`;
    }

    async sendMessage(e) {
        if (e && e.preventDefault) e.preventDefault();

        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        // Clear input
        input.value = '';
        this.adjustChatInputHeight();

        // Add user message to chat
        this.addChatMessage(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Get current code context
            const currentCode = document.getElementById('codeEditor').value;

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    language: this.currentLanguage,
                    code: currentCode,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                // Remove typing indicator
                this.hideTypingIndicator();

                // Add AI response
                this.addChatMessage(data.response, 'assistant');

                // If code was generated, ask if user wants to insert it
                if (data.code) {
                    this.offerCodeInsertion(data.code);
                }
            } else {
                this.hideTypingIndicator();
                this.addChatMessage('Entschuldigung, es gab einen Fehler beim Verarbeiten Ihrer Nachricht.', 'assistant', 'error');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addChatMessage('Verbindungsfehler. Bitte versuchen Sie es erneut.', 'assistant', 'error');
        }
    }

    addChatMessage(message, sender, type = 'normal') {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender} ${type}`;

        const timestamp = new Date().toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender-name">${sender === 'user' ? 'Du' : 'Claude'}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-content">${this.formatMessage(message)}</div>
        `;

        chatMessages.appendChild(messageDiv);
        this.scrollChatToBottom();

        // Save to history
        this.chatHistory.push({
            message: message,
            sender: sender,
            timestamp: Date.now(),
            type: type
        });

        // Limit history size
        if (this.chatHistory.length > 100) {
            this.chatHistory = this.chatHistory.slice(-100);
        }
    }

    formatMessage(message) {
        // Basic markdown-like formatting
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message assistant typing';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-header">
                <span class="sender-name">Claude</span>
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        this.scrollChatToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollChatToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    offerCodeInsertion(code) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const offerDiv = document.createElement('div');
        offerDiv.className = 'code-insertion-offer';
        offerDiv.innerHTML = `
            <div class="offer-content">
                <p>💡 Code generiert! Möchten Sie ihn in den Editor einfügen?</p>
                <div class="offer-actions">
                    <button class="btn btn-primary" onclick="programmingInterface.insertCode(\`${code.replace(/`/g, '\\`')}\`)">
                        Einfügen
                    </button>
                    <button class="btn btn-secondary" onclick="this.closest('.code-insertion-offer').remove()">
                        Ablehnen
                    </button>
                </div>
            </div>
        `;

        chatMessages.appendChild(offerDiv);
        this.scrollChatToBottom();
    }

    insertCode(code) {
        const editor = document.getElementById('codeEditor');
        if (editor) {
            editor.value = code;
            editor.focus();
            this.onCodeChange();
            this.showMessage('Code eingefügt! 📝', 'success');
        }

        // Remove the offer
        document.querySelector('.code-insertion-offer')?.remove();
    }

    async runCode() {
        const code = document.getElementById('codeEditor').value;
        const output = document.getElementById('output');

        if (!code.trim()) {
            this.showMessage('Bitte geben Sie Code ein!', 'warning');
            return;
        }

        if (!output) return;

        // Show loading
        output.innerHTML = '<div class="output-loading">Code wird ausgeführt... ⚡</div>';

        try {
            // Simulate code execution (in real implementation, this would call a backend)
            await this.simulateCodeExecution(code);
        } catch (error) {
            console.error('Code execution error:', error);
            output.innerHTML = `<div class="output-error">Fehler beim Ausführen des Codes: ${error.message}</div>`;
        }
    }

    async simulateCodeExecution(code) {
        const output = document.getElementById('output');

        // Simulate delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Basic simulation based on language
        let result = '';

        switch (this.currentLanguage) {
            case 'python':
                result = this.simulatePythonExecution(code);
                break;
            case 'javascript':
                result = this.simulateJavaScriptExecution(code);
                break;
            default:
                result = `Code-Ausführung für ${this.currentLanguage} wird simuliert...\n\n✅ Code erfolgreich verarbeitet!`;
        }

        output.innerHTML = `<pre class="output-success">${result}</pre>`;
    }

    simulatePythonExecution(code) {
        // Basic Python simulation
        let output = '';

        if (code.includes('print(')) {
            const printMatches = code.match(/print\((.*?)\)/g);
            if (printMatches) {
                printMatches.forEach(match => {
                    const content = match.replace(/print\((.*?)\)/, '$1').replace(/['"]/g, '');
                    output += content + '\n';
                });
            }
        }

        if (!output) {
            output = '✅ Python Code erfolgreich ausgeführt!\n(Simulation - für echte Ausführung würde ein Python-Interpreter benötigt)';
        }

        return output;
    }

    simulateJavaScriptExecution(code) {
        // Basic JavaScript simulation
        let output = '';

        if (code.includes('console.log(')) {
            const logMatches = code.match(/console\.log\((.*?)\)/g);
            if (logMatches) {
                logMatches.forEach(match => {
                    const content = match.replace(/console\.log\((.*?)\)/, '$1').replace(/['"]/g, '');
                    output += content + '\n';
                });
            }
        }

        if (!output) {
            output = '✅ JavaScript Code erfolgreich ausgeführt!\n(Simulation - für echte Ausführung verwenden Sie die Browser-Konsole)';
        }

        return output;
    }

    clearOutput() {
        const output = document.getElementById('output');
        if (output) {
            output.innerHTML = '<div class="output-placeholder">Output wird hier angezeigt...</div>';
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
            this.chatHistory = [];
            this.showMessage('Chat geleert! 🧹', 'success');
        }
    }

    exportCode() {
        const code = document.getElementById('codeEditor').value;
        const language = this.currentLanguage;

        const extensions = {
            python: 'py',
            javascript: 'js',
            html: 'html',
            css: 'css',
            java: 'java',
            cpp: 'cpp',
            sql: 'sql'
        };

        const extension = extensions[language] || 'txt';
        const filename = `code.${extension}`;

        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showMessage(`Code als ${filename} exportiert! 📄`, 'success');
    }

    importCode() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.py,.js,.html,.css,.java,.cpp,.sql,.txt';

        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const code = e.target.result;
                    document.getElementById('codeEditor').value = code;
                    this.onCodeChange();
                    this.showMessage(`Code aus ${file.name} importiert! 📂`, 'success');
                };
                reader.readAsText(file);
            }
        };

        input.click();
    }

    toggleSettings() {
        // Toggle settings panel (would be implemented based on UI)
        this.showMessage('Einstellungen-Panel (noch nicht implementiert) 🔧', 'info');
    }

    toggleTheme() {
        const body = document.body;
        const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        if (newTheme === 'dark') {
            body.classList.add('dark-theme');
        } else {
            body.classList.remove('dark-theme');
        }

        localStorage.setItem('theme', newTheme);
        this.showMessage(`Theme zu ${newTheme === 'dark' ? 'Dunkel' : 'Hell'} geändert! 🎨`, 'success');
    }

    saveCode() {
        const code = document.getElementById('codeEditor').value;
        const key = `code_${this.currentLanguage}`;
        localStorage.setItem(key, code);

        // Mark as saved
        const editor = document.getElementById('codeEditor');
        if (editor) {
            editor.dataset.changed = 'false';
        }
    }

    getStoredCode() {
        const key = `code_${this.currentLanguage}`;
        return localStorage.getItem(key);
    }

    loadSessionData() {
        // Load language preference
        const savedLanguage = localStorage.getItem('programmingLanguage');
        if (savedLanguage) {
            this.currentLanguage = savedLanguage;
            const selector = document.getElementById('languageSelect');
            if (selector) {
                selector.value = savedLanguage;
            }
        }

        // Load theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
        }

        // Load chat history
        this.loadChatHistory();
    }

    loadChatHistory() {
        const saved = localStorage.getItem('chatHistory');
        if (saved) {
            try {
                this.chatHistory = JSON.parse(saved);
                // Restore recent messages (last 10)
                const recentMessages = this.chatHistory.slice(-10);
                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                    recentMessages.forEach(msg => {
                        this.addChatMessage(msg.message, msg.sender, msg.type);
                    });
                }
            } catch (error) {
                console.error('Error loading chat history:', error);
            }
        }
    }

    saveSessionData() {
        // Save code
        this.saveCode();

        // Save chat history
        try {
            localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory));
        } catch (error) {
            console.error('Error saving chat history:', error);
        }
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Utility methods for code editor
    insertIndentation(editor, start, end) {
        const value = editor.value;
        const indent = '    '; // 4 spaces

        if (start === end) {
            // No selection, just insert indent
            editor.value = value.substring(0, start) + indent + value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + indent.length;
        } else {
            // Selection exists, indent all lines
            const lines = value.substring(start, end).split('\n');
            const indentedLines = lines.map(line => indent + line);
            const newText = indentedLines.join('\n');

            editor.value = value.substring(0, start) + newText + value.substring(end);
            editor.selectionStart = start;
            editor.selectionEnd = start + newText.length;
        }
    }

    toggleComment() {
        const editor = document.getElementById('codeEditor');
        if (!editor) return;

        const commentChars = {
            python: '#',
            javascript: '//',
            html: '<!--',
            css: '/*',
            java: '//',
            cpp: '//',
            sql: '--'
        };

        const comment = commentChars[this.currentLanguage] || '//';

        // Get current line
        const start = editor.selectionStart;
        const value = editor.value;
        const lineStart = value.lastIndexOf('\n', start - 1) + 1;
        const lineEnd = value.indexOf('\n', start);
        const lineEndPos = lineEnd === -1 ? value.length : lineEnd;

        const line = value.substring(lineStart, lineEndPos);

        let newLine;
        if (line.trim().startsWith(comment)) {
            // Uncomment
            newLine = line.replace(new RegExp(`^(\\s*)${comment}\\s?`), '$1');
        } else {
            // Comment
            const indent = line.match(/^\s*/)[0];
            newLine = indent + comment + ' ' + line.substring(indent.length);
        }

        editor.value = value.substring(0, lineStart) + newLine + value.substring(lineEndPos);

        // Restore cursor position
        const newPos = start + (newLine.length - line.length);
        editor.selectionStart = editor.selectionEnd = Math.max(lineStart, newPos);
    }

    duplicateLine() {
        const editor = document.getElementById('codeEditor');
        if (!editor) return;

        const start = editor.selectionStart;
        const value = editor.value;
        const lineStart = value.lastIndexOf('\n', start - 1) + 1;
        const lineEnd = value.indexOf('\n', start);
        const lineEndPos = lineEnd === -1 ? value.length : lineEnd;

        const line = value.substring(lineStart, lineEndPos);
        const newLine = '\n' + line;

        editor.value = value.substring(0, lineEndPos) + newLine + value.substring(lineEndPos);

        // Move cursor to duplicated line
        editor.selectionStart = editor.selectionEnd = lineEndPos + newLine.length;
    }

    showMessage(message, type = 'info') {
        // Use the global showMessage function from main.js
        if (window.showMessage) {
            window.showMessage(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.programmingInterface = new ProgrammingInterface();
});

// Global access for code insertion
window.insertCode = function(code) {
    if (window.programmingInterface) {
        window.programmingInterface.insertCode(code);
    }
};