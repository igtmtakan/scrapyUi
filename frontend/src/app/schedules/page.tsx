'use client'

import React, { useState, useEffect } from 'react'
import {
  Calendar,
  Clock,
  Play,
  Pause,
  Edit,
  Trash2,
  Plus,
  CheckCircle,
  XCircle,
  AlertCircle,
  Filter,
  Search,
  RefreshCw,
  Activity,
  TrendingUp,
  BarChart3,
  FolderEdit,
  FileEdit,
  Download,
  ExternalLink,
  Power,
  PowerOff
} from 'lucide-react'
import { Schedule, scheduleService } from '@/services/scheduleService'
import ScheduleModal from '@/components/schedules/ScheduleModal'

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // モーダル状態
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [editingSchedule, setEditingSchedule] = useState<Schedule | undefined>()

  // フィルター・検索状態
  const [searchTerm, setSearchTerm] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | null>(null)
  const [selectedProject, setSelectedProject] = useState<string>('')

  // 統計情報
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    running: 0
  })

  // タスク情報（プログレスバー用）
  const [taskProgress, setTaskProgress] = useState<{[scheduleId: string]: any}>({})
  const [autoRefresh, setAutoRefresh] = useState(true)

  // データ取得
  useEffect(() => {
    loadSchedules()
  }, [])

  // 統計情報の更新
  useEffect(() => {
    updateStats()
  }, [schedules, taskProgress])

  // 自動更新の設定
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (autoRefresh) {
      interval = setInterval(() => {
        loadSchedules()
        loadTaskProgress()
      }, 5000) // 5秒ごとに更新
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [autoRefresh])

  // 初回タスク進行状況取得
  useEffect(() => {
    if (schedules.length > 0) {
      loadTaskProgress()
    }
  }, [schedules])

  const loadSchedules = async () => {
    try {
      setLoading(true)
      setError(null)

      // キャッシュを無効化してデータを取得
      const data = await scheduleService.getSchedules(true) // forceRefresh = true

      // デバッグ用ログ出力
      console.log('🔍 スケジュールデータ受信:', data)
      data.forEach((schedule, index) => {
        console.log(`📅 スケジュール${index + 1}: ${schedule.name}`)
        console.log(`   間隔: ${schedule.interval_minutes}分`)
        console.log(`   ID: ${schedule.id}`)
        if (schedule.latest_task) {
          console.log(`   最新タスク: ${schedule.latest_task.status} - アイテム${schedule.latest_task.items_count}, リクエスト${schedule.latest_task.requests_count}`)
        } else {
          console.log(`   最新タスク: なし`)
        }
      })

      // データの整合性チェック
      const validSchedules = data.filter(schedule => schedule && schedule.id)

      if (validSchedules.length !== data.length) {
        console.warn(`Filtered out ${data.length - validSchedules.length} invalid schedules`)
      }

      setSchedules(validSchedules)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'スケジュールの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const loadTaskProgress = async () => {
    try {
      const progressData: {[scheduleId: string]: any} = {}

      // 各スケジュールの最新タスクを取得
      for (const schedule of schedules) {
        try {
          const response = await fetch(
            `/api/tasks/?project_id=${schedule.project_id}&spider_id=${schedule.spider_id}&limit=1&status=RUNNING,PENDING`,
            {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
              }
            }
          )

          if (response.ok) {
            const tasks = await response.json()

            if (tasks.length > 0) {
              const task = tasks[0]

              // 実行中または待機中のタスクがある場合
              if (task.status === 'RUNNING' || task.status === 'PENDING') {
                progressData[schedule.id] = {
                  taskId: task.id,
                  status: task.status.toLowerCase(),
                  itemsScraped: task.items_count || 0,
                  requestsCount: task.requests_count || 0,
                  errorsCount: task.error_count || 0,
                  startedAt: task.started_at,
                  elapsedTime: task.started_at ?
                    Math.floor((new Date().getTime() - new Date(task.started_at).getTime()) / 1000) : 0
                }
              }
            }
          }
        } catch (error) {
          console.error(`Failed to get task progress for schedule ${schedule.id}:`, error)
        }
      }

      setTaskProgress(progressData)
    } catch (error) {
      console.error('Failed to load task progress:', error)
    }
  }

  const updateStats = () => {
    const total = schedules.length
    const active = schedules.filter(s => s.is_active).length
    const inactive = total - active
    const running = Object.keys(taskProgress).length // 実行中のタスク数

    setStats({ total, active, inactive, running })
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Never'

    const date = new Date(dateString)
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatElapsedTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}秒`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}分${remainingSeconds}秒`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}時間${minutes}分`
    }
  }

  const handleCreateSchedule = () => {
    setModalMode('create')
    setEditingSchedule(undefined)
    setShowModal(true)
  }

  const handleEditSchedule = (schedule: Schedule) => {
    setModalMode('edit')
    setEditingSchedule(schedule)
    setShowModal(true)
  }

  const handleSaveSchedule = (schedule: Schedule) => {
    if (modalMode === 'create') {
      setSchedules(prev => [schedule, ...prev])
    } else {
      setSchedules(prev => prev.map(s => s.id === schedule.id ? schedule : s))
    }
  }

  const handleToggleSchedule = async (scheduleId: string) => {
    try {
      const updatedSchedule = await scheduleService.toggleSchedule(scheduleId)
      setSchedules(prev => prev.map(s => s.id === scheduleId ? updatedSchedule : s))
    } catch (error: any) {
      alert(error.response?.data?.detail || 'スケジュールの切り替えに失敗しました')
    }
  }

  const handleRunScheduleNow = async (scheduleId: string) => {
    try {
      const result = await scheduleService.runSchedule(scheduleId)
      alert(`スケジュールを実行しました。タスクID: ${result.task_id}`)
      // 最終実行時刻を更新
      loadSchedules()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'スケジュールの実行に失敗しました')
    }
  }

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!confirm('このスケジュールを削除しますか？')) return

    try {
      await scheduleService.deleteSchedule(scheduleId)
      setSchedules(prev => prev.filter(s => s.id !== scheduleId))
    } catch (error: any) {
      alert(error.response?.data?.detail || 'スケジュールの削除に失敗しました')
    }
  }

  // プロジェクト編集ページに移動
  const handleEditProject = (projectId: string) => {
    window.open(`/projects/${projectId}/edit`, '_blank')
  }

  // スパイダー編集ページに移動
  const handleEditSpider = (projectId: string, spiderId: string) => {
    window.open(`/projects/${projectId}/spiders/${spiderId}/edit`, '_blank')
  }

  // 結果ダウンロード
  const handleDownloadResults = async (schedule: Schedule) => {
    try {
      // 最新のタスクを取得してダウンロード
      const response = await fetch(`/api/tasks?project_id=${schedule.project_id}&spider_id=${schedule.spider_id}&limit=1`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })

      if (response.ok) {
        const tasks = await response.json()
        if (tasks.length > 0) {
          const latestTask = tasks[0]
          // タスク結果ページを新しいタブで開く
          window.open(`/projects/${schedule.project_id}/tasks/${latestTask.id}/results`, '_blank')
        } else {
          alert('このスケジュールの実行結果がありません')
        }
      } else {
        alert('タスク情報の取得に失敗しました')
      }
    } catch (error) {
      console.error('Failed to get task results:', error)
      alert('結果の取得に失敗しました')
    }
  }

  // フィルター処理
  const filteredSchedules = schedules.filter(schedule => {
    if (!searchTerm.trim()) {
      // 検索語が空の場合は検索条件をスキップ
      const matchesActive = filterActive === null || schedule.is_active === filterActive
      const matchesProject = !selectedProject || schedule.project_id === selectedProject
      return matchesActive && matchesProject
    }

    const searchLower = searchTerm.toLowerCase()
    const matchesSearch = (schedule.name || '').toLowerCase().includes(searchLower) ||
                         (schedule.description || '').toLowerCase().includes(searchLower) ||
                         (schedule.project_name || '').toLowerCase().includes(searchLower) ||
                         (schedule.spider_name || '').toLowerCase().includes(searchLower)

    const matchesActive = filterActive === null || schedule.is_active === filterActive
    const matchesProject = !selectedProject || schedule.project_id === selectedProject

    return matchesSearch && matchesActive && matchesProject
  })

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* ヘッダー */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Calendar className="w-6 h-6 text-blue-400" />
            <h1 className="text-2xl font-bold">スケジュール管理</h1>
          </div>

          <div className="flex items-center space-x-3">
            {/* 自動更新トグル */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="autoRefresh" className="text-sm text-gray-300">
                自動更新 (5秒)
              </label>
            </div>

            <button
              onClick={() => {
                loadSchedules()
                loadTaskProgress()
              }}
              className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 px-3 py-2 rounded-lg transition-colors"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>更新</span>
            </button>

            <button
              onClick={handleCreateSchedule}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>新規作成</span>
            </button>
          </div>
        </div>

        {/* 統計情報 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              <div>
                <p className="text-sm text-gray-400">総スケジュール数</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <Activity className="w-8 h-8 text-green-400" />
              <div>
                <p className="text-sm text-gray-400">アクティブ</p>
                <p className="text-2xl font-bold text-green-400">{stats.active}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <Pause className="w-8 h-8 text-gray-400" />
              <div>
                <p className="text-sm text-gray-400">非アクティブ</p>
                <p className="text-2xl font-bold text-gray-400">{stats.inactive}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-8 h-8 text-yellow-400" />
              <div>
                <p className="text-sm text-gray-400">実行中</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.running}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 検索・フィルター */}
        <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="スケジュール名、説明、プロジェクト、スパイダーで検索..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400"
            />
          </div>

          <select
            value={filterActive === null ? '' : filterActive.toString()}
            onChange={(e) => setFilterActive(e.target.value === '' ? null : e.target.value === 'true')}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
          >
            <option value="">全ての状態</option>
            <option value="true">アクティブのみ</option>
            <option value="false">非アクティブのみ</option>
          </select>
        </div>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="p-6">
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-300">{error}</span>
            <button
              onClick={loadSchedules}
              className="ml-auto px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      )}

      {/* ローディング表示 */}
      {loading && (
        <div className="p-6">
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
            <span className="ml-3 text-gray-400">読み込み中...</span>
          </div>
        </div>
      )}

      {/* スケジュール一覧 */}
      {!loading && !error && (
        <div className="p-6">
          <div className="grid gap-6">
            {filteredSchedules.map((schedule, index) => (
              <div
                key={schedule.id || `schedule-${index}`}
                className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold">{schedule.name}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        schedule.is_active
                          ? 'bg-green-900/50 text-green-300 border border-green-500'
                          : 'bg-gray-700 text-gray-300 border border-gray-600'
                      }`}>
                        {schedule.is_active ? 'アクティブ' : '非アクティブ'}
                      </span>

                      {/* 実行統計 */}
                      {(schedule.success_count || schedule.failure_count) && (
                        <div className="flex items-center space-x-2 text-xs">
                          <span className="flex items-center space-x-1 text-green-400">
                            <CheckCircle className="w-3 h-3" />
                            <span>{schedule.success_count || 0}</span>
                          </span>
                          <span className="flex items-center space-x-1 text-red-400">
                            <XCircle className="w-3 h-3" />
                            <span>{schedule.failure_count || 0}</span>
                          </span>
                        </div>
                      )}
                    </div>

                    {schedule.description && (
                      <p className="text-gray-400 mb-4">{schedule.description}</p>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">スケジュール:</span>
                        <p className="text-white font-mono">{schedule.cron_expression}</p>
                        <p className="text-blue-400 text-xs">{scheduleService.formatCronExpression(schedule.cron_expression)}</p>
                      </div>

                      <div>
                        <span className="text-gray-500">プロジェクト:</span>
                        <button
                          onClick={() => window.open(`/projects/${schedule.project_id}`, '_blank')}
                          className="text-white hover:text-blue-400 transition-colors text-left"
                          title="プロジェクト詳細を表示"
                        >
                          {schedule.project_name || 'N/A'}
                        </button>
                      </div>

                      <div>
                        <span className="text-gray-500">スパイダー:</span>
                        <button
                          onClick={() => window.open(`/projects/${schedule.project_id}/spiders/${schedule.spider_id}`, '_blank')}
                          className="text-white hover:text-blue-400 transition-colors text-left"
                          title="スパイダー詳細を表示"
                        >
                          {schedule.spider_name || 'N/A'}
                        </button>
                      </div>

                      <div>
                        <span className="text-gray-500">最終実行:</span>
                        <p className="text-white">{formatDateTime(schedule.last_run)}</p>
                      </div>
                    </div>

                    {/* 実行状況表示 */}
                    {taskProgress[schedule.id] ? (
                      <div className="mt-4 p-4 bg-gray-700 rounded-lg border border-blue-500">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <div className={`w-3 h-3 rounded-full ${
                              taskProgress[schedule.id].status === 'running'
                                ? 'bg-green-400 animate-pulse'
                                : taskProgress[schedule.id].status === 'pending'
                                ? 'bg-yellow-400 animate-bounce'
                                : 'bg-blue-400 animate-pulse'
                            }`}></div>
                            <span className={`text-sm font-medium ${
                              taskProgress[schedule.id].status === 'running'
                                ? 'text-green-300'
                                : taskProgress[schedule.id].status === 'pending'
                                ? 'text-yellow-300'
                                : 'text-blue-300'
                            }`}>
                              {taskProgress[schedule.id].status === 'running'
                                ? '🚀 実行中'
                                : taskProgress[schedule.id].status === 'pending'
                                ? '⏳ 待機中'
                                : '🔄 処理中'
                              }
                            </span>
                            <span className="text-xs text-gray-400">
                              (タスクID: {taskProgress[schedule.id].taskId.slice(0, 8)}...)
                            </span>
                          </div>
                          <button
                            onClick={() => window.open(`/projects/${schedule.project_id}/tasks/${taskProgress[schedule.id].taskId}/results`, '_blank')}
                            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            結果表示
                          </button>
                        </div>

                        <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                          <div className="text-center">
                            <p className="text-gray-400">リクエスト数</p>
                            <p className="text-lg font-bold text-blue-400">
                              {taskProgress[schedule.id].requestsCount.toLocaleString()}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-gray-400">アイテム数</p>
                            <p className="text-lg font-bold text-green-400">
                              {taskProgress[schedule.id].itemsScraped.toLocaleString()}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-gray-400">経過時間</p>
                            <p className="text-lg font-bold text-purple-400">
                              {formatElapsedTime(taskProgress[schedule.id].elapsedTime)}
                            </p>
                          </div>
                        </div>

                        {/* プログレスバー */}
                        {taskProgress[schedule.id].status === 'running' && (
                          <div className="w-full bg-gray-600 rounded-full h-3 mb-2">
                            <div className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500 flex items-center justify-center text-xs font-bold text-white"
                                 style={{
                                   width: `${Math.min(100, Math.max(5,
                                     taskProgress[schedule.id].requestsCount > 0
                                       ? (taskProgress[schedule.id].itemsScraped / taskProgress[schedule.id].requestsCount) * 100
                                       : taskProgress[schedule.id].elapsedTime > 0 ? Math.min(95, (taskProgress[schedule.id].elapsedTime / 60) * 10) : 5
                                   ))}%`
                                 }}>
                              {taskProgress[schedule.id].requestsCount > 0
                                ? `${Math.round((taskProgress[schedule.id].itemsScraped / taskProgress[schedule.id].requestsCount) * 100)}%`
                                : `${Math.min(95, Math.round((taskProgress[schedule.id].elapsedTime / 60) * 10))}%`
                              }
                            </div>
                          </div>
                        )}

                        {/* エラー表示 */}
                        {taskProgress[schedule.id].errorsCount > 0 && (
                          <div className="mt-2 text-xs text-orange-400">
                            ⚠️ エラー: {taskProgress[schedule.id].errorsCount}件
                          </div>
                        )}
                      </div>
                    ) : schedule.latest_task ? (
                      /* 最新完了タスクの表示 */
                      <div className="mt-4 p-3 bg-gray-700/50 rounded-lg border border-gray-600">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <div className={`w-3 h-3 rounded-full ${
                              schedule.latest_task.status === 'FINISHED'
                                ? 'bg-blue-400'
                                : schedule.latest_task.status === 'FAILED'
                                ? 'bg-red-400'
                                : 'bg-gray-400'
                            }`}></div>
                            <span className="text-sm font-medium text-gray-300">
                              {schedule.latest_task.status === 'FINISHED' ? '✅ 最新実行完了' :
                               schedule.latest_task.status === 'FAILED' ? '❌ 最新実行失敗' : '📋 最新実行'}
                            </span>
                            <span className="text-xs text-gray-400">
                              (タスクID: {schedule.latest_task.id.slice(0, 8)}...)
                            </span>
                          </div>
                          <button
                            onClick={() => window.open(`/projects/${schedule.project_id}/tasks/${schedule.latest_task.id}/results`, '_blank')}
                            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            結果表示
                          </button>
                        </div>

                        <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                          <div className="text-center">
                            <p className="text-gray-400">リクエスト数</p>
                            <p className="text-lg font-bold text-blue-400">
                              {(schedule.latest_task.requests_count || 0).toLocaleString()}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-gray-400">アイテム数</p>
                            <p className="text-lg font-bold text-green-400">
                              {(schedule.latest_task.items_count || 0).toLocaleString()}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-gray-400">エラー数</p>
                            <p className="text-lg font-bold text-red-400">
                              {(schedule.latest_task.error_count || 0).toLocaleString()}
                            </p>
                          </div>
                        </div>

                        {/* 完了タスクの進行状況バー */}
                        {schedule.latest_task.status === 'FINISHED' && schedule.latest_task.requests_count > 0 && (
                          <div className="w-full bg-gray-600 rounded-full h-2 mb-2">
                            <div className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-500 flex items-center justify-center text-xs font-bold text-white"
                                 style={{
                                   width: `${Math.min(100, (schedule.latest_task.items_count / schedule.latest_task.requests_count) * 100)}%`
                                 }}>
                            </div>
                          </div>
                        )}

                        {/* 実行時間表示 */}
                        {schedule.latest_task.started_at && schedule.latest_task.finished_at && (
                          <div className="text-xs text-gray-400 mt-2">
                            実行時間: {formatDateTime(schedule.latest_task.started_at)} ～ {formatDateTime(schedule.latest_task.finished_at)}
                          </div>
                        )}
                      </div>
                    ) : (
                      /* 実行履歴がない場合の待機中表示 */
                      <div className="mt-4 p-3 bg-gray-700/50 rounded-lg border border-gray-600">
                        <div className="flex items-center space-x-2">
                          <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                          <span className="text-sm font-medium text-gray-300">
                            💤 待機中
                          </span>
                          <span className="text-xs text-gray-500">
                            次回実行を待機しています
                          </span>
                        </div>
                      </div>
                    )}

                    <div className="mt-4 flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <Clock className="w-4 h-4 text-blue-400" />
                          <span className="text-gray-400">次回実行:</span>
                          <span className="text-white">{formatDateTime(schedule.next_run)}</span>
                        </div>

                        {schedule.run_count && (
                          <div className="flex items-center space-x-2">
                            <Activity className="w-4 h-4 text-purple-400" />
                            <span className="text-gray-400">実行回数:</span>
                            <span className="text-white">{schedule.run_count}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* アクション */}
                  <div className="flex flex-col space-y-2 ml-4">
                    {/* 第1行: 実行・制御ボタン */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleRunScheduleNow(schedule.id)}
                        className="p-2 text-gray-400 hover:text-green-400 transition-colors"
                        title="今すぐ実行"
                      >
                        <Play className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleToggleSchedule(schedule.id)}
                        className={`p-2 transition-colors ${
                          schedule.is_active
                            ? 'text-green-400 hover:text-red-400'
                            : 'text-gray-400 hover:text-green-400'
                        }`}
                        title={schedule.is_active ? '無効化' : '有効化'}
                      >
                        {schedule.is_active ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                      </button>

                      <button
                        onClick={() => handleEditSchedule(schedule)}
                        className="p-2 text-gray-400 hover:text-blue-400 transition-colors"
                        title="スケジュール編集"
                      >
                        <Edit className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleDeleteSchedule(schedule.id)}
                        className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                        title="削除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    {/* 第2行: プロジェクト・スパイダー・結果ボタン */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditProject(schedule.project_id)}
                        className="p-2 text-gray-400 hover:text-purple-400 transition-colors"
                        title="プロジェクト編集"
                      >
                        <FolderEdit className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleEditSpider(schedule.project_id, schedule.spider_id)}
                        className="p-2 text-gray-400 hover:text-orange-400 transition-colors"
                        title="スパイダー編集"
                      >
                        <FileEdit className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleDownloadResults(schedule)}
                        className="p-2 text-gray-400 hover:text-cyan-400 transition-colors"
                        title="結果ダウンロード"
                      >
                        <Download className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => window.open(`/projects/${schedule.project_id}/tasks`, '_blank')}
                        className="p-2 text-gray-400 hover:text-indigo-400 transition-colors"
                        title="タスク一覧"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* 空の状態表示 */}
            {filteredSchedules.length === 0 && schedules.length === 0 && (
              <div className="text-center py-12">
                <Calendar className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">スケジュールがありません</h3>
                <p className="text-gray-500 mb-4">最初のスケジュールを作成して、スパイダーの自動実行を開始しましょう</p>
                <button
                  onClick={handleCreateSchedule}
                  className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition-colors"
                >
                  スケジュール作成
                </button>
              </div>
            )}

            {/* フィルター結果が空の場合 */}
            {filteredSchedules.length === 0 && schedules.length > 0 && (
              <div className="text-center py-12">
                <Search className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">検索結果がありません</h3>
                <p className="text-gray-500 mb-4">検索条件を変更してください</p>
                <button
                  onClick={() => {
                    setSearchTerm('')
                    setFilterActive(null)
                    setSelectedProject('')
                  }}
                  className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg transition-colors"
                >
                  フィルターをクリア
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* スケジュール作成・編集モーダル */}
      <ScheduleModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSave={handleSaveSchedule}
        schedule={editingSchedule}
        mode={modalMode}
      />
    </div>
  )
}
