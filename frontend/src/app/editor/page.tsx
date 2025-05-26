'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/authStore'
import { ScriptEditor } from '@/components/editor/ScriptEditor'
import TemplateSelector from '@/components/editor/TemplateSelector'
import { ScrapyShell } from '@/components/editor/ScrapyShell'
import {
  FileText,
  FolderOpen,
  Play,
  Square,
  Settings,
  Terminal,
  Eye,
  Code,
  Layers,
  Download,
  FileDown,
  Table,
  History,
  Clock,
  Search,
  Filter,
  FileX,
  Bug,
  Save,
  ChevronDown,
  FileSpreadsheet,
  FileCode
} from 'lucide-react'

interface SpiderFile {
  id: string
  name: string
  content: string
  language: string
  modified: boolean
}

export default function EditorPage() {
  const router = useRouter()
  const { isAuthenticated, isInitialized, initialize } = useAuthStore()
  const [files, setFiles] = useState<SpiderFile[]>([
    {
      id: '1',
      name: 'example_spider.py',
      content: `import scrapy

class ExampleSpider(scrapy.Spider):
    name = 'example'
    start_urls = ['https://httpbin.org/json']

    def parse(self, response):
        debug_print(f"Parsing response from {response.url}")

        # レスポンスの基本情報を取得
        debug_print(f"Status code: {response.status}")
        debug_print(f"Content type: {response.headers.get('content-type', b'').decode()}")

        # JSONレスポンスの場合
        if 'json' in response.headers.get('content-type', b'').decode().lower():
            try:
                json_data = response.json()
                debug_print("JSON data received:")
                debug_pprint(json_data)

                yield {
                    'url': response.url,
                    'status': response.status,
                    'content_type': response.headers.get('content-type', b'').decode(),
                    'data': json_data
                }
            except Exception as e:
                debug_print(f"Error parsing JSON: {e}")
                yield {
                    'url': response.url,
                    'status': response.status,
                    'error': str(e)
                }
        else:
            # HTMLレスポンスの場合
            title = response.css('title::text').get()
            debug_print(f"Extracted title: {title}")

            # 基本的なデータを抽出
            data = {
                'url': response.url,
                'status': response.status,
                'title': title,
                'content_length': len(response.text)
            }

            debug_print("Yielding extracted data:")
            debug_pprint(data)

            yield data
`,
      language: 'python',
      modified: false
    }
  ])

  const [activeFileId, setActiveFileId] = useState<string>('1')
  const [showTemplateSelector, setShowTemplateSelector] = useState(false)
  const [showNewSpiderDialog, setShowNewSpiderDialog] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [showTerminal, setShowTerminal] = useState(false)
  const [terminalOutput, setTerminalOutput] = useState<string[]>([])
  const [showScrapyShell, setShowScrapyShell] = useState(false)
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [showResults, setShowResults] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [executionHistory, setExecutionHistory] = useState<any[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [dataFilter, setDataFilter] = useState('')
  const [showFilter, setShowFilter] = useState(false)
  const [showDebug, setShowDebug] = useState(false)
  const [debugOutput, setDebugOutput] = useState<string[]>([])
  const [savedScripts, setSavedScripts] = useState<Array<{ name: string; size: number; modified: string; path: string }>>([])
  const [showSavedScripts, setShowSavedScripts] = useState(false)
  const [showExportDropdown, setShowExportDropdown] = useState(false)

  // 中央パネルのタブ管理
  const [activeTab, setActiveTab] = useState<'debug' | 'terminal' | 'history' | 'results'>('terminal')

  const activeFile = files.find(file => file.id === activeFileId)

  // 認証状態を初期化
  useEffect(() => {
    initialize()
  }, [initialize])

  // 認証状態をチェックしてリダイレクト
  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      console.log('❌ Not authenticated, redirecting to login')
      router.push('/login?redirect=/editor')
    }
  }, [isInitialized, isAuthenticated, router])

  // エクスポートドロップダウンの外側クリックで閉じる
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showExportDropdown) {
        const target = event.target as Element
        if (!target.closest('.relative')) {
          setShowExportDropdown(false)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showExportDropdown])

  const handleFileChange = (content: string) => {
    setFiles(files.map(file =>
      file.id === activeFileId
        ? { ...file, content, modified: true }
        : file
    ))
  }

  const handleSave = async () => {
    if (!activeFile) return

    try {
      addTerminalOutput(`💾 Saving ${activeFile.name}...`)

      const { apiClient } = await import('@/lib/api')
      const result = await apiClient.saveScript(activeFile.name, activeFile.content)

      setFiles(files.map(file =>
        file.id === activeFileId
          ? { ...file, modified: false }
          : file
      ))

      addTerminalOutput(`✅ Saved ${result.file_name} successfully`)

      // 保存済みスクリプト一覧を更新
      if (showSavedScripts) {
        loadSavedScripts()
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      // 認証エラーの場合は特別な処理
      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        addTerminalOutput(`❌ Failed to save ${activeFile.name}: ${errorMessage}`)
      }

      console.error('Save error:', error)
    }
  }

  const loadSavedScripts = async () => {
    try {
      const { apiClient } = await import('@/lib/api')
      const response = await apiClient.getUserScripts()
      setSavedScripts(response.files)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        console.error('Failed to load saved scripts:', error)
        addTerminalOutput(`❌ Failed to load saved scripts: ${errorMessage}`)
      }
    }
  }

  const loadSavedScript = async (fileName: string) => {
    try {
      addTerminalOutput(`📂 Loading ${fileName}...`)

      const { apiClient } = await import('@/lib/api')
      const response = await apiClient.getScriptContent(fileName)

      // 新しいファイルとして追加
      const newFile: SpiderFile = {
        id: Date.now().toString(),
        name: response.file_name,
        content: response.content,
        language: 'python',
        modified: false
      }

      setFiles([...files, newFile])
      setActiveFileId(newFile.id)

      addTerminalOutput(`✅ Loaded ${fileName} successfully`)
      setShowSavedScripts(false)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        addTerminalOutput(`❌ Failed to load ${fileName}: ${errorMessage}`)
      }

      console.error('Load script error:', error)
    }
  }

  const toggleSavedScripts = () => {
    setShowSavedScripts(!showSavedScripts)
    if (!showSavedScripts && savedScripts.length === 0) {
      loadSavedScripts()
    }
  }

  const handleTest = async () => {
    if (!activeFile || isRunning) return

    setIsRunning(true)
    setActiveTab('terminal')
    setShowResults(false)
    setExecutionResult(null)
    addTerminalOutput(`🧪 Quick testing ${activeFile.name}...`)

    try {
      const { apiClient } = await import('@/lib/api')

      // スパイダー名を抽出（ファイル名から.pyを除去）
      const spiderName = activeFile.name.replace('.py', '')

      // スクリプトからstart_urlsを抽出（簡単な正規表現）
      const urlsMatch = activeFile.content.match(/start_urls\s*=\s*\[(.*?)\]/s)
      let startUrls = ['https://example.com']

      if (urlsMatch) {
        try {
          const urlsStr = urlsMatch[1]
          const urls = urlsStr.match(/'([^']+)'/g) || urlsStr.match(/"([^"]+)"/g)
          if (urls) {
            startUrls = urls.map(url => url.replace(/['"]/g, ''))
          }
        } catch (e) {
          console.warn('Failed to parse start_urls, using default')
        }
      }

      addTerminalOutput(`📝 Spider name: ${spiderName}`)
      addTerminalOutput(`🔗 Target URLs: ${startUrls.join(', ')}`)

      const result = await apiClient.testScript({
        script_content: activeFile.content,
        spider_name: spiderName,
        start_urls: startUrls,
        settings: {}
      })

      // 結果を表示
      setExecutionResult(result)
      setShowResults(true)

      addTerminalOutput(`✅ Quick test completed!`)
      result.output.forEach((line: string) => addTerminalOutput(line))

      if (result.errors.length > 0) {
        result.errors.forEach(error => addTerminalOutput(`❌ Error: ${error}`))
      }

      if (result.extracted_data.length > 0) {
        addTerminalOutput(`📊 ${result.extracted_data.length} test items extracted`)
        setActiveTab('results')
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      // 認証エラーの場合は特別な処理
      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        addTerminalOutput(`❌ Quick test failed: ${errorMessage}`)
      }

      console.error('Script test error:', error)
    } finally {
      setIsRunning(false)
    }
  }

  const handleRun = async () => {
    if (!activeFile || isRunning) return

    setIsRunning(true)
    setActiveTab('terminal')
    setShowResults(false)
    setExecutionResult(null)
    addTerminalOutput(`▶ Running ${activeFile.name}...`)

    try {
      const { apiClient } = await import('@/lib/api')

      // スパイダー名を抽出（ファイル名から.pyを除去）
      const spiderName = activeFile.name.replace('.py', '')

      // スクリプトからstart_urlsを抽出（簡単な正規表現）
      const urlsMatch = activeFile.content.match(/start_urls\s*=\s*\[(.*?)\]/s)
      let startUrls = ['https://example.com']

      if (urlsMatch) {
        try {
          const urlsStr = urlsMatch[1]
          const urls = urlsStr.match(/'([^']+)'/g) || urlsStr.match(/"([^"]+)"/g)
          if (urls) {
            startUrls = urls.map(url => url.replace(/['"]/g, ''))
          }
        } catch (e) {
          console.warn('Failed to parse start_urls, using default')
        }
      }

      addTerminalOutput(`📡 Executing spider: ${spiderName}`)
      addTerminalOutput(`🌐 Target URLs: ${startUrls.join(', ')}`)

      const result = await apiClient.executeScript({
        script_content: activeFile.content,
        spider_name: spiderName,
        start_urls: startUrls,
        settings: {}
      })

      // 結果を表示
      setExecutionResult(result)
      setShowResults(true)

      // デバッグ出力を分離
      const debugLines = result.output.filter((line: string) => line.includes('🐛 ['))
      const regularLines = result.output.filter((line: string) => !line.includes('🐛 ['))

      setDebugOutput(debugLines)

      // 結果に応じてタブを切り替え
      if (result.extracted_data.length > 0) {
        setActiveTab('results')
      } else if (debugLines.length > 0) {
        setActiveTab('debug')
      }

      // ターミナル出力を更新（デバッグ出力以外）
      regularLines.forEach((line: string) => addTerminalOutput(line))

      if (result.errors.length > 0) {
        result.errors.forEach(error => addTerminalOutput(`❌ ${error}`))
      }

      if (result.extracted_data.length > 0) {
        addTerminalOutput(`✅ Execution completed successfully`)
        addTerminalOutput(`📊 Extracted ${result.extracted_data.length} items`)
        addTerminalOutput(`⏱️ Execution time: ${result.execution_time.toFixed(2)}s`)
      } else {
        addTerminalOutput(`⚠️ No data extracted`)
      }

      // 実行履歴を更新
      if (showHistory) {
        loadExecutionHistory()
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      // 認証エラーの場合は特別な処理
      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        addTerminalOutput(`❌ Execution failed: ${errorMessage}`)
      }

      console.error('Script execution error:', error)
    } finally {
      setIsRunning(false)
    }
  }

  const handleStop = () => {
    setIsRunning(false)
    addTerminalOutput('⏹ Execution stopped')
  }

  const addTerminalOutput = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setTerminalOutput(prev => [...prev, `[${timestamp}] ${message}`])
  }

  const handleTemplateSelect = (template: any) => {
    const newFile: SpiderFile = {
      id: Date.now().toString(),
      name: `${template.name.toLowerCase().replace(/\s+/g, '_')}.py`,
      content: template.code,
      language: 'python',
      modified: true
    }

    setFiles([...files, newFile])
    setActiveFileId(newFile.id)
    setShowTemplateSelector(false)
  }

  const createNewFile = () => {
    setShowNewSpiderDialog(true)
  }

  const handleNewSpiderFromTemplate = () => {
    setShowNewSpiderDialog(false)
    setShowTemplateSelector(true)
  }

  const handleNewBasicSpider = () => {
    setShowNewSpiderDialog(false)
    const newFile: SpiderFile = {
      id: Date.now().toString(),
      name: 'new_spider.py',
      content: `import scrapy
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class NewSpider(scrapy.Spider):
    name = 'new_spider'
    start_urls = ['https://example.com']

    def parse(self, response):
        debug_print(f"Parsing response from {response.url}")

        # 基本的なデータを抽出
        data = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'h1_count': len(response.css('h1').getall()),
            'links_count': len(response.css('a::attr(href)').getall())
        }

        debug_print("Extracted data:")
        debug_pprint(data)

        yield data
`,
      language: 'python',
      modified: true
    }

    setFiles([...files, newFile])
    setActiveFileId(newFile.id)
  }

  const handleExport = async (format: 'json' | 'csv' | 'excel' | 'xml') => {
    if (!executionResult?.execution_id) return

    setShowExportDropdown(false) // ドロップダウンを閉じる

    try {
      const { apiClient } = await import('@/lib/api')
      await apiClient.exportExecutionData(executionResult.execution_id, format)
      addTerminalOutput(`✅ Data exported as ${format.toUpperCase()}`)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        addTerminalOutput(`❌ Export failed: ${errorMessage}`)
      }

      console.error('Export error:', error)
    }
  }

  const loadExecutionHistory = async () => {
    if (loadingHistory) return

    setLoadingHistory(true)
    try {
      const { apiClient } = await import('@/lib/api')
      const response = await apiClient.getExecutionHistory(20)
      setExecutionHistory(response.history)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)

      if (errorMessage.includes('Not authenticated') || errorMessage.includes('Unauthorized')) {
        addTerminalOutput(`❌ Authentication failed. Please log in again.`)
        localStorage.removeItem('token')
        router.push('/login?redirect=/editor')
      } else {
        console.error('Failed to load execution history:', error)
        addTerminalOutput(`❌ Failed to load execution history: ${errorMessage}`)
      }
    } finally {
      setLoadingHistory(false)
    }
  }

  const toggleHistory = () => {
    setShowHistory(!showHistory)
    if (!showHistory && executionHistory.length === 0) {
      loadExecutionHistory()
    }
  }

  const filteredData = executionResult?.extracted_data?.filter((item: any) => {
    if (!dataFilter) return true

    const searchText = dataFilter.toLowerCase()
    const itemString = JSON.stringify(item).toLowerCase()
    return itemString.includes(searchText)
  }) || []

  // 初期化中または認証されていない場合はローディング表示
  if (!isInitialized || !isAuthenticated) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">
            {!isInitialized ? 'Initializing...' : 'Checking authentication...'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* ヘッダー */}
      <div className="h-14 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold text-white flex items-center space-x-2">
            <Code className="w-5 h-5" />
            <span>Script Editor</span>
          </h1>

          <div className="flex items-center space-x-2">
            <button
              onClick={createNewFile}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
            >
              New Spider
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowScrapyShell(true)}
            className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors flex items-center space-x-2"
            title="Open Scrapy Shell"
          >
            <Terminal className="w-4 h-4" />
            <span>Scrapy Shell</span>
          </button>

          <button
            onClick={toggleSavedScripts}
            className={`p-2 rounded transition-colors ${
              showSavedScripts
                ? 'bg-yellow-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
            title="Saved Scripts"
          >
            <Save className="w-4 h-4" />
          </button>

          <button
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* 左パネル - ファイル管理 */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          <div className="p-3 border-b border-gray-700">
            <h2 className="text-sm font-medium text-gray-300 flex items-center space-x-2">
              <FolderOpen className="w-4 h-4" />
              <span>Files</span>
            </h2>
          </div>

          <div className="p-2 flex-1 overflow-y-auto">
            {files.map(file => (
              <div
                key={file.id}
                onClick={() => setActiveFileId(file.id)}
                className={`flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors ${
                  file.id === activeFileId
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span className="text-sm truncate">{file.name}</span>
                {file.modified && (
                  <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                )}
              </div>
            ))}
          </div>

          {/* 保存済みスクリプトパネル */}
          {showSavedScripts && (
            <div className="border-t border-gray-700 max-h-80 flex flex-col">
              <div className="p-3 border-b border-gray-700">
                <h3 className="text-sm font-medium text-gray-300 flex items-center space-x-2">
                  <Save className="w-4 h-4" />
                  <span>Saved Scripts</span>
                  {savedScripts.length > 0 && (
                    <span className="text-xs bg-yellow-600 text-white px-2 py-0.5 rounded">
                      {savedScripts.length}
                    </span>
                  )}
                </h3>
              </div>

              <div className="flex-1 overflow-y-auto">
                {savedScripts.length > 0 ? (
                  <div className="p-2 space-y-2">
                    {savedScripts.map((script, index) => (
                      <div
                        key={script.name}
                        className="p-2 bg-gray-700 rounded text-xs hover:bg-gray-600 transition-colors cursor-pointer"
                        onClick={() => loadSavedScript(script.name)}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-gray-300 font-medium truncate">
                            {script.name}
                          </span>
                          <span className="text-xs text-gray-500">
                            {Math.round(script.size / 1024)}KB
                          </span>
                        </div>
                        <div className="text-gray-400">
                          <div className="text-xs">
                            {new Date(script.modified).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-center text-gray-500">
                    <Save className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs">No saved scripts</p>
                    <p className="text-xs mt-1">Save your scripts to see them here</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 実行履歴パネル */}
          {showHistory && (
            <div className="border-t border-gray-700 max-h-80 flex flex-col">
              <div className="p-3 border-b border-gray-700">
                <h3 className="text-sm font-medium text-gray-300 flex items-center space-x-2">
                  <History className="w-4 h-4" />
                  <span>Execution History</span>
                  {loadingHistory && (
                    <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                  )}
                </h3>
              </div>

              <div className="flex-1 overflow-y-auto">
                {executionHistory.length > 0 ? (
                  <div className="p-2 space-y-2">
                    {executionHistory.map((execution, index) => (
                      <div
                        key={execution.execution_id}
                        className="p-2 bg-gray-700 rounded text-xs hover:bg-gray-600 transition-colors cursor-pointer"
                        onClick={() => {
                          // 履歴から実行結果を復元
                          setExecutionResult({
                            execution_id: execution.execution_id,
                            status: execution.status,
                            extracted_data: [],
                            execution_time: execution.execution_time,
                            started_at: execution.started_at,
                            finished_at: execution.finished_at,
                            output: [],
                            errors: []
                          })
                          setShowResults(true)
                        }}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-gray-300 font-medium truncate">
                            {execution.spider_name}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded text-xs ${
                            execution.status === 'completed'
                              ? 'bg-green-600 text-white'
                              : 'bg-red-600 text-white'
                          }`}>
                            {execution.status}
                          </span>
                        </div>
                        <div className="text-gray-400 space-y-1">
                          <div className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{execution.execution_time.toFixed(2)}s</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Eye className="w-3 h-3" />
                            <span>{execution.extracted_count} items</span>
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(execution.started_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-center text-gray-500">
                    <History className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs">No execution history</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 中央パネル - タブ切り替え */}
        <div className="w-96 bg-gray-900 border-r border-gray-700 flex flex-col">
          {/* タブヘッダー */}
          <div className="h-10 bg-gray-800 border-b border-gray-700 flex">
            <button
              onClick={() => setActiveTab('terminal')}
              className={`flex-1 flex items-center justify-center space-x-2 text-sm transition-colors ${
                activeTab === 'terminal'
                  ? 'bg-gray-700 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>Terminal</span>
            </button>
            <button
              onClick={() => setActiveTab('debug')}
              className={`flex-1 flex items-center justify-center space-x-2 text-sm transition-colors ${
                activeTab === 'debug'
                  ? 'bg-gray-700 text-white border-b-2 border-red-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Bug className="w-4 h-4" />
              <span>Debug</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 flex items-center justify-center space-x-2 text-sm transition-colors ${
                activeTab === 'history'
                  ? 'bg-gray-700 text-white border-b-2 border-orange-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <History className="w-4 h-4" />
              <span>History</span>
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`flex-1 flex items-center justify-center space-x-2 text-sm transition-colors ${
                activeTab === 'results'
                  ? 'bg-gray-700 text-white border-b-2 border-purple-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Eye className="w-4 h-4" />
              <span>Results</span>
            </button>
          </div>

          {/* タブコンテンツ */}
          <div className="flex-1 overflow-hidden">
            {/* ターミナルタブ */}
            {activeTab === 'terminal' && (
              <div className="h-full bg-black">
                <div className="h-8 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
                  <div className="flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-300">Terminal Output</span>
                  </div>
                  <button
                    onClick={() => setTerminalOutput([])}
                    className="text-xs text-gray-400 hover:text-white"
                  >
                    Clear
                  </button>
                </div>
                <div className="p-4 h-full overflow-y-auto font-mono text-sm">
                  {terminalOutput.map((line, index) => (
                    <div key={index} className="text-green-400 mb-1">
                      {line}
                    </div>
                  ))}
                  {isRunning && (
                    <div className="text-yellow-400 animate-pulse">
                      Running...
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* デバッグタブ */}
            {activeTab === 'debug' && (
              <div className="h-full bg-gray-900">
                <div className="h-8 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
                  <div className="flex items-center space-x-2">
                    <Bug className="w-4 h-4 text-red-400" />
                    <span className="text-sm text-gray-300">Debug Output</span>
                    {debugOutput.length > 0 && (
                      <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded">
                        {debugOutput.length}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setDebugOutput([])}
                    className="text-xs text-gray-400 hover:text-white"
                  >
                    Clear
                  </button>
                </div>
                <div className="p-4 h-full overflow-y-auto font-mono text-sm">
                  {debugOutput.length > 0 ? (
                    debugOutput.map((line, index) => (
                      <div key={index} className="mb-2 p-2 bg-gray-800 rounded border-l-4 border-red-500">
                        <div className="text-red-400 text-xs mb-1">
                          {line.includes('[PRINT]') ? '🖨️ PRINT' : line.includes('[PPRINT]') ? '📋 PPRINT' : '🐛 DEBUG'}
                        </div>
                        <div className="text-gray-300">
                          {line.replace(/🐛 \[(PRINT|PPRINT|DEBUG)\] \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+: /, '')}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <Bug className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No debug output yet</p>
                        <p className="text-sm mt-2">Add debug statements:</p>
                        <div className="mt-4 text-left bg-gray-800 p-3 rounded">
                          <div className="text-green-400 text-sm">
                            <div>debug_print("Hello!")</div>
                            <div>debug_pprint(data)</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 履歴タブ */}
            {activeTab === 'history' && (
              <div className="h-full bg-gray-900">
                <div className="h-8 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
                  <div className="flex items-center space-x-2">
                    <History className="w-4 h-4 text-orange-400" />
                    <span className="text-sm text-gray-300">Execution History</span>
                    {loadingHistory && (
                      <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                    )}
                  </div>
                  <button
                    onClick={() => loadExecutionHistory()}
                    className="text-xs text-gray-400 hover:text-white"
                  >
                    Refresh
                  </button>
                </div>
                <div className="p-4 h-full overflow-y-auto">
                  {executionHistory.length > 0 ? (
                    <div className="space-y-2">
                      {executionHistory.map((execution, index) => (
                        <div
                          key={execution.execution_id}
                          className="p-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors cursor-pointer"
                          onClick={() => {
                            setExecutionResult({
                              execution_id: execution.execution_id,
                              status: execution.status,
                              extracted_data: [],
                              execution_time: execution.execution_time,
                              started_at: execution.started_at,
                              finished_at: execution.finished_at,
                              output: [],
                              errors: []
                            })
                            setActiveTab('results')
                          }}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-300 font-medium truncate">
                              {execution.spider_name}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              execution.status === 'completed'
                                ? 'bg-green-600 text-white'
                                : 'bg-red-600 text-white'
                            }`}>
                              {execution.status}
                            </span>
                          </div>
                          <div className="text-gray-400 text-sm space-y-1">
                            <div className="flex items-center space-x-2">
                              <Clock className="w-3 h-3" />
                              <span>{execution.execution_time.toFixed(2)}s</span>
                              <Eye className="w-3 h-3" />
                              <span>{execution.extracted_count} items</span>
                            </div>
                            <div className="text-xs text-gray-500">
                              {new Date(execution.started_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No execution history</p>
                        <button
                          onClick={() => loadExecutionHistory()}
                          className="mt-2 px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors"
                        >
                          Load History
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 結果タブ */}
            {activeTab === 'results' && (
              <div className="h-full bg-gray-900 flex flex-col">
                <div className="h-8 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
                  <div className="flex items-center space-x-2">
                    <Eye className="w-4 h-4 text-purple-400" />
                    <span className="text-sm text-gray-300">Extracted Data</span>
                    {executionResult && (
                      <span className="text-xs bg-purple-600 text-white px-2 py-0.5 rounded">
                        {filteredData.length}/{executionResult.extracted_data.length} items
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-1">
                    {executionResult && executionResult.extracted_data.length > 0 && (
                      <>
                        <button
                          onClick={() => setShowFilter(!showFilter)}
                          className={`p-1 rounded transition-colors ${
                            showFilter
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-400 hover:text-white hover:bg-gray-700'
                          }`}
                          title="Filter Data"
                        >
                          <Search className="w-3 h-3" />
                        </button>
                        <div className="relative">
                          <button
                            onClick={() => setShowExportDropdown(!showExportDropdown)}
                            className="flex items-center space-x-1 p-1 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
                            title="Export Data"
                          >
                            <FileDown className="w-3 h-3" />
                            <ChevronDown className="w-3 h-3" />
                          </button>
                          {showExportDropdown && (
                            <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-600 rounded shadow-lg z-50 min-w-32">
                              <button
                                onClick={() => handleExport('json')}
                                className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                              >
                                <FileCode className="w-4 h-4" />
                                <span>JSON</span>
                              </button>
                              <button
                                onClick={() => handleExport('csv')}
                                className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                              >
                                <Table className="w-4 h-4" />
                                <span>CSV</span>
                              </button>
                              <button
                                onClick={() => handleExport('excel')}
                                className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                              >
                                <FileSpreadsheet className="w-4 h-4" />
                                <span>Excel</span>
                              </button>
                              <button
                                onClick={() => handleExport('xml')}
                                className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                              >
                                <FileText className="w-4 h-4" />
                                <span>XML</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* フィルター */}
                {showFilter && executionResult && executionResult.extracted_data.length > 0 && (
                  <div className="p-3 border-b border-gray-700 bg-gray-800">
                    <div className="flex items-center space-x-2">
                      <Search className="w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search in data..."
                        value={dataFilter}
                        onChange={(e) => setDataFilter(e.target.value)}
                        className="flex-1 bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                      />
                    </div>
                  </div>
                )}

                {/* データ表示 */}
                <div className="flex-1 p-4 overflow-y-auto">
                  {executionResult && executionResult.extracted_data.length > 0 ? (
                    filteredData.length > 0 ? (
                      <div className="space-y-3">
                        {filteredData.map((item: any, index: number) => (
                          <div key={index} className="bg-gray-800 rounded p-3 border border-gray-700">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-purple-400">Item #{index + 1}</span>
                              <span className="text-xs text-gray-500">
                                {Object.keys(item).length} fields
                              </span>
                            </div>
                            <pre className="text-xs text-gray-300 overflow-x-auto">
                              {JSON.stringify(item, null, 2)}
                            </pre>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        <div className="text-center">
                          <Filter className="w-12 h-12 mx-auto mb-4 opacity-50" />
                          <p>No items match the filter</p>
                        </div>
                      </div>
                    )
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No data extracted yet</p>
                        <p className="text-sm">Run a spider to see results</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 右パネル - スクリプトエディター */}
        <div className="flex-1 flex flex-col">
          {/* タブバー */}
          <div className="h-10 bg-gray-800 border-b border-gray-700 flex items-center px-4">
            {activeFile && (
              <div className="flex items-center space-x-2 text-sm text-gray-300">
                <FileText className="w-4 h-4" />
                <span>{activeFile.name}</span>
                {activeFile.modified && (
                  <div className="w-1.5 h-1.5 bg-orange-500 rounded-full"></div>
                )}
              </div>
            )}
          </div>

          {/* エディタ */}
          <div className="flex-1">
            {activeFile ? (
              <ScriptEditor
                value={activeFile.content}
                onChange={handleFileChange}
                language={activeFile.language}
                fileName={activeFile.name}
                onSave={handleSave}
                onTest={isRunning ? undefined : handleTest}
                onRun={isRunning ? handleStop : handleRun}
              />
            ) : (
              <div className="flex items-center justify-center h-full bg-gray-900 text-gray-400">
                <div className="text-center">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No file selected</p>
                  <button
                    onClick={createNewFile}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                  >
                    Create New Spider
                  </button>
                </div>
              </div>
            )}
          </div>


        </div>
      </div>

      {/* 新しいスパイダー作成ダイアログ */}
      {showNewSpiderDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">新しいスパイダーを作成</h3>
              <p className="text-gray-400 mb-6">どの方法でスパイダーを作成しますか？</p>

              <div className="space-y-3">
                <button
                  onClick={handleNewBasicSpider}
                  className="w-full p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
                >
                  <div className="flex items-center space-x-3">
                    <Code className="w-5 h-5 text-blue-400" />
                    <div>
                      <div className="text-white font-medium">基本スパイダー</div>
                      <div className="text-gray-400 text-sm">シンプルなスパイダーをすぐに作成</div>
                    </div>
                  </div>
                </button>

                <button
                  onClick={handleNewSpiderFromTemplate}
                  className="w-full p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
                >
                  <div className="flex items-center space-x-3">
                    <Layers className="w-5 h-5 text-purple-400" />
                    <div>
                      <div className="text-white font-medium">テンプレートから作成</div>
                      <div className="text-gray-400 text-sm">豊富なテンプレートから選択</div>
                    </div>
                  </div>
                </button>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowNewSpiderDialog(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  キャンセル
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* テンプレートセレクター */}
      <TemplateSelector
        isOpen={showTemplateSelector}
        onSelectTemplate={handleTemplateSelect}
        onClose={() => setShowTemplateSelector(false)}
      />

      {/* Scrapy Shell */}
      <ScrapyShell
        isOpen={showScrapyShell}
        onClose={() => setShowScrapyShell(false)}
      />
    </div>
  )
}
