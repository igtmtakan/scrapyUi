'use client'

import React, { useState, useEffect } from 'react'
import {
  Activity,
  Database,
  Server,
  Globe,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock
} from 'lucide-react'
import { apiClient } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

interface ServiceStatus {
  status: 'running' | 'stopped' | 'error' | 'unknown'
  message: string
}

interface SystemStatusData {
  timestamp: string
  services: {
    redis: ServiceStatus
    celery_worker: ServiceStatus
    celery_scheduler: ServiceStatus
    fastapi_backend: ServiceStatus
    scheduler: ServiceStatus
    nodejs_puppeteer: ServiceStatus
    nextjs_frontend: ServiceStatus
  }
}

interface SystemMetrics {
  timestamp: string
  cpu: {
    usage_percent: number
    count: number
    frequency?: {
      current: number
      min: number
      max: number
    }
  }
  memory: {
    virtual: {
      total: number
      available: number
      used: number
      percent: number
    }
    swap: {
      total: number
      used: number
      percent: number
    }
  }
  disk: {
    total: number
    used: number
    free: number
    percent: number
  }
  network: {
    bytes_sent: number
    bytes_recv: number
    packets_sent: number
    packets_recv: number
  }
}

export default function SystemStatus() {
  const { isAuthenticated, isInitialized, user } = useAuthStore()
  const [systemStatus, setSystemStatus] = useState<SystemStatusData | null>(null)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchSystemStatus = async () => {
    // 認証されていない場合はスキップ
    if (!isAuthenticated || !user) {
      console.log('SystemStatus: Not authenticated, skipping data load')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)

      // apiClientを使用（認証あり）
      const [statusData, metricsData] = await Promise.all([
        apiClient.request('/api/system/status'),
        apiClient.request('/api/system/metrics')
      ])

      setSystemStatus(statusData)
      setSystemMetrics(metricsData)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch system data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch system data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isInitialized && isAuthenticated && user) {
      fetchSystemStatus()

      // 30秒ごとに自動更新
      const interval = setInterval(fetchSystemStatus, 30000)

      return () => clearInterval(interval)
    }
  }, [isInitialized, isAuthenticated, user])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'stopped':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />
      default:
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-400'
      case 'stopped':
        return 'text-red-400'
      case 'error':
        return 'text-red-400'
      default:
        return 'text-yellow-400'
    }
  }

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName) {
      case 'redis':
        return <Database className="w-5 h-5 text-red-400" />
      case 'celery_worker':
        return <Activity className="w-5 h-5 text-green-400" />
      case 'celery_scheduler':
        return <Clock className="w-5 h-5 text-orange-400" />
      case 'fastapi_backend':
        return <Server className="w-5 h-5 text-blue-400" />
      case 'scheduler':
        return <Clock className="w-5 h-5 text-purple-400" />
      case 'nodejs_puppeteer':
        return <Globe className="w-5 h-5 text-yellow-400" />
      case 'nextjs_frontend':
        return <Globe className="w-5 h-5 text-cyan-400" />
      default:
        return <Server className="w-5 h-5 text-gray-400" />
    }
  }

  const getServiceDisplayName = (serviceName: string) => {
    switch (serviceName) {
      case 'redis':
        return 'Redis Cache'
      case 'celery_worker':
        return 'Celery Worker'
      case 'celery_scheduler':
        return 'Celery Scheduler'
      case 'fastapi_backend':
        return 'FastAPI Backend'
      case 'scheduler':
        return 'Task Scheduler'
      case 'nodejs_puppeteer':
        return 'Node.js Puppeteer'
      case 'nextjs_frontend':
        return 'Next.js Frontend'
      default:
        return serviceName
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getUsageColor = (percent: number) => {
    if (percent < 50) return 'bg-green-500'
    if (percent < 80) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  // 認証されていない場合の表示
  if (!isInitialized || !isAuthenticated || !user) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Server className="w-8 h-8 mx-auto mb-2 opacity-50 text-gray-400" />
            <p className="text-sm text-gray-400">
              {!isInitialized ? 'Initializing...' : 'Authentication required'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (loading && !systemStatus) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
          <span className="ml-2 text-gray-400">Loading system status...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-400 font-medium">Error loading system status</span>
          </div>
          <p className="text-red-300 mt-2">{error}</p>
          <button
            onClick={fetchSystemStatus}
            className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!systemStatus) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-400">No system status data available</div>
      </div>
    )
  }

  const runningServices = Object.values(systemStatus.services).filter(s => s.status === 'running').length
  const totalServices = Object.keys(systemStatus.services).length

  return (
    <div className="p-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">System Status</h2>
          <p className="text-gray-400 mt-1">
            {runningServices}/{totalServices} services running
          </p>
        </div>

        <div className="flex items-center space-x-4">
          {lastUpdated && (
            <div className="text-sm text-gray-400">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={fetchSystemStatus}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* サービス状態一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* サービスを論理的な順序で表示 */}
        {[
          'fastapi_backend',
          'redis',
          'celery_worker',
          'celery_scheduler',
          'scheduler',
          'nodejs_puppeteer',
          'nextjs_frontend'
        ].filter(serviceName => systemStatus.services[serviceName as keyof typeof systemStatus.services])
         .map(serviceName => {
           const service = systemStatus.services[serviceName as keyof typeof systemStatus.services]
           return (
          <div
            key={serviceName}
            className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                {getServiceIcon(serviceName)}
                <h3 className="text-white font-medium">
                  {getServiceDisplayName(serviceName)}
                </h3>
              </div>
              {getStatusIcon(service.status)}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-400 text-sm">Status:</span>
                <span className={`text-sm font-medium ${getStatusColor(service.status)}`}>
                  {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                </span>
              </div>

              <div className="text-sm text-gray-300">
                {service.message}
              </div>
            </div>
          </div>
           )
         })}
      </div>

      {/* システム概要 */}
      <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">System Overview</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400">{runningServices}</div>
            <div className="text-gray-400 text-sm">Running Services</div>
          </div>

          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400">
              {Math.round((runningServices / totalServices) * 100)}%
            </div>
            <div className="text-gray-400 text-sm">System Health</div>
          </div>

          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400">
              {new Date(systemStatus.timestamp).toLocaleTimeString()}
            </div>
            <div className="text-gray-400 text-sm">Last Check</div>
          </div>
        </div>
      </div>

      {/* システムメトリクス */}
      {systemMetrics && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* CPU & Memory */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">CPU & Memory</h3>

            <div className="space-y-4">
              {/* CPU使用率 */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-400">CPU Usage</span>
                  <span className="text-white">{systemMetrics.cpu.usage_percent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(systemMetrics.cpu.usage_percent)}`}
                    style={{ width: `${Math.min(systemMetrics.cpu.usage_percent, 100)}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {systemMetrics.cpu.count} cores
                </div>
              </div>

              {/* メモリ使用率 */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-400">Memory Usage</span>
                  <span className="text-white">
                    {formatBytes(systemMetrics.memory.virtual.used)} / {formatBytes(systemMetrics.memory.virtual.total)}
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(systemMetrics.memory.virtual.percent)}`}
                    style={{ width: `${systemMetrics.memory.virtual.percent}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {systemMetrics.memory.virtual.percent.toFixed(1)}% used
                </div>
              </div>
            </div>
          </div>

          {/* Disk & Network */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Disk & Network</h3>

            <div className="space-y-4">
              {/* ディスク使用率 */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-400">Disk Usage</span>
                  <span className="text-white">
                    {formatBytes(systemMetrics.disk.used)} / {formatBytes(systemMetrics.disk.total)}
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(systemMetrics.disk.percent)}`}
                    style={{ width: `${systemMetrics.disk.percent}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {systemMetrics.disk.percent.toFixed(1)}% used
                </div>
              </div>

              {/* ネットワーク統計 */}
              <div>
                <div className="text-gray-400 mb-2">Network I/O</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500">Sent</div>
                    <div className="text-white">{formatBytes(systemMetrics.network.bytes_sent)}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Received</div>
                    <div className="text-white">{formatBytes(systemMetrics.network.bytes_recv)}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
