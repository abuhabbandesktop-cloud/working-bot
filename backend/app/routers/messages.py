# backend/app/routers/messages.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from ..db import get_db
from .. import models
from ..websocket import manager

router = APIRouter(prefix="/api", tags=["messages"])


@router.post("/ingest")
async def ingest_message(payload: dict, db: Session = Depends(get_db)):
    """
    Ingest a message from the bot.
    Payload example:
    {
        "message_id": 123,
        "chat_id": 789,
        "from_user_id": 456,
        "is_bot": false,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johnd",
        "language_code": "en",
        "content_type": "text",
        "text": "Hello",
        "media_path": "/media/file.png"
    }
    """

    # ✅ Ensure User exists
    user = None
    if payload.get("from_user_id"):
        user = db.query(models.User).filter_by(id=payload["from_user_id"]).first()
        if not user:
            user = models.User(
                id=payload["from_user_id"],
                chat_id=payload["chat_id"],
                is_bot=payload.get("is_bot", False),
                first_name=payload.get("first_name"),
                last_name=payload.get("last_name"),
                username=payload.get("username"),
                language_code=payload.get("language_code"),
            )
            db.add(user)
            db.commit()

    # ✅ Save Message
    msg = models.Message(
        tg_message_id=payload["message_id"],
        chat_id=payload["chat_id"],
        from_user_id=payload.get("from_user_id"),
        content_type=payload.get("content_type", "text"),
        text=payload.get("text"),
        media_path=payload.get("media_path"),
        created_at=datetime.utcnow(),
        sent=True,
        delivered=True,
        seen=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # ✅ Broadcast
    await manager.broadcast({
        "event": "new_message",
        "data": {
            "id": msg.id,
            "tg_message_id": msg.tg_message_id,
            "chat_id": msg.chat_id,
            "from_user_id": msg.from_user_id,
            "content_type": msg.content_type,
            "text": msg.text,
            "media_path": msg.media_path,
            "created_at": str(msg.created_at),
            "sent": msg.sent,
            "delivered": msg.delivered,
            "seen": msg.seen,
        }
    })

    return {"status": "ok", "message_id": msg.id}
