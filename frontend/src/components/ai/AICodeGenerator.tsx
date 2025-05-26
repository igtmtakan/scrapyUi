'use client';

import { useState } from 'react';
import { 
  Bot, 
  Code, 
  Wand2, 
  Search, 
  AlertTriangle,
  CheckCircle,
  Copy,
  Download,
  Sparkles
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface CodeSuggestion {
  type: string;
  title: string;
  description: string;
  code: string;
  confidence: number;
  reasoning: string;
  tags: string[];
}

interface BugReport {
  severity: string;
  category: string;
  line_number?: number;
  description: string;
  suggestion: string;
  code_snippet: string;
}

interface AICodeGeneratorProps {
  projectId: string;
}

export default function AICodeGenerator({ projectId }: AICodeGeneratorProps) {
  const [activeTab, setActiveTab] = useState<'generate' | 'analyze' | 'optimize'>('generate');
  const [isLoading, setIsLoading] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<CodeSuggestion | null>(null);
  const [bugs, setBugs] = useState<BugReport[]>([]);
  const [optimizations, setOptimizations] = useState<CodeSuggestion[]>([]);

  // スパイダー生成フォーム
  const [spiderForm, setSpiderForm] = useState({
    spider_name: '',
    target_url: '',
    data_fields: ['title', 'description']
  });

  // コード分析フォーム
  const [codeToAnalyze, setCodeToAnalyze] = useState('');

  const generateSpider = async () => {
    if (!spiderForm.spider_name || !spiderForm.target_url) {
      alert('スパイダー名とターゲットURLを入力してください');
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiClient.request('/api/ai/generate/spider', {
        method: 'POST',
        body: JSON.stringify(spiderForm)
      });

      setGeneratedCode(response.suggestion);
    } catch (error) {
      console.error('Failed to generate spider:', error);
      alert('スパイダーの生成に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeCode = async () => {
    if (!codeToAnalyze.trim()) {
      alert('分析するコードを入力してください');
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiClient.request('/api/ai/analyze/code', {
        method: 'POST',
        body: JSON.stringify({
          code: codeToAnalyze,
          file_type: 'spider'
        })
      });

      setBugs(response.bugs);
    } catch (error) {
      console.error('Failed to analyze code:', error);
      alert('コードの分析に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeCode = async () => {
    if (!codeToAnalyze.trim()) {
      alert('最適化するコードを入力してください');
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiClient.request('/api/ai/optimize/code', {
        method: 'POST',
        body: JSON.stringify({
          code: codeToAnalyze
        })
      });

      setOptimizations(response.suggestions);
    } catch (error) {
      console.error('Failed to optimize code:', error);
      alert('コードの最適化に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('クリップボードにコピーしました');
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-red-300';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="h-4 w-4" />;
      case 'medium':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <CheckCircle className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* タブナビゲーション */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Bot className="h-6 w-6 text-purple-400" />
          <h2 className="text-xl font-semibold text-white">AI コードアシスタント</h2>
        </div>
        
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('generate')}
            className={`px-4 py-2 rounded-md transition-colors ${
              activeTab === 'generate'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Wand2 className="h-4 w-4 inline mr-2" />
            コード生成
          </button>
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-4 py-2 rounded-md transition-colors ${
              activeTab === 'analyze'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Search className="h-4 w-4 inline mr-2" />
            コード分析
          </button>
          <button
            onClick={() => setActiveTab('optimize')}
            className={`px-4 py-2 rounded-md transition-colors ${
              activeTab === 'optimize'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Sparkles className="h-4 w-4 inline mr-2" />
            最適化提案
          </button>
        </div>
      </div>

      {/* コード生成タブ */}
      {activeTab === 'generate' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 入力フォーム */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-400 mb-4">スパイダー生成</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  スパイダー名
                </label>
                <input
                  type="text"
                  value={spiderForm.spider_name}
                  onChange={(e) => setSpiderForm({...spiderForm, spider_name: e.target.value})}
                  className="w-full p-3 bg-gray-700 text-white rounded-md"
                  placeholder="example_spider"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  ターゲットURL
                </label>
                <input
                  type="url"
                  value={spiderForm.target_url}
                  onChange={(e) => setSpiderForm({...spiderForm, target_url: e.target.value})}
                  className="w-full p-3 bg-gray-700 text-white rounded-md"
                  placeholder="https://example.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  データフィールド
                </label>
                <div className="space-y-2">
                  {spiderForm.data_fields.map((field, index) => (
                    <div key={index} className="flex space-x-2">
                      <input
                        type="text"
                        value={field}
                        onChange={(e) => {
                          const newFields = [...spiderForm.data_fields];
                          newFields[index] = e.target.value;
                          setSpiderForm({...spiderForm, data_fields: newFields});
                        }}
                        className="flex-1 p-2 bg-gray-700 text-white rounded-md"
                      />
                      <button
                        onClick={() => {
                          const newFields = spiderForm.data_fields.filter((_, i) => i !== index);
                          setSpiderForm({...spiderForm, data_fields: newFields});
                        }}
                        className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                      >
                        削除
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => setSpiderForm({...spiderForm, data_fields: [...spiderForm.data_fields, '']})}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    フィールド追加
                  </button>
                </div>
              </div>
              
              <button
                onClick={generateSpider}
                disabled={isLoading}
                className="w-full px-4 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '生成中...' : 'スパイダーを生成'}
              </button>
            </div>
          </div>

          {/* 生成結果 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-400 mb-4">生成結果</h3>
            
            {generatedCode ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-white">{generatedCode.title}</h4>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => copyToClipboard(generatedCode.code)}
                      className="p-2 bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                <p className="text-gray-400 text-sm">{generatedCode.description}</p>
                
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-400">信頼度:</span>
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-green-400 h-2 rounded-full"
                      style={{ width: `${generatedCode.confidence * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-green-400">{(generatedCode.confidence * 100).toFixed(0)}%</span>
                </div>
                
                <div className="bg-gray-900 rounded-md p-4 overflow-x-auto">
                  <pre className="text-sm text-gray-300">
                    <code>{generatedCode.code}</code>
                  </pre>
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {generatedCode.tags.map((tag, index) => (
                    <span key={index} className="px-2 py-1 bg-purple-600 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-400">
                <Code className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>スパイダーを生成すると結果がここに表示されます</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* コード分析タブ */}
      {activeTab === 'analyze' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 入力エリア */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-400 mb-4">コード分析</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  分析するコード
                </label>
                <textarea
                  value={codeToAnalyze}
                  onChange={(e) => setCodeToAnalyze(e.target.value)}
                  className="w-full h-64 p-3 bg-gray-700 text-white rounded-md font-mono text-sm"
                  placeholder="ここにPythonコードを貼り付けてください..."
                />
              </div>
              
              <button
                onClick={analyzeCode}
                disabled={isLoading}
                className="w-full px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '分析中...' : 'コードを分析'}
              </button>
            </div>
          </div>

          {/* 分析結果 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-400 mb-4">分析結果</h3>
            
            {bugs.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {bugs.map((bug, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <div className={getSeverityColor(bug.severity)}>
                        {getSeverityIcon(bug.severity)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`text-sm font-medium ${getSeverityColor(bug.severity)}`}>
                            {bug.severity.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-400">{bug.category}</span>
                          {bug.line_number && (
                            <span className="text-xs text-gray-400">Line {bug.line_number}</span>
                          )}
                        </div>
                        <p className="text-white text-sm mb-2">{bug.description}</p>
                        <p className="text-gray-400 text-xs mb-2">{bug.suggestion}</p>
                        {bug.code_snippet && (
                          <div className="bg-gray-900 rounded p-2">
                            <code className="text-xs text-gray-300">{bug.code_snippet}</code>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-400">
                <Search className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>コードを分析すると結果がここに表示されます</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 最適化提案タブ */}
      {activeTab === 'optimize' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 入力エリア */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-400 mb-4">コード最適化</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  最適化するコード
                </label>
                <textarea
                  value={codeToAnalyze}
                  onChange={(e) => setCodeToAnalyze(e.target.value)}
                  className="w-full h-64 p-3 bg-gray-700 text-white rounded-md font-mono text-sm"
                  placeholder="ここにPythonコードを貼り付けてください..."
                />
              </div>
              
              <button
                onClick={optimizeCode}
                disabled={isLoading}
                className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '最適化中...' : '最適化提案を取得'}
              </button>
            </div>
          </div>

          {/* 最適化提案 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-400 mb-4">最適化提案</h3>
            
            {optimizations.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {optimizations.map((suggestion, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-white">{suggestion.title}</h4>
                      <button
                        onClick={() => copyToClipboard(suggestion.code)}
                        className="p-1 bg-gray-600 text-gray-300 rounded hover:bg-gray-500"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                    </div>
                    <p className="text-gray-400 text-sm mb-3">{suggestion.description}</p>
                    <div className="bg-gray-900 rounded p-3 mb-3">
                      <pre className="text-xs text-gray-300 overflow-x-auto">
                        <code>{suggestion.code}</code>
                      </pre>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex flex-wrap gap-1">
                        {suggestion.tags.map((tag, tagIndex) => (
                          <span key={tagIndex} className="px-2 py-1 bg-green-600 text-xs rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <span className="text-xs text-gray-400">
                        信頼度: {(suggestion.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-400">
                <Sparkles className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>コードを最適化すると提案がここに表示されます</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
