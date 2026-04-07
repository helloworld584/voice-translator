/**
 * Main call screen
 * - LiveKit connection
 * - Microphone permission handling
 * - Audio Mixing Mode toggle
 * - Subtitle display
 * - Translation mode selector
 */
import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { Audio } from "expo-av";
import { useCallStore, TranslationMode } from "../store/callStore";
import { useLiveKit } from "../hooks/useLiveKit";
import { AudioMixingToggle } from "../components/AudioMixingToggle";
import { SubtitleDisplay } from "../components/SubtitleDisplay";

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

const TRANSLATION_MODES: { mode: TranslationMode; label: string }[] = [
  { mode: "game_tactical",      label: "게임" },
  { mode: "casual_friend_call", label: "일상" },
  { mode: "polite_professional", label: "공식" },
];

export function CallScreen() {
  const {
    isConnected,
    translationMode,
    setTranslationMode,
    setRoom,
    disconnect,
  } = useCallStore();

  const { connect, disconnect: disconnectLiveKit } = useLiveKit();
  const [loading, setLoading] = useState(false);

  const requestMicPermission = useCallback(async (): Promise<boolean> => {
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== "granted") {
      Alert.alert(
        "마이크 권한 필요",
        "음성 번역을 사용하려면 마이크 접근 권한이 필요합니다.",
        [{ text: "확인" }]
      );
      return false;
    }
    return true;
  }, []);

  const handleConnect = useCallback(async () => {
    const hasPermission = await requestMicPermission();
    if (!hasPermission) return;

    setLoading(true);
    try {
      const roomName = `room-${Date.now()}`;
      const userId = `user-${Math.random().toString(36).slice(2, 8)}`;

      const res = await fetch(`${BACKEND_URL}/rooms/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room_name: roomName, user_id: userId }),
      });
      if (!res.ok) throw new Error("Failed to get room token");

      const { url, token } = await res.json();
      await connect(url, token);
      setRoom(roomName, userId);
    } catch (err) {
      Alert.alert("연결 실패", String(err));
    } finally {
      setLoading(false);
    }
  }, [connect, requestMicPermission, setRoom]);

  const handleDisconnect = useCallback(async () => {
    await disconnectLiveKit();
  }, [disconnectLiveKit]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Voice Translator</Text>

      {/* Translation mode selector */}
      <View style={styles.modeRow}>
        {TRANSLATION_MODES.map(({ mode, label }) => (
          <TouchableOpacity
            key={mode}
            style={[styles.modeBtn, translationMode === mode && styles.modeBtnActive]}
            onPress={() => setTranslationMode(mode)}
          >
            <Text style={[styles.modeBtnText, translationMode === mode && styles.modeBtnTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Connection status */}
      <View style={styles.statusRow}>
        <View style={[styles.statusDot, isConnected && styles.statusDotActive]} />
        <Text style={styles.statusText}>
          {isConnected ? "연결됨" : "연결 안 됨"}
        </Text>
      </View>

      {/* Subtitle display — always visible */}
      <SubtitleDisplay />

      {/* Audio Mixing Mode toggle */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>오디오 믹싱</Text>
        <AudioMixingToggle />
      </View>

      {/* Connect / Disconnect */}
      <TouchableOpacity
        style={[styles.callBtn, isConnected && styles.callBtnEnd]}
        onPress={isConnected ? handleDisconnect : handleConnect}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.callBtnText}>
            {isConnected ? "통화 종료" : "통화 시작"}
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0f1a",
    paddingTop: 60,
    paddingHorizontal: 20,
    gap: 20,
  },
  title: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "700",
    textAlign: "center",
  },
  modeRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 8,
  },
  modeBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#374151",
  },
  modeBtnActive: {
    backgroundColor: "#4f46e5",
    borderColor: "#4f46e5",
  },
  modeBtnText: {
    color: "#9ca3af",
    fontSize: 14,
  },
  modeBtnTextActive: {
    color: "#ffffff",
    fontWeight: "700",
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#6b7280",
  },
  statusDotActive: {
    backgroundColor: "#22c55e",
  },
  statusText: {
    color: "#9ca3af",
    fontSize: 14,
  },
  section: {
    gap: 8,
  },
  sectionLabel: {
    color: "#6b7280",
    fontSize: 12,
    textAlign: "center",
  },
  callBtn: {
    backgroundColor: "#4f46e5",
    borderRadius: 50,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: "auto",
    marginBottom: 40,
  },
  callBtnEnd: {
    backgroundColor: "#dc2626",
  },
  callBtnText: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700",
  },
});
