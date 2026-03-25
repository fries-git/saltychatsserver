from typing import Dict, Any, Optional
from pydantic import ValidationError
from schemas.attachment_schema import Attachment_upload, Attachment_delete, Attachment_get
from db import attachments as attachments_db
from handlers.rotur_api import has_permanent_upload
from handlers.messages.helpers import _error, _require_user_id
from handlers.websocket_utils import _get_ws_attr
from logger import Logger


def handle_attachment_upload(ws, message: Dict[str, Any], server_data: Dict[str, Any], match_cmd: str) -> Optional[Dict[str, Any]]:
    user_id, error = _require_user_id(ws, "Authentication required")
    if error or not user_id:
        return error

    username = _get_ws_attr(ws, "username", "")

    try:
        upload_cmd = Attachment_upload.model_validate(message)
    except ValidationError as e:
        return _error(f"Invalid attachment_upload command: {str(e)}", match_cmd)

    from db import channels
    if not channels.channel_exists(upload_cmd.channel):
        return _error("Channel does not exist", match_cmd)

    user_roles = _get_ws_attr(ws, "user_roles", [])
    if not channels.does_user_have_permission(upload_cmd.channel, user_roles, "send"):
        return _error("You don't have permission to send in this channel", match_cmd)

    is_permanent = has_permanent_upload(username)

    config = server_data.get("config", {})
    base_url = ""
    if "server" in config and "url" in config["server"]:
        base_url = config["server"]["url"].rstrip("/")

    attachment = attachments_db.save_attachment(
        file_data=upload_cmd.file,
        original_name=upload_cmd.name,
        mime_type=upload_cmd.mime_type,
        uploader_id=user_id,
        uploader_name=username,
        channel=upload_cmd.channel,
        permanent=is_permanent,
        custom_expires_in_days=upload_cmd.expires_in_days,
    )

    if not attachment:
        return _error("Failed to save attachment", match_cmd)

    attachment_info = attachments_db.get_attachment_info_for_client(attachment, base_url)

    Logger.success(f"Attachment uploaded: {attachment['id']} by {username}")

    return {
        "cmd": "attachment_uploaded",
        "attachment": attachment_info,
        "permanent": is_permanent,
    }


def handle_attachment_delete(ws, message: Dict[str, Any], server_data: Dict[str, Any], match_cmd: str) -> Optional[Dict[str, Any]]:
    user_id, error = _require_user_id(ws, "Authentication required")
    if error:
        return error

    try:
        delete_cmd = Attachment_delete.model_validate(message)
    except ValidationError as e:
        return _error(f"Invalid attachment_delete command: {str(e)}", match_cmd)

    attachment = attachments_db.get_attachment(delete_cmd.attachment_id)
    if not attachment:
        return _error("Attachment not found", match_cmd)

    user_roles = _get_ws_attr(ws, "user_roles", [])
    if "owner" not in user_roles and "admin" not in user_roles:
        if attachment.get("uploader_id") != user_id:
            return _error("You can only delete your own attachments", match_cmd)

    deleted = attachments_db.delete_attachment(delete_cmd.attachment_id)
    if not deleted:
        return _error("Failed to delete attachment", match_cmd)

    Logger.info(f"Attachment deleted: {delete_cmd.attachment_id}")

    return {
        "cmd": "attachment_deleted",
        "attachment_id": delete_cmd.attachment_id,
        "deleted": True,
    }


def handle_attachment_get(ws, message: Dict[str, Any], server_data: Dict[str, Any], match_cmd: str) -> Optional[Dict[str, Any]]:
    user_id, error = _require_user_id(ws, "Authentication required")
    if error:
        return error

    try:
        get_cmd = Attachment_get.model_validate(message)
    except ValidationError as e:
        return _error(f"Invalid attachment_get command: {str(e)}", match_cmd)

    attachment = attachments_db.get_attachment(get_cmd.attachment_id)
    if not attachment:
        return _error("Attachment not found or expired", match_cmd)

    config = server_data.get("config", {})
    base_url = ""
    if "server" in config and "url" in config["server"]:
        base_url = config["server"]["url"].rstrip("/")

    attachment_info = attachments_db.get_attachment_info_for_client(attachment, base_url)

    return {
        "cmd": "attachment_info",
        "attachment": attachment_info,
    }


ATTACHMENT_HANDLERS = {
    "attachment_upload": handle_attachment_upload,
    "attachment_delete": handle_attachment_delete,
    "attachment_get": handle_attachment_get,
}
