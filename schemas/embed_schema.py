from typing import Literal, Optional, List
from pydantic import BaseModel, Field, model_validator


class EmbedAuthor(BaseModel):
    name: str = Field(..., max_length=256)
    url: Optional[str] = None
    icon_url: Optional[str] = None


class EmbedFooter(BaseModel):
    text: str = Field(..., max_length=2048)
    icon_url: Optional[str] = None


class EmbedImage(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


class EmbedThumbnail(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


class EmbedField(BaseModel):
    name: str = Field(..., max_length=256)
    value: str = Field(..., max_length=1024)
    inline: bool = False


class PollOption(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., max_length=100)
    emoji: Optional[str] = None


class PollData(BaseModel):
    question: str = Field(..., max_length=300)
    options: List[PollOption] = Field(..., min_length=2, max_length=10)
    allow_multiselect: bool = False
    expires_at: Optional[float] = None


class Embed(BaseModel):
    type: Literal["rich", "poll", "link", "image", "video", "article"] = "rich"
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = Field(None, max_length=4096)
    url: Optional[str] = None
    color: Optional[int] = Field(None, ge=0, le=16777215)
    timestamp: Optional[str] = None
    author: Optional[EmbedAuthor] = None
    footer: Optional[EmbedFooter] = None
    image: Optional[EmbedImage] = None
    thumbnail: Optional[EmbedThumbnail] = None
    fields: Optional[List[EmbedField]] = Field(None, max_length=25)
    poll: Optional[PollData] = None

    @model_validator(mode="after")
    def validate_embed_type(self):
        if self.type == "poll":
            if not self.poll:
                raise ValueError("Poll embeds must have 'poll' data")
            if self.title:
                if len(self.title) > 256:
                    raise ValueError("Poll title cannot exceed 256 characters")
        
        if self.type == "link":
            if not self.url:
                raise ValueError("Link embeds must have 'url'")
        
        if self.type == "image":
            if not self.image:
                raise ValueError("Image embeds must have 'image'")
        
        total_chars = 0
        if self.title:
            total_chars += len(self.title)
        if self.description:
            total_chars += len(self.description)
        if self.fields:
            for field in self.fields:
                total_chars += len(field.name) + len(field.value)
        if self.footer and self.footer.text:
            total_chars += len(self.footer.text)
        if self.author and self.author.name:
            total_chars += len(self.author.name)
        if self.poll and self.poll.question:
            total_chars += len(self.poll.question)
            for opt in self.poll.options:
                total_chars += len(opt.text)
        
        if total_chars > 6000:
            raise ValueError("Embed total characters cannot exceed 6000")
        
        return self


def validate_embeds(embeds: list) -> tuple[bool, str | None]:
    if not isinstance(embeds, list):
        return False, "Embeds must be an array"
    
    if len(embeds) > 10:
        return False, "Cannot have more than 10 embeds"
    
    for i, embed in enumerate(embeds):
        try:
            Embed.model_validate(embed)
        except Exception as e:
            return False, f"Embed {i}: {str(e)}"
    
    return True, None
