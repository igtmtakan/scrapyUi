'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import {
  Play,
  Pause,
  Square,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Search,
  Filter,
  Download,
  Eye,
  MoreVertical,
  Calendar,
  User,
  Database
} from 'lucide-react';
import Link from 'next/link';
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

export default function TasksPage() {
  const { user, isAuthenticated } = useAuthStore();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [projectFilter, setProjectFilter] = useState<string>('all');
  const [spiderFilter, setSpiderFilter] = useState<string>('all');
  const [selectedTask, setSelectedTask] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadTasks();
    }
  }, [isAuthenticated]);

  const loadTasks = async () => {
    try {
      setIsLoading(true);
      const tasksData = await apiClient.getTasks();
      setTasks(tasksData);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    if (!confirm('このタスクをキャンセルしますか？')) {
      return;
    }

    try {
      await apiClient.cancelTask(taskId);
      await loadTasks(); // Reload tasks
      alert('タスクがキャンセルされました。');
    } catch (error) {
      console.error('Failed to cancel task:', error);
      alert('タスクのキャンセルに失敗しました。');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'RUNNING':
        return <Play className="w-4 h-4 text-blue-400" />;
      case 'FINISHED':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'CANCELLED':
        return <Square className="w-4 h-4 text-gray-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
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

  const calculateProgress = (task: Task) => {
    // ステータス完了で経過(%) = 100%
    if (task.status === 'FINISHED') {
      return 100;
    }

    if (task.status === 'FAILED' || task.status === 'CANCELLED') {
      return 0;
    }

    if (task.status === 'PENDING') {
      return 0;
    }

    // 実行中の場合: 経過(%) = リクエスト数/アイテム数
    if (task.status === 'RUNNING') {
      if (task.items_count > 0) {
        return Math.min(95, (task.requests_count / task.items_count) * 100);
      } else {
        return 10; // 開始時は10%
      }
    }

    return 0;
  };

  const getProgressBarColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-blue-500';
      case 'FINISHED':
        return 'bg-green-500';
      case 'FAILED':
        return 'bg-red-500';
      case 'CANCELLED':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.project?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         task.spider?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         task.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         task.spider_id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
    const matchesProject = projectFilter === 'all' || task.project?.name === projectFilter;
    const matchesSpider = spiderFilter === 'all' || task.spider?.name === spiderFilter;

    return matchesSearch && matchesStatus && matchesProject && matchesSpider;
  });

  // ユニークなプロジェクト名とスパイダー名を取得
  const uniqueProjects = Array.from(new Set(tasks.map(task => task.project?.name).filter(Boolean)));
  const uniqueSpiders = Array.from(new Set(tasks.map(task => task.spider?.name).filter(Boolean)));

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">ログインが必要です</h1>
          <Link href="/login" className="text-blue-400 hover:text-blue-300">
            ログインページへ
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">タスク管理</h1>
              <p className="text-gray-400 mt-2">
                スクレイピングタスクの実行状況を監視
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={loadTasks}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Database className="w-4 h-4 mr-2" />
                更新
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="プロジェクト名、スパイダー名、タスクID、スパイダーIDで検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative">
              <Filter className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-10 pr-8 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">全てのステータス</option>
                <option value="PENDING">待機中</option>
                <option value="RUNNING">実行中</option>
                <option value="FINISHED">完了</option>
                <option value="FAILED">失敗</option>
                <option value="CANCELLED">キャンセル</option>
              </select>
            </div>

            <div className="relative">
              <Filter className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <select
                value={projectFilter}
                onChange={(e) => setProjectFilter(e.target.value)}
                className="pl-10 pr-8 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">全てのプロジェクト</option>
                {uniqueProjects.map(project => (
                  <option key={project} value={project}>{project}</option>
                ))}
              </select>
            </div>

            <div className="relative">
              <Filter className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <select
                value={spiderFilter}
                onChange={(e) => setSpiderFilter(e.target.value)}
                className="pl-10 pr-8 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">全てのスパイダー</option>
                {uniqueSpiders.map(spider => (
                  <option key={spider} value={spider}>{spider}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Tasks List */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-gray-800 rounded-lg p-6 animate-pulse">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-700 rounded-lg"></div>
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-700 rounded w-32"></div>
                      <div className="h-3 bg-gray-700 rounded w-24"></div>
                    </div>
                  </div>
                  <div className="w-20 h-6 bg-gray-700 rounded"></div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="h-4 bg-gray-700 rounded"></div>
                  <div className="h-4 bg-gray-700 rounded"></div>
                  <div className="h-4 bg-gray-700 rounded"></div>
                  <div className="h-4 bg-gray-700 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">
              {searchTerm || statusFilter !== 'all' ? 'タスクが見つかりません' : 'タスクがありません'}
            </h3>
            <p className="text-gray-400 mb-6">
              {searchTerm || statusFilter !== 'all' || projectFilter !== 'all' || spiderFilter !== 'all'
                ? '検索条件を調整してください'
                : 'プロジェクトでスパイダーを実行するとタスクが表示されます'
              }
            </p>
            <Link
              href="/projects"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              プロジェクト一覧へ
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTasks.map((task) => (
              <div key={task.id} className="bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
                <div className="p-6">
                  {/* Task Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(task.status)}
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {task.project?.name || 'プロジェクト不明'} / {task.spider?.name || 'スパイダー不明'}
                        </h3>
                        <p className="text-sm text-gray-400">
                          タスクID: {task.id}
                        </p>
                        <p className="text-xs text-gray-500">
                          スパイダーID: {task.spider_id}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                        {getStatusText(task.status)}
                      </span>

                      <div className="relative">
                        <button
                          onClick={() => setSelectedTask(selectedTask === task.id ? null : task.id)}
                          className="p-1 text-gray-400 hover:text-gray-300 rounded"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {selectedTask === task.id && (
                          <div className="absolute right-0 mt-2 w-48 bg-gray-700 rounded-lg shadow-lg border border-gray-600 z-10">
                            <div className="py-1">
                              <Link
                                href={`/tasks/${task.id}`}
                                className="flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-600"
                              >
                                <Eye className="w-4 h-4 mr-2" />
                                詳細表示
                              </Link>
                              {task.status === 'FINISHED' && (
                                <Link
                                  href={`/tasks/${task.id}/results`}
                                  className="flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-600"
                                >
                                  <Download className="w-4 h-4 mr-2" />
                                  結果ダウンロード
                                </Link>
                              )}
                              {(task.status === 'PENDING' || task.status === 'RUNNING') && (
                                <button
                                  onClick={() => handleCancelTask(task.id)}
                                  className="flex items-center w-full px-4 py-2 text-sm text-red-400 hover:bg-gray-600"
                                >
                                  <Square className="w-4 h-4 mr-2" />
                                  キャンセル
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Task Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">{task.items_count}</div>
                      <div className="text-xs text-gray-400">アイテム数</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-400">{task.requests_count}</div>
                      <div className="text-xs text-gray-400">リクエスト数</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-400">{task.error_count}</div>
                      <div className="text-xs text-gray-400">エラー数</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-400">
                        {formatDuration(task.started_at, task.finished_at)}
                      </div>
                      <div className="text-xs text-gray-400">実行時間</div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-300">
                        進行状況
                      </span>
                      <span className="text-sm text-gray-400">
                        {calculateProgress(task).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(task.status)}`}
                        style={{ width: `${calculateProgress(task)}%` }}
                      ></div>
                    </div>
                    {task.status === 'RUNNING' && task.items_count > 0 && (
                      <div className="text-xs text-gray-500 mt-1">
                        経過(%) = リクエスト数({task.requests_count}) ÷ アイテム数({task.items_count})
                      </div>
                    )}
                  </div>

                  {/* Task Timeline */}
                  <div className="flex items-center justify-between text-sm text-gray-400">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>作成: {formatDate(task.created_at)}</span>
                    </div>
                    {task.started_at && (
                      <div className="flex items-center space-x-1">
                        <Play className="w-4 h-4" />
                        <span>開始: {formatDate(task.started_at)}</span>
                      </div>
                    )}
                    {task.finished_at && (
                      <div className="flex items-center space-x-1">
                        <CheckCircle className="w-4 h-4" />
                        <span>終了: {formatDate(task.finished_at)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
