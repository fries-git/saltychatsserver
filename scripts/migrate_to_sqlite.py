#!/usr/bin/env python3
"""
Migration script to convert JSONL message storage to SQLite.

This script:
1. Creates the SQLite database with proper schema
2. Migrates all channels from channels.json
3. Migrates all messages from db/channels/*.json files
4. Migrates all threads from db/threads/*.json files
5. Migrates all thread messages from db/threadMessages/*.jsonl files
6. Extracts reactions from messages and stores them in the reactions table

Usage:
    python scripts/migrate_to_sqlite.py [--backup] [--dry-run]

Options:
    --backup    Create backup of original files before migration
    --dry-run   Show what would be migrated without actually doing it
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "originchats.db"

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

-- Users table
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


def create_backup():
    """Create backup of original files."""
    backup_dir = DB_DIR / "backup" / f"backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup channels index
    channels_index = DB_DIR / "channels.json"
    if channels_index.exists():
        shutil.copy2(channels_index, backup_dir / "channels.json")
    
    # Backup channels directory
    channels_dir = DB_DIR / "channels"
    if channels_dir.exists():
        shutil.copytree(channels_dir, backup_dir / "channels")
    
    # Backup threads directory
    threads_dir = DB_DIR / "threads"
    if threads_dir.exists():
        shutil.copytree(threads_dir, backup_dir / "threads")
    
    # Backup threadMessages directory
    thread_messages_dir = DB_DIR / "threadMessages"
    if thread_messages_dir.exists():
        shutil.copytree(thread_messages_dir, backup_dir / "threadMessages")
    
    print(f"Backup created at: {backup_dir}")
    return backup_dir


def json_dumps(obj):
    """Safely serialize to JSON."""
    if obj is None:
        return None
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)


def load_jsonl(file_path):
    """Load a JSONL file and return list of objects."""
    messages = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        pass
    return messages


def load_json(file_path):
    """Load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def migrate_channels(conn, channels_data):
    """Migrate channels from channels.json."""
    cursor = conn.cursor()
    count = 0
    
    for i, channel in enumerate(channels_data):
        cursor.execute(
            """INSERT OR REPLACE INTO channels
               (name, type, description, permissions, position, size)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (channel.get("name"),
             channel.get("type", "text"),
             channel.get("description"),
             json_dumps(channel.get("permissions", {})),
             i,
             channel.get("size"))
        )
        count += 1
    
    return count


def migrate_messages(conn, messages, channel_name, thread_id=None):
    """Migrate messages and extract reactions."""
    cursor = conn.cursor()
    msg_count = 0
    reaction_count = 0
    
    for msg in messages:
        msg_id = msg.get("id")
        if not msg_id:
            continue
        
        reply_to = msg.get("reply_to") or {}
        
        cursor.execute(
            """INSERT OR REPLACE INTO messages
               (id, channel, thread_id, user_id, content, timestamp,
                edited, pinned, reply_to_id, reply_to_user, attachments, embeds, webhook, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id,
             channel_name,
             thread_id,
             msg.get("user"),
             msg.get("content", ""),
             msg.get("timestamp"),
             1 if msg.get("edited") else 0,
             1 if msg.get("pinned") else 0,
             reply_to.get("id"),
             reply_to.get("user"),
             json_dumps(msg.get("attachments")),
             json_dumps(msg.get("embeds")),
             json_dumps(msg.get("webhook")),
             msg.get("timestamp"))
        )
        msg_count += 1
        
        # Extract and migrate reactions
        reactions = msg.get("reactions", {})
        for emoji, user_ids in reactions.items():
            for user_id in user_ids:
                try:
                    cursor.execute(
                        """INSERT INTO reactions (message_id, emoji, user_id, added_at)
                           VALUES (?, ?, ?, ?)""",
                        (msg_id, emoji, user_id, msg.get("timestamp", time.time()))
                    )
                    reaction_count += 1
                except sqlite3.IntegrityError:
                    pass  # Duplicate reaction
        
        # Track pinned messages
        if msg.get("pinned"):
            cursor.execute(
                """INSERT OR IGNORE INTO pinned_messages (message_id, channel, thread_id, pinned_at)
                   VALUES (?, ?, ?, ?)""",
                (msg_id, channel_name, thread_id, msg.get("timestamp", time.time()))
            )
    
    return msg_count, reaction_count


