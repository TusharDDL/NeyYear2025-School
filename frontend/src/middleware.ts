import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Get the pathname of the request (e.g. /, /dashboard)
  const path = request.nextUrl.pathname;

  // Define public paths that don't require authentication
  const isPublicPath =
    path === "/login" || path === "/register" || path === "/";

  // Get the token from cookies
  const token = request.cookies.get("accessToken")?.value || "";

  // If the user is on a public path and has a token, redirect to dashboard
  if (isPublicPath && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // If the user is not on a public path and doesn't have a token,
  // redirect to login
  if (!isPublicPath && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
