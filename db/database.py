import json
import os
import sqlite3
import sys
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
    display_name TEXT,
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
    interaction TEXT,
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
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT,
    hoisted INTEGER DEFAULT 0,
    permissions TEXT,
    self_assignable INTEGER DEFAULT 0,
    category TEXT,
    position INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- Polls table
CREATE TABLE IF NOT EXISTS polls (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    channel TEXT,
    thread_id TEXT,
    question TEXT NOT NULL,
    options TEXT NOT NULL,
    allow_multiselect INTEGER DEFAULT 0,
    expires_at REAL,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    ended INTEGER DEFAULT 0,
    ended_at REAL,
    UNIQUE(message_id)
);

CREATE INDEX IF NOT EXISTS idx_polls_message ON polls(message_id);

-- Poll votes table
    CREATE TABLE IF NOT EXISTS poll_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id TEXT NOT NULL,
    option_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    voted_at REAL NOT NULL,
    UNIQUE(poll_id, option_id, user_id),
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_poll_votes_poll ON poll_votes(poll_id);
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

        # Check if database exists, handle migration or fresh setup
        if not os.path.exists(_DB_PATH):
            _handle_first_time_setup()

        conn = get_connection()
        conn.executescript(SCHEMA)
        conn.commit()

        _run_schema_migrations(conn)

        conn.commit()
        _initialized = True


def _insert_default_roles(conn, uuid, json):
    """Insert default roles into the database."""
    OWNER_PERMS = ["administrator"]
    ADMIN_PERMS = ["manage_roles", "manage_channels", "manage_users", "manage_server",
                  "manage_messages", "manage_threads", "mention_everyone", "use_slash_commands"]
    MODERATOR_PERMS = ["manage_messages", "manage_threads", "use_slash_commands"]
    USER_PERMS = ["use_slash_commands"]

    default_roles = [
        (str(uuid.uuid4()), "owner", "Server owner with ultimate permissions.", "#d5beff", 1, json.dumps(OWNER_PERMS), 0, None, 0),
        (str(uuid.uuid4()), "admin", "Administrator role with full permissions.", "#FF0000", 1, json.dumps(ADMIN_PERMS), 0, None, 1),
        (str(uuid.uuid4()), "moderator", "Moderator role with elevated permissions.", "#FFFF00", 1, json.dumps(MODERATOR_PERMS), 0, None, 2),
        (str(uuid.uuid4()), "user", "Regular user role with standard permissions.", "#FFFFFF", 0, json.dumps(USER_PERMS), 0, None, 3),
    ]

    for role in default_roles:
        conn.execute(
            "INSERT INTO roles (id, name, description, color, hoisted, permissions, self_assignable, category, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            role
        )


