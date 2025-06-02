'use client'

import React from 'react'
import {
  Activity,
  TrendingUp,
  BarChart3,
  Clock,
  CheckCircle,
  AlertCircle,
  Zap,
  Target,
  Timer,
  Download
} from 'lucide-react'

interface RichProgressData {
  taskId: string
  status: 'running' | 'pending' | 'completed' | 'failed'
  itemsScraped: number
  requestsCount: number
  errorCount?: number
  startedAt?: string
  finishedAt?: string
  elapsedTime: number
  progressPercentage?: number
  currentUrl?: string
  itemsPerSecond?: number
  requestsPerSecond?: number
  estimatedTimeRemaining?: number
  totalPages?: number
  currentPage?: number
}

interface RichProgressDisplayProps {
  scheduleId: string
  progressData?: RichProgressData
  className?: string
}

const RichProgressDisplay: React.FC<RichProgressDisplayProps> = ({
  scheduleId,
  progressData,
  className = ''
}) => {
  // 表示用データ（propsデータのみ使用）
  const displayData = progressData

  if (!displayData) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <div className="flex items-center space-x-2 text-gray-400">
          <Activity className="w-4 h-4" />
          <span className="text-sm">進捗データなし</span>
        </div>
      </div>
    )
  }

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-400 bg-green-900/30 border-green-500'
      case 'pending': return 'text-yellow-400 bg-yellow-900/30 border-yellow-500'
      case 'completed': return 'text-blue-400 bg-blue-900/30 border-blue-500'
      case 'failed': return 'text-red-400 bg-red-900/30 border-red-500'
      default: return 'text-gray-400 bg-gray-900/30 border-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Activity className="w-4 h-4 animate-pulse" />
      case 'pending': return <Clock className="w-4 h-4" />
      case 'completed': return <CheckCircle className="w-4 h-4" />
      case 'failed': return <AlertCircle className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running': return '実行中'
      case 'pending': return '待機中'
      case 'completed': return '完了'
      case 'failed': return '失敗'
      default: return '不明'
    }
  }

  return (
    <div className={`bg-gray-800 rounded-lg border border-gray-700 ${className}`}>
      {/* ヘッダー */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusColor(displayData.status)}`}>
              {getStatusIcon(displayData.status)}
              <span className="text-sm font-medium">{getStatusText(displayData.status)}</span>
            </div>
            {/* 静的表示 */}
            <div className="flex items-center space-x-1 text-gray-500">
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              <span className="text-xs">静的表示</span>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            タスクID: {displayData.taskId.slice(0, 8)}...
          </div>
        </div>
      </div>

      {/* 進捗統計 */}
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {/* スクレイピング済みアイテム */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <Download className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-gray-400">アイテム</span>
            </div>
            <div className="text-lg font-bold text-blue-400">{displayData.itemsScraped.toLocaleString()}</div>
            {displayData.itemsPerSecond && (
              <div className="text-xs text-gray-500">{displayData.itemsPerSecond.toFixed(1)}/秒</div>
            )}
          </div>

          {/* リクエスト数 */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-xs text-gray-400">リクエスト</span>
            </div>
            <div className="text-lg font-bold text-green-400">{displayData.requestsCount.toLocaleString()}</div>
            {displayData.requestsPerSecond && (
              <div className="text-xs text-gray-500">{displayData.requestsPerSecond.toFixed(1)}/秒</div>
            )}
          </div>

          {/* 経過時間 */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <Timer className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-gray-400">経過時間</span>
            </div>
            <div className="text-lg font-bold text-yellow-400">{formatTime(displayData.elapsedTime)}</div>
            {displayData.estimatedTimeRemaining && (
              <div className="text-xs text-gray-500">残り {formatTime(displayData.estimatedTimeRemaining)}</div>
            )}
          </div>

          {/* エラー数 */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-xs text-gray-400">エラー</span>
            </div>
            <div className="text-lg font-bold text-red-400">{displayData.errorCount || 0}</div>
            <div className="text-xs text-gray-500">
              {displayData.requestsCount > 0 ? 
                `${((displayData.errorCount || 0) / displayData.requestsCount * 100).toFixed(1)}%` : 
                '0%'
              }
            </div>
          </div>
        </div>

        {/* 進捗バー */}
        {displayData.progressPercentage !== undefined && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">進捗</span>
              <span className="text-sm font-medium text-gray-300">{displayData.progressPercentage.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(displayData.progressPercentage, 100)}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* ページ進捗 */}
        {displayData.totalPages && displayData.currentPage && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">ページ進捗</span>
              <span className="text-sm font-medium text-gray-300">
                {displayData.currentPage} / {displayData.totalPages}
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(displayData.currentPage / displayData.totalPages) * 100}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* 現在のURL */}
        {displayData.currentUrl && (
          <div className="mt-4 p-3 bg-gray-900/50 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <Target className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-400">現在のURL</span>
            </div>
            <div className="text-sm text-purple-400 truncate" title={displayData.currentUrl}>
              {displayData.currentUrl}
            </div>
          </div>
        )}

        {/* 完了時刻 */}
        {displayData.status === 'completed' && displayData.finishedAt && (
          <div className="mt-4 p-3 bg-green-900/20 rounded-lg border border-green-500/30">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-400">
                スクレイピング完了: {new Date(displayData.finishedAt).toLocaleString('ja-JP')}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default RichProgressDisplay
