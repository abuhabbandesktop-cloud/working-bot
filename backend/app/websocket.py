# backend/app/websocket.py
from typing import List, Dict
from fastapi import WebSocket
import json
from datetime import datetime
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # chatId -> [connections]

    async def connect(self, websocket: WebSocket, chat_id: str):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        print(f"👤 Client connected to chat {chat_id}")

    def disconnect(self, websocket: WebSocket, chat_id: str):
        if chat_id in self.active_connections and websocket in self.active_connections[chat_id]:
            self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
            print(f"👋 Client disconnected from chat {chat_id}")

    async def broadcast_to_chat(self, message: dict, chat_id: str):
        """Broadcast a message to all clients in a specific chat."""
        if chat_id not in self.active_connections:
            return

        # Ensure message has required fields
        if not message.get('id'):
            message['id'] = str(uuid.uuid4())
        if not message.get('timestamp'):
            message['timestamp'] = datetime.utcnow().isoformat()

        print(f"📢 Broadcasting to chat {chat_id} ({len(self.active_connections[chat_id])} clients):", message)
        disconnected = []
        for connection in self.active_connections[chat_id]:
            try:
                await connection.send_json(message)
                print(f"✅ Sent to client in chat {chat_id}")
            except Exception as e:
                print(f"❌ Error sending to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients after iteration
        for conn in disconnected:
            self.disconnect(conn, chat_id)


# Global instance
manager = ConnectionManager()
