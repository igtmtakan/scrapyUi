'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import AuthGuard from '@/components/AuthGuard';

interface AuthProviderProps {
  children: React.ReactNode;
}

export default function AuthProvider({ children }: AuthProviderProps) {
  const { initialize, isInitialized } = useAuthStore();

  useEffect(() => {
    // Initialize auth store on app load
    if (!isInitialized) {
      initialize();
    }
  }, [initialize, isInitialized]);

  return (
    <AuthGuard>
      {children}
    </AuthGuard>
  );
}
