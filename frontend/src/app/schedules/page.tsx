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
import RichProgressDisplay from '@/components/schedules/RichProgressDisplay'
import { apiClient } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

// Rich progress統計情報のインターフェース
interface RichStats {
  // 基本カウンター
  items_count: number;
  requests_count: number;
  responses_count: number;
  errors_count: number;

  // 時間情報
  start_time?: string;
  finish_time?: string;
  elapsed_time_seconds: number;

  // 速度メトリクス
  items_per_second: number;
  requests_per_second: number;
  items_per_minute: number;

  // 成功率・エラー率
  success_rate: number;
  error_rate: number;

  // 詳細統計
  downloader_request_bytes: number;
  downloader_response_bytes: number;
  downloader_response_status_count_200: number;
  downloader_response_status_count_404: number;
  downloader_response_status_count_500: number;

  // メモリ・パフォーマンス
  memusage_startup: number;
  memusage_max: number;

  // ログレベル統計
  log_count_debug: number;
  log_count_info: number;
  log_count_warning: number;
  log_count_error: number;
  log_count_critical: number;

  // スケジューラー統計
  scheduler_enqueued: number;
  scheduler_dequeued: number;

  // 重複フィルター
  dupefilter_filtered: number;

  // ファイル統計
  file_count: number;
  file_status_count_downloaded: number;
}

