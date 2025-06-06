'use client';

import { useState, useEffect } from 'react';

interface ResearchFormProps {
  onSubmit: (projectDetails: string) => void;
  initialValue?: string;
}

export default function ResearchForm({ onSubmit, initialValue = '' }: ResearchFormProps) {
  const [projectTitle, setProjectTitle] = useState('');
  const [projectDescription, setProjectDescription] = useState('');

  // Parse initialValue if provided
  useEffect(() => {
    if (initialValue) {
      // Try to extract project title and description from initialValue
      const titleMatch = initialValue.match(/Project Title: (.*?)(?:\n\n|$)/);
      const descriptionMatch = initialValue.match(/Research Description:\n([\s\S]*?)$/);
      
      if (titleMatch && titleMatch[1]) {
        setProjectTitle(titleMatch[1].trim());
      }
      
      if (descriptionMatch && descriptionMatch[1]) {
        setProjectDescription(descriptionMatch[1].trim());
      } else {
        // If no structured format, just use the whole text as description
        setProjectDescription(initialValue);
      }
    }
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const details = `
Project Title: ${projectTitle}

Research Description:
${projectDescription}
    `.trim();
    onSubmit(details);
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-2xl font-semibold text-indigo-900 mb-6">Tell us about your research</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="projectTitle" className="block text-sm font-medium text-gray-700 mb-2">
            Project Title
          </label>
          <input
            type="text"
            id="projectTitle"
            value={projectTitle}
            onChange={(e) => setProjectTitle(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
            placeholder="e.g., Impact of Social Media on Student Mental Health"
            required
          />
        </div>

        <div>
          <label htmlFor="projectDescription" className="block text-sm font-medium text-gray-700 mb-2">
            Research Description
          </label>
          <p className="text-sm text-gray-500 mb-2">
            Please describe your research goals, questions, and what you hope to discover.
          </p>
          <textarea
            id="projectDescription"
            value={projectDescription}
            onChange={(e) => setProjectDescription(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent min-h-[150px] text-gray-800 font-medium placeholder:text-gray-400"
            placeholder="e.g., This research aims to understand how social media usage affects students' mental well-being. I want to explore both the positive and negative impacts, and gather data through..."
            required
          />
        </div>

        <button
          type="submit"
          disabled={!projectTitle.trim() || !projectDescription.trim()}
          className="w-full py-3 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          Start Research Analysis
        </button>
      </form>
    </div>
  );
} 