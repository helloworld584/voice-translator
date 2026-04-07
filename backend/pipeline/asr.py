"""
Step 3: Deepgram Streaming ASR
WebSocket-based streaming ASR with mode-based endpointing.
Interim results → subtitle update
Final results → translation pipeline
"""

import asyncio
import json
from typing import Callable, Optional
import websockets
from backend.config.settings import DEEPGRAM_API_KEY, ENDPOINTING_MS

DEEPGRAM_WSS_URL = "wss://api.deepgram.com/v1/listen"


def _build_deepgram_url(mode: str, language: str = "ko") -> str:
    endpointing = ENDPOINTING_MS.get(mode, 600)
    params = [
        f"model=nova-2",
        f"language={language}",
        "detect_language=true",
        "smart_format=true",
        "interim_results=true",
        f"endpointing={endpointing}",
        "utterance_end_ms=1000",
        "vad_events=true",
        "encoding=linear16",
        "sample_rate=16000",
        "channels=1",
    ]
    return f"{DEEPGRAM_WSS_URL}?" + "&".join(params)


class DeepgramASRStream:
    """
    Manages a Deepgram streaming ASR WebSocket connection.

    Callbacks:
        on_interim(text): called with interim transcript text
        on_final(text):   called with final transcript text (utterance complete)
        on_error(error):  called on connection/parse errors
    """

    def __init__(
        self,
        mode: str = "casual_friend_call",
        language: str = "ko",
        on_interim: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        self.mode = mode
        self.language = language
        self.on_interim = on_interim or (lambda t: None)
        self.on_final = on_final or (lambda t: None)
        self.on_error = on_error or (lambda e: None)
        self._ws = None
        self._running = False

    async def connect(self):
        url = _build_deepgram_url(self.mode, self.language)
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        self._ws = await websockets.connect(url, additional_headers=headers)
        self._running = True

    async def send_audio(self, chunk: bytes):
        """Send raw PCM16 audio chunk to Deepgram."""
        if self._ws and self._running:
            await self._ws.send(chunk)

    async def listen(self):
        """Receive and dispatch ASR events. Run as a background task."""
        try:
            async for message in self._ws:
                self._handle_message(message)
        except websockets.ConnectionClosed:
            self._running = False
        except Exception as e:
            self.on_error(e)
            self._running = False

    def _handle_message(self, raw: str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "Results":
            channel = data.get("channel", {})
            alternatives = channel.get("alternatives", [])
            if not alternatives:
                return
            transcript = alternatives[0].get("transcript", "").strip()
            if not transcript:
                return
            is_final = data.get("is_final", False)
            speech_final = data.get("speech_final", False)

            if speech_final or is_final:
                self.on_final(transcript)
            else:
                self.on_interim(transcript)

        elif msg_type == "UtteranceEnd":
            # Deepgram signals utterance end — useful for flush
            pass

        elif msg_type == "SpeechStarted":
            pass  # VAD: speech detected

    async def close(self):
        self._running = False
        if self._ws:
            await self._ws.send(json.dumps({"type": "CloseStream"}))
            await self._ws.close()


async def run_asr_stream(
    audio_source: asyncio.Queue,
    mode: str = "casual_friend_call",
    language: str = "ko",
    on_interim: Optional[Callable[[str], None]] = None,
    on_final: Optional[Callable[[str], None]] = None,
):
    """
    High-level helper: reads PCM chunks from audio_source queue and streams to Deepgram.

    Args:
        audio_source: asyncio.Queue yielding raw PCM16 bytes
        mode: translation mode (controls endpointing)
        language: primary language hint
        on_interim: callback for interim results → subtitle updates
        on_final: callback for final results → translation pipeline
    """
    stream = DeepgramASRStream(
        mode=mode,
        language=language,
        on_interim=on_interim,
        on_final=on_final,
    )
    await stream.connect()
    listen_task = asyncio.create_task(stream.listen())

    try:
        while True:
            chunk = await audio_source.get()
            if chunk is None:  # sentinel to stop
                break
            await stream.send_audio(chunk)
    finally:
        await stream.close()
        listen_task.cancel()
