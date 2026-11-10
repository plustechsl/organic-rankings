import { NextResponse, type NextRequest } from "next/server";
import { DEFAULT_LOCALE, isLocale } from "@/app/lib/i18n";

const LOCALE_COOKIE = "NEXT_LOCALE";

function detectLocale(request: NextRequest): string {
  const cookie = request.cookies.get(LOCALE_COOKIE)?.value;

  if (isLocale(cookie)) {
    return cookie;
  }

  const header = request.headers.get("accept-language") ?? "";
  const preferred = header.split(",")[0]?.split("-")[0]?.trim().toLowerCase();

  if (isLocale(preferred)) {
    return preferred;
  }

  return DEFAULT_LOCALE;
}

function shouldSkip(pathname: string): boolean {
  return (
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    /\.[^/]+$/.test(pathname)
  );
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (shouldSkip(pathname)) {
    return NextResponse.next();
  }

  const firstSegment = pathname.split("/")[1] ?? "";

  if (isLocale(firstSegment)) {
    const response = NextResponse.next();
    response.cookies.set(LOCALE_COOKIE, firstSegment, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
    });
    return response;
  }

  const locale = detectLocale(request);

  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname === "/" ? "" : pathname}`;

  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
