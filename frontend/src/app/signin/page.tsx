'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import supabase from '@/lib/supabase';

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;
      
      // On successful sign in, redirect to the research page
      router.push('/research');
    } catch (err: any) {
      setError(err.message || 'Error signing in');
    }
  };

  const handleForgotPassword = async () => {
    setError('');
    setInfo('');

    if (!email) {
      setError('Please enter your email first.');
      return;
    }

    try {
      const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
        // Adjust the redirect URL as needed
        redirectTo: `${window.location.origin}/reset-password`,
      });
      if (error) throw error;
      setInfo('Password reset email sent. Please check your inbox.');
    } catch (err: any) {
      setError(err.message || 'Error sending password reset email.');
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-indigo-50 to-white">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-indigo-900 mb-2">Research Assistant</h1>
        <p className="text-indigo-600 text-lg font-medium">Your AI-powered research companion</p>
      </header>
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 w-full max-w-sm">
        <h2 className="text-2xl font-bold text-indigo-900 mb-4">Sign In</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
              required
            />
          </div>
          <div className="mb-4 text-right">
            <button 
              type="button"
              onClick={handleForgotPassword}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Forgot password?
            </button>
          </div>
          {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
          {info && <p className="text-green-500 text-sm mb-2">{info}</p>}
          <button 
            type="submit" 
            className="w-full py-3 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Sign In
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <button 
            type="button" 
            onClick={() => router.push('/signup')} 
            className="text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Create one
          </button>
        </p>
      </div>
    </div>
  );
}
