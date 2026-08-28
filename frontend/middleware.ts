import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Protect pages under /admin and /notifications unless a valid auth cookie or
// Authorization header is present. Note: middleware cannot read localStorage;
// for SSR protection prefer cookie-based tokens or server sessions.

const PROTECTED_PATHS = ['/admin', '/notifications'];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // only evaluate top-level protected paths
  if (!PROTECTED_PATHS.some(p => pathname.startsWith(p))) return NextResponse.next();

  const authHeader = req.headers.get('authorization');
  const authCookie = req.cookies.get('auth_access')?.value;

  if (authHeader || authCookie) {
    return NextResponse.next();
  }

  // redirect to login if not authenticated
  const loginUrl = new URL('/auth/login', req.url);
  loginUrl.searchParams.set('redirect', pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/admin/:path*', '/notifications/:path*'],
};
