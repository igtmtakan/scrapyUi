'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import AuthGuard from '@/components/AuthGuard';

interface AuthProviderProps {
  children: React.ReactNode;
}

export default function AuthProvider({ children }: AuthProviderProps) {
  const { initialize, isInitialized, isLoading } = useAuthStore();

  useEffect(() => {
    // Initialize auth store on app load
    console.log('🏗️ AuthProvider mounted, isInitialized:', isInitialized, 'isLoading:', isLoading);

    if (!isInitialized && !isLoading) {
      console.log('🚀 Starting initialization from AuthProvider...');
      initialize().catch(error => {
        console.error('❌ AuthProvider initialization failed:', error);
        // 失敗した場合でも初期化済みとしてマーク
        useAuthStore.setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isInitialized: true,
          error: 'Authentication initialization failed'
        });
      });
    } else if (isInitialized) {
      console.log('✅ AuthProvider: Already initialized');
    } else if (isLoading) {
      console.log('⏳ AuthProvider: Initialization in progress');
    }
  }, [initialize, isInitialized, isLoading]);

  return (
    <AuthGuard>
      {children}
    </AuthGuard>
  );
}
