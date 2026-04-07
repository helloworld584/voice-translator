"""
Step 5: LiveKit Session Management
- Room creation / join / leave
- Token generation for participants
- Publishes original audio track and translated TTS track separately
"""

import time
from livekit import api
from backend.config.settings import LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET


def create_access_token(
    room_name: str,
    participant_identity: str,
    participant_name: str = "",
    ttl_seconds: int = 3600,
) -> str:
    """
    Generate a LiveKit access token for a participant.
    The participant gets publish + subscribe grants.
    """
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity(participant_identity)
    token.with_name(participant_name or participant_identity)
    token.with_ttl(ttl_seconds)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    ))
    return token.to_jwt()


async def create_room(room_name: str, empty_timeout: int = 300) -> dict:
    """
    Create a LiveKit room via the server API.
    Returns the room info dict.
    """
    livekit_api = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )
    room = await livekit_api.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            empty_timeout=empty_timeout,
        )
    )
    await livekit_api.aclose()
    return {"name": room.name, "sid": room.sid}


async def delete_room(room_name: str):
    """Delete a LiveKit room."""
    livekit_api = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )
    await livekit_api.room.delete_room(api.DeleteRoomRequest(room=room_name))
    await livekit_api.aclose()


async def list_participants(room_name: str) -> list[dict]:
    """List current participants in a room."""
    livekit_api = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )
    response = await livekit_api.room.list_participants(
        api.ListParticipantsRequest(room=room_name)
    )
    await livekit_api.aclose()
    return [{"identity": p.identity, "name": p.name, "sid": p.sid}
            for p in response.participants]


def get_join_info(room_name: str, user_id: str, display_name: str = "") -> dict:
    """
    Returns all info the client needs to join a LiveKit room:
    - server URL
    - access token
    - room name
    """
    token = create_access_token(room_name, user_id, display_name)
    return {
        "url": LIVEKIT_URL,
        "token": token,
        "room": room_name,
    }
