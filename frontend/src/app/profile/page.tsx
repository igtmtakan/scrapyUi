'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'next/navigation';
import {
  User,
  Mail,
  Calendar,
  Clock,
  Shield,
  Edit3,
  Save,
  X,
  Camera,
  Globe,
  Settings
} from 'lucide-react';

export default function ProfilePage() {
  const { user, isAuthenticated, getCurrentUser } = useAuthStore();
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    email: '',
    timezone: 'UTC',
  });
  const [stats, setStats] = useState({
    projectCount: 0,
    taskCount: 0,
    isLoading: true,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (user) {
      setFormData({
        full_name: user.full_name || '',
        username: user.username || '',
        email: user.email || '',
        timezone: user.timezone || 'UTC',
      });
    }
  }, [isAuthenticated, user, router]);

  // 統計データを取得する関数
  const loadStats = async () => {
    try {
      setStats(prev => ({ ...prev, isLoading: true }));

      const { apiClient } = await import('@/lib/api');

      console.log('📊 Loading profile stats...');

      // プロジェクト数を取得
      console.log('📁 Fetching projects...');
      const projects = await apiClient.getProjects();
      console.log('📁 Projects loaded:', projects.length);

      // タスク数を取得
      console.log('📋 Fetching tasks...');
      const tasks = await apiClient.getTasks();
      console.log('📋 Tasks loaded:', tasks.length);

      setStats({
        projectCount: projects.length,
        taskCount: tasks.length,
        isLoading: false,
      });

      console.log('✅ Profile stats loaded successfully');
    } catch (error) {
      console.error('❌ Failed to load stats:', error);

      // エラーの詳細をログ出力
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
      }

      setStats(prev => ({ ...prev, isLoading: false }));
    }
  };

  // 統計データを初期化時に読み込み
  useEffect(() => {
    if (isAuthenticated && user) {
      loadStats();
    }
  }, [isAuthenticated, user]);

  const handleSave = async () => {
    try {
      console.log('🔄 Starting profile update...');
      console.log('📊 Current auth state:', {
        isAuthenticated,
        hasUser: !!user,
        userEmail: user?.email
      });

      // トークンの存在確認
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      console.log('🔑 Token status:', { hasToken: !!token, tokenLength: token?.length });

      // API呼び出しでプロフィール更新
      const { apiClient } = await import('@/lib/api');
      console.log('📡 Calling updateProfile API...');

      await apiClient.updateProfile({
        full_name: formData.full_name,
        timezone: formData.timezone,
      });

      console.log('✅ Profile update successful');

      // ユーザー情報を再取得
      await getCurrentUser();
      setIsEditing(false);
    } catch (error) {
      console.error('❌ Profile update failed:', error);

      // 認証エラーの場合はログインページにリダイレクト
      if (error instanceof Error && error.message.includes('Not authenticated')) {
        console.log('🔄 Authentication error detected, redirecting to login...');
        router.push('/login');
      }
    }
  };

  const handleCancel = () => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        username: user.username || '',
        email: user.email || '',
        timezone: user.timezone || 'UTC',
      });
    }
    setIsEditing(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">プロフィールを読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">プロフィール</h1>
          <p className="mt-2 text-gray-600">アカウント情報と設定を管理します</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center">
                {/* Avatar */}
                <div className="relative inline-block">
                  <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                  </div>
                  <button className="absolute bottom-0 right-0 bg-white rounded-full p-2 shadow-lg border border-gray-200 hover:bg-gray-50">
                    <Camera className="w-4 h-4 text-gray-600" />
                  </button>
                </div>

                <h2 className="mt-4 text-xl font-semibold text-gray-900">
                  {user.full_name || user.username}
                </h2>
                <p className="text-gray-600">@{user.username}</p>

                {/* Status Badges */}
                <div className="mt-4 flex justify-center space-x-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <div className="w-1.5 h-1.5 bg-green-400 rounded-full mr-1"></div>
                    アクティブ
                  </span>
                  {user.is_superuser && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      <Shield className="w-3 h-3 mr-1" />
                      管理者
                    </span>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="mt-6 border-t border-gray-200 pt-6">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    {stats.isLoading ? (
                      <div className="text-2xl font-bold text-gray-400">
                        <div className="animate-pulse">-</div>
                      </div>
                    ) : (
                      <div className="text-2xl font-bold text-gray-900">{stats.projectCount}</div>
                    )}
                    <div className="text-sm text-gray-600">プロジェクト</div>
                  </div>
                  <div>
                    {stats.isLoading ? (
                      <div className="text-2xl font-bold text-gray-400">
                        <div className="animate-pulse">-</div>
                      </div>
                    ) : (
                      <div className="text-2xl font-bold text-gray-900">{stats.taskCount}</div>
                    )}
                    <div className="text-sm text-gray-600">タスク</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Profile Details */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">アカウント情報</h3>
                {!isEditing ? (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Edit3 className="w-4 h-4 mr-2" />
                    編集
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSave}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      保存
                    </button>
                    <button
                      onClick={handleCancel}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <X className="w-4 h-4 mr-2" />
                      キャンセル
                    </button>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="px-6 py-6">
                <div className="grid grid-cols-1 gap-6">
                  {/* Full Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <User className="w-4 h-4 inline mr-2" />
                      フルネーム
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={formData.full_name}
                        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900">{user.full_name || '未設定'}</p>
                    )}
                  </div>

                  {/* Username */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <User className="w-4 h-4 inline mr-2" />
                      ユーザー名
                    </label>
                    <p className="text-gray-900">{user.username}</p>
                    <p className="text-sm text-gray-500">ユーザー名は変更できません</p>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Mail className="w-4 h-4 inline mr-2" />
                      メールアドレス
                    </label>
                    <p className="text-gray-900">{user.email}</p>
                    <p className="text-sm text-gray-500">メールアドレスは変更できません</p>
                  </div>

                  {/* Timezone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Globe className="w-4 h-4 inline mr-2" />
                      タイムゾーン
                    </label>
                    {isEditing ? (
                      <select
                        value={formData.timezone}
                        onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="UTC">UTC</option>
                        <option value="Asia/Tokyo">Asia/Tokyo</option>
                        <option value="America/New_York">America/New_York</option>
                        <option value="Europe/London">Europe/London</option>
                      </select>
                    ) : (
                      <p className="text-gray-900">{user.timezone}</p>
                    )}
                  </div>

                  {/* Account Info */}
                  <div className="border-t border-gray-200 pt-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-4">アカウント情報</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Calendar className="w-4 h-4 inline mr-2" />
                          作成日
                        </label>
                        <p className="text-gray-900">{formatDate(user.created_at)}</p>
                      </div>
                      {user.last_login && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Clock className="w-4 h-4 inline mr-2" />
                            最終ログイン
                          </label>
                          <p className="text-gray-900">{formatDate(user.last_login)}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Settings Link */}
            <div className="mt-6">
              <button
                onClick={() => router.push('/settings')}
                className="w-full bg-white border border-gray-300 rounded-lg px-6 py-4 text-left hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <div className="flex items-center">
                  <Settings className="w-5 h-5 text-gray-400 mr-3" />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">設定</h4>
                    <p className="text-sm text-gray-500">アプリケーション設定とプリファレンス</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
