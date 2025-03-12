import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(req: NextRequest) {
  // For MVP, we're bypassing authentication checks
  // Simply allow access to all routes
  return NextResponse.next();
}

// Keep the matcher to maintain the structure for future auth implementation
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/research/:path*',
    '/signin',
    '/signup',
    '/reset-password',
  ],
}; 