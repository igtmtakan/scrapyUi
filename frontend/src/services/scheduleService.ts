import { apiClient } from '../lib/api';

// Task interface for latest_task
export interface LatestTask {
  id: string;
  status: string;
  items_count: number;
  requests_count: number;
  error_count: number;
  started_at?: string;
  finished_at?: string;
  created_at: string;
}

// Task interface for schedule history
export interface ScheduleTask {
  id: string;
  status: string;
  items_count: number;
  requests_count: number;
  error_count: number;
  started_at?: string;
  finished_at?: string;
  created_at: string;
  updated_at?: string;
  log_level: string;
  settings?: Record<string, any>;
  celery_task_id?: string;
  error_message?: string;
}

// Schedule tasks response
export interface ScheduleTasksResponse {
  tasks: ScheduleTask[];
  total_count: number;
  limit: number;
  offset: number;
  schedule_id: string;
}

// Schedule interfaces
export interface Schedule {
  id: string;
  name: string;
  description?: string;
  cron_expression: string;
  interval_minutes?: number;
  is_active: boolean;
  project_id: string;
  spider_id: string;
  project_name?: string;
  spider_name?: string;
  last_run?: string;
  next_run?: string;
  created_at?: string;
  updated_at?: string;
  settings?: Record<string, any>;
  run_count?: number;
  success_count?: number;
  failure_count?: number;
  latest_task?: LatestTask;
}

export interface ScheduleCreate {
  name: string;
  description?: string;
  cron_expression: string;
  project_id: string;
  spider_id: string;
  is_active?: boolean;
  settings?: Record<string, any>;
}

export interface ScheduleUpdate {
  name?: string;
  description?: string;
  cron_expression?: string;
  is_active?: boolean;
  settings?: Record<string, any>;
}

export interface ScheduleRunResponse {
  message: string;
  task_id: string;
  schedule_id: string;
  realtime?: boolean;
  command?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
}

export interface Spider {
  id: string;
  name: string;
  project_id: string;
  description?: string;
}

class ScheduleService {
  // スケジュール一覧取得
  async getSchedules(forceRefresh?: boolean, projectId?: string, isActive?: boolean): Promise<Schedule[]> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (isActive !== undefined) params.append('is_active', isActive.toString());

    // キャッシュ無効化のためのタイムスタンプを追加
    if (forceRefresh) {
      params.append('_t', new Date().getTime().toString());
    }

    const config = forceRefresh ? {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    } : {};

    console.log('📡 scheduleService: API呼び出し開始')
    console.log('📡 URL:', `/api/schedules/?${params.toString()}`)
    console.log('📡 Config:', config)

    const response = await apiClient.get<Schedule[]>(`/api/schedules/?${params.toString()}`, config);

    console.log('📡 scheduleService: APIレスポンス受信')
    console.log('📡 Response:', response)
    console.log('📡 Response.data:', response.data)
    console.log('📡 Response.data type:', typeof response.data)
    console.log('📡 Response.data length:', Array.isArray(response.data) ? response.data.length : 'Not an array')

