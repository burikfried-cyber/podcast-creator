/**
 * Offline Context
 * Manages offline state and data synchronization
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { OfflineState, Podcast } from '@/types';
import { storage, STORAGE_KEYS } from '@/utils/storage';

interface OfflineContextType extends OfflineState {
  cachedPodcasts: Podcast[];
  syncOfflineData: () => Promise<void>;
  addToCache: (podcast: Podcast) => void;
  removeFromCache: (podcastId: string) => void;
  clearCache: () => void;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export const OfflineProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<OfflineState>({
    isOffline: !navigator.onLine,
    syncStatus: 'synced',
    lastSyncTime: null,
    pendingChanges: 0
  });

  const [cachedPodcasts, setCachedPodcasts] = useState<Podcast[]>(() => {
    return storage.get<Podcast[]>(STORAGE_KEYS.CACHED_PODCASTS, []);
  });

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setState(prev => ({ ...prev, isOffline: false }));
      syncOfflineData();
    };

    const handleOffline = () => {
      setState(prev => ({ ...prev, isOffline: true }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const syncOfflineData = async () => {
    if (state.isOffline) return;

    setState(prev => ({ ...prev, syncStatus: 'syncing' }));

    try {
      // Get offline queue
      const offlineQueue = storage.get<any[]>(STORAGE_KEYS.OFFLINE_QUEUE, []);

      // Sync each queued item
      for (const item of offlineQueue) {
        // Process based on item type
        // This would call appropriate API methods
        console.log('Syncing offline item:', item);
      }

      // Clear queue after successful sync
      storage.set(STORAGE_KEYS.OFFLINE_QUEUE, []);

      setState(prev => ({
        ...prev,
        syncStatus: 'synced',
        lastSyncTime: new Date(),
        pendingChanges: 0
      }));
    } catch (error) {
      console.error('Sync failed:', error);
      setState(prev => ({ ...prev, syncStatus: 'error' }));
    }
  };

  const addToCache = (podcast: Podcast) => {
    setCachedPodcasts(prev => {
      const updated = [...prev.filter(p => p.id !== podcast.id), podcast];
      storage.set(STORAGE_KEYS.CACHED_PODCASTS, updated);
      return updated;
    });
  };

  const removeFromCache = (podcastId: string) => {
    setCachedPodcasts(prev => {
      const updated = prev.filter(p => p.id !== podcastId);
      storage.set(STORAGE_KEYS.CACHED_PODCASTS, updated);
      return updated;
    });
  };

  const clearCache = () => {
    setCachedPodcasts([]);
    storage.remove(STORAGE_KEYS.CACHED_PODCASTS);
  };

  return (
    <OfflineContext.Provider
      value={{
        ...state,
        cachedPodcasts,
        syncOfflineData,
        addToCache,
        removeFromCache,
        clearCache
      }}
    >
      {children}
    </OfflineContext.Provider>
  );
};

export const useOffline = () => {
  const context = useContext(OfflineContext);
  if (context === undefined) {
    throw new Error('useOffline must be used within an OfflineProvider');
  }
  return context;
};
