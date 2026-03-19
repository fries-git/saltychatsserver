from db import channels, users
from config_store import get_config_value
from handlers.websocket_utils import _get_ws_attr
from typing import TypeVar

T = TypeVar("T")


def error(error_message, match_cmd=None):
    if match_cmd:
        return {"cmd": "error", "src": match_cmd, "val": error_message}
    return {"cmd": "error", "val": error_message}


def config_value(server_data, *path: str, default: T) -> T:
    config = server_data.get("config") if isinstance(server_data, dict) else None
    return get_config_value(*path, default=default, config=config)


def require_user_id(ws, error_message: str = "User not authenticated"):
    user_id = _get_ws_attr(ws, "user_id")
    if not user_id:
        return None, error(error_message)
    return user_id, None


def require_user_roles(user_id, *, requiredRoles=[], forbiddenRoles=[], missing_roles_message="User roles not found"):
    user_roles = users.get_user_roles(user_id)
    for role in requiredRoles:
        if not user_roles or role not in user_roles:
            return None, error(f"Access denied: '{role}' role required")
    if not user_roles:
        return None, error(missing_roles_message)
    return user_roles, None


def require_text_channel_access(user_id, channel_name):
    if not channel_name:
        return None, error("Channel name not provided")
    user_data = users.get_user(user_id)
    if not user_data:
        return None, error("User not found")
    allowed_channels = channels.get_all_channels_for_roles(user_data.get("roles", []))
    allowed_text_channel_names = [c.get("name") for c in allowed_channels if c.get("type") == "text"]
    if channel_name not in allowed_text_channel_names:
        return None, error("Access denied to this channel")
    channel_info = channels.get_channel(channel_name)
    if channel_info and channel_info.get("type") != "text":
        return None, error("Cannot use this command in this channel type")
    return user_data, None


def get_thread_context(thread_id, user_id, user_roles, require_view=True):
    from db import threads
    thread_data = threads.get_thread(thread_id)
    if not thread_data:
        return None, ("Thread not found", "thread_id")
    if threads.is_thread_locked(thread_id):
        return None, ("This thread is locked", "thread_id")
    if threads.is_thread_archived(thread_id):
        return None, ("This thread is archived", "thread_id")
    parent_channel = thread_data.get("parent_channel")
    if require_view:
        if not channels.does_user_have_permission(parent_channel, user_roles, "view"):
            return None, ("You do not have permission to view this thread", "thread_id")
    return {"thread": thread_data, "parent_channel": parent_channel}, None


def get_channel_or_thread_context(channel_name, thread_id, user_id, user_roles, require_send=False):
    if thread_id:
        ctx, err = get_thread_context(thread_id, user_id, user_roles, require_view=True)
        if err:
            return None, err
        if not ctx:
            return None, ("Thread not found", "thread")
        ctx["is_thread"] = True
        return ctx, None
    elif channel_name:
        if not channels.channel_exists(channel_name):
            return None, ("Channel not found", "channel")
        if require_send:
            if not channels.does_user_have_permission(channel_name, user_roles, "send"):
                return None, ("You do not have permission to send messages in this channel", "channel")
        return {"channel": channel_name, "is_thread": False}, None
    else:
        return None, ("Channel or thread_id required", "channel")


def require_voice_channel_access(user_id, channel_name, match_cmd):
    if not channel_name:
        return None, error("Channel name is required", match_cmd)
    user_data = users.get_user(user_id)
    if not user_data:
        return None, error("User not found", match_cmd)
    user_roles = user_data.get("roles", [])
    if not channels.does_user_have_permission(channel_name, user_roles, "view"):
        return None, error("You do not have permission to access this voice channel", match_cmd)
    channel_info = channels.get_channel(channel_name)
    if not channel_info or channel_info.get("type") != "voice":
        return None, error("This is not a voice channel", match_cmd)
    return {"user_data": user_data, "channel_info": channel_info}, None


def require_voice_channel_membership(ws, server_data, match_cmd):
    _ws_data = server_data.get("_ws_data", {}) if server_data else {}
    ws_data = _ws_data.get(id(ws), {})
    user_id = ws_data.get("user_id")
    if not user_id:
        return None, None, error("Authentication required", match_cmd)
    if not server_data:
        return None, None, error("Server data not available", match_cmd)
    voice_channels = server_data.get("voice_channels", {})
    current_channel = ws_data.get("voice_channel")
    if not current_channel:
        return None, None, error("You are not in a voice channel", match_cmd)
    if current_channel not in voice_channels:
        ws_data["voice_channel"] = None
        return None, None, error("Voice channel no longer exists", match_cmd)
    if user_id not in voice_channels[current_channel]:
        ws_data["voice_channel"] = None
        return None, None, error("You are not in this voice channel", match_cmd)
    return user_id, current_channel, None


def build_voice_participant_data(user_id, username, peer_id, muted, include_peer_id=True):
    data = {"id": user_id, "username": username, "muted": muted}
    if include_peer_id:
        data["peer_id"] = peer_id
    return data


def validate_type(value, expected_type):
    match expected_type:
        case "str": return isinstance(value, str)
        case "int": return isinstance(value, int) and not isinstance(value, bool)
        case "float": return isinstance(value, (int, float)) and not isinstance(value, bool)
        case "bool": return isinstance(value, bool)
        case "enum": return isinstance(value, str)
        case _: return False


