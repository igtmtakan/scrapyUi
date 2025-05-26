'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { 
  ArrowLeft, 
  Play, 
  Square, 
  Download, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  Database,
  FileText,
  Settings,
  Activity
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Task {
  id: string;
  status: 'PENDING' | 'RUNNING' | 'FINISHED' | 'FAILED' | 'CANCELLED';
  started_at?: string;
  finished_at?: string;
  items_count: number;
  requests_count: number;
  error_count: number;
  log_level: string;
  settings?: any;
  created_at: string;
  updated_at: string;
  project_id: string;
  spider_id: string;
  user_id: string;
  project?: {
    id: string;
    name: string;
  };
  spider?: {
    id: string;
    name: string;
  };
}

interface Log {
  id: string;
  level: string;
  message: string;
  timestamp: string;
}

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.id as string;
  
  const [task, setTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'settings'>('overview');

  useEffect(() => {
    loadTaskDetails();
  }, [taskId]);

  const loadTaskDetails = async () => {
    try {
      setIsLoading(true);
      const taskData = await apiClient.getTask(taskId);
      setTask(taskData);
      
      // Load logs if available
      // Note: This would need to be implemented in the API
      // const logsData = await apiClient.getTaskLogs(taskId);
      // setLogs(logsData);
    } catch (error) {
      console.error('Failed to load task details:', error);
      alert('タスクの読み込みに失敗しました。');
      router.push('/tasks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelTask = async () => {
    if (!task || !confirm('このタスクをキャンセルしますか？')) {
      return;
    }

    try {
      await apiClient.cancelTask(task.id);
      await loadTaskDetails(); // Reload task details
      alert('タスクがキャンセルされました。');
    } catch (error) {
      console.error('Failed to cancel task:', error);
      alert('タスクのキャンセルに失敗しました。');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Clock className="w-6 h-6 text-yellow-400" />;
      case 'RUNNING':
        return <Play className="w-6 h-6 text-blue-400" />;
      case 'FINISHED':
        return <CheckCircle className="w-6 h-6 text-green-400" />;
      case 'FAILED':
        return <XCircle className="w-6 h-6 text-red-400" />;
      case 'CANCELLED':
        return <Square className="w-6 h-6 text-gray-400" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'PENDING':
        return '待機中';
      case 'RUNNING':
        return '実行中';
      case 'FINISHED':
        return '完了';
      case 'FAILED':
        return '失敗';
      case 'CANCELLED':
        return 'キャンセル';
      default:
        return '不明';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-900 text-yellow-300';
      case 'RUNNING':
        return 'bg-blue-900 text-blue-300';
      case 'FINISHED':
        return 'bg-green-900 text-green-300';
      case 'FAILED':
        return 'bg-red-900 text-red-300';
      case 'CANCELLED':
        return 'bg-gray-700 text-gray-300';
      default:
        return 'bg-gray-700 text-gray-300';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ja-JP');
  };

  const formatDuration = (startedAt?: string, finishedAt?: string) => {
    if (!startedAt) return '-';
    
    const start = new Date(startedAt);
    const end = finishedAt ? new Date(finishedAt) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (duration < 60) return `${duration}秒`;
    if (duration < 3600) return `${Math.floor(duration / 60)}分`;
    return `${Math.floor(duration / 3600)}時間${Math.floor((duration % 3600) / 60)}分`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-400">タスクを読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">タスクが見つかりません。</p>
          <button
            onClick={() => router.push('/tasks')}
            className="text-blue-400 hover:text-blue-300"
          >
            タスク一覧に戻る
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/tasks')}
                className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
              >
                <ArrowLeft className="h-5 w-5" />
                <span>タスク一覧</span>
              </button>
              <div className="flex items-center space-x-3">
                {getStatusIcon(task.status)}
                <div>
                  <h1 className="text-xl font-semibold">{task.project?.name} / {task.spider?.name}</h1>
                  <p className="text-sm text-gray-400">タスクID: {task.id}</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(task.status)}`}>
                {getStatusText(task.status)}
              </span>
              
              {task.status === 'FINISHED' && (
                <button
                  onClick={() => router.push(`/tasks/${task.id}/results`)}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  <Download className="h-4 w-4" />
                  <span>結果表示</span>
                </button>
              )}
              
              {(task.status === 'PENDING' || task.status === 'RUNNING') && (
                <button
                  onClick={handleCancelTask}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  <Square className="h-4 w-4" />
                  <span>キャンセル</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-blue-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">アイテム数</p>
                <p className="text-2xl font-bold text-white">{task.items_count}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-green-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">リクエスト数</p>
                <p className="text-2xl font-bold text-white">{task.requests_count}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <XCircle className="h-8 w-8 text-red-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">エラー数</p>
                <p className="text-2xl font-bold text-white">{task.error_count}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-purple-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">実行時間</p>
                <p className="text-2xl font-bold text-white">
                  {formatDuration(task.started_at, task.finished_at)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                概要
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'logs'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                ログ
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'settings'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                設定
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Task Timeline */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 text-blue-400">タスクタイムライン</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <div>
                    <p className="text-white">タスク作成</p>
                    <p className="text-sm text-gray-400">{formatDate(task.created_at)}</p>
                  </div>
                </div>
                
                {task.started_at && (
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <div>
                      <p className="text-white">実行開始</p>
                      <p className="text-sm text-gray-400">{formatDate(task.started_at)}</p>
                    </div>
                  </div>
                )}
                
                {task.finished_at && (
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      task.status === 'FINISHED' ? 'bg-green-400' : 'bg-red-400'
                    }`}></div>
                    <div>
                      <p className="text-white">実行終了</p>
                      <p className="text-sm text-gray-400">{formatDate(task.finished_at)}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Project and Spider Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-lg font-semibold mb-4 text-blue-400">プロジェクト情報</h2>
                <div className="space-y-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-400">プロジェクト名</label>
                    <p className="text-white">{task.project?.name}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400">プロジェクトID</label>
                    <p className="text-white font-mono text-sm">{task.project_id}</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-lg font-semibold mb-4 text-blue-400">スパイダー情報</h2>
                <div className="space-y-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-400">スパイダー名</label>
                    <p className="text-white">{task.spider?.name}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400">スパイダーID</label>
                    <p className="text-white font-mono text-sm">{task.spider_id}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-blue-400">実行ログ</h2>
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm">
              {logs.length > 0 ? (
                <div className="space-y-1">
                  {logs.map((log) => (
                    <div key={log.id} className="flex space-x-2">
                      <span className="text-gray-400">{formatDate(log.timestamp)}</span>
                      <span className={`font-medium ${
                        log.level === 'ERROR' ? 'text-red-400' :
                        log.level === 'WARNING' ? 'text-yellow-400' :
                        log.level === 'INFO' ? 'text-blue-400' :
                        'text-gray-300'
                      }`}>
                        [{log.level}]
                      </span>
                      <span className="text-gray-300">{log.message}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400">ログがありません</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-blue-400">タスク設定</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">ログレベル</label>
                <p className="text-white">{task.log_level}</p>
              </div>
              
              {task.settings && (
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">カスタム設定</label>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <pre className="text-sm text-gray-300 overflow-x-auto">
                      {JSON.stringify(task.settings, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
