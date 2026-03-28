import time
import uuid
from typing import Dict, List, Optional, Tuple, Any

from .database import (
    init_db, execute, fetchone, fetchall,
    _json_dumps, _json_loads, get_connection
)


def save_message(
    channel: str,
    user_id: str,
    content: str,
    message_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    reply_to_id: Optional[str] = None,
    reply_to_user: Optional[str] = None,
    attachments: Optional[List] = None,
    embeds: Optional[Dict] = None,
    timestamp: Optional[float] = None
) -> str:
    """Save a new message to the database."""
    init_db()
    
    if message_id is None:
        message_id = str(uuid.uuid4())
    if timestamp is None:
        timestamp = time.time()
    
    execute(
        """INSERT INTO messages 
           (id, channel, thread_id, user_id, content, timestamp, 
            reply_to_id, reply_to_user, attachments, embeds)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (message_id, channel, thread_id, user_id, content, timestamp,
         reply_to_id, reply_to_user, _json_dumps(attachments), _json_dumps(embeds))
    )
    
    return message_id


def get_message(message_id: str) -> Optional[Dict[str, Any]]:
    """Get a single message by ID with reactions."""
    init_db()
    
    msg = fetchone("SELECT * FROM messages WHERE id = ?", (message_id,))
    if not msg:
        return None
    
    reactions = fetchall(
        "SELECT emoji, user_id FROM reactions WHERE message_id = ?",
        (message_id,)
    )
    
    msg['reactions'] = _reactions_to_dict(reactions)
    msg['edited'] = bool(msg.get('edited', 0))
    msg['pinned'] = bool(msg.get('pinned', 0))
    msg['attachments'] = _json_loads(msg.get('attachments'))
    msg['embeds'] = _json_loads(msg.get('embeds'))
    
    return msg


def get_messages(
    channel: str,
    thread_id: Optional[str] = None,
    start: Optional[int] = 0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get messages from a channel or thread with pagination."""
    init_db()
    
    limit = min(max(limit, 1), 200)
    
    if thread_id:
        query = """SELECT * FROM messages 
                   WHERE thread_id = ? 
                   ORDER BY timestamp ASC 
                   LIMIT ? OFFSET ?"""
        params = (thread_id, limit, start)
    else:
        query = """SELECT * FROM messages 
                   WHERE channel = ? AND thread_id IS NULL 
                   ORDER BY timestamp ASC 
                   LIMIT ? OFFSET ?"""
        params = (channel, limit, start)
    
    messages = fetchall(query, params)
    
    if not messages:
        return []
    
    message_ids = [m['id'] for m in messages]
    placeholders = ','.join('?' * len(message_ids))
    
    reactions = fetchall(
        f"SELECT message_id, emoji, user_id FROM reactions WHERE message_id IN ({placeholders})",
        tuple(message_ids)
    )
    
    reactions_by_msg = {}
    for r in reactions:
        msg_id = r['message_id']
        if msg_id not in reactions_by_msg:
            reactions_by_msg[msg_id] = []
        reactions_by_msg[msg_id].append(r)
    
    for msg in messages:
        msg_reactions = reactions_by_msg.get(msg['id'], [])
        msg['reactions'] = _reactions_to_dict(msg_reactions)
        msg['edited'] = bool(msg.get('edited', 0))
        msg['pinned'] = bool(msg.get('pinned', 0))
        msg['attachments'] = _json_loads(msg.get('attachments'))
        msg['embeds'] = _json_loads(msg.get('embeds'))
    
    return messages


def get_messages_around(
    channel: str,
    message_id: str,
    above: int = 50,
    below: int = 50,
    thread_id: Optional[str] = None
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[int], Optional[int]]:
    """Get messages centered around a specific message ID."""
    init_db()
    
    above = min(max(above, 0), 200)
    below = min(max(below, 0), 200)
    
    target = fetchone(
        "SELECT timestamp FROM messages WHERE id = ?",
        (message_id,)
    )
    
    if not target:
        return None, None, None
    
    target_ts = target['timestamp']
    
    if thread_id:
        count_query = "SELECT COUNT(*) as cnt FROM messages WHERE thread_id = ?"
        count_params = (thread_id,)
        range_query = """SELECT * FROM messages 
                         WHERE thread_id = ? AND timestamp BETWEEN ? AND ?
                         ORDER BY timestamp ASC"""
        range_params = (thread_id, target_ts - below * 0.001, target_ts + above * 0.001)
    else:
        count_query = "SELECT COUNT(*) as cnt FROM messages WHERE channel = ? AND thread_id IS NULL"
        count_params = (channel,)
        range_query = """SELECT * FROM messages 
                         WHERE channel = ? AND thread_id IS NULL AND timestamp BETWEEN ? AND ?
                         ORDER BY timestamp ASC"""
        range_params = (channel, target_ts - below * 0.001, target_ts + above * 0.001)
    
    conn = get_connection()
    cursor = conn.execute(range_query, range_params)
    messages = [dict(row) for row in cursor.fetchall()]
    
    if not messages:
        return [], 0, 0
    
    message_ids = [m['id'] for m in messages]
    placeholders = ','.join('?' * len(message_ids))
    
    reactions = fetchall(
        f"SELECT message_id, emoji, user_id FROM reactions WHERE message_id IN ({placeholders})",
        tuple(message_ids)
    )
    
    reactions_by_msg = {}
    for r in reactions:
        msg_id = r['message_id']
        if msg_id not in reactions_by_msg:
            reactions_by_msg[msg_id] = []
        reactions_by_msg[msg_id].append(r)
    
    for msg in messages:
        msg_reactions = reactions_by_msg.get(msg['id'], [])
        msg['reactions'] = _reactions_to_dict(msg_reactions)
        msg['edited'] = bool(msg.get('edited', 0))
        msg['pinned'] = bool(msg.get('pinned', 0))
        msg['attachments'] = _json_loads(msg.get('attachments'))
        msg['embeds'] = _json_loads(msg.get('embeds'))
    
    start_idx = 0
    for i, msg in enumerate(messages):
        if msg['id'] == message_id:
            start_idx = i
            break
    
    end_idx = start_idx + len(messages)
    
    return messages, start_idx, end_idx


def edit_message(
    message_id: str,
    new_content: str,
    embeds: Optional[Dict] = None
) -> bool:
    """Edit a message's content."""
    init_db()
    
    existing = fetchone("SELECT id FROM messages WHERE id = ?", (message_id,))
    if not existing:
        return False
    
    if embeds is not None:
        execute(
            "UPDATE messages SET content = ?, edited = 1, embeds = ? WHERE id = ?",
            (new_content, _json_dumps(embeds), message_id)
        )
    else:
        execute(
            "UPDATE messages SET content = ?, edited = 1 WHERE id = ?",
            (new_content, message_id)
        )
    
    return True


def delete_message(message_id: str) -> bool:
    """Delete a message and its reactions."""
    init_db()
    
    result = execute("DELETE FROM messages WHERE id = ?", (message_id,))
    return result.rowcount > 0


def add_reaction(message_id: str, emoji: str, user_id: str) -> bool:
    """Add a reaction to a message."""
    init_db()
    
    existing = fetchone("SELECT id FROM messages WHERE id = ?", (message_id,))
    if not existing:
        return False
    
    try:
        execute(
            "INSERT INTO reactions (message_id, emoji, user_id, added_at) VALUES (?, ?, ?, ?)",
            (message_id, emoji, user_id, time.time())
        )
        return True
    except Exception:
        return True  # Already exists (UNIQUE constraint)


def remove_reaction(message_id: str, emoji: str, user_id: str) -> bool:
    """Remove a reaction from a message."""
    init_db()
    
    result = execute(
        "DELETE FROM reactions WHERE message_id = ? AND emoji = ? AND user_id = ?",
        (message_id, emoji, user_id)
    )
    return result.rowcount > 0


def get_message_count(channel: str, thread_id: Optional[str] = None) -> int:
    """Get the total message count for a channel or thread."""
    init_db()
    
    if thread_id:
        row = fetchone("SELECT COUNT(*) as cnt FROM messages WHERE thread_id = ?", (thread_id,))
    else:
        row = fetchone("SELECT COUNT(*) as cnt FROM messages WHERE channel = ? AND thread_id IS NULL", (channel,))
    
    return row['cnt'] if row else 0


def pin_message(message_id: str) -> bool:
    """Pin a message."""
    init_db()
    
    msg = fetchone("SELECT id, channel, thread_id FROM messages WHERE id = ?", (message_id,))
    if not msg:
        return False
    
    execute("UPDATE messages SET pinned = 1 WHERE id = ?", (message_id,))
    
    execute(
        """INSERT OR IGNORE INTO pinned_messages (message_id, channel, thread_id, pinned_at)
           VALUES (?, ?, ?, ?)""",
        (message_id, msg['channel'], msg.get('thread_id'), time.time())
    )
    
    return True


def unpin_message(message_id: str) -> bool:
    """Unpin a message."""
    init_db()
    
    execute("UPDATE messages SET pinned = 0 WHERE id = ?", (message_id,))
    execute("DELETE FROM pinned_messages WHERE message_id = ?", (message_id,))
    
    return True


def get_pinned_messages(channel: str, thread_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all pinned messages for a channel or thread."""
    init_db()
    
    if thread_id:
        pinned_ids = fetchall(
            "SELECT message_id FROM pinned_messages WHERE channel = ? AND thread_id = ? ORDER BY pinned_at DESC",
            (channel, thread_id)
        )
    else:
        pinned_ids = fetchall(
            "SELECT message_id FROM pinned_messages WHERE channel = ? AND thread_id IS NULL ORDER BY pinned_at DESC",
            (channel,)
        )
    
    messages = []
    for p in pinned_ids:
        msg = get_message(p['message_id'])
        if msg:
            messages.append(msg)
    
    return messages


def search_messages(channel: str, query: str, thread_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search messages by content."""
    init_db()
    
    search_term = f"%{query.lower()}%"
    
    if thread_id:
        messages = fetchall(
            """SELECT * FROM messages 
               WHERE thread_id = ? AND LOWER(content) LIKE ?
               ORDER BY timestamp DESC""",
            (thread_id, search_term)
        )
    else:
        messages = fetchall(
            """SELECT * FROM messages 
               WHERE channel = ? AND thread_id IS NULL AND LOWER(content) LIKE ?
               ORDER BY timestamp DESC""",
            (channel, search_term)
        )
    
    for msg in messages:
        msg['edited'] = bool(msg.get('edited', 0))
        msg['pinned'] = bool(msg.get('pinned', 0))
        msg['attachments'] = _json_loads(msg.get('attachments'))
        msg['embeds'] = _json_loads(msg.get('embeds'))
        msg_reactions = fetchall(
            "SELECT emoji, user_id FROM reactions WHERE message_id = ?",
            (msg['id'],)
        )
        msg['reactions'] = _reactions_to_dict(msg_reactions)
    
    return messages


def _reactions_to_dict(reactions: List[Dict]) -> Dict[str, List[str]]:
    """Convert reaction list to emoji -> user_ids dict."""
    result: Dict[str, List[str]] = {}
    for r in reactions:
        emoji = r['emoji']
        user_id = r['user_id']
        if emoji not in result:
            result[emoji] = []
        result[emoji].append(user_id)
    return result
