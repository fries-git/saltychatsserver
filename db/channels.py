import copy
import json
import os
import threading
from typing import Dict, List, Optional, Tuple

from . import users
from . import threads
from .database import init_db, execute, fetchone, fetchall, _json_dumps, _json_loads, get_connection
from .emoji_utils import is_valid_emoji

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
channels_index = os.path.join(_MODULE_DIR, "channels.json")

DEFAULT_PERMISSIONS = {
    "view": ["owner"],
    "send": ["owner"],
    "delete": ["owner"],
    "delete_own": ["user"],
    "edit_own": ["user"],
    "react": ["user"],
    "pin": ["owner"],
    "create_thread": ["owner"]
}

DEFAULT_CHANNELS = [
    {
        "type": "text",
        "name": "general",
        "description": "General chat channel for everyone",
        "permissions": {
            "view": ["user"],
            "send": ["user"],
            "delete": ["admin", "moderator"],
            "create_thread": ["user"]
        }
    }
]

_global_lock = threading.RLock()
_permission_cache: Dict[str, dict] = {}
_permission_cache_valid: bool = False


def _invalidate_permission_cache():
    global _permission_cache_valid
    _permission_cache_valid = False


def _get_channel_permissions_cached(channel_name: str) -> Optional[dict]:
    global _permission_cache, _permission_cache_valid
    if not _permission_cache_valid:
        with _global_lock:
            channels_list = _get_channels()
            _permission_cache = {ch["name"]: ch.get("permissions", {}) for ch in channels_list if ch.get("name")}
            _permission_cache_valid = True
    return _permission_cache.get(channel_name)


_channels_cache: List[dict] = []
_channels_loaded: bool = False


def _load_channels_index() -> List[dict]:
    global _channels_cache, _channels_loaded
    init_db()
    try:
        channels_data = fetchall("SELECT * FROM channels ORDER BY position")
        if channels_data:
            _channels_cache = []
            for ch in channels_data:
                channel_obj = {
                    "type": ch.get("type", "text"),
                    "permissions": _json_loads(ch.get("permissions")) or {},
                    "position": ch.get("position", 0)
                }
                if ch.get("name"):
                    channel_obj["name"] = ch["name"]
                if ch.get("description"):
                    channel_obj["description"] = ch["description"]
                if ch.get("display_name"):
                    channel_obj["display_name"] = ch["display_name"]
                if ch.get("size"):
                    channel_obj["size"] = ch["size"]
                _channels_cache.append(channel_obj)
        else:
            _channels_cache = copy.deepcopy(DEFAULT_CHANNELS)
            for i, ch in enumerate(_channels_cache):
                execute(
                    "INSERT OR REPLACE INTO channels (name, type, description, display_name, permissions, position, size) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ch.get("name"), ch.get("type", "text"), ch.get("description"), ch.get("display_name"), _json_dumps(ch.get("permissions", {})), i, ch.get("size"))
                )
    except Exception:
        _channels_cache = copy.deepcopy(DEFAULT_CHANNELS)
    
    _channels_loaded = True
    return _channels_cache


def _save_channels_index(channels: List[dict]) -> None:
    global _channels_cache, _channels_loaded
    init_db()
    
    for i, ch in enumerate(channels):
        execute(
            "INSERT OR REPLACE INTO channels (name, type, description, display_name, permissions, position, size) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ch.get("name"), ch.get("type", "text"), ch.get("description"), ch.get("display_name"), _json_dumps(ch.get("permissions", {})), i, ch.get("size"))
        )
    
    _channels_cache = channels
    _channels_loaded = True
    _invalidate_permission_cache()


def _get_channels() -> List[dict]:
    if not _channels_loaded:
        _load_channels_index()
    return _channels_cache


def get_channel(channel_name: str) -> Optional[dict]:
    """Get channel data by channel name."""
    init_db()
    channels_list = _get_channels()
    for channel in channels_list:
        if channel.get("name") == channel_name:
            return copy.deepcopy(channel)
    return None


