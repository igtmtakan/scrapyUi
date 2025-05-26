import { create } from 'zustand';
import { apiClient, Task, Result } from '@/lib/api';

interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  results: Result[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchTasks: (filters?: {
    project_id?: string;
    spider_id?: string;
    status?: string;
  }) => Promise<void>;
  fetchTask: (id: string) => Promise<void>;
  createTask: (taskData: {
    project_id: string;
    spider_id: string;
    log_level?: string;
    settings?: Record<string, any>;
  }) => Promise<Task>;
  cancelTask: (id: string) => Promise<void>;
  setCurrentTask: (task: Task | null) => void;
  
  // Results actions
  fetchResults: (taskId?: string) => Promise<void>;
  exportResults: (taskId: string, format: 'json' | 'csv' | 'excel' | 'xml') => Promise<void>;
  
  clearError: () => void;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  currentTask: null,
  results: [],
  isLoading: false,
  error: null,

  fetchTasks: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await apiClient.getTasks(filters);
      set({ tasks, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch tasks',
        isLoading: false 
      });
    }
  },

  fetchTask: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const task = await apiClient.getTask(id);
      set({ currentTask: task, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch task',
        isLoading: false 
      });
    }
  },

  createTask: async (taskData) => {
    set({ isLoading: true, error: null });
    try {
      const task = await apiClient.createTask(taskData);
      const { tasks } = get();
      set({ 
        tasks: [task, ...tasks],
        isLoading: false 
      });
      return task;
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to create task',
        isLoading: false 
      });
      throw error;
    }
  },

  cancelTask: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.cancelTask(id);
      const { tasks, currentTask } = get();
      const updatedTasks = tasks.map(task => 
        task.id === id ? { ...task, status: 'CANCELLED' as const } : task
      );
      set({ 
        tasks: updatedTasks,
        currentTask: currentTask?.id === id 
          ? { ...currentTask, status: 'CANCELLED' as const }
          : currentTask,
        isLoading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to cancel task',
        isLoading: false 
      });
      throw error;
    }
  },

  setCurrentTask: (task) => {
    set({ currentTask: task });
  },

  fetchResults: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const results = await apiClient.getResults(taskId);
      set({ results, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch results',
        isLoading: false 
      });
    }
  },

  exportResults: async (taskId: string, format: 'json' | 'csv' | 'excel' | 'xml') => {
    set({ isLoading: true, error: null });
    try {
      const blob = await apiClient.exportResults(taskId, format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `results_${taskId}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      set({ isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to export results',
        isLoading: false 
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
