import { create } from 'zustand';
import { apiClient, Project, Spider } from '@/lib/api';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  spiders: Spider[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchProjects: () => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  createProject: (projectData: {
    name: string;
    description?: string;
    settings?: Record<string, any>;
  }) => Promise<Project>;
  updateProject: (id: string, projectData: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;

  // Spider actions
  fetchSpiders: (projectId?: string) => Promise<void>;
  createSpider: (spiderData: {
    name: string;
    code: string;
    project_id: string;
    settings?: Record<string, any>;
  }) => Promise<Spider>;
  updateSpider: (id: string, spiderData: Partial<Spider>) => Promise<void>;
  deleteSpider: (id: string) => Promise<void>;

  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  spiders: [],
  isLoading: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      // 認証状態をチェック
      if (!apiClient.isAuthenticated()) {
        console.warn('Not authenticated, redirecting to login');
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return;
      }

      const projects = await apiClient.getProjects();
      set({ projects, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch projects';

      // 認証エラーの場合はログインページにリダイレクト
      if (errorMessage.includes('認証') || errorMessage.includes('Not authenticated')) {
        console.warn('Authentication error in fetchProjects, redirecting to login');
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return;
      }

      set({
        error: errorMessage,
        isLoading: false
      });
    }
  },

  fetchProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await apiClient.getProject(id);
      set({ currentProject: project, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch project',
        isLoading: false
      });
    }
  },

  createProject: async (projectData) => {
    set({ isLoading: true, error: null });
    try {
      const project = await apiClient.createProject(projectData);
      const { projects } = get();
      set({
        projects: [...projects, project],
        isLoading: false
      });
      return project;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create project',
        isLoading: false
      });
      throw error;
    }
  },

  updateProject: async (id: string, projectData) => {
    set({ isLoading: true, error: null });
    try {
      const updatedProject = await apiClient.updateProject(id, projectData);
      const { projects, currentProject } = get();
      set({
        projects: projects.map(p => p.id === id ? updatedProject : p),
        currentProject: currentProject?.id === id ? updatedProject : currentProject,
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update project',
        isLoading: false
      });
      throw error;
    }
  },

  deleteProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.deleteProject(id);
      const { projects, currentProject } = get();
      set({
        projects: projects.filter(p => p.id !== id),
        currentProject: currentProject?.id === id ? null : currentProject,
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete project',
        isLoading: false
      });
      throw error;
    }
  },

  setCurrentProject: (project) => {
    set({ currentProject: project });
  },

  fetchSpiders: async (projectId) => {
    set({ isLoading: true, error: null });
    try {
      const spiders = await apiClient.getSpiders(projectId);
      set({ spiders, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch spiders',
        isLoading: false
      });
    }
  },

  createSpider: async (spiderData) => {
    set({ isLoading: true, error: null });
    try {
      const spider = await apiClient.createSpider(spiderData);
      const { spiders } = get();
      set({
        spiders: [...spiders, spider],
        isLoading: false
      });
      return spider;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create spider',
        isLoading: false
      });
      throw error;
    }
  },

  updateSpider: async (id: string, spiderData) => {
    set({ isLoading: true, error: null });
    try {
      const updatedSpider = await apiClient.updateSpider(id, spiderData);
      const { spiders } = get();
      set({
        spiders: spiders.map(s => s.id === id ? updatedSpider : s),
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update spider',
        isLoading: false
      });
      throw error;
    }
  },

  deleteSpider: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.deleteSpider(id);
      const { spiders } = get();
      set({
        spiders: spiders.filter(s => s.id !== id),
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete spider',
        isLoading: false
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
