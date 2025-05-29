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

  // パスワード変更用のstate
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // 一般設定用のstate
  const [generalSettings, setGeneralSettings] = useState({
    default_scrapy_version: '2.11.0',
    project_directory: '/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects',
    auto_save: true,
    dark_mode: false,
    default_log_level: 'INFO',
  });
  const [generalLoading, setGeneralLoading] = useState(false);
  const [generalMessage, setGeneralMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // 一般設定を読み込む
  const loadGeneralSettings = async () => {
    try {
      const { apiClient } = await import('@/lib/api');
      const settings = await apiClient.getGeneralSettings();
      setGeneralSettings(prev => ({ ...prev, ...settings }));
      setSettingsLoaded(true);
    } catch (error) {
      console.error('Failed to load general settings:', error);
      // エラーが発生してもデフォルト値を使用
      setSettingsLoaded(true);
    }
  };

  // 初期化時に設定を読み込み
  useEffect(() => {
    if (isAuthenticated && !settingsLoaded) {
      loadGeneralSettings();
    }
  }, [isAuthenticated, settingsLoaded]);

  // 一般設定保存処理
  const handleGeneralSettingsSave = async () => {
    setGeneralLoading(true);
    setGeneralMessage(null);

    try {
      const { apiClient } = await import('@/lib/api');
      await apiClient.updateGeneralSettings(generalSettings);

      setGeneralMessage({ type: 'success', text: '設定が正常に保存されました。' });
    } catch (error) {
      console.error('General settings save failed:', error);
      if (error instanceof Error) {
        setGeneralMessage({ type: 'error', text: error.message || '設定の保存に失敗しました。' });
      } else {
        setGeneralMessage({ type: 'error', text: '設定の保存に失敗しました。' });
      }
    } finally {
      setGeneralLoading(false);
    }
  };

  // 一般設定をデフォルトに戻す
  const handleGeneralSettingsReset = async () => {
    if (!confirm('設定をデフォルト値に戻しますか？この操作は元に戻せません。')) {
      return;
    }

    setGeneralLoading(true);
    setGeneralMessage(null);

    try {
      const { apiClient } = await import('@/lib/api');
      await apiClient.resetGeneralSettings();

      // デフォルト値に戻す
      setGeneralSettings({
        default_scrapy_version: '2.11.0',
        project_directory: '/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects',
        auto_save: true,
        dark_mode: false,
        default_log_level: 'INFO',
      });

      setGeneralMessage({ type: 'success', text: '設定がデフォルト値に戻されました。' });
    } catch (error) {
      console.error('General settings reset failed:', error);
      setGeneralMessage({ type: 'error', text: '設定のリセットに失敗しました。' });
    } finally {
      setGeneralLoading(false);
    }
  };

  // パスワード変更処理
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    // バリデーション
    if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      setPasswordMessage({ type: 'error', text: 'すべてのフィールドを入力してください。' });
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordMessage({ type: 'error', text: '新しいパスワードと確認用パスワードが一致しません。' });
      return;
    }

    if (passwordForm.newPassword.length < 6) {
      setPasswordMessage({ type: 'error', text: 'パスワードは6文字以上で入力してください。' });
      return;
    }

    setPasswordLoading(true);
    setPasswordMessage(null);

    try {
      const { apiClient } = await import('@/lib/api');
      await apiClient.changePassword({
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
      });

      setPasswordMessage({ type: 'success', text: 'パスワードが正常に変更されました。' });
      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (error) {
      console.error('Password change failed:', error);
      if (error instanceof Error) {
        setPasswordMessage({ type: 'error', text: error.message || 'パスワードの変更に失敗しました。' });
      } else {
        setPasswordMessage({ type: 'error', text: 'パスワードの変更に失敗しました。' });
      }
    } finally {
      setPasswordLoading(false);
    }
  };

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

  // 設定項目の定義
  const settingItems = [
    {
      key: 'default_scrapy_version',
      title: 'デフォルトScrapyバージョン',
      description: '新規プロジェクト作成時のデフォルトバージョン',
      type: 'select',
      options: ['2.11.0', '2.10.1', '2.9.0', '2.8.0']
    },
    {
      key: 'project_directory',
      title: 'プロジェクト保存場所',
      description: 'プロジェクトファイルの保存ディレクトリ（固定）',
      type: 'readonly'
    },
    {
      key: 'auto_save',
      title: '自動保存',
      description: 'ファイル編集時の自動保存機能',
      type: 'boolean'
    },
    {
      key: 'dark_mode',
      title: 'ダークモード',
      description: 'ダークテーマの使用',
      type: 'boolean'
    },
    {
      key: 'default_log_level',
      title: 'デフォルトログレベル',
      description: 'スパイダー実行時のデフォルトログレベル',
      type: 'select',
      options: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
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

              {settingsSections
                .filter(section => {
                  // データベース設定は管理者のみ表示
                  if (section.id === 'database') {
                    return user?.role === 'admin';
                  }
                  return true;
                })
                .map((section) => (
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
                  <p className="mt-1 text-sm text-gray-600">基本的なアプリケーション設定とScrapyの動作設定</p>
                </div>

                <div className="px-6 py-6">
                  {generalMessage && (
                    <div className={`mb-6 p-4 rounded-md ${
                      generalMessage.type === 'success'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-red-50 text-red-800 border border-red-200'
                    }`}>
                      {generalMessage.text}
                    </div>
                  )}

                  <div className="space-y-8">
                    {/* 基本設定セクション */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">基本設定</h3>
                      <div className="space-y-6">
                        {settingItems.map((item) => (
                          <div key={item.key} className="flex items-center justify-between">
                            <div className="flex-1">
                              <h4 className="text-sm font-medium text-gray-900">{item.title}</h4>
                              <p className="text-sm text-gray-500">{item.description}</p>
                            </div>
                            <div className="ml-4">
                              {item.type === 'boolean' ? (
                                <label className="relative inline-flex items-center cursor-pointer">
                                  <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={generalSettings[item.key as keyof typeof generalSettings] as boolean}
                                    onChange={(e) => setGeneralSettings(prev => ({
                                      ...prev,
                                      [item.key]: e.target.checked
                                    }))}
                                    disabled={generalLoading}
                                  />
                                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                              ) : item.type === 'select' ? (
                                <select
                                  value={generalSettings[item.key as keyof typeof generalSettings] as string}
                                  onChange={(e) => setGeneralSettings(prev => ({
                                    ...prev,
                                    [item.key]: e.target.value
                                  }))}
                                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                  disabled={generalLoading}
                                >
                                  {item.options?.map((option) => (
                                    <option key={option} value={option}>{option}</option>
                                  ))}
                                </select>
                              ) : item.type === 'readonly' ? (
                                <input
                                  type="text"
                                  value={generalSettings[item.key as keyof typeof generalSettings] as string}
                                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500"
                                  readOnly
                                />
                              ) : item.type === 'number' ? (
                                <input
                                  type="number"
                                  value={generalSettings[item.key as keyof typeof generalSettings] as number}
                                  onChange={(e) => setGeneralSettings(prev => ({
                                    ...prev,
                                    [item.key]: parseFloat(e.target.value) || 0
                                  }))}
                                  min={item.min}
                                  max={item.max}
                                  step={item.step}
                                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-24"
                                  disabled={generalLoading}
                                />
                              ) : (
                                <input
                                  type="text"
                                  value={generalSettings[item.key as keyof typeof generalSettings] as string}
                                  onChange={(e) => setGeneralSettings(prev => ({
                                    ...prev,
                                    [item.key]: e.target.value
                                  }))}
                                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                  disabled={generalLoading}
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-200">
                    <div className="flex justify-between">
                      <button
                        onClick={handleGeneralSettingsReset}
                        disabled={generalLoading}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        デフォルトに戻す
                      </button>
                      <button
                        onClick={handleGeneralSettingsSave}
                        disabled={generalLoading}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {generalLoading ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            保存中...
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" />
                            設定を保存
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">セキュリティ設定</h2>
                  <p className="mt-1 text-sm text-gray-600">パスワード、二要素認証、セッション管理</p>
                </div>

                <div className="px-6 py-6">
                  {/* パスワード変更セクション */}
                  <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">パスワード変更</h3>

                    {passwordMessage && (
                      <div className={`mb-4 p-4 rounded-md ${
                        passwordMessage.type === 'success'
                          ? 'bg-green-50 text-green-800 border border-green-200'
                          : 'bg-red-50 text-red-800 border border-red-200'
                      }`}>
                        {passwordMessage.text}
                      </div>
                    )}

                    <form onSubmit={handlePasswordChange} className="space-y-4">
                      <div>
                        <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
                          現在のパスワード
                        </label>
                        <input
                          type="password"
                          id="currentPassword"
                          value={passwordForm.currentPassword}
                          onChange={(e) => setPasswordForm(prev => ({ ...prev, currentPassword: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="現在のパスワードを入力"
                          disabled={passwordLoading}
                        />
                      </div>

                      <div>
                        <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
                          新しいパスワード
                        </label>
                        <input
                          type="password"
                          id="newPassword"
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm(prev => ({ ...prev, newPassword: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="新しいパスワードを入力（6文字以上）"
                          disabled={passwordLoading}
                        />
                      </div>

                      <div>
                        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                          新しいパスワード（確認）
                        </label>
                        <input
                          type="password"
                          id="confirmPassword"
                          value={passwordForm.confirmPassword}
                          onChange={(e) => setPasswordForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="新しいパスワードを再入力"
                          disabled={passwordLoading}
                        />
                      </div>

                      <div className="pt-4">
                        <button
                          type="submit"
                          disabled={passwordLoading}
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {passwordLoading ? (
                            <>
                              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                              変更中...
                            </>
                          ) : (
                            <>
                              <Lock className="w-4 h-4 mr-2" />
                              パスワードを変更
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </div>

                  {/* セキュリティ情報セクション */}
                  <div className="border-t border-gray-200 pt-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">セキュリティ情報</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">最終ログイン</h4>
                          <p className="text-sm text-gray-600">
                            {user?.updated_at ? new Date(user.updated_at).toLocaleString('ja-JP') : '不明'}
                          </p>
                        </div>
                        <Shield className="w-5 h-5 text-green-600" />
                      </div>

                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">アカウント作成日</h4>
                          <p className="text-sm text-gray-600">
                            {user?.created_at ? new Date(user.created_at).toLocaleString('ja-JP') : '不明'}
                          </p>
                        </div>
                        <User className="w-5 h-5 text-blue-600" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Other tabs content */}
            {activeTab !== 'general' && activeTab !== 'security' && (
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
