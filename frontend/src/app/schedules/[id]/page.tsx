'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Calendar, Clock, Play, ArrowLeft, RefreshCw, ExternalLink, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { scheduleService, Schedule, ScheduleTask } from '../../../services/scheduleService'
import { useAuthStore } from '../../../stores/authStore'

interface ScheduleDetailPageProps {}

const ScheduleDetailPage: React.FC<ScheduleDetailPageProps> = () => {
  const params = useParams()
  const router = useRouter()
  const { isAuthenticated, user, isLoading: authLoading, isInitialized } = useAuthStore()
  const scheduleId = params.id as string

  // デバッグ情報
  console.log('🔍 ScheduleDetailPage - Auth State:', {
    isAuthenticated,
    isInitialized,
    authLoading,
    user: user?.email,
    scheduleId
  })

  const [schedule, setSchedule] = useState<Schedule | null>(null)
  const [tasks, setTasks] = useState<ScheduleTask[]>([])
  const [loading, setLoading] = useState(true)
  const [tasksLoading, setTasksLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [statusFilter, setStatusFilter] = useState<string>('')

  const tasksPerPage = 20

  // スケジュール詳細を取得
  const loadSchedule = async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('📡 Loading schedule:', scheduleId)

      if (!scheduleId) {
        throw new Error('スケジュールIDが指定されていません')
      }

      const scheduleData = await scheduleService.getSchedule(scheduleId)
      console.log('✅ Schedule loaded:', scheduleData)
      setSchedule(scheduleData)
    } catch (error: any) {
      console.error('❌ Failed to load schedule:', {
        scheduleId,
        error: error instanceof Error ? error.message : String(error),
        errorType: error?.constructor?.name,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      })

      let errorMessage = 'スケジュールの取得に失敗しました'

      if (error.response?.status === 404) {
        errorMessage = 'スケジュールが見つかりません'
      } else if (error.response?.status === 403) {
        errorMessage = 'このスケジュールにアクセスする権限がありません'
      } else if (error.response?.status === 401) {
        errorMessage = '認証が必要です。ログインしてください。'
      } else if (error.message?.includes('ネットワークエラー')) {
        errorMessage = 'サーバーに接続できません。サーバーが起動しているか確認してください。'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }

      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 実行履歴を取得
  const loadTasks = async (page: number = 0, status: string = '') => {
    try {
      setTasksLoading(true)
      const offset = page * tasksPerPage
      console.log('📡 Loading tasks:', { scheduleId, page, offset, status })

      const response = await scheduleService.getScheduleTasks(
        scheduleId,
        tasksPerPage,
        offset,
        status || undefined
      )

      console.log('✅ Tasks loaded:', {
        tasksCount: response.tasks.length,
        totalCount: response.total_count,
        page: page
      })

      setTasks(response.tasks)
      setTotalCount(response.total_count)
      setCurrentPage(page)
    } catch (error: any) {
      console.error('❌ Failed to load tasks:', error)
      console.error('❌ Task loading error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        url: error.config?.url
      })
      setError(error.response?.data?.detail || error.message || '実行履歴の取得に失敗しました')
    } finally {
      setTasksLoading(false)
    }
  }

  // 初期データ読み込み
  useEffect(() => {
    if (isInitialized && isAuthenticated && scheduleId) {
      loadSchedule()
      loadTasks()
    }
  }, [isInitialized, isAuthenticated, scheduleId])

  // 自動更新機能（5秒間隔）
  useEffect(() => {
    if (!scheduleId || !isAuthenticated || !user) return

    const interval = setInterval(() => {
      loadSchedule() // スケジュール情報を更新
      loadTasks()    // タスク履歴を更新
    }, 5000) // 5秒間隔で更新

    return () => clearInterval(interval)
  }, [scheduleId, isAuthenticated, user])

  // ステータスフィルター変更
  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(status)
    loadTasks(0, status)
  }

  // ページ変更
  const handlePageChange = (page: number) => {
    loadTasks(page, statusFilter)
  }

  // 日時フォーマット
  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('ja-JP')
  }

  // 実行時間計算
  const calculateDuration = (startedAt?: string, finishedAt?: string) => {
    if (!startedAt || !finishedAt) return 'N/A'
    const start = new Date(startedAt)
    const end = new Date(finishedAt)
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000)
    
    if (duration < 60) return `${duration}秒`
    if (duration < 3600) return `${Math.floor(duration / 60)}分${duration % 60}秒`
    return `${Math.floor(duration / 3600)}時間${Math.floor((duration % 3600) / 60)}分`
  }

  // ステータスアイコン
  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'FINISHED':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-400" />
      case 'RUNNING':
        return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
      case 'PENDING':
        return <Clock className="w-4 h-4 text-yellow-400" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  // ステータス色
  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'FINISHED':
        return 'text-green-400'
      case 'FAILED':
        return 'text-red-400'
      case 'RUNNING':
        return 'text-blue-400'
      case 'PENDING':
        return 'text-yellow-400'
      default:
        return 'text-gray-400'
    }
  }

  // 認証の初期化中
  if (!isInitialized || authLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  // 認証が必要
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl mb-4">認証が必要です</p>
          <button
            onClick={() => router.push('/login')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            ログインページへ
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
          >
            戻る
          </button>
        </div>
      </div>
    )
  }

  if (!schedule) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <p>スケジュールが見つかりません</p>
      </div>
    )
  }

  const totalPages = Math.ceil(totalCount / tasksPerPage)

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.back()}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold">{schedule.name}</h1>
              <p className="text-gray-400">スケジュール実行履歴</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 text-sm rounded-full ${
              schedule.is_active
                ? 'bg-green-900/50 text-green-300 border border-green-500'
                : 'bg-gray-700 text-gray-300 border border-gray-600'
            }`}>
              {schedule.is_active ? 'アクティブ' : '非アクティブ'}
            </span>
          </div>
        </div>

        {/* スケジュール情報 */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">スケジュール情報</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-gray-400 text-sm">プロジェクト</p>
              <p className="text-white font-medium">{schedule.project_name}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">スパイダー</p>
              <p className="text-white font-medium">{schedule.spider_name}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">実行間隔</p>
              <p className="text-white font-medium font-mono">{schedule.cron_expression}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">次回実行</p>
              <p className="text-white font-medium">
                {schedule.next_run ? formatDateTime(schedule.next_run) : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* フィルターとリフレッシュ */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <select
              value={statusFilter}
              onChange={(e) => handleStatusFilterChange(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="">全てのステータス</option>
              <option value="FINISHED">完了</option>
              <option value="RUNNING">実行中</option>
              <option value="PENDING">待機中</option>
              <option value="FAILED">失敗</option>
            </select>
            <p className="text-gray-400 text-sm">
              {totalCount}件中 {currentPage * tasksPerPage + 1}-{Math.min((currentPage + 1) * tasksPerPage, totalCount)}件を表示
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={async () => {
                await loadSchedule()
                await loadTasks(currentPage, statusFilter)
              }}
              disabled={loading || tasksLoading}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 rounded transition-colors"
              title="スケジュール情報とタスク履歴を更新"
            >
              <RefreshCw className={`w-4 h-4 ${loading || tasksLoading ? 'animate-spin' : ''}`} />
              <span>全体更新</span>
            </button>
            <button
              onClick={() => loadTasks(currentPage, statusFilter)}
              disabled={tasksLoading}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded transition-colors"
              title="タスク履歴のみ更新"
            >
              <RefreshCw className={`w-4 h-4 ${tasksLoading ? 'animate-spin' : ''}`} />
              <span>履歴更新</span>
            </button>
          </div>
        </div>

        {/* 実行履歴一覧 */}
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          {tasksLoading ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">読み込み中...</p>
            </div>
          ) : tasks.length === 0 ? (
            <div className="p-8 text-center">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-400">実行履歴がありません</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      ステータス
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      実行時間
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      結果
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      実行時間
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      アクション
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {tasks.map((task) => (
                    <tr key={task.id} className="hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(task.status)}
                          <span className={`text-sm font-medium ${getStatusColor(task.status)}`}>
                            {task.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        <div>
                          <p>開始: {formatDateTime(task.started_at)}</p>
                          {task.finished_at && (
                            <p>完了: {formatDateTime(task.finished_at)}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        <div>
                          <p>アイテム: {task.items_count}</p>
                          <p>リクエスト: {task.requests_count}</p>
                          {task.error_count > 0 && (
                            <p className="text-red-400">エラー: {task.error_count}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {calculateDuration(task.started_at, task.finished_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => window.open(`/tasks/${task.id}`, '_blank')}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ページネーション */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 0}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 rounded transition-colors"
            >
              前へ
            </button>
            
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = Math.max(0, Math.min(totalPages - 5, currentPage - 2)) + i
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`px-3 py-2 rounded transition-colors ${
                    pageNum === currentPage
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  }`}
                >
                  {pageNum + 1}
                </button>
              )
            })}
            
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages - 1}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 rounded transition-colors"
            >
              次へ
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScheduleDetailPage
