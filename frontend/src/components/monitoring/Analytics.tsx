'use client';

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  Activity,
  Clock,
  Database,
  TrendingUp,
  BarChart3,
  PieChart,
  Calendar,
  Globe
} from 'lucide-react';

// Chart.jsの登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
);

interface AnalyticsData {
  totalTasks: number;
  activeTasks: number;
  totalResults: number;
  successRate: number;
  systemLoad: number;
  taskTrends: Array<{ date: string; tasks: number; success: number; failed: number }>;
  statusDistribution: Array<{ status: string; count: number; color: string }>;
  spiderPerformance: Array<{ spider: string; successRate: number; totalTasks: number }>;
  dailyVolume: Array<{ date: string; items: number; requests: number }>;
  topDomains: Array<{ domain: string; count: number }>;
  recentActivity: Array<{
    id: string;
    type: string;
    status: string;
    message: string;
    time: string;
  }>;
}

export default function Analytics() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>({
    totalTasks: 0,
    activeTasks: 0,
    totalResults: 0,
    successRate: 0,
    systemLoad: 0,
    taskTrends: [],
    statusDistribution: [],
    spiderPerformance: [],
    dailyVolume: [],
    topDomains: [],
    recentActivity: []
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadAnalyticsData();
    const interval = setInterval(loadAnalyticsData, 30000); // 30秒ごと更新
    return () => clearInterval(interval);
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);

      // タスクデータを取得
      const tasksResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tasks/`);
      const tasks = await tasksResponse.json();

      // 結果データを取得
      const resultsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/results/`);
      const results = await resultsResponse.json();

      // データを分析
      const analytics = analyzeData(tasks, results);
      setAnalyticsData(analytics);

    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeData = (tasks: any[], results: any[]): AnalyticsData => {
    const totalTasks = tasks.length;
    const activeTasks = tasks.filter(t => t.status === 'RUNNING').length;
    const totalResults = results.length;
    const successfulTasks = tasks.filter(t => t.status === 'FINISHED').length;
    const successRate = totalTasks > 0 ? Math.round((successfulTasks / totalTasks) * 100) : 0;

    // タスクトレンド（過去7日間）
    const taskTrends = generateTaskTrends(tasks);

    // ステータス分布
    const statusDistribution = [
      { status: 'FINISHED', count: tasks.filter(t => t.status === 'FINISHED').length, color: '#10B981' },
      { status: 'RUNNING', count: tasks.filter(t => t.status === 'RUNNING').length, color: '#F59E0B' },
      { status: 'FAILED', count: tasks.filter(t => t.status === 'FAILED').length, color: '#EF4444' },
      { status: 'PENDING', count: tasks.filter(t => t.status === 'PENDING').length, color: '#6B7280' },
      { status: 'CANCELLED', count: tasks.filter(t => t.status === 'CANCELLED').length, color: '#8B5CF6' }
    ].filter(item => item.count > 0);

    // スパイダーパフォーマンス
    const spiderPerformance = generateSpiderPerformance(tasks);

    // 日次ボリューム
    const dailyVolume = generateDailyVolume(tasks);

    // トップドメイン
    const topDomains = generateTopDomains(results);

    // 最近のアクティビティ
    const recentActivity = generateRecentActivity(tasks);

    return {
      totalTasks,
      activeTasks,
      totalResults,
      successRate,
      systemLoad: Math.floor(Math.random() * 30) + 20, // モック値
      taskTrends,
      statusDistribution,
      spiderPerformance,
      dailyVolume,
      topDomains,
      recentActivity
    };
  };

  const generateTaskTrends = (tasks: any[]) => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split('T')[0];
    });

    return last7Days.map(date => {
      const dayTasks = tasks.filter(t => t.created_at?.startsWith(date));
      return {
        date: new Date(date).toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' }),
        tasks: dayTasks.length,
        success: dayTasks.filter(t => t.status === 'FINISHED').length,
        failed: dayTasks.filter(t => t.status === 'FAILED').length
      };
    });
  };

  const generateSpiderPerformance = (tasks: any[]) => {
    const spiderStats = tasks.reduce((acc, task) => {
      const spiderName = task.spider?.name || 'Unknown';
      if (!acc[spiderName]) {
        acc[spiderName] = { total: 0, success: 0 };
      }
      acc[spiderName].total++;
      if (task.status === 'FINISHED') {
        acc[spiderName].success++;
      }
      return acc;
    }, {} as Record<string, { total: number; success: number }>);

    return Object.entries(spiderStats)
      .map(([spider, stats]) => ({
        spider,
        successRate: stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0,
        totalTasks: stats.total
      }))
      .sort((a, b) => b.totalTasks - a.totalTasks)
      .slice(0, 5);
  };

  const generateDailyVolume = (tasks: any[]) => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split('T')[0];
    });

    return last7Days.map(date => {
      const dayTasks = tasks.filter(t => t.created_at?.startsWith(date));
      return {
        date: new Date(date).toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' }),
        items: dayTasks.reduce((sum, t) => sum + (t.items_count || 0), 0),
        requests: dayTasks.reduce((sum, t) => sum + (t.requests_count || 0), 0)
      };
    });
  };

  const generateTopDomains = (results: any[]) => {
    const domainCounts = results.reduce((acc, result) => {
      try {
        const url = result.data?.url || result.url;
        if (url) {
          const domain = new URL(url).hostname;
          acc[domain] = (acc[domain] || 0) + 1;
        }
      } catch (e) {
        // Invalid URL
      }
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(domainCounts)
      .map(([domain, count]) => ({ domain, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  };

  const generateRecentActivity = (tasks: any[]) => {
    return tasks
      .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
      .slice(0, 5)
      .map(task => ({
        id: task.id,
        type: 'task',
        status: task.status,
        message: `${task.spider?.name || 'Unknown'} - ${task.status}`,
        time: new Date(task.created_at || 0).toLocaleString('ja-JP')
      }));
  };

  // チャートオプション
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#D1D5DB'
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#9CA3AF'
        },
        grid: {
          color: '#374151'
        }
      },
      y: {
        ticks: {
          color: '#9CA3AF'
        },
        grid: {
          color: '#374151'
        }
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#D1D5DB',
          padding: 20
        }
      }
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 overflow-y-auto">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 overflow-y-auto">
      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Tasks</p>
              <p className="text-2xl font-bold text-white">{analyticsData.totalTasks}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Active Tasks</p>
              <p className="text-2xl font-bold text-white">{analyticsData.activeTasks}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Results</p>
              <p className="text-2xl font-bold text-white">{analyticsData.totalResults.toLocaleString()}</p>
            </div>
            <Database className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Success Rate</p>
              <p className="text-2xl font-bold text-white">{analyticsData.successRate}%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* チャートエリア */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* タスクトレンドチャート */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center mb-4">
            <BarChart3 className="w-5 h-5 text-blue-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">タスクトレンド（過去7日間）</h3>
          </div>
          <div className="h-64">
            <Bar
              data={{
                labels: analyticsData.taskTrends.map(d => d.date),
                datasets: [
                  {
                    label: '成功',
                    data: analyticsData.taskTrends.map(d => d.success),
                    backgroundColor: '#10B981',
                    borderColor: '#059669',
                    borderWidth: 1
                  },
                  {
                    label: '失敗',
                    data: analyticsData.taskTrends.map(d => d.failed),
                    backgroundColor: '#EF4444',
                    borderColor: '#DC2626',
                    borderWidth: 1
                  }
                ]
              }}
              options={chartOptions}
            />
          </div>
        </div>

        {/* タスクステータス分布 */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center mb-4">
            <PieChart className="w-5 h-5 text-green-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">タスクステータス分布</h3>
          </div>
          <div className="h-64">
            <Doughnut
              data={{
                labels: analyticsData.statusDistribution.map(d => d.status),
                datasets: [
                  {
                    data: analyticsData.statusDistribution.map(d => d.count),
                    backgroundColor: analyticsData.statusDistribution.map(d => d.color),
                    borderColor: '#1F2937',
                    borderWidth: 2
                  }
                ]
              }}
              options={doughnutOptions}
            />
          </div>
        </div>
      </div>

      {/* 追加チャート */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* スパイダー成功率 */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center mb-4">
            <Activity className="w-5 h-5 text-purple-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">スパイダー成功率</h3>
          </div>
          <div className="h-64">
            <Bar
              data={{
                labels: analyticsData.spiderPerformance.map(d => d.spider.length > 10 ? d.spider.substring(0, 10) + '...' : d.spider),
                datasets: [
                  {
                    label: '成功率 (%)',
                    data: analyticsData.spiderPerformance.map(d => d.successRate),
                    backgroundColor: '#8B5CF6',
                    borderColor: '#7C3AED',
                    borderWidth: 1
                  }
                ]
              }}
              options={{
                ...chartOptions,
                scales: {
                  ...chartOptions.scales,
                  y: {
                    ...chartOptions.scales.y,
                    max: 100
                  }
                }
              }}
            />
          </div>
        </div>

        {/* 日次ボリューム */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center mb-4">
            <Calendar className="w-5 h-5 text-yellow-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">日次ボリューム</h3>
          </div>
          <div className="h-64">
            <Line
              data={{
                labels: analyticsData.dailyVolume.map(d => d.date),
                datasets: [
                  {
                    label: 'アイテム数',
                    data: analyticsData.dailyVolume.map(d => d.items),
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4
                  },
                  {
                    label: 'リクエスト数',
                    data: analyticsData.dailyVolume.map(d => d.requests),
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                  }
                ]
              }}
              options={chartOptions}
            />
          </div>
        </div>

        {/* トップドメイン */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center mb-4">
            <Globe className="w-5 h-5 text-cyan-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">トップドメイン</h3>
          </div>
          <div className="space-y-3">
            {analyticsData.topDomains.map((domain, index) => (
              <div key={domain.domain} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    index === 0 ? 'bg-yellow-400' :
                    index === 1 ? 'bg-gray-400' :
                    index === 2 ? 'bg-orange-400' :
                    'bg-blue-400'
                  }`}></div>
                  <span className="text-sm text-gray-300 truncate max-w-32">{domain.domain}</span>
                </div>
                <span className="text-sm font-medium text-white">{domain.count}</span>
              </div>
            ))}
            {analyticsData.topDomains.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">データがありません</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 最近のアクティビティ */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {analyticsData.recentActivity.map(activity => (
            <div key={activity.id} className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg">
              <div className={`w-2 h-2 rounded-full ${
                activity.status === 'FINISHED' ? 'bg-green-500' :
                activity.status === 'RUNNING' ? 'bg-yellow-500' :
                activity.status === 'FAILED' ? 'bg-red-500' :
                'bg-gray-500'
              }`}></div>
              <div className="flex-1">
                <p className="text-sm text-white">{activity.message}</p>
                <p className="text-xs text-gray-400">{activity.time}</p>
              </div>
            </div>
          ))}
          {analyticsData.recentActivity.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">最近のアクティビティがありません</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
