import React, { useState } from 'react';
import { updateProject } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

interface ResearchTypeSelectorProps {
  projectId: number;
  suggestedType: string;
  aiExplanation: string;
  onComplete: () => void;
}

const RESEARCH_TYPES = [
  { value: 'Quantitative', label: 'Quantitative Research' },
  { value: 'Qualitative', label: 'Qualitative Research' },
  { value: 'Mixed Methods', label: 'Mixed Methods Research' },
];

const ResearchTypeSelector: React.FC<ResearchTypeSelectorProps> = ({
  projectId,
  suggestedType,
  aiExplanation,
  onComplete,
}) => {
  const [selectedType, setSelectedType] = useState(suggestedType);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await updateProject(projectId, {
        research_type: selectedType,
      });
      onComplete();
    } catch (err: any) {
      console.error('Error updating research type:', err);
      setError(err.message || 'Failed to update research type');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-2xl font-bold text-black mb-4">Research Type Recommendation</h2>
      
      <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200">
        <div className="flex items-center mb-3">
          <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center mr-3">
            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-black">AI Recommendation</h3>
        </div>
        <div className="prose prose-sm max-w-none text-black">
          <div className="text-black">
            <ReactMarkdown
              components={{
                h1: ({node, ...props}) => <h1 className="text-black text-xl font-bold mt-4 mb-2" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-black text-lg font-bold mt-3 mb-2" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-black text-base font-bold mt-2 mb-1" {...props} />,
                p: ({node, ...props}) => <p className="text-black mb-2" {...props} />,
                ul: ({node, ...props}) => <ul className="text-black list-disc pl-5 mb-2" {...props} />,
                ol: ({node, ...props}) => <ol className="text-black list-decimal pl-5 mb-2" {...props} />,
                li: ({node, ...props}) => <li className="text-black mb-1" {...props} />,
                strong: ({node, ...props}) => <strong className="text-black font-bold" {...props} />,
                em: ({node, ...props}) => <em className="text-black italic" {...props} />,
              }}
            >
              {aiExplanation}
            </ReactMarkdown>
          </div>
        </div>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-6">
          <label className="block text-sm font-medium text-black mb-2">
            Choose Research Type
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {RESEARCH_TYPES.map((type) => (
              <div 
                key={type.value}
                className={`
                  border rounded-lg p-4 cursor-pointer transition-colors
                  ${selectedType === type.value 
                    ? 'border-indigo-500 bg-indigo-50' 
                    : 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/50'}
                `}
                onClick={() => setSelectedType(type.value)}
              >
                <div className="flex items-center">
                  <div className={`w-4 h-4 rounded-full mr-2 border ${selectedType === type.value ? 'border-indigo-600 bg-indigo-600' : 'border-gray-400'}`}>
                    {selectedType === type.value && (
                      <div className="w-2 h-2 rounded-full bg-white m-0.5"></div>
                    )}
                  </div>
                  <span className="font-medium text-black">{type.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        
        <div className="flex justify-end">
          <button
            type="submit"
            className="py-2 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Saving...' : 'Continue with Selected Type'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ResearchTypeSelector; 