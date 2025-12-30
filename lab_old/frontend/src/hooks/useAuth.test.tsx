import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from './useAuth'
import { authService } from '../services/auth'

// Mock authService
vi.mock('../services/auth', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
  },
}))

import type { User } from '../types'

// Test component that uses useAuth
function TestComponent() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth()

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="user">{user ? user.username : 'none'}</div>
      <button onClick={() => login('testuser', 'testpass')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('provides auth context to children', () => {
    vi.mocked(authService.getCurrentUser).mockReturnValue(null)
    vi.mocked(authService.isAuthenticated).mockReturnValue(false)

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('loads existing user on mount', async () => {
    const mockUser = { id: 1, username: 'testuser', role: 'ADMIN' } as User
    vi.mocked(authService.getCurrentUser).mockReturnValue(mockUser)
    vi.mocked(authService.isAuthenticated).mockReturnValue(true)

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
    })

    expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
    expect(screen.getByTestId('user')).toHaveTextContent('testuser')
  })

  it('handles login successfully', async () => {
    const mockUser = { id: 1, username: 'testuser', role: 'ADMIN' } as User
    vi.mocked(authService.getCurrentUser).mockReturnValue(null)
    vi.mocked(authService.isAuthenticated).mockReturnValue(false)
    vi.mocked(authService.login).mockResolvedValue({
      access: 'token',
      refresh: 'refresh',
      user: mockUser,
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    const loginButton = screen.getByText('Login')
    loginButton.click()

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
      expect(screen.getByTestId('user')).toHaveTextContent('testuser')
    })
  })

  it('handles logout successfully', async () => {
    const mockUser = { id: 1, username: 'testuser', role: 'ADMIN' } as User
    vi.mocked(authService.getCurrentUser).mockReturnValue(mockUser)
    vi.mocked(authService.isAuthenticated).mockReturnValue(true)
    vi.mocked(authService.logout).mockResolvedValue()

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
    })

    const logoutButton = screen.getByText('Logout')
    logoutButton.click()

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
      expect(screen.getByTestId('user')).toHaveTextContent('none')
    })
  })

  it('throws error when used outside AuthProvider', () => {
    // Suppress console errors for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(
        <BrowserRouter>
          <TestComponent />
        </BrowserRouter>
      )
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleSpy.mockRestore()
  })
})
