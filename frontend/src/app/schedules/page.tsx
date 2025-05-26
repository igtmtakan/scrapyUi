'use client'

import React, { useState } from 'react'
import { 
  Calendar, 
  Clock, 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  Plus,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'

interface Schedule {
  id: string
  name: string
  description: string
  cron_expression: string
  is_active: boolean
  last_run?: string
  next_run?: string
  project_name: string
  spider_name: string
}

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([
    {
      id: '1',
      name: 'Daily News Scraping',
      description: 'Scrape latest news articles every day at 6 AM',
      cron_expression: '0 6 * * *',
      is_active: true,
      last_run: '2024-01-15T06:00:00Z',
      next_run: '2024-01-16T06:00:00Z',
      project_name: 'News Project',
      spider_name: 'news_spider'
    },
    {
      id: '2',
      name: 'E-commerce Price Check',
      description: 'Check product prices every 4 hours',
      cron_expression: '0 */4 * * *',
      is_active: true,
      last_run: '2024-01-15T12:00:00Z',
      next_run: '2024-01-15T16:00:00Z',
      project_name: 'E-commerce Project',
      spider_name: 'product_spider'
    },
    {
      id: '3',
      name: 'Weekly Report Generation',
      description: 'Generate weekly analytics report',
      cron_expression: '0 9 * * 1',
      is_active: false,
      last_run: '2024-01-08T09:00:00Z',
      next_run: '2024-01-15T09:00:00Z',
      project_name: 'Analytics Project',
      spider_name: 'report_spider'
    }
  ])

  const [showCreateModal, setShowCreateModal] = useState(false)

  const formatCronExpression = (cron: string) => {
    // 簡単なCron式の説明変換
    const cronDescriptions: { [key: string]: string } = {
      '0 6 * * *': 'Daily at 6:00 AM',
      '0 */4 * * *': 'Every 4 hours',
      '0 9 * * 1': 'Weekly on Monday at 9:00 AM',
      '0 0 * * *': 'Daily at midnight',
      '*/15 * * * *': 'Every 15 minutes'
    }
    
    return cronDescriptions[cron] || cron
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Never'
    
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const toggleSchedule = (scheduleId: string) => {
    setSchedules(prev => 
      prev.map(schedule => 
        schedule.id === scheduleId 
          ? { ...schedule, is_active: !schedule.is_active }
          : schedule
      )
    )
  }

  const runScheduleNow = (scheduleId: string) => {
    // TODO: API呼び出し
    console.log('Running schedule:', scheduleId)
  }

  const deleteSchedule = (scheduleId: string) => {
    if (confirm('Are you sure you want to delete this schedule?')) {
      setSchedules(prev => prev.filter(schedule => schedule.id !== scheduleId))
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* ヘッダー */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Calendar className="w-6 h-6 text-blue-400" />
            <h1 className="text-2xl font-bold">Schedules</h1>
          </div>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Schedule</span>
          </button>
        </div>
      </div>

      {/* スケジュール一覧 */}
      <div className="p-6">
        <div className="grid gap-6">
          {schedules.map(schedule => (
            <div
              key={schedule.id}
              className="bg-gray-800 rounded-lg border border-gray-700 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold">{schedule.name}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      schedule.is_active 
                        ? 'bg-green-100 text-green-800 border border-green-200'
                        : 'bg-gray-100 text-gray-800 border border-gray-200'
                    }`}>
                      {schedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  
                  <p className="text-gray-400 mb-4">{schedule.description}</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Schedule:</span>
                      <p className="text-white">{formatCronExpression(schedule.cron_expression)}</p>
                    </div>
                    
                    <div>
                      <span className="text-gray-500">Project:</span>
                      <p className="text-white">{schedule.project_name}</p>
                    </div>
                    
                    <div>
                      <span className="text-gray-500">Spider:</span>
                      <p className="text-white">{schedule.spider_name}</p>
                    </div>
                    
                    <div>
                      <span className="text-gray-500">Last Run:</span>
                      <p className="text-white">{formatDateTime(schedule.last_run)}</p>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex items-center space-x-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-blue-400" />
                      <span className="text-gray-400">Next run:</span>
                      <span className="text-white">{formatDateTime(schedule.next_run)}</span>
                    </div>
                  </div>
                </div>
                
                {/* アクション */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => runScheduleNow(schedule.id)}
                    className="p-2 text-gray-400 hover:text-green-400 transition-colors"
                    title="Run now"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => toggleSchedule(schedule.id)}
                    className={`p-2 transition-colors ${
                      schedule.is_active 
                        ? 'text-gray-400 hover:text-yellow-400' 
                        : 'text-gray-400 hover:text-green-400'
                    }`}
                    title={schedule.is_active ? 'Pause' : 'Activate'}
                  >
                    {schedule.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  
                  <button
                    className="p-2 text-gray-400 hover:text-blue-400 transition-colors"
                    title="Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => deleteSchedule(schedule.id)}
                    className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
          
          {schedules.length === 0 && (
            <div className="text-center py-12">
              <Calendar className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <h3 className="text-lg font-medium text-gray-400 mb-2">No schedules yet</h3>
              <p className="text-gray-500 mb-4">Create your first schedule to automate spider runs</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition-colors"
              >
                Create Schedule
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 作成モーダル（簡略版） */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowCreateModal(false)}></div>
            
            <div className="relative bg-gray-800 rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Create New Schedule</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    placeholder="Schedule name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Cron Expression</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    placeholder="0 6 * * *"
                  />
                </div>
                
                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                  >
                    Create
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
