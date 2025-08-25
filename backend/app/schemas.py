from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, validator, Field
from typing import Optional

# Auth
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=1, max_length=128, description="Password")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower().strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Basic entities
class ChatOut(BaseModel):
    id: int
    type: str
    title: str | None

class MessageOut(BaseModel):
    id: int
    tg_message_id: int
    chat_id: int
    from_user_id: int | None
    content_type: str
    text: str | None
    media_path: str | None
    created_at: datetime
    sent: bool
    delivered: bool
    seen: bool

# Ingest payload sent by the bot
class IngestMessage(BaseModel):
    chat: ChatOut
    user_id: int | None = Field(None, ge=1)
    tg_message_id: int = Field(..., ge=1)
    content_type: str = Field(..., min_length=1, max_length=30)
    text: str | None = Field(None, max_length=10000)
    media_path: str | None = Field(None, max_length=500)
    created_at: datetime
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = {'text', 'photo', 'video', 'voice', 'document', 'sticker', 'audio', 'command'}
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('media_path')
    def validate_media_path(cls, v):
        if v and ('..' in v or v.startswith('/')):
            raise ValueError('Invalid media path')
        return v