    return response.data;
  }

  // スケジュール詳細取得
  async getSchedule(scheduleId: string): Promise<Schedule> {
    try {
      console.log('📡 scheduleService: getSchedule呼び出し', scheduleId);
      const response = await apiClient.get<Schedule>(`/api/schedules/${scheduleId}`);
      console.log('📡 scheduleService: getScheduleレスポンス', response);
      return response.data;
    } catch (error) {
      console.error('❌ scheduleService: getScheduleエラー', {
        scheduleId,
        error: error instanceof Error ? error.message : String(error),
        errorType: error?.constructor?.name
      });
      throw error;
    }
  }

  // スケジュール作成
  async createSchedule(schedule: ScheduleCreate): Promise<Schedule> {
    const response = await apiClient.post<Schedule>('/api/schedules/', schedule);
    return response.data;
  }

  // スケジュール更新
  async updateSchedule(scheduleId: string, schedule: ScheduleUpdate): Promise<Schedule> {
    const response = await apiClient.put<Schedule>(`/api/schedules/${scheduleId}`, schedule);
    return response.data;
  }

  // スケジュール削除
  async deleteSchedule(scheduleId: string): Promise<void> {
    await apiClient.delete(`/api/schedules/${scheduleId}`);
  }

  // スケジュール即座実行
  async runSchedule(scheduleId: string): Promise<ScheduleRunResponse> {
    const response = await apiClient.post<ScheduleRunResponse>(`/api/schedules/${scheduleId}/run`);
    return response.data;
  }

  // スケジュール有効/無効切り替え
  async toggleSchedule(scheduleId: string): Promise<Schedule> {
    console.log('📡 scheduleService: toggleSchedule呼び出し', scheduleId)
    const response = await apiClient.post<Schedule>(`/api/schedules/${scheduleId}/toggle`);
    console.log('📡 scheduleService: toggleScheduleレスポンス', response)
    return response.data;
  }

  // スケジュール実行履歴取得
  async getScheduleTasks(
    scheduleId: string,
    limit: number = 20,
    offset: number = 0,
    status?: string
  ): Promise<ScheduleTasksResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    if (status) params.append('status', status);

    const response = await apiClient.get<ScheduleTasksResponse>(
      `/api/schedules/${scheduleId}/tasks?${params.toString()}`
    );
    return response.data;
  }

  // プロジェクト一覧取得
  async getProjects(): Promise<Project[]> {
    const response = await apiClient.get<Project[]>('/api/projects/');
    return response.data;
  }

  // スパイダー一覧取得
  async getSpiders(projectId?: string): Promise<Spider[]> {
    if (projectId) {
      // プロジェクトIDが指定された場合はクエリパラメータで取得
      const response = await apiClient.get<Spider[]>(`/api/spiders/?project_id=${projectId}`);
      return response.data;
    } else {
      // プロジェクトIDが指定されていない場合は全スパイダーを取得
      const response = await apiClient.get<Spider[]>('/api/spiders/');
      return response.data;
    }
  }

  // 待機タスク数取得
  async getPendingTasksCount(): Promise<number> {
    const response = await apiClient.get<{count: number}>('/api/schedules/pending-tasks/count');
    return response.data.count;
  }

  // タスクリセット
  async resetTasks(): Promise<{message: string; cleared_count: number}> {
    console.log('📡 scheduleService: resetTasks呼び出し')
    const response = await apiClient.post<{message: string; cleared_count: number}>('/api/tasks/reset');
    console.log('📡 scheduleService: resetTasksレスポンス', response)
    return response.data;
  }

  // タスククリア（DELETE版）
  async clearTasks(): Promise<{message: string; cleared_count: number}> {
    console.log('📡 scheduleService: clearTasks呼び出し')
    const response = await apiClient.delete<{message: string; cleared_count: number}>('/api/tasks/clear');
    console.log('📡 scheduleService: clearTasksレスポンス', response)
    return response.data;
  }

  // Cron式の説明を取得
  formatCronExpression(cron: string): string {
    const cronDescriptions: { [key: string]: string } = {
      '0 0 * * *': '毎日深夜0時',
      '0 6 * * *': '毎日午前6時',
      '0 12 * * *': '毎日正午',
      '0 18 * * *': '毎日午後6時',
      '0 */2 * * *': '2時間ごと',
      '0 */4 * * *': '4時間ごと',
      '0 */6 * * *': '6時間ごと',
      '0 */12 * * *': '12時間ごと',
      '*/5 * * * *': '5分ごと',
      '*/7 * * * *': '7分ごと',
      '*/15 * * * *': '15分ごと',
      '*/20 * * * *': '20分ごと (毎時0分、20分、40分)',
      '*/25 * * * *': '25分ごと (毎時0分、25分、50分)',
      '*/30 * * * *': '30分ごと',
      '*/40 * * * *': '40分ごと (毎時0分、40分)',
      '0 9 * * 1': '毎週月曜日午前9時',
      '0 9 * * 1-5': '平日午前9時',
      '0 0 1 * *': '毎月1日深夜0時',
      '0 0 * * 0': '毎週日曜日深夜0時'
    };

    return cronDescriptions[cron] || cron;
  }

  // 次回実行時刻を計算
  calculateNextRun(cronExpression: string): Date | null {
    try {
      // 簡単な計算（実際にはcroniterライブラリを使用）
      const now = new Date();
      const parts = cronExpression.split(' ');

      if (parts.length !== 5) return null;

      const [minute, hour, day, month, dayOfWeek] = parts;

      // 簡単な例：毎日の場合
      if (day === '*' && month === '*' && dayOfWeek === '*') {
        const nextRun = new Date(now);
        nextRun.setHours(parseInt(hour) || 0);
        nextRun.setMinutes(parseInt(minute) || 0);
        nextRun.setSeconds(0);
        nextRun.setMilliseconds(0);

        if (nextRun <= now) {
          nextRun.setDate(nextRun.getDate() + 1);
        }

        return nextRun;
      }

      return null;
    } catch (error) {
      console.error('Error calculating next run:', error);
      return null;
    }
  }

  // Cron式の検証
  validateCronExpression(cron: string): { isValid: boolean; error?: string } {
    try {
      const parts = cron.trim().split(/\s+/);

      if (parts.length !== 5) {
        return {
          isValid: false,
          error: 'Cron式は5つの部分（分 時 日 月 曜日）で構成される必要があります'
        };
      }

      const [minute, hour, day, month, dayOfWeek] = parts;

      // 基本的な検証
      if (!this.isValidCronField(minute, 0, 59)) {
        return { isValid: false, error: '分は0-59の範囲で指定してください' };
      }

      if (!this.isValidCronField(hour, 0, 23)) {
        return { isValid: false, error: '時は0-23の範囲で指定してください' };
      }

      if (!this.isValidCronField(day, 1, 31)) {
        return { isValid: false, error: '日は1-31の範囲で指定してください' };
      }

      if (!this.isValidCronField(month, 1, 12)) {
        return { isValid: false, error: '月は1-12の範囲で指定してください' };
      }

      if (!this.isValidCronField(dayOfWeek, 0, 7)) {
        return { isValid: false, error: '曜日は0-7の範囲で指定してください' };
      }

      return { isValid: true };
    } catch (error) {
      return {
        isValid: false,
        error: 'Cron式の形式が正しくありません'
      };
    }
  }

  private isValidCronField(field: string, min: number, max: number): boolean {
    if (field === '*') return true;

    // 範囲指定 (例: 1-5)
    if (field.includes('-')) {
      const [start, end] = field.split('-').map(Number);
      return start >= min && end <= max && start <= end;
    }

    // ステップ指定 (例: */2)
    if (field.includes('/')) {
      const [range, step] = field.split('/');
      const stepNum = Number(step);
      if (isNaN(stepNum) || stepNum <= 0) return false;

      if (range === '*') return true;
      return this.isValidCronField(range, min, max);
    }

    // リスト指定 (例: 1,3,5)
    if (field.includes(',')) {
      const values = field.split(',').map(Number);
      return values.every(val => val >= min && val <= max);
    }

    // 単一値
    const num = Number(field);
    return !isNaN(num) && num >= min && num <= max;
  }

  // 一般的なCron式のテンプレート
  getCronTemplates() {
    return [
      { label: '毎分', value: '* * * * *', description: '毎分実行' },
      { label: '5分ごと', value: '*/5 * * * *', description: '5分間隔で実行' },
      { label: '15分ごと', value: '*/15 * * * *', description: '15分間隔で実行' },
      { label: '30分ごと', value: '*/30 * * * *', description: '30分間隔で実行' },
      { label: '毎時', value: '0 * * * *', description: '毎時0分に実行' },
      { label: '2時間ごと', value: '0 */2 * * *', description: '2時間間隔で実行' },
      { label: '4時間ごと', value: '0 */4 * * *', description: '4時間間隔で実行' },
      { label: '6時間ごと', value: '0 */6 * * *', description: '6時間間隔で実行' },
      { label: '毎日深夜', value: '0 0 * * *', description: '毎日深夜0時に実行' },
      { label: '毎日午前6時', value: '0 6 * * *', description: '毎日午前6時に実行' },
      { label: '毎日正午', value: '0 12 * * *', description: '毎日正午に実行' },
      { label: '毎日午後6時', value: '0 18 * * *', description: '毎日午後6時に実行' },
      { label: '平日午前9時', value: '0 9 * * 1-5', description: '月曜日から金曜日の午前9時に実行' },
      { label: '毎週月曜日', value: '0 9 * * 1', description: '毎週月曜日午前9時に実行' },
      { label: '毎月1日', value: '0 0 1 * *', description: '毎月1日深夜0時に実行' }
    ];
  }
}

export const scheduleService = new ScheduleService();
