import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, User } from '@/lib/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  isInitialized: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (userData: {
    email: string;
    username: string;
    full_name: string;
    password: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  getCurrentUser: () => Promise<void>;
  initialize: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      isInitialized: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          await apiClient.login(email, password);
          const user = await apiClient.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false
          });
          throw error;
        }
      },

      register: async (userData) => {
        set({ isLoading: true, error: null });
        try {
          const user = await apiClient.register(userData);
          set({
            user,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Registration failed',
            isLoading: false
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await apiClient.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }
      },

      getCurrentUser: async () => {
        set({ isLoading: true, error: null });
        try {
          const user = await apiClient.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
            error: error instanceof Error ? error.message : 'Failed to get user',
            isLoading: false
          });
        }
      },

      initialize: async () => {
        if (get().isInitialized) {
          console.log('🔄 Already initialized, skipping...');
          return;
        }

        console.log('🚀 Initializing auth store...');
        set({ isLoading: true });
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        console.log('🔑 Token found:', !!token);

        if (!token) {
          console.log('❌ No token, setting as unauthenticated');
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            isInitialized: true
          });
          return;
        }

        try {
          console.log('📡 Verifying token...');
          const user = await apiClient.getCurrentUser();
          console.log('✅ Token valid, user:', user.email);
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true
          });
        } catch (error) {
          console.log('❌ Token invalid, removing:', error);
          // トークンが無効な場合は削除
          if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
          }
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            isInitialized: true
          });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated
      }),
    }
  )
);
