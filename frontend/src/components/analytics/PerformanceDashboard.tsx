'use client';

import { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';

interface PerformanceStats {
  cpu_avg: number;
  memory_avg: number;
  disk_usage: number;
  network_throughput: number;
  active_spiders: number;
  total_requests: number;
  success_rate: number;
  avg_response_time: number;
}

interface PerformanceDashboardProps {
  projectId: string;
}

export default function PerformanceDashboard({ projectId }: PerformanceDashboardProps) {
  const { isAuthenticated, isInitialized, user } = useAuthStore();
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isInitialized && isAuthenticated && user && projectId) {
      loadStats();
      const interval = setInterval(() => {
        if (isAuthenticated && user) {
          loadStats();
        }
      }, 5000); // 5秒ごとに更新
      return () => clearInterval(interval);
    }
  }, [isInitialized, isAuthenticated, user, projectId]);

  const loadStats = async () => {
    // 認証されていない場合はスキップ
    if (!isAuthenticated || !user) {
      console.log('PerformanceDashboard: Not authenticated, skipping data load');
      setIsLoading(false);
      return;
    }

    try {
      const data = await apiClient.request(`/api/projects/${projectId}/monitoring/stats`);
      setStats(data);
    } catch (error) {
      console.error('Failed to load performance stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startMonitoring = async () => {
    try {
      await apiClient.request(`/api/projects/${projectId}/monitoring/start`, {
        method: 'POST'
      });
      setIsMonitoring(true);
      alert('パフォーマンス監視を開始しました');
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      alert('監視の開始に失敗しました');
    }
  };

  const stopMonitoring = async () => {
    try {
      await apiClient.request(`/api/projects/${projectId}/monitoring/stop`, {
        method: 'POST'
      });
      setIsMonitoring(false);
      alert('パフォーマンス監視を停止しました');
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
      alert('監視の停止に失敗しました');
    }
  };

  const getStatusColor = (value: number, thresholds: { warning: number; danger: number }) => {
    if (value >= thresholds.danger) return 'text-red-400';
    if (value >= thresholds.warning) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getStatusIcon = (value: number, thresholds: { warning: number; danger: number }) => {
    if (value >= thresholds.danger) return <AlertTriangle className="h-5 w-5 text-red-400" />;
    if (value >= thresholds.warning) return <AlertTriangle className="h-5 w-5 text-yellow-400" />;
    return <CheckCircle className="h-5 w-5 text-green-400" />;
  };

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center">
          <Activity className="h-6 w-6 animate-pulse text-blue-400" />
          <span className="ml-2 text-gray-300">パフォーマンスデータを読み込み中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 監視制御 */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-blue-400 flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            リアルタイム監視
          </h3>
          <div className="flex space-x-2">
            <button
              onClick={startMonitoring}
              disabled={isMonitoring}
              className={`px-4 py-2 rounded-md transition-colors ${
                isMonitoring
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              監視開始
            </button>
            <button
              onClick={stopMonitoring}
              disabled={!isMonitoring}
              className={`px-4 py-2 rounded-md transition-colors ${
                !isMonitoring
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              監視停止
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isMonitoring ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
          <span className="text-gray-300">
            {isMonitoring ? '監視中' : '監視停止中'}
          </span>
        </div>
      </div>

      {/* システムメトリクス */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* CPU使用率 */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Cpu className="h-5 w-5 text-blue-400" />
              <span className="text-gray-300">CPU使用率</span>
            </div>
            {stats && getStatusIcon(stats.cpu_avg, { warning: 70, danger: 90 })}
          </div>
          <div className={`text-2xl font-bold ${stats ? getStatusColor(stats.cpu_avg, { warning: 70, danger: 90 }) : 'text-gray-400'}`}>
            {stats ? `${stats.cpu_avg.toFixed(1)}%` : 'N/A'}
          </div>
          <div className="mt-2 bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${stats ? Math.min(stats.cpu_avg, 100) : 0}%` }}
            ></div>
          </div>
        </div>

        {/* メモリ使用率 */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <MemoryStick className="h-5 w-5 text-green-400" />
              <span className="text-gray-300">メモリ使用率</span>
            </div>
            {stats && getStatusIcon(stats.memory_avg, { warning: 70, danger: 90 })}
          </div>
          <div className={`text-2xl font-bold ${stats ? getStatusColor(stats.memory_avg, { warning: 70, danger: 90 }) : 'text-gray-400'}`}>
            {stats ? `${stats.memory_avg.toFixed(1)}%` : 'N/A'}
          </div>
          <div className="mt-2 bg-gray-700 rounded-full h-2">
            <div
              className="bg-green-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${stats ? Math.min(stats.memory_avg, 100) : 0}%` }}
            ></div>
          </div>
        </div>

        {/* ディスク使用率 */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <HardDrive className="h-5 w-5 text-purple-400" />
              <span className="text-gray-300">ディスク使用率</span>
            </div>
            {stats && getStatusIcon(stats.disk_usage, { warning: 80, danger: 95 })}
          </div>
          <div className={`text-2xl font-bold ${stats ? getStatusColor(stats.disk_usage, { warning: 80, danger: 95 }) : 'text-gray-400'}`}>
            {stats ? `${stats.disk_usage.toFixed(1)}%` : 'N/A'}
          </div>
          <div className="mt-2 bg-gray-700 rounded-full h-2">
            <div
              className="bg-purple-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${stats ? Math.min(stats.disk_usage, 100) : 0}%` }}
            ></div>
          </div>
        </div>

        {/* ネットワーク */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-2">
            <Network className="h-5 w-5 text-orange-400" />
            <span className="text-gray-300">ネットワーク</span>
          </div>
          <div className="text-2xl font-bold text-orange-400">
            {stats ? `${(stats.network_throughput / 1024 / 1024).toFixed(1)} MB` : 'N/A'}
          </div>
          <div className="text-sm text-gray-400">総転送量</div>
        </div>
      </div>

      {/* Scrapyメトリクス */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* アクティブスパイダー */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-2">
            <Zap className="h-5 w-5 text-yellow-400" />
            <span className="text-gray-300">アクティブスパイダー</span>
          </div>
          <div className="text-2xl font-bold text-yellow-400">
            {stats ? stats.active_spiders : 0}
          </div>
          <div className="text-sm text-gray-400">実行中</div>
        </div>

        {/* 総リクエスト数 */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-2">
            <TrendingUp className="h-5 w-5 text-blue-400" />
            <span className="text-gray-300">総リクエスト数</span>
          </div>
          <div className="text-2xl font-bold text-blue-400">
            {stats ? stats.total_requests.toLocaleString() : 0}
          </div>
          <div className="text-sm text-gray-400">累計</div>
        </div>

        {/* 成功率 */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <span className="text-gray-300">成功率</span>
            </div>
            {stats && getStatusIcon(100 - stats.success_rate, { warning: 10, danger: 20 })}
          </div>
          <div className={`text-2xl font-bold ${stats ? getStatusColor(100 - stats.success_rate, { warning: 10, danger: 20 }) : 'text-gray-400'}`}>
            {stats ? `${stats.success_rate.toFixed(1)}%` : 'N/A'}
          </div>
          <div className="mt-2 bg-gray-700 rounded-full h-2">
            <div
              className="bg-green-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${stats ? stats.success_rate : 0}%` }}
            ></div>
          </div>
        </div>

        {/* 平均レスポンス時間 */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="h-5 w-5 text-indigo-400" />
            <span className="text-gray-300">平均レスポンス時間</span>
          </div>
          <div className="text-2xl font-bold text-indigo-400">
            {stats ? `${stats.avg_response_time.toFixed(2)}s` : 'N/A'}
          </div>
          <div className="text-sm text-gray-400">秒</div>
        </div>
      </div>

      {/* パフォーマンス警告 */}
      {stats && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-400 mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            パフォーマンス警告
          </h3>
          <div className="space-y-2">
            {stats.cpu_avg > 90 && (
              <div className="flex items-center space-x-2 text-red-400">
                <AlertTriangle className="h-4 w-4" />
                <span>CPU使用率が危険レベルです ({stats.cpu_avg.toFixed(1)}%)</span>
              </div>
            )}
            {stats.memory_avg > 90 && (
              <div className="flex items-center space-x-2 text-red-400">
                <AlertTriangle className="h-4 w-4" />
                <span>メモリ使用率が危険レベルです ({stats.memory_avg.toFixed(1)}%)</span>
              </div>
            )}
            {stats.success_rate < 90 && (
              <div className="flex items-center space-x-2 text-yellow-400">
                <AlertTriangle className="h-4 w-4" />
                <span>成功率が低下しています ({stats.success_rate.toFixed(1)}%)</span>
              </div>
            )}
            {stats.avg_response_time > 5 && (
              <div className="flex items-center space-x-2 text-yellow-400">
                <AlertTriangle className="h-4 w-4" />
                <span>レスポンス時間が遅くなっています ({stats.avg_response_time.toFixed(2)}s)</span>
              </div>
            )}
            {stats.cpu_avg <= 90 && stats.memory_avg <= 90 && stats.success_rate >= 90 && stats.avg_response_time <= 5 && (
              <div className="flex items-center space-x-2 text-green-400">
                <CheckCircle className="h-4 w-4" />
                <span>すべてのメトリクスが正常範囲内です</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
