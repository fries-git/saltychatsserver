import copy
import os
import secrets
import threading
import sys
from typing import Dict, Optional

from .database import init_db, execute, fetchone, fetchall, _json_dumps, _json_loads
from . import roles

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import Logger
from config_store import get_config_value

_lock = threading.RLock()

ALLOWED_STATUSES = ["online", "idle", "dnd", "offline"]
DEFAULT_STATUS = {"status": "online", "text": ""}


def _process_user(row):
    """Convert database row to user dict."""
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "roles": _json_loads(row.get("roles")) or [],
        "validator": row.get("validator"),
        "nickname": row.get("nickname"),
        "status": _json_loads(row.get("status")) or DEFAULT_STATUS,
        "created_at": row.get("created_at"),
        "last_seen": row.get("last_seen")
    }


def user_exists(user_id):
    """Check if a user exists in the users database."""
    init_db()
    row = fetchone("SELECT id FROM users WHERE id = ?", (user_id,))
    return row is not None


def get_user(user_id):
    """Get user data by user ID."""
    init_db()
    row = fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
    return _process_user(row)


def add_user(user_id, username=None):
    """Add a new user to the users database."""
    init_db()
    
    with _lock:
        if user_exists(user_id):
            return False
        
        user_data = get_config_value("DB", "users", "default", default={}).copy()
        
        if username:
            user_data["username"] = username
        elif "username" not in user_data:
            user_data["username"] = user_id
        
        execute(
            "INSERT INTO users (id, username, roles, validator, nickname, status, created_at, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id,
             user_data.get("username"),
             _json_dumps(user_data.get("roles", [])),
             user_data.get("validator"),
             user_data.get("nickname"),
             _json_dumps(user_data.get("status", DEFAULT_STATUS)),
             user_data.get("created_at"),
             user_data.get("last_seen"))
        )
        return True


def get_user_roles(user_id):
    """Get the roles of a user."""
    user = get_user(user_id)
    if user:
        return user.get("roles", [])
    return []


def get_users():
    """Get all users from the users database."""
    init_db()
    
    rows = fetchall("SELECT * FROM users")
    user_arr = []
    
    for row in rows:
        user_data = _process_user(row)
        if not user_data:
            continue
        
        if "banned" in user_data.get("roles", []):
            continue
        
        user_roles = user_data.get("roles", [])
        color = None
        if user_roles:
            first_role_name = user_roles[0]
            first_role_data = roles.get_role(first_role_name)
            if first_role_data:
                color = first_role_data.get("color")
        
        user_status = get_status(user_data["id"])
        username = user_data.get("username", user_data["id"])
        nickname = user_data.get("nickname")
        
        user_arr.append({
            "username": username,
            "nickname": nickname,
            "roles": list(user_roles),
            "color": color,
            "status": user_status
        })
    
    return user_arr


def count_users() -> int:
    """Count users in the users database."""
    init_db()

    ret = fetchone("SELECT COUNT(*) as cnt FROM users")
    if ret is None:
        return 0
    return ret["cnt"]

def save_user(user_id, user_data):
    """Save user data to the users database."""
    init_db()
    
    with _lock:
        execute(
            """UPDATE users SET username = ?, roles = ?, validator = ?, nickname = ?, status = ?, last_seen = ?
               WHERE id = ?""",
            (user_data.get("username"),
             _json_dumps(user_data.get("roles", [])),
             user_data.get("validator"),
             user_data.get("nickname"),
             _json_dumps(user_data.get("status", DEFAULT_STATUS)),
             user_data.get("last_seen"),
             user_id)
        )


def get_banned_users():
    """Get a list of all banned users."""
    init_db()
    
    rows = fetchall("SELECT * FROM users")
    banned = []
    
    for row in rows:
        user_data = _process_user(row)
        if "banned" in user_data.get("roles", []):
            banned.append(user_data.get("username", row["id"]))
    
    return banned


def is_user_banned(user_id):
    """Check if a user is banned by checking if they have the 'banned' role."""
    user = get_user(user_id)
    return user and "banned" in user.get("roles", [])


def ban_user(user_id):
    """Ban a user by giving them the 'banned' role."""
    with _lock:
        user = get_user(user_id)
        if user and "banned" not in user.get("roles", []):
            user["roles"].insert(0, "banned")
            save_user(user_id, user)
            return True
        return False


def unban_user(user_id):
    """Unban a user by removing the 'banned' role."""
    with _lock:
        user = get_user(user_id)
        if user and "banned" in user["roles"]:
            user["roles"].remove("banned")
            save_user(user_id, user)
            return True
        return False


def give_role(user_id, role):
    """Give a user a role."""
    with _lock:
        user = get_user(user_id)
        if user:
            user["roles"].append(role)
            save_user(user_id, user)
            return True
        return False


