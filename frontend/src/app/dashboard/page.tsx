'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getUserProjects, Project, deleteProject } from '@/lib/api';
import ProjectCard from '@/components/ProjectCard';
import CreateProjectForm from '@/components/CreateProjectForm';
import ProfileIcon from '@/components/ProfileIcon';
import supabase from '@/lib/supabase';

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  // Check authentication status
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        
        if (!session) {
          // No session, redirect to sign in
          console.log('No active session, redirecting to sign in');
          router.replace('/signin');
          return;
        }
        
        setIsAuthChecking(false);
        fetchProjects();
      } catch (err) {
        console.error('Error checking auth:', err);
        setError('Authentication error. Please try again.');
        setIsAuthChecking(false);
      }
    };
    
    checkAuth();
  }, [router]);

  const fetchProjects = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const projectsData = await getUserProjects();
      setProjects(projectsData);
    } catch (err: any) {
      console.error('Error fetching projects:', err);
      setError('Failed to load projects. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = () => {
    // Scroll to top before showing form
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setShowCreateForm(true);
  };

  const handleProjectCreated = () => {
    setShowCreateForm(false);
    fetchProjects();
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      // Refresh the projects list after deletion
      fetchProjects();
    } catch (err) {
      console.error('Error deleting project:', err);
      setError('Failed to delete project. Please try again.');
    }
  };

  // For MVP, modify sign-out to just navigate to root
  const handleSignOut = async () => {
    router.replace('/');
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      <div className="w-full max-w-6xl mx-auto px-4 py-8">
        <header className="relative flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-indigo-900">Research Projects</h1>
            <p className="text-indigo-600 text-lg font-medium">Manage your research projects</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleSignOut}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Sign Out
            </button>
            <ProfileIcon />
          </div>
        </header>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {isAuthChecking ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            <div className={`transition-all duration-300 ease-in-out ${showCreateForm ? 'opacity-100 max-h-[1000px]' : 'opacity-0 max-h-0 overflow-hidden'}`}>
              <div className="max-w-2xl mx-auto">
                <CreateProjectForm
                  onProjectCreated={handleProjectCreated}
                  onCancel={() => setShowCreateForm(false)}
                />
              </div>
            </div>

            <div className={`transition-all duration-300 ease-in-out ${showCreateForm ? 'opacity-0 max-h-0 overflow-hidden' : 'opacity-100 max-h-[5000px]'}`}>
              <div className="flex justify-end mb-6">
                <button
                  onClick={handleCreateProject}
                  className="py-2 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 flex items-center"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create New Project
                </button>
              </div>
              
              <div className="mb-6 flex items-center">
                <div className="flex-grow h-px bg-gray-200"></div>
                <h2 className="mx-4 text-lg font-medium text-gray-700">Your Projects</h2>
                <div className="flex-grow h-px bg-gray-200"></div>
              </div>
              
              {isLoading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
              ) : (
                <>
                  {projects.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {projects.map((project) => (
                        <ProjectCard 
                          key={project.project_id} 
                          project={project}
                          onDelete={handleDeleteProject}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <h3 className="text-xl font-medium text-gray-700 mb-2">No projects yet</h3>
                      <p className="text-gray-500 mb-6">Create your first research project to get started</p>
                      <button
                        onClick={handleCreateProject}
                        className="py-2 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700"
                      >
                        Create Your First Project
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
} 