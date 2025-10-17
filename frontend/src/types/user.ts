/**
 * User and Authentication Types
 */

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  tier: 'free' | 'premium' | 'ultra_premium';
  createdAt: Date;
  lastLogin: Date;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

export interface OfflineState {
  isOffline: boolean;
  syncStatus: 'synced' | 'syncing' | 'error' | 'pending';
  lastSyncTime: Date | null;
  pendingChanges: number;
}
