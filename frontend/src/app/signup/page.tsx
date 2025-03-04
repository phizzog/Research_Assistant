'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import supabase from '@/lib/supabase';

export default function SignUpPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) throw error;
      
      // Redirect to sign in page after successful account creation
      router.push('/signin');
    } catch (err: any) {
      setError(err.message || 'Error creating account');
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-indigo-50 to-white">
      {/* Shared Header */}
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-indigo-900 mb-2">Research Assistant</h1>
        <p className="text-indigo-600 text-lg font-medium">Your AI-powered research companion</p>
      </header>

      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 w-full max-w-sm">
        <h2 className="text-2xl font-bold text-indigo-900 mb-4">Create an Account</h2>
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
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
              required
            />
          </div>
          {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
          <button 
            type="submit" 
            className="w-full py-3 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Sign Up
          </button>
          <p className="mt-4 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <button 
              type="button" 
              onClick={() => router.push('/signin')} 
              className="text-indigo-600 hover:text-indigo-800 font-medium"
            >
              Sign In
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}
