# Voice Translator

실시간 한국어↔영어 음성 번역 시스템.
화자의 말투/감정/리듬/존재감을 보존하면서 다른 언어로 실시간 렌더링하는 cross-lingual speech rendering system.

## 주요 사용 상황
- 게임 보이스챗
- 외국인 친구와의 실시간 통화

## 기술 스택

| 역할 | 기술 |
|---|---|
| 모바일 | React Native (Expo) |
| 백엔드 | Python FastAPI |
| WebRTC 인프라 | LiveKit |
| ASR | Deepgram Nova-2 (streaming) |
| Translation + Policy | Claude API (Anthropic) |
| TTS (영어) | ElevenLabs Flash v2.5 |
| TTS (한국어) | Google Cloud TTS Neural2 |
| DB / 세션 | Supabase |

---

## 디렉토리 구조

```
/backend
  /api          ← FastAPI 라우터 (HTTP 엔드포인트, WebSocket 핸들러)
  /pipeline     ← ASR, tagging, translation, TTS 각 처리 모듈
  /policy       ← translation policy 로직 (mode별 동작 제어)
  /livekit      ← LiveKit 세션 생성/관리/종료
  /config       ← 환경변수 로딩, 모드 설정 상수
  requirements.txt

/mobile
  /src
    /screens    ← 화면 단위 컴포넌트 (통화 화면, 설정 등)
    /components ← 재사용 UI 컴포넌트 (자막, 토글, 볼륨 등)
    /hooks      ← 오디오 처리, LiveKit 연결, 상태 구독
    /store      ← 전역 상태 관리 (Zustand)
  package.json

/shared
  /glossary     ← 게임 용어/슬랭/고유명사 시드 데이터 (JSON)
  /policy       ← translation policy 설정 (JSON)
  /schema       ← span tag JSON schema 정의

/credentials    ← Google TTS JSON 키 파일 위치 (gitignore 포함)

README.md
.env            ← API 키 (gitignore 포함, 절대 커밋 금지)
.gitignore
```

---

## 시스템 파이프라인

```
음성 입력 (마이크)
  → noise suppression / echo handling
  → [Audio Mixing Layer]
  → VAD (Voice Activity Detection)
      game_tactical: silence 0.3초
      casual:        silence 0.6초
  → Streaming ASR (Deepgram Nova-2)
  → Span Tagging + Policy Decision + Translation (Claude API, 단일 호출)
  → TTS Rendering
      영어 → ElevenLabs Flash v2.5 (streaming)
      한국어 → Google Cloud TTS Neural2
  → LiveKit relay → 상대방 출력
  → 자막/텍스트 로그 (항상 병행)
```

---

## Audio Mixing Mode

| 모드 | 동작 |
|---|---|
| Pass-through | 원본 100% + TTS 순차 출력 |
| Blend (기본값) | 원본 30% + TTS 100% |
| TTS Only | 원본 차단 + TTS만 출력 |

---

## Translation Mode

| 모드 | 특징 |
|---|---|
| game_tactical | 짧고 즉각적, 전술 용어 보존 우선 |
| casual_friend_call | 자연스러운 일상 표현 |
| polite_professional | 격식체 |

---

## Voice Cloning 전략

- **Phase 1 (0~10초)**: preset voice (mode 기반 선택)
- **Phase 2 (10~30초 이후)**: ElevenLabs instant cloning (누적 발화 → cloned voice)
- 전환은 자동, 사용자에게 노출하지 않음

---

## 설계 원칙

- 하드코딩 최소화: rule table 대신 span tagging + policy layer + glossary memory
- MVP 우선
- 자막은 TTS와 항상 병행 (fallback 채널)
