/**
 * Test Utilities
 * Helper functions and custom render methods for testing
 */
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

interface AllTheProvidersProps {
  children: React.ReactNode;
}

// Wrapper with all providers
const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>{children}</AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Mock user data
export const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  name: 'Test User',
  tier: 'free' as const,
  createdAt: new Date('2024-01-01'),
  lastLogin: new Date('2024-01-15'),
};

// Mock podcast data
export const mockPodcast = {
  id: 'test-podcast-id',
  title: 'Test Podcast',
  description: 'A test podcast about Paris',
  location: 'Paris, France',
  duration: 300,
  audioUrl: 'https://example.com/audio.mp3',
  createdAt: new Date('2024-01-15'),
  status: 'completed' as const,
};

// Mock preferences
export const mockPreferences = {
  topics: {
    history: { weight: 0.8, subcategories: {} },
    culture: { weight: 0.6, subcategories: {} },
  },
  depthPreference: 3,
  surpriseTolerance: 4,
  contextualPreferences: {
    timeOfDay: {},
    deviceType: {},
    locationContext: {},
  },
  learningEnabled: true,
  confidenceScore: 0.7,
};

// Wait for async operations
export const waitFor = (ms: number) =>
  new Promise(resolve => setTimeout(resolve, ms));
