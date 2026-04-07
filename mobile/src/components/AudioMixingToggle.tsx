/**
 * 3-way Audio Mixing Mode toggle
 * Pass-through | Blend (default) | TTS Only
 */
import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import { useCallStore, AudioMixingMode } from "../store/callStore";

const OPTIONS: { mode: AudioMixingMode; label: string }[] = [
  { mode: "pass_through", label: "원본" },
  { mode: "blend",        label: "혼합" },
  { mode: "tts_only",     label: "번역만" },
];

export function AudioMixingToggle() {
  const { audioMixingMode, setAudioMixingMode } = useCallStore();

  return (
    <View style={styles.container}>
      {OPTIONS.map(({ mode, label }) => (
        <TouchableOpacity
          key={mode}
          style={[styles.option, audioMixingMode === mode && styles.selected]}
          onPress={() => setAudioMixingMode(mode)}
          accessibilityRole="button"
          accessibilityState={{ selected: audioMixingMode === mode }}
        >
          <Text style={[styles.label, audioMixingMode === mode && styles.selectedLabel]}>
            {label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "#1a1a2e",
    borderRadius: 10,
    padding: 3,
    alignSelf: "center",
  },
  option: {
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: 8,
  },
  selected: {
    backgroundColor: "#4f46e5",
  },
  label: {
    color: "#9ca3af",
    fontSize: 14,
    fontWeight: "500",
  },
  selectedLabel: {
    color: "#ffffff",
    fontWeight: "700",
  },
});
