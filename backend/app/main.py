import os
import json
import asyncio
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import aioredis

# Load environment variables
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CHANNEL = "locations"

app = FastAPI(title="fastapi-tracking-service")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- WebSocket Connection Manager ----
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"✅ {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"❌ {client_id} disconnected")

    async def broadcast(self, message: str):
        """Send message to all active connections"""
        to_remove = []
        for cid, ws in list(self.active_connections.items()):
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.append(cid)
        for cid in to_remove:
            self.disconnect(cid)


manager = ConnectionManager()

# ---- Redis Publisher & Subscriber ----
async def redis_subscriber():
    """Background task: listen for Redis messages and broadcast to WebSocket clients"""
    try:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        print("📡 Subscribed to Redis channel:", CHANNEL)
        async for message in pubsub.listen():
            if message["type"] == "message":
                await manager.broadcast(message["data"])
    except Exception as e:
        print("Redis subscriber error:", e)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(redis_subscriber())


# ---- WebSocket endpoint ----
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)  # optional local echo
    except WebSocketDisconnect:
        manager.disconnect(client_id)


# ---- REST endpoint for publishing ----
@app.post("/publish")
async def publish_location(payload: dict):
    try:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        await redis.publish(CHANNEL, json.dumps(payload))
        return {"ok": True, "data": payload}
    except Exception as e:
        return {"ok": False, "error": str(e)}
