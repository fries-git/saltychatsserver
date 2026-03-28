import json
import os
import sqlite3
import threading
import time
from typing import Dict, List, Optional, Any

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_MODULE_DIR, "originchats.db")

_local = threading.local()
_initialized = False
_init_lock = threading.Lock()

SCHEMA = """
-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    name TEXT,
    type TEXT DEFAULT 'text',
    description TEXT,
    permissions TEXT,
    position INTEGER DEFAULT 0,
    size INTEGER
);

-- Messages table (works for both channel messages and thread messages)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    thread_id TEXT,
    user_id TEXT NOT NULL,
    content TEXT,
    timestamp REAL NOT NULL,
    edited INTEGER DEFAULT 0,
    pinned INTEGER DEFAULT 0,
    reply_to_id TEXT,
    reply_to_user TEXT,
    attachments TEXT,
    embeds TEXT,
    webhook TEXT,
    created_at REAL
);

CREATE INDEX IF NOT EXISTS idx_messages_channel_ts ON messages(channel, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_thread_ts ON messages(thread_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_id ON messages(id);

-- Reactions table
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    emoji TEXT NOT NULL,
    user_id TEXT NOT NULL,
    added_at REAL NOT NULL,
    UNIQUE(message_id, emoji, user_id),
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reactions_msg ON reactions(message_id);

-- Threads metadata table
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    name TEXT,
    parent_channel TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    locked INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    participants TEXT
);

CREATE INDEX IF NOT EXISTS idx_threads_channel ON threads(parent_channel);

-- Pinned messages tracking
CREATE TABLE IF NOT EXISTS pinned_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    thread_id TEXT,
    pinned_at REAL NOT NULL,
    UNIQUE(message_id),
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pinned_channel ON pinned_messages(channel, thread_id);

-- Webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    name TEXT NOT NULL,
    token TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    avatar TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhooks_channel ON webhooks(channel);

-- Users table (for user data that needs to persist)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    roles TEXT,
    validator TEXT,
    nickname TEXT,
    status TEXT,
    created_at REAL,
    last_seen REAL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_validator ON users(validator);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    name TEXT PRIMARY KEY,
    description TEXT,
    color TEXT,
    hoisted INTEGER DEFAULT 0,
    permissions TEXT,
    self_assignable INTEGER DEFAULT 0,
    category TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
        _local.connection.execute("PRAGMA foreign_keys = ON")
        _local.connection.execute("PRAGMA journal_mode = WAL")
    return _local.connection


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the database, creating tables if they don't exist."""
    global _DB_PATH, _initialized
    
    with _init_lock:
        if _initialized:
            return
        
        if db_path:
            _DB_PATH = db_path
        
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
        
        conn = get_connection()
        conn.executescript(SCHEMA)
        conn.commit()
        _initialized = True


def close_connection() -> None:
    """Close the thread-local connection."""
    if hasattr(_local, 'connection') and _local.connection:
        _local.connection.close()
        _local.connection = None


def execute(query: str, params: tuple = (), commit: bool = True) -> sqlite3.Cursor:
    """Execute a query and optionally commit."""
    conn = get_connection()
    cursor = conn.execute(query, params)
    if commit:
        conn.commit()
    return cursor


def executemany(query: str, params_list: List[tuple], commit: bool = True) -> sqlite3.Cursor:
    """Execute many queries and optionally commit."""
    conn = get_connection()
    cursor = conn.executemany(query, params_list)
    if commit:
        conn.commit()
    return cursor


def fetchone(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Execute a query and return a single row as dict."""
    conn = get_connection()
    cursor = conn.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None


def fetchall(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a query and return all rows as list of dicts."""
    conn = get_connection()
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def _json_dumps(obj: Any) -> Optional[str]:
    """Safely serialize to JSON."""
    if obj is None:
        return None
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)


def _json_loads(s: Optional[str]) -> Any:
    """Safely deserialize from JSON."""
    if s is None:
        return None
    return json.loads(s)


if os.path.exists(_DB_PATH):
    init_db()
