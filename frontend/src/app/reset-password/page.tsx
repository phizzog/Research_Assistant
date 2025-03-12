'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ResetPasswordPage() {
  const router = useRouter();

  // For MVP, automatically redirect to dashboard
  useEffect(() => {
    console.log('MVP mode: Bypassing authentication, redirecting to dashboard');
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-indigo-50 to-white">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-indigo-900 mb-2">Research Assistant</h1>
        <p className="text-indigo-600 text-lg font-medium">Your AI-powered research companion</p>
      </header>
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 w-full max-w-sm">
        <h2 className="text-2xl font-bold text-indigo-900 mb-4">Redirecting to Dashboard...</h2>
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    </div>
  );
}
