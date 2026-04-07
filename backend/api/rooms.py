"""
FastAPI router: room management endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.livekit.session import create_room, delete_room, list_participants, get_join_info

router = APIRouter(prefix="/rooms", tags=["rooms"])


class CreateRoomRequest(BaseModel):
    room_name: str
    empty_timeout: int = 300


class JoinRoomRequest(BaseModel):
    room_name: str
    user_id: str
    display_name: str = ""


@router.post("/create")
async def api_create_room(req: CreateRoomRequest):
    try:
        room = await create_room(req.room_name, req.empty_timeout)
        return room
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/join")
async def api_join_room(req: JoinRoomRequest):
    """Returns LiveKit URL + token for the client to connect."""
    return get_join_info(req.room_name, req.user_id, req.display_name)


@router.delete("/{room_name}")
async def api_delete_room(room_name: str):
    try:
        await delete_room(room_name)
        return {"deleted": room_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{room_name}/participants")
async def api_list_participants(room_name: str):
    try:
        return await list_participants(room_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
