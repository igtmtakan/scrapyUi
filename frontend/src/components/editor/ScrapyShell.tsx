'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Terminal,
  Play,
  Square,
  Trash2,
  Download,
  Copy,
  Send,
  History,
  HelpCircle,
  Settings
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ShellCommand {
  id: string;
  command: string;
  output: string;
  timestamp: Date;
  status: 'success' | 'error' | 'running';
}

interface ScrapyShellProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ScrapyShell({ isOpen, onClose }: ScrapyShellProps) {
  const [commands, setCommands] = useState<ShellCommand[]>([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [showHelp, setShowHelp] = useState(false);
  const [shellUrl, setShellUrl] = useState('https://example.com');

  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 初期化時にウェルカムメッセージを表示
  useEffect(() => {
    if (isOpen && commands.length === 0) {
      const welcomeCommand: ShellCommand = {
        id: 'welcome',
        command: '# Scrapy Shell 開始',
        output: `Scrapy Shell へようこそ！

利用可能なコマンド:
- fetch(url): URLからページを取得
- view(response): レスポンスをブラウザで表示
- response.css('selector'): CSSセレクターでデータ抽出
- response.xpath('xpath'): XPathでデータ抽出
- response.text: ページのHTMLテキスト
- response.url: 現在のURL
- response.status: HTTPステータスコード

例:
fetch('https://example.com')
response.css('title::text').get()
response.xpath('//title/text()').get()

ヘルプを表示するには 'help' と入力してください。`,
        timestamp: new Date(),
        status: 'success'
      };
      setCommands([welcomeCommand]);
    }
  }, [isOpen, commands.length]);

  // ターミナルを最下部にスクロール
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [commands]);

  // 入力フィールドにフォーカス
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const executeCommand = async (command: string) => {
    if (!command.trim()) return;

    const newCommand: ShellCommand = {
      id: Date.now().toString(),
      command: command.trim(),
      output: '',
      timestamp: new Date(),
      status: 'running'
    };

    setCommands(prev => [...prev, newCommand]);
    setCommandHistory(prev => [...prev, command.trim()]);
    setHistoryIndex(-1);
    setCurrentCommand('');
    setIsRunning(true);

    try {
      // 実際のAPIを呼び出し
      const response = await apiClient.executeShellCommand(command.trim(), shellUrl);

      setCommands(prev => prev.map(cmd =>
        cmd.id === newCommand.id
          ? {
              ...cmd,
              output: response.output,
              status: response.status === 'success' ? 'success' as const : 'error' as const
            }
          : cmd
      ));
    } catch (error) {
      setCommands(prev => prev.map(cmd =>
        cmd.id === newCommand.id
          ? {
              ...cmd,
              output: `エラー: ${error instanceof Error ? error.message : 'Unknown error'}`,
              status: 'error' as const
            }
          : cmd
      ));
    } finally {
      setIsRunning(false);
    }
  };

  const simulateScrapyCommand = async (command: string): Promise<string> => {
    // 実際の実装では、バックエンドAPIを呼び出してScrapyシェルコマンドを実行
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    if (command === 'help') {
      return `Scrapy Shell コマンドヘルプ:

基本コマンド:
  fetch(url)                    - URLからページを取得
  view(response)                - レスポンスをブラウザで表示

レスポンス操作:
  response.url                  - 現在のURL
  response.status               - HTTPステータスコード
  response.headers              - HTTPヘッダー
  response.text                 - ページのHTMLテキスト
  response.body                 - ページのバイナリデータ

データ抽出:
  response.css('selector')      - CSSセレクターで要素を選択
  response.xpath('xpath')       - XPathで要素を選択
  response.css('selector::text').get()     - テキストを取得
  response.css('selector::attr(href)').get() - 属性を取得
  response.css('selector').getall()        - 全ての要素を取得

セレクター操作:
  sel = response.css('div')     - セレクターオブジェクトを作成
  sel.css('a::text').getall()  - ネストした選択

その他:
  clear                         - ターミナルをクリア
  history                       - コマンド履歴を表示
  exit                          - シェルを終了`;
    }

    if (command === 'clear') {
      setCommands([]);
      return '';
    }

    if (command === 'history') {
      return commandHistory.map((cmd, index) => `${index + 1}: ${cmd}`).join('\n');
    }

    if (command === 'exit') {
      onClose();
      return 'Scrapy Shell を終了しました。';
    }

    if (command.startsWith('fetch(')) {
      const urlMatch = command.match(/fetch\(['"]([^'"]+)['"]\)/);
      if (urlMatch) {
        const url = urlMatch[1];
        setShellUrl(url);
        return `[s] Available Scrapy objects:
[s]   scrapy     scrapy module (contains scrapy.Request, scrapy.Selector, etc)
[s]   crawler    <scrapy.crawler.Crawler object at 0x...>
[s]   item       {}
[s]   request    <GET ${url}>
[s]   response   <200 ${url}>
[s]   settings   <scrapy.settings.Settings object at 0x...>
[s]   spider     <DefaultSpider 'default' at 0x...>
[s] Useful shortcuts:
[s]   fetch(url[, redirect=True]) Fetch URL and update local objects
[s]   view(response)              View response in a browser

✅ Page fetched successfully with HTTP requests`;
      }
    }

    if (command.startsWith('pw_fetch(')) {
      const urlMatch = command.match(/pw_fetch\(['"]([^'"]+)['"]\)/);
      if (urlMatch) {
        const url = urlMatch[1];
        setShellUrl(url);
        return `[s] Available Scrapy objects:
[s]   scrapy     scrapy module (contains scrapy.Request, scrapy.Selector, etc)
[s]   crawler    <scrapy.crawler.Crawler object at 0x...>
[s]   item       {}
[s]   request    <GET ${url}>
[s]   response   <200 ${url}>
[s]   settings   <scrapy.settings.Settings object at 0x...>
[s]   spider     <DefaultSpider 'default' at 0x...>
[s] Useful shortcuts:
[s]   fetch(url[, redirect=True]) Fetch URL and update local objects
[s]   view(response)              View response in a browser

✅ Page fetched successfully with Playwright`;
      }
    }

    if (command === 'response.url') {
      return `'${shellUrl}'`;
    }

    if (command === 'response.status') {
      return '200';
    }

    if (command === 'response.headers') {
      return `{'Content-Type': ['text/html; charset=utf-8'], 'Content-Length': ['1256'], 'Server': ['nginx/1.18.0']}`;
    }

    if (command.includes('response.css(')) {
      const selectorMatch = command.match(/response\.css\(['"]([^'"]+)['"]\)/);
      if (selectorMatch) {
        const selector = selectorMatch[1];
        if (command.includes('.get()')) {
          if (selector.includes('title')) {
            return `'Example Domain'`;
          }
          if (selector.includes('::text')) {
            return `'サンプルテキスト'`;
          }
          return `'抽出されたテキスト'`;
        }
        if (command.includes('.getall()')) {
          return `['要素1', '要素2', '要素3']`;
        }
        return `[<Selector xpath='descendant-or-self::${selector}' data='<${selector}>...</${selector}>'>]`;
      }
    }

    if (command.includes('response.xpath(')) {
      const xpathMatch = command.match(/response\.xpath\(['"]([^'"]+)['"]\)/);
      if (xpathMatch) {
        const xpath = xpathMatch[1];
        if (command.includes('.get()')) {
          return `'XPathで抽出されたテキスト'`;
        }
        if (command.includes('.getall()')) {
          return `['XPath要素1', 'XPath要素2']`;
        }
        return `[<Selector xpath='${xpath}' data='<element>...</element>'>]`;
      }
    }

    if (command === 'response.text') {
      return `'<!DOCTYPE html>\\n<html>\\n<head>\\n    <title>Example Domain</title>\\n</head>\\n<body>\\n    <h1>Example Domain</h1>\\n    <p>This domain is for use in illustrative examples...</p>\\n</body>\\n</html>'`;
    }

    if (command.startsWith('view(')) {
      return 'ブラウザでレスポンスを表示しました。';
    }

    // デフォルトレスポンス
    return `コマンド "${command}" を実行しました。\n結果: サンプル出力`;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
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

  const clearTerminal = () => {
    setCommands([]);
  };

  const copyOutput = (output: string) => {
    navigator.clipboard.writeText(output);
  };

  const downloadLog = () => {
    const log = commands.map(cmd =>
      `[${cmd.timestamp.toLocaleString()}] >>> ${cmd.command}\n${cmd.output}\n`
    ).join('\n');

    const blob = new Blob([log], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scrapy-shell-log-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-6xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <Terminal className="w-6 h-6 text-green-400" />
            <h2 className="text-xl font-semibold text-white">Scrapy Shell</h2>
            <span className="text-sm text-gray-400">({shellUrl})</span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="p-2 text-gray-400 hover:text-white rounded-md hover:bg-gray-700"
              title="ヘルプ"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
            <button
              onClick={clearTerminal}
              className="p-2 text-gray-400 hover:text-white rounded-md hover:bg-gray-700"
              title="クリア"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={downloadLog}
              className="p-2 text-gray-400 hover:text-white rounded-md hover:bg-gray-700"
              title="ログダウンロード"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white rounded-md hover:bg-gray-700"
              title="閉じる"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Terminal Content */}
        <div className="flex-1 flex flex-col">
          {/* Main Content Area */}
          <div className="flex-1 flex min-h-0">
            {/* Main Terminal */}
            <div className="flex-1 flex flex-col">
              {/* Terminal Output */}
              <div
                ref={terminalRef}
                className="flex-1 p-4 bg-black text-green-400 font-mono text-sm overflow-y-auto scrollbar-thin scrollbar-track-gray-800 scrollbar-thumb-gray-600 hover:scrollbar-thumb-gray-500"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: '#4B5563 #1F2937'
                }}
              >
                {commands.map((cmd) => (
                  <div key={cmd.id} className="mb-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-blue-400">scrapy&gt;</span>
                      <span className="text-white">{cmd.command}</span>
                      <span className="text-gray-500 text-xs">
                        [{cmd.timestamp.toLocaleTimeString()}]
                      </span>
                      {cmd.status === 'running' && (
                        <div className="animate-spin w-3 h-3 border border-green-400 border-t-transparent rounded-full"></div>
                      )}
                      {cmd.output && (
                        <button
                          onClick={() => copyOutput(cmd.output)}
                          className="p-1 text-gray-500 hover:text-gray-300"
                          title="コピー"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                    {cmd.output && (
                      <pre className={`whitespace-pre-wrap ml-4 ${
                        cmd.status === 'error' ? 'text-red-400' : 'text-green-300'
                      }`}>
                        {cmd.output}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Help Panel */}
            {showHelp && (
              <div className="w-80 border-l border-gray-700 bg-gray-800 p-4 overflow-y-auto scrollbar-thin scrollbar-track-gray-700 scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: '#6B7280 #374151'
                }}
              >
                <h3 className="text-lg font-semibold text-white mb-4">クイックヘルプ</h3>

                <div className="space-y-4 text-sm">
                  <div>
                    <h4 className="font-medium text-blue-400 mb-2">基本コマンド</h4>
                    <div className="space-y-1 text-gray-300">
                      <div><code className="text-green-400">fetch('url')</code> - ページ取得（HTTP）</div>
                      <div><code className="text-green-400">pw_fetch('url')</code> - ページ取得（Playwright）</div>
                      <div><code className="text-green-400">view(response)</code> - ブラウザ表示</div>
                      <div><code className="text-green-400">help</code> - ヘルプ表示</div>
                      <div><code className="text-green-400">clear</code> - 画面クリア</div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-blue-400 mb-2">データ抽出</h4>
                    <div className="space-y-1 text-gray-300">
                      <div><code className="text-green-400">response.css('title::text').get()</code></div>
                      <div><code className="text-green-400">response.xpath('//title/text()').get()</code></div>
                      <div><code className="text-green-400">response.css('a::attr(href)').getall()</code></div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-blue-400 mb-2">レスポンス情報</h4>
                    <div className="space-y-1 text-gray-300">
                      <div><code className="text-green-400">response.url</code> - URL</div>
                      <div><code className="text-green-400">response.status</code> - ステータス</div>
                      <div><code className="text-green-400">response.headers</code> - ヘッダー</div>
                      <div><code className="text-green-400">response.text</code> - HTMLテキスト</div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-blue-400 mb-2">例</h4>
                    <div className="space-y-1 text-gray-300 text-xs">
                      <div>1. <code className="text-green-400">fetch('https://example.com')</code></div>
                      <div>2. <code className="text-green-400">pw_fetch('https://spa-site.com')</code></div>
                      <div>3. <code className="text-green-400">response.css('title::text').get()</code></div>
                      <div>4. <code className="text-green-400">response.css('a').getall()</code></div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-blue-400 mb-2">コマンドの違い</h4>
                    <div className="space-y-1 text-gray-300 text-xs">
                      <div><code className="text-green-400">fetch()</code> - 高速、軽量</div>
                      <div><code className="text-green-400">pw_fetch()</code> - JS実行、SPA対応</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Command Input - Fixed at Bottom */}
          <div className="border-t border-gray-700 bg-gray-800 p-4 flex-shrink-0">
            <div className="flex items-center space-x-2">
              <span className="text-blue-400 font-mono">scrapy&gt;</span>
              <input
                ref={inputRef}
                type="text"
                value={currentCommand}
                onChange={(e) => setCurrentCommand(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isRunning}
                className="flex-1 bg-transparent text-white font-mono outline-none"
                placeholder="コマンドを入力してください..."
              />
              <button
                onClick={() => executeCommand(currentCommand)}
                disabled={isRunning || !currentCommand.trim()}
                className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              ↑↓ でコマンド履歴、Enter で実行、Ctrl+C でキャンセル
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
