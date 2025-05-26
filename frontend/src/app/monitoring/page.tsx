'use client'

import React, { useState } from 'react'
import TaskMonitor from '@/components/monitoring/TaskMonitor'
// import { TaskTrendChart, SpiderSuccessRateChart, TaskStatusChart } from '@/components/charts/TaskPerformanceChart'
// import { ResultsTimelineChart, DailyVolumeChart, TopDomainsChart } from '@/components/charts/ResultsChart'
import {
  Activity,
  BarChart3,
  Database,
  Globe,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react'

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState<'tasks' | 'analytics' | 'system'>('tasks')

  // モックデータ（実際の実装では API から取得）
  const systemStats = {
    totalTasks: 156,
    activeTasks: 8,
    completedTasks: 142,
    failedTasks: 6,
    totalResults: 15420,
    avgResponseTime: 1.2,
    successRate: 96.2,
    systemLoad: 45
  }

  const recentActivity = [
    { id: 1, type: 'task_completed', message: 'E-commerce spider completed successfully', time: '2 minutes ago', status: 'success' },
    { id: 2, type: 'task_started', message: 'News spider started crawling', time: '5 minutes ago', status: 'info' },
    { id: 3, type: 'error', message: 'Connection timeout for product spider', time: '8 minutes ago', status: 'error' },
    { id: 4, type: 'task_completed', message: 'API spider finished with 250 items', time: '12 minutes ago', status: 'success' },
  ]

  const getActivityIcon = (type: string, status: string) => {
    if (status === 'success') return <CheckCircle className="w-4 h-4 text-green-500" />
    if (status === 'error') return <XCircle className="w-4 h-4 text-red-500" />
    if (status === 'warning') return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    return <Activity className="w-4 h-4 text-blue-500" />
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* ヘッダー */}
      <div className="h-16 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <Activity className="w-6 h-6 text-blue-400" />
          <h1 className="text-xl font-semibold text-white">Monitoring Dashboard</h1>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-300">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>System Online</span>
          </div>
        </div>
      </div>

      {/* タブナビゲーション */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="flex space-x-8 px-6">
          {[
            { id: 'tasks', label: 'Task Monitor', icon: Activity },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'system', label: 'System Status', icon: Database }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-4 px-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'tasks' && (
          <TaskMonitor showAllTasks={true} />
        )}

        {activeTab === 'analytics' && (
          <div className="p-6 overflow-y-auto">
            {/* 統計カード */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Total Tasks</p>
                    <p className="text-2xl font-bold text-white">{systemStats.totalTasks}</p>
                  </div>
                  <Activity className="w-8 h-8 text-blue-400" />
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Active Tasks</p>
                    <p className="text-2xl font-bold text-white">{systemStats.activeTasks}</p>
                  </div>
                  <Clock className="w-8 h-8 text-yellow-400" />
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Total Results</p>
                    <p className="text-2xl font-bold text-white">{systemStats.totalResults.toLocaleString()}</p>
                  </div>
                  <Database className="w-8 h-8 text-green-400" />
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Success Rate</p>
                    <p className="text-2xl font-bold text-white">{systemStats.successRate}%</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-purple-400" />
                </div>
              </div>
            </div>

            {/* チャートエリア */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-center py-8">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-400">タスクトレンドチャート</p>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-center py-8">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-400">タスクステータスチャート</p>
                </div>
              </div>
            </div>

            {/* 追加チャート */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-center py-8">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-400">スパイダー成功率</p>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-center py-8">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-400">日次ボリューム</p>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-center py-8">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-400">トップドメイン</p>
                </div>
              </div>
            </div>

            {/* リアルタイムチャート */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
              <div className="text-center py-8">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-400">結果タイムラインチャート</p>
              </div>
            </div>

            {/* 最近のアクティビティ */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
              <div className="space-y-3">
                {recentActivity.map(activity => (
                  <div key={activity.id} className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg">
                    {getActivityIcon(activity.type, activity.status)}
                    <div className="flex-1">
                      <p className="text-sm text-white">{activity.message}</p>
                      <p className="text-xs text-gray-400">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'system' && (
          <div className="p-6 overflow-y-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* システム情報 */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">System Information</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-400">CPU Usage</span>
                    <span className="text-white">{systemStats.systemLoad}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${systemStats.systemLoad}%` }}
                    ></div>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-400">Memory Usage</span>
                    <span className="text-white">2.1 GB / 8 GB</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '26%' }}></div>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-400">Disk Usage</span>
                    <span className="text-white">45.2 GB / 100 GB</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '45%' }}></div>
                  </div>
                </div>
              </div>

              {/* 接続状況 */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Connection Status</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-white">Database</span>
                    </div>
                    <span className="text-green-400">Connected</span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-white">WebSocket</span>
                    </div>
                    <span className="text-green-400">Connected</span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-white">Scrapy Engine</span>
                    </div>
                    <span className="text-green-400">Running</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
