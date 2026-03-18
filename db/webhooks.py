import copy
import json
import os
import threading
import uuid
import time
from typing import Dict, List, Optional

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
webhooks_file = os.path.join(_MODULE_DIR, "webhooks.json")
DEFAULT_WEBHOOKS = {}

_lock = threading.RLock()

_webhooks_cache: Dict[str, dict] = {}
_webhooks_loaded: bool = False


def _load_webhooks() -> Dict[str, dict]:
    global _webhooks_cache, _webhooks_loaded
    try:
        with open(webhooks_file, "r") as f:
            _webhooks_cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _webhooks_cache = {}
    _webhooks_loaded = True
    return _webhooks_cache


def _save_webhooks(webhooks_dict: Dict[str, dict]) -> None:
    global _webhooks_cache, _webhooks_loaded
    tmp = webhooks_file + ".tmp"
    with open(tmp, "w") as f:
        json.dump(webhooks_dict, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, webhooks_file)
    _webhooks_cache = webhooks_dict
    _webhooks_loaded = True


def _get_webhooks_cache() -> Dict[str, dict]:
    if not _webhooks_loaded:
        _load_webhooks()
    return _webhooks_cache


def _ensure_storage():
    os.makedirs(_MODULE_DIR, exist_ok=True)
    if not os.path.exists(webhooks_file):
        tmp = webhooks_file + ".tmp"
        with open(tmp, "w") as f:
            json.dump(DEFAULT_WEBHOOKS, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, webhooks_file)


_ensure_storage()


def create_webhook(channel: str, name: str, created_by: str) -> Optional[dict]:
    """
    Create a new webhook for a channel.
    Returns the webhook data including the token.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        
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
        
        webhooks[webhook_id] = webhook_data
        _save_webhooks(webhooks)
        
        return copy.deepcopy(webhook_data)


def get_webhook(webhook_id: str) -> Optional[dict]:
    """
    Get a webhook by ID.
    Returns webhook data without the token for security.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        webhook = webhooks.get(webhook_id)
        if webhook:
            result = copy.deepcopy(webhook)
            return result
        return None


def get_webhook_by_token(token: str) -> Optional[dict]:
    """
    Get a webhook by its token (for incoming webhook requests).
    Returns full webhook data including token.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        for webhook_id, webhook in webhooks.items():
            if webhook.get("token") == token:
                return copy.deepcopy(webhook)
        return None


def get_webhooks_for_channel(channel: str) -> List[dict]:
    """
    Get all webhooks for a channel.
    Returns webhook data without tokens.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        result = []
        for webhook in webhooks.values():
            if webhook.get("channel") == channel:
                wh_copy = copy.deepcopy(webhook)
                del wh_copy["token"]
                result.append(wh_copy)
        return result


def get_all_webhooks() -> List[dict]:
    """
    Get all webhooks.
    Returns webhook data without tokens.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        result = []
        for webhook in webhooks.values():
            wh_copy = copy.deepcopy(webhook)
            del wh_copy["token"]
            result.append(wh_copy)
        return result


def delete_webhook(webhook_id: str) -> bool:
    """
    Delete a webhook by ID.
    Returns True if deleted, False if not found.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        if webhook_id in webhooks:
            del webhooks[webhook_id]
            _save_webhooks(webhooks)
            return True
        return False


def update_webhook(webhook_id: str, updates: dict) -> Optional[dict]:
    """
    Update a webhook.
    Returns updated webhook data without token, or None if not found.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        if webhook_id not in webhooks:
            return None
        
        webhook = webhooks[webhook_id]
        
        if "name" in updates:
            webhook["name"] = updates["name"]
        if "avatar" in updates:
            webhook["avatar"] = updates["avatar"]
        
        _save_webhooks(webhooks)
        
        result = copy.deepcopy(webhook)
        del result["token"]
        return result


def webhook_exists_for_channel(channel: str, webhook_id: str) -> bool:
    """
    Check if a webhook exists and belongs to a specific channel.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        webhook = webhooks.get(webhook_id)
        return webhook is not None and webhook.get("channel") == channel


def get_webhook_owner(webhook_id: str) -> Optional[str]:
    """
    Get the user ID of the webhook owner.
    """
    with _lock:
        webhooks = _get_webhooks_cache()
        webhook = webhooks.get(webhook_id)
        return webhook.get("created_by") if webhook else None