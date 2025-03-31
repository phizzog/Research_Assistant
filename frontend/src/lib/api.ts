// API service for interacting with the backend

// Base URL for the backend API
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Types
import { ChatHistory, ChatMessage } from './gemini';
import supabase from './supabase';
import type { Database } from '@/types/supabase';

interface QueryResponse {
  answer: string;
}

// Extend the Project type to include the sources field
export interface Source {
  // New field structure
  title?: string;          // Title field for display
  display_name?: string;   // Alternative display name
  name?: string;           // Old field for backward compatibility
  document_id: string;     // Unique identifier for the document
  source_id?: string;      // Unique identifier for the source
  upload_date?: string;    // Old field for timestamp
  added_at?: string;       // New field for timestamp
  summary?: string;        // Summary of the document content
}

export type Project = Database['public']['Tables']['projects']['Row'] & {
  sources?: Source[];
};

// Function to query the backend
export async function queryBackend(
  query: string, 
  topK: number = 5, 
  projectId?: number, 
  selectedDocumentIds?: string[],
  enhancedQueries: boolean = true
): Promise<string> {
  try {
    const payload: any = { 
      query, 
      top_k: topK,
      enhanced_queries: enhancedQueries
    };
    
    // Add project_id if provided
    if (projectId !== undefined) {
      payload.project_id = projectId;
    }
    
    // Add selected document IDs if provided
    if (selectedDocumentIds && selectedDocumentIds.length > 0) {
      payload.selected_document_ids = selectedDocumentIds;
    }
    
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
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
export async function sendChatMessage(
  message: string, 
  chatHistory: ChatHistory, 
  projectId?: number, 
  selectedDocumentIds?: string[],
  enhancedQueries: boolean = true
): Promise<string> {
  try {
    // First, get a response from the queryBackend function
    // This will handle the embedding search logic
    if (projectId !== undefined) {
      const queryResponse = await queryBackend(message, 5, projectId, selectedDocumentIds, enhancedQueries);
      
      // Add the response to our payload for the chat history
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message, 
          chat_history: chatHistory,
          enhanced_queries: enhancedQueries
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      // Return the query response instead of the chat response
      // since we're focusing on document search
      return queryResponse;
    } else {
      // If no project ID, use the standard chat endpoint
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message, 
          chat_history: chatHistory,
          enhanced_queries: enhancedQueries
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data: QueryResponse = await response.json();
      return data.answer;
    }
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
}

// Function to upload a file to the backend
/**
 * Uploads a file to the backend using the /ingest endpoint with simple_mode=true
 * This maintains compatibility with the deprecated /upload endpoint
 * 
 * @param file - The file to upload
 * @param metadata - Optional metadata to include with the upload
 * @param projectId - Optional project ID to associate the file with
 * @param customName - Optional custom name to use as the document_id
 * @returns A string containing the response message
 */
export async function uploadFile(file: File, metadata?: any, projectId?: number, customName?: string): Promise<string> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('simple_mode', 'true'); // Use simple_mode to mimic the old /upload behavior
    
    // Add project_id if provided
    if (projectId) {
      formData.append('project_id', projectId.toString());
    }
    
    // Add custom name if provided
    if (customName) {
      formData.append('custom_document_name', customName);
    }
    
    // Add metadata if provided
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    // Using the /ingest endpoint instead of /upload as per migration guide
    const response = await fetch(`${API_BASE_URL}/ingest`, {
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

export async function deleteProject(projectId: string): Promise<void> {
  try {
    // Get the current user's session
    const { data: { session } } = await supabase.auth.getSession();
    
    // If no session, throw an error
    if (!session?.user?.id) {
      throw new Error('Authentication required. Please sign in to delete a project.');
    }
    
    const { error } = await supabase
      .from('projects')
      .delete()
      .eq('project_id', projectId)
      .eq('user_id', session.user.id); // Ensure the user owns the project
      
    if (error) {
      throw error;
    }
  } catch (error) {
    console.error(`Error deleting project with ID ${projectId}:`, error);
    throw new Error('Failed to delete project');
  }
} 