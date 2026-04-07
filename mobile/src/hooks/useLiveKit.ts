/**
 * LiveKit connection hook — uses livekit-client (web + native 공용)
 * Audio mixing mode에 따라 수신 트랙 볼륨 조절
 */
import { useEffect, useRef, useCallback } from 'react';
import { Room, RoomEvent, Track, RemoteTrack } from 'livekit-client';
import { useCallStore, AudioMixingMode } from '../store/callStore';

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

    await room.connect(url, token);
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

  const applyMixingMode = useCallback((mode: AudioMixingMode) => {
    if (!roomRef.current) return;
    const volumes = MIXING_VOLUMES[mode];

    roomRef.current.remoteParticipants.forEach((participant) => {
      participant.trackPublications.forEach((pub) => {
        if (!pub.track || pub.track.kind !== Track.Kind.Audio) return;
        const isTTS = (pub.trackName || '').includes('tts');
        const volume = isTTS ? volumes.tts : volumes.original;
        (pub.track as RemoteTrack).setVolume(volume);
      });
    });
  }, []);

  useEffect(() => {
    applyMixingMode(audioMixingMode);
  }, [audioMixingMode, applyMixingMode]);

  return { connect, disconnect: disconnectRoom, applyMixingMode };
}