def _run_schema_migrations(conn):
    """Run schema migrations for existing databases."""
    import uuid
    import json

    # Create roles table if it doesn't exist
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'")
        roles_table_exists = cursor.fetchone() is not None
        
        if not roles_table_exists:
            conn.execute("""
                CREATE TABLE roles (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT,
                    hoisted INTEGER DEFAULT 0,
                    permissions TEXT,
                    self_assignable INTEGER DEFAULT 0,
                    category TEXT,
                    position INTEGER DEFAULT 0
                )
            """)
        
        # Check if roles table is empty - if so, try to migrate from roles.json
        cursor = conn.execute("SELECT COUNT(*) FROM roles")
        roles_count = cursor.fetchone()[0]
        
        if roles_count == 0:
            roles_json_path = os.path.join(os.path.dirname(_DB_PATH), "roles.json")
            if os.path.exists(roles_json_path):
                try:
                    with open(roles_json_path, 'r', encoding='utf-8') as f:
                        roles_data = json.load(f)
                    
                    if roles_data:
                        print("[Migrating roles from roles.json]")
                        position = 0
                        for role_name, role_data in roles_data.items():
                            role_id = str(uuid.uuid4())
                            conn.execute(
                                "INSERT INTO roles (id, name, description, color, hoisted, permissions, self_assignable, category, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (role_id, 
                                 role_name, 
                                 role_data.get("description"), 
                                 role_data.get("color"), 
                                 1 if role_data.get("hoisted") else 0, 
                                 json.dumps(role_data.get("permissions", {})), 
                                 1 if role_data.get("self_assignable") else 0, 
                                 role_data.get("category"),
                                 position)
                            )
                            position += 1
                        print(f"[Migrated {position} roles from roles.json]")
                except Exception as e:
                    print(f"Error migrating roles.json: {e}")
                    if roles_count == 0 and not roles_table_exists:
                        _insert_default_roles(conn, uuid, json)
            elif roles_count == 0 and not roles_table_exists:
                _insert_default_roles(conn, uuid, json)
    except Exception as e:
        print(f"Migration error (roles table creation): {e}")

    # Add position column to roles if missing
    try:
        cursor = conn.execute("PRAGMA table_info(roles)")
        columns = [row[1] for row in cursor.fetchall()]
        if columns and "position" not in columns:
            conn.execute("ALTER TABLE roles ADD COLUMN position INTEGER DEFAULT 0")
    except Exception:
        pass

    try:
        cursor = conn.execute("PRAGMA table_info(roles)")
        columns = [row[1] for row in cursor.fetchall()]
        # Only run this migration if roles table exists and doesn't have id column
        if columns and "id" not in columns:
            cursor = conn.execute("SELECT name FROM roles")
            existing_roles = [row[0] for row in cursor.fetchall()]

            conn.execute("""
                CREATE TABLE roles_new (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT,
                    hoisted INTEGER DEFAULT 0,
                    permissions TEXT,
                    self_assignable INTEGER DEFAULT 0,
                    category TEXT,
                    position INTEGER DEFAULT 0
                )
            """)

            for role_name in existing_roles:
                role_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO roles_new (id, name, description, color, hoisted, permissions, self_assignable, category, position)
                    SELECT ?, name, description, color, hoisted, permissions, self_assignable, category, position
                    FROM roles WHERE name = ?
                """, (role_id, role_name))

            conn.execute("DROP TABLE roles")
            conn.execute("ALTER TABLE roles_new RENAME TO roles")
    except Exception:
        pass

    try:
        cursor = conn.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]
        if "interaction" not in columns:
            conn.execute("ALTER TABLE messages ADD COLUMN interaction TEXT")
    except Exception:
        pass

    try:
        cursor = conn.execute("PRAGMA table_info(channels)")
        columns = [row[1] for row in cursor.fetchall()]
        if "display_name" not in columns:
            conn.execute("ALTER TABLE channels ADD COLUMN display_name TEXT")
    except Exception:
        pass


def _handle_first_time_setup():
    """Handle first-time setup: ask about migration or create defaults."""
    json_files = [
        ("channels.json", "Channels"),
        ("roles.json", "Roles"),
        ("webhooks.json", "Webhooks"),
        ("users.json", "Users"),
    ]
    
    existing_data = []
    for filename, _ in json_files:
        filepath = os.path.join(os.path.dirname(_DB_PATH), filename)
        if os.path.exists(filepath):
            existing_data.append(filename)
    
    if existing_data:
        print("\n" + "=" * 60)
        print("Existing JSON data detected:")
        print(f"  {', '.join(existing_data)}")
        print("=" * 60)
        print("\nWould you like to migrate this data to SQLite?")
        print("  yes - Migrate existing data")
        print("  no  - Exit (you can run migration manually later)")
        
        response = input("\nChoice (yes/no): ").strip().lower()
        
        if response in ('yes', 'y'):
            print("\n[Migrating data to SQLite...]")
            _run_migration()
            print("[Migration complete!]\n")
        else:
            print("\nMigration cancelled. Exiting...")
            sys.exit(0)
    else:
        # No existing data - create defaults
        print("\n[First time setup - creating default channels and roles]")
        _create_default_data()


def _create_default_data():
    """Create default channels and roles for a fresh installation."""
    import uuid
    import json
    conn = get_connection()

    OWNER_PERMS = ["administrator"]
    ADMIN_PERMS = [
        "administrator",
        "manage_roles", "manage_channels", "manage_users", "manage_server",
        "manage_messages", "manage_threads", "manage_nicknames",
        "kick_members", "ban_members",
        "create_invite", "manage_invites",
        "mention_everyone", "use_slash_commands",
        "mute_members", "deafen_members", "move_members",
        "connect", "speak", "stream",
    ]
    MODERATOR_PERMS = [
        "manage_messages", "manage_threads",
        "kick_members", "manage_nicknames",
        "mute_members", "deafen_members", "move_members",
        "create_invite",
        "use_slash_commands",
    ]
    USER_PERMS = [
        "send_messages", "read_message_history",
        "add_reactions", "attach_files", "embed_links", "external_emojis",
        "connect", "speak", "stream", "use_voice_activity",
        "change_nickname", "create_invite", "use_slash_commands",
    ]

    default_roles = {
        "owner": {"description": "Server owner with ultimate permissions.", "color": "#d5beff", "hoisted": True, "permissions": OWNER_PERMS, "position": 0},
        "admin": {"description": "Administrator role with full permissions.", "color": "#FF0000", "hoisted": True, "permissions": ADMIN_PERMS, "position": 1},
        "moderator": {"description": "Moderator role with elevated permissions.", "color": "#FFFF00", "hoisted": True, "permissions": MODERATOR_PERMS, "position": 2},
        "user": {"description": "Regular user role with standard permissions.", "color": "#FFFFFF", "hoisted": False, "permissions": USER_PERMS, "position": 3},
    }

    for role_name, role_data in default_roles.items():
        role_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR IGNORE INTO roles (id, name, description, color, hoisted, permissions, self_assignable, category, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (role_id, role_name, role_data.get("description"), role_data.get("color"),
            1 if role_data.get("hoisted") else 0, json.dumps(role_data.get("permissions", [])), 0, None, role_data.get("position", 0))
        )
    
    # Default channels
    default_channels = [
        {"name": "welcome", "type": "text", "description": "Welcome channel for new users", "permissions": {"view": ["user"], "send": ["user"]}},
        {"name": "general", "type": "text", "description": "General chat channel", "permissions": {"view": ["user"], "send": ["user"], "delete": ["admin"]}},
        {"name": "rules", "type": "text", "description": "Server rules", "permissions": {"view": ["user"], "send": ["owner"]}},
        {"name": "announcements", "type": "text", "description": "Important announcements", "permissions": {"view": ["user"], "send": ["admin"]}},
    ]
    
    for i, ch in enumerate(default_channels):
        conn.execute(
            "INSERT OR IGNORE INTO channels (name, type, description, permissions, position, size) VALUES (?, ?, ?, ?, ?, ?)",
            (ch.get("name"), ch.get("type", "text"), ch.get("description"),
             json.dumps(ch.get("permissions", {}), separators=(',', ':')), i, None)
        )
    
    conn.commit()
    conn.close()
    print("[Created default channels and roles]\n")


def _run_migration():
    """Run the migration from JSON files to SQLite."""
    import json
    import time as time_module
    import uuid

    db_dir = os.path.dirname(_DB_PATH)
    
    # Create the database with schema
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    
    def json_dumps(obj):
        if obj is None:
            return None
        return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
    
    # Migrate channels
    channels_file = os.path.join(db_dir, "channels.json")
    if os.path.exists(channels_file):
        print("  Migrating channels...")
        with open(channels_file, 'r') as f:
            channels_data = json.load(f)
        for i, ch in enumerate(channels_data):
            conn.execute(
                "INSERT OR REPLACE INTO channels (name, type, description, permissions, position, size) VALUES (?, ?, ?, ?, ?, ?)",
                (ch.get("name"), ch.get("type", "text"), ch.get("description"),
                 json_dumps(ch.get("permissions", {})), i, ch.get("size"))
            )
        conn.commit()
    
    # Migrate roles
    roles_file = os.path.join(db_dir, "roles.json")
    if os.path.exists(roles_file):
        print("  Migrating roles...")
        with open(roles_file, 'r') as f:
            roles_data = json.load(f)
        for role_name, role_data in roles_data.items():
            role_id = str(uuid.uuid4())
            conn.execute(
                "INSERT OR REPLACE INTO roles (id, name, description, color, hoisted, permissions, self_assignable, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (role_id, role_name, role_data.get("description"), role_data.get("color"),
                1 if role_data.get("hoisted") else 0, json_dumps(role_data.get("permissions", {})),
                1 if role_data.get("self_assignable") else 0, role_data.get("category"))
            )
        conn.commit()
    
    # Migrate webhooks
    webhooks_file = os.path.join(db_dir, "webhooks.json")
    if os.path.exists(webhooks_file):
        print("  Migrating webhooks...")
        with open(webhooks_file, 'r') as f:
            webhooks_data = json.load(f)
        for wh_id, wh_data in webhooks_data.items():
            conn.execute(
                "INSERT OR REPLACE INTO webhooks (id, channel, name, token, created_by, created_at, avatar) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (wh_data.get("id"), wh_data.get("channel"), wh_data.get("name"),
                 wh_data.get("token"), wh_data.get("created_by"),
                 wh_data.get("created_at"), wh_data.get("avatar"))
            )
        conn.commit()
    
    # Migrate users
    users_file = os.path.join(db_dir, "users.json")
    if os.path.exists(users_file):
        print("  Migrating users...")
        with open(users_file, 'r') as f:
            users_data = json.load(f)
        for user_id, user_data in users_data.items():
            conn.execute(
                "INSERT OR REPLACE INTO users (id, username, roles, validator, nickname, status, created_at, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, user_data.get("username"),
                 json_dumps(user_data.get("roles", [])),
                 user_data.get("validator"), user_data.get("nickname"),
                 json_dumps(user_data.get("status", {"status": "online", "text": ""})),
                 user_data.get("created_at"), user_data.get("last_seen"))
            )
        conn.commit()
    
    # Migrate messages from channel files
    channels_dir = os.path.join(db_dir, "channels")
    if os.path.isdir(channels_dir):
        print("  Migrating channel messages...")
        for channel_file in sorted(os.listdir(channels_dir)):
            if channel_file.endswith(".json"):
                channel_name = channel_file[:-5]
                filepath = os.path.join(channels_dir, channel_file)
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                msg = json.loads(line)
                                reply_to = msg.get("reply_to") or {}
                                conn.execute(
                                    """INSERT OR REPLACE INTO messages 
                                       (id, channel, thread_id, user_id, content, timestamp, 
                                        edited, pinned, reply_to_id, reply_to_user, attachments, embeds, webhook, created_at)
                                       VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (msg.get("id"), channel_name, msg.get("user"), msg.get("content", ""),
                                     msg.get("timestamp"), 1 if msg.get("edited") else 0,
                                     1 if msg.get("pinned") else 0, reply_to.get("id"), reply_to.get("user"),
                                     json_dumps(msg.get("attachments")), json_dumps(msg.get("embeds")),
                                     json_dumps(msg.get("webhook")), msg.get("timestamp"))
                                )
                                # Reactions
                                for emoji, user_ids in msg.get("reactions", {}).items():
                                    for user_id in user_ids:
                                        conn.execute(
                                            "INSERT OR IGNORE INTO reactions (message_id, emoji, user_id, added_at) VALUES (?, ?, ?, ?)",
                                            (msg.get("id"), emoji, user_id, msg.get("timestamp", time_module.time()))
                                        )
                            except json.JSONDecodeError:
                                pass
                conn.commit()
    
    # Migrate threads
    threads_dir = os.path.join(db_dir, "threads")
    if os.path.isdir(threads_dir):
        print("  Migrating threads...")
        for thread_file in sorted(os.listdir(threads_dir)):
            if thread_file.endswith(".json"):
                filepath = os.path.join(threads_dir, thread_file)
                with open(filepath, 'r') as f:
                    thread_data = json.load(f)
                conn.execute(
                    "INSERT OR REPLACE INTO threads (id, name, parent_channel, created_by, created_at, locked, archived, participants) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (thread_data.get("id"), thread_data.get("name"), thread_data.get("parent_channel"),
                     thread_data.get("created_by"), thread_data.get("created_at"),
                     1 if thread_data.get("locked") else 0, 1 if thread_data.get("archived") else 0,
                     json_dumps(thread_data.get("participants", [])))
                )
        conn.commit()
    
    # Migrate thread messages
    thread_messages_dir = os.path.join(db_dir, "threadMessages")
    if os.path.isdir(thread_messages_dir):
        print("  Migrating thread messages...")
        for msg_file in sorted(os.listdir(thread_messages_dir)):
            if msg_file.endswith(".jsonl"):
                thread_id = msg_file[:-6]
                filepath = os.path.join(thread_messages_dir, msg_file)
                # Get parent channel from thread
                thread_row = conn.execute("SELECT parent_channel FROM threads WHERE id = ?", (thread_id,)).fetchone()
                parent_channel = thread_row["parent_channel"] if thread_row else "general"
                
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                msg = json.loads(line)
                                reply_to = msg.get("reply_to") or {}
                                conn.execute(
                                    """INSERT OR REPLACE INTO messages 
                                       (id, channel, thread_id, user_id, content, timestamp, 
                                        edited, pinned, reply_to_id, reply_to_user, attachments, embeds, webhook, created_at)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (msg.get("id"), parent_channel, thread_id, msg.get("user"), msg.get("content", ""),
                                     msg.get("timestamp"), 1 if msg.get("edited") else 0,
                                     1 if msg.get("pinned") else 0, reply_to.get("id"), reply_to.get("user"),
                                     json_dumps(msg.get("attachments")), json_dumps(msg.get("embeds")),
                                     json_dumps(msg.get("webhook")), msg.get("timestamp"))
                                )
                            except json.JSONDecodeError:
                                pass
                conn.commit()
    
    conn.close()
    print(f"  Database created at: {_DB_PATH}")


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
