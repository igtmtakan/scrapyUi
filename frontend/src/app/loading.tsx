import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">読み込み中...</h2>
        <p className="text-gray-400">しばらくお待ちください</p>
      </div>
    </div>
  );
}
