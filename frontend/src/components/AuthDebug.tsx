'use client';

import { useState, useEffect } from 'react';
import supabase from '@/lib/supabase';

// This component will help debug authentication issues
export default function AuthDebug({ show = false }: { show?: boolean }) {
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [cookies, setCookies] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(show);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Get session data
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          setError(error.message);
        } else {
          setSessionInfo(data);
          
          // Get available cookies
          const availableCookies = document.cookie.split(';')
            .map(cookie => cookie.trim())
            .filter(cookie => cookie.startsWith('sb-') || cookie.includes('supabase'));
          
          setCookies(availableCookies);
        }
      } catch (err: any) {
        setError(err.message || 'Unknown error checking authentication');
      }
    };
    
    if (isVisible) {
      checkAuth();
    }
  }, [isVisible]);

  if (!isVisible) {
    return (
      <button 
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-gray-800 text-white px-3 py-1 rounded-md text-sm opacity-50 hover:opacity-100"
      >
        Debug
      </button>
    );
  }
  
  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-96 overflow-auto bg-gray-900 text-white p-4 rounded-lg shadow-lg text-xs z-50">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold">Auth Debug</h3>
        <button onClick={() => setIsVisible(false)} className="text-gray-400 hover:text-white">
          Close
        </button>
      </div>
      
      {error && (
        <div className="bg-red-900 p-2 rounded mb-2">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      <div className="mb-4">
        <strong>Session Status:</strong> {sessionInfo?.session ? 'Authenticated' : 'Not Authenticated'}
      </div>
      
      {sessionInfo?.session && (
        <div className="mb-4">
          <strong>User:</strong> {sessionInfo.session.user.email}
          <div className="text-gray-400">
            <strong>Expires:</strong> {new Date(sessionInfo.session.expires_at * 1000).toLocaleString()}
          </div>
        </div>
      )}
      
      <div className="mb-4">
        <strong>Auth Cookies:</strong>
        {cookies.length > 0 ? (
          <ul className="list-disc pl-4 mt-1">
            {cookies.map((cookie, i) => (
              <li key={i} className="break-all">{cookie}</li>
            ))}
          </ul>
        ) : (
          <div className="text-red-400 mt-1">No auth cookies found!</div>
        )}
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={async () => {
            try {
              await supabase.auth.refreshSession();
              // Refresh the info
              const { data } = await supabase.auth.getSession();
              setSessionInfo(data);
            } catch (err: any) {
              setError(err.message);
            }
          }}
          className="bg-blue-700 px-2 py-1 rounded hover:bg-blue-600"
        >
          Refresh Session
        </button>
        
        <button
          onClick={async () => {
            try {
              await supabase.auth.signOut();
              setSessionInfo(null);
              setCookies([]);
            } catch (err: any) {
              setError(err.message);
            }
          }}
          className="bg-red-700 px-2 py-1 rounded hover:bg-red-600"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
} 