def get_channel_messages(channel_name: str, start, limit: int = 100) -> List[dict]:
    """Retrieve messages from a specific channel."""
    init_db()
    
    limit = min(max(limit, 1), 200)
    
    if isinstance(start, int):
        count = fetchone("SELECT COUNT(*) as cnt FROM messages WHERE channel = ? AND thread_id IS NULL", (channel_name,))
        total = count["cnt"] if count else 0
        
        if start < 0:
            start = 0
        
        end = total - start
        begin = max(0, end - limit)
        
        messages = fetchall(
            """SELECT * FROM messages 
               WHERE channel = ? AND thread_id IS NULL 
               ORDER BY timestamp ASC 
               LIMIT ? OFFSET ?""",
            (channel_name, limit, begin)
        )
    else:
        target = fetchone("SELECT timestamp FROM messages WHERE id = ? AND channel = ?", (start, channel_name))
        if not target:
            return []
        
        messages = fetchall(
            """SELECT * FROM messages 
               WHERE channel = ? AND thread_id IS NULL AND timestamp < ?
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (channel_name, target["timestamp"], limit)
        )
        messages = list(reversed(messages))
    
    if not messages:
        return []
    
    message_ids = [m["id"] for m in messages]
    placeholders = ",".join("?" * len(message_ids))
    reactions = fetchall(
        f"SELECT message_id, emoji, user_id FROM reactions WHERE message_id IN ({placeholders})",
        tuple(message_ids)
    )
    
    reactions_by_msg = {}
    for r in reactions:
        msg_id = r["message_id"]
        if msg_id not in reactions_by_msg:
            reactions_by_msg[msg_id] = []
        reactions_by_msg[msg_id].append(r)
    
    result = []
    for msg in messages:
        msg_copy = _process_message(msg, reactions_by_msg.get(msg["id"], []))
        result.append(msg_copy)
    
    return result


def get_channel_messages_around(channel_name: str, message_id: str, above: int = 50, below: int = 50) -> Tuple[Optional[List[dict]], Optional[int], Optional[int]]:
    """Get messages centered around a specific message ID."""
    init_db()
    
    above = min(max(above, 0), 200)
    below = min(max(below, 0), 200)
    
    target = fetchone("SELECT timestamp FROM messages WHERE id = ? AND channel = ?", (message_id, channel_name))
    if not target:
        return None, None, None
    
    target_ts = target["timestamp"]
    
    below_messages = fetchall(
        """SELECT * FROM messages 
           WHERE channel = ? AND thread_id IS NULL AND timestamp < ?
           ORDER BY timestamp DESC LIMIT ?""",
        (channel_name, target_ts, below)
    )
    
    target_msg = fetchone("SELECT * FROM messages WHERE id = ?", (message_id,))
    
    above_messages = fetchall(
        """SELECT * FROM messages 
           WHERE channel = ? AND thread_id IS NULL AND timestamp > ?
           ORDER BY timestamp ASC LIMIT ?""",
        (channel_name, target_ts, above)
    )
    
    messages = list(reversed(below_messages)) + [target_msg] + above_messages
    
    if not messages:
        return [], 0, 0
    
    message_ids = [m["id"] for m in messages if m]
    placeholders = ",".join("?" * len(message_ids))
    reactions = fetchall(
        f"SELECT message_id, emoji, user_id FROM reactions WHERE message_id IN ({placeholders})",
        tuple(message_ids)
    )
    
    reactions_by_msg = {}
    for r in reactions:
        msg_id = r["message_id"]
        if msg_id not in reactions_by_msg:
            reactions_by_msg[msg_id] = []
        reactions_by_msg[msg_id].append(r)
    
    result = []
    for msg in messages:
        if msg:
            msg_copy = _process_message(msg, reactions_by_msg.get(msg["id"], []))
            result.append(msg_copy)
    
    start_idx = below
    end_idx = start_idx + len(result)
    
    return result, start_idx, end_idx


def _process_message(msg: dict, reactions: List[dict]) -> dict:
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
    
    webhook = _json_loads(msg.get("webhook"))
    if webhook:
        msg_copy["webhook"] = webhook
    
    msg_copy["type"] = "message"
    
    return msg_copy


def convert_messages_to_user_format(messages: List[dict]) -> List[dict]:
    """Convert messages with user IDs to messages with usernames for sending to clients."""
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


def save_channel_message(channel_name: str, message: dict) -> bool:
    """Save a message to a specific channel."""
    init_db()

    message_id = message.get("id")
    if not message_id:
        return False

    execute(
        """INSERT INTO messages
            (id, channel, thread_id, user_id, content, timestamp,
            reply_to_id, reply_to_user, attachments, embeds, webhook, interaction)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (message_id, channel_name, message.get("user"), message.get("content", ""),
         message.get("timestamp"), message.get("reply_to", {}).get("id"),
         message.get("reply_to", {}).get("user"),
         _json_dumps(message.get("attachments")),
         _json_dumps(message.get("embeds")),
         _json_dumps(message.get("webhook")),
         _json_dumps(message.get("interaction")))
    )

    return True


