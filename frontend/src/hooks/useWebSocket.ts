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
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectAttempts = 5,
  reconnectInterval = 3000
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
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
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
        console.error('WebSocket error:', {
          url,
          readyState: ws.current?.readyState,
          error: error
        })
        setConnectionStatus('error')
        onError?.(error)
      }

    } catch (error) {
      setConnectionStatus('error')
      console.error('WebSocket connection error:', error)
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectInterval])

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
