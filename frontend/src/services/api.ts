/**
 * API Service
 * Centralized API client with error handling and interceptors
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { storage, STORAGE_KEYS } from '@/utils/storage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token and log requests
    this.client.interceptors.request.use(
      (config) => {
        console.log('🚀 API Request:', {
          method: config.method?.toUpperCase(),
          url: config.url,
          baseURL: config.baseURL,
          data: config.data,
          headers: config.headers
        });
        
        const token = storage.get(STORAGE_KEYS.AUTH_TOKEN, null);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors and log responses
    this.client.interceptors.response.use(
      (response) => {
        console.log('✅ API Response:', {
          status: response.status,
          url: response.config.url,
          data: response.data
        });
        return response;
      },
      async (error: AxiosError) => {
        console.error('❌ API Error:', {
          status: error.response?.status,
          url: error.config?.url,
          data: error.response?.data,
          message: error.message
        });
        
        if (error.response?.status === 401) {
          // Don't try to refresh if we're already on login/register pages
          const currentPath = window.location.pathname;
          if (currentPath === '/login' || currentPath === '/register') {
            return Promise.reject(error);
          }
          
          // Don't try to refresh if this IS the refresh endpoint
          if (error.config?.url?.includes('/auth/refresh')) {
            storage.remove(STORAGE_KEYS.AUTH_TOKEN);
            storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
            window.location.href = '/login';
            return Promise.reject(error);
          }
          
          // Token expired, try to refresh
          const refreshToken = storage.get(STORAGE_KEYS.REFRESH_TOKEN, null);
          if (refreshToken) {
            try {
              const response = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken
              });
              // Backend returns access_token, not token
              const { access_token } = response.data;
              storage.set(STORAGE_KEYS.AUTH_TOKEN, access_token);
              
              // Retry original request
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${access_token}`;
                return this.client.request(error.config);
              }
            } catch (refreshError) {
              // Refresh failed, clear tokens and redirect
              storage.remove(STORAGE_KEYS.AUTH_TOKEN);
              storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
              // Only redirect if not already on login page
              if (window.location.pathname !== '/login') {
                window.location.href = '/login';
              }
              return Promise.reject(refreshError);
            }
          } else {
            // No refresh token, clear and redirect
            storage.remove(STORAGE_KEYS.AUTH_TOKEN);
            // Only redirect if not already on login page
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Generic request methods
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

export const api = new ApiService();
