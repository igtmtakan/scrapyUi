'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  task_id?: string
  data?: any
  timestamp?: string
}

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnectAttempts?: number
  reconnectInterval?: number
  // タスク詳細ページ用のコールバック
  onProgressUpdate?: (data: any) => void
  onItemScraped?: (data: any) => void
  onTaskStatusChange?: (status: string, details?: any) => void
  onWebSocketError?: (error: any, details?: any) => void
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectAttempts = 5,
  reconnectInterval = 3000,
  onProgressUpdate,
  onItemScraped,
  onTaskStatusChange,
  onWebSocketError
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  const ws = useRef<WebSocket | null>(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    // URLが空の場合は接続しない
    if (!url) {
      console.warn('WebSocket URL is empty, skipping connection')
      return
    }

    // URLの形式を検証
    try {
      const wsUrl = new URL(url)
      if (!['ws:', 'wss:'].includes(wsUrl.protocol)) {
        console.error('Invalid WebSocket URL protocol:', wsUrl.protocol)
        setConnectionStatus('error')
        return
      }
    } catch (error) {
      console.error('Invalid WebSocket URL format:', url, error)
      setConnectionStatus('error')
      return
    }

    console.log('Attempting WebSocket connection to:', url)

    // 既存の接続をクリーンアップ
    if (ws.current) {
      if (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING) {
        console.log('WebSocket already connected or connecting')
        return
      }
      ws.current.close()
      ws.current = null
    }

    setConnectionStatus('connecting')

    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('WebSocket connected successfully to:', url)
        setIsConnected(true)
        setConnectionStatus('connected')
        reconnectCount.current = 0
        onConnect?.()
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)

          // 汎用メッセージコールバック
          onMessage?.(message)

          // 特定のメッセージタイプに対する専用コールバック
          switch (message.type) {
            case 'progress_update':
              onProgressUpdate?.(message.data)
              break
            case 'item_scraped':
              onItemScraped?.(message.data)
              break
            case 'task_status_change':
              onTaskStatusChange?.(message.data?.status, message.data)
              break
            case 'error':
              onWebSocketError?.(message.data?.error, message.data)
              break
            default:
              // その他のメッセージタイプは汎用コールバックで処理
              break
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error, 'Raw data:', event.data)
          onWebSocketError?.(error, { raw_data: event.data, error_type: 'parse_error' })
        }
      }

      ws.current.onclose = () => {
        setIsConnected(false)
        setConnectionStatus('disconnected')
        onDisconnect?.()

        // 自動再接続
        if (reconnectCount.current < reconnectAttempts) {
          reconnectCount.current++
          reconnectTimer.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      ws.current.onerror = (error) => {
        const errorDetails = {
          url,
          readyState: ws.current?.readyState,
          readyStateText: ws.current?.readyState === 0 ? 'CONNECTING' :
                         ws.current?.readyState === 1 ? 'OPEN' :
                         ws.current?.readyState === 2 ? 'CLOSING' :
                         ws.current?.readyState === 3 ? 'CLOSED' : 'UNKNOWN',
          error: error,
          errorType: error.type,
          errorMessage: error instanceof ErrorEvent ? error.message :
                       error instanceof Event ? `Event type: ${error.type}` :
                       typeof error === 'object' ? JSON.stringify(error) :
                       String(error) || 'Unknown error',
          timestamp: new Date().toISOString()
        }

        console.warn('WebSocket error details (non-critical):', errorDetails)
        setConnectionStatus('error')

        // 汎用エラーコールバック
        onError?.(error)

        // 専用エラーコールバック
        onWebSocketError?.(error, errorDetails)
      }

    } catch (error) {
      setConnectionStatus('error')
      console.error('WebSocket connection error:', error)
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectInterval, onProgressUpdate, onItemScraped, onTaskStatusChange, onWebSocketError])

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }

    if (ws.current) {
      ws.current.close()
      ws.current = null
    }

    setIsConnected(false)
    setConnectionStatus('disconnected')
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
      return true
    }
    return false
  }, [])

  const subscribeToTask = useCallback((taskId: string) => {
    return sendMessage({
      type: 'subscribe_task',
      task_id: taskId,
      timestamp: new Date().toISOString()
    })
  }, [sendMessage])

  const unsubscribeFromTask = useCallback((taskId: string) => {
    return sendMessage({
      type: 'unsubscribe_task',
      task_id: taskId,
      timestamp: new Date().toISOString()
    })
  }, [sendMessage])

  const ping = useCallback(() => {
    return sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }, [sendMessage])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [url]) // URLが変更された時のみ再接続

  // 定期的なping送信
  useEffect(() => {
    if (!isConnected) return

    const pingInterval = setInterval(() => {
      ping()
    }, 30000) // 30秒ごと

    return () => clearInterval(pingInterval)
  }, [isConnected, ping])

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    subscribeToTask,
    unsubscribeFromTask,
    ping,
    connect,
    disconnect
  }
}
