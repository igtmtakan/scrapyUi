'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft,
  Download,
  FileText,
  Database,
  Search,
  Filter,
  Eye,
  Copy,
  ExternalLink,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Result {
  id: string;
  data: Record<string, any>;
  url?: string;
  created_at: string;
  task_id: string;
}

interface Task {
  id: string;
  status: 'PENDING' | 'RUNNING' | 'FINISHED' | 'FAILED' | 'CANCELLED';
  started_at?: string;
  finished_at?: string;
  items_count: number;
  requests_count: number;
  error_count: number;
  created_at: string;
  project?: {
    id: string;
    name: string;
  };
  spider?: {
    id: string;
    name: string;
  };
}

export default function TaskResultsPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.id as string;

  const [task, setTask] = useState<Task | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedResult, setSelectedResult] = useState<Result | null>(null);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [taskId]);

  const loadData = async () => {
    try {
      setIsLoading(true);

      // タスク情報を取得
      const taskData = await apiClient.getTask(taskId);
      setTask(taskData);

      // 結果データを取得
      let resultsData = await apiClient.getResults({ task_id: taskId });

      // 結果がない場合は、結果ファイルから読み込みを試行
      if (resultsData.length === 0 && taskData.items_count > 0) {
        try {
          console.log('No results in database, trying to load from file...');
          // apiClientを使用（認証あり）
          const loadResult = await apiClient.request(`/api/tasks/${taskId}/results/load-from-file`, {
            method: 'POST'
          });
          console.log('Loaded results from file:', loadResult);

          // 再度結果データを取得
          resultsData = await apiClient.getResults({ task_id: taskId });
        } catch (fileError) {
          console.error('Failed to load from file:', fileError);
        }
      }

      setResults(resultsData);

    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async (format: 'json' | 'jsonl' | 'csv' | 'excel' | 'xml') => {
    try {
      setIsDownloading(format);

      const blob = await apiClient.downloadTaskResults(taskId, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `${task?.spider?.name || 'results'}_${timestamp}.${format === 'jsonl' ? 'jsonl' : format}`;
      link.download = filename;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Download failed:', error);
      alert('ダウンロードに失敗しました。');
    } finally {
      setIsDownloading(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ja-JP');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('クリップボードにコピーしました');
  };

  const filteredResults = results.filter(result => {
    if (!searchTerm) return true;

    const searchLower = searchTerm.toLowerCase();
    const dataString = JSON.stringify(result.data).toLowerCase();
    const urlString = (result.url || '').toLowerCase();

    return dataString.includes(searchLower) || urlString.includes(searchLower);
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">結果を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.back()}
              className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-white">タスク結果</h1>
              <p className="text-gray-400">
                {task?.project?.name} / {task?.spider?.name}
              </p>
            </div>
          </div>

          {/* Download Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleDownload('json')}
              disabled={isDownloading === 'json'}
              className="px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDownloading === 'json' ? '...' : 'JSON'}
            </button>
            <button
              onClick={() => handleDownload('jsonl')}
              disabled={isDownloading === 'jsonl'}
              className="px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDownloading === 'jsonl' ? '...' : 'JSONL'}
            </button>
            <button
              onClick={() => handleDownload('csv')}
              disabled={isDownloading === 'csv'}
              className="px-3 py-2 bg-yellow-600 text-white text-sm rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDownloading === 'csv' ? '...' : 'CSV'}
            </button>
            <button
              onClick={() => handleDownload('excel')}
              disabled={isDownloading === 'excel'}
              className="px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDownloading === 'excel' ? '...' : 'Excel'}
            </button>
            <button
              onClick={() => handleDownload('xml')}
              disabled={isDownloading === 'xml'}
              className="px-3 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDownloading === 'xml' ? '...' : 'XML'}
            </button>
          </div>
        </div>

        {/* Task Summary */}
        {task && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{task.items_count}</div>
                <div className="text-sm text-gray-400">アイテム数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{task.requests_count}</div>
                <div className="text-sm text-gray-400">リクエスト数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">{task.error_count}</div>
                <div className="text-sm text-gray-400">エラー数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">{results.length}</div>
                <div className="text-sm text-gray-400">結果アイテム数</div>
              </div>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="結果を検索..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Results */}
        {filteredResults.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">
              {searchTerm ? '検索結果が見つかりません' : '結果がありません'}
            </h3>
            <p className="text-gray-400">
              {searchTerm ? '検索条件を調整してください' : 'このタスクではまだ結果が生成されていません'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredResults.map((result, index) => (
              <div key={result.id} className="bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
                <div className="p-6">
                  {/* Result Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          結果 #{index + 1}
                        </h3>
                        <p className="text-sm text-gray-400">
                          {formatDate(result.created_at)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {result.url && (
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-blue-400 hover:text-blue-300 hover:bg-gray-700 rounded-md transition-colors"
                          title="URLを開く"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(result.data, null, 2))}
                        className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-md transition-colors"
                        title="JSONをコピー"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setSelectedResult(selectedResult?.id === result.id ? null : result)}
                        className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-md transition-colors"
                        title="詳細表示"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* URL */}
                  {result.url && (
                    <div className="mb-4">
                      <div className="text-sm text-gray-400 mb-1">URL:</div>
                      <div className="text-sm text-blue-400 break-all">{result.url}</div>
                    </div>
                  )}

                  {/* Data Preview */}
                  <div className="mb-4">
                    <div className="text-sm text-gray-400 mb-2">データプレビュー:</div>
                    <div className="bg-gray-900 rounded-lg p-4 max-h-40 overflow-y-auto">
                      <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {/* Detailed View */}
                  {selectedResult?.id === result.id && (
                    <div className="border-t border-gray-700 pt-4">
                      <div className="text-sm text-gray-400 mb-2">完全なJSONデータ:</div>
                      <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                        <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
