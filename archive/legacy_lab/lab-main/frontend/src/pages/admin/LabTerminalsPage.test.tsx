import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LabTerminalsPage } from './LabTerminalsPage'
import { terminalService } from '../../services/terminals'
import type { LabTerminal } from '../../types'

vi.mock('../../services/terminals')
vi.mock('../../utils/terminal', () => ({
  calculateTerminalUtilization: (terminal: LabTerminal) => {
    if (terminal.offline_current === 0) return 0
    const total = terminal.offline_range_end - terminal.offline_range_start + 1
    const used = terminal.offline_current - terminal.offline_range_start + 1
    return Math.round((used / total) * 100)
  },
  calculateRangeCapacity: (start: number, end: number) => end - start + 1,
}))

const mockTerminals: LabTerminal[] = [
  {
    id: 1,
    code: 'LAB1-PC',
    name: 'Lab 1 PC',
    offline_range_start: 1000,
    offline_range_end: 1999,
    offline_current: 0,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    code: 'RECEP-1',
    name: 'Reception Terminal 1',
    offline_range_start: 2000,
    offline_range_end: 2999,
    offline_current: 2050,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('LabTerminalsPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('renders lab terminals page', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Lab Terminals')).toBeInTheDocument()
    expect(screen.getByText('Add Terminal')).toBeInTheDocument()
  })

  it('displays loading state initially', () => {
    vi.mocked(terminalService.getAll).mockReturnValue(new Promise(() => {}))

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading terminals...')).toBeInTheDocument()
  })

  it('displays terminals when loaded', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
      expect(screen.getByText('Lab 1 PC')).toBeInTheDocument()
    })
  })

  it('displays error message on fetch failure', async () => {
    vi.mocked(terminalService.getAll).mockRejectedValue(
      new Error('Network error')
    )

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })
  })

  it('opens modal when Add Terminal button is clicked', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Terminal')
    fireEvent.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Terminal')).toBeInTheDocument()
    })
  })

  it('opens edit modal when Edit button is clicked', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit Terminal')).toBeInTheDocument()
    })
  })

  it('displays terminal details correctly', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
      expect(screen.getByText('Lab 1 PC')).toBeInTheDocument()
      expect(screen.getByText('1000 - 1999')).toBeInTheDocument()
    })
  })

  it('calls delete service on delete confirmation', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)
    vi.mocked(terminalService.delete).mockResolvedValue(undefined)
    globalThis.confirm = vi.fn(() => true)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(terminalService.delete).toHaveBeenCalledWith(1)
    })
  })

  it('does not call delete when cancelled', async () => {
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)
    vi.mocked(terminalService.delete).mockResolvedValue(undefined)
    globalThis.confirm = vi.fn(() => false)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    expect(terminalService.delete).not.toHaveBeenCalled()
  })

  it('creates new terminal successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)
    vi.mocked(terminalService.create).mockResolvedValue({
      id: 3,
      code: 'LAB2-PC',
      name: 'Lab 2 PC',
      offline_range_start: 3000,
      offline_range_end: 3999,
      offline_current: 0,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    const { container } = render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Terminal')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Terminal')).toBeInTheDocument()
    })

    const codeInput = container.querySelector('input[name="code"]')
    const nameInput = container.querySelector('input[name="name"]')
    const startInput = container.querySelector(
      'input[name="offline_range_start"]'
    )
    const endInput = container.querySelector('input[name="offline_range_end"]')

    if (codeInput) await user.type(codeInput, 'LAB2-PC')
    if (nameInput) await user.type(nameInput, 'Lab 2 PC')
    if (startInput) {
      await user.clear(startInput)
      await user.type(startInput, '3000')
    }
    if (endInput) {
      await user.clear(endInput)
      await user.type(endInput, '3999')
    }

    const createButton = screen.getByRole('button', {
      name: /Create Terminal/i,
    })
    await user.click(createButton)

    await waitFor(() => {
      expect(terminalService.create).toHaveBeenCalled()
    })
  })

  it('shows validation error when range start is greater than or equal to range end', async () => {
    const user = userEvent.setup()
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    const { container } = render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Terminal')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Terminal')).toBeInTheDocument()
    })

    const codeInput = container.querySelector('input[name="code"]')
    const nameInput = container.querySelector('input[name="name"]')
    const startInput = container.querySelector(
      'input[name="offline_range_start"]'
    )
    const endInput = container.querySelector('input[name="offline_range_end"]')

    if (codeInput) await user.type(codeInput, 'LAB2-PC')
    if (nameInput) await user.type(nameInput, 'Lab 2 PC')
    if (startInput) {
      await user.clear(startInput)
      await user.type(startInput, '3999')
    }
    if (endInput) {
      await user.clear(endInput)
      await user.type(endInput, '3000')
    }

    const createButton = screen.getByRole('button', {
      name: /Create Terminal/i,
    })
    await user.click(createButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Start MRN must be less than End MRN/)
      ).toBeInTheDocument()
    })
  })

  it('updates existing terminal successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)
    vi.mocked(terminalService.update).mockResolvedValue({
      ...mockTerminals[0],
      name: 'Updated Lab 1 PC',
    })

    const { container } = render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit Terminal')).toBeInTheDocument()
    })

    const nameInput = container.querySelector('input[name="name"]')
    if (nameInput) {
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Lab 1 PC')
    }

    const updateButton = screen.getByRole('button', {
      name: /Update Terminal/i,
    })
    await user.click(updateButton)

    await waitFor(() => {
      expect(terminalService.update).toHaveBeenCalledWith(1, expect.any(Object))
    })
  })

  it('closes modal when Cancel button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)

    render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Terminal')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Terminal')).toBeInTheDocument()
    })

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByText('Add New Terminal')).not.toBeInTheDocument()
    })
  })

  it('displays error message when create fails', async () => {
    const user = userEvent.setup()
    vi.mocked(terminalService.getAll).mockResolvedValue(mockTerminals)
    vi.mocked(terminalService.create).mockRejectedValue(
      new Error('Terminal code already exists')
    )

    const { container } = render(
      <BrowserRouter>
        <LabTerminalsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LAB1-PC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Terminal')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Terminal')).toBeInTheDocument()
    })

    const codeInput = container.querySelector('input[name="code"]')
    const nameInput = container.querySelector('input[name="name"]')
    const startInput = container.querySelector(
      'input[name="offline_range_start"]'
    )
    const endInput = container.querySelector('input[name="offline_range_end"]')

    if (codeInput) await user.type(codeInput, 'LAB1-PC')
    if (nameInput) await user.type(nameInput, 'Lab 1 PC')
    if (startInput) {
      await user.clear(startInput)
      await user.type(startInput, '1000')
    }
    if (endInput) {
      await user.clear(endInput)
      await user.type(endInput, '1999')
    }

    const createButton = screen.getByRole('button', {
      name: /Create Terminal/i,
    })
    await user.click(createButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Terminal code already exists/)
      ).toBeInTheDocument()
    })
  })
})
