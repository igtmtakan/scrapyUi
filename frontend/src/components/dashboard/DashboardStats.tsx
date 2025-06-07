'use client';

import { useEffect, useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { useTaskStore } from '@/stores/taskStore';
import { useNotificationStore } from '@/stores/notificationStore';
import { apiClient } from '@/lib/api';
import { Activity, Database, Play, AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react';

interface StatCard {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
}

export default function DashboardStats() {
  const { projects } = useProjectStore();
  const { tasks } = useTaskStore();
  const { unreadCount } = useNotificationStore();
  const [stats, setStats] = useState<StatCard[]>([]);
  const [flowerStats, setFlowerStats] = useState<any>(null);
  const [useFlowerData, setUseFlowerData] = useState(true);

  // Flowerからの統計データを取得
  useEffect(() => {
    const fetchFlowerStats = async () => {
      try {
        const data = await apiClient.getFlowerDashboardStats();
        setFlowerStats(data);
        setUseFlowerData(true);
      } catch (error) {
        console.warn('Failed to fetch Flower stats, falling back to local data:', error);
        setUseFlowerData(false);
      }
    };

    fetchFlowerStats();

    // 30秒ごとに更新
    const interval = setInterval(fetchFlowerStats, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let newStats: StatCard[] = [];

    if (useFlowerData && flowerStats && !flowerStats.error) {
      // Flowerからの正確な統計を使用
      newStats = [
        {
          title: 'Total Tasks',
          value: flowerStats.total_tasks,
          icon: <Database className="w-6 h-6" />,
          color: 'bg-blue-500',
        },
        {
          title: 'Pending Tasks',
          value: flowerStats.pending_tasks,
          icon: <Clock className="w-6 h-6" />,
          color: 'bg-yellow-500',
        },
        {
          title: 'Successful Tasks',
          value: flowerStats.successful_tasks,
          icon: <CheckCircle className="w-6 h-6" />,
          color: 'bg-green-500',
        },
        {
          title: 'Failed Tasks',
          value: flowerStats.failed_tasks,
          icon: <XCircle className="w-6 h-6" />,
          color: 'bg-red-500',
        },
      ];
    } else {
      // フォールバック: ローカルタスクストアからの統計
      const runningTasks = tasks.filter(task => task.status === 'RUNNING').length;
      const completedTasks = tasks.filter(task => task.status === 'FINISHED').length;
      const failedTasks = tasks.filter(task => task.status === 'FAILED').length;

      newStats = [
        {
          title: 'Total Projects',
          value: projects.length,
          icon: <Database className="w-6 h-6" />,
          color: 'bg-blue-500',
        },
        {
          title: 'Running Tasks',
          value: runningTasks,
          icon: <Play className="w-6 h-6" />,
          color: 'bg-green-500',
        },
        {
          title: 'Completed Tasks',
          value: completedTasks,
          icon: <Activity className="w-6 h-6" />,
          color: 'bg-purple-500',
        },
        {
          title: 'Failed Tasks',
          value: failedTasks,
          icon: <XCircle className="w-6 h-6" />,
          color: 'bg-red-500',
        },
      ];
    }

    setStats(newStats);
  }, [projects, tasks, unreadCount, flowerStats, useFlowerData]);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="flex items-center space-x-4">
            <div className={`${stat.color} p-3 rounded-lg text-white`}>
              {stat.icon}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">{stat.title}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              {stat.change && (
                <p className={`text-sm ${
                  stat.change.type === 'increase' 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {stat.change.type === 'increase' ? '+' : '-'}{stat.change.value}%
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
