/**
 * API Client for Scrapy Web UI
 * Handles all HTTP requests to the backend API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role: 'user' | 'admin' | 'moderator';
  created_at: string;
  last_login?: string;
  avatar_url?: string;
  timezone: string;
  preferences: Record<string, any>;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  path: string;
  user_id: string;
  username?: string;  // ユーザー名を追加
  created_at: string;
  updated_at: string;
  is_active: boolean;
  settings: Record<string, any>;
  is_fully_synced?: boolean;  // 同期状態を追加
  spiders?: Spider[];  // スパイダー一覧を追加（プロジェクト詳細用）
}

export interface Spider {
  id: string;
  name: string;
  description: string;
  code: string;
  template: string;
  framework: string;
  start_urls: string[];
  project_id: string;
  created_at: string;
  updated_at: string;
  settings: Record<string, any>;
}

export interface Task {
  id: string;
  project_id: string;
  spider_id: string;
  status: 'PENDING' | 'RUNNING' | 'FINISHED' | 'FAILED' | 'CANCELLED';
  user_id: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  log_level: string;
  items_count?: number;
  requests_count?: number;
  error_count?: number;
  settings: Record<string, any>;
}

export interface Result {
  id: string;
  task_id: string;
  url: string;
  data: Record<string, any>;
  created_at: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  user_id: string;
  is_read: boolean;
  created_at: string;
}

export interface Proxy {
  id: string;
  name: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
  proxy_type: 'http' | 'https' | 'socks4' | 'socks5';
  user_id: string;
  is_active: boolean;
  success_rate?: number;
  avg_response_time?: number;
  last_used?: string;
  created_at: string;
}

export interface Schedule {
  id: string;
  name: string;
  description?: string;
  cron_expression: string;
  project_id: string;
  spider_id: string;
  is_active: boolean;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// API Response Types
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

// API Client Class
class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = '') {
    // 直接バックエンドに接続（プロキシを使用しない）
    this.baseURL = baseURL || 'http://localhost:8000';
    this.loadToken();
  }

  private loadToken() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
    }
  }

  private saveToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  private removeToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('auth-storage');
    }
  }

  // 認証状態をチェックするヘルパーメソッド
  public isAuthenticated(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }

    // トークンを再読み込み
    this.loadToken();

    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    console.log('🔍 Auth check:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      tokenInMemory: !!this.token
    });

    return !!(accessToken || refreshToken);
  }

  // トークンの有効性をチェック
  public hasValidTokens(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }

    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    console.log('🔍 Token validity check:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken
    });

    // 少なくともリフレッシュトークンがあれば認証可能
    return !!(accessToken && refreshToken);
  }

  private async refreshToken(): Promise<void> {
    if (typeof window === 'undefined') {
      throw new Error('Cannot refresh token on server side');
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      console.warn('No refresh token available, redirecting to login');
      this.removeToken();
      // ログインページにリダイレクト
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`,
        },
      });

      if (!response.ok) {
        console.warn('Token refresh failed:', response.status, response.statusText);
        this.removeToken();
        // ログインページにリダイレクト
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.saveToken(data.access_token);

      // Update refresh token if provided
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      console.log('Token refreshed successfully');
    } catch (error) {
      console.error('Token refresh error:', error);
      this.removeToken();
      // ログインページにリダイレクト
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      throw error;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // トークンを再読み込み（最新の状態を取得）
    this.loadToken();

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    console.log('🌐 API Request:', {
      method: options.method || 'GET',
      url,
      hasToken: !!this.token,
      tokenPreview: this.token ? `${this.token.slice(0, 10)}...` : 'none'
    });

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        console.warn('🔒 401 Unauthorized detected');

        // Try to refresh token once (avoid infinite recursion)
        if (!endpoint.includes('/auth/') && this.token && !options.headers?.['X-Retry-After-Refresh']) {
          console.log('🔄 Attempting token refresh...');
          try {
            await this.refreshToken();
            // Retry the original request with new token and retry flag
            console.log('✅ Token refreshed, retrying original request...');
            const retryOptions = {
              ...options,
              headers: {
                ...options.headers,
                'X-Retry-After-Refresh': 'true'
              }
            };
            return this.request(endpoint, retryOptions);
          } catch (refreshError) {
            console.error('❌ Token refresh failed:', refreshError);
            this.removeToken();
            // ログインページにリダイレクト
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
              console.log('🔄 Redirecting to login page...');
              window.location.href = '/login';
            }
            throw new Error('Not authenticated');
          }
        } else {
          console.warn('🚫 Cannot refresh token, removing tokens...');
          this.removeToken();
          // ログインページにリダイレクト
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            console.log('🔄 Redirecting to login page...');
            window.location.href = '/login';
          }
          throw new Error('Not authenticated');
        }
      }

      // レスポンステキストを取得（一度だけ）
      const responseText = await response.text();
      console.error(`API Error [${response.status}]:`, {
        status: response.status,
        statusText: response.statusText,
        url: response.url,
        responseText: responseText,
        headers: Object.fromEntries(response.headers.entries()),
        requestHeaders: options.headers,
        requestBody: options.body,
        token: this.token ? 'Present' : 'Missing'
      });

      // JSONパースを試行
      let errorData: any = {};
      if (responseText.trim()) {
        try {
          errorData = JSON.parse(responseText);
        } catch (parseError) {
          console.warn('Failed to parse error response as JSON:', parseError);
          // JSONでない場合はテキストをそのまま使用
          throw new Error(`API request failed: ${response.status} ${response.statusText}${responseText ? ` - ${responseText}` : ''}`);
        }
      }

      // FastAPIのバリデーションエラーの場合
      if (response.status === 422 && errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          const validationErrors = errorData.detail.map((err: any) =>
            `${err.loc?.join('.')}: ${err.msg}`
          ).join(', ');
          throw new Error(`Validation Error: ${validationErrors}`);
        } else {
          throw new Error(`Validation Error: ${errorData.detail}`);
        }
      }

      // 400エラーの場合
      if (response.status === 400) {
        console.error('400 Bad Request details:', {
          url: response.url,
          status: response.status,
          statusText: response.statusText,
          errorData,
          responseText
        });

        // 日本語エラーメッセージに変換
        let errorMessage = 'リクエストに問題があります。';
        if (errorData.detail) {
          // スパイダー関連のエラー
          if (errorData.detail.includes('Spider with this name already exists')) {
            errorMessage = errorData.detail; // スパイダー作成ページで詳細処理される
          } else if (errorData.detail.includes('Spider file') && errorData.detail.includes('already exists')) {
            errorMessage = errorData.detail; // スパイダー作成ページで詳細処理される
          }
          // ユーザー関連のエラー
          else if (errorData.detail.includes('このメールアドレスは既に使用されています') ||
              (errorData.detail.includes('already exists') && errorData.detail.includes('email')) ||
              (errorData.detail.includes('already taken') && errorData.detail.includes('email'))) {
            errorMessage = 'このメールアドレスは既に使用されています。';
          } else if (errorData.detail.includes('password') && errorData.detail.includes('length')) {
            errorMessage = 'パスワードは8文字以上である必要があります。';
          } else if (errorData.detail.includes('email') && errorData.detail.includes('invalid')) {
            errorMessage = '有効なメールアドレスを入力してください。';
          } else if (errorData.detail.includes('validation')) {
            errorMessage = '入力データに問題があります。入力内容を確認してください。';
          } else {
            errorMessage = errorData.detail;
          }
        }

        throw new Error(errorMessage);
      }

      // 401 Unauthorized エラーの場合、ログイン画面にリダイレクト
      if (response.status === 401) {
        console.warn('401 Unauthorized: Clearing tokens and redirecting to login page');

        // トークンをクリア
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('auth-storage');

          // 現在のページがログインページでない場合のみリダイレクト
          if (!window.location.pathname.includes('/login')) {
            console.log('Redirecting to login page from:', window.location.pathname);
            window.location.href = '/login';
          }
        }

        throw new Error('認証が必要です。ログインページにリダイレクトします。');
      }

      // 404エラーの場合
      if (response.status === 404) {
        throw new Error(errorData.detail || 'Resource not found');
      }

      // 403エラーの場合（認証が必要または権限不足）
      if (response.status === 403) {
        console.warn('403 Forbidden: Checking if authentication is required');

        // "Not authenticated"の場合は401と同様に処理
        if (errorData.detail && errorData.detail.includes('Not authenticated')) {
          console.warn('403 Forbidden (Not authenticated): Clearing tokens and redirecting to login page');

          // トークンをクリア
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('auth-storage');

            // 現在のページがログインページでない場合のみリダイレクト
            if (!window.location.pathname.includes('/login')) {
              console.log('Redirecting to login page from:', window.location.pathname);
              window.location.href = '/login';
            }
          }

          throw new Error('認証が必要です。ログインページにリダイレクトします。');
        }

        // その他の403エラー（権限不足など）
        throw new Error(errorData.detail || 'アクセスが拒否されました。権限を確認してください。');
      }

      // 500エラーの場合
      if (response.status >= 500) {
        console.error('500 Internal Server Error details:', {
          url: response.url,
          status: response.status,
          statusText: response.statusText,
          errorData,
          responseText
        });

        // 日本語エラーメッセージに変換
        let errorMessage = 'サーバーエラーが発生しました。';
        if (errorData.detail) {
          // スパイダー関連のエラー
          if (errorData.detail.includes('Spider') && errorData.detail.includes('already exists')) {
            errorMessage = `サーバーエラー: ${errorData.detail}`;
          }
          // ユーザー関連のエラー
          else if ((errorData.detail.includes('already exists') || errorData.detail.includes('already taken')) &&
                   (errorData.detail.includes('email') || errorData.detail.includes('username'))) {
            errorMessage = 'このメールアドレスまたはユーザー名は既に使用されています。';
          } else if (errorData.detail.includes('password')) {
            errorMessage = 'パスワードに関するエラーが発生しました。';
          } else if (errorData.detail.includes('validation')) {
            errorMessage = '入力データの検証でエラーが発生しました。';
          } else if (errorData.detail.includes('role')) {
            errorMessage = 'ユーザー権限の設定でエラーが発生しました。';
          } else {
            errorMessage = `サーバーエラー: ${errorData.detail}`;
          }
        }

        throw new Error(errorMessage);
      }

      // その他のエラー
      throw new Error(errorData.detail || errorData.message || `API request failed: ${response.status} ${response.statusText}`);
    }

    // 204 No Content の場合は空のオブジェクトを返す
    if (response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      // レスポンスボディが空の場合をチェック
      const text = await response.text();
      if (!text.trim()) {
        return {} as T;
      }
      try {
        return JSON.parse(text);
      } catch (error) {
        console.warn('Failed to parse JSON response:', text);
        return {} as T;
      }
    }

    return response.text() as unknown as T;
  }

  // Health check
  async healthCheck(): Promise<any> {
    try {
      const response = await fetch('/api/auth/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Health check failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    this.saveToken(response.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('refresh_token', response.refresh_token);
    }

    return response;
  }

  async register(userData: {
    email: string;
    username: string;
    full_name: string;
    password: string;
  }): Promise<User> {
    return this.request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout(): Promise<void> {
    try {
      // トークンが存在する場合のみサーバーにログアウト要求を送信
      if (this.token) {
        await this.request('/api/auth/logout', { method: 'POST' });
      }
    } catch (error) {
      // ログアウトエラーは無視（トークンが無効でも問題ない）
      console.warn('Logout request failed:', error);
    } finally {
      // 常にローカルトークンを削除
      this.removeToken();
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  async updateProfile(profileData: {
    full_name?: string;
    timezone?: string;
    preferences?: Record<string, any>;
  }): Promise<User> {
    return this.request<User>('/api/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async changePassword(passwordData: { current_password: string; new_password: string }): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/auth/change-password', {
      method: 'PUT',
      body: JSON.stringify(passwordData),
    });
  }

  // 一般設定関連のメソッド
  async getGeneralSettings(): Promise<any> {
    return this.request<any>('/api/settings/general');
  }

  async updateGeneralSettings(settings: any): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/settings/general', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async resetGeneralSettings(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/settings/general/reset', {
      method: 'POST',
    });
  }

  // 共有機能関連のメソッド
  async createTeam(teamData: { name: string; description?: string }): Promise<{ message: string; team_id: string }> {
    return this.request<{ message: string; team_id: string }>('/api/sharing/teams', {
      method: 'POST',
      body: JSON.stringify(teamData),
    });
  }

  async getTeams(): Promise<any[]> {
    return this.request<any[]>('/api/sharing/teams');
  }

  async addTeamMember(teamId: string, memberData: { user_email: string; role?: string }): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/sharing/teams/${teamId}/members`, {
      method: 'POST',
      body: JSON.stringify(memberData),
    });
  }

  async shareProject(shareData: {
    project_id: string;
    target_type: string;
    target_identifier: string;
    permission?: string;
    expires_days?: number;
  }): Promise<{ message: string; share_id: string }> {
    return this.request<{ message: string; share_id: string }>('/api/sharing/projects/share', {
      method: 'POST',
      body: JSON.stringify(shareData),
    });
  }

  async getSharedProjects(): Promise<any[]> {
    return this.request<any[]>('/api/sharing/projects/shared');
  }

  // 管理者用ユーザー管理メソッド
  async getAllUsers(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<any[]> {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params?.search) searchParams.append('search', params.search);
    if (params?.role) searchParams.append('role', params.role);
    if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());

    const url = `/api/admin/users${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return this.request<any[]>(url);
  }

  async getUserById(userId: string): Promise<any> {
    return this.request<any>(`/api/admin/users/${userId}`);
  }

  async createUser(userData: {
    email: string;
    username: string;
    full_name?: string;
    password: string;
    role?: string;
    is_active?: boolean;
    avatar_url?: string;
  }): Promise<any> {
    return this.request<any>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(userId: string, userData: {
    email?: string;
    username?: string;
    full_name?: string;
    role?: string;
    is_active?: boolean;
    avatar_url?: string;
  }): Promise<any> {
    return this.request<any>(`/api/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async activateUser(userId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/users/${userId}/activate`, {
      method: 'POST',
    });
  }

  async deactivateUser(userId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/users/${userId}/deactivate`, {
      method: 'POST',
    });
  }

  async resetUserPassword(userId: string, newPassword: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/users/${userId}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    });
  }

  async getUserStats(): Promise<{
    total_users: number;
    active_users: number;
    inactive_users: number;
    admin_users: number;
    moderator_users: number;
    regular_users: number;
    recent_registrations: number;
  }> {
    return this.request<any>('/api/admin/stats/users');
  }



  // Script Execution
  async executeScript(scriptData: {
    script_content: string;
    spider_name: string;
    start_urls?: string[];
    settings?: Record<string, any>;
    project_id?: string;
    spider_id?: string;
  }): Promise<{
    execution_id: string;
    status: string;
    output: string[];
    errors: string[];
    extracted_data: any[];
    execution_time: number;
    started_at: string;
    finished_at?: string;
  }> {
    console.log('API executeScript called with:', {
      spider_name: scriptData.spider_name,
      start_urls: scriptData.start_urls,
      script_length: scriptData.script_content?.length,
      settings: scriptData.settings
    });

    // 6分のタイムアウトを設定（バックエンドの5分より長く）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 360000);

    try {
      const result = await this.request('/api/script/execute', {
        method: 'POST',
        body: JSON.stringify(scriptData),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Script execution timed out (6 minutes). Please try again or optimize your script.');
      }
      throw error;
    }
  }

  // Test Script Execution (simplified)
  async testScript(scriptData: {
    script_content: string;
    spider_name: string;
    start_urls?: string[];
    settings?: Record<string, any>;
    project_id?: string;
    spider_id?: string;
  }): Promise<{
    execution_id: string;
    status: string;
    output: string[];
    errors: string[];
    extracted_data: any[];
    execution_time: number;
    started_at: string;
    finished_at?: string;
  }> {
    console.log('API testScript called with:', {
      spider_name: scriptData.spider_name,
      start_urls: scriptData.start_urls,
      script_length: scriptData.script_content?.length,
      settings: scriptData.settings
    });

    // 1分のタイムアウトを設定
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      const result = await this.request('/api/script/test', {
        method: 'POST',
        body: JSON.stringify(scriptData),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Script test timed out (1 minute). Please try again or optimize your script.');
      }
      throw error;
    }
  }

  async getExecutionStatus(executionId: string): Promise<{
    execution_id: string;
    status: string;
    output: string[];
    errors: string[];
    extracted_data: any[];
    execution_time: number;
    started_at: string;
    finished_at?: string;
  }> {
    return this.request(`/api/script/execution/${executionId}`);
  }

  async cancelExecution(executionId: string): Promise<void> {
    return this.request<void>(`/api/script/execution/${executionId}`, {
      method: 'DELETE',
    });
  }

  async exportExecutionData(executionId: string, format: 'json' | 'csv' | 'excel' | 'xml'): Promise<void> {
    const token = this.token || (typeof window !== 'undefined' ? localStorage.getItem('access_token') : null);
    const response = await fetch(`${this.baseURL}/api/script/execution/${executionId}/export/${format}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        console.warn('401 Unauthorized: Redirecting to login page');

        // トークンをクリア
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');

          // ログインページにリダイレクト
          window.location.href = '/login';
        }

        throw new Error('認証が必要です。ログインページにリダイレクトします。');
      }
      throw new Error(`Export failed: ${response.statusText}`);
    }

    // ファイルダウンロードを処理
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;

    // ファイル名をContent-Dispositionヘッダーから取得
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `scraped_data.${format}`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/);
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
    }

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  async getExecutionHistory(limit: number = 20): Promise<{
    history: Array<{
      execution_id: string;
      spider_name: string;
      status: string;
      start_urls: string[];
      extracted_count: number;
      execution_time: number;
      started_at: string;
      finished_at?: string;
    }>;
  }> {
    return this.request(`/api/script/history?limit=${limit}`);
  }

  // Script Management
  async saveScript(fileName: string, content: string): Promise<{ message: string; file_name: string; file_path: string }> {
    return this.request<{ message: string; file_name: string; file_path: string }>('/api/script/save', {
      method: 'POST',
      body: JSON.stringify({ file_name: fileName, content }),
    });
  }

  async getUserScripts(): Promise<{ files: Array<{ name: string; size: number; modified: string; path: string }> }> {
    return this.request<{ files: Array<{ name: string; size: number; modified: string; path: string }> }>('/api/script/files');
  }

  async getScriptContent(fileName: string): Promise<{ file_name: string; content: string }> {
    return this.request<{ file_name: string; content: string }>(`/api/script/files/${encodeURIComponent(fileName)}`);
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/api/projects/');
  }

  async getProject(id: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${id}`);
  }

  async createProject(projectData: {
    name: string;
    description?: string;
    path?: string;
    settings?: Record<string, any>;
  }): Promise<Project> {
    return this.request<Project>('/api/projects/', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  }

  async updateProject(id: string, projectData: Partial<Project>): Promise<Project> {
    return this.request<Project>(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });
  }

  async deleteProject(id: string): Promise<void> {
    return this.request<void>(`/api/projects/${id}`, {
      method: 'DELETE',
    });
  }

  // 手動同期メソッドは削除されました（自動同期により不要）

  // Spiders
  async getSpiders(projectId?: string): Promise<Spider[]> {
    const params = projectId ? `?project_id=${projectId}` : '';
    return this.request<Spider[]>(`/api/spiders/${params}`);
  }

  async getSpider(projectId: string, spiderId: string): Promise<Spider>;
  async getSpider(spiderId: string): Promise<Spider>;
  async getSpider(projectIdOrSpiderId: string, spiderId?: string): Promise<Spider> {
    // 2つのパラメータが渡された場合は、2番目のパラメータをスパイダーIDとして使用
    const id = spiderId || projectIdOrSpiderId;
    return this.request<Spider>(`/api/spiders/${id}`);
  }

  async createSpider(projectId: string, spiderData: {
    name: string;
    code: string;
    template?: string;
    project_id?: string;
    settings?: Record<string, any>;
  }): Promise<Spider> {
    return this.request<Spider>('/api/spiders/', {
      method: 'POST',
      body: JSON.stringify({
        name: spiderData.name,
        code: spiderData.code,
        template: spiderData.template,
        project_id: projectId,
        settings: spiderData.settings || {}
      }),
    });
  }

  async updateSpider(id: string, spiderData: Partial<Spider>): Promise<Spider> {
    return this.request<Spider>(`/api/spiders/${id}`, {
      method: 'PUT',
      body: JSON.stringify(spiderData),
    });
  }

  async deleteSpider(projectId: string, spiderId: string): Promise<void> {
    return this.request<void>(`/api/spiders/${spiderId}`, {
      method: 'DELETE',
    });
  }

  async runSpider(projectId: string, spiderId: string, settings?: Record<string, any>): Promise<Task> {
    return this.request<Task>('/api/tasks/', {
      method: 'POST',
      body: JSON.stringify({
        project_id: projectId,
        spider_id: spiderId,
        settings: settings || {}
      }),
    });
  }

  async stopTask(taskId: string): Promise<void> {
    return this.request<void>(`/api/tasks/${taskId}/stop`, {
      method: 'POST',
    });
  }

  async restartTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${taskId}/restart`, {
      method: 'POST',
    });
  }



  async getSpiderCode(id: string): Promise<{ code: string }> {
    return this.request<{ code: string }>(`/api/spiders/${id}/code`);
  }

  // Tasks
  async getTasks(filters?: {
    project_id?: string;
    spider_id?: string;
    status?: string;
    limit?: number;
    per_spider?: number;
  }): Promise<Task[]> {
    console.log('getTasks called with filters:', filters);
    console.log('Current token:', this.token ? 'Present' : 'Missing');

    const params = new URLSearchParams();
    if (filters?.project_id) params.append('project_id', filters.project_id);
    if (filters?.spider_id) params.append('spider_id', filters.spider_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.per_spider) params.append('per_spider', filters.per_spider.toString());

    const queryString = params.toString();
    const url = `/api/tasks/${queryString ? `?${queryString}` : ''}`;
    console.log('Request URL:', url);

    return this.request<Task[]>(url);
  }

  async getTask(id: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${id}`);
  }

  async createTask(taskData: {
    project_id: string;
    spider_id: string;
    log_level?: string;
    settings?: Record<string, any>;
  }): Promise<Task> {
    return this.request<Task>('/api/tasks/', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  async cancelTask(id: string): Promise<void> {
    return this.request<void>(`/api/tasks/${id}/cancel`, {
      method: 'POST',
    });
  }

  async runSpider(projectId: string, spiderId: string, settings?: Record<string, any>): Promise<Task> {
    console.log(`🚀 Running spider via API: projectId=${projectId}, spiderId=${spiderId}`);
    return this.createTask({
      project_id: projectId,
      spider_id: spiderId,
      settings: settings || {}
    });
  }

  // Watchdog監視付きスパイダー実行
  async runSpiderWithWatchdog(
    projectId: string,
    spiderId: string,
    request: { settings?: Record<string, any> } = {}
  ): Promise<{
    task_id: string;
    celery_task_id: string;
    status: string;
    monitoring: string;
    spider_name: string;
    project_name: string;
    message: string;
  }> {
    console.log(`🐕 Running spider with watchdog monitoring: projectId=${projectId}, spiderId=${spiderId}`);
    return this.request<{
      task_id: string;
      celery_task_id: string;
      status: string;
      monitoring: string;
      spider_name: string;
      project_name: string;
      message: string;
    }>(`/api/spiders/${spiderId}/run-with-watchdog?project_id=${projectId}`, {
      method: 'POST',
      body: JSON.stringify({
        settings: request.settings || {}
      }),
    });
  }

  // カスタムScrapyラッパー実行
  async runSpiderWrapper(
    projectId: string,
    spiderName: string,
    options: {
      items?: number;
      timeout?: number;
      no_cache?: boolean;
      debug?: boolean;
    } = {}
  ): Promise<any> {
    const params = new URLSearchParams();
    if (options.items !== undefined) params.append('items', options.items.toString());
    if (options.timeout !== undefined) params.append('timeout', options.timeout.toString());
    if (options.no_cache !== undefined) params.append('no_cache', options.no_cache.toString());
    if (options.debug !== undefined) params.append('debug', options.debug.toString());

    const url = `/api/tasks/run-wrapper/${projectId}/${spiderName}${params.toString() ? '?' + params.toString() : ''}`;

    console.log(`🕷️ Running spider wrapper: ${url}`);

    return this.request(url, {
      method: 'POST'
    });
  }

  async getTaskLogs(taskId: string, limit: number = 100): Promise<any[]> {
    return this.request<any[]>(`/api/tasks/${taskId}/logs?limit=${limit}`);
  }

  async getTaskProgress(taskId: string): Promise<any> {
    return this.request<any>(`/api/tasks/${taskId}/progress`);
  }

  // Results
  async getResults(params?: { project_id?: string; spider_id?: string; task_id?: string }): Promise<Result[]> {
    const queryParams = new URLSearchParams();
    if (params?.project_id) queryParams.append('project_id', params.project_id);
    if (params?.spider_id) queryParams.append('spider_id', params.spider_id);
    if (params?.task_id) queryParams.append('task_id', params.task_id);

    const url = `/api/results/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.request<Result[]>(url);
  }

  async getResult(id: string): Promise<Result> {
    return this.request<Result>(`/api/results/${id}`);
  }

  async downloadResult(resultId: string): Promise<Blob> {
    const headers: HeadersInit = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseURL}/api/results/${resultId}/download`, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.blob();
  }

  async downloadTaskResults(taskId: string, format: 'json' | 'jsonl' | 'csv' | 'excel' | 'xml'): Promise<Blob> {
    const headers: HeadersInit = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseURL}/api/tasks/${taskId}/results/download?format=${format}`, {
      headers,
    });

    if (!response.ok) {
      // より詳細なエラー情報を取得
      let errorMessage = `HTTP error! status: ${response.status}`;

      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = errorData.detail;

          // Task info が含まれている場合は整形して表示
          if (errorMessage.includes('Task info:')) {
            const taskInfoStart = errorMessage.indexOf('Task info:');
            const jsonStart = errorMessage.indexOf('{', taskInfoStart);
            if (jsonStart !== -1) {
              // JSON部分を抽出（改行文字も考慮）
              let jsonPart = errorMessage.substring(jsonStart);

              // JSONの終了位置を見つける（ネストしたオブジェクトに対応）
              let braceCount = 0;
              let endIndex = -1;
              for (let i = 0; i < jsonPart.length; i++) {
                if (jsonPart[i] === '{') braceCount++;
                if (jsonPart[i] === '}') {
                  braceCount--;
                  if (braceCount === 0) {
                    endIndex = i + 1;
                    break;
                  }
                }
              }

              if (endIndex > 0) {
                jsonPart = jsonPart.substring(0, endIndex);
              }

              try {
                const taskInfo = JSON.parse(jsonPart);
                console.error('Task download error details:', taskInfo);

                // タスク情報が有効かチェック
                if (taskInfo && typeof taskInfo === 'object' && Object.keys(taskInfo).length > 0) {
                  // ユーザーフレンドリーなエラーメッセージを作成
                  if (taskInfo.task_status === 'FAILED') {
                    errorMessage = `タスクが失敗しているため、結果ファイルをダウンロードできません。\nタスク状態: ${taskInfo.task_status}\nアイテム数: ${taskInfo.items_count || 0}\nエラー数: ${taskInfo.error_count || 0}`;
                  } else if (taskInfo.task_status) {
                    errorMessage = `結果ファイルが見つかりません。\nタスク状態: ${taskInfo.task_status}\nアイテム数: ${taskInfo.items_count || 0}`;
                  } else {
                    // タスク情報が不完全な場合
                    errorMessage = `結果ファイルが見つかりません。タスクの詳細情報を確認してください。`;
                  }
                } else {
                  // 空のオブジェクトまたは無効なデータの場合
                  console.warn('Empty or invalid task info received');
                  errorMessage = `結果ファイルが見つかりません。タスクが正常に完了していない可能性があります。`;
                }
              } catch (parseError) {
                // JSON解析に失敗した場合
                console.warn('Failed to parse task info JSON:', parseError);

                // JSONパースエラーの詳細を確認
                if (parseError instanceof SyntaxError && parseError.message.includes('Extra data')) {
                  errorMessage = `結果ファイルの形式が不正です。\nJSONファイルに余分なデータが含まれています。\n詳細: ${parseError.message}`;
                } else if (parseError instanceof SyntaxError && parseError.message.includes('Unterminated')) {
                  errorMessage = `結果ファイルの形式が不正です。\nJSONファイルが不完全です。\n詳細: ${parseError.message}`;
                } else {
                  errorMessage = `結果ファイルが見つかりません。詳細なエラー情報の解析に失敗しました。\n詳細: ${parseError.message}`;
                }
              }
            }
          }
        }
      } catch (e) {
        // レスポンスがJSONでない場合は元のエラーメッセージを使用
      }

      throw new Error(errorMessage);
    }

    return response.blob();
  }

  async downloadTaskResultsFile(taskId: string, format: 'jsonl' = 'jsonl'): Promise<Blob> {
    const headers: HeadersInit = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseURL}/api/tasks/${taskId}/results/download-file?format=${format}`, {
      headers,
    });

    if (!response.ok) {
      // より詳細なエラー情報を取得
      let errorMessage = `HTTP error! status: ${response.status}`;

      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (e) {
        // JSON解析に失敗した場合はデフォルトメッセージを使用
      }

      throw new Error(errorMessage);
    }

    return response.blob();
  }

  // Project Files
  async getProjectFiles(projectId: string): Promise<any[]> {
    return this.request<any[]>(`/api/projects/${projectId}/files/`);
  }

  async getProjectFile(projectId: string, filePath: string): Promise<any> {
    return this.request<any>(`/api/projects/${projectId}/files/${encodeURIComponent(filePath)}`);
  }

  async updateProjectFile(projectId: string, filePath: string, content: string): Promise<any> {
    return this.request<any>(`/api/projects/${projectId}/files/${encodeURIComponent(filePath)}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async createProjectFile(projectId: string, filePath: string, content: string): Promise<any> {
    return this.request<any>(`/api/projects/${projectId}/files/`, {
      method: 'POST',
      body: JSON.stringify({ path: filePath, content }),
    });
  }

  async deleteProjectFile(projectId: string, filePath: string): Promise<void> {
    return this.request<void>(`/api/projects/${projectId}/files/${encodeURIComponent(filePath)}`, {
      method: 'DELETE',
    });
  }

  async exportResults(taskId: string, format: 'json' | 'csv' | 'excel' | 'xml'): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/api/results/export/${taskId}?format=${format}`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  }

  // Notifications
  async getNotifications(): Promise<Notification[]> {
    return this.request<Notification[]>('/api/notifications/');
  }

  async markNotificationAsRead(id: string): Promise<void> {
    return this.request<void>(`/api/notifications/${id}/read`, {
      method: 'POST',
    });
  }

  async markAllNotificationsAsRead(): Promise<void> {
    return this.request<void>('/api/notifications/mark-all-read', {
      method: 'POST',
    });
  }

  async deleteNotification(id: string): Promise<void> {
    return this.request<void>(`/api/notifications/${id}`, {
      method: 'DELETE',
    });
  }

  // Proxies
  async getProxies(): Promise<Proxy[]> {
    return this.request<Proxy[]>('/api/proxies/');
  }

  async getProxy(id: string): Promise<Proxy> {
    return this.request<Proxy>(`/api/proxies/${id}`);
  }

  async createProxy(proxyData: {
    name: string;
    host: string;
    port: number;
    username?: string;
    password?: string;
    proxy_type: 'http' | 'https' | 'socks4' | 'socks5';
  }): Promise<Proxy> {
    return this.request<Proxy>('/api/proxies/', {
      method: 'POST',
      body: JSON.stringify(proxyData),
    });
  }

  async updateProxy(id: string, proxyData: Partial<Proxy>): Promise<Proxy> {
    return this.request<Proxy>(`/api/proxies/${id}`, {
      method: 'PUT',
      body: JSON.stringify(proxyData),
    });
  }

  async deleteProxy(id: string): Promise<void> {
    return this.request<void>(`/api/proxies/${id}`, {
      method: 'DELETE',
    });
  }

  async testProxy(id: string): Promise<{ success: boolean; response_time?: number; error?: string }> {
    return this.request<{ success: boolean; response_time?: number; error?: string }>(`/api/proxies/${id}/test`, {
      method: 'POST',
    });
  }

  // Schedules
  async getSchedules(): Promise<Schedule[]> {
    return this.request<Schedule[]>('/api/schedules/');
  }

  async getSchedule(id: string): Promise<Schedule> {
    return this.request<Schedule>(`/api/schedules/${id}`);
  }

  async createSchedule(scheduleData: {
    name: string;
    description?: string;
    cron_expression: string;
    project_id: string;
    spider_id: string;
    settings?: Record<string, any>;
  }): Promise<Schedule> {
    return this.request<Schedule>('/api/schedules/', {
      method: 'POST',
      body: JSON.stringify(scheduleData),
    });
  }

  async updateSchedule(id: string, scheduleData: Partial<Schedule>): Promise<Schedule> {
    return this.request<Schedule>(`/api/schedules/${id}`, {
      method: 'PUT',
      body: JSON.stringify(scheduleData),
    });
  }

  async deleteSchedule(id: string): Promise<void> {
    return this.request<void>(`/api/schedules/${id}`, {
      method: 'DELETE',
    });
  }

  // AI Analysis
  async suggestSpider(url: string): Promise<{ code: string; suggestions: string[] }> {
    return this.request<{ code: string; suggestions: string[] }>('/api/ai/suggest-spider', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  }

  async analyzeResults(taskId: string, analysisType: 'comprehensive' | 'performance' | 'quality'): Promise<{
    analysis_type: string;
    insights: string[];
    recommendations: string[];
    charts?: any[];
  }> {
    return this.request<{
      analysis_type: string;
      insights: string[];
      recommendations: string[];
      charts?: any[];
    }>(`/api/ai/analyze-results/${taskId}`, {
      method: 'POST',
      body: JSON.stringify({ analysis_type: analysisType }),
    });
  }

  // Scrapy Shell
  async executeShellCommand(command: string, url?: string, projectId?: string): Promise<{
    output: string;
    error?: string;
    status: string;
    timestamp: string;
  }> {
    return this.request<{
      output: string;
      error?: string;
      status: string;
      timestamp: string;
    }>('/api/shell/execute', {
      method: 'POST',
      body: JSON.stringify({
        command,
        url,
        project_id: projectId
      }),
    });
  }

  async getShellSessions(): Promise<{ sessions: Record<string, any> }> {
    return this.request<{ sessions: Record<string, any> }>('/api/shell/sessions');
  }

  async closeShellSession(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/shell/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Database Configuration
  async getDatabaseConfig(): Promise<any> {
    return this.request<any>('/api/database/config');
  }

  async getAllDatabaseConfigs(): Promise<any> {
    return this.request<any>('/api/database/configs');
  }

  async getDatabaseHealth(): Promise<any> {
    return this.request<any>('/api/database/health');
  }

  async getDatabaseStatistics(): Promise<any> {
    return this.request<any>('/api/database/statistics');
  }

  async getSupportedDatabaseTypes(): Promise<string[]> {
    return this.request<string[]>('/api/database/types');
  }

  async testDatabaseConnection(config: any): Promise<any> {
    return this.request<any>('/api/database/test-connection', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async backupDatabase(): Promise<any> {
    return this.request<any>('/api/database/backup', {
      method: 'POST',
    });
  }

  async clearDatabaseCache(): Promise<any> {
    return this.request<any>('/api/database/cache', {
      method: 'DELETE',
    });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }

  // Sharing and Team Management
  async shareProject(shareData: {
    project_id: string;
    target_type: string;
    target_identifier: string;
    permission: string;
    expires_days?: number;
  }): Promise<{ message: string; share_id: string }> {
    return this.request<{ message: string; share_id: string }>('/api/projects/share', {
      method: 'POST',
      body: JSON.stringify(shareData),
    });
  }

  async getSharedProjects(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    owner_name: string;
    permission: string;
    shared_via: string;
    created_at: string;
  }>> {
    return this.request<Array<{
      id: string;
      name: string;
      description: string;
      owner_name: string;
      permission: string;
      shared_via: string;
      created_at: string;
    }>>('/api/projects/shared');
  }

  async createTeam(teamData: {
    name: string;
    description?: string;
  }): Promise<{ message: string; team_id: string }> {
    return this.request<{ message: string; team_id: string }>('/api/teams', {
      method: 'POST',
      body: JSON.stringify(teamData),
    });
  }

  async getTeams(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    owner_id: string;
    my_role: string;
    created_at: string;
  }>> {
    return this.request<Array<{
      id: string;
      name: string;
      description: string;
      owner_id: string;
      my_role: string;
      created_at: string;
    }>>('/api/teams');
  }

  async addTeamMember(teamId: string, memberData: {
    user_email: string;
    role: string;
  }): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/teams/${teamId}/members`, {
      method: 'POST',
      body: JSON.stringify(memberData),
    });
  }

  // Convenience methods for HTTP verbs
  async get<T>(endpoint: string, options?: RequestInit): Promise<{ data: T }> {
    const result = await this.request<T>(endpoint, { ...options, method: 'GET' });
    return { data: result };
  }

  async post<T>(endpoint: string, data?: any, options?: RequestInit): Promise<{ data: T }> {
    const result = await this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    return { data: result };
  }

  async put<T>(endpoint: string, data?: any, options?: RequestInit): Promise<{ data: T }> {
    const result = await this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
    return { data: result };
  }

  async delete<T>(endpoint: string, options?: RequestInit): Promise<{ data: T }> {
    const result = await this.request<T>(endpoint, { ...options, method: 'DELETE' });
    return { data: result };
  }

  // Command execution
  async executeCommand(commandData: {
    command: string;
    working_directory?: string;
    timeout?: number;
  }): Promise<{
    output: string;
    error?: string;
    exit_code: number;
  }> {
    // Set timeout based on command type
    const isScrapyCrawl = commandData.command.startsWith('scrapy crawl');
    const defaultTimeout = isScrapyCrawl ? 300000 : 30000; // 5 minutes for scrapy crawl, 30 seconds for others
    const timeout = commandData.timeout || defaultTimeout;

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const result = await this.request<{
        output: string;
        error?: string;
        exit_code: number;
      }>('/api/nodejs/execute', {
        method: 'POST',
        body: JSON.stringify({
          ...commandData,
          timeout: timeout
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Command timed out after ${timeout / 1000} seconds`);
      }
      throw error;
    }
  }
}

// Export singleton instance with direct backend connection
export const apiClient = new ApiClient('http://localhost:8000');