def migrate_thread(conn, thread_data):
    """Migrate thread metadata."""
    cursor = conn.cursor()
    
    thread_id = thread_data.get("id")
    if not thread_id:
        return 0
    
    cursor.execute(
        """INSERT OR REPLACE INTO threads 
           (id, name, parent_channel, created_by, created_at, locked, archived, participants)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (thread_id,
         thread_data.get("name"),
         thread_data.get("parent_channel"),
         thread_data.get("created_by"),
         thread_data.get("created_at", time.time()),
         1 if thread_data.get("locked") else 0,
         1 if thread_data.get("archived") else 0,
         json_dumps(thread_data.get("participants", [])))
    )
    
    return 1


def run_migration(backup=False, dry_run=False):
    """Run the full migration."""
    print("=" * 60)
    print("JSONL to SQLite Migration")
    print("=" * 60)
    
    if dry_run:
        print("\n[DRY RUN] No changes will be made\n")
    
    # Create backup if requested
    if backup and not dry_run:
        create_backup()
    
    # Initialize database
    if not dry_run:
        if DB_PATH.exists():
            print(f"\nDatabase already exists at: {DB_PATH}")
            response = input("Do you want to overwrite it? (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                return
            DB_PATH.unlink()
        
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.executescript(SCHEMA)
        conn.commit()
    else:
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA)
    
    total_messages = 0
    total_reactions = 0
    total_channels = 0
    total_threads = 0
    
    # Migrate channels index
    print("\n[Migrating Channels Index]")
    channels_index = DB_DIR / "channels.json"
    channels_data = load_json(channels_index)
    if channels_data:
        if not dry_run:
            count = migrate_channels(conn, channels_data)
            conn.commit()
        else:
            count = len([c for c in channels_data if c.get("name")])
        total_channels = count
        print(f"  Channels: {count}")
    else:
        print("  No channels.json found, skipping...")
    
    # Migrate channel messages
    print("\n[Migrating Channel Messages]")
    channels_dir = DB_DIR / "channels"
    if channels_dir.exists():
        for channel_file in sorted(channels_dir.glob("*.json")):
            channel_name = channel_file.stem
            messages = load_jsonl(channel_file)
            if messages:
                if not dry_run:
                    msg_count, reaction_count = migrate_messages(conn, messages, channel_name)
                    conn.commit()
                else:
                    msg_count = len(messages)
                    reaction_count = sum(len(r) for m in messages for r in m.get("reactions", {}).values())
                total_messages += msg_count
                total_reactions += reaction_count
                print(f"  {channel_name}: {msg_count} messages, {reaction_count} reactions")
    
    # Migrate threads
    print("\n[Migrating Threads]")
    threads_dir = DB_DIR / "threads"
    if threads_dir.exists():
        for thread_file in sorted(threads_dir.glob("*.json")):
            thread_data = load_json(thread_file)
            if thread_data:
                if not dry_run:
                    count = migrate_thread(conn, thread_data)
                    conn.commit()
                else:
                    count = 1
                total_threads += count
                print(f"  {thread_file.stem}: migrated")
    
    # Migrate thread messages
    print("\n[Migrating Thread Messages]")
    thread_messages_dir = DB_DIR / "threadMessages"
    if thread_messages_dir.exists():
        for msg_file in sorted(thread_messages_dir.glob("*.jsonl")):
            thread_id = msg_file.stem
            messages = load_jsonl(msg_file)
            if messages:
                # Get parent channel from thread metadata
                thread_data = load_json(threads_dir / f"{thread_id}.json")
                parent_channel = thread_data.get("parent_channel", "general") if thread_data else "general"
                
                if not dry_run:
                    msg_count, reaction_count = migrate_messages(conn, messages, parent_channel, thread_id)
                    conn.commit()
                else:
                    msg_count = len(messages)
                    reaction_count = sum(len(r) for m in messages for r in m.get("reactions", {}).values())
                total_messages += msg_count
                total_reactions += reaction_count
                print(f"  Thread {thread_id}: {msg_count} messages, {reaction_count} reactions")
    
    # Migrate webhooks
    print("\n[Migrating Webhooks]")
    webhooks_file = DB_DIR / "webhooks.json"
    if webhooks_file.exists():
        webhooks_data = load_json(webhooks_file)
        if webhooks_data:
            webhook_count = 0
            for wh_id, wh_data in webhooks_data.items():
                if not dry_run:
                    conn.execute(
                        """INSERT OR REPLACE INTO webhooks (id, channel, name, token, created_by, created_at, avatar)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (wh_data.get("id"),
                         wh_data.get("channel"),
                         wh_data.get("name"),
                         wh_data.get("token"),
                         wh_data.get("created_by"),
                         wh_data.get("created_at"),
                         wh_data.get("avatar"))
                    )
                    conn.commit()
                webhook_count += 1
            print(f"  Webhooks: {webhook_count}")
    
    # Migrate users
    print("\n[Migrating Users]")
    users_file = DB_DIR / "users.json"
    if users_file.exists():
        users_data = load_json(users_file)
        if users_data:
            user_count = 0
            for user_id, user_data in users_data.items():
                if not dry_run:
                    conn.execute(
                        """INSERT OR REPLACE INTO users (id, username, roles, validator, nickname, status, created_at, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_id,
                        user_data.get("username"),
                        json_dumps(user_data.get("roles", [])),
                        user_data.get("validator"),
                        user_data.get("nickname"),
                        json_dumps(user_data.get("status")),
                        user_data.get("created_at"),
                        user_data.get("last_seen"))
                    )
                    conn.commit()
                user_count += 1
            print(f"  Users: {user_count}")
    
    # Migrate roles
    print("\n[Migrating Roles]")
    roles_file = DB_DIR / "roles.json"
    if roles_file.exists():
        roles_data = load_json(roles_file)
        if roles_data:
            role_count = 0
            for role_name, role_data in roles_data.items():
                if not dry_run:
                    conn.execute(
                        """INSERT OR REPLACE INTO roles (name, description, color, hoisted, permissions, self_assignable, category)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (role_name,
                         role_data.get("description"),
                         role_data.get("color"),
                         1 if role_data.get("hoisted") else 0,
                         json_dumps(role_data.get("permissions", {})),
                         1 if role_data.get("self_assignable") else 0,
                         role_data.get("category"))
                    )
                    conn.commit()
                role_count += 1
            print(f"  Roles: {role_count}")
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"  Channels:      {total_channels}")
    print(f"  Threads:       {total_threads}")
    print(f"  Messages:      {total_messages}")
    print(f"  Reactions:     {total_reactions}")
    
    if not dry_run:
        print(f"\nDatabase created at: {DB_PATH}")
        print(f"Database size: {DB_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print("\n[DRY RUN] No database was created")
    
    print("\nMigration complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate JSONL storage to SQLite")
    parser.add_argument("--backup", action="store_true", help="Create backup before migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without doing it")
    
    args = parser.parse_args()
    run_migration(backup=args.backup, dry_run=args.dry_run)
