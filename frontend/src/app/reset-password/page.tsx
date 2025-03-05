'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import supabase from '@/lib/supabase';

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  useEffect(() => {
    // Process the recovery token in the URL to complete the password reset flow
    const access_token = searchParams.get('access_token');
    const type = searchParams.get('type');
    if (access_token && type === 'recovery') {
      supabase.auth.setSession({ access_token: searchParams.get('access_token')!, refresh_token: '' }).then(({ error }) => {
        if (error) {
          setError('Error processing reset token: ' + error.message);
        }
      });
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      if (error) throw error;
      setInfo('Password updated successfully. Redirecting to sign in...');
      setTimeout(() => {
        router.push('/signin');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Error updating password');
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-indigo-50 to-white">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-indigo-900 mb-2">Research Assistant</h1>
        <p className="text-indigo-600 text-lg font-medium">Your AI-powered research companion</p>
      </header>
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 w-full max-w-sm">
        <h2 className="text-2xl font-bold text-indigo-900 mb-4">Reset Password</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
              required
            />
          </div>
          {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
          {info && <p className="text-green-500 text-sm mb-2">{info}</p>}
          <button 
            type="submit" 
            className="w-full py-3 px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Reset Password
          </button>
        </form>
      </div>
    </div>
  );
}
