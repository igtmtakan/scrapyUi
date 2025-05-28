'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // グローバルエラーをログに記録
    console.error('Global application error:', error);
  }, [error]);

  return (
    <html>
      <body className="bg-gray-900 text-white">
        <div className="min-h-screen flex items-center justify-center">
          <div className="max-w-md w-full mx-auto text-center p-6">
            <div className="mb-6">
              <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-white mb-2">
                システムエラー
              </h1>
              <p className="text-gray-400 mb-4">
                アプリケーションで重大なエラーが発生しました。
              </p>
              
              {/* 開発環境でのエラー詳細表示 */}
              {process.env.NODE_ENV === 'development' && (
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4 text-left">
                  <h3 className="text-sm font-medium text-red-400 mb-2">エラー詳細:</h3>
                  <pre className="text-xs text-gray-300 overflow-auto">
                    {error.message}
                  </pre>
                  {error.digest && (
                    <p className="text-xs text-gray-500 mt-2">
                      Error ID: {error.digest}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-3">
              <button
                onClick={reset}
                className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                アプリケーションを再起動
              </button>
              
              <button
                onClick={() => window.location.href = '/'}
                className="w-full flex items-center justify-center px-4 py-2 border border-gray-600 text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
              >
                ホームページに移動
              </button>
            </div>

            <div className="mt-6 text-xs text-gray-500">
              <p>このエラーが続く場合は、ブラウザを再起動するか、システム管理者にお問い合わせください。</p>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