def get_all_channels_for_roles(roles: List[str]) -> List[dict]:
    """Get all channels available for the specified roles."""
    init_db()
    result = []
    
    for channel in _get_channels():
        permissions = channel.get("permissions", {})
        view_roles = permissions.get("view", [])
        if not any(role in view_roles for role in roles):
            continue
        
        channel_copy = copy.deepcopy(channel)
        if channel_copy.get("type") != "forum":
            result.append(channel_copy)
            continue
        
        channel_name = channel_copy.get("name", "")
        if not channel_name:
            continue
        
        channel_threads = threads.get_channel_threads(channel_name)
        thread_results = []
        for thread in channel_threads:
            thread_copy = copy.deepcopy(thread)
            thread_copy["created_by"] = users.get_username_by_id(thread_copy["created_by"])
            thread_copy["participants"] = [
                users.get_username_by_id(p) for p in thread_copy.get("participants", [])
            ]
            thread_results.append(thread_copy)
        channel_copy["threads"] = thread_results
        result.append(channel_copy)
    
    return result


def edit_channel_message(channel_name: str, message_id: str, new_content: str, embeds=None) -> bool:
    """Edit a message in a specific channel."""
    init_db()
    
    existing = fetchone("SELECT id FROM messages WHERE id = ? AND channel = ?", (message_id, channel_name))
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


def get_channel_message(channel_name: str, message_id: str) -> Optional[dict]:
    """Retrieve a specific message from a channel by its ID."""
    init_db()
    
    msg = fetchone("SELECT * FROM messages WHERE id = ? AND channel = ?", (message_id, channel_name))
    if not msg:
        return None
    
    reactions = fetchall("SELECT emoji, user_id FROM reactions WHERE message_id = ?", (message_id,))
    return _process_message(msg, reactions)


def does_user_have_permission(channel_name: str, user_roles: List[str], permission_type: str) -> bool:
    """Check if a user with the given roles has a specific permission for a channel."""
    if "owner" in user_roles:
        return True
    
    permissions = _get_channel_permissions_cached(channel_name)
    if not permissions:
        allowed_roles = DEFAULT_PERMISSIONS.get(permission_type, [])
    else:
        allowed_roles = permissions.get(permission_type)
        if allowed_roles is None or allowed_roles == []:
            allowed_roles = DEFAULT_PERMISSIONS.get(permission_type, [])
    
    return any(role in allowed_roles for role in user_roles)


def delete_channel_message(channel_name: str, message_id: str) -> bool:
    """Delete a message from a channel."""
    init_db()
    
    result = execute("DELETE FROM messages WHERE id = ? AND channel = ?", (message_id, channel_name))
    return result.rowcount > 0


def get_channels() -> List[dict]:
    """Get all channels."""
    return _get_channels()


def create_channel(channel_name: str, channel_type: str = "text", description: str = None,
                   display_name: str = None, permissions: dict = None, size: dict = None) -> dict:
    """Create a new channel."""
    init_db()

    if permissions is None:
        permissions = DEFAULT_PERMISSIONS.copy()

    channel = {
        "name": channel_name,
        "type": channel_type,
        "description": description,
        "display_name": display_name,
        "permissions": permissions,
        "size": size
    }

    channels_list = _get_channels()
    position = len(channels_list)

    execute(
        "INSERT OR REPLACE INTO channels (name, type, description, display_name, permissions, position, size) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (channel_name, channel_type, description, display_name, _json_dumps(permissions), position, size)
    )

    channels_list.append(channel)
    _invalidate_permission_cache()

    return channel


def can_user_pin(channel_name: str, user_roles: List[str]) -> bool:
    """Check if a user can pin messages in a channel."""
    return does_user_have_permission(channel_name, user_roles, "pin")


