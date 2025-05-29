'use client';

import { useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { RefreshCw, Trash2, User, Shield } from 'lucide-react';

export default function DebugPage() {
  const { user, isAuthenticated, clearCacheAndReload, getCurrentUser } = useAuthStore();
  const [isClearing, setIsClearing] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleClearCache = async () => {
    setIsClearing(true);
    try {
      await clearCacheAndReload();
    } catch (error) {
      console.error('Cache clear failed:', error);
    } finally {
      setIsClearing(false);
    }
  };

  const handleRefreshUser = async () => {
    setIsRefreshing(true);
    try {
      await getCurrentUser();
    } catch (error) {
      console.error('User refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">デバッグページ</h1>
        
        <div className="grid gap-6">
          {/* 現在のユーザー情報 */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <User className="w-5 h-5 mr-2" />
              現在のユーザー情報
            </h2>
            
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">認証状態</label>
                  <p className="text-lg">
                    {isAuthenticated ? (
                      <span className="text-green-600 font-semibold">✅ 認証済み</span>
                    ) : (
                      <span className="text-red-600 font-semibold">❌ 未認証</span>
                    )}
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">ユーザーID</label>
                  <p className="text-sm font-mono bg-gray-100 p-2 rounded">
                    {user?.id || 'N/A'}
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">ユーザー名</label>
                  <p className="text-lg">{user?.username || 'N/A'}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">メールアドレス</label>
                  <p className="text-lg">{user?.email || 'N/A'}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">フルネーム</label>
                  <p className="text-lg">{user?.full_name || 'N/A'}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">役割</label>
                  <p className="text-lg flex items-center">
                    {user?.role === 'admin' ? (
                      <>
                        <Shield className="w-4 h-4 mr-1 text-red-500" />
                        <span className="text-red-600 font-semibold">管理者</span>
                      </>
                    ) : user?.role === 'user' ? (
                      <>
                        <User className="w-4 h-4 mr-1 text-blue-500" />
                        <span className="text-blue-600">一般ユーザー</span>
                      </>
                    ) : (
                      'N/A'
                    )}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* デバッグアクション */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">デバッグアクション</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div>
                  <h3 className="font-medium text-yellow-800">ユーザー情報を再取得</h3>
                  <p className="text-sm text-yellow-600">
                    サーバーから最新のユーザー情報を取得します
                  </p>
                </div>
                <Button
                  onClick={handleRefreshUser}
                  disabled={isRefreshing}
                  variant="outline"
                  className="border-yellow-300 text-yellow-700 hover:bg-yellow-100"
                >
                  {isRefreshing ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-2" />
                  )}
                  再取得
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg">
                <div>
                  <h3 className="font-medium text-red-800">キャッシュをクリア</h3>
                  <p className="text-sm text-red-600">
                    ローカルストレージとキャッシュをクリアして再初期化します
                  </p>
                </div>
                <Button
                  onClick={handleClearCache}
                  disabled={isClearing}
                  variant="destructive"
                >
                  {isClearing ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4 mr-2" />
                  )}
                  クリア
                </Button>
              </div>
            </div>
          </Card>

          {/* ローカルストレージ情報 */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">ローカルストレージ</h2>
            
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-500">アクセストークン</label>
                <p className="text-xs font-mono bg-gray-100 p-2 rounded break-all">
                  {typeof window !== 'undefined' && localStorage.getItem('access_token') 
                    ? `${localStorage.getItem('access_token')?.substring(0, 50)}...`
                    : 'なし'
                  }
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">認証ストレージ</label>
                <p className="text-xs font-mono bg-gray-100 p-2 rounded break-all">
                  {typeof window !== 'undefined' && localStorage.getItem('auth-storage')
                    ? localStorage.getItem('auth-storage')
                    : 'なし'
                  }
                </p>
              </div>
            </div>
          </Card>

          {/* 管理者権限チェック */}
          {user?.role === 'admin' && (
            <Card className="p-6 bg-green-50 border-green-200">
              <h2 className="text-xl font-semibold mb-4 text-green-800 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                管理者権限確認
              </h2>
              <p className="text-green-700">
                ✅ 管理者権限が正しく認識されています。ユーザー管理メニューが表示されるはずです。
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
