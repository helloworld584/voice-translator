/**
 * Subtitle display component
 * Shows rolling transcript with interim (gray) and final (white) differentiation.
 * Always visible as fallback channel alongside TTS.
 */
import React, { useRef, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
} from "react-native";
import { useCallStore } from "../store/callStore";

export function SubtitleDisplay() {
  const { subtitles, interimText } = useCallStore();
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [subtitles, interimText]);

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {subtitles.map((sub) => (
          <Text key={sub.id} style={styles.finalText}>
            {sub.text}
          </Text>
        ))}
        {interimText ? (
          <Text style={styles.interimText}>{interimText}</Text>
        ) : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "rgba(0,0,0,0.6)",
    borderRadius: 12,
    padding: 12,
    maxHeight: 180,
    marginHorizontal: 16,
  },
  scroll: {
    flex: 1,
  },
  content: {
    gap: 4,
  },
  finalText: {
    color: "#ffffff",
    fontSize: 16,
    lineHeight: 22,
  },
  interimText: {
    color: "#9ca3af",
    fontSize: 16,
    lineHeight: 22,
    fontStyle: "italic",
  },
});
