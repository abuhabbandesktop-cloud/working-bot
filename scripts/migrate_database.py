#!/usr/bin/env python3
"""
Database migration script to add new fields for enhanced chat functionality.
Run this script to update your existing database with the new schema.
"""

import sqlite3
import os
from pathlib import Path

# Get the database path
DB_PATH = Path(__file__).parent.parent / "data" / "app.db"

def migrate_database():
    """Apply database migrations for enhanced chat features."""
    print(f"🔄 Starting database migration for: {DB_PATH}")
    
    if not DB_PATH.exists():
        print("❌ Database file not found. Please run the application first to create the database.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(chats)")
        chat_columns = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(messages)")
        message_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📊 Current schema:")
        print(f"   Chats columns: {len(chat_columns)}")
        print(f"   Users columns: {len(user_columns)}")
        print(f"   Messages columns: {len(message_columns)}")
        
        # Migrate chats table
        migrations_applied = 0
        
        if 'description' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN description TEXT")
            migrations_applied += 1
            print("✅ Added 'description' to chats table")
        
        if 'member_count' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN member_count INTEGER DEFAULT 0")
            migrations_applied += 1
            print("✅ Added 'member_count' to chats table")
        
        if 'is_pinned' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE")
            migrations_applied += 1
            print("✅ Added 'is_pinned' to chats table")
        
        if 'is_muted' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN is_muted BOOLEAN DEFAULT FALSE")
            migrations_applied += 1
            print("✅ Added 'is_muted' to chats table")
        
        if 'last_message_id' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN last_message_id INTEGER")
            migrations_applied += 1
            print("✅ Added 'last_message_id' to chats table")
        
        if 'last_activity' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN last_activity DATETIME")
            migrations_applied += 1
            print("✅ Added 'last_activity' to chats table")
        
        if 'created_at' not in chat_columns:
            cursor.execute("ALTER TABLE chats ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            migrations_applied += 1
            print("✅ Added 'created_at' to chats table")
        
        # Migrate users table
        if 'avatar_url' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
            migrations_applied += 1
            print("✅ Added 'avatar_url' to users table")
        
        if 'is_online' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_online BOOLEAN DEFAULT FALSE")
            migrations_applied += 1
            print("✅ Added 'is_online' to users table")
        
        if 'last_seen' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_seen DATETIME")
            migrations_applied += 1
            print("✅ Added 'last_seen' to users table")
        
        if 'created_at' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            migrations_applied += 1
            print("✅ Added 'created_at' to users table")
        
        # Migrate messages table
        if 'reply_to_message_id' not in message_columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN reply_to_message_id INTEGER")
            migrations_applied += 1
            print("✅ Added 'reply_to_message_id' to messages table")
        
        if 'is_edited' not in message_columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN is_edited BOOLEAN DEFAULT FALSE")
            migrations_applied += 1
            print("✅ Added 'is_edited' to messages table")
        
        if 'edit_date' not in message_columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN edit_date DATETIME")
            migrations_applied += 1
            print("✅ Added 'edit_date' to messages table")
        
        # Update last_message_id for existing chats
        cursor.execute("""
            UPDATE chats 
            SET last_message_id = (
                SELECT id FROM messages 
                WHERE messages.chat_id = chats.id 
                ORDER BY created_at DESC 
                LIMIT 1
            )
            WHERE last_message_id IS NULL
        """)
        
        # Update last_activity for existing chats
        cursor.execute("""
            UPDATE chats 
            SET last_activity = (
                SELECT created_at FROM messages 
                WHERE messages.chat_id = chats.id 
                ORDER BY created_at DESC 
                LIMIT 1
            )
            WHERE last_activity IS NULL
        """)
        
        conn.commit()
        
        if migrations_applied > 0:
            print(f"🎉 Migration completed successfully! Applied {migrations_applied} changes.")
        else:
            print("✨ Database is already up to date!")
        
        # Show final schema
        cursor.execute("PRAGMA table_info(chats)")
        chat_columns_after = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(users)")
        user_columns_after = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(messages)")
        message_columns_after = [row[1] for row in cursor.fetchall()]
        
        print(f"📊 Updated schema:")
        print(f"   Chats columns: {len(chat_columns_after)}")
        print(f"   Users columns: {len(user_columns_after)}")
        print(f"   Messages columns: {len(message_columns_after)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def backup_database():
    """Create a backup of the database before migration."""
    if not DB_PATH.exists():
        return False
    
    backup_path = DB_PATH.with_suffix('.backup.db')
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"💾 Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Telegram Bot Database Migration")
    print("=" * 50)
    
    # Create backup
    if backup_database():
        print("✅ Backup created successfully")
    else:
        print("⚠️  Could not create backup, proceeding anyway...")
    
    print()
    
    # Run migration
    if migrate_database():
        print("\n🎉 Migration completed! Your database is now ready for the enhanced UI.")
        print("\n📝 Next steps:")
        print("   1. Restart your backend server")
        print("   2. Restart your bot")
        print("   3. Refresh your frontend")
        print("   4. Enjoy the new Telegram-like interface!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("   Your original database is backed up and unchanged.")