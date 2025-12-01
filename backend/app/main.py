import json
import asyncio
import logging
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import aioredis

from .settings import get_settings

load_dotenv()

settings = get_settings()

logger = logging.getLogger("tracking-service")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


class LocationPayload(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    lat: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90 to 90)",
    )
    lng: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180 to 180)",
    )
    ts: Optional[int] = Field(None, description="Unix epoch ms (optional)")

    speed: Optional[float] = Field(
        None,
        ge=0.0,
        description="Speed in meters/second (optional, must be >= 0 if provided)",
    )
    heading: Optional[float] = Field(
        None,
        ge=0.0,
        le=360.0,
        description="Heading/bearing in degrees 0-360 (optional)",
    )
    accuracy: Optional[float] = Field(
        None,
        ge=0.0,
        description="Horizontal accuracy in meters (optional, must be >= 0 if provided)",
    )
    battery: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Battery level in percent 0-100 (optional)",
    )


class LocationHistoryResponse(BaseModel):
    device_id: str
    count: int
    items: List[LocationPayload]


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _history_key(device_id: str) -> str:
    """Redis key for storing per-device history."""
    return f"device:{device_id}:history"


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("ws_client_registered", extra={"client_id": client_id})

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info("ws_client_unregistered", extra={"client_id": client_id})

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


async def redis_subscriber():
    """Background task: listen for Redis messages and broadcast to WebSocket clients"""
    try:
        redis = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(settings.REDIS_CHANNEL)
        logger.info(
            "redis_subscribe_started",
            extra={"channel": settings.REDIS_CHANNEL, "redis_url": str(settings.REDIS_URL)},
        )
        async for message in pubsub.listen():
            if message["type"] == "message":
                await manager.broadcast(message["data"])
    except Exception as e:
        logger.exception("redis_subscriber_error", extra={"error": str(e)})


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(redis_subscriber())


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    logger.info("ws_connected", extra={"client_id": client_id})
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)  # optional local echo
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info("ws_disconnected", extra={"client_id": client_id})


@app.post("/publish")
async def publish_location(
    request: Request,
    payload: LocationPayload,
    x_api_key: Optional[str] = Header(None),
):
    if settings.API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")

    try:
        redis = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        data = payload.dict()
        if data.get("ts") is None:
            # Use UNIX epoch milliseconds for ts when not provided
            data["ts"] = int(time.time() * 1000)

        await redis.publish(settings.REDIS_CHANNEL, json.dumps(data))

        key = _history_key(data["device_id"])
        await redis.lpush(key, json.dumps(data))
        await redis.ltrim(key, 0, settings.MAX_DEVICE_HISTORY - 1)

        client_host = request.client.host if request.client else None
        logger.info(
            "location_published",
            extra={
                "device_id": data.get("device_id"),
                "lat": data.get("lat"),
                "lng": data.get("lng"),
                "ts": data.get("ts"),
                "speed": data.get("speed"),
                "heading": data.get("heading"),
                "accuracy": data.get("accuracy"),
                "battery": data.get("battery"),
                "client_ip": client_host,
            },
        )

        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("location_publish_error", extra={"error": str(e)})
        return {"ok": False, "error": str(e)}


@app.get("/history/{device_id}", response_model=LocationHistoryResponse)
async def get_history(device_id: str, limit: int = 100):
    """
    Return last `limit` points for given device_id from Redis LIST.

    Items are returned from newest to oldest (ts descending).
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")
    if limit > settings.MAX_DEVICE_HISTORY:
        limit = settings.MAX_DEVICE_HISTORY

    try:
        redis = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        key = _history_key(device_id)
        raw_items = await redis.lrange(key, 0, limit - 1)
        items: List[LocationPayload] = []
        for raw in raw_items:
            try:
                payload_dict = json.loads(raw)
                items.append(LocationPayload(**payload_dict))
            except Exception:
                continue

        response = LocationHistoryResponse(
            device_id=device_id,
            count=len(items),
            items=items,
        )
        logger.info(
            "history_fetched",
            extra={
                "device_id": device_id,
                "count": len(items),
                "limit": limit,
            },
        )
        return response
    except Exception as e:
        logger.exception("history_fetch_error", extra={"device_id": device_id, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health() -> Dict[str, object]:
    """
    Simple health-check endpoint.

    Returns Redis connectivity and websocket client count.
    """
    redis_status = "unknown"
    try:
        redis = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        pong = await redis.ping()
        redis_status = "ok" if pong else "down"
    except Exception as e:
        redis_status = f"error: {e}"

    ws_clients = len(manager.active_connections)

    status = {
        "redis": redis_status,
        "websocket_clients": ws_clients,
        "app_name": settings.APP_NAME,
    }

    logger.info("health_checked", extra=status)
    return status
