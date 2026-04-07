"""
FastAPI router: translation endpoint (HTTP, for testing)
WebSocket-based real-time translation lives in the pipeline layer.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.pipeline.translation import translate
from backend.policy.glossary import find_hits

router = APIRouter(prefix="/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    utterance: str
    target_lang: str = "en"
    mode: str = "casual_friend_call"
    context: list[str] = []


@router.post("/")
async def api_translate(req: TranslateRequest):
    glossary_hits = find_hits(req.utterance)
    result = translate(
        utterance=req.utterance,
        target_lang=req.target_lang,
        mode=req.mode,
        context=req.context,
        glossary_hits=glossary_hits,
    )
    return result
