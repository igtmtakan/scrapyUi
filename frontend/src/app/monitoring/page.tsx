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
  Database,
  Flower2,
  ExternalLink,
  Monitor
} from 'lucide-react'

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState<'tasks' | 'analytics' | 'system' | 'flower'>('tasks')



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

          {/* Flower WebUI直接リンク */}
          <a
            href="http://localhost:5556/flower"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-3 py-1.5 bg-pink-600 hover:bg-pink-700 text-white text-sm rounded-lg transition-colors"
            title="Flower WebUIを新しいタブで開く"
          >
            <Flower2 className="w-4 h-4" />
            <span>Flower WebUI</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* タブナビゲーション */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="flex space-x-8 px-6">
          {[
            { id: 'tasks', label: 'Task Monitor', icon: Activity },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'system', label: 'System Status', icon: Database },
            { id: 'flower', label: 'Flower Dashboard', icon: Flower2 }
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

        {activeTab === 'flower' && (
          <div className="h-full overflow-y-auto">
            <div className="p-6">
              <div className="max-w-4xl mx-auto">
                {/* Flower Dashboard Header */}
                <div className="mb-8">
                  <div className="flex items-center space-x-3 mb-4">
                    <Flower2 className="w-8 h-8 text-pink-400" />
                    <h2 className="text-2xl font-bold text-white">Flower Dashboard</h2>
                  </div>
                  <p className="text-gray-400">
                    Celeryタスクとワーカーのリアルタイム監視・管理ダッシュボード
                  </p>
                </div>

                {/* Quick Links */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  {/* ScrapyUI統合ダッシュボード */}
                  <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                        <BarChart3 className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">統合ダッシュボード</h3>
                        <p className="text-sm text-gray-400">ScrapyUI内のFlower統合表示</p>
                      </div>
                    </div>
                    <p className="text-gray-300 text-sm mb-4">
                      ScrapyUIと統一されたデザインで、Celeryタスクの状態を確認できます。
                    </p>
                    <a
                      href="/flower"
                      className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                    >
                      <span>統合ダッシュボードを開く</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>

                  {/* Flower WebUI */}
                  <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-12 h-12 bg-pink-600 rounded-lg flex items-center justify-center">
                        <Flower2 className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Flower WebUI</h3>
                        <p className="text-sm text-gray-400">完全なFlower Web インターフェース</p>
                      </div>
                    </div>
                    <p className="text-gray-300 text-sm mb-4">
                      Flowerの全機能にアクセスできる公式WebUIです。詳細な統計とリアルタイム監視が可能です。
                    </p>
                    <a
                      href="http://localhost:5556/flower"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 px-4 py-2 bg-pink-600 hover:bg-pink-700 text-white text-sm rounded-lg transition-colors"
                    >
                      <span>Flower WebUIを開く</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {/* 機能説明 */}
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Flowerで確認できる情報</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-md font-medium text-blue-400 mb-2">タスク監視</h4>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>• 実行中・完了・失敗したタスクの一覧</li>
                        <li>• タスクの詳細情報（引数、結果、実行時間）</li>
                        <li>• タスクの実行履歴とトレンド</li>
                        <li>• リアルタイムタスク状態更新</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-md font-medium text-green-400 mb-2">ワーカー管理</h4>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>• アクティブ・オフラインワーカーの状態</li>
                        <li>• ワーカーのCPU・メモリ使用量</li>
                        <li>• ワーカーの起動・停止制御</li>
                        <li>• ワーカー設定とキュー情報</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-md font-medium text-purple-400 mb-2">統計・分析</h4>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>• タスク実行統計とグラフ</li>
                        <li>• パフォーマンス監視</li>
                        <li>• エラー率と成功率の分析</li>
                        <li>• 時系列データの可視化</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-md font-medium text-orange-400 mb-2">システム情報</h4>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>• Redis/RabbitMQブローカーの状態</li>
                        <li>• キューの状況とメッセージ数</li>
                        <li>• システムリソース使用状況</li>
                        <li>• 接続状態とヘルスチェック</li>
                      </ul>
                    </div>
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
