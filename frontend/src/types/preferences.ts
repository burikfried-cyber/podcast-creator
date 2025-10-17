/**
 * User Preference Types
 * Comprehensive type definitions for user preferences and personalization
 */

export interface TopicWeight {
  weight: number; // 0-1 scale
  subcategories: Record<string, number>;
}

export interface ContextualPreference {
  timeOfDay: Record<string, any>;
  deviceType: Record<string, any>;
  locationContext: Record<string, any>;
}

export interface UserPreferences {
  userId: string;
  topics: Record<string, TopicWeight>;
  depthPreference: number; // 1-6 scale
  surpriseTolerance: number; // 1-5 scale
  preferredLength: 'short' | 'medium' | 'long';
  preferredStyle: 'conversational' | 'formal' | 'energetic' | 'calm';
  preferredPace: 'slow' | 'moderate' | 'fast';
  contextualPreferences: ContextualPreference;
  learningEnabled: boolean;
  confidenceScore: number; // 0-1 scale
  interests: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface PreferenceUpdate {
  type: 'topic' | 'depth' | 'surprise' | 'contextual' | 'learning';
  value: any;
  timestamp: Date;
  source: 'explicit' | 'implicit' | 'system';
}

export interface LearningStats {
  totalInteractions: number;
  successfulPredictions: number;
  failedPredictions: number;
  accuracy: number;
  lastUpdated: Date;
}

export interface RecentAdaptation {
  id: string;
  type: string;
  description: string;
  confidence: number;
  timestamp: Date;
  applied: boolean;
}

export const TOPIC_CATEGORIES = [
  'History',
  'Culture',
  'Nature',
  'Architecture',
  'Food',
  'Arts',
  'Science',
  'Folklore',
  'Geography',
  'Society'
] as const;

export type TopicCategory = typeof TOPIC_CATEGORIES[number];

export const DEPTH_LABELS = [
  'Surface',
  'Basic',
  'Intermediate',
  'Advanced',
  'Expert',
  'Academic'
] as const;

export type DepthLabel = typeof DEPTH_LABELS[number];
