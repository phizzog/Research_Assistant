// app/page.tsx

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function IndexPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard on load
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-indigo-50 to-white">
      <div className="animate-pulse flex flex-col items-center">
        <div className="h-12 w-12 mb-4 rounded-full bg-indigo-200"></div>
        <h2 className="text-xl font-semibold text-indigo-900 mb-2">Redirecting to Dashboard...</h2>
      </div>
    </div>
  );
}

