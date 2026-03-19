from db import users
from handlers.websocket_utils import _get_ws_attr


def _error(error_message, match_cmd):
    if match_cmd:
        return {"cmd": "error", "src": match_cmd, "val": error_message}
    return {"cmd": "error", "val": error_message}


def _require_user_id(ws, error_message: str = "User not authenticated"):
    user_id: str = _get_ws_attr(ws, "user_id")
    if not user_id or not isinstance(user_id, str):
        return None, _error(error_message, None)
    return user_id, None


def _require_user_roles(user_id, *, requiredRoles=[], forbiddenRoles=[], missing_roles_message="User roles not found"):
    user_roles = users.get_user_roles(user_id)
    for role in requiredRoles:
        if not user_roles or role not in user_roles:
            return None, _error(f"Access denied: '{role}' role required", None)

    if not user_roles:
        return None, _error(missing_roles_message, None)
    return user_roles, None
