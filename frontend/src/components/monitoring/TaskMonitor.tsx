'use client'

import React, { useState, useEffect } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
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
  TrendingUp
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
}

interface TaskMonitorProps {
  taskId?: string
  showAllTasks?: boolean
}

export default function TaskMonitor({ taskId, showAllTasks = false }: TaskMonitorProps) {
  const [tasks, setTasks] = useState<TaskStatus[]>([])
  const [logs, setLogs] = useState<Array<{ timestamp: string; level: string; message: string }>>([])
  const [selectedTask, setSelectedTask] = useState<string | null>(taskId || null)
  const [isLoading, setIsLoading] = useState(true)

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
        progress: calculateProgress(task)
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

  // プログレス計算
  const calculateProgress = (task: any) => {
    if (task.status === 'FINISHED') return 100
    if (task.status === 'FAILED' || task.status === 'CANCELLED') return 0
    if (task.status === 'PENDING') return 0

    if (task.status === 'RUNNING') {
      if (task.items_count > 0) {
        return Math.min(95, (task.requests_count / task.items_count) * 100)
      } else {
        return 10
      }
    }

    return 0
  }

  // 初期データ読み込み
  React.useEffect(() => {
    if (mounted) {
      loadTasks()
      // 定期的にタスクデータを更新
      const interval = setInterval(loadTasks, 5000) // 5秒ごと
      return () => clearInterval(interval)
    }
  }, [mounted, showAllTasks])

  const { isConnected, connectionStatus, lastMessage, subscribeToTask, unsubscribeFromTask } = useWebSocket({
    url: mounted && clientId ? `${process.env.NEXT_PUBLIC_WS_URL}/ws/${clientId}` : '',
    onMessage: (message) => {
      handleWebSocketMessage(message)
    },
    onConnect: () => {
      console.log('WebSocket connected')
      if (taskId) {
        subscribeToTask(taskId)
      }
    },
    onDisconnect: () => {
      console.log('WebSocket disconnected')
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
    }
  })

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
    subscribeToTask(taskId)
    setLogs([]) // ログをクリア
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
        <div className="w-1/3 border-r border-gray-700">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-medium text-gray-300">Active Tasks</h3>
          </div>

          <div className="overflow-y-auto">
            {tasks.map(task => (
              <div
                key={task.id}
                onClick={() => handleTaskSelect(task.id)}
                className={`p-3 border-b border-gray-800 cursor-pointer hover:bg-gray-800 transition-colors ${
                  selectedTask === task.id ? 'bg-gray-800 border-l-4 border-l-blue-500' : ''
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
              <div className="p-8 text-center text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                <p className="text-sm">Loading tasks...</p>
              </div>
            )}

            {!isLoading && tasks.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">{showAllTasks ? 'No tasks found' : 'No active tasks'}</p>
              </div>
            )}
          </div>
        </div>

        {/* ログ表示 */}
        <div className="flex-1 flex flex-col">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-medium text-gray-300">
              {selectedTask ? `Logs - Task ${selectedTask}` : 'Select a task to view logs'}
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto p-3 font-mono text-sm">
            {logs.map((log, index) => (
              <div key={index} className="mb-1 flex">
                <span className="text-gray-500 mr-2">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={`mr-2 ${
                  log.level === 'ERROR' ? 'text-red-400' :
                  log.level === 'WARNING' ? 'text-yellow-400' :
                  log.level === 'INFO' ? 'text-blue-400' :
                  'text-gray-400'
                }`}>
                  [{log.level}]
                </span>
                <span className="text-gray-300">{log.message}</span>
              </div>
            ))}

            {logs.length === 0 && selectedTask && (
              <div className="text-center text-gray-500 mt-8">
                <p>Waiting for logs...</p>
              </div>
            )}

            {!selectedTask && (
              <div className="text-center text-gray-500 mt-8">
                <p>Select a task to view real-time logs</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
