'use client';

import { useEffect } from 'react';
import { useTaskStore } from '@/stores/taskStore';
import { useProjectStore } from '@/stores/projectStore';
import { Play, Pause, CheckCircle, XCircle, Clock } from 'lucide-react';
import Link from 'next/link';

const statusIcons = {
  PENDING: <Clock className="w-4 h-4 text-yellow-500" />,
  RUNNING: <Play className="w-4 h-4 text-blue-500" />,
  FINISHED: <CheckCircle className="w-4 h-4 text-green-500" />,
  FAILED: <XCircle className="w-4 h-4 text-red-500" />,
  CANCELLED: <Pause className="w-4 h-4 text-gray-500" />,
};

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  RUNNING: 'bg-blue-100 text-blue-800',
  FINISHED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  CANCELLED: 'bg-gray-100 text-gray-800',
};

export default function RecentTasks() {
  const { tasks, fetchTasks, isLoading } = useTaskStore();
  const { projects } = useProjectStore();

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const recentTasks = tasks.slice(0, 10);

  const getProjectName = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    return project?.name || 'Unknown Project';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return '-';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Recent Tasks</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gray-200 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Recent Tasks</h2>
        <Link 
          href="/tasks" 
          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
        >
          View all
        </Link>
      </div>

      {recentTasks.length === 0 ? (
        <div className="text-center py-8">
          <Play className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No tasks yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Create a project and run your first spider
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {recentTasks.map((task) => (
            <div 
              key={task.id} 
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  {statusIcons[task.status]}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {getProjectName(task.project_id)}
                    </p>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[task.status]}`}>
                      {task.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 mt-1">
                    <p className="text-sm text-gray-500">
                      Started: {formatDate(task.created_at)}
                    </p>
                    <p className="text-sm text-gray-500">
                      Duration: {formatDuration(task.started_at, task.finished_at)}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                {task.items_count !== undefined && (
                  <div className="text-center">
                    <p className="font-medium text-gray-900">{task.items_count}</p>
                    <p className="text-xs">Items</p>
                  </div>
                )}
                {task.error_count !== undefined && task.error_count > 0 && (
                  <div className="text-center">
                    <p className="font-medium text-red-600">{task.error_count}</p>
                    <p className="text-xs">Errors</p>
                  </div>
                )}
                <Link 
                  href={`/tasks/${task.id}`}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  View
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
