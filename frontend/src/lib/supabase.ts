import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/supabase';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing environment variables for Supabase. Please check your .env.local file.'
  );
}

// Create a single supabase client for interacting with your database
export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    storageKey: 'supabase.auth.token',
    detectSessionInUrl: true,
    flowType: 'pkce',
  },
  db: {
    schema: 'public'
  },
  global: {
    headers: { 'x-application-name': 'research-assistant' },
  },
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
});

// Export a function to check Supabase connection
export async function checkSupabaseConnection() {
  try {
    const { data, error } = await supabase.from('chathistory').select('count').limit(1);
    if (error) throw error;
    return true;
  } catch (error) {
    console.error('Supabase connection error:', error);
    return false;
  }
}

export default supabase; 