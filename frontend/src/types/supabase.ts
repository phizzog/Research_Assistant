export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      chatmessages: {
        Row: {
          message_id: number
          message_text: string
          project_id: number
          sender_type: string
          sent_at: string | null
          user_id: string
        }
        Insert: {
          message_id?: number
          message_text: string
          project_id: number
          sender_type: string
          sent_at?: string | null
          user_id: string
        }
        Update: {
          message_id?: number
          message_text?: string
          project_id?: number
          sender_type?: string
          sent_at?: string | null
          user_id?: string
        }
      }
      choices: {
        Row: {
          choice_id: number
          choice_text: string
          description: string | null
          question_id: number
        }
        Insert: {
          choice_id?: number
          choice_text: string
          description?: string | null
          question_id: number
        }
        Update: {
          choice_id?: number
          choice_text?: string
          description?: string | null
          question_id?: number
        }
      }
      chunks: {
        Row: {
          chunk_id: string
          contextualized_text: string | null
          embedding: unknown | null
          id: number
          metadata: Json | null
          raw_text: string | null
        }
        Insert: {
          chunk_id: string
          contextualized_text?: string | null
          embedding?: unknown | null
          id?: number
          metadata?: Json | null
          raw_text?: string | null
        }
        Update: {
          chunk_id?: string
          contextualized_text?: string | null
          embedding?: unknown | null
          id?: number
          metadata?: Json | null
          raw_text?: string | null
        }
      }
      pdfs: {
        Row: {
          file_name: string
          file_path: string
          file_size: number | null
          pdf_id: number
          project_id: number
          raw_text: string | null
          upload_date: string | null
        }
        Insert: {
          file_name: string
          file_path: string
          file_size?: number | null
          pdf_id?: number
          project_id: number
          raw_text?: string | null
          upload_date?: string | null
        }
        Update: {
          file_name?: string
          file_path?: string
          file_size?: number | null
          pdf_id?: number
          project_id?: number
          raw_text?: string | null
          upload_date?: string | null
        }
      }
      projects: {
        Row: {
          created_at: string | null
          description: string | null
          learning_objective: string | null
          project_id: number
          project_name: string
          research_type: string | null
          user_id: string
        }
        Insert: {
          created_at?: string | null
          description?: string | null
          learning_objective?: string | null
          project_id?: number
          project_name: string
          research_type?: string | null
          user_id: string
        }
        Update: {
          created_at?: string | null
          description?: string | null
          learning_objective?: string | null
          project_id?: number
          project_name?: string
          research_type?: string | null
          user_id?: string
        }
      }
      questions: {
        Row: {
          question_id: number
          question_text: string
        }
        Insert: {
          question_id?: number
          question_text: string
        }
        Update: {
          question_id?: number
          question_text?: string
        }
      }
      userresponses: {
        Row: {
          choice_id: number
          project_id: number
          question_id: number
          response_id: number
          user_id: string
        }
        Insert: {
          choice_id: number
          project_id: number
          question_id: number
          response_id?: number
          user_id: string
        }
        Update: {
          choice_id?: number
          project_id?: number
          question_id?: number
          response_id?: number
          user_id?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
} 