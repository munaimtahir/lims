import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

// Mock child components
vi.mock('./hooks/useAuth', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

vi.mock('./pages/LoginPage', () => ({
  LoginPage: () => <div data-testid="login-page">Login Page</div>,
}))

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    // Should render login page when not authenticated
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
  })
})
