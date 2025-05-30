'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Terminal as TerminalIcon, X, Minimize2, Maximize2 } from 'lucide-react';

interface TerminalProps {
  className?: string;
}

interface TerminalLine {
  id: string;
  type: 'command' | 'output' | 'error';
  content: string;
  timestamp: Date;
}

const Terminal: React.FC<TerminalProps> = ({ className = '' }) => {
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [currentDir, setCurrentDir] = useState('/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isMinimized, setIsMinimized] = useState(false);

  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 許可されたコマンド
  const allowedCommands = ['scrapy', 'crontab', 'pwd', 'less', 'cd', 'ls', 'clear'];

  // ハートビート機能
  const startHeartbeat = useCallback((ws: WebSocket) => {
    // 既存のハートビートをクリア
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }

    // 30秒間隔でpingを送信
    heartbeatRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        console.log('Sending heartbeat ping...');
        ws.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now(),
          heartbeat: true
        }));
      } else {
        console.log('WebSocket not open, stopping heartbeat');
        if (heartbeatRef.current) {
          clearInterval(heartbeatRef.current);
          heartbeatRef.current = null;
        }
      }
    }, 30000); // 30秒間隔
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  // WebSocket接続
  const connectWebSocket = useCallback(() => {
    // 既存の接続があれば閉じる
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close();
    }

    try {
      const wsUrl = 'ws://localhost:8000/ws/terminal';
      console.log('Attempting to connect to terminal WebSocket:', wsUrl);
      console.log('Browser WebSocket support:', typeof WebSocket !== 'undefined');

      const ws = new WebSocket(wsUrl);
      console.log('WebSocket object created:', {
        url: ws.url,
        readyState: ws.readyState,
        protocol: ws.protocol
      });

      ws.onopen = (event) => {
        setIsConnected(true);
        console.log('Terminal WebSocket connected successfully:', {
          readyState: ws.readyState,
          protocol: ws.protocol,
          extensions: ws.extensions,
          event: event
        });
        addLine('output', 'Connected to terminal server');

        // ハートビートを開始
        startHeartbeat(ws);
      };

      ws.onmessage = (event) => {
        console.log('Terminal WebSocket received:', event.data);
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'output') {
            // 複数行の出力を処理
            if (data.content.includes('\n')) {
              const lines = data.content.split('\n');
              lines.forEach(line => {
                if (line.trim()) {
                  addLine('output', line);
                }
              });
            } else {
              addLine('output', data.content);
            }
          } else if (data.type === 'error') {
            addLine('error', data.content);
          } else if (data.type === 'directory_changed') {
            setCurrentDir(data.directory);
          } else if (data.type === 'ping') {
            // サーバーからのpingメッセージを処理
            console.log('Received ping from server:', data.content);
            addLine('system', `Server ping: ${data.content}`);
          } else if (data.type === 'pong') {
            // サーバーからのpongメッセージを処理（ハートビート応答）
            console.log('Received pong from server:', data.content);
            if (data.content.includes('heartbeat_ack')) {
              // ハートビートの応答は表示しない（ログのみ）
              console.log('Heartbeat acknowledged by server');
            } else {
              addLine('output', data.content);
            }
          } else {
            console.log('Unknown message type:', data.type, data);
          }
        } catch (parseError) {
          console.error('Failed to parse WebSocket message:', parseError);
          addLine('error', 'Failed to parse server response');
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        stopHeartbeat(); // ハートビートを停止

        console.log('Terminal WebSocket closed:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          timestamp: new Date().toISOString()
        });

        // エラー詳細をターミナルに表示
        addLine('error', `Connection closed: ${event.code} - ${event.reason || 'No reason'}`);
        addLine('error', `Clean close: ${event.wasClean}`);

        // WebSocketクローズコードの説明
        const closeCodeExplanation = getCloseCodeExplanation(event.code);
        if (closeCodeExplanation) {
          addLine('error', `Close code explanation: ${closeCodeExplanation}`);
        }

        // 正常な切断でない場合のみ再接続
        if (!event.wasClean && event.code !== 1000) {
          addLine('output', 'Attempting to reconnect in 3 seconds...');

          // 既存の再接続タイマーをクリア
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect terminal WebSocket...');
            connectWebSocket();
          }, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('Terminal WebSocket error details:', {
          type: error.type,
          target: {
            readyState: error.target?.readyState,
            url: error.target?.url,
            protocol: error.target?.protocol,
            extensions: error.target?.extensions
          },
          timestamp: new Date().toISOString(),
          error: error,
          errorString: error.toString(),
          errorMessage: error.message || 'No message',
          errorCode: error.code || 'No code'
        });
        setIsConnected(false);

        // エラー詳細をターミナルに表示
        addLine('error', `WebSocket Error: ${error.type || 'Connection failed'}`);
        addLine('error', `ReadyState: ${error.target?.readyState} (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)`);
        addLine('error', `Error details: ${error.message || error.toString()}`);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create terminal WebSocket:', error);
    }
  }, []);

  // WebSocketクローズコードの説明
  const getCloseCodeExplanation = (code: number): string | null => {
    const explanations: { [key: number]: string } = {
      1000: 'Normal closure',
      1001: 'Going away (page refresh or navigation)',
      1002: 'Protocol error',
      1003: 'Unsupported data type',
      1005: 'No status code received',
      1006: 'Connection closed abnormally',
      1007: 'Invalid data received',
      1008: 'Policy violation',
      1009: 'Message too large',
      1010: 'Extension negotiation failed',
      1011: 'Server error',
      1012: 'Service restart',
      1013: 'Try again later',
      1014: 'Bad gateway',
      1015: 'TLS handshake failure'
    };
    return explanations[code] || null;
  };

  // 行を追加
  const addLine = (type: 'command' | 'output' | 'error' | 'system', content: string) => {
    const newLine: TerminalLine = {
      id: Date.now().toString() + Math.random(),
      type: type === 'system' ? 'output' : type,
      content,
      timestamp: new Date()
    };

    setLines(prev => [...prev, newLine]);
  };

  // コマンド実行
  const executeCommand = async (command: string) => {
    if (!command.trim()) return;

    // コマンド履歴に追加
    setCommandHistory(prev => [...prev, command]);
    setHistoryIndex(-1);

    // コマンドを表示
    addLine('command', `${getPrompt()} ${command}`);

    // clearコマンドの処理
    if (command.trim() === 'clear') {
      setLines([]);
      setCurrentCommand('');
      return;
    }

    // testコマンドの処理（デバッグ用）
    if (command.trim() === 'test') {
      addLine('output', 'Terminal test successful!');
      addLine('output', `Connection state: ${wsRef.current?.readyState} (1=OPEN)`);
      addLine('output', `Current directory: ${currentDir}`);
      addLine('output', `WebSocket URL: ws://localhost:8000/ws/terminal`);
      setCurrentCommand('');
      return;
    }

    // pingコマンドの処理（WebSocket接続テスト）
    if (command.trim() === 'ping') {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        addLine('output', 'Sending ping to server...');
        wsRef.current.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      } else {
        addLine('error', 'WebSocket not connected');
      }
      setCurrentCommand('');
      return;
    }

    // コマンドの検証
    const commandParts = command.trim().split(' ');
    const baseCommand = commandParts[0];

    if (!allowedCommands.includes(baseCommand)) {
      addLine('error', `Command '${baseCommand}' not allowed. Available commands: ${allowedCommands.join(', ')}`);
      setCurrentCommand('');
      return;
    }

    // WebSocket経由でコマンド送信
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('Sending command to WebSocket:', command);
      wsRef.current.send(JSON.stringify({
        type: 'command',
        command: command,
        directory: currentDir
      }));
    } else {
      addLine('error', `Terminal not connected (state: ${wsRef.current?.readyState})`);
    }

    setCurrentCommand('');
  };

  // プロンプト生成
  const getPrompt = () => {
    const shortDir = currentDir.replace('/home/igtmtakan/workplace/python/scrapyUI/', '~/');
    return `scrapy@ui:${shortDir}$`;
  };

  // キーボードイベント処理
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setCurrentCommand(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex !== -1) {
        const newIndex = historyIndex + 1;
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1);
          setCurrentCommand('');
        } else {
          setHistoryIndex(newIndex);
          setCurrentCommand(commandHistory[newIndex]);
        }
      }
    }
  };

  // 自動スクロール
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [lines]);

  // WebSocket接続
  useEffect(() => {
    connectWebSocket();

    return () => {
      // ハートビートを停止
      stopHeartbeat();

      // 再接続タイマーをクリア
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      // WebSocket接続を閉じる
      if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [connectWebSocket, stopHeartbeat]);

  // フォーカス管理
  useEffect(() => {
    if (inputRef.current && !isMinimized) {
      inputRef.current.focus();
    }
  }, [isMinimized]);

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => setIsMinimized(false)}
          className="flex items-center gap-2 bg-gray-800 text-green-400 hover:bg-gray-700"
        >
          <TerminalIcon className="w-4 h-4" />
          Terminal
        </Button>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Terminal Information */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
                🚀 ScrapyUI Terminal v1.0
              </h4>
              <p className="text-blue-700 dark:text-blue-300">
                📁 Working directory: {currentDir.replace('/home/igtmtakan/workplace/python/scrapyUI/', '~/')}
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
                ⚡ Available Commands
              </h4>
              <p className="text-blue-700 dark:text-blue-300">
                {allowedCommands.join(', ')}
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
                💡 Usage Tips
              </h4>
              <p className="text-blue-700 dark:text-blue-300">
                Type "clear" to clear screen, use ↑↓ for command history
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Terminal */}
      <Card className="bg-gray-900 text-green-400 font-mono">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-green-400">
              <TerminalIcon className="w-4 h-4" />
              Terminal
              {isConnected ? (
                <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              ) : (
                <span className="w-2 h-2 bg-red-400 rounded-full"></span>
              )}
            </CardTitle>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMinimized(true)}
                className="text-green-400 hover:bg-gray-800 p-1 h-6 w-6"
              >
                <Minimize2 className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div
            ref={terminalRef}
            className="h-[600px] overflow-y-auto p-4 bg-black text-xs leading-tight"
            style={{ fontFamily: 'Monaco, "Lucida Console", monospace' }}
          >
            {lines.map((line) => (
              <div
                key={line.id}
                className={`mb-1 ${
                  line.type === 'command'
                    ? 'text-white'
                    : line.type === 'error'
                    ? 'text-red-400'
                    : 'text-green-300'
                }`}
              >
                {line.content}
              </div>
            ))}

            {/* 現在のプロンプト */}
            <div className="flex items-center text-white">
              <span className="text-green-400 mr-2">{getPrompt()}</span>
              <Input
                ref={inputRef}
                value={currentCommand}
                onChange={(e) => setCurrentCommand(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 bg-transparent border-none text-white text-xs p-0 h-auto focus:ring-0 focus:outline-none"
                style={{ fontFamily: 'Monaco, "Lucida Console", monospace' }}
                placeholder=""
                disabled={!isConnected}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Terminal;
