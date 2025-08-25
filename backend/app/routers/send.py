from __future__ import annotations
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_admin

router = APIRouter(prefix="/api", tags=["send"])

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

class SendRequest(BaseModel):
    chat_id: int
    text: str

@router.post("/send")
async def send_message(req: SendRequest, _admin = Depends(require_admin)):
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not configured")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(url, json={"chat_id": req.chat_id, "text": req.text})
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Telegram error: {r.text}")
    return {"ok": True}
