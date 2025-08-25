from __future__ import annotations
import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time

from .auth import get_or_bootstrap_admin
from .db import Base, engine, get_db
from .models import Chat, Message
from .routers import auth as auth_router
from .routers import chats as chats_router
from .routers import ingest as ingest_router
from .routers import send as send_router
from .websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    # create default admin if none exists
    db_gen = get_db()
    db = next(db_gen)
    try:
        get_or_bootstrap_admin(db)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
    yield
    # Shutdown (add any cleanup code here if needed)


app = FastAPI(title="TG Bot Backend", version="0.1.0", lifespan=lifespan)

# CORS (SECURE configuration)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
# Add ws:// and wss:// versions of the origins
WS_ORIGINS = []
for origin in CORS_ORIGINS:
    if origin.startswith('http://'):
        WS_ORIGINS.append(f"ws://{origin[7:]}")
    elif origin.startswith('https://'):
        WS_ORIGINS.append(f"wss://{origin[8:]}")
CORS_ORIGINS.extend(WS_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Serve media folder (read-only)
MEDIA_DIR = os.getenv("MEDIA_DIR", "../data/media")
app.mount("/media", StaticFiles(directory=os.path.normpath(MEDIA_DIR)), name="media")

# Routers
app.include_router(auth_router.router)
app.include_router(chats_router.router)
app.include_router(ingest_router.router)
app.include_router(send_router.router)

# WebSocket route
@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    """
    Secure WebSocket endpoint for real-time chat communication.
    
    Security Features:
    - Token-based authentication via query parameter
    - Input validation and sanitization
    - Rate limiting per connection
    - Proper error handling and logging
    
    Args:
        websocket: WebSocket connection instance
        chat_id: Chat identifier (validated as integer)
    """
    from .auth import decode_token
    from .security import validate_input_length, hash_sensitive_data
    
    print(f"⚡ New WebSocket connection request for chat {chat_id}")
    
    # Validate chat_id format
    try:
        chat_id_int = int(chat_id)
        if chat_id_int <= 0:
            await websocket.close(code=4000, reason="Invalid chat ID")
            return
    except ValueError:
        await websocket.close(code=4000, reason="Invalid chat ID format")
        return
    
    # Extract and validate authentication token from query parameters
    query_params = dict(websocket.query_params)
    token = query_params.get('token')
    
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    # Verify JWT token
    payload = decode_token(token)
    if not payload or payload.get("kind") != "access":
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Get admin user from token
    db_gen = get_db()
    db = next(db_gen)
    try:
        from .models import Admin
        admin = db.query(Admin).filter(Admin.username == payload.get("sub")).first()
        if not admin:
            await websocket.close(code=4001, reason="User not found")
            return
        
        # Ensure the chat exists in the database with proper validation
        chat = db.query(Chat).filter(Chat.id == chat_id_int).first()
        if not chat:
            print(f"Creating new chat with ID {chat_id_int}")
            # Sanitize chat title
            chat_title = f"Chat {chat_id_int}"
            if len(chat_title) > 255:
                chat_title = chat_title[:255]
            
            chat = Chat(id=chat_id_int, type="private", title=chat_title)
            db.add(chat)
            db.commit()
        print(f"Chat found/created: {chat.id} - {chat.title}")
        
    except Exception as e:
        print(f"❌ Error ensuring chat exists: {hash_sensitive_data(str(e))}")
        await websocket.close(code=4002, reason="Database error")
        return
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    try:
        print(f"Accepting authenticated WebSocket connection for chat {chat_id}")
        await manager.connect(websocket, chat_id)
        print(f"✅ WebSocket connection established for chat {chat_id}")
        
        message_count = 0
        max_messages_per_minute = 30  # Rate limiting
        
        while True:
            data = await websocket.receive_text()
            
            # Rate limiting check
            message_count += 1
            if message_count > max_messages_per_minute:
                await websocket.close(code=4003, reason="Rate limit exceeded")
                break
            
            print(f"📨 Received message in chat {chat_id}: {hash_sensitive_data(data)}")
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON format"})
                continue
            
            # Validate message structure and content
            content = message.get("content", "")
            if not isinstance(content, str):
                await websocket.send_json({"error": "Invalid message content"})
                continue
            
            # Validate input length (prevent DoS)
            try:
                validate_input_length(content, max_length=4000, field_name="message content")
            except Exception as e:
                await websocket.send_json({"error": str(e)})
                continue
            
            # Sanitize content (basic XSS prevention)
            import html
            content = html.escape(content.strip())
            
            if not content:  # Skip empty messages
                continue
            
            # Create and save the message in the database
            try:
                db_gen = get_db()
                db = next(db_gen)
                db_message = Message(
                    chat_id=chat_id_int,
                    tg_message_id=0,  # Web-originated message
                    content_type="text",
                    text=content,
                    from_user_id=None  # Web admin user
                )
                db.add(db_message)
                db.commit()
                print(f"✅ Message saved to database with ID: {db_message.id}")
                
                # Prepare the message for broadcasting
                broadcast_message = {
                    "id": str(db_message.id),
                    "content": content,
                    "sender": "Admin",
                    "timestamp": db_message.created_at.isoformat(),
                    "chatId": chat_id,
                    "content_type": "text"
                }
                
                # Broadcast the message
                print(f"📢 Broadcasting message to chat {chat_id}")
                await manager.broadcast_to_chat(broadcast_message, chat_id)
                print("✅ Message broadcast complete")
                
            except Exception as e:
                print(f"❌ Error processing message: {hash_sensitive_data(str(e))}")
                await websocket.send_json({"error": "Failed to process message"})
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass

    except WebSocketDisconnect:
        print(f"👋 WebSocket disconnected for chat {chat_id}")
        manager.disconnect(websocket, chat_id)
    except Exception as e:
        print(f"❌ Error in WebSocket connection: {hash_sensitive_data(str(e))}")
        manager.disconnect(websocket, chat_id)
