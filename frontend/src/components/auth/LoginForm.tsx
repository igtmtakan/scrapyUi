'use client'

import React, { useState } from 'react'
import { Eye, EyeOff, Mail, Lock, LogIn } from 'lucide-react'

interface LoginFormProps {
  onLogin: (email: string, password: string) => Promise<void>
  onSwitchToRegister: () => void
  loading?: boolean
  error?: string
}

export default function LoginForm({ 
  onLogin, 
  onSwitchToRegister, 
  loading = false, 
  error 
}: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({})

  const validateForm = () => {
    const errors: {[key: string]: string} = {}
    
    if (!email) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please enter a valid email address'
    }
    
    if (!password) {
      errors.password = 'Password is required'
    }
    
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    try {
      await onLogin(email, password)
    } catch (error) {
      // エラーは親コンポーネントで処理
    }
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
        <div className="text-center mb-8">
          <LogIn className="w-12 h-12 text-blue-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white">Sign In</h2>
          <p className="text-gray-400 mt-2">Welcome back to Scrapy UI</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full pl-10 pr-3 py-3 bg-gray-700 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  validationErrors.email ? 'border-red-500' : 'border-gray-600'
                }`}
                placeholder="Enter your email"
                disabled={loading}
              />
            </div>
            {validationErrors.email && (
              <p className="mt-1 text-sm text-red-400">{validationErrors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full pl-10 pr-12 py-3 bg-gray-700 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  validationErrors.password ? 'border-red-500' : 'border-gray-600'
                }`}
                placeholder="Enter your password"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-300" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 hover:text-gray-300" />
                )}
              </button>
            </div>
            {validationErrors.password && (
              <p className="mt-1 text-sm text-red-400">{validationErrors.password}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Signing In...
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5 mr-2" />
                Sign In
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-gray-400">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToRegister}
              className="text-blue-400 hover:text-blue-300 font-medium"
              disabled={loading}
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
