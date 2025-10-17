/**
 * Preferences Service
 * API methods for user preference management
 */
import { api } from './api';
import { UserPreferences, PreferenceUpdate, LearningStats } from '@/types';

export const preferencesService = {
  /**
   * Get user preferences
   */
  async getPreferences(): Promise<UserPreferences> {
    return api.get<UserPreferences>('/preferences');
  },

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    return api.put<UserPreferences>('/preferences', preferences);
  },

  /**
   * Track preference update (for learning)
   */
  async trackPreferenceUpdate(update: PreferenceUpdate): Promise<void> {
    return api.post('/preferences/track', update);
  },

  /**
   * Get learning statistics
   */
  async getLearningStats(): Promise<LearningStats> {
    return api.get<LearningStats>('/preferences/learning/stats');
  },

  /**
   * Toggle adaptive learning
   */
  async toggleLearning(enabled: boolean): Promise<void> {
    return api.patch('/preferences/learning', { enabled });
  },

  /**
   * Reset preferences to defaults
   */
  async resetPreferences(): Promise<UserPreferences> {
    return api.post<UserPreferences>('/preferences/reset');
  }
};
