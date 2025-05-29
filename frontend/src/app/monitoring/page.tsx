'use client'

import React, { useState } from 'react'
import TaskMonitor from '@/components/monitoring/TaskMonitor'
import Analytics from '@/components/monitoring/Analytics'
import SystemStatus from '@/components/monitoring/SystemStatus'
// import { TaskTrendChart, SpiderSuccessRateChart, TaskStatusChart } from '@/components/charts/TaskPerformanceChart'
// import { ResultsTimelineChart, DailyVolumeChart, TopDomainsChart } from '@/components/charts/ResultsChart'
import {
  Activity,
  BarChart3,
  Database
} from 'lucide-react'

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState<'tasks' | 'analytics' | 'system'>('tasks')



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
          <div className="h-full">
            <TaskMonitor showAllTasks={true} />
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="h-full overflow-y-auto">
            <Analytics />
          </div>
        )}

        {activeTab === 'system' && (
          <div className="h-full overflow-y-auto">
            <SystemStatus />
          </div>
        )}
      </div>
    </div>
  )
}
