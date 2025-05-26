'use client'

import React, { useRef, useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import { Play, Save, FileText, Settings, Bug, Download } from 'lucide-react'

interface ScriptEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  theme?: 'vs-dark' | 'light'
  readOnly?: boolean
  onSave?: () => void
  onRun?: () => void
  onTest?: () => void
  fileName?: string
  className?: string
}

export function ScriptEditor({
  value,
  onChange,
  language = 'python',
  theme = 'vs-dark',
  readOnly = false,
  onSave,
  onRun,
  onTest,
  fileName = 'spider.py',
  className = ''
}: ScriptEditorProps) {
  const editorRef = useRef<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errors, setErrors] = useState<any[]>([])

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor
    setIsLoading(false)

    // Python言語設定の拡張
    if (language === 'python') {
      monaco.languages.setLanguageConfiguration('python', {
        comments: {
          lineComment: '#',
          blockComment: ['"""', '"""']
        },
        brackets: [
          ['{', '}'],
          ['[', ']'],
          ['(', ')']
        ],
        autoClosingPairs: [
          { open: '{', close: '}' },
          { open: '[', close: ']' },
          { open: '(', close: ')' },
          { open: '"', close: '"' },
          { open: "'", close: "'" }
        ],
        surroundingPairs: [
          { open: '{', close: '}' },
          { open: '[', close: ']' },
          { open: '(', close: ')' },
          { open: '"', close: '"' },
          { open: "'", close: "'" }
        ]
      })

      // Scrapy固有のキーワードとクラスの追加
      monaco.languages.registerCompletionItemProvider('python', {
        provideCompletionItems: (model: any, position: any) => {
          const suggestions = [
            {
              label: 'scrapy.Spider',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'scrapy.Spider',
              documentation: 'Base Spider class'
            },
            {
              label: 'start_urls',
              kind: monaco.languages.CompletionItemKind.Property,
              insertText: 'start_urls = []',
              documentation: 'List of URLs to start crawling from'
            },
            {
              label: 'parse',
              kind: monaco.languages.CompletionItemKind.Method,
              insertText: [
                'def parse(self, response):',
                '    """Parse the response and extract data."""',
                '    pass'
              ].join('\n'),
              documentation: 'Default callback method for parsing responses'
            },
            {
              label: 'scrapy.Request',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'scrapy.Request(url, callback=self.parse)',
              documentation: 'Create a new request'
            },
            {
              label: 'response.css',
              kind: monaco.languages.CompletionItemKind.Method,
              insertText: 'response.css("selector")',
              documentation: 'CSS selector for extracting data'
            },
            {
              label: 'response.xpath',
              kind: monaco.languages.CompletionItemKind.Method,
              insertText: 'response.xpath("//xpath")',
              documentation: 'XPath selector for extracting data'
            },
            {
              label: 'yield',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'yield',
              documentation: 'Yield items or requests'
            }
          ]
          return { suggestions }
        }
      })
    }

    // キーボードショートカット
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      onSave?.()
    })

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onRun?.()
    })
  }

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value)
    }
  }

  const formatCode = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument').run()
    }
  }

  const downloadCode = () => {
    const blob = new Blob([value], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className={`flex flex-col h-full bg-gray-900 ${className}`}>
      {/* ツールバー */}
      <div className="flex items-center justify-between p-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-300">{fileName}</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={formatCode}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Format Code (Shift+Alt+F)"
          >
            <Settings className="w-4 h-4" />
          </button>

          <button
            onClick={downloadCode}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4" />
          </button>

          {onSave && (
            <button
              onClick={onSave}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center space-x-1"
              title="Save (Ctrl+S)"
            >
              <Save className="w-4 h-4" />
              <span className="text-sm">Save</span>
            </button>
          )}

          {onTest && (
            <button
              onClick={onTest}
              className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded transition-colors flex items-center space-x-1"
              title="Quick Test"
            >
              <Bug className="w-4 h-4" />
              <span className="text-sm">Test</span>
            </button>
          )}

          {onRun && (
            <button
              onClick={onRun}
              className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors flex items-center space-x-1"
              title="Run (Ctrl+Enter)"
            >
              <Play className="w-4 h-4" />
              <span className="text-sm">Run</span>
            </button>
          )}
        </div>
      </div>

      {/* エディター */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-gray-400">Loading editor...</div>
          </div>
        )}

        <Editor
          height="100%"
          language={language}
          theme={theme}
          value={value}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            readOnly,
            minimap: { enabled: true },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'on',
            folding: true,
            foldingStrategy: 'indentation',
            showFoldingControls: 'always',
            bracketPairColorization: { enabled: true },
            guides: {
              bracketPairs: true,
              indentation: true
            },
            suggest: {
              showKeywords: true,
              showSnippets: true,
              showClasses: true,
              showFunctions: true,
              showVariables: true
            },
            quickSuggestions: {
              other: true,
              comments: false,
              strings: false
            },
            parameterHints: {
              enabled: true
            },
            hover: {
              enabled: true
            }
          }}
        />
      </div>

      {/* エラー表示 */}
      {errors.length > 0 && (
        <div className="p-3 bg-red-900 border-t border-red-700">
          <div className="flex items-center space-x-2 mb-2">
            <Bug className="w-4 h-4 text-red-400" />
            <span className="text-sm text-red-300 font-medium">Errors</span>
          </div>
          <div className="space-y-1">
            {errors.map((error, index) => (
              <div key={index} className="text-sm text-red-200">
                Line {error.line}: {error.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
