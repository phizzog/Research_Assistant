import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize the Gemini API client
export const initializeGemini = (apiKey: string) => {
  const genAI = new GoogleGenerativeAI(apiKey);
  return genAI.getGenerativeModel({ model: 'gemini-pro' });
};

// Type definitions for chat messages
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// Type for the chat history
export type ChatHistory = ChatMessage[]; 