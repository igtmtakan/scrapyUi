'use client'

import React, { useState, useEffect } from 'react'
// import { useWebSocket } from '@/hooks/useWebSocket' // WebSocket機能を無効化
import { apiClient } from '@/lib/api'
import {
  Play,
  Square,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Activity,
  Database,
  Globe,
  TrendingUp,
  ExternalLink
} from 'lucide-react'

interface TaskStatus {
  id: string
  name: string
  status: 'PENDING' | 'RUNNING' | 'FINISHED' | 'FAILED' | 'CANCELLED'
  startedAt?: string
  finishedAt?: string
  itemsCount: number
  requestsCount: number
  errorCount: number
  progress?: number
  project_id?: string
  spider_id?: string
  error_message?: string
}

interface TaskMonitorProps {
  taskId?: string
  showAllTasks?: boolean
}

export default function TaskMonitor({ taskId, showAllTasks = false }: TaskMonitorProps) {
  const [tasks, setTasks] = useState<TaskStatus[]>([])
  const [logs, setLogs] = useState<Array<{ timestamp: string; level: string; message: string }>>([])
  const [selectedTask, setSelectedTask] = useState<string | null>(taskId || null)
  const [selectedTaskDetails, setSelectedTaskDetails] = useState<TaskStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingLogs, setIsLoadingLogs] = useState(false)

  const [clientId, setClientId] = React.useState('')
  const [mounted, setMounted] = React.useState(false)

  // クライアントサイドでのみ初期化
  React.useEffect(() => {
    setMounted(true)
    setClientId(`monitor_${Date.now()}`)
  }, [])

  // 実際のタスクデータを取得
  const loadTasks = async () => {
    try {
      setIsLoading(true)

      // 直接fetchを使用（認証なし）
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tasks/`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const tasksData = await response.json()

      // 実行中のタスクのみフィルタリング（showAllTasksがfalseの場合）
      const filteredTasks = showAllTasks
        ? tasksData
        : tasksData.filter((task: any) => task.status === 'RUNNING')

      // TaskStatusフォーマットに変換
      const formattedTasks = filteredTasks.map((task: any) => ({
        id: task.id,
        name: `${task.project?.name || 'Unknown'} / ${task.spider?.name || 'Unknown'}`,
        status: task.status,
        startedAt: task.started_at,
        finishedAt: task.finished_at,
        itemsCount: task.items_count || 0,
        requestsCount: task.requests_count || 0,
        errorCount: task.error_count || 0,
        progress: calculateProgress(task),
        project_id: task.project_id,
        spider_id: task.spider_id,
        error_message: task.error_message
      }))

      setTasks(formattedTasks)
    } catch (error) {
      console.error('Failed to load tasks:', error)
      // エラーの場合は空の配列を設定
      setTasks([])
    } finally {
      setIsLoading(false)
    }
  }

  // プログレス計算（新方式: pendingアイテム数ベース）
  const calculateProgress = (task: any) => {
    if (task.status === 'FINISHED') return 100
    if (task.status === 'FAILED' || task.status === 'CANCELLED') return 0
    if (task.status === 'PENDING') return 0

    if (task.status === 'RUNNING') {
      if (task.items_count > 0) {
        // pendingアイテム数を推定
        const pendingItems = Math.max(0, Math.min(
          60 - task.items_count, // 最大60アイテムと仮定
          Math.max(task.requests_count - task.items_count, 10) // リクエスト差分または最低10
        ))
        const totalEstimated = task.items_count + pendingItems

        if (totalEstimated > 0) {
          return Math.min(95, (task.items_count / totalEstimated) * 100)
        }
      }
      return 10
    }

    return 0
  }

  // タスクのログを取得
  const loadTaskLogs = async (taskId: string) => {
    try {
      setIsLoadingLogs(true)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tasks/${taskId}/logs?limit=100`)

      if (response.ok) {
        const logsData = await response.json()
        const formattedLogs = logsData.map((log: any) => ({
          timestamp: log.timestamp || new Date().toISOString(),
          level: log.level || 'INFO',
          message: log.message || ''
        }))
        setLogs(formattedLogs)
      } else {
        console.error('Failed to load logs:', response.status)
        setLogs([])
      }
    } catch (error) {
      console.error('Error loading logs:', error)
      setLogs([])
    } finally {
      setIsLoadingLogs(false)
    }
  }

  // 初期データ読み込み
  React.useEffect(() => {
    if (mounted) {
      loadTasks()
      // 定期的にタスクデータを更新（WebSocket無効化のため頻度を上げる）
      const interval = setInterval(loadTasks, 3000) // 3秒ごと
      return () => clearInterval(interval)
    }
  }, [mounted, showAllTasks])

  // WebSocket機能を無効化（HTTPポーリングのみ使用）
  const isConnected = false
  const connectionStatus = 'disconnected'
  const lastMessage = null
  const subscribeToTask = () => false
  const unsubscribeFromTask = () => false

  // const { isConnected, connectionStatus, lastMessage, subscribeToTask, unsubscribeFromTask } = useWebSocket({
  //   url: mounted && clientId ? `${process.env.NEXT_PUBLIC_WS_URL}/ws/${clientId}` : '',
  //   onMessage: (message) => {
  //     console.log('WebSocket message received:', message)
  //     handleWebSocketMessage(message)
  //   },
  //   onConnect: () => {
  //     console.log('WebSocket connected successfully')
  //     if (taskId) {
  //       console.log('Subscribing to task:', taskId)
  //       subscribeToTask(taskId)
  //     }
  //   },
  //   onDisconnect: () => {
  //     console.log('WebSocket disconnected')
  //   },
  //   onError: (error) => {
  //     console.error('WebSocket error in TaskMonitor:', {
  //       error,
  //       url: `${process.env.NEXT_PUBLIC_WS_URL}/ws/${clientId}`,
  //       clientId,
  //       mounted
  //     })
  //   }
  // })

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'task_update':
        updateTaskStatus(message.task_id, message.data)
        break
      case 'log':
        addLogMessage(message.task_id, message.data)
        break
      case 'system_notification':
        // システム通知の処理
        break
    }
  }

  const updateTaskStatus = (taskId: string, data: any) => {
    setTasks(prevTasks => {
      const existingIndex = prevTasks.findIndex(task => task.id === taskId)

      if (existingIndex >= 0) {
        const updatedTasks = [...prevTasks]
        updatedTasks[existingIndex] = { ...updatedTasks[existingIndex], ...data }
        return updatedTasks
      } else {
        return [...prevTasks, { id: taskId, ...data }]
      }
    })
  }

  const addLogMessage = (taskId: string, logData: any) => {
    if (!selectedTask || selectedTask === taskId) {
      setLogs(prevLogs => [
        ...prevLogs.slice(-99), // 最新100件を保持
        {
          timestamp: logData.timestamp || new Date().toISOString(),
          level: logData.level || 'INFO',
          message: logData.message || ''
        }
      ])
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'RUNNING':
        return <Play className="w-4 h-4 text-blue-500 animate-pulse" />
      case 'FINISHED':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'CANCELLED':
        return <Square className="w-4 h-4 text-gray-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'RUNNING':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'FINISHED':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'FAILED':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return '-'

    const start = new Date(startTime)
    const end = endTime ? new Date(endTime) : new Date()
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000)

    const hours = Math.floor(duration / 3600)
    const minutes = Math.floor((duration % 3600) / 60)
    const seconds = duration % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  }

  const handleTaskSelect = (taskId: string) => {
    if (selectedTask && selectedTask !== taskId) {
      unsubscribeFromTask(selectedTask)
    }

    setSelectedTask(taskId)
    const task = tasks.find(t => t.id === taskId)
    setSelectedTaskDetails(task || null)

    subscribeToTask(taskId)
    setLogs([]) // ログをクリア

    // エラータスクまたは完了したタスクのログを読み込み
    if (task && (task.status === 'FAILED' || task.status === 'FINISHED' || task.errorCount > 0)) {
      loadTaskLogs(taskId)
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* ヘッダー */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold">Task Monitor</h2>
          </div>

          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm text-gray-400">
              {connectionStatus}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* タスクリスト */}
        <div className="w-1/3 border-r border-gray-700 flex flex-col">
          <div className="p-3 border-b border-gray-700 flex-shrink-0">
            <h3 className="text-sm font-medium text-gray-300">Active Tasks</h3>
          </div>

          <div className="flex-1 overflow-y-auto max-h-full scrollbar-thin scrollbar-webkit">
            {tasks.map(task => (
              <div
                key={task.id}
                onClick={() => handleTaskSelect(task.id)}
                className={`p-3 border-b border-gray-800 cursor-pointer hover:bg-gray-800 transition-colors ${
                  selectedTask === task.id
                    ? 'bg-gray-800 border-l-4 border-l-blue-500'
                    : task.status === 'FAILED'
                    ? 'border-l-2 border-l-red-500 bg-red-900/10'
                    : ''
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(task.status)}
                    <span className="text-sm font-medium truncate">{task.name}</span>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded border ${getStatusColor(task.status)}`}>
                    {task.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
                  <div className="flex items-center space-x-1">
                    <Database className="w-3 h-3" />
                    <span>{task.itemsCount}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Globe className="w-3 h-3" />
                    <span>{task.requestsCount}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <XCircle className="w-3 h-3" />
                    <span>{task.errorCount}</span>
                  </div>
                </div>

                {task.progress !== undefined && (
                  <div className="mt-2">
                    <div className="w-full bg-gray-700 rounded-full h-1">
                      <div
                        className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                <div className="mt-1 text-xs text-gray-500">
                  {formatDuration(task.startedAt, task.finishedAt)}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex-1 flex items-center justify-center p-8 text-gray-500">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                  <p className="text-sm">Loading tasks...</p>
                </div>
              </div>
            )}

            {!isLoading && tasks.length === 0 && (
              <div className="flex-1 flex items-center justify-center p-8 text-gray-500">
                <div className="text-center">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">{showAllTasks ? 'No tasks found' : 'No active tasks'}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ログ表示 */}
        <div className="flex-1 flex flex-col">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-medium text-gray-300">
              {selectedTask ? `Logs - Task ${selectedTask.slice(0, 8)}...` : 'Select a task to view logs'}
            </h3>
          </div>

          {/* エラー詳細セクション */}
          {selectedTaskDetails && selectedTaskDetails.status === 'FAILED' && (
            <div className="p-3 bg-red-900/20 border-b border-red-500/30">
              <div className="flex items-center space-x-2 mb-2">
                <XCircle className="w-4 h-4 text-red-400" />
                <h4 className="text-sm font-medium text-red-400">エラー詳細</h4>
              </div>

              <div className="space-y-2 text-sm">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <span className="text-gray-400">エラー数:</span>
                    <span className="ml-2 text-red-400 font-semibold">{selectedTaskDetails.errorCount}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">取得アイテム:</span>
                    <span className="ml-2 text-white">{selectedTaskDetails.itemsCount}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">リクエスト数:</span>
                    <span className="ml-2 text-white">{selectedTaskDetails.requestsCount}</span>
                  </div>
                </div>

                {selectedTaskDetails.error_message && (
                  <div className="mt-2">
                    <span className="text-gray-400">エラーメッセージ:</span>
                    <div className="mt-1 p-2 bg-gray-800 rounded text-red-300 text-xs font-mono">
                      {selectedTaskDetails.error_message}
                    </div>
                  </div>
                )}

                <div className="flex items-center space-x-4 mt-2">
                  <button
                    onClick={() => selectedTaskDetails.project_id && window.open(`/projects/${selectedTaskDetails.project_id}/tasks/${selectedTaskDetails.id}`, '_blank')}
                    className="text-blue-400 hover:text-blue-300 text-xs flex items-center space-x-1"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>詳細ページを開く</span>
                  </button>

                  {isLoadingLogs && (
                    <div className="flex items-center space-x-1 text-xs text-gray-400">
                      <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-400"></div>
                      <span>ログ読み込み中...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-3 font-mono text-sm scrollbar-thin scrollbar-webkit">
            {logs.map((log, index) => (
              <div key={index} className={`mb-1 flex ${
                log.level === 'ERROR' ? 'bg-red-900/20 p-2 rounded' : ''
              }`}>
                <span className="text-gray-500 mr-2 flex-shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={`mr-2 flex-shrink-0 font-semibold ${
                  log.level === 'ERROR' ? 'text-red-400' :
                  log.level === 'WARNING' ? 'text-yellow-400' :
                  log.level === 'INFO' ? 'text-blue-400' :
                  'text-gray-400'
                }`}>
                  [{log.level}]
                </span>
                <span className={`${
                  log.level === 'ERROR' ? 'text-red-300' : 'text-gray-300'
                } break-all`}>
                  {log.message}
                </span>
              </div>
            ))}

            {isLoadingLogs && (
              <div className="text-center text-gray-500 mt-8">
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                  <p>ログを読み込み中...</p>
                </div>
              </div>
            )}

            {logs.length === 0 && selectedTask && !isLoadingLogs && (
              <div className="text-center text-gray-500 mt-8">
                <p>
                  {selectedTaskDetails?.status === 'FAILED'
                    ? 'エラーログが見つかりません'
                    : 'ログを待機中...'}
                </p>
              </div>
            )}

            {!selectedTask && (
              <div className="text-center text-gray-500 mt-8">
                <div className="space-y-2">
                  <Activity className="w-8 h-8 mx-auto opacity-50" />
                  <p>タスクを選択してログとエラー詳細を表示</p>
                  <p className="text-xs">エラータスクを選択すると詳細なエラー情報が表示されます</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
