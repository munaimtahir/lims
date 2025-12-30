import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
  it('renders login form', () => {
    const mockLogin = vi.fn()
    render(<LoginPage onLogin={mockLogin} />)

    expect(screen.getByText('Al-Shifa Laboratory')).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
  })

  it('calls onLogin with username and password on submit', async () => {
    const mockLogin = vi.fn().mockResolvedValue(undefined)
    render(<LoginPage onLogin={mockLogin} />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')
    const loginButton = screen.getByRole('button', { name: 'Login' })

    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    fireEvent.change(passwordInput, { target: { value: 'testpass' } })
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'testpass')
    })
  })

  it('shows error message on login failure', async () => {
    const mockLogin = vi
      .fn()
      .mockRejectedValue(new Error('Invalid credentials'))
    render(<LoginPage onLogin={mockLogin} />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')
    const loginButton = screen.getByRole('button', { name: 'Login' })

    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } })
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('shows loading state during login', async () => {
    const mockLogin = vi
      .fn()
      .mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )
    render(<LoginPage onLogin={mockLogin} />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')
    const loginButton = screen.getByRole('button', { name: 'Login' })

    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    fireEvent.change(passwordInput, { target: { value: 'testpass' } })
    fireEvent.click(loginButton)

    expect(screen.getByText('Logging in...')).toBeInTheDocument()
    expect(loginButton).toBeDisabled()
  })

  it('shows demo credentials', () => {
    const mockLogin = vi.fn()
    render(<LoginPage onLogin={mockLogin} />)

    expect(screen.getByText('Demo credentials:')).toBeInTheDocument()
    expect(screen.getByText('admin / admin123')).toBeInTheDocument()
  })

  it('requires username and password', () => {
    const mockLogin = vi.fn()
    render(<LoginPage onLogin={mockLogin} />)

    const usernameInput = screen.getByLabelText('Username') as HTMLInputElement
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement

    expect(usernameInput.required).toBe(true)
    expect(passwordInput.required).toBe(true)
  })
})
