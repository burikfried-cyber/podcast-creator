/**
 * Audio Context
 * Manages audio player state and playback
 */
import React, { createContext, useContext, useState, useRef, useEffect, ReactNode, useCallback } from 'react';
import { AudioPlayerState, PlaybackState, BehaviorEvent, PlaybackSession, ListeningContext } from '@/types';
import { behaviorService } from '@/services/behavior';
import { podcastService } from '@/services/podcasts';

interface AudioContextType extends AudioPlayerState {
  audioRef: React.RefObject<HTMLAudioElement>;
  play: () => void;
  pause: () => void;
  seek: (time: number) => void;
  setSpeed: (speed: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  skipForward: (seconds: number) => void;
  skipBackward: (seconds: number) => void;
  loadPodcast: (podcastId: string, audioUrl: string) => void;
  trackBehavior: (type: BehaviorEvent['type'], data?: Record<string, any>) => void;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

export const AudioProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [state, setState] = useState<AudioPlayerState>({
    currentPodcast: null,
    playbackState: 'stopped',
    currentTime: 0,
    duration: 0,
    playbackSpeed: 1.0,
    volume: 1.0,
    isMuted: false,
    isBuffering: false,
    bufferedRanges: [],
    currentSession: null
  });

  const sessionIdRef = useRef<string>(`session-${Date.now()}`);
  const eventsRef = useRef<BehaviorEvent[]>([]);

  // Get listening context
  const getListeningContext = useCallback((): ListeningContext => {
    const hour = new Date().getHours();
    let timeOfDay: ListeningContext['timeOfDay'];
    if (hour < 12) timeOfDay = 'morning';
    else if (hour < 17) timeOfDay = 'afternoon';
    else if (hour < 21) timeOfDay = 'evening';
    else timeOfDay = 'night';

    return {
      deviceType: window.innerWidth < 768 ? 'mobile' : window.innerWidth < 1024 ? 'tablet' : 'desktop',
      timeOfDay,
      networkType: (navigator as any).connection?.effectiveType || 'wifi'
    };
  }, []);

  // Track behavior event
  const trackBehavior = useCallback((type: BehaviorEvent['type'], data: Record<string, any> = {}) => {
    if (!state.currentPodcast) return;

    const event: BehaviorEvent = {
      type,
      timestamp: state.currentTime,
      data: {
        ...data,
        context: getListeningContext()
      },
      podcastId: state.currentPodcast,
      sessionId: sessionIdRef.current
    };

    eventsRef.current.push(event);

    // Send to backend (debounced in real implementation)
    behaviorService.trackEvent(event).catch(console.error);
  }, [state.currentPodcast, state.currentTime, getListeningContext]);

  // Playback controls
  const play = useCallback(() => {
    audioRef.current?.play();
    setState(prev => ({ ...prev, playbackState: 'playing' }));
    trackBehavior('play_start');
  }, [trackBehavior]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
    setState(prev => ({ ...prev, playbackState: 'paused' }));
    trackBehavior('pause', {
      duration_played: state.currentTime,
      completion_percentage: (state.currentTime / state.duration) * 100
    });
  }, [trackBehavior, state.currentTime, state.duration]);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      const oldTime = audioRef.current.currentTime;
      audioRef.current.currentTime = time;
      setState(prev => ({ ...prev, currentTime: time }));
      trackBehavior('seek', {
        from: oldTime,
        to: time,
        seek_direction: time > oldTime ? 'forward' : 'backward'
      });
    }
  }, [trackBehavior]);

  const setSpeed = useCallback((speed: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
      setState(prev => ({ ...prev, playbackSpeed: speed }));
      trackBehavior('speed_change', { from: state.playbackSpeed, to: speed });
    }
  }, [trackBehavior, state.playbackSpeed]);

  const setVolume = useCallback((volume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
      setState(prev => ({ ...prev, volume, isMuted: volume === 0 }));
      trackBehavior('volume_change', { volume });
    }
  }, [trackBehavior]);

  const toggleMute = useCallback(() => {
    if (audioRef.current) {
      const newMuted = !state.isMuted;
      audioRef.current.muted = newMuted;
      setState(prev => ({ ...prev, isMuted: newMuted }));
    }
  }, [state.isMuted]);

  const skipForward = useCallback((seconds: number = 15) => {
    seek(Math.min(state.currentTime + seconds, state.duration));
    trackBehavior('skip_forward', { seconds });
  }, [seek, state.currentTime, state.duration, trackBehavior]);

  const skipBackward = useCallback((seconds: number = 15) => {
    seek(Math.max(state.currentTime - seconds, 0));
    trackBehavior('skip_backward', { seconds });
  }, [seek, state.currentTime, trackBehavior]);

  const loadPodcast = useCallback((podcastId: string, audioUrl: string) => {
    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      setState(prev => ({
        ...prev,
        currentPodcast: podcastId,
        playbackState: 'stopped',
        currentTime: 0
      }));

      // Create new session
      sessionIdRef.current = `session-${Date.now()}`;
      eventsRef.current = [];

      const session: PlaybackSession = {
        sessionId: sessionIdRef.current,
        podcastId,
        startTime: new Date(),
        totalListeningTime: 0,
        completionRate: 0,
        pauseCount: 0,
        seekCount: 0,
        averageSpeed: 1.0,
        context: getListeningContext(),
        events: []
      };

      setState(prev => ({ ...prev, currentSession: session }));
    }
  }, [getListeningContext]);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      setState(prev => ({ ...prev, currentTime: audio.currentTime }));
      
      // Update progress in backend periodically
      if (state.currentPodcast && audio.currentTime % 30 < 0.5) {
        const progress = (audio.currentTime / audio.duration) * 100;
        podcastService.updateProgress(state.currentPodcast, progress).catch(console.error);
      }
    };

    const handleLoadedMetadata = () => {
      setState(prev => ({ ...prev, duration: audio.duration }));
    };

    const handleEnded = () => {
      setState(prev => ({ ...prev, playbackState: 'stopped' }));
      trackBehavior('complete', {
        total_duration: audio.duration,
        completion_rate: 100
      });
      
      // Mark as listened
      if (state.currentPodcast) {
        podcastService.markAsListened(state.currentPodcast).catch(console.error);
      }
    };

    const handleWaiting = () => {
      setState(prev => ({ ...prev, isBuffering: true }));
    };

    const handleCanPlay = () => {
      setState(prev => ({ ...prev, isBuffering: false }));
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [state.currentPodcast, trackBehavior]);

  // Send session data on unmount or podcast change
  useEffect(() => {
    return () => {
      if (state.currentSession && eventsRef.current.length > 0) {
        const session: PlaybackSession = {
          ...state.currentSession,
          endTime: new Date(),
          events: eventsRef.current,
          completionRate: (state.currentTime / state.duration) * 100
        };
        behaviorService.completeSession(session).catch(console.error);
      }
    };
  }, [state.currentSession, state.currentTime, state.duration]);

  return (
    <AudioContext.Provider
      value={{
        ...state,
        audioRef,
        play,
        pause,
        seek,
        setSpeed,
        setVolume,
        toggleMute,
        skipForward,
        skipBackward,
        loadPodcast,
        trackBehavior
      }}
    >
      <audio ref={audioRef} preload="metadata" />
      {children}
    </AudioContext.Provider>
  );
};

export const useAudio = () => {
  const context = useContext(AudioContext);
  if (context === undefined) {
    throw new Error('useAudio must be used within an AudioProvider');
  }
  return context;
};
