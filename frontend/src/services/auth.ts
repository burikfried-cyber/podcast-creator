/**
 * Authentication Service
 * API methods for user authentication
 */
import { api } from './api';
import { User, LoginCredentials, RegisterData, AuthResponse } from '@/types';
import { storage, STORAGE_KEYS } from '@/utils/storage';

export const authService = {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<any>('/auth/login', credentials);
    
    // Store tokens (backend returns access_token and refresh_token)
    storage.set(STORAGE_KEYS.AUTH_TOKEN, response.access_token);
    storage.set(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);
    
    // Return in expected format
    return {
      token: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user
    };
  },

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<any>('/auth/register', data);
    
    // Store tokens (backend returns access_token and refresh_token)
    storage.set(STORAGE_KEYS.AUTH_TOKEN, response.access_token);
    storage.set(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);
    
    // Return in expected format
    return {
      token: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user
    };
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      // Clear tokens regardless of API response
      storage.remove(STORAGE_KEYS.AUTH_TOKEN);
      storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
    }
  },

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    return api.get<User>('/auth/me');
  },

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    const refreshToken = storage.get(STORAGE_KEYS.REFRESH_TOKEN, null);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post<{ token: string }>('/auth/refresh', {
      refresh_token: refreshToken
    });

    storage.set(STORAGE_KEYS.AUTH_TOKEN, response.token);
    return response.token;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!storage.get(STORAGE_KEYS.AUTH_TOKEN, null);
  }
};
