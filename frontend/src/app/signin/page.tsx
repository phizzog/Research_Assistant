'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth } from '@/lib/firebase';
import { signInWithEmailAndPassword } from 'firebase/auth';

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await signInWithEmailAndPassword(auth, email, password);
      // On successful sign in, redirect to the research page
      router.push('/research');
    } catch (err: any) {
      setError(err.message || 'Error signing in');
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-indigo-50 to-white">
      <h1 className="text-3xl font-bold text-indigo-900 mb-4">Sign In</h1>
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-full max-w-sm">
        <div className="mb-4">
          <label className="block text-gray-700">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 p-2 border rounded w-full"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block text-gray-700">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 p-2 border rounded w-full"
            required
          />
        </div>
        {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
        <button type="submit" className="w-full bg-indigo-600 text-white p-2 rounded">
          Sign In
        </button>
      </form>

      {/* Link to sign up page */}
      <div className="mt-4">
        <p>
          Don't have an account?{' '}
          <span
            onClick={() => router.push('/signup')}
            className="text-indigo-600 underline cursor-pointer"
          >
            Create one
          </span>
        </p>
      </div>
    </div>
  );
}
