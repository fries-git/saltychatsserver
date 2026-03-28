import copy
import threading
import time
import uuid
from typing import Dict, List, Optional

from .database import init_db, execute, fetchone, fetchall

_lock = threading.RLock()


def create_webhook(channel: str, name: str, created_by: str) -> Optional[dict]:
    """Create a new webhook for a channel. Returns the webhook data including the token."""
    init_db()
    
    with _lock:
        webhook_id = str(uuid.uuid4())
        token = str(uuid.uuid4()) + str(uuid.uuid4()).replace("-", "")
        
        webhook_data = {
            "id": webhook_id,
            "channel": channel,
            "name": name,
            "token": token,
            "created_by": created_by,
            "created_at": time.time(),
            "avatar": None
        }
        
        execute(
            "INSERT INTO webhooks (id, channel, name, token, created_by, created_at, avatar) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (webhook_id, channel, name, token, created_by, webhook_data["created_at"], None)
        )
        
        return webhook_data


def get_webhook(webhook_id: str) -> Optional[dict]:
    """Get a webhook by ID. Returns webhook data without the token for security."""
    init_db()
    
    row = fetchone("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))
    if row:
        return dict(row)
    return None


def get_webhook_by_token(token: str) -> Optional[dict]:
    """Get a webhook by its token (for incoming webhook requests). Returns full webhook data including token."""
    init_db()
    
    row = fetchone("SELECT * FROM webhooks WHERE token = ?", (token,))
    if row:
        return dict(row)
    return None


def get_webhooks_for_channel(channel: str) -> List[dict]:
    """Get all webhooks for a channel. Returns webhook data with webhook URLs but without tokens."""
    init_db()
    
    rows = fetchall("SELECT * FROM webhooks WHERE channel = ?", (channel,))
    return [dict(row) for row in rows]


def get_all_webhooks() -> List[dict]:
    """Get all webhooks. Returns webhook data with webhook URLs but without tokens."""
    init_db()
    
    rows = fetchall("SELECT * FROM webhooks")
    return [dict(row) for row in rows]


def delete_webhook(webhook_id: str) -> bool:
    """Delete a webhook by ID. Returns True if deleted, False if not found."""
    init_db()
    
    with _lock:
        result = execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
        return result.rowcount > 0


def update_webhook(webhook_id: str, updates: dict) -> Optional[dict]:
    """Update a webhook. Returns updated webhook data without token, or None if not found."""
    init_db()
    
    with _lock:
        webhook = fetchone("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))
        if not webhook:
            return None
        
        name = updates.get("name", webhook["name"])
        avatar = updates.get("avatar", webhook.get("avatar"))
        
        execute(
            "UPDATE webhooks SET name = ?, avatar = ? WHERE id = ?",
            (name, avatar, webhook_id)
        )
        
        result = dict(webhook)
        result["name"] = name
        result["avatar"] = avatar
        return result


def webhook_exists_for_channel(channel: str, webhook_id: str) -> bool:
    """Check if a webhook exists and belongs to a specific channel."""
    init_db()
    
    row = fetchone("SELECT id FROM webhooks WHERE id = ? AND channel = ?", (webhook_id, channel))
    return row is not None


def get_webhook_owner(webhook_id: str) -> Optional[str]:
    """Get the user ID of the webhook owner."""
    init_db()
    
    row = fetchone("SELECT created_by FROM webhooks WHERE id = ?", (webhook_id,))
    return row["created_by"] if row else None
