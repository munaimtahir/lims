import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ProtectedRoute, TEMPORARY_FULL_ACCESS_MODE } from './ProtectedRoute'
import { useAuth } from '../hooks/useAuth'
import type { User } from '../types'

// Mock useAuth hook
vi.mock('../hooks/useAuth')

const mockUseAuth = vi.mocked(useAuth)

function TestComponent() {
  return <div>Protected Content</div>
}

describe('ProtectedRoute', () => {
  it('shows loading state while checking authentication', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    // Should not render protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: 'test', role: 'ADMIN' } as User,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it.skipIf(TEMPORARY_FULL_ACCESS_MODE)(
    'shows access denied when user lacks required role',
    () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, username: 'test', role: 'RECEPTION' } as User,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        logout: vi.fn(),
      })

      render(
        <BrowserRouter>
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      )

      expect(screen.getByText('Access Denied')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    }
  )

  it('renders children when user has required role', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: 'test', role: 'ADMIN' } as User,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute allowedRoles={['ADMIN', 'RECEPTION']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})
