import React from 'react';
import { useRouter } from 'next/navigation';
import { Project } from '@/lib/api';

interface ProjectCardProps {
  project: Project;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project }) => {
  const router = useRouter();
  
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
  
  const handleClick = () => {
    router.replace(`/research?projectId=${project.project_id}`);
  };
  
  return (
    <div 
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
      onClick={handleClick}
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-xl font-semibold text-indigo-900 truncate">{project.project_name}</h3>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${getBadgeColor(project.research_type)}`}>
          {project.research_type || 'Unspecified'}
        </span>
      </div>
      
      {project.description && (
        <p className="text-gray-600 mb-4 line-clamp-2">{project.description}</p>
      )}
      
      {project.learning_objective && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-1">Learning Objective:</h4>
          <p className="text-gray-600 text-sm line-clamp-2">{project.learning_objective}</p>
        </div>
      )}
      
      <div className="text-xs text-gray-500 mt-2">
        Created on {formatDate(project.created_at)}
      </div>
    </div>
  );
};

export default ProjectCard; 