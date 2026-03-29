import copy
import json
import os
import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple

from . import users
from .database import init_db, execute, fetchone, fetchall, _json_dumps, _json_loads, get_connection
from .emoji_utils import is_valid_emoji

_lock = threading.RLock()
_threads_cache: Dict[str, dict] = {}


def _get_timestamp() -> float:
    return time.time()


def create_thread(parent_channel: str, name: str, creator: str) -> dict:
    """Create a new thread."""
    init_db()
    
    thread_id = str(uuid.uuid4())
    
    metadata = {
        "id": thread_id,
        "name": name,
        "parent_channel": parent_channel,
        "created_by": creator,
        "created_at": _get_timestamp(),
        "locked": False,
        "archived": False,
        "participants": [creator],
    }
    
    execute(
        """INSERT INTO threads (id, name, parent_channel, created_by, created_at, locked, archived, participants)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (thread_id, name, parent_channel, creator, metadata["created_at"], 0, 0, _json_dumps([creator]))
    )
    
    _threads_cache[thread_id] = metadata
    return copy.deepcopy(metadata)


def get_thread(thread_id: str) -> Optional[dict]:
    """Get thread metadata."""
    init_db()
    
    if thread_id in _threads_cache:
        return copy.deepcopy(_threads_cache[thread_id])
    
    row = fetchone("SELECT * FROM threads WHERE id = ?", (thread_id,))
    if not row:
        return None
    
    metadata = {
        "id": row["id"],
        "name": row["name"],
        "parent_channel": row["parent_channel"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "locked": bool(row["locked"]),
        "archived": bool(row["archived"]),
        "participants": _json_loads(row["participants"]) or [],
    }
    
    created_by = metadata.get("created_by")
    participants = metadata.get("participants", [])
    if created_by and created_by not in participants:
        participants.append(created_by)
        metadata["participants"] = participants
        execute("UPDATE threads SET participants = ? WHERE id = ?", (_json_dumps(participants), thread_id))
    
    _threads_cache[thread_id] = metadata
    return metadata


def get_channel_threads(channel_name: str) -> List[dict]:
    """Get all threads for a channel."""
    init_db()
    
    rows = fetchall("SELECT * FROM threads WHERE parent_channel = ?", (channel_name,))
    
    result = []
    for row in rows:
        metadata = {
            "id": row["id"],
            "name": row["name"],
            "parent_channel": row["parent_channel"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "locked": bool(row["locked"]),
            "archived": bool(row["archived"]),
            "participants": _json_loads(row["participants"]) or [],
        }
        result.append(metadata)
    
    return result


def delete_thread(thread_id: str) -> bool:
    """Delete a thread and all its messages."""
    init_db()
    
    execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
    result = execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    
    if thread_id in _threads_cache:
        del _threads_cache[thread_id]
    
    return result.rowcount > 0


def update_thread(thread_id: str, updates: dict) -> bool:
    """Update thread properties."""
    init_db()
    
    thread = get_thread(thread_id)
    if not thread:
        return False
    
    if "name" in updates:
        execute("UPDATE threads SET name = ? WHERE id = ?", (updates["name"], thread_id))
    if "locked" in updates:
        execute("UPDATE threads SET locked = ? WHERE id = ?", (1 if updates["locked"] else 0, thread_id))
    if "archived" in updates:
        execute("UPDATE threads SET archived = ? WHERE id = ?", (1 if updates["archived"] else 0, thread_id))
    
    if thread_id in _threads_cache:
        del _threads_cache[thread_id]
    
    return True


def save_thread_message(thread_id: str, message: dict) -> bool:
    """Save a message to a thread."""
    init_db()
    
    message_id = message.get("id")
    if not message_id:
        return False
    
    thread = get_thread(thread_id)
    if not thread:
        return False
    
    parent_channel = thread.get("parent_channel")
    
    execute(
        """INSERT INTO messages
            (id, channel, thread_id, user_id, content, timestamp,
            reply_to_id, reply_to_user, attachments, embeds, webhook, interaction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (message_id, parent_channel, thread_id, message.get("user"), message.get("content", ""),
         message.get("timestamp"), message.get("reply_to", {}).get("id"),
         message.get("reply_to", {}).get("user"),
         _json_dumps(message.get("attachments")),
         _json_dumps(message.get("embeds")),
         _json_dumps(message.get("webhook")),
         _json_dumps(message.get("interaction")))
    )

    return True


def get_thread_messages(thread_id: str, start=None, limit: int = 100) -> List[dict]:
    """Get messages from a thread."""
    init_db()
    
    limit = min(max(limit, 1), 200)
    
    if start is None:
        count = fetchone("SELECT COUNT(*) as cnt FROM messages WHERE thread_id = ?", (thread_id,))
        total = count["cnt"] if count else 0
        begin = max(0, total - limit)
    elif isinstance(start, int):
        if start < 0:
            start = 0
        count = fetchone("SELECT COUNT(*) as cnt FROM messages WHERE thread_id = ?", (thread_id,))
        total = count["cnt"] if count else 0
        end = total - start
        begin = max(0, end - limit)
    else:
        target = fetchone("SELECT timestamp FROM messages WHERE id = ? AND thread_id = ?", (start, thread_id))
        if not target:
            return []
        
        messages_before = fetchall(
            """SELECT * FROM messages 
               WHERE thread_id = ? AND timestamp < ?
               ORDER BY timestamp DESC LIMIT ?""",
            (thread_id, target["timestamp"], limit)
        )
        return list(reversed([_process_message(m) for m in messages_before]))
    
    messages = fetchall(
        """SELECT * FROM messages 
           WHERE thread_id = ? 
           ORDER BY timestamp ASC 
           LIMIT ? OFFSET ?""",
        (thread_id, limit, begin)
    )
    
    return [_process_message(m) for m in messages]


def get_thread_messages_around(thread_id: str, message_id: str, above: int = 50, below: int = 50) -> Tuple[Optional[List[dict]], Optional[int], Optional[int]]:
    """Get messages centered around a specific message ID."""
    init_db()
    
    above = min(max(above, 0), 200)
    below = min(max(below, 0), 200)
    
    target = fetchone("SELECT timestamp FROM messages WHERE id = ? AND thread_id = ?", (message_id, thread_id))
    if not target:
        return None, None, None
    
    target_ts = target["timestamp"]
    
    below_messages = fetchall(
        """SELECT * FROM messages 
           WHERE thread_id = ? AND timestamp < ?
           ORDER BY timestamp DESC LIMIT ?""",
        (thread_id, target_ts, below)
    )
    
    target_msg = fetchone("SELECT * FROM messages WHERE id = ?", (message_id,))
    
    above_messages = fetchall(
        """SELECT * FROM messages 
           WHERE thread_id = ? AND timestamp > ?
           ORDER BY timestamp ASC LIMIT ?""",
        (thread_id, target_ts, above)
    )
    
    messages = list(reversed(below_messages)) + [target_msg] + above_messages
    
    if not messages:
        return [], 0, 0
    
    result = [_process_message(m) for m in messages if m]
    
    start_idx = below
    end_idx = start_idx + len(result)
    
    return result, start_idx, end_idx


def get_thread_message(thread_id: str, message_id: str) -> Optional[dict]:
    """Get a specific message from a thread."""
    init_db()
    
    msg = fetchone("SELECT * FROM messages WHERE id = ? AND thread_id = ?", (message_id, thread_id))
    if not msg:
        return None
    
    return _process_message(msg)


def edit_thread_message(thread_id: str, message_id: str, new_content: str, embeds=None) -> bool:
    """Edit a message in a thread."""
    init_db()
    
    existing = fetchone("SELECT id FROM messages WHERE id = ? AND thread_id = ?", (message_id, thread_id))
    if not existing:
        return False
    
    if embeds is not None:
        execute(
            "UPDATE messages SET content = ?, edited = 1, embeds = ? WHERE id = ?",
            (new_content, _json_dumps(embeds), message_id)
        )
    else:
        execute("UPDATE messages SET content = ?, edited = 1 WHERE id = ?", (new_content, message_id))
    
    return True


def delete_thread_message(thread_id: str, message_id: str) -> bool:
    """Delete a message from a thread."""
    init_db()
    
    result = execute("DELETE FROM messages WHERE id = ? AND thread_id = ?", (message_id, thread_id))
    return result.rowcount > 0


def _process_message(msg: dict) -> dict:
    """Process a message dict, adding reactions and cleaning up fields."""
    msg_copy = {}
    
    msg_copy["id"] = msg.get("id")
    msg_copy["user"] = msg.get("user_id")
    msg_copy["content"] = msg.get("content")
    msg_copy["timestamp"] = msg.get("timestamp")
    
    if msg.get("reply_to_id") or msg.get("reply_to_user"):
        msg_copy["reply_to"] = {
            "id": msg.get("reply_to_id"),
            "user": msg.get("reply_to_user")
        }
    
    reactions = fetchall("SELECT emoji, user_id FROM reactions WHERE message_id = ?", (msg["id"],))
    
    reactions_dict = {}
    for r in reactions:
        emoji = r["emoji"]
        user_id = r["user_id"]
        if emoji not in reactions_dict:
            reactions_dict[emoji] = []
        reactions_dict[emoji].append(user_id)
    
    msg_copy["reactions"] = reactions_dict
    msg_copy["edited"] = bool(msg.get("edited", 0))
    msg_copy["pinned"] = bool(msg.get("pinned", 0))
    
    attachments = _json_loads(msg.get("attachments"))
    if attachments:
        msg_copy["attachments"] = attachments
    
    embeds = _json_loads(msg.get("embeds"))
    if embeds:
        msg_copy["embeds"] = embeds
    
    msg_copy["type"] = "message"
    
    return msg_copy


def convert_messages_to_user_format(messages: List[dict]) -> List[dict]:
    """Convert messages with user IDs to messages with usernames."""
    user_ids_needed = set()
    for msg in messages:
        if "user" in msg:
            user_ids_needed.add(msg["user"])
        if "reply_to" in msg and "user" in msg["reply_to"]:
            user_ids_needed.add(msg["reply_to"]["user"])
        if "reactions" in msg:
            for uid_list in msg["reactions"].values():
                user_ids_needed.update(uid_list)
    
    uid_to_name = {uid: users.get_username_by_id(uid) for uid in user_ids_needed}
    
    converted = []
    for msg in messages:
        msg_copy = msg.copy()
        
        if "user" in msg_copy:
            uid = msg_copy["user"]
            msg_copy["user"] = uid_to_name.get(uid) or uid
        
        if "reply_to" in msg_copy and "user" in msg_copy["reply_to"]:
            msg_copy["reply_to"] = msg_copy["reply_to"].copy()
            uid = msg_copy["reply_to"]["user"]
            msg_copy["reply_to"]["user"] = uid_to_name.get(uid) or uid
        
        if "reactions" in msg_copy:
            converted_reactions = {}
            for emo, uid_list in msg_copy["reactions"].items():
                converted_reactions[emo] = [uid_to_name.get(u) or u for u in uid_list]
            msg_copy["reactions"] = converted_reactions
        
        msg_copy.setdefault("pinned", False)
        msg_copy.setdefault("type", "message")
        
        converted.append(msg_copy)
    
    return converted


def thread_exists(thread_id: str) -> bool:
    """Check if a thread exists."""
    init_db()
    
    row = fetchone("SELECT id FROM threads WHERE id = ?", (thread_id,))
    return row is not None


def is_thread_locked(thread_id: str) -> bool:
    """Check if a thread is locked."""
    init_db()
    
    row = fetchone("SELECT locked FROM threads WHERE id = ?", (thread_id,))
    return bool(row["locked"]) if row else False


def is_thread_archived(thread_id: str) -> bool:
    """Check if a thread is archived."""
    init_db()
    
    row = fetchone("SELECT archived FROM threads WHERE id = ?", (thread_id,))
    return bool(row["archived"]) if row else False


def join_thread(thread_id: str, user_id: str) -> bool:
    """Add a user to a thread's participants."""
    init_db()
    
    thread = get_thread(thread_id)
    if not thread:
        return False
    
    participants = thread.get("participants", [])
    if user_id in participants:
        return True
    
    participants.append(user_id)
    execute("UPDATE threads SET participants = ? WHERE id = ?", (_json_dumps(participants), thread_id))
    
    if thread_id in _threads_cache:
        _threads_cache[thread_id]["participants"] = participants
    
    return True


def leave_thread(thread_id: str, user_id: str) -> bool:
    """Remove a user from a thread's participants."""
    init_db()
    
    thread = get_thread(thread_id)
    if not thread:
        return False
    
    participants = thread.get("participants", [])
    if user_id not in participants:
        return True
    
    participants.remove(user_id)
    execute("UPDATE threads SET participants = ? WHERE id = ?", (_json_dumps(participants), thread_id))
    
    if thread_id in _threads_cache:
        _threads_cache[thread_id]["participants"] = participants
    
    return True


def get_thread_participants(thread_id: str) -> List[str]:
    """Get participants of a thread."""
    thread = get_thread(thread_id)
    if not thread:
        return []
    return thread.get("participants", [])


def add_thread_reaction(thread_id: str, message_id: str, emoji_str: str, user_id: str) -> bool:
    """Add a reaction to a thread message."""
    init_db()
    
    if not is_valid_emoji(emoji_str):
        return False
    
    existing = fetchone("SELECT id FROM messages WHERE id = ? AND thread_id = ?", (message_id, thread_id))
    if not existing:
        return False
    
    try:
        execute(
            "INSERT INTO reactions (message_id, emoji, user_id, added_at) VALUES (?, ?, ?, ?)",
            (message_id, emoji_str, user_id, time.time())
        )
    except Exception:
        pass
    
    return True


def remove_thread_reaction(thread_id: str, message_id: str, emoji_str: str, user_id: str) -> bool:
    """Remove a reaction from a thread message."""
    init_db()
    
    if not is_valid_emoji(emoji_str):
        return False
    
    result = execute(
        "DELETE FROM reactions WHERE message_id = ? AND emoji = ? AND user_id = ?",
        (message_id, emoji_str, user_id)
    )
    return result.rowcount > 0
