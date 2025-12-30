import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { authService } from '../services/auth'
import type { User } from '../types'

/**
 * Interface for the authentication context.
 */
interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

/**
 * Provides authentication context to its children.
 * @param {object} props - The component props.
 * @param {ReactNode} props.children - The child components.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const currentUser = authService.getCurrentUser()
    if (currentUser && authService.isAuthenticated()) {
      setUser(currentUser)
    }
    setIsLoading(false)
  }, [])

  /**
   * Logs in a user.
   * @param {string} username - The user's username.
   * @param {string} password - The user's password.
   */
  const login = async (username: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await authService.login(username, password)
      setUser(response.user)
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Logs out the current user.
   */
  const logout = async () => {
    setIsLoading(true)
    try {
      await authService.logout()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Custom hook for accessing the authentication context.
 * @returns {AuthContextType} The authentication context.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
