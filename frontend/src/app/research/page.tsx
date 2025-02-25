'use client';

import React, { useState } from 'react';
import Chat from '@/components/Chat';
import ResearchForm from '@/components/ResearchForm';
import { ChatHistory, ChatMessage, initializeGemini } from '@/lib/gemini';

export default function HomePage() {
  const [messages, setMessages] = useState<ChatHistory>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const handleResearchSubmit = async (projectDetails: string) => {
    setIsLoading(true);
    try {
      const model = initializeGemini(process.env.NEXT_PUBLIC_GEMINI_API_KEY || '');
      
      const prompt = `
As a research methodology expert, analyze the following research project description and determine whether it is best suited for:
1. Quantitative research
2. Qualitative research
3. Mixed methods research

Provide a brief explanation of why you chose this methodology and suggest some initial steps for the researcher.

Research Project Details:
${projectDetails}
      `.trim();

      const result = await model.generateContent(prompt);
      const response = result.response;
      const text = response.text();

      setMessages([
        {
          role: 'assistant',
          content:
            "Welcome! I've analyzed your research project. Here's my assessment:\n\n" +
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
      setIsLoading(false);
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
        <header className="text-center py-6 px-4">
          <h1 className="text-3xl font-bold text-indigo-900 mb-2">Research Assistant</h1>
          <p className="text-indigo-600 text-lg font-medium">Your AI-powered research companion</p>
        </header>
        
        <div className="flex-1 overflow-hidden mx-4">
          {!showChat ? (
            <ResearchForm onSubmit={handleResearchSubmit} />
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
