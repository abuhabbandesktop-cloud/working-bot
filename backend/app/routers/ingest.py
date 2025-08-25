from __future__ import annotations
import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Chat, User, Message
from ..schemas import IngestMessage
from ..websocket import manager   # <-- NEW import

router = APIRouter(prefix="/internal", tags=["ingest"])

API_INGEST_SECRET = os.getenv("API_INGEST_SECRET", "dev-secret")

def check_ingest_secret(x_ingest_secret: str | None = Header(default=None)):
    if not x_ingest_secret or x_ingest_secret != API_INGEST_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized ingest")
    return True

@router.post("/ingest/telegram")
async def ingest_telegram(   # <-- make this async so we can await broadcast
    payload: IngestMessage,
    db: Session = Depends(get_db),
    _ok=Depends(check_ingest_secret),
):
    # upsert chat
    chat = db.query(Chat).filter(Chat.id == payload.chat.id).first()
    if not chat:
        chat = Chat(id=payload.chat.id, type=payload.chat.type, title=payload.chat.title)
        db.add(chat)
        db.flush()
    else:
        if chat.title != payload.chat.title or chat.type != payload.chat.type:
            chat.title = payload.chat.title
            chat.type = payload.chat.type

    # upsert user (if present)
    if payload.user_id:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            user = User(id=payload.user_id, chat_id=chat.id, is_bot=False,
                        first_name=None, last_name=None, username=None, language_code=None)
            db.add(user)

    # add message
    msg = Message(
        tg_message_id=payload.tg_message_id,
        chat_id=chat.id,
        from_user_id=payload.user_id,
        content_type=payload.content_type,
        text=payload.text,
        media_path=payload.media_path,
        created_at=payload.created_at,
        sent=True, delivered=True, seen=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    # Update chat's last message info
    chat.last_message_id = msg.id
    chat.last_activity = payload.created_at
    db.commit()

    # 📢 broadcast via WebSocket
    await manager.broadcast_to_chat({
        "id": str(msg.id),
        "chat_id": str(msg.chat_id),
        "from_user_id": str(msg.from_user_id) if msg.from_user_id else None,
        "content_type": msg.content_type,
        "text": msg.text,
        "media_path": msg.media_path,
        "created_at": str(msg.created_at),
        "sender": "User",
    }, str(chat.id))

    return {"ok": True, "message_id": msg.id}
