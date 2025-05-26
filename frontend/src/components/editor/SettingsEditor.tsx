'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';
import { Save, RotateCcw, Check, X, AlertCircle } from 'lucide-react';

interface SettingsEditorProps {
  value: any;
  onChange: (value: any) => void;
  onSave: () => void;
  onCancel: () => void;
  isEditing: boolean;
  isSaving: boolean;
  readOnly?: boolean;
}

export default function SettingsEditor({
  value,
  onChange,
  onSave,
  onCancel,
  isEditing,
  isSaving,
  readOnly = false
}: SettingsEditorProps) {
  const [editorValue, setEditorValue] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const editorRef = useRef<any>(null);

  useEffect(() => {
    try {
      const jsonString = JSON.stringify(value, null, 2);
      setEditorValue(jsonString);
      setIsValid(true);
      setError(null);
    } catch (err) {
      setError('設定の読み込みに失敗しました');
      setIsValid(false);
    }
  }, [value]);

  const handleEditorChange = (newValue: string | undefined) => {
    if (newValue === undefined) return;
    
    setEditorValue(newValue);
    
    try {
      const parsed = JSON.parse(newValue);
      onChange(parsed);
      setIsValid(true);
      setError(null);
    } catch (err) {
      setIsValid(false);
      setError('無効なJSON形式です');
    }
  };

  const handleEditorMount = (editor: any, monaco: any) => {
    editorRef.current = editor;
    
    // Monaco Editorのテーマ設定
    monaco.editor.defineTheme('scrapy-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955' },
        { token: 'keyword', foreground: '569CD6' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: 'B5CEA8' },
        { token: 'regexp', foreground: 'D16969' },
        { token: 'type', foreground: '4EC9B0' },
        { token: 'class', foreground: '4EC9B0' },
        { token: 'function', foreground: 'DCDCAA' },
        { token: 'variable', foreground: '9CDCFE' },
        { token: 'constant', foreground: '4FC1FF' },
      ],
      colors: {
        'editor.background': '#1F2937',
        'editor.foreground': '#F3F4F6',
        'editorLineNumber.foreground': '#6B7280',
        'editorLineNumber.activeForeground': '#9CA3AF',
        'editor.selectionBackground': '#374151',
        'editor.inactiveSelectionBackground': '#374151',
        'editorCursor.foreground': '#F3F4F6',
        'editor.findMatchBackground': '#42A5F5',
        'editor.findMatchHighlightBackground': '#42A5F5',
        'editorWidget.background': '#374151',
        'editorWidget.border': '#4B5563',
        'editorSuggestWidget.background': '#374151',
        'editorSuggestWidget.border': '#4B5563',
        'editorSuggestWidget.foreground': '#F3F4F6',
        'editorSuggestWidget.selectedBackground': '#4B5563',
      }
    });
    
    monaco.editor.setTheme('scrapy-dark');
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(editorValue);
      const formatted = JSON.stringify(parsed, null, 2);
      setEditorValue(formatted);
      onChange(parsed);
      setIsValid(true);
      setError(null);
    } catch (err) {
      setError('JSONの整形に失敗しました');
    }
  };

  const resetToOriginal = () => {
    try {
      const jsonString = JSON.stringify(value, null, 2);
      setEditorValue(jsonString);
      setIsValid(true);
      setError(null);
    } catch (err) {
      setError('元の値の復元に失敗しました');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-semibold text-blue-400">プロジェクト設定</h3>
          {!isValid && (
            <div className="flex items-center space-x-1 text-red-400">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">無効なJSON</span>
            </div>
          )}
          {isValid && isEditing && (
            <div className="flex items-center space-x-1 text-green-400">
              <Check className="h-4 w-4" />
              <span className="text-sm">有効なJSON</span>
            </div>
          )}
        </div>
        
        {isEditing && (
          <div className="flex items-center space-x-2">
            <button
              onClick={formatJson}
              className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-500 transition-colors"
              title="JSONを整形"
            >
              整形
            </button>
            <button
              onClick={resetToOriginal}
              className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-500 transition-colors"
              title="元に戻す"
            >
              <RotateCcw className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/50 rounded-md p-3">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-red-400" />
            <span className="text-sm text-red-300">{error}</span>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="border border-gray-600 rounded-md overflow-hidden">
        <Editor
          height="400px"
          language="json"
          value={editorValue}
          onChange={handleEditorChange}
          onMount={handleEditorMount}
          options={{
            readOnly: !isEditing || readOnly,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineNumbers: 'on',
            renderWhitespace: 'selection',
            automaticLayout: true,
            wordWrap: 'on',
            formatOnPaste: true,
            formatOnType: true,
            tabSize: 2,
            insertSpaces: true,
            folding: true,
            bracketPairColorization: { enabled: true },
            guides: {
              bracketPairs: true,
              indentation: true
            },
            suggest: {
              showKeywords: true,
              showSnippets: true
            },
            quickSuggestions: {
              other: true,
              comments: false,
              strings: true
            }
          }}
        />
      </div>

      {/* Action Buttons */}
      {isEditing && (
        <div className="flex items-center justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
          >
            キャンセル
          </button>
          <button
            onClick={onSave}
            disabled={!isValid || isSaving}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? '保存中...' : '保存'}</span>
          </button>
        </div>
      )}

      {/* Info */}
      {!isEditing && (
        <div className="text-xs text-gray-400">
          設定を編集するには「編集」ボタンをクリックしてください。
        </div>
      )}
    </div>
  );
}
