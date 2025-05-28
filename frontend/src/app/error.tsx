'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // エラーをログに記録
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="max-w-md w-full mx-auto text-center p-6">
        <div className="mb-6">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">
            エラーが発生しました
          </h1>
          <p className="text-gray-400 mb-4">
            申し訳ございません。予期しないエラーが発生しました。
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
            再試行
          </button>
          
          <a
            href="/"
            className="w-full flex items-center justify-center px-4 py-2 border border-gray-600 text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Home className="w-4 h-4 mr-2" />
            ホームに戻る
          </a>
        </div>

        <div className="mt-6 text-xs text-gray-500">
          <p>問題が続く場合は、ページを再読み込みするか、しばらく時間をおいてから再度お試しください。</p>
        </div>
      </div>
    </div>
  );
}
