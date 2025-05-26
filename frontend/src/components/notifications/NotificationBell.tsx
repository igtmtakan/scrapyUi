'use client'

import React, { useState, useEffect } from 'react'
import { Bell } from 'lucide-react'
import NotificationCenter from './NotificationCenter'

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    // 未読通知数を取得
    fetchUnreadCount()

    // 定期的に未読数を更新
    const interval = setInterval(fetchUnreadCount, 30000) // 30秒ごと

    return () => clearInterval(interval)
  }, [])

  const fetchUnreadCount = async () => {
    try {
      // Use the notification store instead of direct API call
      const { unreadCount: count } = await import('@/stores/notificationStore').then(m => m.useNotificationStore.getState())
      setUnreadCount(count)
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
      // エラー時はカウントを0にする
      setUnreadCount(0)
    }
  }

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  return (
    <>
      <button
        onClick={handleToggle}
        className="relative p-2 text-gray-400 hover:text-white transition-colors"
        title="Notifications"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />

        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      <NotificationCenter
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  )
}
