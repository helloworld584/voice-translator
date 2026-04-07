"""
Step 6: Glossary Memory
- Load seed glossary from JSON
- Match terms in utterance
- Supabase-backed persistence for runtime additions
"""

import json
import re
from pathlib import Path
from typing import Optional
from supabase import create_client, Client
from backend.config.settings import SUPABASE_URL, SUPABASE_ANON_KEY

SEED_PATH = Path(__file__).parents[2] / "shared" / "glossary" / "seed.json"

# In-memory glossary cache: list of {term, action, context}
_glossary: list[dict] = []
_supabase: Optional[Client] = None


def _get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase


def load_glossary():
    """
    Load glossary from seed JSON + Supabase.
    Seed data is the baseline; Supabase entries override/extend it.
    """
    global _glossary
    # Load seed
    with open(SEED_PATH, encoding="utf-8") as f:
        seed = json.load(f)

    try:
        db = _get_supabase()
        result = db.table("glossary").select("*").execute()
        db_entries = result.data or []
    except Exception:
        db_entries = []

    # Merge: seed first, DB entries override by term
    merged = {entry["term"].lower(): entry for entry in seed}
    for entry in db_entries:
        merged[entry["term"].lower()] = entry

    _glossary = list(merged.values())


def find_hits(utterance: str) -> list[dict]:
    """
    Find glossary terms present in the utterance.
    Returns list of matching glossary entries.
    Case-insensitive, whole-word matching.
    """
    if not _glossary:
        load_glossary()

    hits = []
    lower_utterance = utterance.lower()
    for entry in _glossary:
        term = entry["term"]
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, lower_utterance):
            hits.append(entry)
    return hits


async def add_term(term: str, action: str, context: str = "general") -> dict:
    """Add a new glossary term to Supabase and refresh in-memory cache."""
    db = _get_supabase()
    entry = {"term": term, "action": action, "context": context}
    result = db.table("glossary").upsert(entry).execute()
    load_glossary()  # refresh cache
    return result.data[0] if result.data else entry


async def delete_term(term: str):
    """Remove a term from Supabase glossary."""
    db = _get_supabase()
    db.table("glossary").delete().eq("term", term).execute()
    load_glossary()


# Supabase schema (run once):
# CREATE TABLE glossary (
#   id SERIAL PRIMARY KEY,
#   term TEXT UNIQUE NOT NULL,
#   action TEXT NOT NULL,
#   context TEXT DEFAULT 'general',
#   created_at TIMESTAMP DEFAULT NOW()
# );
