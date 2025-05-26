import { create } from 'zustand';
import { apiClient, Notification } from '@/lib/api';

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
  addNotification: (notification: Notification) => void;
  clearError: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,

  fetchNotifications: async () => {
    set({ isLoading: true, error: null });
    try {
      const notifications = await apiClient.getNotifications();
      const unreadCount = notifications.filter(n => !n.is_read).length;
      set({ 
        notifications, 
        unreadCount,
        isLoading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch notifications',
        isLoading: false 
      });
    }
  },

  markAsRead: async (id: string) => {
    try {
      await apiClient.markNotificationAsRead(id);
      const { notifications } = get();
      const updatedNotifications = notifications.map(notification =>
        notification.id === id 
          ? { ...notification, is_read: true }
          : notification
      );
      const unreadCount = updatedNotifications.filter(n => !n.is_read).length;
      set({ 
        notifications: updatedNotifications,
        unreadCount
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to mark notification as read'
      });
    }
  },

  markAllAsRead: async () => {
    try {
      await apiClient.markAllNotificationsAsRead();
      const { notifications } = get();
      const updatedNotifications = notifications.map(notification => ({
        ...notification,
        is_read: true
      }));
      set({ 
        notifications: updatedNotifications,
        unreadCount: 0
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to mark all notifications as read'
      });
    }
  },

  deleteNotification: async (id: string) => {
    try {
      await apiClient.deleteNotification(id);
      const { notifications } = get();
      const updatedNotifications = notifications.filter(n => n.id !== id);
      const unreadCount = updatedNotifications.filter(n => !n.is_read).length;
      set({ 
        notifications: updatedNotifications,
        unreadCount
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to delete notification'
      });
    }
  },

  addNotification: (notification: Notification) => {
    const { notifications, unreadCount } = get();
    set({ 
      notifications: [notification, ...notifications],
      unreadCount: notification.is_read ? unreadCount : unreadCount + 1
    });
  },

  clearError: () => set({ error: null }),
}));