export default function SchedulesPage() {
  const { isAuthenticated, isInitialized, user } = useAuthStore()
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
  const [autoRefresh, setAutoRefresh] = useState(false)

  // Rich progress統計情報
  const [richStatsData, setRichStatsData] = useState<{[scheduleId: string]: RichStats}>({})
  const [selectedScheduleStats, setSelectedScheduleStats] = useState<{schedule: Schedule, richStats: RichStats} | null>(null)

  // 待機タスク情報
  const [pendingTasksInfo, setPendingTasksInfo] = useState({
    total_pending: 0,
    old_pending: 0,
    recent_pending: 0
  })
  const [isResettingTasks, setIsResettingTasks] = useState(false)



  // 管理者権限チェック関数
  const isAdmin = (user: any) => {
    if (!user) return false
    const role = user.role?.toLowerCase()
    return role === 'admin' || role === 'administrator'
  }

  // データ取得（SSR対応）
  useEffect(() => {
    if (typeof window !== 'undefined' && isInitialized && isAuthenticated && user) {
      loadSchedules()
      loadPendingTasksInfo()
    }
  }, [isInitialized, isAuthenticated, user])

  // 統計情報の更新
  useEffect(() => {
    updateStats()
  }, [schedules, taskProgress])

  // 自動更新の設定（SSR対応）
  useEffect(() => {
    if (typeof window === 'undefined' || !isAuthenticated || !user) return

    let interval: NodeJS.Timeout | null = null

    if (autoRefresh) {
      interval = setInterval(() => {
        loadSchedules()
        loadTaskProgress()
        loadPendingTasksInfo()
      }, 5000) // 5秒ごとに更新
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [autoRefresh, isAuthenticated, user])

  // 初回タスク進行状況取得（SSR対応）
  useEffect(() => {
    if (typeof window !== 'undefined' && schedules.length > 0 && isAuthenticated && user) {
      loadTaskProgress()
    }
  }, [schedules, isAuthenticated, user])

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
    // 認証されていない場合はスキップ
    if (!isAuthenticated || !user) {
      console.log('SchedulesPage: Not authenticated, skipping task progress load')
      return
    }

    try {
      const progressData: {[scheduleId: string]: any} = {}

      console.log('🔍 Loading task progress for', schedules.length, 'schedules')

      // 各スケジュールの最新タスクを取得
      for (const schedule of schedules) {
        try {
          // URLパラメータを適切にエンコード
          const params = new URLSearchParams({
            project_id: schedule.project_id,
            spider_id: schedule.spider_id,
            limit: '1'
          });

          // RUNNINGタスクのみを取得（PENDINGは除外）
          const runningParams = new URLSearchParams({
            project_id: schedule.project_id,
            spider_id: schedule.spider_id,
            limit: '1',
            status: 'RUNNING'
          });

          // RUNNINGタスクのみを確認
          let tasks = await apiClient.getTasks({
            project_id: schedule.project_id,
            spider_id: schedule.spider_id,
            status: 'RUNNING',
            limit: 1
          })

          if (tasks.length > 0) {
            const task = tasks[0]

            // 実行中のタスクがある場合のみ表示（待機中は除外）
            if (task.status === 'RUNNING') {
              progressData[schedule.id] = {
                taskId: task.id,
                status: task.status.toLowerCase(),
                itemsScraped: task.items_count || 0,
                requestsCount: task.requests_count || 0,
                responsesCount: task.responses_count || 0,
                errorsCount: task.errors_count || 0,
                startedAt: task.started_at,
                elapsedTime: task.started_at ?
                  Math.floor((new Date().getTime() - new Date(task.started_at).getTime()) / 1000) : 0,
                richStats: task.rich_stats || null,
                scrapyStatsUsed: task.scrapy_stats_used || false
              }

              // Rich progress統計情報を保存
              if (task.rich_stats) {
                setRichStatsData(prev => ({
                  ...prev,
                  [schedule.id]: task.rich_stats
                }))
              }
            }
          }
        } catch (error) {
          // ネットワークエラーやその他のエラー
          console.error(`Network error for schedule ${schedule.id}:`, error)

          // エラーの詳細を表示
          if (error instanceof TypeError && error.message.includes('fetch')) {
            console.error('Fetch failed - possible network or CORS issue')
            console.error('Attempted URL:', `${window.location.origin}/api/tasks/?project_id=${schedule.project_id}&spider_id=${schedule.spider_id}`)
          } else if (error instanceof Error) {
            console.error('Error details:', {
              message: error.message,
              name: error.name,
              stack: error.stack
            })
          }

          // フォールバック: 基本的なタスク取得を試行
          try {
            console.log('Trying fallback for schedule:', schedule.id)
            const fallbackTasks = await apiClient.getTasks({ project_id: schedule.project_id, limit: 1 })
            console.log('Fallback response:', fallbackTasks)
          } catch (fallbackError) {
            console.error('Fallback also failed:', fallbackError)
          }
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

  // 待機タスク情報を取得
  const loadPendingTasksInfo = async () => {
    try {
      const response = await apiClient.get('/api/schedules/pending-tasks/count')

      setPendingTasksInfo(response.data)
    } catch (error) {
      console.error('Failed to load pending tasks info:', error)
    }
  }

  // 待機タスクをリセット
  const handleResetPendingTasks = async (resetAll: boolean = false) => {
    const confirmMessage = resetAll
      ? '⚠️ 全ての実行中・待機中タスクをキャンセルしますか？\n\nこの操作は元に戻せません。\n\n• 実行中のタスクを強制停止\n• 待機中のタスクをキャンセル\n• 全てのタスクキューをクリア'
      : '古い待機タスクと孤立タスクをキャンセルしますか？\n\n以下の処理を実行します：\n• 24時間以上前の待機タスクをキャンセル\n• 関連するスケジュールが存在しない孤立タスクをキャンセル\n\nこの操作により、タスクキューがクリアされます。'

    if (!confirm(confirmMessage)) {
      return
    }

    try {
      setIsResettingTasks(true)
      const response = await apiClient.post('/api/schedules/pending-tasks/reset', {
        hours_back: 24,
        cleanup_orphaned: true,
        reset_all: resetAll
      })

      const { cancelled_count, running_count, orphaned_count, total_cancelled, remaining_pending, remaining_running } = response.data

      if (resetAll) {
        let message = '✅ 全てのタスクをクリアしました\n\n'
        if (running_count > 0) {
          message += `• 実行中タスク: ${running_count} 個停止\n`
        }
        if (cancelled_count > 0) {
          message += `• 待機中タスク: ${cancelled_count} 個キャンセル\n`
        }
        if (total_cancelled === 0) {
          message += '• キャンセル対象のタスクはありませんでした\n'
        }
        message += `\n残りタスク: 実行中 ${remaining_running} 個、待機中 ${remaining_pending} 個`
        alert(message)
      } else {
        let message = '✅ タスクリセット完了\n\n'
        if (cancelled_count > 0) {
          message += `• 古い待機タスク: ${cancelled_count} 個キャンセル\n`
        }
        if (orphaned_count > 0) {
          message += `• 孤立タスク: ${orphaned_count} 個キャンセル\n`
        }
        if (total_cancelled === 0) {
          message += '• キャンセル対象のタスクはありませんでした\n'
        }
        message += `\n残り待機タスク: ${remaining_pending} 個`
        alert(message)
      }

      // 待機タスク情報を再取得
      await loadPendingTasksInfo()
    } catch (error: any) {
      console.error('Failed to reset pending tasks:', error)
      alert(error.response?.data?.detail || 'タスクリセットに失敗しました')
    } finally {
      setIsResettingTasks(false)
    }
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

      // リアルタイム実行の場合は別ウィンドウで進捗モニターを表示
      if (result.realtime && result.task_id) {
        // 別ウィンドウを開く（スパイダーページと同じ仕様）
        const streamingWindow = window.open('', '_blank', 'width=1200,height=800');
        if (!streamingWindow) {
          alert('ポップアップがブロックされました。ポップアップを許可してください。');
          return;
        }

        // ウィンドウにリアルタイム進捗表示のHTMLを設定（スパイダーページと同じ仕様）
        const htmlContent = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>リアルタイム実行監視 - Schedule ${scheduleId}</title>
            <style>
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: #111827;
                color: #f9fafb;
                padding: 20px;
                margin: 0;
                line-height: 1.6;
              }
              .header {
                background: #1f2937;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                border: 1px solid #374151;
              }
              .header h1 {
                margin: 0 0 10px 0;
                color: #60a5fa;
                font-size: 24px;
              }
              .header p {
                margin: 5px 0;
                color: #d1d5db;
              }
              .progress-container {
                background: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
              }
              .progress-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
              }
              .progress-item {
                background: #374151;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
              }
              .progress-item .label {
                font-size: 12px;
                color: #9ca3af;
                margin-bottom: 5px;
              }
              .progress-item .value {
                font-size: 20px;
                font-weight: bold;
                color: #60a5fa;
              }
              .progress-bar {
                width: 100%;
                height: 8px;
                background: #374151;
                border-radius: 4px;
                overflow: hidden;
                margin: 10px 0;
              }
              .progress-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #3b82f6, #60a5fa);
                transition: width 0.3s ease;
                width: 0%;
              }
              .status {
                padding: 15px;
                background: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
                margin-bottom: 20px;
              }
              .status.running {
                border-color: #10b981;
                background: #064e3b;
              }
              .status.completed {
                border-color: #3b82f6;
                background: #1e3a8a;
              }
              .status.error {
                border-color: #ef4444;
                background: #7f1d1d;
              }
              .logs {
                background: #000;
                color: #00ff00;
                padding: 15px;
                border-radius: 8px;
                height: 300px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                border: 1px solid #374151;
              }
              .connection-status {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
              }
              .connection-status.connected {
                background: #10b981;
                color: white;
              }
              .connection-status.disconnected {
                background: #ef4444;
                color: white;
              }
              .connection-status.connecting {
                background: #f59e0b;
                color: white;
              }
            </style>
          </head>
          <body>
            <div class="connection-status" id="connectionStatus">接続中...</div>

            <div class="header">
              <h1>🕷️ リアルタイム実行監視</h1>
              <p><strong>スケジュールID:</strong> ${scheduleId}</p>
              <p><strong>タスクID:</strong> ${result.task_id}</p>
              <p><strong>コマンド:</strong> ${result.command || 'scrapy crawlwithwatchdog'}</p>
              <p><strong>開始時刻:</strong> ${new Date().toLocaleString('ja-JP')}</p>
            </div>

            <div class="progress-container">
              <h3 style="margin-top: 0; color: #60a5fa;">📊 進捗統計</h3>
              <div class="progress-grid">
                <div class="progress-item">
                  <div class="label">アイテム数</div>
                  <div class="value" id="itemsCount">0</div>
                </div>
                <div class="progress-item">
                  <div class="label">リクエスト数</div>
                  <div class="value" id="requestsCount">0</div>
                </div>
                <div class="progress-item">
                  <div class="label">レスポンス数</div>
                  <div class="value" id="responsesCount">0</div>
                </div>
                <div class="progress-item">
                  <div class="label">エラー数</div>
                  <div class="value" id="errorsCount">0</div>
                </div>
                <div class="progress-item">
                  <div class="label">経過時間</div>
                  <div class="value" id="elapsedTime">0秒</div>
                </div>
                <div class="progress-item">
                  <div class="label">アイテム/分</div>
                  <div class="value" id="itemsPerMinute">0</div>
                </div>
              </div>

              <div class="progress-bar">
                <div class="progress-bar-fill" id="progressBarFill"></div>
              </div>
              <div style="text-align: center; margin-top: 5px; color: #9ca3af;">
                進捗: <span id="progressPercentage">0%</span>
              </div>
            </div>

            <div class="status" id="taskStatus">
              <strong>ステータス:</strong> <span id="statusText">初期化中...</span>
            </div>

            <div>
              <h3 style="color: #60a5fa; margin-bottom: 10px;">📝 実行ログ</h3>
              <div class="logs" id="logs">リアルタイム進捗データを待機中...\n</div>
            </div>

            <script>
              const taskId = '${result.task_id}';
              let ws = null;
              let isConnected = false;
              let startTime = Date.now();

              // DOM要素の取得
              const elements = {
                connectionStatus: document.getElementById('connectionStatus'),
                itemsCount: document.getElementById('itemsCount'),
                requestsCount: document.getElementById('requestsCount'),
                responsesCount: document.getElementById('responsesCount'),
                errorsCount: document.getElementById('errorsCount'),
                elapsedTime: document.getElementById('elapsedTime'),
                itemsPerMinute: document.getElementById('itemsPerMinute'),
                progressBarFill: document.getElementById('progressBarFill'),
                progressPercentage: document.getElementById('progressPercentage'),
                taskStatus: document.getElementById('taskStatus'),
                statusText: document.getElementById('statusText'),
                logs: document.getElementById('logs')
              };

              // WebSocket接続
              function connectWebSocket() {
                try {
                  const wsUrl = 'ws://localhost:8000/ws/progress/' + taskId;
                  console.log('Connecting to WebSocket:', wsUrl);

                  ws = new WebSocket(wsUrl);

                  ws.onopen = function() {
                    console.log('WebSocket connected to:', wsUrl);
                    isConnected = true;
                    elements.connectionStatus.textContent = '接続済み';
                    elements.connectionStatus.className = 'connection-status connected';

                    addLog('🔗 WebSocket接続が確立されました: ' + wsUrl);
                    addLog('🎯 タスクID: ' + taskId);
                    elements.statusText.textContent = 'WebSocket接続済み - 進捗データを待機中';
                  };

                  ws.onmessage = function(event) {
                    try {
                      const data = JSON.parse(event.data);
                      handleProgressUpdate(data);
                    } catch (e) {
                      console.error('Failed to parse WebSocket message:', e);
                      addLog('⚠️ WebSocketメッセージの解析に失敗: ' + event.data);
                    }
                  };

                  ws.onclose = function() {
                    console.log('WebSocket disconnected');
                    isConnected = false;
                    elements.connectionStatus.textContent = '切断';
                    elements.connectionStatus.className = 'connection-status disconnected';
                    addLog('🔌 WebSocket接続が切断されました');

                    // 5秒後に再接続を試行
                    setTimeout(connectWebSocket, 5000);
                  };

                  ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    console.error('WebSocket URL:', wsUrl);
                    console.error('WebSocket readyState:', ws ? ws.readyState : 'undefined');
                    addLog('❌ WebSocketエラーが発生しました: ' + wsUrl);
                    addLog('🔍 readyState: ' + (ws ? ws.readyState : 'undefined'));
                  };

                } catch (error) {
                  console.error('Failed to connect WebSocket:', error);
                  addLog('❌ WebSocket接続に失敗しました: ' + error.message);
                }
              }

              // 進捗データの更新
              function handleProgressUpdate(data) {
                console.log('Progress update:', data);

                if (data.task_id === taskId) {
                  // 統計情報の更新
                  if (data.items_count !== undefined) {
                    elements.itemsCount.textContent = data.items_count.toLocaleString();
                  }
                  if (data.requests_count !== undefined) {
                    elements.requestsCount.textContent = data.requests_count.toLocaleString();
                  }
                  if (data.responses_count !== undefined) {
                    elements.responsesCount.textContent = data.responses_count.toLocaleString();
                  }
                  if (data.errors_count !== undefined) {
                    elements.errorsCount.textContent = data.errors_count.toLocaleString();
                  }
                  if (data.items_per_minute !== undefined) {
                    elements.itemsPerMinute.textContent = Math.round(data.items_per_minute).toLocaleString();
                  }

                  // 進捗バーの更新
                  if (data.progress_percentage !== undefined) {
                    const percentage = Math.min(100, Math.max(0, data.progress_percentage));
                    elements.progressBarFill.style.width = percentage + '%';
                    elements.progressPercentage.textContent = percentage.toFixed(1) + '%';
                  }

                  // ステータスの更新
                  if (data.status) {
                    elements.statusText.textContent = data.status;
                    elements.taskStatus.className = 'status ' + (data.status.includes('完了') ? 'completed' : 'running');
                  }

                  // ログの追加
                  if (data.message) {
                    addLog(data.message);
                  }
                }
              }

              // ログの追加
              function addLog(message) {
                const timestamp = new Date().toLocaleTimeString('ja-JP');
                elements.logs.textContent += '[' + timestamp + '] ' + message + '\n';
                elements.logs.scrollTop = elements.logs.scrollHeight;
              }

              // 経過時間の更新
              function updateElapsedTime() {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;

                if (minutes > 0) {
                  elements.elapsedTime.textContent = minutes + '分' + seconds + '秒';
                } else {
                  elements.elapsedTime.textContent = seconds + '秒';
                }
              }

              // 初期化
              connectWebSocket();
              setInterval(updateElapsedTime, 1000);

              // ページが閉じられる時にWebSocketを閉じる
              window.addEventListener('beforeunload', function() {
                if (ws) {
                  ws.close();
                }
              });
            </script>
          </body>
          </html>`;

        streamingWindow.document.write(htmlContent);
        streamingWindow.document.close();

        alert(`リアルタイム実行を開始しました。別ウィンドウで進捗を確認できます。\nタスクID: ${result.task_id}`)
      } else {
        alert(`スケジュールを実行しました。タスクID: ${result.task_id}`)
      }

      // 最終実行時刻を更新
      loadSchedules()
    } catch (error: any) {
      console.error('Schedule run error:', error);

      if (error.response?.status === 409) {
        // 重複実行エラーの場合
        const detail = error.response?.data?.detail || '同じスパイダーが既に実行中です。実行中のタスクが完了してから再試行してください。';
        alert(`⚠️ 重複実行防止\n\n${detail}\n\n💡 ヒント: スケジュールページを更新して実行中タスクの状況を確認してください。`);
      } else {
        const detail = error.response?.data?.detail || 'スケジュールの実行に失敗しました';
        alert(`❌ 実行エラー\n\n${detail}\n\nエラーコード: ${error.response?.status || 'Unknown'}`);
      }
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
      // 認証チェック
      if (!isAuthenticated || !user) {
        alert('認証が必要です。ログインしてください。')
        return
      }

      // 最新のタスクを取得してダウンロード
      const params = new URLSearchParams({
        project_id: schedule.project_id,
        spider_id: schedule.spider_id,
        limit: '1'
      });

      const tasks = await apiClient.getTasks({
        project_id: schedule.project_id,
        spider_id: schedule.spider_id,
        limit: 1
      })

      if (tasks.length > 0) {
        const latestTask = tasks[0]
        // タスク結果ページを新しいタブで開く
        window.open(`/projects/${schedule.project_id}/tasks/${latestTask.id}/results`, '_blank')
      } else {
        alert('このスケジュールの実行結果がありません')
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

  // 認証されていない場合の表示
  if (!isInitialized || !isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50 text-gray-400" />
            <p className="text-lg text-gray-400">
              {!isInitialized ? 'Initializing...' : 'Authentication required'}
            </p>
          </div>
        </div>
      </div>
    )
  }

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
            {/* 自動更新トグル - 無効化 */}
            <div className="flex items-center space-x-2 opacity-50">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                disabled={true}
                className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500 cursor-not-allowed"
              />
              <label htmlFor="autoRefresh" className="text-sm text-gray-500 cursor-not-allowed">
                自動更新 (無効)
              </label>
            </div>

            <button
              onClick={() => {
                loadSchedules()
                loadTaskProgress()
                loadPendingTasksInfo()
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
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
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

          {/* 待機タスク情報 */}
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-3">
              <Clock className={`w-8 h-8 ${pendingTasksInfo.total_pending > 0 ? 'text-yellow-400' : 'text-gray-400'}`} />
              <div className="flex-1">
                <p className="text-sm text-gray-400">待機タスク</p>
                <p className={`text-2xl font-bold ${pendingTasksInfo.total_pending > 0 ? 'text-yellow-400' : 'text-gray-400'}`}>
                  {pendingTasksInfo.total_pending}
                </p>
              </div>
            </div>

            {/* 詳細情報とリセットボタン */}
            <div className="space-y-2">
              {pendingTasksInfo.old_pending > 0 && (
                <div className="flex items-center justify-between">
                  <p className="text-xs text-red-400">
                    古いタスク: {pendingTasksInfo.old_pending} 個
                  </p>
                </div>
              )}

              {pendingTasksInfo.recent_pending > 0 && (
                <div className="flex items-center justify-between">
                  <p className="text-xs text-blue-400">
                    最近のタスク: {pendingTasksInfo.recent_pending} 個
                  </p>
                </div>
              )}

              {/* リセットボタン（管理者のみ表示） */}
              {isAdmin(user) && (
                <div className="space-y-2 mt-3">
                  {/* 通常のリセットボタン */}
                  <button
                    onClick={() => handleResetPendingTasks(false)}
                    disabled={isResettingTasks || pendingTasksInfo.total_pending === 0}
                    className={`w-full flex items-center justify-center space-x-2 px-3 py-2 rounded text-sm transition-colors ${
                      pendingTasksInfo.total_pending === 0
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-red-600 hover:bg-red-700 disabled:bg-red-800'
                    }`}
                    title={pendingTasksInfo.total_pending === 0
                      ? '待機タスクがありません'
                      : '古い待機タスクと孤立タスクをキャンセル'
                    }
                  >
                    {isResettingTasks ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>処理中...</span>
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4" />
                        <span>
                          {pendingTasksInfo.total_pending === 0
                            ? 'タスクなし'
                            : `タスクリセット (${pendingTasksInfo.total_pending})`
                          }
                        </span>
                      </>
                    )}
                  </button>

                  {/* 全てクリアボタン */}
                  <button
                    onClick={() => handleResetPendingTasks(true)}
                    disabled={isResettingTasks}
                    className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded text-sm transition-colors bg-red-800 hover:bg-red-900 disabled:bg-red-900"
                    title="全ての実行中・待機中タスクを強制キャンセル"
                  >
                    {isResettingTasks ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>処理中...</span>
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4" />
                        <span>全てクリア</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* 待機タスクがない場合のメッセージ */}
              {pendingTasksInfo.total_pending === 0 && (
                <p className="text-xs text-gray-500 text-center mt-2">
                  待機中のタスクはありません
                </p>
              )}
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
                            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>
                            <span className="text-sm font-medium text-green-300">
                              🚀 実行中
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

                        {/* プログレスバー */}
                        <div className="space-y-3 mb-4">
                          {/* リクエスト数プログレス */}
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-400 flex items-center gap-1">
                                リクエスト数
                                {taskProgress[schedule.id].scrapyStatsUsed && (
                                  <span className="text-xs text-green-400" title="Rich progressと同じ統計情報">
                                    ✓
                                  </span>
                                )}
                              </span>
                              <span className="text-sm font-bold text-blue-400">
                                {taskProgress[schedule.id].requestsCount.toLocaleString()}
                              </span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                                style={{
                                  width: `${Math.min(100, Math.max(5, (taskProgress[schedule.id].requestsCount / 100) * 100))}%`
                                }}
                              ></div>
                            </div>
                          </div>

                          {/* アイテム数プログレス */}
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-400 flex items-center gap-1">
                                アイテム数
                                {taskProgress[schedule.id].scrapyStatsUsed && (
                                  <span className="text-xs text-green-400" title="Rich progressと同じ統計情報">
                                    ✓
                                  </span>
                                )}
                              </span>
                              <span className="text-sm font-bold text-green-400">
                                {taskProgress[schedule.id].itemsScraped.toLocaleString()}
                              </span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-green-400 h-2 rounded-full transition-all duration-300"
                                style={{
                                  width: `${Math.min(100, Math.max(2, (taskProgress[schedule.id].itemsScraped / Math.max(taskProgress[schedule.id].requestsCount, 1)) * 100))}%`
                                }}
                              ></div>
                            </div>
                          </div>

                          {/* Rich progress追加統計情報 */}
                          {taskProgress[schedule.id].richStats && (
                            <>
                              {/* レスポンス数 */}
                              <div>
                                <div className="flex justify-between items-center mb-1">
                                  <span className="text-sm text-gray-400">レスポンス数</span>
                                  <span className="text-sm font-bold text-cyan-400">
                                    {taskProgress[schedule.id].responsesCount.toLocaleString()}
                                  </span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-1">
                                  <div
                                    className="bg-cyan-400 h-1 rounded-full transition-all duration-300"
                                    style={{
                                      width: `${Math.min(100, Math.max(2, (taskProgress[schedule.id].responsesCount / Math.max(taskProgress[schedule.id].requestsCount, 1)) * 100))}%`
                                    }}
                                  ></div>
                                </div>
                              </div>

                              {/* 処理速度 */}
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="text-center">
                                  <p className="text-gray-400">アイテム/秒</p>
                                  <p className="font-bold text-yellow-400">
                                    {taskProgress[schedule.id].richStats.items_per_second.toFixed(2)}
                                  </p>
                                </div>
                                <div className="text-center">
                                  <p className="text-gray-400">成功率</p>
                                  <p className="font-bold text-purple-400">
                                    {taskProgress[schedule.id].richStats.success_rate.toFixed(1)}%
                                  </p>
                                </div>
                              </div>

                              {/* 詳細統計ボタン */}
                              <div className="text-center">
                                <button
                                  onClick={() => setSelectedScheduleStats({
                                    schedule: schedule,
                                    richStats: taskProgress[schedule.id].richStats
                                  })}
                                  className="text-xs text-blue-400 hover:text-blue-300 underline"
                                >
                                  詳細統計を表示
                                </button>
                              </div>
                            </>
                          )}

                          {/* 経過時間 */}
                          <div className="text-center">
                            <p className="text-sm text-gray-400">経過時間</p>
                            <p className="text-lg font-bold text-purple-400">
                              {formatElapsedTime(taskProgress[schedule.id].elapsedTime)}
                            </p>
                          </div>
                        </div>

                        {/* 全体プログレス */}
                        {taskProgress[schedule.id].status === 'running' && (
                          <div className="mt-2">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs text-gray-400">全体進行状況</span>
                              <span className="text-xs text-purple-400">
                                {taskProgress[schedule.id].itemsScraped > 0
                                  ? `${Math.round((taskProgress[schedule.id].itemsScraped / Math.max(taskProgress[schedule.id].requestsCount, taskProgress[schedule.id].itemsScraped)) * 100)}%`
                                  : '開始中...'
                                }
                              </span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-blue-400 to-green-400 h-2 rounded-full transition-all duration-500"
                                style={{
                                  width: `${Math.min(100, Math.max(3, taskProgress[schedule.id].itemsScraped > 0
                                    ? (taskProgress[schedule.id].itemsScraped / Math.max(taskProgress[schedule.id].requestsCount, taskProgress[schedule.id].itemsScraped)) * 100
                                    : (taskProgress[schedule.id].elapsedTime / 60) * 10
                                  ))}%`
                                }}
                              ></div>
                            </div>
                          </div>
                        )}


                      </div>
                    ) : schedule.latest_task ? (
                      /* 最新完了タスクの表示 */
                      <div className="mt-4 p-3 bg-gray-700/50 rounded-lg border border-gray-600">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 rounded-full bg-blue-400"></div>
                            <span className="text-sm font-medium text-gray-300">
                              ✅ 最新実行完了
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

                        <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
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
                        </div>

                        {/* 完了タスクの進行状況バー（常に表示） */}
                        <div className="w-full bg-gray-600 rounded-full h-2 mb-2">
                          <div className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-500 flex items-center justify-center text-xs font-bold text-white"
                               style={{
                                 width: '100%' // 完了タスクは常に100%
                               }}>
                            100%
                          </div>
                        </div>

                        {/* 完了タスクの詳細説明（常に表示） */}
                        <div className="text-xs text-gray-600 mt-1">
                          完了: {schedule.latest_task.items_count || 0}アイテム取得 ({schedule.latest_task.requests_count || 0}リクエスト)
                        </div>

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

                  {/* Rich進捗表示（実行中のみ） */}
                  {taskProgress[schedule.id] && taskProgress[schedule.id].status === 'running' && (
                    <div className="mt-4">
                      <RichProgressDisplay
                        scheduleId={schedule.id}
                        progressData={{
                          taskId: taskProgress[schedule.id].taskId,
                          status: taskProgress[schedule.id].status as 'running' | 'pending' | 'completed' | 'failed',
                          itemsScraped: taskProgress[schedule.id].itemsScraped,
                          requestsCount: taskProgress[schedule.id].requestsCount,
                          elapsedTime: taskProgress[schedule.id].elapsedTime,
                          startedAt: taskProgress[schedule.id].startedAt
                        }}
                        className="mb-4"
                      />
                    </div>
                  )}

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

      {/* Rich progress統計情報詳細モーダル */}
      {selectedScheduleStats && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white flex items-center space-x-2">
                <BarChart3 className="h-6 w-6 text-blue-400" />
                <span>Rich Progress統計情報</span>
                <span className="text-xs text-green-400" title="Rich progressと同じ統計情報">
                  ✓
                </span>
              </h3>
              <button
                onClick={() => setSelectedScheduleStats(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-4 p-4 bg-gray-700 rounded-lg">
              <h4 className="text-lg font-medium text-white mb-2">スケジュール情報</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">スケジュール名</p>
                  <p className="text-white font-medium">{selectedScheduleStats.schedule.name}</p>
                </div>
                <div>
                  <p className="text-gray-400">プロジェクト</p>
                  <p className="text-white font-medium">{selectedScheduleStats.schedule.project_name}</p>
                </div>
                <div>
                  <p className="text-gray-400">スパイダー</p>
                  <p className="text-white font-medium">{selectedScheduleStats.schedule.spider_name}</p>
                </div>
                <div>
                  <p className="text-gray-400">実行間隔</p>
                  <p className="text-white font-medium">{selectedScheduleStats.schedule.interval_minutes}分</p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {/* 基本統計 */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-blue-400" />
                  <span>基本統計</span>
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">アイテム数</p>
                    <p className="text-xl font-bold text-cyan-400">
                      {selectedScheduleStats.richStats.items_count.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">リクエスト数</p>
                    <p className="text-xl font-bold text-blue-400">
                      {selectedScheduleStats.richStats.requests_count.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">レスポンス数</p>
                    <p className="text-xl font-bold text-green-400">
                      {selectedScheduleStats.richStats.responses_count.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">エラー数</p>
                    <p className="text-xl font-bold text-red-400">
                      {selectedScheduleStats.richStats.errors_count.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* 速度メトリクス */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-yellow-400" />
                  <span>速度メトリクス</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">アイテム/秒</p>
                    <p className="text-xl font-bold text-yellow-400">
                      {selectedScheduleStats.richStats.items_per_second.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">リクエスト/秒</p>
                    <p className="text-xl font-bold text-orange-400">
                      {selectedScheduleStats.richStats.requests_per_second.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">アイテム/分</p>
                    <p className="text-xl font-bold text-pink-400">
                      {selectedScheduleStats.richStats.items_per_minute.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {/* 成功率・エラー率 */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-purple-400" />
                  <span>成功率・エラー率</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">成功率</p>
                    <p className="text-xl font-bold text-green-400">
                      {selectedScheduleStats.richStats.success_rate.toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">エラー率</p>
                    <p className="text-xl font-bold text-red-400">
                      {selectedScheduleStats.richStats.error_rate.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* HTTPステータス統計 */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-indigo-400" />
                  <span>HTTPステータス統計</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">200 OK</p>
                    <p className="text-xl font-bold text-green-400">
                      {selectedScheduleStats.richStats.downloader_response_status_count_200.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">404 Not Found</p>
                    <p className="text-xl font-bold text-yellow-400">
                      {selectedScheduleStats.richStats.downloader_response_status_count_404.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-xs text-gray-400">500 Server Error</p>
                    <p className="text-xl font-bold text-red-400">
                      {selectedScheduleStats.richStats.downloader_response_status_count_500.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* 時間情報 */}
              {(selectedScheduleStats.richStats.start_time || selectedScheduleStats.richStats.finish_time) && (
                <div>
                  <h4 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
                    <Clock className="h-5 w-5 text-blue-400" />
                    <span>時間情報</span>
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {selectedScheduleStats.richStats.start_time && (
                      <div className="bg-gray-700 rounded-lg p-4">
                        <p className="text-xs text-gray-400">開始時刻</p>
                        <p className="text-sm font-bold text-blue-400">
                          {new Date(selectedScheduleStats.richStats.start_time).toLocaleString('ja-JP')}
                        </p>
                      </div>
                    )}
                    {selectedScheduleStats.richStats.finish_time && (
                      <div className="bg-gray-700 rounded-lg p-4">
                        <p className="text-xs text-gray-400">終了時刻</p>
                        <p className="text-sm font-bold text-green-400">
                          {new Date(selectedScheduleStats.richStats.finish_time).toLocaleString('ja-JP')}
                        </p>
                      </div>
                    )}
                    <div className="bg-gray-700 rounded-lg p-4">
                      <p className="text-xs text-gray-400">実行時間</p>
                      <p className="text-sm font-bold text-yellow-400">
                        {selectedScheduleStats.richStats.elapsed_time_seconds.toFixed(1)}秒
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedScheduleStats(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                閉じる
              </button>
            </div>
          </div>
        </div>
      )}


    </div>
  )
}
