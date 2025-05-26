'use client';

import { useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { useTaskStore } from '@/stores/taskStore';
import { Plus, Play, Code, Calendar, Settings, Zap } from 'lucide-react';
import Link from 'next/link';

export default function QuickActions() {
  const { projects } = useProjectStore();
  const { createTask } = useTaskStore();
  const [isCreatingTask, setIsCreatingTask] = useState(false);

  const handleQuickRun = async () => {
    if (projects.length === 0) return;
    
    setIsCreatingTask(true);
    try {
      // Get the first project and its first spider for quick run
      const project = projects[0];
      // This would need to be enhanced to get spiders for the project
      // For now, we'll just redirect to the project page
      window.location.href = `/projects/${project.id}`;
    } catch (error) {
      console.error('Failed to create quick task:', error);
    } finally {
      setIsCreatingTask(false);
    }
  };

  const quickActions = [
    {
      title: 'New Project',
      description: 'Create a new scraping project',
      icon: <Plus className="w-5 h-5" />,
      href: '/projects/new',
      color: 'bg-blue-600 hover:bg-blue-700',
    },
    {
      title: 'Quick Run',
      description: 'Run your latest spider',
      icon: <Play className="w-5 h-5" />,
      onClick: handleQuickRun,
      disabled: projects.length === 0 || isCreatingTask,
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      title: 'Spider Editor',
      description: 'Create or edit spiders',
      icon: <Code className="w-5 h-5" />,
      href: '/editor',
      color: 'bg-purple-600 hover:bg-purple-700',
    },
    {
      title: 'Schedule Task',
      description: 'Set up automated runs',
      icon: <Calendar className="w-5 h-5" />,
      href: '/schedules/new',
      color: 'bg-orange-600 hover:bg-orange-700',
    },
    {
      title: 'AI Assistant',
      description: 'Get spider suggestions',
      icon: <Zap className="w-5 h-5" />,
      href: '/ai-assistant',
      color: 'bg-indigo-600 hover:bg-indigo-700',
    },
    {
      title: 'Settings',
      description: 'Configure your workspace',
      icon: <Settings className="w-5 h-5" />,
      href: '/settings',
      color: 'bg-gray-600 hover:bg-gray-700',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Quick Actions</h2>
      
      <div className="grid grid-cols-1 gap-3">
        {quickActions.map((action, index) => {
          const ActionComponent = action.href ? Link : 'button';
          const actionProps = action.href 
            ? { href: action.href }
            : { 
                onClick: action.onClick,
                disabled: action.disabled,
                type: 'button' as const
              };

          return (
            <ActionComponent
              key={index}
              {...actionProps}
              className={`
                ${action.color} text-white p-4 rounded-lg transition-colors
                flex items-center space-x-3 text-left w-full
                ${action.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md'}
              `}
            >
              <div className="flex-shrink-0">
                {action.icon}
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium">{action.title}</p>
                <p className="text-sm opacity-90 mt-1">{action.description}</p>
              </div>
            </ActionComponent>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h3>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Active Projects</span>
            <span className="font-medium text-gray-900">
              {projects.filter(p => p.is_active).length}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Projects</span>
            <span className="font-medium text-gray-900">{projects.length}</span>
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 mb-3">💡 Tips</h3>
        <div className="space-y-2 text-sm text-gray-600">
          <p>• Use the AI Assistant to generate spider code automatically</p>
          <p>• Schedule regular runs to keep your data fresh</p>
          <p>• Monitor your tasks in real-time from the Tasks page</p>
        </div>
      </div>
    </div>
  );
}
