import { NextResponse, type NextRequest } from "next/server";

// Inject the current pathname as a request header so server components
// (e.g. AppShell's onboarding gate) can read it via next/headers.
export function middleware(req: NextRequest) {
  const headers = new Headers(req.headers);
  headers.set("x-pathname", req.nextUrl.pathname);
  return NextResponse.next({ request: { headers } });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
