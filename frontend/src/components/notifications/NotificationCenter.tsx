'use client'

import React, { useState, useEffect } from 'react'
import {
  Bell,
  X,
  Check,
  Info,
  AlertTriangle,
  XCircle,
  CheckCircle,
  Trash2,
  CheckCheck
} from 'lucide-react'

interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success'
  is_read: boolean
  created_at: string
  task_id?: string
  project_id?: string
}

interface NotificationCenterProps {
  isOpen: boolean
  onClose: () => void
}

export default function NotificationCenter({ isOpen, onClose }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)

  // モックデータ（実際の実装ではAPIから取得）
  const mockNotifications: Notification[] = [
    {
      id: '1',
      title: 'Task Completed',
      message: 'E-commerce spider has successfully completed with 250 items scraped.',
      type: 'success',
      is_read: false,
      created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      task_id: 'task-1'
    },
    {
      id: '2',
      title: 'Spider Failed',
      message: 'News spider encountered an error: Connection timeout after 30 seconds.',
      type: 'error',
      is_read: false,
      created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      task_id: 'task-2'
    },
    {
      id: '3',
      title: 'High Memory Usage',
      message: 'System memory usage has exceeded 85%. Consider optimizing your spiders.',
      type: 'warning',
      is_read: true,
      created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString()
    },
    {
      id: '4',
      title: 'Schedule Updated',
      message: 'Daily news scraping schedule has been updated to run at 6:00 AM.',
      type: 'info',
      is_read: false,
      created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
      project_id: 'project-1'
    }
  ]

  useEffect(() => {
    if (isOpen) {
      loadNotifications()
    }
  }, [isOpen])

  const loadNotifications = async () => {
    setLoading(true)
    try {
      // TODO: 実際のAPI呼び出し
      // const response = await fetch('/api/notifications')
      // const data = await response.json()

      // モックデータを使用
      setNotifications(mockNotifications)
      setUnreadCount(mockNotifications.filter(n => !n.is_read).length)
    } catch (error) {
      console.error('Failed to load notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async (notificationId: string) => {
    try {
      // TODO: 実際のAPI呼び出し
      // await fetch(`/api/notifications/${notificationId}/read`, { method: 'PUT' })

      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      // TODO: 実際のAPI呼び出し
      // await fetch('/api/notifications/read-all', { method: 'PUT' })

      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      )
      setUnreadCount(0)
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error)
    }
  }

  const deleteNotification = async (notificationId: string) => {
    try {
      // TODO: 実際のAPI呼び出し
      // await fetch(`/api/notifications/${notificationId}`, { method: 'DELETE' })

      setNotifications(prev => prev.filter(n => n.id !== notificationId))
      const notification = notifications.find(n => n.id === notificationId)
      if (notification && !notification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1))
      }
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      default:
        return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const formatTime = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose}></div>

      <div className="absolute right-0 top-0 h-full w-96 bg-gray-900 border-l border-gray-700 shadow-xl">
        {/* ヘッダー */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-semibold text-white">Notifications</h2>
              {unreadCount > 0 && (
                <span className="px-2 py-1 bg-red-600 text-white text-xs rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                  title="Mark all as read"
                >
                  <CheckCheck className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={onClose}
                className="p-1 text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* 通知リスト */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-8 text-center text-gray-400">
              <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              <p>Loading notifications...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No notifications</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-gray-800 transition-colors ${
                    !notification.is_read ? 'bg-gray-800/50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <h3 className={`text-sm font-medium ${
                          notification.is_read ? 'text-gray-300' : 'text-white'
                        }`}>
                          {notification.title}
                        </h3>

                        <div className="flex items-center space-x-1 ml-2">
                          {!notification.is_read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                              title="Mark as read"
                            >
                              <Check className="w-3 h-3" />
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>

                      <p className={`text-sm mt-1 ${
                        notification.is_read ? 'text-gray-400' : 'text-gray-300'
                      }`}>
                        {notification.message}
                      </p>

                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {formatTime(notification.created_at)}
                        </span>

                        {!notification.is_read && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