def validate_option_value(option_name, value, option):
    if not validate_type(value, option.type):
        return False, f"Invalid type for argument '{option_name}': expected {option.type}, got {type(value).__name__}"
    if option.type == "enum":
        if not option.choices:
            return False, f"Enum argument '{option_name}' has no choices configured"
        if value not in option.choices:
            allowed_values = ", ".join(option.choices)
            return False, f"Invalid value for argument '{option_name}': expected one of [{allowed_values}], got '{value}'"
    return True, None


def validate_embed(embed: dict) -> tuple[bool, str | None]:
    if not isinstance(embed, dict):
        return False, "Embed must be an object"

    if len(embed) > 25:
        return False, "Embed cannot have more than 25 fields"

    if "title" in embed:
        if not isinstance(embed["title"], str):
            return False, "Embed title must be a string"
        if len(embed["title"]) > 256:
            return False, "Embed title cannot exceed 256 characters"

    if "description" in embed:
        if not isinstance(embed["description"], str):
            return False, "Embed description must be a string"
        if len(embed["description"]) > 4096:
            return False, "Embed description cannot exceed 4096 characters"

    if "url" in embed:
        if not isinstance(embed["url"], str):
            return False, "Embed url must be a string"

    if "color" in embed:
        if not isinstance(embed["color"], int):
            return False, "Embed color must be an integer"
        if embed["color"] < 0 or embed["color"] > 16777215:
            return False, "Embed color must be between 0 and 16777215"

    if "timestamp" in embed:
        if not isinstance(embed["timestamp"], str):
            return False, "Embed timestamp must be a string"

    if "author" in embed:
        author = embed["author"]
        if not isinstance(author, dict):
            return False, "Embed author must be an object"
        if "name" in author:
            if not isinstance(author["name"], str):
                return False, "Embed author name must be a string"
            if len(author["name"]) > 256:
                return False, "Embed author name cannot exceed 256 characters"
        if "url" in author and not isinstance(author["url"], str):
            return False, "Embed author url must be a string"
        if "icon_url" in author and not isinstance(author["icon_url"], str):
            return False, "Embed author icon_url must be a string"

    if "footer" in embed:
        footer = embed["footer"]
        if not isinstance(footer, dict):
            return False, "Embed footer must be an object"
        if "text" in footer:
            if not isinstance(footer["text"], str):
                return False, "Embed footer text must be a string"
            if len(footer["text"]) > 2048:
                return False, "Embed footer text cannot exceed 2048 characters"
        if "icon_url" in footer and not isinstance(footer["icon_url"], str):
            return False, "Embed footer icon_url must be a string"

    if "image" in embed:
        image = embed["image"]
        if not isinstance(image, dict):
            return False, "Embed image must be an object"
        if "url" in image and not isinstance(image["url"], str):
            return False, "Embed image url must be a string"

    if "thumbnail" in embed:
        thumbnail = embed["thumbnail"]
        if not isinstance(thumbnail, dict):
            return False, "Embed thumbnail must be an object"
        if "url" in thumbnail and not isinstance(thumbnail["url"], str):
            return False, "Embed thumbnail url must be a string"

    if "fields" in embed:
        fields = embed["fields"]
        if not isinstance(fields, list):
            return False, "Embed fields must be an array"
        if len(fields) > 25:
            return False, "Embed cannot have more than 25 fields"

        for i, field in enumerate(fields):
            if not isinstance(field, dict):
                return False, f"Embed field {i} must be an object"
            if "name" not in field:
                return False, f"Embed field {i} is missing required 'name'"
            if "value" not in field:
                return False, f"Embed field {i} is missing required 'value'"
            if not isinstance(field["name"], str):
                return False, f"Embed field {i} name must be a string"
            if not isinstance(field["value"], str):
                return False, f"Embed field {i} value must be a string"
            if len(field["name"]) > 256:
                return False, f"Embed field {i} name cannot exceed 256 characters"
            if len(field["value"]) > 1024:
                return False, f"Embed field {i} value cannot exceed 1024 characters"
            if "inline" in field and not isinstance(field["inline"], bool):
                return False, f"Embed field {i} inline must be a boolean"

    total_chars = 0
    if "title" in embed:
        total_chars += len(embed["title"])
    if "description" in embed:
        total_chars += len(embed["description"])
    if "fields" in embed:
        for field in embed["fields"]:
            total_chars += len(field.get("name", ""))
            total_chars += len(field.get("value", ""))
    if "footer" in embed and "text" in embed["footer"]:
        total_chars += len(embed["footer"]["text"])
    if "author" in embed and "name" in embed["author"]:
        total_chars += len(embed["author"]["name"])

    if total_chars > 6000:
        return False, "Embed total characters cannot exceed 6000"

    return True, None


def validate_embeds(embeds: list) -> tuple[bool, str | None]:
    if not isinstance(embeds, list):
        return False, "Embeds must be an array"

    if len(embeds) > 10:
        return False, "Cannot have more than 10 embeds"

    for i, embed in enumerate(embeds):
        is_valid, error = validate_embed(embed)
        if not is_valid:
            return False, f"Embed {i}: {error}"

    return True, None
