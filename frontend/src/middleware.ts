import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 大文字小文字の正規化マッピング
  const routeNormalizations: Record<string, string> = {
    '/ADMIN': '/admin',
    '/Admin': '/admin',
    '/PROJECTS': '/projects',
    '/Projects': '/projects',
    '/TASKS': '/tasks',
    '/Tasks': '/tasks',
    '/SCHEDULES': '/schedules',
    '/Schedules': '/schedules',
    '/MONITORING': '/monitoring',
    '/Monitoring': '/monitoring',
    '/EDITOR': '/editor',
    '/Editor': '/editor',
    '/NODEJS': '/nodejs',
    '/Nodejs': '/nodejs',
    '/NodeJS': '/nodejs',
    '/SETTINGS': '/settings',
    '/Settings': '/settings',
    '/LOGIN': '/login',
    '/Login': '/login',
    '/REGISTER': '/register',
    '/Register': '/register',
    '/PROFILE': '/profile',
    '/Profile': '/profile',
  };

  // パスの正規化チェック
  const normalizedPath = routeNormalizations[pathname];
  if (normalizedPath && normalizedPath !== pathname) {
    console.log(`🔄 Redirecting ${pathname} to ${normalizedPath}`);
    const url = request.nextUrl.clone();
    url.pathname = normalizedPath;
    return NextResponse.redirect(url);
  }

  // 管理者ページへのアクセス制御（追加のセキュリティ）
  if (pathname.startsWith('/admin')) {
    // ここでは基本的なパス正規化のみ行い、
    // 実際の権限チェックはAdminGuardコンポーネントで行う
    console.log(`🔒 Admin page access: ${pathname}`);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
