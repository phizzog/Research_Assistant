import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize the Gemini API client
export const initializeGemini = (apiKey: string) => {
  const genAI = new GoogleGenerativeAI(apiKey);
  // Use the latest stable version of the model
  return genAI.getGenerativeModel({ model: 'gemini-1.5-pro' });
};

// Type definitions for chat messages
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// Type for the chat history
export type ChatHistory = ChatMessage[]; 