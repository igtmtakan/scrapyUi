'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  Activity, 
  Database, 
  Play, 
  AlertCircle, 
  CheckCircle, 
  XCircle, 
  Clock,
  Users,
  Server,
  ExternalLink,
  RefreshCw,
  Power,
  PowerOff,
  Trash2,
  Zap,
  Copy
} from 'lucide-react';

interface FlowerStats {
  total_tasks: number;
  pending_tasks: number;
  running_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  revoked_tasks: number;
  total_workers: number;
  active_workers: number;
  offline_workers: number;
  source: string;
  flower_url?: string;
  timestamp: string;
  error?: string;
}

interface FlowerServicesStatus {
  embedded: {
    running: boolean;
    url?: string;
  };
  api: {
    available: boolean;
    url: string;
  };
  standalone: {
    running: boolean;
    process_id?: number;
    url?: string;
  };
  timestamp: string;
}

export default function FlowerDashboard() {
  const [stats, setStats] = useState<FlowerStats | null>(null);
  const [servicesStatus, setServicesStatus] = useState<FlowerServicesStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isCleaningUp, setIsCleaningUp] = useState(false);
  const [cleanupResults, setCleanupResults] = useState<any>(null);

  const fetchFlowerData = async () => {
    try {
      setError(null);
      console.log('🌸 Fetching Flower data...');

      // 統計データを取得
      console.log('📊 Fetching dashboard stats...');
      const statsData = await apiClient.getFlowerDashboardStats();
      console.log('✅ Dashboard stats received:', statsData);
      setStats(statsData);

      // サービス状態を取得
      console.log('🔍 Fetching services status...');
      const statusData = await apiClient.getFlowerServicesStatus();
      console.log('✅ Services status received:', statusData);
      setServicesStatus(statusData);

      console.log('🎉 Flower data fetch completed successfully');
    } catch (err) {
      console.error('❌ Failed to fetch Flower data:', err);
      console.error('❌ Error details:', {
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: err instanceof Error ? err.stack : undefined,
        type: typeof err,
        err
      });
      setError(err instanceof Error ? err.message : 'Failed to fetch Flower data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFlowerData();
    
    // 30秒ごとに自動更新
    const interval = setInterval(fetchFlowerData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchFlowerData();
  };

  const handleStartServices = async () => {
    try {
      setIsRefreshing(true);
      await apiClient.startFlowerServices();
      await fetchFlowerData();
    } catch (err) {
      console.error('Failed to start Flower services:', err);
      setError(err instanceof Error ? err.message : 'Failed to start services');
    }
  };

  const handleStopServices = async () => {
    try {
      setIsRefreshing(true);
      await apiClient.stopFlowerServices();
      await fetchFlowerData();
    } catch (err) {
      console.error('Failed to stop Flower services:', err);
      setError(err instanceof Error ? err.message : 'Failed to stop services');
    }
  };

  const handleCleanupProcesses = async () => {
    try {
      setIsCleaningUp(true);
      setError(null);
      const result = await apiClient.cleanupProcesses();
      setCleanupResults(result);
      await fetchFlowerData(); // データを再取得
    } catch (err) {
      console.error('Failed to cleanup processes:', err);
      setError(err instanceof Error ? err.message : 'Failed to cleanup processes');
    } finally {
      setIsCleaningUp(false);
    }
  };

  const handleCleanupZombies = async () => {
    try {
      setIsCleaningUp(true);
      setError(null);
      const result = await apiClient.cleanupZombieProcesses();
      setCleanupResults(result);
      await fetchFlowerData(); // データを再取得
    } catch (err) {
      console.error('Failed to cleanup zombie processes:', err);
      setError(err instanceof Error ? err.message : 'Failed to cleanup zombie processes');
    } finally {
      setIsCleaningUp(false);
    }
  };

  const handleCleanupDuplicates = async () => {
    try {
      setIsCleaningUp(true);
      setError(null);
      const result = await apiClient.cleanupDuplicateProcesses();
      setCleanupResults(result);
      await fetchFlowerData(); // データを再取得
    } catch (err) {
      console.error('Failed to cleanup duplicate processes:', err);
      setError(err instanceof Error ? err.message : 'Failed to cleanup duplicate processes');
    } finally {
      setIsCleaningUp(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="ml-2 text-gray-300">Loading Flower data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-pink-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Flower Monitoring</h2>
              <p className="text-gray-400">Celery task monitoring and management</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing || isCleaningUp}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              onClick={handleStartServices}
              disabled={isRefreshing || isCleaningUp}
              className="px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <Power className="w-4 h-4" />
              <span>Start</span>
            </button>

            <button
              onClick={handleStopServices}
              disabled={isRefreshing || isCleaningUp}
              className="px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <PowerOff className="w-4 h-4" />
              <span>Stop</span>
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/50 border border-red-600 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-300">{error}</span>
          </div>
        </div>
      )}

      {/* Cleanup Results */}
      {cleanupResults && (
        <div className="bg-green-900/50 border border-green-600 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span className="text-green-300 font-medium">{cleanupResults.message}</span>
            </div>
            <button
              onClick={() => setCleanupResults(null)}
              className="text-green-400 hover:text-green-300"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
          {cleanupResults.results && (
            <div className="text-sm text-green-200 mt-2">
              <pre className="bg-green-900/30 p-2 rounded text-xs overflow-x-auto">
                {JSON.stringify(cleanupResults.results, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Process Cleanup Controls */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
          <Trash2 className="w-5 h-5 text-orange-400" />
          <span>Process Cleanup</span>
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          重複プロセスやゾンビプロセスをクリーンアップして、システムの安定性を向上させます。
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Full Cleanup */}
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Trash2 className="w-5 h-5 text-orange-400" />
              <h4 className="font-medium text-white">完全クリーンアップ</h4>
            </div>
            <p className="text-sm text-gray-400 mb-3">
              重複プロセス、ゾンビプロセス、古いファイルを一括クリーンアップ
            </p>
            <button
              onClick={handleCleanupProcesses}
              disabled={isCleaningUp}
              className="w-full px-3 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-orange-800 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {isCleaningUp ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              <span>{isCleaningUp ? 'クリーンアップ中...' : '完全クリーンアップ'}</span>
            </button>
          </div>

          {/* Zombie Cleanup */}
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Zap className="w-5 h-5 text-yellow-400" />
              <h4 className="font-medium text-white">ゾンビプロセス</h4>
            </div>
            <p className="text-sm text-gray-400 mb-3">
              ゾンビプロセスのみを対象としたクリーンアップ
            </p>
            <button
              onClick={handleCleanupZombies}
              disabled={isCleaningUp}
              className="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {isCleaningUp ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              <span>{isCleaningUp ? 'クリーンアップ中...' : 'ゾンビ除去'}</span>
            </button>
          </div>

          {/* Duplicate Cleanup */}
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Copy className="w-5 h-5 text-purple-400" />
              <h4 className="font-medium text-white">重複プロセス</h4>
            </div>
            <p className="text-sm text-gray-400 mb-3">
              重複プロセスのみを対象としたクリーンアップ
            </p>
            <button
              onClick={handleCleanupDuplicates}
              disabled={isCleaningUp}
              className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {isCleaningUp ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
              <span>{isCleaningUp ? 'クリーンアップ中...' : '重複除去'}</span>
            </button>
          </div>
        </div>

        <div className="mt-4 p-3 bg-blue-900/30 border border-blue-500/30 rounded-lg">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-blue-400 mt-0.5" />
            <div className="text-sm text-blue-200">
              <p className="font-medium mb-1">クリーンアップについて</p>
              <ul className="text-xs space-y-1 text-blue-300">
                <li>• 管理者権限が必要です</li>
                <li>• 実行中のタスクには影響しません</li>
                <li>• システムの安定性向上に役立ちます</li>
                <li>• 定期的な実行を推奨します</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Services Status */}
      {servicesStatus && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Service Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Embedded Service */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300 font-medium">Embedded</span>
                <div className={`w-3 h-3 rounded-full ${servicesStatus.embedded.running ? 'bg-green-400' : 'bg-red-400'}`}></div>
              </div>
              <p className="text-sm text-gray-400">
                {servicesStatus.embedded.running ? 'Running' : 'Stopped'}
              </p>
              {servicesStatus.embedded.url && (
                <a
                  href={servicesStatus.embedded.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center mt-2 text-blue-400 hover:text-blue-300 text-sm"
                >
                  <ExternalLink className="w-4 h-4 mr-1" />
                  Open UI
                </a>
              )}
            </div>

            {/* API Service */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300 font-medium">API</span>
                <div className={`w-3 h-3 rounded-full ${servicesStatus.api.available ? 'bg-green-400' : 'bg-red-400'}`}></div>
              </div>
              <p className="text-sm text-gray-400">
                {servicesStatus.api.available ? 'Available' : 'Unavailable'}
              </p>
              {servicesStatus.api.available && (
                <a
                  href={servicesStatus.api.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center mt-2 text-blue-400 hover:text-blue-300 text-sm"
                >
                  <ExternalLink className="w-4 h-4 mr-1" />
                  Open UI
                </a>
              )}
            </div>

            {/* Standalone Service */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300 font-medium">Standalone</span>
                <div className={`w-3 h-3 rounded-full ${servicesStatus.standalone.running ? 'bg-green-400' : 'bg-red-400'}`}></div>
              </div>
              <p className="text-sm text-gray-400">
                {servicesStatus.standalone.running ? `PID: ${servicesStatus.standalone.process_id}` : 'Stopped'}
              </p>
              {servicesStatus.standalone.url && (
                <a
                  href={servicesStatus.standalone.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center mt-2 text-blue-400 hover:text-blue-300 text-sm"
                >
                  <ExternalLink className="w-4 h-4 mr-1" />
                  Open UI
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Task Statistics */}
      {stats && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Task Statistics</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <span>Source: {stats.source}</span>
              {stats.flower_url && (
                <a
                  href={stats.flower_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {/* Total Tasks */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Database className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.total_tasks}</div>
              <div className="text-sm text-gray-400">Total Tasks</div>
            </div>

            {/* Pending Tasks */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Clock className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.pending_tasks}</div>
              <div className="text-sm text-gray-400">Pending</div>
            </div>

            {/* Running Tasks */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Play className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.running_tasks}</div>
              <div className="text-sm text-gray-400">Running</div>
            </div>

            {/* Successful Tasks */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.successful_tasks}</div>
              <div className="text-sm text-gray-400">Successful</div>
            </div>

            {/* Failed Tasks */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <XCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.failed_tasks}</div>
              <div className="text-sm text-gray-400">Failed</div>
            </div>

            {/* Revoked Tasks */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <AlertCircle className="w-8 h-8 text-orange-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.revoked_tasks}</div>
              <div className="text-sm text-gray-400">Revoked</div>
            </div>
          </div>
        </div>
      )}

      {/* Worker Statistics */}
      {stats && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Worker Statistics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total Workers */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Users className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.total_workers}</div>
              <div className="text-sm text-gray-400">Total Workers</div>
            </div>

            {/* Active Workers */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Server className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.active_workers}</div>
              <div className="text-sm text-gray-400">Active</div>
            </div>

            {/* Offline Workers */}
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{stats.offline_workers}</div>
              <div className="text-sm text-gray-400">Offline</div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-gray-400">
        Last updated: {stats ? new Date(stats.timestamp).toLocaleString() : 'Never'}
      </div>
    </div>
  );
}
