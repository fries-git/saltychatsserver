import re
from typing import Literal, Optional
from pydantic import BaseModel, field_validator

DATA_URI_PATTERN = re.compile(r"^data:([a-zA-Z0-9.+-]+\/[a-zA-Z0-9.+-]+);base64,(.+)$")


class Attachment_upload(BaseModel):
    cmd: Literal["attachment_upload"]
    file: str
    name: str
    mime_type: str
    channel: str
    expires_in_days: Optional[float] = None

    @field_validator("file")
    @classmethod
    def validate_file(cls, v):
        if not v:
            raise ValueError("File data is required")
        if v.startswith("data:"):
            match = DATA_URI_PATTERN.match(v)
            if not match:
                raise ValueError("Invalid data URI format")
        else:
            try:
                import base64
                base64.b64decode(v, validate=True)
            except Exception:
                raise ValueError("Invalid base64 data")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("File name is required")
        v = v.strip()
        if len(v) > 255:
            raise ValueError("File name too long (max 255 characters)")
        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v):
        if not v:
            raise ValueError("MIME type is required")
        if "/" not in v:
            raise ValueError("Invalid MIME type format")
        return v

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v):
        if not v or not v.strip():
            raise ValueError("Channel name is required")
        return v.strip()

    @field_validator("expires_in_days")
    @classmethod
    def validate_expires_in_days(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError("expires_in_days must be positive")
            if v > 365:
                raise ValueError("expires_in_days cannot exceed 365")
        return v


class Attachment_delete(BaseModel):
    cmd: Literal["attachment_delete"]
    attachment_id: str

    @field_validator("attachment_id")
    @classmethod
    def validate_attachment_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Attachment ID is required")
        return v.strip()


class Attachment_get(BaseModel):
    cmd: Literal["attachment_get"]
    attachment_id: str

    @field_validator("attachment_id")
    @classmethod
    def validate_attachment_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Attachment ID is required")
        return v.strip()