def set_user_roles(user_id, roles_list):
    """Set the exact roles for a user."""
    with _lock:
        user = get_user(user_id)
        if user:
            user["roles"] = roles_list
            save_user(user_id, user)
            return True
        return False


def remove_role(user_id, role):
    """Remove a role from a user."""
    with _lock:
        user = get_user(user_id)
        if user and role in user.get("roles", []):
            user["roles"].remove(role)
            save_user(user_id, user)
            return True
        return False


def remove_role_from_all_users(role):
    """Remove a role from all users that have it."""
    init_db()
    with _lock:
        rows = fetchall("SELECT id, roles FROM users WHERE roles LIKE ?", (f'%"{role}"%',))
        for row in rows:
            user_roles = _json_loads(row.get("roles")) or []
            if role in user_roles:
                user_roles.remove(role)
                execute("UPDATE users SET roles = ? WHERE id = ?", (_json_dumps(user_roles), row["id"]))


def remove_user_roles(user_id, roles_to_remove):
    """Remove multiple roles from a user."""
    with _lock:
        user = get_user(user_id)
        if not user:
            return False
        
        current_roles = user.get("roles", [])
        removed_any = False
        
        for role in roles_to_remove:
            if role in current_roles:
                current_roles.remove(role)
                removed_any = True
        
        if removed_any:
            user["roles"] = current_roles
            save_user(user_id, user)
            return True
        
        return False


def remove_user(user_id):
    """Remove a user from the users database."""
    with _lock:
        result = execute("DELETE FROM users WHERE id = ?", (user_id,))
        return result.rowcount > 0


def get_id_by_username(username):
    """Get a user's ID by their username."""
    init_db()
    
    row = fetchone("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    return row["id"] if row else None


def get_username_by_id(user_id):
    """Get a user's username by their ID."""
    user = get_user(user_id)
    if user:
        return user.get("username") or user_id
    return user_id


def update_user_username(user_id, new_username):
    """Update a user's username."""
    with _lock:
        user = get_user(user_id)
        if user:
            user["username"] = new_username
            execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
            return True
        return False


def generate_validator(user_id):
    """Generate a new random validator token for a user and store it."""
    with _lock:
        user = get_user(user_id)
        if not user:
            return None
        
        validator = secrets.token_urlsafe(32)
        user["validator"] = validator
        execute("UPDATE users SET validator = ? WHERE id = ?", (validator, user_id))
        return validator


def get_validator(user_id):
    """Get the stored validator token for a user."""
    user = get_user(user_id)
    return user.get("validator") if user else None


def get_user_id_by_validator(validator_token):
    """Get a user's ID by their validator token."""
    if not validator_token:
        return None
    
    row = fetchone("SELECT id FROM users WHERE validator = ?", (validator_token,))
    return row["id"] if row else None


def get_usernames_by_role(role_name):
    """Get all usernames that have a specific role."""
    init_db()
    
    rows = fetchall("SELECT * FROM users")
    usernames = []
    
    for row in rows:
        user_data = _process_user(row)
        if role_name in user_data.get("roles", []):
            usernames.append(user_data.get("username", row["id"]))
    
    return usernames


def set_nickname(user_id, nickname):
    """Set a user's display nickname."""
    with _lock:
        user = get_user(user_id)
        if not user:
            return False
        user["nickname"] = nickname
        execute("UPDATE users SET nickname = ? WHERE id = ?", (nickname, user_id))
        return True


def get_nickname(user_id):
    """Get a user's nickname."""
    user = get_user(user_id)
    return user.get("nickname") if user else None


def clear_nickname(user_id):
    """Clear a user's nickname."""
    with _lock:
        user = get_user(user_id)
        if not user:
            return False
        if "nickname" in user:
            execute("UPDATE users SET nickname = NULL WHERE id = ?", (user_id,))
        return True


def get_status(user_id) -> dict:
    """Get a user's status."""
    user = get_user(user_id)
    if user:
        return user.get("status", DEFAULT_STATUS)
    return DEFAULT_STATUS


def set_status(user_id, status, text=None):
    """Set a user's status."""
    if status not in ALLOWED_STATUSES:
        return False
    
    if text is not None and len(text) > 100:
        return False
    
    with _lock:
        user = get_user(user_id)
        if not user:
            return False
        
        status_data = {
            "status": status,
            "text": text[:100] if text else ""
        }
        execute("UPDATE users SET status = ? WHERE id = ?", (_json_dumps(status_data), user_id))
        return True


def reload_users():
    """Reload users from database (no-op for SQLite, kept for compatibility)."""
    init_db()
    return {row["id"]: _process_user(row) for row in fetchall("SELECT * FROM users")}
