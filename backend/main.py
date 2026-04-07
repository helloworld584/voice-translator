"""
Voice Translator — FastAPI entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.rooms import router as rooms_router
from backend.api.translate import router as translate_router
from backend.api.glossary import router as glossary_router
from backend.policy.glossary import load_glossary

app = FastAPI(
    title="Voice Translator API",
    description="Real-time Korean↔English cross-lingual speech rendering",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router)
app.include_router(translate_router)
app.include_router(glossary_router)


@app.on_event("startup")
async def startup():
    load_glossary()


@app.get("/health")
def health():
    return {"status": "ok"}
