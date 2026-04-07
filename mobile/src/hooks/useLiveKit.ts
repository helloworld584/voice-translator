/**
 * LiveKit connection hook
 * Manages room connect/disconnect and audio track volume for mixing modes.
 */
import { useEffect, useRef, useCallback } from "react";
import {
  useRoom,
  useLocalParticipant,
  useRemoteParticipants,
  RoomEvent,
} from "@livekit/react-native";
import { Room, RoomOptions } from "livekit-client";
import { useCallStore, AudioMixingMode } from "../store/callStore";

const MIXING_VOLUMES: Record<AudioMixingMode, { original: number; tts: number }> = {
  pass_through: { original: 1.0, tts: 1.0 },
  blend:        { original: 0.3, tts: 1.0 },
  tts_only:     { original: 0.0, tts: 1.0 },
};

export function useLiveKit() {
  const { audioMixingMode, setConnected, disconnect } = useCallStore();
  const roomRef = useRef<Room | null>(null);

  const connect = useCallback(async (url: string, token: string) => {
    const room = new Room();
    roomRef.current = room;

    room.on(RoomEvent.Disconnected, () => {
      disconnect();
    });

    await room.connect(url, token, {
      autoSubscribe: true,
    } as RoomOptions);

    setConnected(true);
    return room;
  }, [setConnected, disconnect]);

  const disconnectRoom = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    disconnect();
  }, [disconnect]);

  // Apply audio mixing mode to remote participant tracks
  const applyMixingMode = useCallback((mode: AudioMixingMode) => {
    if (!roomRef.current) return;
    const volumes = MIXING_VOLUMES[mode];

    roomRef.current.remoteParticipants.forEach((participant) => {
      participant.audioTrackPublications.forEach((pub) => {
        if (!pub.track) return;
        const trackName = pub.trackName || "";
        // TTS tracks are published with name "tts"
        const isTTS = trackName.includes("tts");
        const volume = isTTS ? volumes.tts : volumes.original;
        pub.track.setVolume(volume);
      });
    });
  }, []);

  useEffect(() => {
    applyMixingMode(audioMixingMode);
  }, [audioMixingMode, applyMixingMode]);

  return { connect, disconnect: disconnectRoom, applyMixingMode };
}
