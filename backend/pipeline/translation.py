"""
Step 2: Span Tagging + Policy Decision + Translation
Single structured Claude API call that handles all three stages.
"""

import json
import re
from typing import Optional
import anthropic
from backend.config.settings import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a real-time Korean↔English speech translation engine for a cross-lingual voice chat system.

Your job is to perform span tagging, policy decision, and translation in a single pass.

Given:
- utterance: the spoken text to process
- target_lang: the language to translate INTO ("en" or "ko")
- mode: translation mode
- context: list of recent utterances for continuity
- glossary_hits: terms flagged by the glossary system

Output ONLY valid JSON matching this schema (no markdown, no explanation):
{
  "spans": [
    {
      "text": "<span text>",
      "lang": "ko | en | mixed",
      "type": "gaming_term | slang | proper_noun | discourse_marker | general",
      "action": "preserve | translate | paraphrase | soften | censor | defer_to_context",
      "confidence": <0.0-1.0>
    }
  ],
  "translation": "<final translated/rendered output>",
  "rendering_hint": {
    "speed": "slow | normal | fast",
    "energy": "low | normal | high"
  },
  "mode_applied": "game_tactical | casual_friend_call | polite_professional"
}

Mode behavior:
- game_tactical: short, immediate. Preserve gaming terms (one shot, rotate, GG, etc). Fast energy.
- casual_friend_call: natural everyday speech. Preserve slang and discourse markers (bro, hey, etc).
- polite_professional: formal register. Soften casual expressions.

Code-switching rules:
- gaming_term / proper_noun with action=preserve → keep original term in translation output
- Example: "나 one shot" → translation keeps "one shot" as-is
- Example: "rotate B 빨리" → translation keeps "rotate B" as-is

The "translation" field is the final rendered output the TTS will speak."""


def _build_user_message(
    utterance: str,
    target_lang: str,
    mode: str,
    context: list[str],
    glossary_hits: list[dict],
) -> str:
    return json.dumps({
        "utterance": utterance,
        "target_lang": target_lang,
        "mode": mode,
        "context": context[-3:] if context else [],
        "glossary_hits": glossary_hits,
    }, ensure_ascii=False)


def _fallback_response(utterance: str, mode: str) -> dict:
    """Return a minimal valid response when Claude output cannot be parsed."""
    return {
        "spans": [{"text": utterance, "lang": "mixed", "type": "general",
                   "action": "translate", "confidence": 0.5}],
        "translation": utterance,
        "rendering_hint": {"speed": "normal", "energy": "normal"},
        "mode_applied": mode,
        "_fallback": True,
    }


def _parse_response(text: str) -> Optional[dict]:
    """Extract JSON from Claude response, stripping any markdown fences."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find first { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def translate(
    utterance: str,
    target_lang: str = "en",
    mode: str = "casual_friend_call",
    context: Optional[list[str]] = None,
    glossary_hits: Optional[list[dict]] = None,
) -> dict:
    """
    Single Claude API call: span tag + policy decision + translation.

    Args:
        utterance: The spoken text to process.
        target_lang: "en" or "ko".
        mode: "game_tactical" | "casual_friend_call" | "polite_professional".
        context: Recent prior utterances (up to 3).
        glossary_hits: Glossary entries matched in the utterance.

    Returns:
        Parsed JSON dict matching the span tag schema.
    """
    context = context or []
    glossary_hits = glossary_hits or []

    user_msg = _build_user_message(utterance, target_lang, mode, context, glossary_hits)

    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text
        result = _parse_response(raw)
        if result is None:
            return _fallback_response(utterance, mode)
        return result
    except Exception:
        return _fallback_response(utterance, mode)
