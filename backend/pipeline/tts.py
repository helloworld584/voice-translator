"""
Step 4: TTS Rendering
- English: ElevenLabs Flash v2.5 (streaming)
- Korean: Google Cloud TTS Neural2

Voice cloning strategy:
  Phase 1 (< PHASE2_THRESHOLD seconds accumulated): preset voice per mode
  Phase 2 (>= PHASE2_THRESHOLD): ElevenLabs instant voice cloning using accumulated audio
"""

import asyncio
import io
import time
from typing import AsyncIterator, Optional
import httpx
from google.cloud import texttospeech

from backend.config.settings import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_PRESET_VOICES,
    VOICE_CLONE_PHASE2_THRESHOLD,
    VOICE_CLONE_MIN_AUDIO,
)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
ELEVENLABS_MODEL = "eleven_flash_v2_5"


# ---------------------------------------------------------------------------
# ElevenLabs
# ---------------------------------------------------------------------------

class ElevenLabsTTS:
    """
    Streaming TTS via ElevenLabs with automatic phase transition
    from preset voice (Phase 1) to instant voice clone (Phase 2).
    """

    def __init__(self, mode: str = "casual_friend_call", session_id: str = "default"):
        self.mode = mode
        self.session_id = session_id
        self._voice_id: str = ELEVENLABS_PRESET_VOICES.get(mode, list(ELEVENLABS_PRESET_VOICES.values())[0])
        self._cloned_voice_id: Optional[str] = None
        self._reference_audio_chunks: list[bytes] = []
        self._accumulated_duration: float = 0.0
        self._phase = 1

    def accumulate_audio(self, pcm_chunk: bytes, duration_sec: float):
        """Feed raw speaker audio for future voice cloning."""
        self._reference_audio_chunks.append(pcm_chunk)
        self._accumulated_duration += duration_sec
        if self._phase == 1 and self._accumulated_duration >= VOICE_CLONE_PHASE2_THRESHOLD:
            asyncio.create_task(self._trigger_voice_clone())

    async def _trigger_voice_clone(self):
        """Request instant voice clone from ElevenLabs and switch to Phase 2."""
        audio_data = b"".join(self._reference_audio_chunks)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{ELEVENLABS_BASE}/voice-generation/instant-voice-cloning",
                    headers={"xi-api-key": ELEVENLABS_API_KEY},
                    files={"files": ("reference.pcm", audio_data, "audio/wav")},
                    data={
                        "name": f"clone_{self.session_id}",
                        "description": "Auto-generated voice clone",
                    },
                )
                response.raise_for_status()
                self._cloned_voice_id = response.json()["voice_id"]
                self._voice_id = self._cloned_voice_id
                self._phase = 2
        except Exception:
            # Silently stay on Phase 1 if cloning fails
            pass

    @property
    def current_voice_id(self) -> str:
        return self._voice_id

    async def synthesize_stream(
        self,
        text: str,
        speed: str = "normal",
        energy: str = "normal",
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized audio chunks from ElevenLabs.
        Yields MP3 audio bytes as they arrive.
        """
        speed_map = {"slow": 0.75, "normal": 1.0, "fast": 1.25}
        stability_map = {"low": 0.3, "normal": 0.5, "high": 0.7}
        similarity_map = {"low": 0.6, "normal": 0.75, "high": 0.9}

        speed_val = speed_map.get(speed, 1.0)
        stability = stability_map.get(energy, 0.5)
        similarity = similarity_map.get(energy, 0.75)

        url = f"{ELEVENLABS_BASE}/text-to-speech/{self._voice_id}/stream"
        payload = {
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
                "speed": speed_val,
            },
        }
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk


# ---------------------------------------------------------------------------
# Google Cloud TTS (Korean)
# ---------------------------------------------------------------------------

class GoogleTTS:
    """Korean TTS using Google Cloud Neural2."""

    def __init__(self):
        self._client = texttospeech.TextToSpeechAsyncClient()

    async def synthesize(
        self,
        text: str,
        speed: str = "normal",
        energy: str = "normal",
    ) -> bytes:
        """
        Synthesize Korean text and return MP3 bytes.
        Google TTS does not support true streaming; returns full audio at once.
        """
        speed_map = {"slow": 0.75, "normal": 1.0, "fast": 1.3}
        pitch_map = {"low": -2.0, "normal": 0.0, "high": 2.0}

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Neural2-C",
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speed_map.get(speed, 1.0),
            pitch=pitch_map.get(energy, 0.0),
        )

        response = await self._client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        return response.audio_content


# ---------------------------------------------------------------------------
# Unified TTS dispatcher
# ---------------------------------------------------------------------------

async def synthesize(
    text: str,
    target_lang: str,
    rendering_hint: dict,
    elevenlabs_tts: Optional[ElevenLabsTTS] = None,
    google_tts: Optional[GoogleTTS] = None,
) -> AsyncIterator[bytes]:
    """
    Route TTS to the correct engine based on target_lang.
    - "en": ElevenLabs streaming
    - "ko": Google Cloud TTS (returns single chunk)
    """
    speed = rendering_hint.get("speed", "normal")
    energy = rendering_hint.get("energy", "normal")

    if target_lang == "en":
        tts = elevenlabs_tts or ElevenLabsTTS()
        async for chunk in tts.synthesize_stream(text, speed=speed, energy=energy):
            yield chunk
    else:
        tts = google_tts or GoogleTTS()
        audio = await tts.synthesize(text, speed=speed, energy=energy)
        yield audio
