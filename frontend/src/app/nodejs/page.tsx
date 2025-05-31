'use client';

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Server,
  Globe,
  FileText,
  Camera,
  Activity,
  Zap,
  Code,
  Monitor,
  Terminal
} from 'lucide-react';

import NodeJSMonitor from '@/components/nodejs/NodeJSMonitor';
import SPAScrapingForm from '@/components/nodejs/SPAScrapingForm';
import PDFGenerator from '@/components/nodejs/PDFGenerator';
import ScreenshotCapture from '@/components/nodejs/ScreenshotCapture';
import WorkflowManager from '@/components/nodejs/WorkflowManager';
import TerminalComponent from '@/components/nodejs/Terminal';

export default function NodeJSPage() {
  const [activeTab, setActiveTab] = useState('monitor');

  const features = [
    {
      icon: <Globe className="w-6 h-6" />,
      title: 'SPA Scraping',
      description: 'JavaScript重要サイトのスクレイピング',
      badge: 'Puppeteer',
      color: 'bg-blue-100 text-blue-800'
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: 'PDF Generation',
      description: 'WebページやHTMLからPDF生成',
      badge: 'PDF',
      color: 'bg-green-100 text-green-800'
    },
    {
      icon: <Camera className="w-6 h-6" />,
      title: 'Screenshot Capture',
      description: 'Webページのスクリーンショット取得',
      badge: 'Image',
      color: 'bg-purple-100 text-purple-800'
    },
    {
      icon: <Activity className="w-6 h-6" />,
      title: 'Browser Automation',
      description: 'ブラウザ自動化とワークフロー',
      badge: 'Automation',
      color: 'bg-orange-100 text-orange-800'
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <div className="p-3 bg-green-100 rounded-full">
            <Server className="w-8 h-8 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Node.js Integration
          </h1>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          Puppeteerを使用したブラウザ自動化、PDF生成、スクリーンショット機能
        </p>
      </div>

      {/* Features Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((feature, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  {feature.icon}
                </div>
                <Badge className={feature.color}>
                  {feature.badge}
                </Badge>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {feature.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="monitor" className="flex items-center gap-2">
            <Monitor className="w-4 h-4" />
            Monitor
          </TabsTrigger>
          <TabsTrigger value="terminal" className="flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            Terminal
          </TabsTrigger>
          <TabsTrigger value="workflows" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Workflows
          </TabsTrigger>
          <TabsTrigger value="scraping" className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            SPA Scraping
          </TabsTrigger>
          <TabsTrigger value="pdf" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            PDF Generator
          </TabsTrigger>
          <TabsTrigger value="screenshot" className="flex items-center gap-2">
            <Camera className="w-4 h-4" />
            Screenshot
          </TabsTrigger>
        </TabsList>

        <TabsContent value="monitor" className="space-y-6">
          <NodeJSMonitor />
        </TabsContent>

        <TabsContent value="terminal" className="space-y-6">
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Terminal
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Scrapy プロジェクト用のインタラクティブターミナル
              </p>
              <p className="text-sm text-blue-600 dark:text-blue-400 mt-2">
                🚀 scrapy crawlwithwatchdog コマンドでリアルタイム監視付きスクレイピング
              </p>
            </div>
            <TerminalComponent className="max-w-full" />
          </div>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-6">
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Workflow Automation
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                複数操作の連携とスケジュール実行
              </p>
            </div>
            <WorkflowManager />
          </div>
        </TabsContent>

        <TabsContent value="scraping" className="space-y-6">
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                SPA Scraping
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                JavaScript重要サイトやSingle Page Applicationのスクレイピング
              </p>
            </div>
            <SPAScrapingForm />
          </div>
        </TabsContent>

        <TabsContent value="pdf" className="space-y-6">
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                PDF Generator
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                WebページやHTMLコンテンツからPDFファイルを生成
              </p>
            </div>
            <PDFGenerator />
          </div>
        </TabsContent>

        <TabsContent value="screenshot" className="space-y-6">
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Screenshot Capture
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Webページの高品質スクリーンショットを取得
              </p>
            </div>
            <ScreenshotCapture />
          </div>
        </TabsContent>
      </Tabs>

      {/* Technical Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="w-5 h-5" />
            Technical Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Architecture
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                <li>• Node.js + Express</li>
                <li>• Puppeteer Browser Pool</li>
                <li>• FastAPI Integration</li>
                <li>• Rate Limiting & Security</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Capabilities
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                <li>• JavaScript Execution</li>
                <li>• Dynamic Content Loading</li>
                <li>• Custom User Agents</li>
                <li>• Viewport Configuration</li>
                <li>• Interactive Terminal</li>
                <li>• Real-time Monitoring</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Output Formats
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                <li>• JSON Data Extraction</li>
                <li>• PDF Documents</li>
                <li>• PNG/JPEG Images</li>
                <li>• Base64 Encoding</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Tips */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-800 dark:text-blue-200">
            <Zap className="w-5 h-5" />
            Performance Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-700 dark:text-blue-300">
            <div>
              <h5 className="font-medium mb-2">Optimization</h5>
              <ul className="space-y-1">
                <li>• ブラウザプールで効率的なリソース管理</li>
                <li>• 適切なタイムアウト設定</li>
                <li>• 必要最小限のビューポートサイズ</li>
              </ul>
            </div>
            <div>
              <h5 className="font-medium mb-2">Best Practices</h5>
              <ul className="space-y-1">
                <li>• 具体的なCSSセレクターを使用</li>
                <li>• レート制限を考慮した実行</li>
                <li>• エラーハンドリングの実装</li>
              </ul>
            </div>
            <div>
              <h5 className="font-medium mb-2">Terminal Usage</h5>
              <ul className="space-y-1">
                <li>• crawlwithwatchdogでリアルタイム監視</li>
                <li>• 適切なタスクIDの指定</li>
                <li>• JSONLファイル出力の活用</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
