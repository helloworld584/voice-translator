/**
 * Global call state management (Zustand)
 */
import { create } from "zustand";

export type TranslationMode = "game_tactical" | "casual_friend_call" | "polite_professional";
export type AudioMixingMode = "pass_through" | "blend" | "tts_only";

interface Subtitle {
  id: string;
  text: string;
  isFinal: boolean;
  timestamp: number;
}

interface CallState {
  // Connection
  isConnected: boolean;
  roomName: string | null;
  userId: string | null;

  // Mode
  translationMode: TranslationMode;
  audioMixingMode: AudioMixingMode;
  targetLang: "en" | "ko";

  // Subtitles
  subtitles: Subtitle[];
  interimText: string;

  // Actions
  setConnected: (connected: boolean) => void;
  setRoom: (roomName: string, userId: string) => void;
  setTranslationMode: (mode: TranslationMode) => void;
  setAudioMixingMode: (mode: AudioMixingMode) => void;
  setTargetLang: (lang: "en" | "ko") => void;
  addSubtitle: (text: string, isFinal: boolean) => void;
  setInterimText: (text: string) => void;
  clearSubtitles: () => void;
  disconnect: () => void;
}

export const useCallStore = create<CallState>((set) => ({
  isConnected: false,
  roomName: null,
  userId: null,
  translationMode: "casual_friend_call",
  audioMixingMode: "blend",
  targetLang: "en",
  subtitles: [],
  interimText: "",

  setConnected: (connected) => set({ isConnected: connected }),

  setRoom: (roomName, userId) => set({ roomName, userId }),

  setTranslationMode: (mode) => set({ translationMode: mode }),

  setAudioMixingMode: (mode) => set({ audioMixingMode: mode }),

  setTargetLang: (lang) => set({ targetLang: lang }),

  addSubtitle: (text, isFinal) =>
    set((state) => ({
      subtitles: [
        ...state.subtitles.slice(-19), // keep last 20
        {
          id: `${Date.now()}-${Math.random()}`,
          text,
          isFinal,
          timestamp: Date.now(),
        },
      ],
      interimText: isFinal ? "" : text,
    })),

  setInterimText: (text) => set({ interimText: text }),

  clearSubtitles: () => set({ subtitles: [], interimText: "" }),

  disconnect: () =>
    set({
      isConnected: false,
      roomName: null,
      subtitles: [],
      interimText: "",
    }),
}));
