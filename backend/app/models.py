from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )  # Telegram chat_id may not fit int? using int64 in SQLite is fine
    type: Mapped[str] = mapped_column(String(20))  # private/group/supergroup/channel
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship("User", back_populates="chat")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Telegram user_id
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    username: Mapped[str | None] = mapped_column(String(120))
    language_code: Mapped[str | None] = mapped_column(String(10))
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="users")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )  # internal id
    tg_message_id: Mapped[int] = mapped_column(
        Integer, index=True
    )  # original Telegram message_id
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), index=True)
    from_user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Telegram user_id
    content_type: Mapped[str] = mapped_column(
        String(30)
    )  # text/photo/video/voice/document/sticker/command/...
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # relative path under data/media
    reply_to_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # delivery/read flags (best-effort)
    sent: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # received by us means "sent"
    delivered: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Telegram doesn't expose per-user delivery
    seen: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # we'll mark when admin opens a chat in UI later

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")


class Media(Base):
    __tablename__ = "media"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))  # photo/video/voice/document
    file_path: Mapped[str] = mapped_column(String(500))  # relative path


class AdminAction(Base):
    __tablename__ = "admin_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"))
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
