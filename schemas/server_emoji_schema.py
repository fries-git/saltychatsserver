from typing import Literal, Optional
from pydantic import BaseModel, Base64Str, model_validator

class Emoji_add(BaseModel):
    cmd: Literal["emoji_add"]
    name: str
    image: Base64Str
    
class Emoji_delete(BaseModel):
    cmd: Literal["emoji_delete"]
    emoji_id: int

class Emoji_get_all(BaseModel):
    cmd: Literal["emoji_get_all"]

class Emoji_get_id(BaseModel):
    cmd: Literal["emoji_get_id"]
    name: str

class Emoji_get_filename(BaseModel):
    cmd: Literal["emoji_get_filename"]
    name: str

class Emoji_update(BaseModel):
    cmd: Literal["emoji_update"]
    emoji_id: int
    name: Optional[str] = None
    image: Optional[Base64Str] = None
