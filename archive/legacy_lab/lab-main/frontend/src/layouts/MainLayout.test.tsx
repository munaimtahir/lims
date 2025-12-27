import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { MainLayout } from './MainLayout'

describe('MainLayout', () => {
  it('renders header with Al-Shifa Laboratory title', () => {
    render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )

    expect(screen.getByText('Al-Shifa Laboratory')).toBeInTheDocument()
  })

  it('shows navigation when user is logged in', () => {
    const mockUser = { username: 'testuser', role: 'ADMIN' }

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} />
      </BrowserRouter>
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Lab')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('displays user info when logged in', () => {
    const mockUser = { username: 'testuser', role: 'ADMIN' }

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} />
      </BrowserRouter>
    )

    expect(screen.getByText('testuser')).toBeInTheDocument()
    expect(screen.getByText('ADMIN')).toBeInTheDocument()
  })

  it('hides navigation when user is not logged in', () => {
    render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )

    expect(screen.queryByText('Home')).not.toBeInTheDocument()
    expect(screen.queryByText('Lab')).not.toBeInTheDocument()
  })

  it('shows logout button when user is logged in', () => {
    const mockUser = { username: 'testuser', role: 'ADMIN' }
    const mockLogout = () => {}

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} onLogout={mockLogout} />
      </BrowserRouter>
    )

    expect(screen.getByText('Logout')).toBeInTheDocument()
  })

  it('filters navigation based on user role', () => {
    const mockUser = { username: 'testuser', role: 'RECEPTION' }

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} />
      </BrowserRouter>
    )

    // Reception should see Home and Lab but not Settings
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Lab')).toBeInTheDocument()
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
  })

  it('shows hamburger menu button on mobile when user is logged in', () => {
    const mockUser = { username: 'testuser', role: 'ADMIN' }

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} />
      </BrowserRouter>
    )

    const menuButton = screen.getByLabelText('Toggle menu')
    expect(menuButton).toBeInTheDocument()
  })

  it('toggles mobile menu when hamburger button is clicked', async () => {
    const user = userEvent.setup()
    const mockUser = { username: 'testuser', role: 'ADMIN' }

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} />
      </BrowserRouter>
    )

    const menuButton = screen.getByLabelText('Toggle menu')

    // Initially mobile menu should not be expanded
    expect(menuButton).toHaveAttribute('aria-expanded', 'false')

    // Click to open menu
    await user.click(menuButton)
    expect(menuButton).toHaveAttribute('aria-expanded', 'true')

    // Click to close menu
    await user.click(menuButton)
    expect(menuButton).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes mobile menu on ESC key press', async () => {
    const user = userEvent.setup()
    const mockUser = { username: 'testuser', role: 'ADMIN' }

    render(
      <BrowserRouter>
        <MainLayout user={mockUser} />
      </BrowserRouter>
    )

    const menuButton = screen.getByLabelText('Toggle menu')

    // Open menu
    await user.click(menuButton)
    expect(menuButton).toHaveAttribute('aria-expanded', 'true')

    // Press ESC to close
    await user.keyboard('{Escape}')
    expect(menuButton).toHaveAttribute('aria-expanded', 'false')
  })
})
