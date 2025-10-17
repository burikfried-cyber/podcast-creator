/**
 * Audio Player Types
 * Type definitions for audio playback and behavioral tracking
 */

export type PlaybackState = 'stopped' | 'playing' | 'paused' | 'buffering';

export interface PlaybackPosition {
  currentTime: number;
  duration: number;
  percentage: number;
}

export interface BufferedRange {
  start: number;
  end: number;
}

export interface BehaviorEvent {
  type: 'play_start' | 'pause' | 'seek' | 'speed_change' | 'volume_change' | 
        'skip_forward' | 'skip_backward' | 'complete' | 'engagement_update' | 
        'explicit_feedback';
  timestamp: number;
  data: Record<string, any>;
  podcastId: string;
  sessionId: string;
}

export interface ListeningContext {
  deviceType: 'mobile' | 'tablet' | 'desktop';
  timeOfDay: 'morning' | 'afternoon' | 'evening' | 'night';
  location?: string;
  networkType?: 'wifi' | '4g' | '3g' | 'offline';
}

export interface PlaybackSession {
  sessionId: string;
  podcastId: string;
  startTime: Date;
  endTime?: Date;
  totalListeningTime: number;
  completionRate: number;
  pauseCount: number;
  seekCount: number;
  averageSpeed: number;
  context: ListeningContext;
  events: BehaviorEvent[];
}

export interface AudioPlayerState {
  currentPodcast: string | null;
  playbackState: PlaybackState;
  currentTime: number;
  duration: number;
  playbackSpeed: number;
  volume: number;
  isMuted: boolean;
  isBuffering: boolean;
  bufferedRanges: BufferedRange[];
  currentSession: PlaybackSession | null;
}

export interface AudioQuality {
  bitrate: string;
  format: string;
  sampleRate: number;
}

export interface AudioPlayerControls {
  play: () => void;
  pause: () => void;
  seek: (time: number) => void;
  setSpeed: (speed: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  skipForward: (seconds: number) => void;
  skipBackward: (seconds: number) => void;
}

export const PLAYBACK_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2] as const;
export type PlaybackSpeed = typeof PLAYBACK_SPEEDS[number];
