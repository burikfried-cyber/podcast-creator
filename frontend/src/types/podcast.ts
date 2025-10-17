/**
 * Podcast Types
 * Type definitions for podcast content and metadata
 */

export type PodcastType = 'base' | 'standout' | 'topic' | 'personalized';

export type PodcastStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface Location {
  lat: number;
  lng: number;
  name: string;
  country?: string;
  region?: string;
}

export interface PodcastMetadata {
  title: string;
  description: string;
  duration: number; // seconds
  createdAt: Date;
  location: Location;
  topics: string[];
  standoutScore?: number;
  tier?: string;
}

export interface Chapter {
  id: string;
  title: string;
  startTime: number;
  endTime: number;
  description?: string;
}

export interface Podcast {
  id: string;
  userId: string;
  type: PodcastType;
  status: PodcastStatus;
  metadata: PodcastMetadata;
  audioUrl?: string;
  streamingUrl?: string;
  downloadUrl?: string;
  chapters?: Chapter[];
  transcript?: string;
  qualityScore?: number;
  engagementScore?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface PodcastGenerationRequest {
  location: string | Location;
  type: PodcastType;
  preferences?: Partial<UserPreferences>;
  demoMode?: boolean;
}

export interface PodcastGenerationResponse {
  job_id: string;
  status: string;
  message: string;
  podcast_id?: string;
  progress?: number;  // 0-100
}

export interface PodcastLibraryItem {
  id: string;
  title: string;
  location: string;
  duration: number;
  createdAt: Date;
  thumbnailUrl?: string;
  listened: boolean;
  progress: number; // 0-100
}

import { UserPreferences } from './preferences';
