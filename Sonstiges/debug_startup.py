#!/usr/bin/env python3
"""
Flask Startup Debugging Script
Diagnoses why main.py exits with code 0 immediately
"""

import sys
import os
import traceback

print("🔍 PROGRAMMING BOT 2025 - STARTUP DIAGNOSTICS")
print("=" * 60)

# Test 1: Python Environment
print("1. PYTHON ENVIRONMENT CHECK")
print(f"   Python Version: {sys.version}")
print(f"   Python Executable: {sys.executable}")
print(f"   Current Working Directory: {os.getcwd()}")
print(f"   Python Path: {len(sys.path)} entries")

# Test 2: Required Files Check
print("\n2. REQUIRED FILES CHECK")
required_files = [
    'main.py',
    'auth_system.py',
    'session_manager.py',
    'config.py',
    '.env'
]

for file in required_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"   ✅ {file} ({size} bytes)")
    else:
        print(f"   ❌ {file} - MISSING!")

# Test 3: Import Tests (Individual)
print("\n3. INDIVIDUAL IMPORT TESTS")

# Test Flask
try:
    import flask

    print(f"   ✅ Flask {flask.__version__}")
except ImportError as e:
    print(f"   ❌ Flask: {e}")

# Test python-dotenv
try:
    import dotenv

    print(f"   ✅ python-dotenv")
except ImportError as e:
    print(f"   ❌ python-dotenv: {e}")

# Test our modules one by one
modules_to_test = [
    ('config', 'config.py'),
    ('auth_system', 'auth_system.py'),
    ('session_manager', 'session_manager.py')
]

for module_name, file_name in modules_to_test:
    try:
        if os.path.exists(file_name):
            # Try to import
            exec(f"import {module_name}")
            print(f"   ✅ {module_name}")
        else:
            print(f"   ❌ {module_name} - File missing")
    except Exception as e:
        print(f"   ❌ {module_name}: {e}")
        # Show detailed error for our modules
        print(f"      Details: {traceback.format_exc()}")

# Test 4: Environment Variables
print("\n4. ENVIRONMENT VARIABLES")
env_vars = [
    'CLAUDE_API_KEY',
    'SECRET_KEY',
    'HOST',
    'PORT',
    'DEBUG'
]

for var in env_vars:
    value = os.environ.get(var)
    if value:
        # Mask sensitive values
        if 'KEY' in var or 'SECRET' in var:
            display_value = f"{'*' * min(10, len(value))}... (length: {len(value)})"
        else:
            display_value = value
        print(f"   ✅ {var} = {display_value}")
    else:
        print(f"   ⚠️  {var} - Not set")

# Test 5: Try to load .env file
print("\n5. .ENV FILE TEST")
try:
    if os.path.exists('../.env'):
        with open('../.env', 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"   ✅ .env file exists with {len(lines)} configuration lines")

        # Try to load with python-dotenv
        try:
            from dotenv import load_dotenv

            load_dotenv()
            print("   ✅ .env file loaded successfully")
        except Exception as e:
            print(f"   ❌ .env loading failed: {e}")
    else:
        print("   ⚠️  .env file not found")
except Exception as e:
    print(f"   ❌ .env file error: {e}")

# Test 6: Try to run main.py parts step by step
print("\n6. MAIN.PY STEP-BY-STEP TEST")

try:
    print("   Step 1: Import main module...")
    sys.path.insert(0, '..')

    # Read main.py and analyze
    if os.path.exists('../main.py'):
        with open('../main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()

        print(f"   ✅ main.py read ({len(main_content)} characters)")

        # Check for if __name__ == "__main__"
        if 'if __name__ == ' in main_content:
            print("   ✅ Found __name__ check")
        else:
            print("   ❌ Missing __name__ check - this might be the problem!")

        # Check for main() function
        if 'def main():' in main_content:
            print("   ✅ Found main() function")
        else:
            print("   ⚠️  No main() function found")

        # Check for app.run()
        if 'app.run(' in main_content:
            print("   ✅ Found app.run() call")
        else:
            print("   ⚠️  No app.run() call found")

    else:
        print("   ❌ main.py not found!")

except Exception as e:
    print(f"   ❌ main.py analysis failed: {e}")

# Test 7: Try minimal Flask test
print("\n7. MINIMAL FLASK TEST")
try:
    from flask import Flask

    test_app = Flask(__name__)


    @test_app.route('/')
    def hello():
        return "Test OK"


    print("   ✅ Minimal Flask app created successfully")

    # Try to get app config
    print(f"   ✅ App name: {test_app.name}")
    print(f"   ✅ App debug: {test_app.debug}")

except Exception as e:
    print(f"   ❌ Minimal Flask test failed: {e}")

# Test 8: Port availability
print("\n8. PORT AVAILABILITY")
import socket


def check_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


ports_to_check = [8100, 5000, 8000]
for port in ports_to_check:
    if check_port('127.0.0.1', port):
        print(f"   ⚠️  Port {port} is OCCUPIED")
    else:
        print(f"   ✅ Port {port} is available")

print("\n" + "=" * 60)
print("🎯 DIAGNOSIS COMPLETE")
print("\nNext steps:")
print("1. Check for any ❌ errors in the imports")
print("2. Verify all required files exist")
print("3. Make sure .env file is properly formatted")
print("4. Check if __name__ == '__main__' is present in main.py")
print("5. Look for any blocking code before app.run()")

print(f"\nTo run this script: python debug_startup.py")
print("To run main with verbose output: python -v main.py")