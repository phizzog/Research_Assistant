// API service for interacting with the backend

// Base URL for the backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Types
import { ChatHistory, ChatMessage } from './gemini';
import supabase from './supabase';
import type { Database } from '@/types/supabase';

interface QueryResponse {
  answer: string;
}

export type Project = Database['public']['Tables']['projects']['Row'];

// Function to query the backend
export async function queryBackend(query: string, topK: number = 5): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: QueryResponse = await response.json();
    return data.answer;
  } catch (error) {
    console.error('Error querying backend:', error);
    throw error;
  }
}

// Function to send a chat message to the backend
export async function sendChatMessage(message: string, chatHistory: ChatHistory): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message, 
        chat_history: chatHistory 
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: QueryResponse = await response.json();
    return data.answer;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
}

// Function to upload a file to the backend
export async function uploadFile(file: File): Promise<string> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: QueryResponse = await response.json();
    return data.answer;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
}

// Function to check if the backend is healthy
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

// Function to get all projects for a user
export async function getUserProjects(): Promise<Project[]> {
  try {
    // Get the current user's session
    const { data: { session } } = await supabase.auth.getSession();
    
    // If no session, return empty array
    if (!session?.user) {
      return [];
    }
    
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .eq('user_id', session.user.id)
      .order('created_at', { ascending: false });
      
    if (error) {
      throw error;
    }
    
    return data as Project[];
  } catch (error) {
    console.error('Error fetching user projects:', error);
    // Return empty array instead of throwing
    return [];
  }
}

// Function to create a new project
export async function createProject(projectData: Omit<Project, 'project_id' | 'created_at' | 'user_id'>): Promise<Project> {
  try {
    // Get the current user's session
    const { data: { session } } = await supabase.auth.getSession();
    
    // If no session, throw an error instead of using a fallback UUID
    if (!session?.user?.id) {
      throw new Error('Authentication required. Please sign in to create a project.');
    }
    
    const { data, error } = await supabase
      .from('projects')
      .insert([
        { 
          ...projectData,
          user_id: session.user.id
        }
      ])
      .select()
      .single();
      
    if (error) {
      throw error;
    }
    
    return data as Project;
  } catch (error) {
    console.error('Error creating project:', error);
    throw error;
  }
}

// Function to get a project by ID
export async function getProjectById(projectId: number): Promise<Project> {
  try {
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .eq('project_id', projectId)
      .single();
      
    if (error) {
      throw error;
    }
    
    return data as Project;
  } catch (error) {
    console.error(`Error fetching project with ID ${projectId}:`, error);
    throw error;
  }
}

// Function to update a project
export async function updateProject(projectId: number, projectData: Partial<Omit<Project, 'project_id' | 'created_at' | 'user_id'>>): Promise<Project> {
  try {
    // Get the current user's session
    const { data: { session } } = await supabase.auth.getSession();
    
    // If no session, throw an error
    if (!session?.user?.id) {
      throw new Error('Authentication required. Please sign in to update a project.');
    }
    
    const { data, error } = await supabase
      .from('projects')
      .update(projectData)
      .eq('project_id', projectId)
      .eq('user_id', session.user.id) // Ensure the user owns the project
      .select()
      .single();
      
    if (error) {
      throw error;
    }
    
    return data as Project;
  } catch (error) {
    console.error(`Error updating project with ID ${projectId}:`, error);
    throw error;
  }
} 