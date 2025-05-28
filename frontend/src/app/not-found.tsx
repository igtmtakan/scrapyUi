'use client';

import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="max-w-md w-full mx-auto text-center p-6">
        <div className="mb-6">
          <FileQuestion className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h1 className="text-6xl font-bold text-white mb-2">404</h1>
          <h2 className="text-2xl font-bold text-white mb-2">
            ページが見つかりません
          </h2>
          <p className="text-gray-400 mb-6">
            お探しのページは存在しないか、移動された可能性があります。
          </p>
        </div>

        <div className="space-y-3">
          <Link
            href="/"
            className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Home className="w-4 h-4 mr-2" />
            ホームに戻る
          </Link>

          <button
            onClick={() => window.history.back()}
            className="w-full flex items-center justify-center px-4 py-2 border border-gray-600 text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            前のページに戻る
          </button>
        </div>

        <div className="mt-6 text-xs text-gray-500">
          <p>URLが正しいかご確認ください。問題が続く場合は、サイト管理者にお問い合わせください。</p>
        </div>
      </div>
    </div>
  );
}
