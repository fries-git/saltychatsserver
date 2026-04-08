from db import channels, threads, users
from handlers.websocket_utils import _get_ws_attr
from handlers.helpers.validation import (
    make_error as _error,
    require_user_id as _require_user_id,
    require_user_roles as _require_user_roles,
    get_channel_or_thread_context as _get_channel_or_thread_context,
    validate_embeds,
)
from handlers.helpers.mentions import (
    get_message_pings,
    validate_role_mentions_permissions,
)


async def handle_message_edit(ws, message, server_data):
    match_cmd = "message_edit"
    user_id = _get_ws_attr(ws, "user_id")
    if not user_id:
        return _error("Authentication required", match_cmd)

    if server_data and server_data.get("rate_limiter"):
        is_allowed, reason, wait_time = server_data["rate_limiter"].is_allowed(user_id)
        if not is_allowed:
            wait_time_ms = int(wait_time * 1000)
            return {"cmd": "rate_limit", "length": wait_time_ms}

    message_id = message.get("id")
    channel_name = message.get("channel")
    thread_id = message.get("thread_id")
    new_content = message.get("content")
    embeds = message.get("embeds")
    if not message_id or (not channel_name and not thread_id) or not new_content:
        return _error("Invalid message edit format", match_cmd)

    if embeds:
        is_valid, error_msg = validate_embeds(embeds)
        if not is_valid:
            return _error(error_msg, match_cmd)

    user_roles = users.get_user_roles(user_id)
    if not user_roles:
        return _error("User roles not found", match_cmd)

    ctx, err = await _get_channel_or_thread_context(channel_name, thread_id, user_id, user_roles)
    if err:
        msg, key = err
        return _error(msg, match_cmd)

    if not ctx:
        return _error("Channel or thread not found", match_cmd)

    is_thread = ctx["is_thread"]
    parent_channel = ctx.get("parent_channel") or ctx.get("channel")

    if is_thread and thread_id:
        msg_obj = threads.get_thread_message(thread_id, message_id)
    else:
        msg_obj = channels.get_channel_message(channel_name, message_id)

    if not msg_obj:
        return _error("Message not found or cannot be edited", match_cmd)

    if msg_obj.get("user") == user_id:
        if not channels.can_user_edit_own(parent_channel, user_roles):
            return _error(f"You do not have permission to edit your own message in this {'thread' if is_thread else 'channel'}", match_cmd)
    else:
        return _error("You do not have permission to edit this message", match_cmd)

    is_valid, error_msg = validate_role_mentions_permissions(new_content, user_roles)
    if not is_valid:
        return _error(error_msg, match_cmd)

    if is_thread and thread_id:
        if not threads.edit_thread_message(thread_id, message_id, new_content, embeds):
            return _error("Failed to edit message", match_cmd)
        if server_data:
            username = users.get_username_by_id(user_id)
            server_data["plugin_manager"].trigger_event("message_edit", ws, {
                "channel": parent_channel,
                "thread_id": thread_id,
                "id": message_id,
                "content": new_content,
                "user_id": user_id,
                "username": username
            }, server_data)
        edited_msg = threads.get_thread_message(thread_id, message_id)
        if edited_msg:
            edited_msg = threads.convert_messages_to_user_format([edited_msg])[0]
            pings = get_message_pings(new_content, user_roles)
            if pings.get("users") or pings.get("roles"):
                edited_msg["pings"] = pings
            if embeds:
                edited_msg["embeds"] = embeds
        return {"cmd": "message_edit", "id": message_id, "content": new_content, "message": edited_msg, "channel": parent_channel, "thread_id": thread_id, "global": True}
    else:
        if not channels.edit_channel_message(channel_name, message_id, new_content, embeds):
            return _error("Failed to edit message", match_cmd)
        if server_data:
            username = users.get_username_by_id(user_id)
            server_data["plugin_manager"].trigger_event("message_edit", ws, {
                "channel": channel_name,
                "thread_id": thread_id,
                "id": message_id,
                "content": new_content,
                "user_id": user_id,
                "username": username
            }, server_data)
        edited_msg = channels.get_channel_message(channel_name, message_id)
        if edited_msg:
            edited_msg = channels.convert_messages_to_user_format([edited_msg])[0]
            pings = get_message_pings(new_content, user_roles)
            if pings.get("users") or pings.get("roles"):
                edited_msg["pings"] = pings
            if embeds:
                edited_msg["embeds"] = embeds
    return {"cmd": "message_edit", "id": message_id, "content": new_content, "message": edited_msg, "channel": channel_name, "global": True}
