'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Shield, AlertTriangle, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AdminGuardProps {
  children: React.ReactNode;
  requireSuperUser?: boolean; // trueの場合はスーパーユーザーのみ、falseの場合は管理者権限でOK
  fallbackPath?: string; // アクセス拒否時のリダイレクト先
}

export default function AdminGuard({ 
  children, 
  requireSuperUser = false,
  fallbackPath = '/dashboard'
}: AdminGuardProps) {
  const router = useRouter();
  const { user, isAuthenticated, isInitialized, isAdmin, isSuperUser } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAdminAccess = () => {
      console.log('🔒 AdminGuard: Checking admin access...');
      console.log('User:', user);
      console.log('Is authenticated:', isAuthenticated);
      console.log('Is initialized:', isInitialized);
      console.log('Require super user:', requireSuperUser);

      // 初期化が完了していない場合は待機
      if (!isInitialized) {
        console.log('⏳ Waiting for initialization...');
        return;
      }

      // 認証されていない場合はログインページへ
      if (!isAuthenticated || !user) {
        console.log('❌ Not authenticated, redirecting to login');
        router.push('/login');
        return;
      }

      // 権限チェック
      const hasRequiredPermission = requireSuperUser ? isSuperUser() : isAdmin();
      
      console.log('🔑 Permission check:', {
        hasRequiredPermission,
        isAdmin: isAdmin(),
        isSuperUser: isSuperUser(),
        userRole: user.role,
        userIsSuperUser: user.is_superuser
      });

      if (!hasRequiredPermission) {
        console.log('❌ Insufficient permissions');
        setIsChecking(false);
        return;
      }

      console.log('✅ Admin access granted');
      setIsChecking(false);
    };

    checkAdminAccess();
  }, [user, isAuthenticated, isInitialized, requireSuperUser, isAdmin, isSuperUser, router]);

  // 初期化中またはチェック中の場合はローディング表示
  if (!isInitialized || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">権限を確認中...</p>
        </div>
      </div>
    );
  }

  // 認証されていない場合（リダイレクト中）
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">ログインページにリダイレクト中...</p>
        </div>
      </div>
    );
  }

  // 権限チェック
  const hasRequiredPermission = requireSuperUser ? isSuperUser() : isAdmin();

  // 権限が不足している場合はアクセス拒否画面を表示
  if (!hasRequiredPermission) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            <CardTitle className="text-xl font-bold text-gray-900 dark:text-white">
              アクセス拒否
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-gray-600 dark:text-gray-300">
              {requireSuperUser 
                ? 'このページにアクセスするにはスーパーユーザー権限が必要です。'
                : 'このページにアクセスするには管理者権限が必要です。'
              }
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                <Shield className="w-4 h-4" />
                <span>現在の権限: {user.role || 'user'}</span>
              </div>
              {user.is_superuser && (
                <div className="mt-1 text-xs text-blue-600 dark:text-blue-400">
                  スーパーユーザー権限あり
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => router.back()}
                className="flex-1"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                戻る
              </Button>
              <Button 
                onClick={() => router.push(fallbackPath)}
                className="flex-1"
              >
                ダッシュボードへ
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 権限がある場合はコンテンツを表示
  return <>{children}</>;
}
