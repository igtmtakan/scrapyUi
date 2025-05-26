'use client';

import React, { useState, useEffect } from 'react';

interface ClientOnlyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * クライアントサイドでのみレンダリングするコンポーネント
 * Hydrationエラーを防ぐために使用
 */
export default function ClientOnly({ children, fallback = null }: ClientOnlyProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