def pin_channel_message(channel_name: str, message_id: str) -> bool:
    """Pin a message in a channel."""
    init_db()
    
    msg = fetchone("SELECT id FROM messages WHERE id = ? AND channel = ?", (message_id, channel_name))
    if not msg:
        return False
    
    execute("UPDATE messages SET pinned = 1 WHERE id = ?", (message_id,))
    execute(
        "INSERT OR IGNORE INTO pinned_messages (message_id, channel, thread_id, pinned_at) VALUES (?, ?, NULL, ?)",
        (message_id, channel_name, __import__("time").time())
    )
    
    return True


def unpin_channel_message(channel_name: str, message_id: str) -> bool:
    """Unpin a message in a channel."""
    init_db()
    
    execute("UPDATE messages SET pinned = 0 WHERE id = ?", (message_id,))
    execute("DELETE FROM pinned_messages WHERE message_id = ?", (message_id,))
    
    return True


def get_pinned_messages(channel_name: str) -> List[dict]:
    """Get all pinned messages for a channel."""
    init_db()
    
    pinned_ids = fetchall(
        "SELECT message_id FROM pinned_messages WHERE channel = ? AND thread_id IS NULL ORDER BY pinned_at DESC",
        (channel_name,)
    )
    
    messages = []
    for p in pinned_ids:
        msg = get_channel_message(channel_name, p["message_id"])
        if msg:
            messages.append(msg)
    
    return messages


def search_channel_messages(channel_name: str, query: str) -> List[dict]:
    """Search messages in a channel by content."""
    init_db()
    
    search_term = f"%{query.lower()}%"
    
    messages = fetchall(
        """SELECT * FROM messages 
           WHERE channel = ? AND thread_id IS NULL AND LOWER(content) LIKE ?
           ORDER BY timestamp DESC""",
        (channel_name, search_term)
    )
    
    result = []
    for msg in messages:
        reactions = fetchall("SELECT emoji, user_id FROM reactions WHERE message_id = ?", (msg["id"],))
        msg_copy = _process_message(msg, reactions)
        result.append(msg_copy)
    
    return result


def delete_channel(channel_name: str) -> bool:
    """Delete a channel and all its messages."""
    init_db()
    
    execute("DELETE FROM messages WHERE channel = ?", (channel_name,))
    result = execute("DELETE FROM channels WHERE name = ?", (channel_name,))
    
    if result.rowcount > 0:
        _channels_cache[:] = [ch for ch in _get_channels() if ch.get("name") != channel_name]
        _invalidate_permission_cache()
        return True
    return False


def set_channel_permissions(channel_name: str, role: str, permission: str, allow: bool = True) -> bool:
    """Set permissions for a role in a channel."""
    init_db()
    
    channel = get_channel(channel_name)
    if not channel:
        return False
    
    permissions = channel.get("permissions", {})
    if permission not in permissions:
        permissions[permission] = []
    
    if allow:
        if role not in permissions[permission]:
            permissions[permission].append(role)
    else:
        if role in permissions[permission]:
            permissions[permission].remove(role)
    
    execute(
        "UPDATE channels SET permissions = ? WHERE name = ?",
        (_json_dumps(permissions), channel_name)
    )
    
    _invalidate_permission_cache()
    return True


def get_channel_permissions(channel_name: str) -> Optional[dict]:
    """Get permissions for a channel."""
    return _get_channel_permissions_cached(channel_name)


def reorder_channel(channel_name: str, new_position: int) -> bool:
    """Reorder a channel to a new position."""
    init_db()
    
    channels_list = _get_channels()
    channel = get_channel(channel_name)
    if not channel:
        return False
    
    channels_list = [ch for ch in channels_list if ch.get("name") != channel_name]
    channels_list.insert(new_position, channel)
    
    for i, ch in enumerate(channels_list):
        execute("UPDATE channels SET position = ? WHERE name = ?", (i, ch["name"]))
    
    return True


def get_message_replies(channel_name: str, message_id: str, limit: int = 50) -> List[dict]:
    """Get replies to a message."""
    init_db()
    
    messages = fetchall(
        """SELECT * FROM messages 
           WHERE channel = ? AND thread_id IS NULL AND reply_to_id = ?
           ORDER BY timestamp ASC LIMIT ?""",
        (channel_name, message_id, limit)
    )
    
    result = []
    for msg in messages:
        reactions = fetchall("SELECT emoji, user_id FROM reactions WHERE message_id = ?", (msg["id"],))
        msg_copy = _process_message(msg, reactions)
        result.append(msg_copy)
    
    return result


