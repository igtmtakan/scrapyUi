'use client'

import Link from "next/link"
import { Code, Database, Play, Settings, FileText, BarChart3 } from "lucide-react"
import NotificationBell from '@/components/notifications/NotificationBell'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* ヘッダー */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Code className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-white">Scrapy-Playwright UI</h1>
            </div>
            <div className="flex items-center space-x-6">
              <nav className="flex items-center space-x-6">
                <Link href="/editor" className="text-gray-300 hover:text-white transition-colors">
                  Editor
                </Link>
                <Link href="/projects" className="text-gray-300 hover:text-white transition-colors">
                  Projects
                </Link>
                <Link href="/monitoring" className="text-gray-300 hover:text-white transition-colors">
                  Monitoring
                </Link>
                <Link href="/schedules" className="text-gray-300 hover:text-white transition-colors">
                  Schedules
                </Link>
                <Link href="/tasks" className="text-gray-300 hover:text-white transition-colors">
                  Tasks
                </Link>
              </nav>

              <NotificationBell />
            </div>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="container mx-auto px-6 py-12">
        {/* ヒーローセクション */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Web Scraping
            <span className="text-blue-400"> Made Easy</span>
          </h2>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Powerful web interface for Scrapy with Playwright integration.
            Create, edit, and manage your web scrapers with JavaScript support.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/editor"
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              <Code className="w-5 h-5" />
              <span>Start Coding</span>
            </Link>
            <Link
              href="/projects"
              className="px-8 py-3 border border-gray-600 hover:border-gray-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              <Database className="w-5 h-5" />
              <span>View Projects</span>
            </Link>
          </div>
        </div>

        {/* 機能カード */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
              <Code className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Script Editor</h3>
            <p className="text-gray-300">
              Monaco Editor with Python syntax highlighting, auto-completion, and Scrapy-specific snippets.
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
              <Play className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Playwright Integration</h3>
            <p className="text-gray-300">
              Handle JavaScript-heavy websites with full browser automation capabilities.
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
              <Database className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Project Management</h3>
            <p className="text-gray-300">
              Organize your scrapers into projects with version control and settings management.
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center mb-4">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Real-time Monitoring</h3>
            <p className="text-gray-300">
              Monitor your scraping tasks with live logs, statistics, and performance metrics.
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="w-12 h-12 bg-red-600 rounded-lg flex items-center justify-center mb-4">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Templates</h3>
            <p className="text-gray-300">
              Pre-built templates for common scraping scenarios: e-commerce, news, APIs, and more.
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-4">
              <Settings className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Easy Configuration</h3>
            <p className="text-gray-300">
              Configure browser settings, delays, proxies, and other scraping parameters through the UI.
            </p>
          </div>
        </div>

        {/* CTA セクション */}
        <div className="text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8">
            <h3 className="text-2xl font-bold text-white mb-4">
              Ready to start scraping?
            </h3>
            <p className="text-blue-100 mb-6">
              Create your first spider in minutes with our intuitive interface.
            </p>
            <Link
              href="/editor"
              className="inline-flex items-center space-x-2 px-6 py-3 bg-white text-blue-600 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              <Code className="w-5 h-5" />
              <span>Open Editor</span>
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}
