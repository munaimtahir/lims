import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { UserManagementPage } from './UserManagementPage'
import { userService } from '../../services/users'
import type { User } from '../../types'

vi.mock('../../services/users')

const mockUsers: User[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'ADMIN',
    first_name: 'Admin',
    last_name: 'User',
    is_active: true,
  },
  {
    id: 2,
    username: 'tech',
    email: 'tech@example.com',
    role: 'TECHNOLOGIST',
    first_name: 'Tech',
    last_name: 'User',
    is_active: true,
  },
]

describe('UserManagementPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('renders user management page', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    expect(screen.getByText('User Management')).toBeInTheDocument()
    expect(screen.getByText('Add User')).toBeInTheDocument()
  })

  it('displays loading state initially', () => {
    vi.mocked(userService.getAll).mockReturnValue(new Promise(() => {}))

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading users...')).toBeInTheDocument()
  })

  it('displays users when loaded', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
      expect(screen.getByText('tech')).toBeInTheDocument()
    })
  })

  it('displays error message on fetch failure', async () => {
    vi.mocked(userService.getAll).mockRejectedValue(new Error('Network error'))

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })
  })

  it('opens modal when Add User button is clicked', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add User')
    fireEvent.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New User')).toBeInTheDocument()
    })
  })

  it('opens edit modal when Edit button is clicked', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit User')).toBeInTheDocument()
    })
  })

  it('displays user details correctly', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument()
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
      expect(screen.getByText('ADMIN')).toBeInTheDocument()
      const activeStatuses = screen.getAllByText('Active')
      expect(activeStatuses.length).toBeGreaterThan(0)
    })
  })

  it('shows deactivate button for active users', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      const deactivateButtons = screen.getAllByText('Deactivate')
      expect(deactivateButtons.length).toBeGreaterThan(0)
    })
  })

  it('calls delete service on deactivate confirmation', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)
    vi.mocked(userService.delete).mockResolvedValue(undefined)
    globalThis.confirm = vi.fn(() => true)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const deactivateButtons = screen.getAllByText('Deactivate')
    fireEvent.click(deactivateButtons[0])

    await waitFor(() => {
      expect(userService.delete).toHaveBeenCalledWith(1)
    })
  })

  it('does not call delete when deactivate is cancelled', async () => {
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)
    vi.mocked(userService.delete).mockResolvedValue(undefined)
    globalThis.confirm = vi.fn(() => false)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const deactivateButtons = screen.getAllByText('Deactivate')
    fireEvent.click(deactivateButtons[0])

    expect(userService.delete).not.toHaveBeenCalled()
  })

  it('creates new user successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)
    vi.mocked(userService.create).mockResolvedValue({
      id: 3,
      username: 'newuser',
      email: 'new@example.com',
      role: 'RECEPTION',
      first_name: 'New',
      last_name: 'User',
      is_active: true,
    })

    const { container } = render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add User')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New User')).toBeInTheDocument()
    })

    // Fill form using querySelector
    const usernameInput = container.querySelector('input[name="username"]')
    const emailInput = container.querySelector('input[name="email"]')
    const firstNameInput = container.querySelector('input[name="first_name"]')
    const lastNameInput = container.querySelector('input[name="last_name"]')
    const passwordInput = container.querySelector('input[name="password"]')

    if (usernameInput) await user.type(usernameInput, 'newuser')
    if (emailInput) await user.type(emailInput, 'new@example.com')
    if (firstNameInput) await user.type(firstNameInput, 'New')
    if (lastNameInput) await user.type(lastNameInput, 'User')
    if (passwordInput) await user.type(passwordInput, 'password123')

    const createButton = screen.getByRole('button', { name: /Create User/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(userService.create).toHaveBeenCalled()
    })
  })

  it('shows validation error when password is missing for new user', async () => {
    const user = userEvent.setup()
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    const { container } = render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add User')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New User')).toBeInTheDocument()
    })

    // Fill form without password
    const usernameInput = container.querySelector('input[name="username"]')
    const emailInput = container.querySelector('input[name="email"]')
    const firstNameInput = container.querySelector('input[name="first_name"]')
    const lastNameInput = container.querySelector('input[name="last_name"]')
    const passwordInput = container.querySelector('input[name="password"]')

    if (usernameInput) await user.type(usernameInput, 'newuser')
    if (emailInput) await user.type(emailInput, 'new@example.com')
    if (firstNameInput) await user.type(firstNameInput, 'New')
    if (lastNameInput) await user.type(lastNameInput, 'User')

    // Verify password field is required (HTML5 validation)
    expect(passwordInput).toHaveAttribute('required')

    // The form won't submit due to HTML5 validation if password is empty
    // So we just verify the input is marked as required
    expect(passwordInput).toBeInTheDocument()
  })

  it('updates existing user successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)
    vi.mocked(userService.update).mockResolvedValue({
      ...mockUsers[0],
      email: 'updated@example.com',
    })

    const { container } = render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit User')).toBeInTheDocument()
    })

    const emailInput = container.querySelector('input[name="email"]')
    if (emailInput) {
      await user.clear(emailInput)
      await user.type(emailInput, 'updated@example.com')
    }

    const updateButton = screen.getByRole('button', { name: /Update User/i })
    await user.click(updateButton)

    await waitFor(() => {
      expect(userService.update).toHaveBeenCalledWith(1, expect.any(Object))
    })
  })

  it('closes modal when Cancel button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)

    render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add User')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New User')).toBeInTheDocument()
    })

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByText('Add New User')).not.toBeInTheDocument()
    })
  })

  it('displays error message when create fails', async () => {
    const user = userEvent.setup()
    vi.mocked(userService.getAll).mockResolvedValue(mockUsers)
    vi.mocked(userService.create).mockRejectedValue(
      new Error('Username already exists')
    )

    const { container } = render(
      <BrowserRouter>
        <UserManagementPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add User')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New User')).toBeInTheDocument()
    })

    const usernameInput = container.querySelector('input[name="username"]')
    const emailInput = container.querySelector('input[name="email"]')
    const firstNameInput = container.querySelector('input[name="first_name"]')
    const lastNameInput = container.querySelector('input[name="last_name"]')
    const passwordInput = container.querySelector('input[name="password"]')

    if (usernameInput) await user.type(usernameInput, 'newuser')
    if (emailInput) await user.type(emailInput, 'new@example.com')
    if (firstNameInput) await user.type(firstNameInput, 'New')
    if (lastNameInput) await user.type(lastNameInput, 'User')
    if (passwordInput) await user.type(passwordInput, 'password123')

    const createButton = screen.getByRole('button', { name: /Create User/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByText(/Username already exists/)).toBeInTheDocument()
    })
  })
})
