import sqlite3
import time
from typing import List, Dict, Any, Optional
from config import DB_PATH, MAX_WARNS_DEFAULT

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables for Riya."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                chat_type TEXT,
                is_active INTEGER DEFAULT 1,
                welcome_enabled INTEGER DEFAULT 1,
                welcome_message TEXT,
                ai_chat_enabled INTEGER DEFAULT 1,
                anti_link_enabled INTEGER DEFAULT 0,
                rules TEXT,
                added_at INTEGER
            )
        """)
        
        # Users table (tracks users in bot DMs or groups for broadcasts & stats)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_active INTEGER DEFAULT 1,
                first_seen INTEGER
            )
        """)
        
        # Warnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                warned_by INTEGER,
                warned_at INTEGER
            )
        """)
        
        # AFK table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS afk (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                afk_time INTEGER
            )
        """)
        
        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                chat_id INTEGER,
                keyword TEXT,
                content TEXT,
                file_id TEXT,
                media_type TEXT,
                PRIMARY KEY (chat_id, keyword)
            )
        """)
        
        # Locks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locks (
                chat_id INTEGER,
                lock_type TEXT,
                PRIMARY KEY (chat_id, lock_type)
            )
        """)
        
        conn.commit()

# --- Group Operations ---

def register_group(chat_id: int, title: str, chat_type: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO groups (chat_id, title, chat_type, is_active, added_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                title = excluded.title,
                chat_type = excluded.chat_type,
                is_active = 1
        """, (chat_id, title, chat_type, int(time.time())))
        conn.commit()

def set_group_active(chat_id: int, is_active: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET is_active = ? WHERE chat_id = ?", (1 if is_active else 0, chat_id))
        conn.commit()

def get_all_active_groups() -> List[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM groups WHERE is_active = 1")
        return [row["chat_id"] for row in cursor.fetchall()]

def get_group_settings(chat_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_group_setting(chat_id: int, key: str, value: Any):
    allowed_keys = {"welcome_enabled", "ai_chat_enabled", "anti_link_enabled", "welcome_message", "rules"}
    if key not in allowed_keys:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE groups SET {key} = ? WHERE chat_id = ?", (value, chat_id))
        conn.commit()

# --- User Operations ---

def register_user(user_id: int, username: str, first_name: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name, is_active, first_seen)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                is_active = 1
        """, (user_id, username or "", first_name or "", int(time.time())))
        conn.commit()

def get_all_active_users() -> List[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_active = 1")
        return [row["user_id"] for row in cursor.fetchall()]

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    clean = username.lstrip("@").lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Warn Operations ---

def add_warning(chat_id: int, user_id: int, reason: str, warned_by: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO warns (chat_id, user_id, reason, warned_by, warned_at)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, user_id, reason, warned_by, int(time.time())))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) as count FROM warns WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        return cursor.fetchone()["count"]

def get_warning_count(chat_id: int, user_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM warns WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        return cursor.fetchone()["count"]

def reset_warnings(chat_id: int, user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM warns WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        conn.commit()

# --- AFK Operations ---

def set_afk(user_id: int, reason: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO afk (user_id, reason, afk_time)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                reason = excluded.reason,
                afk_time = excluded.afk_time
        """, (user_id, reason, int(time.time())))
        conn.commit()

def get_afk(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def remove_afk(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM afk WHERE user_id = ?", (user_id,))
        conn.commit()

# --- Notes Operations ---

def set_note(chat_id: int, keyword: str, content: str, file_id: str = None, media_type: str = "text"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notes (chat_id, keyword, content, file_id, media_type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, keyword) DO UPDATE SET
                content = excluded.content,
                file_id = excluded.file_id,
                media_type = excluded.media_type
        """, (chat_id, keyword.lower(), content, file_id, media_type))
        conn.commit()

def get_note(chat_id: int, keyword: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE chat_id = ? AND keyword = ?", (chat_id, keyword.lower()))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_note(chat_id: int, keyword: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE chat_id = ? AND keyword = ?", (chat_id, keyword.lower()))
        conn.commit()
        return cursor.rowcount > 0

def get_all_notes(chat_id: int) -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM notes WHERE chat_id = ?", (chat_id,))
        return [row["keyword"] for row in cursor.fetchall()]

# --- Lock Operations ---

def set_lock(chat_id: int, lock_type: str, lock: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        if lock:
            cursor.execute("INSERT OR IGNORE INTO locks (chat_id, lock_type) VALUES (?, ?)", (chat_id, lock_type))
        else:
            cursor.execute("DELETE FROM locks WHERE chat_id = ? AND lock_type = ?", (chat_id, lock_type))
        conn.commit()

def is_locked(chat_id: int, lock_type: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM locks WHERE chat_id = ? AND lock_type = ?", (chat_id, lock_type))
        return cursor.fetchone() is not None

def get_locked_types(chat_id: int) -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT lock_type FROM locks WHERE chat_id = ?", (chat_id,))
        return [row["lock_type"] for row in cursor.fetchall()]

# --- Stats Operations ---

def get_total_stats() -> Dict[str, int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM groups WHERE is_active = 1")
        total_groups = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()["count"]
        return {"groups": total_groups, "users": total_users}