def purge_messages(channel_name: str, count: int) -> int:
    """Purge a number of recent messages from a channel."""
    init_db()
    
    recent = fetchall(
        """SELECT id FROM messages 
           WHERE channel = ? AND thread_id IS NULL 
           ORDER BY timestamp DESC LIMIT ?""",
        (channel_name, count)
    )
    
    if not recent:
        return 0
    
    ids_to_delete = [m["id"] for m in recent]
    placeholders = ",".join("?" * len(ids_to_delete))
    result = execute(f"DELETE FROM messages WHERE id IN ({placeholders})", tuple(ids_to_delete))
    
    return result.rowcount


def can_user_delete_own(channel_name: str, user_roles: List[str]) -> bool:
    """Check if a user can delete their own messages."""
    return does_user_have_permission(channel_name, user_roles, "delete_own")


def can_user_edit_own(channel_name: str, user_roles: List[str]) -> bool:
    """Check if a user can edit their own messages."""
    return does_user_have_permission(channel_name, user_roles, "edit_own")


def can_user_react(channel_name: str, user_roles: List[str]) -> bool:
    """Check if a user can react to messages."""
    return does_user_have_permission(channel_name, user_roles, "react")


def add_reaction(channel_name: str, message_id: str, emoji_str: str, user_id: str) -> bool:
    """Add a reaction to a message."""
    init_db()
    
    if not is_valid_emoji(emoji_str):
        return False
    
    existing = fetchone("SELECT id FROM messages WHERE id = ? AND channel = ?", (message_id, channel_name))
    if not existing:
        return False
    
    try:
        execute(
            "INSERT INTO reactions (message_id, emoji, user_id, added_at) VALUES (?, ?, ?, ?)",
            (message_id, emoji_str, user_id, __import__("time").time())
        )
    except Exception:
        pass
    
    return True


def remove_reaction(channel_name: str, message_id: str, emoji_str: str, user_id: str) -> bool:
    """Remove a reaction from a message."""
    init_db()
    
    if not is_valid_emoji(emoji_str):
        return False
    
    result = execute(
        "DELETE FROM reactions WHERE message_id = ? AND emoji = ? AND user_id = ?",
        (message_id, emoji_str, user_id)
    )
    return result.rowcount > 0


def get_reactions(channel_name: str, message_id: str) -> Dict[str, List[str]]:
    """Get all reactions for a message."""
    init_db()
    
    reactions = fetchall(
        "SELECT emoji, user_id FROM reactions WHERE message_id = ?",
        (message_id,)
    )
    
    result = {}
    for r in reactions:
        emoji = r["emoji"]
        if emoji not in result:
            result[emoji] = []
        result[emoji].append(r["user_id"])
    
    return result


def get_reaction_users(channel_name: str, message_id: str, emoji_str: str) -> List[str]:
    """Get users who reacted with a specific emoji."""
    init_db()
    
    reactions = fetchall(
        "SELECT user_id FROM reactions WHERE message_id = ? AND emoji = ?",
        (message_id, emoji_str)
    )
    
    return [r["user_id"] for r in reactions]


def channel_exists(channel_name: str) -> bool:
    """Check if a channel exists."""
    init_db()
    
    channel = fetchone("SELECT name FROM channels WHERE name = ?", (channel_name,))
    return channel is not None


def update_channel(channel_name: str, updates: dict) -> bool:
    """Update channel properties."""
    init_db()

    channel = get_channel(channel_name)
    if not channel:
        return False

    if "description" in updates:
        execute("UPDATE channels SET description = ? WHERE name = ?", (updates["description"], channel_name))
    if "display_name" in updates:
        execute("UPDATE channels SET display_name = ? WHERE name = ?", (updates["display_name"], channel_name))
    if "permissions" in updates:
        execute("UPDATE channels SET permissions = ? WHERE name = ?", (_json_dumps(updates["permissions"]), channel_name))
    if "type" in updates:
        execute("UPDATE channels SET type = ? WHERE name = ?", (updates["type"], channel_name))
    if "name" in updates and updates["name"] != channel_name:
        execute("UPDATE channels SET name = ? WHERE name = ?", (updates["name"], channel_name))

    _invalidate_permission_cache()
    return True
