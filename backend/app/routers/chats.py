from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Dict, List

from ..db import get_db
from ..models import Chat, Message, User
from ..schemas import ChatOut, MessageOut
from ..auth import require_admin

router = APIRouter(prefix="/api", tags=["chats"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/chats", response_model=list[ChatOut])
def list_chats(
    q: str | None = Query(default=None, description="search in title"),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    query = db.query(Chat)
    if q:
        query = query.filter(Chat.title.ilike(f"%{q}%"))
    chats = query.order_by(Chat.id.desc()).limit(200).all()
    return [ChatOut(id=c.id, type=c.type, title=c.title) for c in chats]


@router.get("/chats/organized")
def get_organized_chats(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
) -> Dict[str, List[Dict]]:
    """Get chats organized by type (Users/Groups/Channels)."""
    
    # Get all chats with their latest message info
    chats_query = (
        db.query(Chat, Message.text.label('last_message_text'), Message.created_at.label('last_message_time'))
        .outerjoin(Message, Chat.last_message_id == Message.id)
        .order_by(desc(Message.created_at))
    ).all()
    
    # Organize chats by type
    organized = {
        "users": [],
        "groups": [],
        "channels": [],
        "saved": []
    }
    
    for chat, last_message_text, last_message_time in chats_query:
        # Get user info for private chats
        user_info = None
        if chat.type == "private":
            user = db.query(User).filter(User.chat_id == chat.id).first()
            if user:
                user_info = {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "is_online": user.is_online,
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None,
                    "avatar_url": user.avatar_url
                }
        
        # Get unread message count
        unread_count = db.query(func.count(Message.id)).filter(
            Message.chat_id == chat.id,
            Message.seen == False
        ).scalar() or 0
        
        chat_data = {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title or (f"{user_info['first_name'] or ''} {user_info['last_name'] or ''}".strip() if user_info else f"Chat {chat.id}"),
            "description": chat.description,
            "last_message": last_message_text,
            "last_activity": last_message_time.isoformat() if last_message_time else None,
            "unread_count": unread_count,
            "is_pinned": chat.is_pinned,
            "is_muted": chat.is_muted,
            "member_count": chat.member_count,
            "user_info": user_info,
            "created_at": chat.created_at.isoformat() if chat.created_at else None
        }
        
        # Categorize chats
        if chat.type == "private":
            organized["users"].append(chat_data)
        elif chat.type in ["group", "supergroup"]:
            organized["groups"].append(chat_data)
        elif chat.type == "channel":
            organized["channels"].append(chat_data)
    
    # Sort each category by last activity (most recent first)
    for category in organized.values():
        category.sort(key=lambda x: x["last_activity"] or "1970-01-01", reverse=True)
    
    return organized

@router.get("/messages", response_model=list[MessageOut])
def list_messages(
    chat_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    msgs = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    return [
        MessageOut(
            id=m.id,
            tg_message_id=m.tg_message_id,
            chat_id=m.chat_id,
            from_user_id=m.from_user_id,
            content_type=m.content_type,
            text=m.text,
            media_path=m.media_path,
            created_at=m.created_at,
            sent=m.sent,
            delivered=m.delivered,
            seen=m.seen,
        )
        for m in reversed(msgs)
    ]
