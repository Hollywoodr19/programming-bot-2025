#!/bin/bash

echo "🚀 Starting Programming Bot..."
echo "================================"

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    exit 1
fi

# Prüfe Port
if lsof -Pi :8100 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Port 8100 ist bereits belegt!"
    echo "   Prozess auf Port 8100:"
    lsof -i :8100
    echo ""
    echo "   Beende den Prozess mit: kill -9 <PID>"
    exit 1
fi

# Prüfe Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Erstelle Virtual Environment..."
    python3 -m venv venv
fi

# Aktiviere venv
source venv/bin/activate

# Prüfe Dependencies
echo "📦 Prüfe Dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Prüfe .env
if [ ! -f .env ]; then
    echo "⚠️  .env Datei nicht gefunden!"
    cp .env.example .env
    echo "✅ .env wurde aus .env.example erstellt"
    echo "⚠️  Bitte trage deinen ANTHROPIC_API_KEY in .env ein!"
    exit 1
fi

# Prüfe API Key
if grep -q "your_anthropic_api_key_here" .env; then
    echo "⚠️  ANTHROPIC_API_KEY noch nicht gesetzt!"
    echo "   Bitte editiere .env und trage deinen API Key ein"
    exit 1
fi

# Erstelle notwendige Ordner
mkdir -p static templates

echo ""
echo "✅ Alle Checks erfolgreich!"
echo "🚀 Starte Bot auf http://localhost:8100"
echo "================================"
echo ""

# Starte den Bot
python main.py