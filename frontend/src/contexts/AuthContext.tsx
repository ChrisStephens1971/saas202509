import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { authApi } from '../api/auth'
import type { LoginRequest } from '../types/api'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check if user is authenticated on mount
    const authenticated = authApi.isAuthenticated()
    setIsAuthenticated(authenticated)
    setIsLoading(false)
  }, [])

  const login = async (credentials: LoginRequest) => {
    setError(null)
    setIsLoading(true)

    try {
      const response = await authApi.login(credentials)
      authApi.setTokens(response.access, response.refresh)
      setIsAuthenticated(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    authApi.logout()
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        login,
        logout,
        error,
      }}
    >
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
