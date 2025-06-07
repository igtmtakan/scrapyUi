'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Eye, EyeOff, Code, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, isInitialized, isLoading, error, clearError, initialize } = useAuthStore();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [initTimeout, setInitTimeout] = useState(false);

  // 初期化処理
  useEffect(() => {
    console.log('🔍 Login page mount - isInitialized:', isInitialized);

    if (!isInitialized) {
      console.log('🚀 Initializing auth store from login page...');
      initialize().catch(error => {
        console.error('❌ Initialization failed:', error);
        // 初期化に失敗した場合でも初期化済みとしてマーク
        useAuthStore.setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isInitialized: true,
          error: 'Initialization failed'
        });
      });
    }

    // 初期化タイムアウト（5秒）
    const timeout = setTimeout(() => {
      if (!isInitialized) {
        console.warn('⏰ Initialization timeout, forcing initialization');
        setInitTimeout(true);
        useAuthStore.setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isInitialized: true
        });
      }
    }, 5000);

    return () => clearTimeout(timeout);
  }, [isInitialized, initialize]);

  // 認証済みユーザーのリダイレクト処理
  useEffect(() => {
    if (!isInitialized) return; // 初期化完了まで待機

    if (isAuthenticated) {
      const redirectTo = searchParams.get('redirect') || '/projects';
      console.log('🔄 Authenticated user detected, redirecting to:', redirectTo);

      // 現在のパスがログインページの場合のみリダイレクト
      if (typeof window !== 'undefined' && window.location.pathname === '/login') {
        router.push(redirectTo);
      }
    }
  }, [isInitialized, isAuthenticated, router, searchParams]);

  useEffect(() => {
    clearError();
  }, [clearError]);

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      await login(formData.email, formData.password);
      // リダイレクト処理はuseEffectで行われるため、ここでは何もしない
    } catch (error) {
      // Error is handled by the store
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // 初期化中の場合はローディング表示
  if (!isInitialized && !initTimeout) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">認証状態を確認中...</p>
          <p className="text-gray-400 text-sm mt-2">しばらくお待ちください</p>

          {/* 緊急ボタン */}
          <button
            onClick={() => {
              console.log('🚨 Emergency initialization');
              useAuthStore.setState({
                user: null,
                isAuthenticated: false,
                isLoading: false,
                isInitialized: true
              });
            }}
            className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
          >
            スキップしてログインページを表示
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center">
              <Code className="w-8 h-8 text-white" />
            </div>
          </div>
          <h2 className="mt-6 text-3xl font-bold text-white">
            Welcome back
          </h2>
          <p className="mt-2 text-gray-300">
            Sign in to your Scrapy Web UI account
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Global Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className={`
                  w-full px-3 py-2 border rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  ${validationErrors.email ? 'border-red-300' : 'border-gray-300'}
                `}
                placeholder="Enter your email"
              />
              {validationErrors.email && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`
                    w-full px-3 py-2 border rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10
                    ${validationErrors.password ? 'border-red-300' : 'border-gray-300'}
                  `}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5 text-gray-400" />
                  ) : (
                    <Eye className="w-5 h-5 text-gray-400" />
                  )}
                </button>
              </div>
              {validationErrors.password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
              )}
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                  Remember me
                </label>
              </div>
              <Link href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-500">
                Forgot password?
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Signing in...</span>
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link href="/register" className="font-medium text-blue-600 hover:text-blue-500">
                Sign up
              </Link>
            </p>
          </div>
        </div>

        {/* Demo Credentials */}
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <p className="text-gray-300 text-sm mb-2">Demo Credentials:</p>
          <div className="space-y-1">
            <p className="text-gray-400 text-xs">
              Admin: admin@scrapyui.com | admin123456
            </p>
            <p className="text-gray-400 text-xs">
              Demo: demo@example.com | demo12345
            </p>
          </div>

          {/* デバッグボタン */}
          {(error || initTimeout) && (
            <div className="mt-3 pt-3 border-t border-gray-600">
              <button
                onClick={() => {
                  console.log('🧹 Clearing auth cache...');
                  if (typeof window !== 'undefined') {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('auth-storage');
                  }
                  useAuthStore.setState({
                    user: null,
                    isAuthenticated: false,
                    isLoading: false,
                    error: null,
                    isInitialized: true
                  });
                  window.location.reload();
                }}
                className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
              >
                認証データをクリアして再読み込み
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
