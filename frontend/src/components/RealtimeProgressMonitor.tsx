'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  Download,
  Package,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Wifi,
  WifiOff
} from 'lucide-react';

interface RealtimeProgressData {
  items_count: number;
  requests_count: number;
  responses_count: number;
  errors_count: number;
  bytes_downloaded: number;
  elapsed_time: number;
  items_per_minute: number;
  requests_per_minute: number;
  progress_percentage: number;
  estimated_completion?: string;
}

interface DownloadProgressData {
  url: string;
  status: number;
  size: number;
  download_count: number;
  method: string;
  timestamp: string;
}

interface ItemProgressData {
  item_count: number;
  url: string;
  item_fields: number;
  timestamp: string;
}

interface WebSocketMessage {
  type: 'task_progress' | 'download_progress' | 'item_processed' | 'task_error' | 'task_completion';
  task_id: string;
  data: RealtimeProgressData | DownloadProgressData | ItemProgressData | any;
  timestamp: string;
}

interface RealtimeProgressMonitorProps {
  taskId: string;
  isActive: boolean;
  onComplete?: (taskId: string) => void;
  onError?: (taskId: string, error: any) => void;
}

export default function RealtimeProgressMonitor({
  taskId,
  isActive,
  onComplete,
  onError
}: RealtimeProgressMonitorProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState<RealtimeProgressData>({
    items_count: 0,
    requests_count: 0,
    responses_count: 0,
    errors_count: 0,
    bytes_downloaded: 0,
    elapsed_time: 0,
    items_per_minute: 0,
    requests_per_minute: 0,
    progress_percentage: 0
  });
  const [recentDownloads, setRecentDownloads] = useState<DownloadProgressData[]>([]);
  const [recentItems, setRecentItems] = useState<ItemProgressData[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // WebSocket状態チェック関数
  const isWebSocketReady = (): boolean => {
    return wsRef.current !== null && wsRef.current.readyState === WebSocket.OPEN;
  };

  // 安全なメッセージ送信関数
  const sendWebSocketMessage = (message: any): boolean => {
    try {
      if (isWebSocketReady()) {
        wsRef.current!.send(JSON.stringify(message));
        return true;
      } else {
        console.warn('⚠️ WebSocket not ready for sending message, state:', wsRef.current?.readyState);
        return false;
      }
    } catch (error) {
      console.error('❌ Error sending WebSocket message:', error);
      return false;
    }
  };

  const connectWebSocket = () => {
    if (!isActive) return;

    setConnectionStatus('connecting');

    try {
      const wsUrl = `ws://localhost:8000/ws/realtime-progress`;
      console.log(`🔗 Attempting WebSocket connection to: ${wsUrl}`);

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('🔗 WebSocket connected for realtime progress');
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);

        // 接続確認メッセージを送信（少し遅延を入れて確実に接続完了後に送信）
        setTimeout(() => {
          const message = {
            task_id: taskId,
            action: 'subscribe',
            timestamp: new Date().toISOString()
          };

          if (sendWebSocketMessage(message)) {
            console.log('📡 Subscription message sent:', message);
          } else {
            console.warn('⚠️ Failed to send subscription message');
          }
        }, 100); // 100ms遅延
      };

      wsRef.current.onmessage = (event) => {
        try {
          console.log('📨 WebSocket message received:', event.data);

          // 接続確認メッセージの場合
          if (typeof event.data === 'string' && event.data.startsWith('Connected:')) {
            console.log('✅ WebSocket connection confirmed');
            return;
          }

          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📊 Parsed message:', message);

          // 対象のタスクIDのメッセージのみ処理
          if (message.task_id && message.task_id !== taskId) {
            console.log(`⏭️ Skipping message for different task: ${message.task_id}`);
            return;
          }

          handleWebSocketMessage(message);

        } catch (error) {
          console.error('Error parsing WebSocket message:', {
            error: error.message,
            data: event.data,
            timestamp: new Date().toISOString()
          });
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          timestamp: new Date().toISOString()
        });
        setIsConnected(false);
        setConnectionStatus('disconnected');

        // 自動再接続
        if (isActive && reconnectAttempts < maxReconnectAttempts) {
          console.log(`🔄 Scheduling reconnection attempt ${reconnectAttempts + 1}/${maxReconnectAttempts} in 3 seconds`);
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connectWebSocket();
          }, 3000);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.log('❌ Max reconnection attempts reached');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', {
          type: error.type,
          target: error.target?.readyState,
          url: wsUrl,
          timestamp: new Date().toISOString()
        });
        setConnectionStatus('disconnected');
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('disconnected');
    }
  };

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'task_progress':
        setProgress(message.data as RealtimeProgressData);
        break;

      case 'download_progress':
        const downloadData = message.data as DownloadProgressData;
        setRecentDownloads(prev => [downloadData, ...prev.slice(0, 9)]); // 最新10件
        break;

      case 'item_processed':
        const itemData = message.data as ItemProgressData;
        setRecentItems(prev => [itemData, ...prev.slice(0, 9)]); // 最新10件
        break;

      case 'task_error':
        console.error('Task error:', message.data);
        onError?.(taskId, message.data);
        break;

      case 'task_completion':
        console.log('Task completed:', message.data);
        onComplete?.(taskId);
        break;
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  // 手動再接続
  const manualReconnect = () => {
    console.log('🔄 Manual reconnection triggered');
    setReconnectAttempts(0);
    disconnectWebSocket();
    setTimeout(() => {
      connectWebSocket();
    }, 500);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (isActive) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isActive, taskId]);

  if (!isActive) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* 接続状態 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            {connectionStatus === 'connected' ? (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-green-600">リアルタイム監視中</span>
              </>
            ) : connectionStatus === 'connecting' ? (
              <>
                <Activity className="h-4 w-4 text-yellow-500 animate-pulse" />
                <span className="text-yellow-600">接続中...</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500" />
                <span className="text-red-600">接続切断</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={manualReconnect}
                  className="ml-2"
                >
                  再接続
                </Button>
                {reconnectAttempts > 0 && (
                  <span className="text-xs text-gray-500 ml-2">
                    ({reconnectAttempts}/{maxReconnectAttempts})
                  </span>
                )}
              </>
            )}
          </CardTitle>
        </CardHeader>
      </Card>

      {/* 進捗概要 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            実行進捗
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 進捗バー */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>進捗率</span>
              <span>{progress.progress_percentage.toFixed(1)}%</span>
            </div>
            <Progress value={progress.progress_percentage} className="h-2" />
          </div>

          {/* 統計情報 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-blue-600 mb-1">
                <Package className="h-4 w-4" />
                <span className="text-sm font-medium">アイテム</span>
              </div>
              <div className="text-2xl font-bold">{progress.items_count}</div>
              <div className="text-xs text-gray-500">
                {progress.items_per_minute.toFixed(1)}/分
              </div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-green-600 mb-1">
                <Download className="h-4 w-4" />
                <span className="text-sm font-medium">リクエスト</span>
              </div>
              <div className="text-2xl font-bold">{progress.requests_count}</div>
              <div className="text-xs text-gray-500">
                {progress.requests_per_minute.toFixed(1)}/分
              </div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-purple-600 mb-1">
                <Activity className="h-4 w-4" />
                <span className="text-sm font-medium">ダウンロード</span>
              </div>
              <div className="text-2xl font-bold">{formatBytes(progress.bytes_downloaded)}</div>
              <div className="text-xs text-gray-500">
                {progress.responses_count} レスポンス
              </div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-red-600 mb-1">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">エラー</span>
              </div>
              <div className="text-2xl font-bold">{progress.errors_count}</div>
              <div className="text-xs text-gray-500">
                {progress.errors_count === 0 ? '正常' : '要確認'}
              </div>
            </div>
          </div>

          {/* 実行時間と予測完了時刻 */}
          <div className="flex justify-between items-center pt-2 border-t">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <span className="text-sm">実行時間: {formatDuration(progress.elapsed_time)}</span>
            </div>
            {progress.estimated_completion && (
              <div className="text-sm text-gray-500">
                予測完了: {new Date(progress.estimated_completion).toLocaleTimeString()}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 最近のアクティビティ */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 最近のダウンロード */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">最近のダウンロード</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {recentDownloads.length === 0 ? (
                <p className="text-sm text-gray-500">ダウンロード待機中...</p>
              ) : (
                recentDownloads.map((download, index) => (
                  <div key={index} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Badge
                        variant={download.status === 200 ? "default" : "destructive"}
                        className="text-xs"
                      >
                        {download.status}
                      </Badge>
                      <span className="truncate">{download.url}</span>
                    </div>
                    <span className="text-gray-500 ml-2">
                      {formatBytes(download.size)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* 最近のアイテム */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">最近のアイテム</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {recentItems.length === 0 ? (
                <p className="text-sm text-gray-500">アイテム処理待機中...</p>
              ) : (
                recentItems.map((item, index) => (
                  <div key={index} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Badge variant="outline" className="text-xs">
                        #{item.item_count}
                      </Badge>
                      <span className="truncate">{item.url}</span>
                    </div>
                    <span className="text-gray-500 ml-2">
                      {item.item_fields} フィールド
                    </span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
