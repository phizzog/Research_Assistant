import React, { useState } from 'react';
import { createProject } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface CreateProjectFormProps {
  onProjectCreated: () => void;
  onCancel: () => void;
}

const CreateProjectForm: React.FC<CreateProjectFormProps> = ({ onProjectCreated, onCancel }) => {
  const router = useRouter();
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [learningObjective, setLearningObjective] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (!projectName.trim()) {
        throw new Error('Project name is required');
      }

      const createdProject = await createProject({
        project_name: projectName,
        description,
        learning_objective: learningObjective,
        research_type: null, // Will be determined later in the research flow
      });

      // Notify parent component
      onProjectCreated();
      
      // Redirect to research page to determine research type
      router.push(`/research?projectId=${createdProject.project_id}`);
    } catch (err: any) {
      console.error('Error creating project:', err);
      
      // Handle authentication error specifically
      if (err.message && err.message.includes('Authentication required')) {
        setError('You need to be signed in to create a project. Redirecting to sign in...');
        // Redirect to sign in page after a short delay
        setTimeout(() => {
          router.push('/signin');
        }, 2000);
      } else {
        setError(err.message || 'Failed to create project');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-indigo-900 mb-2">Create New Research Project</h2>
        <p className="text-gray-600">Start your research journey by providing some basic information</p>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Project Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-black"
            placeholder="Enter project name"
            required
            autoFocus
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-black"
            placeholder="Describe your research project"
            rows={3}
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Learning Objective
          </label>
          <textarea
            value={learningObjective}
            onChange={(e) => setLearningObjective(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-black"
            placeholder="What do you hope to learn from this research?"
            rows={3}
          />
        </div>
        
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="py-2 px-4 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="py-2 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateProjectForm; 