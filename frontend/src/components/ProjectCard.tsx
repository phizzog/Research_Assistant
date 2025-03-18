import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Project } from '@/lib/api';

interface ProjectCardProps {
  project: Project;
  onDelete: (projectId: string) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Function to format the date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown date';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };
  
  // Function to get the badge color based on research type
  const getBadgeColor = (researchType: string | null) => {
    switch (researchType?.toLowerCase()) {
      case 'quantitative':
        return 'bg-blue-100 text-blue-800';
      case 'qualitative':
        return 'bg-green-100 text-green-800';
      case 'mixed methods':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 relative">
      {/* Three dots menu button */}
      <div className="absolute top-4 right-4" ref={menuRef}>
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="p-1 hover:bg-gray-100 rounded-full"
        >
          <svg
            className="w-5 h-5 text-gray-500"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
          </svg>
        </button>

        {/* Dropdown menu */}
        {showMenu && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
            <button
              onClick={() => {
                if (confirm('Are you sure you want to delete this project?')) {
                  onDelete(project.project_id);
                }
                setShowMenu(false);
              }}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              Delete Project
            </button>
          </div>
        )}
      </div>

      <Link href={`/project/${project.project_id}`}>
        <h3 className="text-xl font-semibold text-gray-900 mb-2 pr-8">
          {project.project_name}
        </h3>
        <p className="text-gray-600 mb-4">{project.description}</p>
        <div className="text-sm text-gray-500">
          Created: {formatDate(project.created_at)}
        </div>
      </Link>
    </div>
  );
} 