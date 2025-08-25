import sqlite3
import os
from datetime import datetime

# Database path
db_path = "data/app.db"

def fix_database():
    print("🔧 Fixing database schema...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if created_at column exists in chats table
        cursor.execute("PRAGMA table_info(chats)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in columns:
            print("➕ Adding created_at column to chats table...")
            cursor.execute("ALTER TABLE chats ADD COLUMN created_at DATETIME DEFAULT '2025-01-01 00:00:00'")
            print("✅ Added created_at column")
        else:
            print("✅ created_at column already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Database schema fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()