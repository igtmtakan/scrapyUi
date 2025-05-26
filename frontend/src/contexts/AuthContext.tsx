'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  email: string
  username: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  avatar_url?: string
  timezone: string
  preferences: Record<string, any>
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  updateUser: (userData: Partial<User>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!token

  // 初期化時にローカルストレージからトークンを読み込み
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('access_token')
        const storedRefreshToken = localStorage.getItem('refresh_token')
        
        if (storedToken && storedRefreshToken) {
          setToken(storedToken)
          
          // ユーザー情報を取得
          try {
            await getCurrentUser(storedToken)
          } catch (error) {
            // トークンが無効な場合はリフレッシュを試行
            try {
              await refreshTokenWithRefreshToken(storedRefreshToken)
            } catch (refreshError) {
              // リフレッシュも失敗した場合はログアウト
              logout()
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const data = await response.json()
      
      // トークンを保存
      setToken(data.access_token)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      // ユーザー情報を取得
      await getCurrentUser(data.access_token)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    
    // ログアウトAPIを呼び出し（ベストエフォート）
    if (token) {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }).catch(() => {
        // エラーは無視（既にローカル状態はクリア済み）
      })
    }
  }

  const refreshToken = async () => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token')
      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      await refreshTokenWithRefreshToken(refreshTokenValue)
    } catch (error) {
      console.error('Token refresh error:', error)
      logout()
      throw error
    }
  }

  const refreshTokenWithRefreshToken = async (refreshTokenValue: string) => {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshTokenValue}`,
      },
    })

    if (!response.ok) {
      throw new Error('Token refresh failed')
    }

    const data = await response.json()
    
    setToken(data.access_token)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)

    await getCurrentUser(data.access_token)
  }

  const getCurrentUser = async (accessToken: string) => {
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to get user info')
    }

    const userData = await response.json()
    setUser(userData)
  }

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData })
    }
  }

  // 自動トークンリフレッシュ
  useEffect(() => {
    if (!token || !isAuthenticated) return

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto refresh failed:', error)
        // 自動リフレッシュが失敗した場合はログアウト
        logout()
      }
    }, 25 * 60 * 1000) // 25分ごと（トークンの有効期限30分より少し前）

    return () => clearInterval(refreshInterval)
  }, [token, isAuthenticated])

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshToken,
    updateUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// 認証が必要なコンポーネントをラップするHOC
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth()

    if (isLoading) {
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading...</p>
          </div>
        </div>
      )
    }

    if (!isAuthenticated) {
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-white mb-4">Authentication Required</h2>
            <p className="text-gray-400">Please log in to access this page.</p>
          </div>
        </div>
      )
    }

    return <Component {...props} />
  }
}
