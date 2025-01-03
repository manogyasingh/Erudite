import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token'); // Check for authentication token
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') || 
                     request.nextUrl.pathname.startsWith('/register');

  // Redirect to login if on the home page (/) and not authenticated
  if (request.nextUrl.pathname === '/' && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect to login if trying to access protected routes without a token
  if (!token && !isAuthPage) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect to home if trying to access auth pages while logged in
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
