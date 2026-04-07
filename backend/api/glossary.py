"""
FastAPI router: glossary management
"""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.policy.glossary import find_hits, add_term, delete_term, load_glossary, _glossary

router = APIRouter(prefix="/glossary", tags=["glossary"])


class AddTermRequest(BaseModel):
    term: str
    action: str
    context: str = "general"


@router.get("/")
def api_list_glossary():
    if not _glossary:
        load_glossary()
    return _glossary


@router.post("/")
async def api_add_term(req: AddTermRequest):
    return await add_term(req.term, req.action, req.context)


@router.delete("/{term}")
async def api_delete_term(term: str):
    await delete_term(term)
    return {"deleted": term}
