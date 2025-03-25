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
import ChatHistoryPanel from '@/components/ChatHistoryPanel';
import { v4 as uuidv4 } from 'uuid';

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
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat');
  const [session, setSession] = useState<any>(null);
  const [showNewChatConfirm, setShowNewChatConfirm] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session: currentSession } } = await supabase.auth.getSession();
      setSession(currentSession);
      
      if (!currentSession) {
        router.replace('/signin?redirectTo=' + encodeURIComponent(window.location.pathname + window.location.search));
      }
    };
    
    checkAuth();
  }, []);

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
            // Generate a new session ID when starting the chat
            const newSessionId = uuidv4();
            setCurrentSessionId(newSessionId);
            console.log('Starting chat with new session ID:', newSessionId);
            
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
        
        // Generate a new session ID when starting the chat
        const newSessionId = uuidv4();
        setCurrentSessionId(newSessionId);
        console.log('Starting chat with new session ID:', newSessionId);
        
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

  const handleBackToDashboard = async () => {
    // Save current conversation before navigating
    if (messages.length > 0) {
      console.log('Saving current conversation before navigating to dashboard');
      await saveCurrentConversation();
    }
    router.push('/dashboard');
  };

  const handleNewChat = async () => {
    console.log('Starting handleNewChat with current state:', {
      messagesLength: messages.length,
      currentSessionId,
      projectId,
      userId: session?.user?.id
    });

    // Save current conversation before clearing
    if (messages.length > 0) {
      console.log('Saving current conversation before starting new chat');
      await saveCurrentConversation();
      
      // Force a refresh of the history panel
      console.log('Refreshing history panel...');
      const event = new CustomEvent('refreshHistory');
      window.dispatchEvent(event);
    }

    // Generate a new session ID for the new chat
    const newSessionId = uuidv4();
    console.log('Generated new session ID:', newSessionId);
    setCurrentSessionId(newSessionId);

    if (currentProject) {
      const initialMessage: ChatMessage = {
        role: 'assistant' as const,
        content: `# Research Project Setup Complete!

## Your project "${currentProject.project_name}" has been set up as a ${currentProject.research_type} Research project.

Based on this methodology, I can help you with:

- **Designing appropriate research methods**
- **Analyzing your data**
- **Structuring your research paper**
- **Finding relevant sources and literature**

How would you like to proceed with your research?`
      };

      // Set messages with the new session ID
      setMessages([initialMessage]);
      console.log('Set initial message with new session ID');
    } else {
      setMessages([]);
    }
    setActiveTab('chat');
    setShowNewChatConfirm(false);
  };

  const saveCurrentConversation = async () => {
    console.log('Starting saveCurrentConversation with:', {
      messagesLength: messages.length,
      hasUserMessages: messages.some(msg => msg.role === 'user'),
      userId: session?.user?.id,
      projectId,
      currentSessionId
    });

    // Skip if there's no user interaction (only AI messages) or no messages at all
    const hasUserMessages = messages.some(msg => msg.role === 'user');
    if (!messages.length || !session?.user?.id || !projectId || !hasUserMessages) {
      console.log('Skipping save - no user interaction:', { 
        messagesLength: messages.length, 
        hasUserMessages,
        userId: session?.user?.id, 
        projectId 
      });
      return;
    }

    try {
      // Use the current session ID
      const sessionIdToUse = currentSessionId;
      if (!sessionIdToUse) {
        console.log('No session ID available, skipping save');
        return;
      }

      console.log('Saving conversation with session ID:', sessionIdToUse);

      // Prepare messages for insertion with the same session ID and sequential timestamps
      const messagesToInsert = messages.map((message, index) => ({
        project_id: Number(projectId),
        user_id: session.user.id,
        sender_type: message.role === 'user' ? 'User' : 'AI',
        message_text: message.content,
        session_id: sessionIdToUse,
        sent_at: new Date(Date.now() + index * 1000).toISOString() // Add 1 second between messages
      }));

      console.log('Messages to insert:', messagesToInsert);

      // Delete any existing messages with this session ID to prevent duplicates
      console.log('Deleting existing messages for session:', sessionIdToUse);
      const { error: deleteError } = await supabase
        .from('chathistory')
        .delete()
        .eq('session_id', sessionIdToUse)
        .eq('project_id', projectId)
        .eq('user_id', session.user.id);

      if (deleteError) {
        console.error('Error deleting existing messages:', deleteError);
        throw deleteError;
      }

      // Insert all messages as a single conversation
      console.log('Inserting new messages...');
      const { error: insertError } = await supabase
        .from('chathistory')
        .insert(messagesToInsert);

      if (insertError) {
        console.error('Error saving conversation:', insertError);
        throw insertError;
      }

      console.log('Conversation saved successfully');
    } catch (error) {
      console.error('Error saving conversation:', error);
    }
  };

  const handleClearHistory = async () => {
    // Save current conversation before clearing
    if (messages.length > 0) {
      await saveCurrentConversation();
    }
    setMessages([]);
    setCurrentSessionId(''); // Clear the session ID
  };

  // Save conversation only when navigating away from the page
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (messages.length > 0) {
        saveCurrentConversation();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [messages, currentSessionId, session?.user?.id, projectId]);

  const handleLoadConversation = async (messages: ChatHistory, sessionId: string) => {
    console.log('Loading conversation with session ID:', sessionId);
    
    // Save current conversation before loading the historical one
    if (messages.length > 0) {
      console.log('Saving current conversation before loading historical one');
      await saveCurrentConversation();
      
      // Force a refresh of the history panel
      console.log('Refreshing history panel...');
      const event = new CustomEvent('refreshHistory');
      window.dispatchEvent(event);
    }

    // Set the new messages and session ID
    setMessages(messages);
    setCurrentSessionId(sessionId);
    setActiveTab('chat'); // Switch back to chat tab
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
                <div className="flex-1 overflow-hidden flex flex-col">
                  <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
                    <div className="flex justify-between items-center">
                      <div className="flex">
                        <button
                          onClick={() => setActiveTab('chat')}
                          className={`px-4 py-2 text-sm font-medium ${
                            activeTab === 'chat'
                              ? 'text-indigo-600 border-b-2 border-indigo-600'
                              : 'text-gray-500 hover:text-gray-700'
                          }`}
                        >
                          Chat
                        </button>
                        <button
                          onClick={() => setActiveTab('history')}
                          className={`px-4 py-2 text-sm font-medium ${
                            activeTab === 'history'
                              ? 'text-indigo-600 border-b-2 border-indigo-600'
                              : 'text-gray-500 hover:text-gray-700'
                          }`}
                        >
                          History
                        </button>
                      </div>
                      {activeTab === 'chat' && (
                        <button
                          onClick={() => setShowNewChatConfirm(true)}
                          className="mr-4 px-3 py-1 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors"
                        >
                          New Chat
                        </button>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex-1 overflow-hidden">
                    {activeTab === 'chat' ? (
                      <Chat 
                        onSendMessage={handleSendMessage} 
                        messages={messages} 
                        isLoading={isLoading}
                        userId={session?.user?.id || ''}
                        projectId={Number(projectId)}
                        onClearHistory={handleClearHistory}
                        onSessionIdChange={setCurrentSessionId}
                      />
                    ) : (
                      <ChatHistoryPanel
                        projectId={Number(projectId)}
                        userId={session?.user?.id || ''}
                        onLoadConversation={handleLoadConversation}
                        showNewChat={false}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* New Chat Confirmation Dialog */}
      {showNewChatConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2 text-indigo-900">Start New Chat?</h3>
            <p className="text-gray-600 mb-4">
              This will clear your current conversation. The chat history will still be saved.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowNewChatConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleNewChat}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors"
              >
                Start New Chat
              </button>
            </div>
          </div>
        </div>
      )}

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
