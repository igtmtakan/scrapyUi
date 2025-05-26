'use client';

import React, { useState, useEffect } from 'react';
import ClientOnly from '@/components/common/ClientOnly';
import {
  Wifi,
  WifiOff,
  Send,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';

export default function WebSocketTestPage() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [messages, setMessages] = useState<Array<{ type: 'sent' | 'received'; content: string; timestamp: string }>>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [clientId, setClientId] = useState('');
  const [mounted, setMounted] = useState(false);

  const connect = () => {
    if (ws?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const websocket = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/${clientId}`);

      websocket.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        addMessage('received', 'WebSocket connection established');
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          addMessage('received', JSON.stringify(data, null, 2));
        } catch (error) {
          addMessage('received', event.data);
        }
      };

      websocket.onclose = () => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        addMessage('received', 'WebSocket connection closed');
      };

      websocket.onerror = (error) => {
        setConnectionStatus('error');
        addMessage('received', `WebSocket error: ${error}`);
      };

      setWs(websocket);
    } catch (error) {
      setConnectionStatus('error');
      addMessage('received', `Connection error: ${error}`);
    }
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      setWs(null);
    }
  };

  const sendMessage = () => {
    if (ws?.readyState === WebSocket.OPEN && inputMessage.trim()) {
      try {
        const message = JSON.parse(inputMessage);
        ws.send(JSON.stringify(message));
        addMessage('sent', JSON.stringify(message, null, 2));
        setInputMessage('');
      } catch (error) {
        // JSON形式でない場合はそのまま送信
        ws.send(inputMessage);
        addMessage('sent', inputMessage);
        setInputMessage('');
      }
    }
  };

  const addMessage = (type: 'sent' | 'received', content: string) => {
    setMessages(prev => [...prev, {
      type,
      content,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const sendPing = () => {
    if (ws?.readyState === WebSocket.OPEN) {
      const pingMessage = {
        type: 'ping',
        timestamp: new Date().toISOString()
      };
      ws.send(JSON.stringify(pingMessage));
      addMessage('sent', JSON.stringify(pingMessage, null, 2));
    }
  };

  const subscribeToTask = () => {
    if (ws?.readyState === WebSocket.OPEN) {
      const subscribeMessage = {
        type: 'subscribe_task',
        task_id: 'test_task_123',
        timestamp: new Date().toISOString()
      };
      ws.send(JSON.stringify(subscribeMessage));
      addMessage('sent', JSON.stringify(subscribeMessage, null, 2));
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'connecting':
        return <RefreshCw className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  // クライアントサイドでのみ初期化
  useEffect(() => {
    setMounted(true);
    setClientId(`client_${Date.now()}`);
  }, []);

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  // サーバーサイドレンダリング中は何も表示しない
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Wifi className="h-8 w-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold">WebSocket Test</h1>
                <p className="text-gray-400">Test WebSocket connection and messaging</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <span className="text-sm font-medium capitalize">{connectionStatus}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Connection Control */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Connection Control</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Client ID
                </label>
                <input
                  type="text"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isConnected}
                />
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={connect}
                  disabled={isConnected}
                  className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Wifi className="h-4 w-4" />
                  <span>Connect</span>
                </button>

                <button
                  onClick={disconnect}
                  disabled={!isConnected}
                  className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <WifiOff className="h-4 w-4" />
                  <span>Disconnect</span>
                </button>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-700">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={sendPing}
                  disabled={!isConnected}
                  className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  Send Ping
                </button>

                <button
                  onClick={subscribeToTask}
                  disabled={!isConnected}
                  className="w-full px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  Subscribe to Test Task
                </button>
              </div>
            </div>
          </div>

          {/* Message Input */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Send Message</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Message (JSON format)
                </label>
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder='{"type": "ping", "timestamp": "2023-01-01T00:00:00Z"}'
                  className="w-full h-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>

              <button
                onClick={sendMessage}
                disabled={!isConnected || !inputMessage.trim()}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-4 w-4" />
                <span>Send Message</span>
              </button>
            </div>
          </div>

          {/* Connection Info */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Connection Info</h2>

            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-400">Status:</span>
                <span className={`ml-2 text-sm font-medium ${
                  connectionStatus === 'connected' ? 'text-green-400' :
                  connectionStatus === 'connecting' ? 'text-yellow-400' :
                  connectionStatus === 'error' ? 'text-red-400' : 'text-gray-400'
                }`}>
                  {connectionStatus.toUpperCase()}
                </span>
              </div>

              <ClientOnly fallback={
                <div>
                  <span className="text-sm text-gray-400">URL:</span>
                  <span className="ml-2 text-sm font-mono">
                    {process.env.NEXT_PUBLIC_WS_URL}/ws/[loading...]
                  </span>
                </div>
              }>
                <div>
                  <span className="text-sm text-gray-400">URL:</span>
                  <span className="ml-2 text-sm font-mono">
                    {process.env.NEXT_PUBLIC_WS_URL}/ws/{clientId}
                  </span>
                </div>
              </ClientOnly>

              <div>
                <span className="text-sm text-gray-400">Messages:</span>
                <span className="ml-2 text-sm font-medium">
                  {messages.length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Messages Log */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Messages Log</h2>
            <button
              onClick={clearMessages}
              className="flex items-center space-x-2 px-3 py-1 bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              <span>Clear</span>
            </button>
          </div>

          <div className="bg-gray-900 rounded-md p-4 h-96 overflow-y-auto font-mono text-sm">
            {messages.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                No messages yet. Connect and send a message to see logs here.
              </div>
            ) : (
              <div className="space-y-2">
                {messages.map((message, index) => (
                  <div key={index} className="flex">
                    <span className="text-gray-500 w-20 flex-shrink-0">
                      [{message.timestamp}]
                    </span>
                    <span className={`w-16 flex-shrink-0 ${
                      message.type === 'sent' ? 'text-blue-400' : 'text-green-400'
                    }`}>
                      {message.type.toUpperCase()}:
                    </span>
                    <pre className="text-gray-300 whitespace-pre-wrap flex-1">
                      {message.content}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
