'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Settings, 
  Database, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  Code, 
  Download,
  Upload,
  Trash2,
  Save,
  RefreshCw,
  ChevronRight,
  User,
  Lock,
  Monitor,
  Zap
} from 'lucide-react';

interface SettingsSection {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  href?: string;
  action?: () => void;
}

export default function SettingsPage() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const settingsSections: SettingsSection[] = [
    {
      id: 'profile',
      title: 'プロフィール',
      description: 'アカウント情報とプロフィール設定',
      icon: <User className="w-5 h-5" />,
      href: '/profile'
    },
    {
      id: 'security',
      title: 'セキュリティ',
      description: 'パスワード、二要素認証、セッション管理',
      icon: <Shield className="w-5 h-5" />
    },
    {
      id: 'database',
      title: 'データベース設定',
      description: 'データベース接続とバックアップ設定',
      icon: <Database className="w-5 h-5" />,
      href: '/settings/database'
    },
    {
      id: 'notifications',
      title: '通知設定',
      description: 'メール通知、プッシュ通知、アラート設定',
      icon: <Bell className="w-5 h-5" />
    },
    {
      id: 'appearance',
      title: '外観',
      description: 'テーマ、言語、表示設定',
      icon: <Palette className="w-5 h-5" />
    },
    {
      id: 'performance',
      title: 'パフォーマンス',
      description: 'システム最適化、キャッシュ、リソース管理',
      icon: <Zap className="w-5 h-5" />
    },
    {
      id: 'monitoring',
      title: '監視設定',
      description: 'ログ設定、メトリクス、アラート',
      icon: <Monitor className="w-5 h-5" />
    },
    {
      id: 'api',
      title: 'API設定',
      description: 'API キー、レート制限、Webhook設定',
      icon: <Code className="w-5 h-5" />
    }
  ];

  const generalSettings = [
    {
      title: 'デフォルトScrapyバージョン',
      description: '新規プロジェクト作成時のデフォルトバージョン',
      value: '2.11.0',
      type: 'select',
      options: ['2.11.0', '2.10.1', '2.9.0']
    },
    {
      title: 'プロジェクト保存場所',
      description: 'プロジェクトファイルの保存ディレクトリ',
      value: './projects',
      type: 'text'
    },
    {
      title: '自動保存',
      description: 'ファイル編集時の自動保存機能',
      value: true,
      type: 'boolean'
    },
    {
      title: 'ダークモード',
      description: 'ダークテーマの使用',
      value: false,
      type: 'boolean'
    }
  ];

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">認証中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">設定</h1>
          <p className="mt-2 text-gray-600">アプリケーションの設定とプリファレンスを管理します</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-1">
              <button
                onClick={() => setActiveTab('general')}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'general'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Settings className="w-4 h-4 inline mr-2" />
                一般設定
              </button>
              
              {settingsSections.map((section) => (
                <div key={section.id}>
                  {section.href ? (
                    <Link
                      href={section.href}
                      className="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100 flex items-center justify-between group"
                    >
                      <div className="flex items-center">
                        {section.icon}
                        <span className="ml-2">{section.title}</span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
                    </Link>
                  ) : (
                    <button
                      onClick={() => setActiveTab(section.id)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium ${
                        activeTab === section.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      } flex items-center`}
                    >
                      {section.icon}
                      <span className="ml-2">{section.title}</span>
                    </button>
                  )}
                </div>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === 'general' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">一般設定</h2>
                  <p className="mt-1 text-sm text-gray-600">基本的なアプリケーション設定</p>
                </div>
                
                <div className="px-6 py-6">
                  <div className="space-y-6">
                    {generalSettings.map((setting, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-gray-900">{setting.title}</h3>
                          <p className="text-sm text-gray-500">{setting.description}</p>
                        </div>
                        <div className="ml-4">
                          {setting.type === 'boolean' ? (
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                className="sr-only peer"
                                defaultChecked={setting.value as boolean}
                              />
                              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                          ) : setting.type === 'select' ? (
                            <select
                              defaultValue={setting.value as string}
                              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                              {setting.options?.map((option) => (
                                <option key={option} value={option}>{option}</option>
                              ))}
                            </select>
                          ) : (
                            <input
                              type="text"
                              defaultValue={setting.value as string}
                              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-200">
                    <div className="flex justify-between">
                      <button className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        デフォルトに戻す
                      </button>
                      <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <Save className="w-4 h-4 mr-2" />
                        設定を保存
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Other tabs content */}
            {activeTab !== 'general' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">
                    {settingsSections.find(s => s.id === activeTab)?.title}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">
                    {settingsSections.find(s => s.id === activeTab)?.description}
                  </p>
                </div>
                
                <div className="px-6 py-12 text-center">
                  <div className="text-gray-400 mb-4">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">設定項目準備中</h3>
                  <p className="text-gray-600">この設定項目は現在開発中です。</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <Download className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">設定エクスポート</h3>
                <p className="text-sm text-gray-600">現在の設定をファイルに保存</p>
              </div>
            </div>
            <button className="mt-4 w-full bg-blue-50 text-blue-700 px-4 py-2 rounded-md hover:bg-blue-100">
              エクスポート
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <Upload className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">設定インポート</h3>
                <p className="text-sm text-gray-600">設定ファイルから復元</p>
              </div>
            </div>
            <button className="mt-4 w-full bg-green-50 text-green-700 px-4 py-2 rounded-md hover:bg-green-100">
              インポート
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <Trash2 className="w-8 h-8 text-red-600" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">設定リセット</h3>
                <p className="text-sm text-gray-600">すべての設定を初期化</p>
              </div>
            </div>
            <button className="mt-4 w-full bg-red-50 text-red-700 px-4 py-2 rounded-md hover:bg-red-100">
              リセット
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
