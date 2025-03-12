'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Chat from '@/components/Chat';
import ResearchForm from '@/components/ResearchForm';
import ResearchQuestionsForm from '@/components/ResearchQuestionsForm';
import ResearchTypeSelector from '@/components/ResearchTypeSelector';
import ProfileIcon from '@/components/ProfileIcon';
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
    setIsLoading(true);
    
    try {
      // Add user message to chat
      const updatedMessages: ChatHistory = [
        ...messages,
        { role: 'user' as const, content: message }
      ];
      setMessages(updatedMessages);
      
      // Handle file upload if provided
      if (file) {
        const uploadResponse = await uploadFile(file);
        const fileMessage: ChatMessage = {
          role: 'assistant',
          content: `File uploaded successfully. ${uploadResponse}`
        };
        setMessages([...updatedMessages, fileMessage]);
        setIsLoading(false);
        return;
      }
      
      // Send message to backend
      const response = await sendChatMessage(
        message, 
        updatedMessages.slice(0, -1) // Don't include the message we just added
      );
      
      // Add assistant response to chat
      setMessages([
        ...updatedMessages,
        { role: 'assistant' as const, content: response }
      ]);
    } catch (err: any) {
      console.error('Error sending message:', err);
      // Add error message to chat
      setMessages([
        ...messages,
        { role: 'user' as const, content: message },
        { 
          role: 'assistant' as const, 
          content: 'Sorry, I encountered an error processing your request. Please try again.' 
        }
      ]);
    } finally {
      setIsLoading(false);
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
    <main className="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      <div className="w-full max-w-6xl mx-auto px-4 py-8">
        <header className="flex justify-between items-center mb-8">
          <button
            onClick={handleBackToDashboard}
            className="text-indigo-600 hover:text-indigo-800 flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to Dashboard
          </button>
          
          <div className="text-center">
            <h1 className="text-3xl font-bold text-indigo-900 mb-2">
              {currentProject ? currentProject.project_name : 'Research Assistant'}
            </h1>
            <p className="text-indigo-600 text-lg font-medium">
              {currentProject && currentProject.research_type 
                ? `${currentProject.research_type} Research Project` 
                : 'Your AI-powered research companion'}
            </p>
            {!backendHealthy && (
              <p className="text-red-500 text-sm mt-2">
                Warning: Backend service is unavailable. Some features may not work.
              </p>
            )}
          </div>
          
          <div>
            <ProfileIcon />
          </div>
        </header>
        
        {error && (
          <div className="mx-4 mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}
        
        {isAuthChecking || isLoadingProject ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            {showChat ? (
              <Chat 
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
              />
            ) : showResearchTypeSelector ? (
              <ResearchTypeSelector
                projectId={Number(projectId)}
                suggestedType={suggestedResearchType}
                aiExplanation={aiExplanation}
                onComplete={handleResearchTypeSelected}
              />
            ) : showQuestionnaire ? (
              <>
                {analyzing ? (
                  <div className="w-full max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                    <h2 className="text-2xl font-semibold text-indigo-900 mb-6 text-center">Analyzing Your Research Approach</h2>
                    <div className="flex flex-col items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mb-4"></div>
                      <p className="text-gray-600">Our AI is analyzing your responses to determine the best research methodology...</p>
                    </div>
                  </div>
                ) : (
                  <ResearchQuestionsForm 
                    onComplete={handleQuestionnaireComplete} 
                    projectName={currentProject?.project_name}
                  />
                )}
              </>
            ) : projectId ? (
              // If we have a project ID but haven't shown the questionnaire yet,
              // show a loading state while we prepare to transition
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              </div>
            ) : (
              // Only show the research form for manual entry (no project ID)
              <ResearchForm onSubmit={handleResearchSubmit} initialValue={projectDetails} />
            )}
          </>
        )}
      </div>
    </main>
  );
}
