import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Deepgram
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Google Cloud TTS
GOOGLE_CLOUD_TTS_KEY = os.getenv("GOOGLE_CLOUD_TTS_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# LiveKit
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Translation Mode endpointing (ms)
ENDPOINTING_MS = {
    "game_tactical": 300,
    "casual_friend_call": 600,
    "polite_professional": 600,
}

# ElevenLabs preset voice IDs per mode
ELEVENLABS_PRESET_VOICES = {
    "game_tactical": "pNInz6obpgDQGcFmaJgB",   # Adam - energetic/tactical
    "casual_friend_call": "ErXwobaYiN019PkySvjV", # Antoni - casual
    "polite_professional": "VR6AewLTigWG4xSOukaG", # Arnold - professional
}

# Voice cloning thresholds (seconds)
VOICE_CLONE_PHASE2_THRESHOLD = 10.0   # start cloning after 10s of audio
VOICE_CLONE_MIN_AUDIO = 30.0          # target 30s for stable clone
