/**
 * Podcast Service
 * API methods for podcast generation and management
 */
import { api } from './api';
import {
  Podcast,
  PodcastGenerationRequest,
  PodcastGenerationResponse,
  PodcastLibraryItem
} from '@/types';

export const podcastService = {
  /**
   * Generate a new podcast
   */
  async generatePodcast(request: PodcastGenerationRequest): Promise<PodcastGenerationResponse> {
    return api.post<PodcastGenerationResponse>('/podcasts/generate', request);
  },

  /**
   * Get podcast by ID
   */
  async getPodcast(id: string): Promise<Podcast> {
    return api.get<Podcast>(`/podcasts/${id}`);
  },

  /**
   * Get podcast generation status
   */
  async getPodcastStatus(jobId: string): Promise<PodcastGenerationResponse> {
    return api.get<PodcastGenerationResponse>(`/podcasts/status/${jobId}`);
  },

  /**
   * Get user's podcast library
   */
  async getLibrary(params?: {
    skip?: number;
    limit?: number;
    status_filter?: string;
  }): Promise<{ podcasts: PodcastLibraryItem[]; total: number; skip: number; limit: number }> {
    return api.get('/podcasts/', params);
  },

  /**
   * Delete a podcast
   */
  async deletePodcast(id: string): Promise<void> {
    return api.delete(`/podcasts/${id}`);
  },

  /**
   * Update podcast listening progress
   */
  async updateProgress(id: string, progress: number): Promise<void> {
    return api.patch(`/podcasts/${id}/progress`, { progress });
  },

  /**
   * Mark podcast as listened
   */
  async markAsListened(id: string): Promise<void> {
    return api.patch(`/podcasts/${id}/listened`, { listened: true });
  },

  /**
   * Get recommended podcasts based on user preferences
   */
  async getRecommendations(limit: number = 10): Promise<PodcastLibraryItem[]> {
    return api.get('/podcasts/recommendations', { limit });
  }
};
