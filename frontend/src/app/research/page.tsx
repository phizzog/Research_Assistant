'use client';

import React, { useState } from 'react';
import Chat from '@/components/Chat';
import ResearchForm from '@/components/ResearchForm';
import ResearchQuestionsForm from '@/components/ResearchQuestionsForm';
import ProfileIcon from '@/components/ProfileIcon';
import { ChatHistory, ChatMessage, initializeGemini } from '@/lib/gemini';

export default function HomePage() {
  const [messages, setMessages] = useState<ChatHistory>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [showQuestionnaire, setShowQuestionnaire] = useState(false);
  const [projectDetails, setProjectDetails] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  const handleResearchSubmit = async (details: string) => {
    setProjectDetails(details);
    setShowQuestionnaire(true);
  };

  const handleQuestionnaireComplete = async (responses: Array<{ question: string, answer: string }>) => {
    setAnalyzing(true);
    try {
      const model = initializeGemini(process.env.NEXT_PUBLIC_GEMINI_API_KEY || '');
      
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

Research Project Details:
${projectDetails}

Questionnaire Responses:
${formattedResponses}
      `.trim();

      const result = await model.generateContent(prompt);
      const response = result.response;
      const text = response.text();

      setMessages([
        {
          role: 'assistant',
          content:
            "Welcome! I've analyzed your research project and questionnaire responses. Here's my assessment:\n\n" +
            text +
            "\n\nWhat questions do you have about the suggested methodology?"
        }
      ]);
      setShowChat(true);
    } catch (error) {
      console.error('Error:', error);
      setMessages([
        {
          role: 'assistant',
          content: "Sorry, I encountered an error analyzing your research project. Please try again."
        }
      ]);
    } finally {
      setAnalyzing(false);
      setShowQuestionnaire(false);
    }
  };

  const handleSendMessage = async (message: string, file?: File) => {
    setIsLoading(true);
    try {
      // Add the user message to the chat
      const userMessage: ChatMessage = { role: 'user', content: message };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);

      const model = initializeGemini(process.env.NEXT_PUBLIC_GEMINI_API_KEY || '');
      let text = '';

      if (file) {
        // Handle file upload
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
        const result = await response.json();
        text = result.text;
      } else {
        // Get response from Gemini
        const result = await model.generateContent(message);
        const response = result.response;
        text = response.text();
      }

      // Add the assistant's response to the chat
      const assistantMessage: ChatMessage = { role: 'assistant', content: text };
      setMessages([...newMessages, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: "Sorry, I encountered an error. Please try again."
      };
      setMessages([...messages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      <div className="w-full h-screen max-w-4xl mx-auto flex flex-col">
        <header className="relative py-6 px-4">
          <div className="absolute top-6 right-4">
            <ProfileIcon />
          </div>
          <div className="text-center">
            <h1 className="text-3xl font-bold text-indigo-900 mb-2">Research Assistant</h1>
            <p className="text-indigo-600 text-lg font-medium">Your AI-powered research companion</p>
          </div>
        </header>
        
        <div className="flex-1 overflow-hidden mx-4">
          {!showQuestionnaire && !showChat ? (
            <ResearchForm onSubmit={handleResearchSubmit} />
          ) : showQuestionnaire && !showChat ? (
            <>
              {analyzing ? (
                <div className="w-full max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-6 flex flex-col items-center justify-center">
                  <div className="animate-pulse flex flex-col items-center">
                    <div className="h-12 w-12 mb-4 rounded-full bg-indigo-200"></div>
                    <h2 className="text-2xl font-semibold text-indigo-900 mb-2">Analyzing your research...</h2>
                    <p className="text-gray-600">Please wait while we process your responses</p>
                  </div>
                </div>
              ) : (
                <ResearchQuestionsForm onComplete={handleQuestionnaireComplete} />
              )}
            </>
          ) : (
            <Chat
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          )}
        </div>
      </div>
    </main>
  );
}
