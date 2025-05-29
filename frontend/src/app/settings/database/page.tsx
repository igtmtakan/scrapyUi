'use client';

import React, { useState, useEffect } from 'react';
import {
  Database,
  Server,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Save,
  TestTube,
  BarChart3,
  Shield,
  Download
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';

interface DatabaseConfig {
  type: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  echo: boolean;
  pool_size: number;
  max_overflow: number;
  charset?: string;
}

interface DatabaseHealth {
  type: string;
  status: string;
  message: string;
  timestamp: string;
}

interface DatabaseStats {
  database_type: string;
  statistics: {
    users: number;
    projects: number;
    spiders: number;
    tasks: number;
    results: number;
    task_status: Record<string, number>;
  };
  timestamp: string;
}

export default function DatabaseSettingsPage() {
  const { isAuthenticated, isInitialized, user } = useAuthStore();
  const [config, setConfig] = useState<DatabaseConfig | null>(null);
  const [allConfigs, setAllConfigs] = useState<Record<string, DatabaseConfig>>({});
  const [health, setHealth] = useState<DatabaseHealth[]>([]);
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [supportedTypes, setSupportedTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    if (isInitialized && isAuthenticated && user) {
      loadDatabaseInfo();
    }
  }, [isInitialized, isAuthenticated, user]);

  const loadDatabaseInfo = async () => {
    // 認証されていない場合はスキップ
    if (!isAuthenticated || !user) {
      console.log('DatabaseSettingsPage: Not authenticated, skipping data load');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      // 個別にリクエストして、エラーが発生しても他の情報は取得できるようにする
      try {
        const configRes = await apiClient.request('/api/database/config');
        setConfig(configRes);
      } catch (error) {
        console.error('Failed to load database config:', error);
      }

      try {
        const allConfigsRes = await apiClient.request('/api/database/configs');
        setAllConfigs(allConfigsRes);
      } catch (error) {
        console.error('Failed to load all database configs:', error);
      }

      try {
        const healthRes = await apiClient.request('/api/database/health');
        setHealth(healthRes);
      } catch (error) {
        console.error('Failed to load database health:', error);
        setHealth([]);
      }

      try {
        const statsRes = await apiClient.request('/api/database/statistics');
        setStats(statsRes);
      } catch (error) {
        console.error('Failed to load database statistics:', error);
      }

      try {
        const typesRes = await apiClient.request('/api/database/types');
        setSupportedTypes(typesRes);
      } catch (error) {
        console.error('Failed to load supported types:', error);
        setSupportedTypes([]);
      }
    } catch (error) {
      console.error('Failed to load database info:', error);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (testConfig: any) => {
    try {
      setTesting(true);
      const result = await apiClient.request('/api/database/test-connection', {
        method: 'POST',
        body: JSON.stringify(testConfig)
      });
      setTestResult({ success: true, ...result });
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Connection test failed'
      });
    } finally {
      setTesting(false);
    }
  };

  const backupDatabase = async () => {
    try {
      const result = await apiClient.request('/api/database/backup', {
        method: 'POST'
      });
      alert(`Backup created: ${result.backup_file}`);
    } catch (error: any) {
      alert(`Backup failed: ${error.message}`);
    }
  };

  const clearCache = async () => {
    try {
      await apiClient.request('/api/database/cache', {
        method: 'DELETE'
      });
      alert('Database cache cleared successfully');
      loadDatabaseInfo();
    } catch (error: any) {
      alert(`Failed to clear cache: ${error.message}`);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
  };

  // 認証されていない場合の表示
  if (!isInitialized || !isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <Database className="w-12 h-12 mx-auto mb-4 opacity-50 text-gray-400" />
          <p className="text-lg text-gray-400">
            {!isInitialized ? 'Initializing...' : 'Authentication required'}
          </p>
        </div>
      </div>
    );
  }

  // 管理者権限チェック
  if (user.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <Database className="w-12 h-12 mx-auto mb-4 opacity-50 text-red-400" />
          <p className="text-lg text-red-400 mb-2">Access Denied</p>
          <p className="text-gray-400">
            Administrator privileges required to access database settings.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading database settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <Database className="h-8 w-8 text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold">Database Settings</h1>
              <p className="text-gray-400">Manage database configuration and monitoring</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Current Configuration */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold flex items-center">
                <Settings className="h-5 w-5 mr-2 text-blue-400" />
                Current Configuration
              </h2>
              <button
                onClick={loadDatabaseInfo}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>

            {config && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Database Type
                    </label>
                    <div className="px-3 py-2 bg-gray-700 rounded-md">
                      {config.type.toUpperCase()}
                    </div>
                  </div>

                  {config.host && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Host
                      </label>
                      <div className="px-3 py-2 bg-gray-700 rounded-md">
                        {config.host}:{config.port}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Database
                  </label>
                  <div className="px-3 py-2 bg-gray-700 rounded-md">
                    {config.database}
                  </div>
                </div>

                {config.username && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Username
                    </label>
                    <div className="px-3 py-2 bg-gray-700 rounded-md">
                      {config.username}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Pool Size
                    </label>
                    <div className="px-3 py-2 bg-gray-700 rounded-md">
                      {config.pool_size}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Max Overflow
                    </label>
                    <div className="px-3 py-2 bg-gray-700 rounded-md">
                      {config.max_overflow}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Health Status */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-6 flex items-center">
              <Server className="h-5 w-5 mr-2 text-green-400" />
              Health Status
            </h2>

            <div className="space-y-3">
              {health.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-md">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(item.status)}
                    <div>
                      <div className="font-medium">{item.type.toUpperCase()}</div>
                      <div className="text-sm text-gray-400">{item.message}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Statistics */}
          {stats && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-6 flex items-center">
                <BarChart3 className="h-5 w-5 mr-2 text-purple-400" />
                Database Statistics
              </h2>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center p-3 bg-gray-700 rounded-md">
                  <div className="text-2xl font-bold text-blue-400">{stats.statistics.users}</div>
                  <div className="text-sm text-gray-400">Users</div>
                </div>
                <div className="text-center p-3 bg-gray-700 rounded-md">
                  <div className="text-2xl font-bold text-green-400">{stats.statistics.projects}</div>
                  <div className="text-sm text-gray-400">Projects</div>
                </div>
                <div className="text-center p-3 bg-gray-700 rounded-md">
                  <div className="text-2xl font-bold text-yellow-400">{stats.statistics.spiders}</div>
                  <div className="text-sm text-gray-400">Spiders</div>
                </div>
                <div className="text-center p-3 bg-gray-700 rounded-md">
                  <div className="text-2xl font-bold text-purple-400">{stats.statistics.tasks}</div>
                  <div className="text-sm text-gray-400">Tasks</div>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-300 mb-3">Task Status</h3>
                <div className="space-y-2">
                  {Object.entries(stats.statistics.task_status).map(([status, count]) => (
                    <div key={status} className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">{status}</span>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-6 flex items-center">
              <Shield className="h-5 w-5 mr-2 text-orange-400" />
              Database Actions
            </h2>

            <div className="space-y-4">
              <button
                onClick={() => testConnection(config)}
                disabled={testing || !config}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {testing ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <TestTube className="h-4 w-4" />
                )}
                <span>{testing ? 'Testing...' : 'Test Connection'}</span>
              </button>

              <button
                onClick={backupDatabase}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Create Backup</span>
              </button>

              <button
                onClick={clearCache}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Clear Cache</span>
              </button>
            </div>

            {testResult && (
              <div className={`mt-4 p-3 rounded-md ${testResult.success ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                <div className="flex items-center space-x-2">
                  {testResult.success ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <XCircle className="h-4 w-4" />
                  )}
                  <span className="text-sm font-medium">
                    {testResult.success ? 'Connection Successful' : 'Connection Failed'}
                  </span>
                </div>
                {testResult.message && (
                  <div className="text-xs mt-1">{testResult.message}</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Supported Database Types */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Supported Database Types</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {supportedTypes.map((type) => (
              <div
                key={type}
                className={`p-3 rounded-md text-center ${
                  config?.type === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300'
                }`}
              >
                <Database className="h-6 w-6 mx-auto mb-2" />
                <div className="text-sm font-medium">{type.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
