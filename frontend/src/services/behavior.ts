/**
 * Behavior Tracking Service
 * API methods for tracking user behavior and engagement
 */
import { api } from './api';
import { BehaviorEvent, PlaybackSession } from '@/types';

export const behaviorService = {
  /**
   * Track a behavior event
   */
  async trackEvent(event: BehaviorEvent): Promise<void> {
    return api.post('/behavior/track', event);
  },

  /**
   * Track multiple events in batch
   */
  async trackBatch(events: BehaviorEvent[]): Promise<void> {
    return api.post('/behavior/track/batch', { events });
  },

  /**
   * Complete a playback session
   */
  async completeSession(session: PlaybackSession): Promise<void> {
    return api.post('/behavior/session/complete', session);
  },

  /**
   * Send explicit feedback
   */
  async sendFeedback(podcastId: string, rating: number, comment?: string): Promise<void> {
    return api.post('/behavior/feedback', {
      podcast_id: podcastId,
      rating,
      comment
    });
  },

  /**
   * Get user engagement stats
   */
  async getEngagementStats(): Promise<{
    totalListeningTime: number;
    averageCompletionRate: number;
    favoriteTopic: string;
    totalPodcasts: number;
  }> {
    return api.get('/behavior/stats');
  }
};
