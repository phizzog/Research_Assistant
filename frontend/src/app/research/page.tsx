'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Chat from '@/components/Chat';
import ResearchForm from '@/components/ResearchForm';
import ResearchQuestionsForm from '@/components/ResearchQuestionsForm';
import ResearchTypeSelector from '@/components/ResearchTypeSelector';
import ProfileIcon from '@/components/ProfileIcon';
import SourcesPanel from '@/components/SourcesPanel';
import { ChatHistory, ChatMessage } from '@/lib/gemini';
import { 
  queryBackend, 
  sendChatMessage, 
  uploadFile, 
  checkBackendHealth, 
  getProjectById, 
  updateProject,
  Project 
} from '@/lib/api';
import supabase from '@/lib/supabase';

export default function ResearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get('projectId');
  
  const [messages, setMessages] = useState<ChatHistory>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [showQuestionnaire, setShowQuestionnaire] = useState(false);
  const [projectDetails, setProjectDetails] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(true);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [isLoadingProject, setIsLoadingProject] = useState(false);
  const [error, setError] = useState('');
  const [isAuthChecking, setIsAuthChecking] = useState(false);
  const [showResearchTypeSelector, setShowResearchTypeSelector] = useState(false);
  const [suggestedResearchType, setSuggestedResearchType] = useState('');
  const [aiExplanation, setAiExplanation] = useState('');

  // Check backend health on component mount
  useEffect(() => {
    const checkHealth = async () => {
      const isHealthy = await checkBackendHealth();
      setBackendHealthy(isHealthy);
      if (!isHealthy) {
        console.error('Backend is not healthy. Some features may not work.');
      }
    };
    checkHealth();
  }, []);

  // Load project if projectId is provided
  useEffect(() => {
    if (projectId) {
      const fetchProject = async () => {
        setIsLoadingProject(true);
        setError('');
        
        try {
          const project = await getProjectById(Number(projectId));
          setCurrentProject(project);
          
          // If the project already has a research type, we can skip to the chat
          if (project.research_type) {
            setShowChat(true);
            setMessages([
              {
                role: 'assistant',
                content: `Welcome back to your "${project.project_name}" research project! This project is using ${project.research_type} methodology. How can I assist you today?`
              }
            ]);
          } else {
            // For a newly created project, set project details and go directly to questionnaire
            const formattedDetails = `
Project Title: ${project.project_name}

Research Description:
${project.description || ''}
            `.trim();
            
            setProjectDetails(formattedDetails);
            setShowQuestionnaire(true);
          }
        } catch (err: any) {
          console.error('Error fetching project:', err);
          setError('Failed to load project. Please try again.');
        } finally {
          setIsLoadingProject(false);
        }
      };
      
      fetchProject();
    }
  }, [projectId]);

  const handleResearchSubmit = async (details: string) => {
    setProjectDetails(details);
    setShowQuestionnaire(true);
  };

  const handleQuestionnaireComplete = async (responses: Array<{ question: string, answer: string }>) => {
    setAnalyzing(true);
    try {
      // Format the questionnaire responses
      const formattedResponses = responses.map(r => 
        `Question: ${r.question}\nAnswer: ${r.answer}`
      ).join('\n\n');
      
      const prompt = `
As a research methodology expert, analyze the following research project description and questionnaire responses to determine whether it is best suited for:
1. Quantitative research
2. Qualitative research
3. Mixed methods research

Provide a detailed explanation of why you chose this methodology and suggest some initial steps for the researcher.

Format your response in Markdown with appropriate headings, bullet points, and emphasis. Make sure to include:
- A clear recommendation at the top with the heading "# Recommendation:" followed by your recommended research type
- A detailed explanation of why this methodology fits
- Initial steps the researcher should take
- Any potential challenges they might face

Research Project: ${currentProject?.project_name || 'Untitled Project'}

Research Project Details:
${projectDetails}

Questionnaire Responses:
${formattedResponses}
      `.trim();

      // Use the backend API instead of direct Gemini call
      const response = await queryBackend(prompt);

      // Extract the research type from the response using more robust pattern matching
      let researchType = '';
      
      // Look for a recommendation heading followed by the research type
      const recommendationMatch = response.match(/# Recommendation:?\s*(.*?)(?:\n|$)/i);
      if (recommendationMatch && recommendationMatch[1]) {
        const recommendation = recommendationMatch[1].trim();
        if (recommendation.toLowerCase().includes('quantitative')) {
          researchType = 'Quantitative';
        } else if (recommendation.toLowerCase().includes('qualitative')) {
          researchType = 'Qualitative';
        } else if (recommendation.toLowerCase().includes('mixed methods')) {
          researchType = 'Mixed Methods';
        }
      }
      
      // If no match found with the heading, fall back to the previous method
      if (!researchType) {
        if (response.toLowerCase().includes('recommend') && response.toLowerCase().includes('mixed methods')) {
          researchType = 'Mixed Methods';
        } else if (response.toLowerCase().includes('recommend') && response.toLowerCase().includes('qualitative')) {
          researchType = 'Qualitative';
        } else if (response.toLowerCase().includes('recommend') && response.toLowerCase().includes('quantitative')) {
          researchType = 'Quantitative';
        }
      }
      
      // If still no match, use a default
      if (!researchType) {
        // Look for the most mentioned research type
        const quantitativeCount = (response.toLowerCase().match(/quantitative/g) || []).length;
        const qualitativeCount = (response.toLowerCase().match(/qualitative/g) || []).length;
        const mixedMethodsCount = (response.toLowerCase().match(/mixed methods/g) || []).length;
        
        if (mixedMethodsCount > quantitativeCount && mixedMethodsCount > qualitativeCount) {
          researchType = 'Mixed Methods';
        } else if (qualitativeCount > quantitativeCount) {
          researchType = 'Qualitative';
        } else {
          researchType = 'Quantitative';
        }
      }

      // Store the suggested research type and explanation
      setSuggestedResearchType(researchType);
      setAiExplanation(response);
      
      // Show the research type selector
      setShowResearchTypeSelector(true);
      setAnalyzing(false);
    } catch (err) {
      console.error('Error analyzing responses:', err);
      setError('Failed to analyze responses. Please try again.');
      setAnalyzing(false);
    }
  };

  const handleResearchTypeSelected = async () => {
    // Refresh the project data
    if (projectId) {
      try {
        const project = await getProjectById(Number(projectId));
        setCurrentProject(project);
        
        // Show the chat with a welcome message
        setShowChat(true);
        setMessages([
          {
            role: 'assistant',
            content: `# Research Project Setup Complete!

## Your project "${project.project_name}" has been set up as a ${project.research_type} Research project.

Based on this methodology, I can help you with:

- **Designing appropriate research methods**
- **Analyzing your data**
- **Structuring your research paper**
- **Finding relevant sources and literature**

How would you like to proceed with your research?`
          }
        ]);
        
        // Hide the research type selector
        setShowResearchTypeSelector(false);
      } catch (err) {
        console.error('Error refreshing project:', err);
      }
    }
  };

  const handleSendMessage = async (message: string, file?: File) => {
    if (isLoading) return;
    
    setIsLoading(true);
    
    try {
      // Add user message to chat
      const userMessage: ChatMessage = {
        role: 'user',
        content: message
      };
      
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      
      let responseContent = '';
      
      // Handle file upload if provided
      if (file) {
        try {
          // Create metadata for the file
          const metadata = {
            project_id: Number(projectId),
            name: file.name,
            filename: file.name,
            upload_date: new Date().toISOString()
          };
          
          // Upload the file with metadata
          const uploadResponse = await uploadFile(file, metadata);
          responseContent = uploadResponse;
          
          // No need for setTimeout to refresh sources - we'll use the refreshSources callback
        } catch (error) {
          console.error('Error uploading file:', error);
          responseContent = 'There was an error processing your file. Please try again.';
        }
      } else {
        // Regular text message
        try {
          responseContent = await sendChatMessage(message, updatedMessages);
        } catch (error) {
          console.error('Error sending message:', error);
          responseContent = 'Sorry, I encountered an error processing your message. Please try again.';
        }
      }
      
      // Add assistant response to chat
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: responseContent
      };
      
      setMessages([...updatedMessages, assistantMessage]);
    } catch (error) {
      console.error('Error in chat flow:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Create a refreshSources function
  const refreshSources = async () => {
    console.log('Refreshing sources for project', projectId);
    
    if (!projectId) {
      console.error('Cannot refresh sources: No project ID provided');
      return;
    }
    
    try {
      // First try to get the sources directly from Supabase
      const { data, error } = await supabase
        .from('projects')
        .select('sources')
        .eq('project_id', projectId)
        .single();
        
      if (error) {
        console.error('Error fetching sources from Supabase:', error);
      } else if (data && data.sources) {
        console.log('Successfully refreshed sources:', data.sources);
      } else {
        console.log('No sources found in project data:', data);
      }
      
      // Refresh the project data to update any components that depend on it
      const project = await getProjectById(Number(projectId));
      setCurrentProject(project);
      console.log('Updated current project with refreshed data:', project);
    } catch (error) {
      console.error('Error refreshing sources:', error);
    }
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  if (isLoadingProject) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-indigo-50 to-white flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-12 w-12 mb-4 rounded-full bg-indigo-200"></div>
          <h2 className="text-2xl font-semibold text-indigo-900 mb-2">Loading project...</h2>
          <p className="text-gray-600">Please wait</p>
        </div>
      </main>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-indigo-50 to-white">
      {/* Header */}
      <header className="flex justify-between items-center p-4 border-b border-gray-200 bg-white">
        <button
          onClick={handleBackToDashboard}
          className="text-indigo-600 hover:text-indigo-800"
        >
          ← Back to Dashboard
        </button>
        <div className="text-center flex-1">
          <h1 className="text-xl font-semibold text-indigo-900">
            {currentProject?.project_name || 'New Research Project'}
          </h1>
          {currentProject?.research_type && (
            <p className="text-sm text-indigo-600">{currentProject.research_type} Research</p>
          )}
        </div>
        <ProfileIcon />
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {!backendHealthy && (
          <div className="bg-red-50 text-red-700 p-3 text-center border-b border-red-200">
            Backend service is currently unavailable. Some features may not work properly.
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 p-3 text-center border-b border-red-200">
            {error}
          </div>
        )}

        {isLoadingProject ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-2"></div>
            <p className="text-indigo-600 ml-3">Loading project...</p>
          </div>
        ) : (
          <>
            {!showQuestionnaire && !showChat && !showResearchTypeSelector && (
              <div className="flex-1 p-4 max-w-4xl mx-auto w-full">
                <ResearchForm onSubmit={handleResearchSubmit} />
              </div>
            )}

            {showQuestionnaire && !showChat && !showResearchTypeSelector && (
              <div className="flex-1 p-4 max-w-4xl mx-auto w-full">
                <ResearchQuestionsForm 
                  projectName={currentProject?.project_name}
                  onComplete={handleQuestionnaireComplete} 
                />
              </div>
            )}

            {showResearchTypeSelector && !showChat && (
              <div className="flex-1 p-4 max-w-4xl mx-auto w-full">
                <ResearchTypeSelector 
                  projectId={Number(projectId)}
                  suggestedType={suggestedResearchType}
                  aiExplanation={aiExplanation}
                  onComplete={handleResearchTypeSelected}
                />
              </div>
            )}

            {showChat && (
              <div className="flex-1 flex overflow-hidden">
                <SourcesPanel 
                  onFileUpload={(file) => handleSendMessage('File uploaded', file)} 
                  projectId={Number(projectId)}
                  refreshSources={refreshSources}
                />
                <div className="flex-1 overflow-hidden">
                  <Chat 
                    onSendMessage={handleSendMessage} 
                    messages={messages} 
                    isLoading={isLoading} 
                  />
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {analyzing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-2 text-indigo-900">Analyzing your research needs...</h3>
            <p className="text-gray-600 mb-4">
              Our AI is analyzing your responses to suggest the best research methodology for your project.
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-indigo-600 h-2.5 rounded-full animate-pulse w-full"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
