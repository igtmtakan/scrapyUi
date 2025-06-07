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
  AlertCircle,
  BarChart3,
  Globe,
  AlertTriangle,
  Info
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Result {
  id: string;
  data: Record<string, any>;
  url?: string;
  created_at: string;
  crawl_start_datetime?: string;
  item_acquired_datetime?: string;
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
    db_save_enabled?: boolean;
  };
  spider?: {
    id: string;
    name: string;
  };
}

interface ExportFormat {
  format: string;
  name: string;
  description: string;
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
  const [totalResultsCount, setTotalResultsCount] = useState<number>(0);
  // availableFormats は不要（固定で全形式対応）

  useEffect(() => {
    loadData();
  }, [taskId]);

  const loadData = async () => {
    try {
      setIsLoading(true);

      // タスク情報を取得
      const taskData = await apiClient.getTask(taskId);
      setTask(taskData);

      // エクスポート形式は固定で設定（全形式対応）

      // 結果総数を取得
      const countData = await apiClient.getResultsCount(taskId);
      setTotalResultsCount(countData.total_count);

      // 結果データを取得（表示用に制限）
      let resultsData = await apiClient.getResults({
        task_id: taskId,
        limit: 100  // 表示用に制限
      });

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

      // エラーの詳細を表示
      if (error instanceof Error) {
        if (error.message.includes('404') || error.message.includes('Not found')) {
          console.error('Task not found:', taskId);
          alert(`タスクが見つかりません: ${taskId}`);
        } else if (error.message.includes('401') || error.message.includes('Not authenticated')) {
          console.error('Authentication error');
          // 認証エラーの場合は自動的にログインページにリダイレクトされる
        } else {
          console.error('Unexpected error:', error.message);
          alert(`データの読み込みに失敗しました: ${error.message}`);
        }
      }
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
      const fileExtension = format === 'excel' ? 'xlsx' : (format === 'jsonl' ? 'jsonl' : format);
      const filename = `${task?.spider?.name || 'results'}_${timestamp}.${fileExtension}`;
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

  const handleFileDownload = async (format: 'jsonl') => {
    try {
      setIsDownloading(format);

      const blob = await apiClient.downloadTaskResultsFile(taskId, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const fileExtension = format === 'excel' ? 'xlsx' : format;
      const filename = `${task?.spider?.name || 'results'}_${timestamp}_file.${fileExtension}`;
      link.download = filename;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('File download failed:', error);
      alert('ファイルダウンロードに失敗しました。');
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
          <div className="space-y-4">
            {/* DBエクスポート */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center">
                <Database className="w-4 h-4 mr-2" />
                DBエクスポート（データベースから）
              </h4>
              <p className="text-xs text-gray-400 mb-2">
                💾 データベースに保存された結果を各種形式でエクスポートします
              </p>
              <div className="flex flex-wrap gap-2">
                {[
                  { format: 'jsonl', name: 'JSONL', description: 'JSON Lines形式でエクスポート', color: 'bg-green-600 hover:bg-green-700' },
                  { format: 'json', name: 'JSON', description: '標準JSON形式でエクスポート', color: 'bg-blue-600 hover:bg-blue-700' },
                  { format: 'csv', name: 'CSV', description: 'CSV形式でエクスポート', color: 'bg-yellow-600 hover:bg-yellow-700' },
                  { format: 'excel', name: 'Excel', description: 'Excel形式でエクスポート', color: 'bg-purple-600 hover:bg-purple-700' },
                  { format: 'xml', name: 'XML', description: 'XML形式でエクスポート', color: 'bg-red-600 hover:bg-red-700' }
                ].map((format) => {
                  const isDisabled = !task?.project?.db_save_enabled && format.format !== 'jsonl';

                  return (
                    <button
                      key={`db-${format.format}`}
                      onClick={() => handleDownload(format.format as any)}
                      disabled={isDownloading === format.format || isDisabled}
                      className={`px-3 py-2 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${format.color}`}
                      title={isDisabled ? 'DB保存が無効のため利用できません' : format.description}
                    >
                      {isDownloading === format.format ? '...' : format.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* ファイルエクスポート */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center">
                <Download className="w-4 h-4 mr-2" />
                ファイルエクスポート（Scrapyファイルから）
              </h4>
              <p className="text-xs text-gray-400 mb-2">
                💡 Scrapyが生成したJSONLファイルを直接ダウンロードします
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleFileDownload('jsonl')}
                  disabled={isDownloading === 'jsonl'}
                  className="px-3 py-2 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors bg-green-600 hover:bg-green-700"
                  title="JSON Lines形式でダウンロード"
                >
                  {isDownloading === 'jsonl' ? '...' : 'JSONL'}
                </button>
              </div>
            </div>

            {/* DB保存設定の表示 */}
            {task?.project && (
              <div className="px-3 py-2 bg-gray-700 rounded-lg text-sm inline-block">
                <span className="text-gray-400">DB保存: </span>
                <span className={task.project.db_save_enabled ? 'text-green-400' : 'text-yellow-400'}>
                  {task.project.db_save_enabled ? '有効' : '無効'}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Task Summary */}
        {task && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              タスク実行統計
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-2xl font-bold text-blue-400">{task.items_count}</div>
                  <Database className="w-6 h-6 text-blue-400" />
                </div>
                <div className="text-sm text-gray-300 font-medium">処理アイテム数</div>
                <div className="text-xs text-gray-500 mt-1">
                  Scrapyが処理したアイテムの総数
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-2xl font-bold text-green-400">{task.requests_count}</div>
                  <Globe className="w-6 h-6 text-green-400" />
                </div>
                <div className="text-sm text-gray-300 font-medium">HTTPリクエスト数</div>
                <div className="text-xs text-gray-500 mt-1">
                  送信されたWebリクエストの総数
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-2xl font-bold text-red-400">{task.error_count}</div>
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                </div>
                <div className="text-sm text-gray-300 font-medium">エラー数</div>
                <div className="text-xs text-gray-500 mt-1">
                  処理中に発生したエラーの数
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-2xl font-bold text-purple-400">{totalResultsCount}</div>
                  <CheckCircle className="w-6 h-6 text-purple-400" />
                </div>
                <div className="text-sm text-gray-300 font-medium">保存済み結果数</div>
                <div className="text-xs text-gray-500 mt-1">
                  データベースに保存された結果の総数
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-2xl font-bold text-orange-400">
                    {task.items_count > 0 ? Math.round(((task.items_count - totalResultsCount) / task.items_count) * 100) : 0}%
                  </div>
                  <Filter className="w-6 h-6 text-orange-400" />
                </div>
                <div className="text-sm text-gray-300 font-medium">重複除去率</div>
                <div className="text-xs text-gray-500 mt-1">
                  重複として除去されたデータの割合
                </div>
              </div>
            </div>

            {/* 統計の説明 */}
            <div className="mt-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
              <div className="flex items-start space-x-3">
                <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-100">
                  <div className="font-medium mb-2">統計の説明:</div>
                  <ul className="space-y-1 text-xs text-blue-200">
                    <li>• <strong>処理アイテム数</strong>: Scrapyが内部で処理したアイテムの総数（重複除去前）</li>
                    <li>• <strong>HTTPリクエスト数</strong>: Webサイトに送信されたリクエストの総数</li>
                    <li>• <strong>エラー数</strong>: ネットワークエラーや解析エラーなどの発生回数</li>
                    <li>• <strong>保存済み結果数</strong>: 最終的にデータベースに保存された有効な結果の数</li>
                    <li>• <strong>重複除去率</strong>: 同じ内容のデータとして除去された割合</li>
                  </ul>
                  {task.items_count !== totalResultsCount && (
                    <div className="mt-3 p-3 bg-yellow-900/30 border border-yellow-500/30 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-400" />
                        <strong className="text-yellow-200">データ処理の詳細</strong>
                      </div>
                      <div className="text-sm text-yellow-100 space-y-1">
                        <div className="flex justify-between">
                          <span>Scrapyが処理したアイテム:</span>
                          <span className="font-mono">{task.items_count}個</span>
                        </div>
                        <div className="flex justify-between">
                          <span>データベースに保存:</span>
                          <span className="font-mono">{totalResultsCount}個</span>
                        </div>
                        <div className="flex justify-between border-t border-yellow-500/30 pt-1">
                          <span>重複除去・フィルタリング:</span>
                          <span className="font-mono text-yellow-300">-{task.items_count - totalResultsCount}個</span>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-yellow-200">
                        💡 同じ内容のデータは自動的に重複除去されます
                      </div>
                    </div>
                  )}
                </div>
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

        {/* Results Count Info */}
        {totalResultsCount > results.length && (
          <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
            <div className="flex items-center space-x-2 text-blue-200">
              <Info className="w-4 h-4" />
              <span className="text-sm">
                データベースには{totalResultsCount}件の結果がありますが、表示は最新{results.length}件に制限されています。
                全件を確認するには「DBエクスポート」をご利用ください。
              </span>
            </div>
          </div>
        )}

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
                        <div className="text-sm text-gray-400 space-y-1">
                          <p>作成: {formatDate(result.created_at)}</p>
                          {result.crawl_start_datetime && (
                            <p className="flex items-center space-x-1">
                              <Clock className="h-3 w-3" />
                              <span>開始: {formatDate(result.crawl_start_datetime)}</span>
                            </p>
                          )}
                          {result.item_acquired_datetime && (
                            <p className="flex items-center space-x-1">
                              <CheckCircle className="h-3 w-3" />
                              <span>取得: {formatDate(result.item_acquired_datetime)}</span>
                            </p>
                          )}
                        </div>
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
