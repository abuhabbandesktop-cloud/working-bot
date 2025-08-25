import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket server, waiting for messages...")
        try:
            while True:
                msg = await websocket.recv()
                print("📩 Raw message from server:", msg)  # DEBUG
                try:
                    data = json.loads(msg)
                    print("🔍 Parsed JSON:", data)
                except Exception as e:
                    print("❌ Failed to parse JSON:", e)
        except Exception as e:
            print("❌ Connection error:", e)

if __name__ == "__main__":
    asyncio.run(listen())
