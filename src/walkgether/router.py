import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.walkgether.repository import walkgether_db

router = APIRouter(prefix="/api/walkgether", tags=["walkgether"])

_connections: dict[int, list[WebSocket]] = {}


async def _current_user(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization[7:]
    user = await walkgether_db.get_user_by_token(token)
    if not user:
        raise HTTPException(401, "Invalid session")
    return user.id


class RegisterReq(BaseModel):
    email: str
    password: str = Field(min_length=4)
    name: str


class LoginReq(BaseModel):
    email: str
    password: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    pace: Optional[str] = None
    interests: Optional[str] = None
    availability: Optional[str] = None
    fitness_goal: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class WalkCreate(BaseModel):
    title: str
    location: str
    scheduled_at: str
    partner_id: Optional[int] = None


class MessageSend(BaseModel):
    receiver_id: int
    body: str


class ReportReq(BaseModel):
    reported_id: int
    reason: str


@router.post("/auth/register")
async def register(req: RegisterReq):
    try:
        user, token = await walkgether_db.register(req.email, req.password, req.name)
        return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/auth/login")
async def login(req: LoginReq):
    try:
        user, token = await walkgether_db.login(req.email, req.password)
        return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}
    except ValueError as e:
        raise HTTPException(401, str(e))


@router.get("/me")
async def me(user_id: int = Depends(_current_user)):
    user = await walkgether_db.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "bio": user.bio,
        "avatar": user.avatar,
        "pace": user.pace,
        "interests": user.interests,
        "availability": user.availability,
        "fitness_goal": user.fitness_goal,
        "lat": user.lat,
        "lng": user.lng,
    }


@router.put("/profile")
async def update_profile(req: ProfileUpdate, user_id: int = Depends(_current_user)):
    user = await walkgether_db.update_profile(user_id, req.model_dump(exclude_none=True))
    return {
        "id": user.id,
        "name": user.name,
        "bio": user.bio,
        "avatar": user.avatar,
        "pace": user.pace,
        "interests": user.interests,
        "availability": user.availability,
        "fitness_goal": user.fitness_goal,
        "lat": user.lat,
        "lng": user.lng,
    }


@router.get("/walkers/nearby")
async def nearby(lat: float, lng: float, radius: float = 5.0, user_id: int = Depends(_current_user)):
    return await walkgether_db.nearby_walkers(user_id, lat, lng, radius)


@router.get("/matches")
async def matches(user_id: int = Depends(_current_user)):
    return await walkgether_db.list_matches(user_id)


@router.post("/matches/{target_id}")
async def create_match(target_id: int, user_id: int = Depends(_current_user)):
    return await walkgether_db.create_match(user_id, target_id)


@router.get("/walks")
async def walks(user_id: int = Depends(_current_user)):
    return await walkgether_db.list_walks(user_id)


@router.post("/walks")
async def create_walk(req: WalkCreate, user_id: int = Depends(_current_user)):
    scheduled = datetime.fromisoformat(req.scheduled_at.replace("Z", ""))
    return await walkgether_db.schedule_walk(user_id, req.title, req.location, scheduled, req.partner_id)


@router.get("/conversations")
async def conversations(user_id: int = Depends(_current_user)):
    return await walkgether_db.list_conversations(user_id)


@router.get("/messages/{other_id}")
async def messages(other_id: int, user_id: int = Depends(_current_user)):
    return await walkgether_db.get_messages(user_id, other_id)


@router.post("/messages")
async def send_message(req: MessageSend, user_id: int = Depends(_current_user)):
    msg = await walkgether_db.send_message(user_id, req.receiver_id, req.body)
    payload = json.dumps({"type": "message", "data": msg})
    for ws in _connections.get(req.receiver_id, []):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return msg


@router.get("/notifications")
async def notifications(user_id: int = Depends(_current_user)):
    return await walkgether_db.list_notifications(user_id)


@router.post("/block/{blocked_id}")
async def block(blocked_id: int, user_id: int = Depends(_current_user)):
    await walkgether_db.block_user(user_id, blocked_id)
    return {"status": "blocked"}


@router.post("/report")
async def report(req: ReportReq, user_id: int = Depends(_current_user)):
    await walkgether_db.report_user(user_id, req.reported_id, req.reason)
    return {"status": "reported"}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    user = await walkgether_db.get_user_by_token(token)
    if not user:
        await websocket.close(code=4001)
        return
    uid = user.id
    _connections.setdefault(uid, []).append(websocket)
    try:
        await websocket.send_json({"type": "connected", "user_id": uid})
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if uid in _connections:
            _connections[uid] = [w for w in _connections[uid] if w != websocket]
