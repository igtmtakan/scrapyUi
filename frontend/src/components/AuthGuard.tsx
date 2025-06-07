'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isInitialized } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  // 認証が不要なページのリスト
  const publicPaths = ['/login', '/register', '/'];

  useEffect(() => {
    const checkAuth = () => {
      // ログレベルを下げて重複ログを減らす
      if (process.env.NODE_ENV === 'development') {
        console.log('🔍 AuthGuard: Checking authentication status...');
        console.log('Current path:', pathname);
        console.log('Is authenticated:', isAuthenticated);
        console.log('Is initialized:', isInitialized);
      }

      // パブリックページの場合は認証チェックをスキップ
      if (publicPaths.includes(pathname)) {
        console.log('📖 Public page, skipping auth check');
        setIsChecking(false);
        return;
      }

      // 初期化が完了していない場合は待機
      if (!isInitialized) {
        if (process.env.NODE_ENV === 'development') {
          console.log('⏳ Waiting for initialization...');
        }
        return;
      }

      try {
        // 認証状態をチェック
        const hasTokens = apiClient.hasValidTokens();
        const isAuth = apiClient.isAuthenticated();

        console.log('🔑 Token status:', { hasTokens, isAuth });

        if (!hasTokens || !isAuth || !isAuthenticated) {
          console.warn('❌ Not authenticated, redirecting to login');
          router.push('/login');
          return;
        }

        console.log('✅ Authentication verified');

      } catch (error) {
        console.error('❌ Auth check failed:', error);
        router.push('/login');
      } finally {
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [pathname, isAuthenticated, isInitialized, router]);

  // 認証チェック中の場合はローディング表示
  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">認証状態を確認中...</p>
        </div>
      </div>
    );
  }

  // パブリックページまたは認証済みの場合はコンテンツを表示
  if (publicPaths.includes(pathname) || isAuthenticated) {
    return <>{children}</>;
  }

  // 認証が必要だが未認証の場合はローディング表示（リダイレクト中）
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">ログインページにリダイレクト中...</p>
      </div>
    </div>
  );
}
