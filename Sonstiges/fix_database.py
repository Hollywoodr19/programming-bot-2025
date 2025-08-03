# FÜHRE DIESES SCRIPT AUS UM DIE DATABASE ZU FIXEN:
# Speichere als fix_database.py und führe aus: python fix_database.py

import sqlite3
import os


def fix_projects_table():
    """Fix projects table schema mismatch"""

    db_path = "../bot_data.db"

    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()

        print("🔍 Current projects table schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        existing_columns = [col[1] for col in columns]

        # Add missing columns
        missing_columns = {
            'status': 'TEXT DEFAULT "active"',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }

        for col_name, col_def in missing_columns.items():
            if col_name not in existing_columns:
                print(f"✅ Adding missing column: {col_name}")
                cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}")
            else:
                print(f"✅ Column {col_name} already exists")

        # Fix user_id column if needed
        if 'user_id' not in existing_columns:
            print("✅ Adding missing column: user_id")
            cursor.execute("ALTER TABLE projects ADD COLUMN user_id TEXT")

            # Update existing projects with default user_id
            cursor.execute("UPDATE projects SET user_id = 'admin' WHERE user_id IS NULL")

        conn.commit()

        # Verify final schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()

        print("\n🎯 Final projects table schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        print("\n✅ Database schema fixed successfully!")

    except Exception as e:
        print(f"❌ Error fixing database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔧 Fixing Projects Database Schema...")
    fix_projects_table()
    print("🚀 Run your bot again: python main.py")