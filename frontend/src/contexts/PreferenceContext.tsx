/**
 * Preference Context
 * Manages user preferences and adaptive learning
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserPreferences, PreferenceUpdate, LearningStats, RecentAdaptation } from '@/types';
import { preferencesService } from '@/services/preferences';
import { storage, STORAGE_KEYS } from '@/utils/storage';

interface PreferenceContextType {
  preferences: UserPreferences | null;
  learningStats: LearningStats | null;
  recentAdaptations: RecentAdaptation[];
  isLoading: boolean;
  error: string | null;
  updatePreferences: (updates: Partial<UserPreferences>) => Promise<void>;
  trackUpdate: (update: PreferenceUpdate) => Promise<void>;
  toggleLearning: (enabled: boolean) => Promise<void>;
  resetPreferences: () => Promise<void>;
  refreshPreferences: () => Promise<void>;
}

const PreferenceContext = createContext<PreferenceContextType | undefined>(undefined);

export const PreferenceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [learningStats, setLearningStats] = useState<LearningStats | null>(null);
  const [recentAdaptations, setRecentAdaptations] = useState<RecentAdaptation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setIsLoading(true);
    try {
      // Check if user is authenticated before making API call
      const token = storage.get(STORAGE_KEYS.AUTH_TOKEN, null);
      if (!token) {
        // No token, just load from cache
        const cached = storage.get<UserPreferences | null>(STORAGE_KEYS.USER_PREFERENCES, null);
        if (cached) {
          setPreferences(cached);
        }
        setIsLoading(false);
        return;
      }

      // Try to load from API
      const prefs = await preferencesService.getPreferences();
      setPreferences(prefs);
      storage.set(STORAGE_KEYS.USER_PREFERENCES, prefs);

      // Load learning stats if learning is enabled
      if (prefs.learningEnabled) {
        const stats = await preferencesService.getLearningStats();
        setLearningStats(stats);
      }

      setError(null);
    } catch (err) {
      // Fallback to cached preferences
      const cached = storage.get<UserPreferences | null>(STORAGE_KEYS.USER_PREFERENCES, null);
      if (cached) {
        setPreferences(cached);
      }
      setError(err instanceof Error ? err.message : 'Failed to load preferences');
    } finally {
      setIsLoading(false);
    }
  };

  const updatePreferences = async (updates: Partial<UserPreferences>) => {
    try {
      const updated = await preferencesService.updatePreferences(updates);
      setPreferences(updated);
      storage.set(STORAGE_KEYS.USER_PREFERENCES, updated);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      throw err;
    }
  };

  const trackUpdate = async (update: PreferenceUpdate) => {
    try {
      await preferencesService.trackPreferenceUpdate(update);
      
      // Add to recent adaptations if it's a system update
      if (update.source === 'system') {
        const adaptation: RecentAdaptation = {
          id: `${Date.now()}-${Math.random()}`,
          type: update.type,
          description: `Updated ${update.type} preference`,
          confidence: 0.8,
          timestamp: update.timestamp,
          applied: true
        };
        setRecentAdaptations(prev => [adaptation, ...prev].slice(0, 10));
      }
    } catch (err) {
      console.error('Failed to track preference update:', err);
    }
  };

  const toggleLearning = async (enabled: boolean) => {
    try {
      await preferencesService.toggleLearning(enabled);
      setPreferences(prev => prev ? { ...prev, learningEnabled: enabled } : null);
      
      if (enabled) {
        const stats = await preferencesService.getLearningStats();
        setLearningStats(stats);
      } else {
        setLearningStats(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle learning');
      throw err;
    }
  };

  const resetPreferences = async () => {
    try {
      const reset = await preferencesService.resetPreferences();
      setPreferences(reset);
      storage.set(STORAGE_KEYS.USER_PREFERENCES, reset);
      setRecentAdaptations([]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset preferences');
      throw err;
    }
  };

  const refreshPreferences = async () => {
    await loadPreferences();
  };

  return (
    <PreferenceContext.Provider
      value={{
        preferences,
        learningStats,
        recentAdaptations,
        isLoading,
        error,
        updatePreferences,
        trackUpdate,
        toggleLearning,
        resetPreferences,
        refreshPreferences
      }}
    >
      {children}
    </PreferenceContext.Provider>
  );
};

export const usePreferences = () => {
  const context = useContext(PreferenceContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferenceProvider');
  }
  return context;
};
