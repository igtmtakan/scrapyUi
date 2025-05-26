'use client';

import { useEffect } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { Database, Settings, Calendar } from 'lucide-react';
import Link from 'next/link';

export default function ProjectOverview() {
  const { projects, fetchProjects, isLoading } = useProjectStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const recentProjects = projects.slice(0, 5);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Projects</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
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
        <h2 className="text-lg font-semibold text-gray-900">Projects</h2>
        <Link 
          href="/projects" 
          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
        >
          View all
        </Link>
      </div>

      {recentProjects.length === 0 ? (
        <div className="text-center py-8">
          <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No projects yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Create your first scraping project
          </p>
          <Link 
            href="/projects/new"
            className="inline-flex items-center mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Project
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {recentProjects.map((project) => (
            <div 
              key={project.id} 
              className="flex items-center space-x-4 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
              </div>
              
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {project.name}
                  </p>
                  <div className="flex items-center space-x-1">
                    {project.is_active ? (
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    ) : (
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    )}
                  </div>
                </div>
                
                {project.description && (
                  <p className="text-sm text-gray-500 truncate mt-1">
                    {project.description}
                  </p>
                )}
                
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>Created {formatDate(project.created_at)}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Settings className="w-3 h-3" />
                    <span>{Object.keys(project.settings || {}).length} settings</span>
                  </div>
                </div>
              </div>
              
              <div className="flex-shrink-0">
                <Link 
                  href={`/projects/${project.id}`}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View
                </Link>
              </div>
            </div>
          ))}
          
          {projects.length > 5 && (
            <div className="text-center pt-4">
              <Link 
                href="/projects"
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                View {projects.length - 5} more projects
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
