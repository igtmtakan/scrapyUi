'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'next/navigation';
import {
  Users,
  UserPlus,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  Shield,
  ShieldCheck,
  UserCheck,
  UserX,
  Eye,
  Settings,
  BarChart3
} from 'lucide-react';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  role: 'user' | 'admin' | 'moderator';
  created_at: string;
  last_login?: string;
}

interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  admin_users: number;
  moderator_users: number;
  regular_users: number;
  recent_registrations: number;
}

export default function AdminPage() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (user?.role !== 'admin') {
      router.push('/');
      return;
    }

    fetchUsers();
    fetchStats();
  }, [isAuthenticated, user, router]);

  // フィルター変更時にユーザーリストを更新
  useEffect(() => {
    if (isAuthenticated && user?.role === 'admin') {
      fetchUsers();
    }
  }, [searchTerm, roleFilter, statusFilter]);

  const fetchUsers = async () => {
    try {
      const { apiClient } = await import('@/lib/api');
      const userData = await apiClient.getAllUsers({
        search: searchTerm || undefined,
        role: roleFilter !== 'all' ? roleFilter : undefined,
        is_active: statusFilter !== 'all' ? statusFilter === 'active' : undefined
      });
      setUsers(userData);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const { apiClient } = await import('@/lib/api');
      const statsData = await apiClient.getUserStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleUserAction = async (userId: string, action: string) => {
    try {
      const { apiClient } = await import('@/lib/api');

      if (action === 'activate') {
        await apiClient.activateUser(userId);
      } else if (action === 'deactivate') {
        await apiClient.deactivateUser(userId);
      }

      fetchUsers();
      fetchStats();
    } catch (error) {
      console.error(`Failed to ${action} user:`, error);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);

    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' ||
                         (statusFilter === 'active' && user.is_active) ||
                         (statusFilter === 'inactive' && !user.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleBadge = (role: string) => {
    const styles = {
      admin: 'bg-red-100 text-red-800',
      moderator: 'bg-yellow-100 text-yellow-800',
      user: 'bg-blue-100 text-blue-800'
    };

    const icons = {
      admin: <ShieldCheck className="w-3 h-3 mr-1" />,
      moderator: <Shield className="w-3 h-3 mr-1" />,
      user: <Users className="w-3 h-3 mr-1" />
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[role as keyof typeof styles]}`}>
        {icons[role as keyof typeof icons]}
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isAuthenticated || user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">アクセス権限がありません</h2>
          <p className="text-gray-600">この機能は管理者のみ利用できます。</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">ユーザー情報を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">ユーザー管理</h1>
          <p className="mt-2 text-gray-600">システムユーザーの管理と統計情報</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">総ユーザー数</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_users}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <UserCheck className="w-8 h-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">アクティブユーザー</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.active_users}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <ShieldCheck className="w-8 h-8 text-red-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">管理者</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.admin_users}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">新規登録（30日）</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.recent_registrations}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="ユーザーを検索..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Role Filter */}
              <div>
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">すべてのロール</option>
                  <option value="admin">管理者</option>
                  <option value="moderator">モデレーター</option>
                  <option value="user">一般ユーザー</option>
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">すべてのステータス</option>
                  <option value="active">アクティブ</option>
                  <option value="inactive">非アクティブ</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ユーザー
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ロール
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    登録日
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    最終ログイン
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    アクション
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                          {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.full_name || user.username}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getRoleBadge(user.role)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {user.is_active ? (
                          <>
                            <UserCheck className="w-3 h-3 mr-1" />
                            アクティブ
                          </>
                        ) : (
                          <>
                            <UserX className="w-3 h-3 mr-1" />
                            非アクティブ
                          </>
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.last_login ? formatDate(user.last_login) : '未ログイン'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => {
                            setSelectedUser(user);
                            setShowUserModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleUserAction(user.id, user.is_active ? 'deactivate' : 'activate')}
                          className={`${user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}`}
                        >
                          {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredUsers.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">ユーザーが見つかりません</h3>
              <p className="text-gray-600">検索条件を変更してください。</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
