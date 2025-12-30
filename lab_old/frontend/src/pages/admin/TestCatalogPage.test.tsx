import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { TestCatalogPage } from './TestCatalogPage'
import { catalogService } from '../../services/catalog'
import type { TestCatalog } from '../../types'

vi.mock('../../services/catalog')

const mockTests: TestCatalog[] = [
  {
    id: 1,
    code: 'CBC',
    name: 'Complete Blood Count',
    description: 'Blood test',
    category: 'Hematology',
    sample_type: 'Blood',
    price: 500,
    turnaround_time_hours: 24,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    code: 'LFT',
    name: 'Liver Function Test',
    description: 'Liver panel',
    category: 'Chemistry',
    sample_type: 'Serum',
    price: 800,
    turnaround_time_hours: 48,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('TestCatalogPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('renders test catalog page', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Test Catalog')).toBeInTheDocument()
    expect(screen.getByText('Add Test')).toBeInTheDocument()
  })

  it('displays loading state initially', () => {
    vi.mocked(catalogService.getAll).mockReturnValue(new Promise(() => {}))

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading tests...')).toBeInTheDocument()
  })

  it('displays tests when loaded', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
      expect(screen.getByText('Complete Blood Count')).toBeInTheDocument()
    })
  })

  it('displays error message on fetch failure', async () => {
    vi.mocked(catalogService.getAll).mockRejectedValue(
      new Error('Network error')
    )

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })
  })

  it('opens modal when Add Test button is clicked', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Test')
    fireEvent.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Test')).toBeInTheDocument()
    })
  })

  it('opens edit modal when Edit button is clicked', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit Test')).toBeInTheDocument()
    })
  })

  it('displays test details correctly', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
      expect(screen.getByText('Complete Blood Count')).toBeInTheDocument()
      expect(screen.getByText('Hematology')).toBeInTheDocument()
      expect(screen.getByText('Blood')).toBeInTheDocument()
      expect(screen.getByText('Rs. 500.00')).toBeInTheDocument()
    })
  })

  it('calls delete service on delete confirmation', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)
    vi.mocked(catalogService.delete).mockResolvedValue(undefined)
    globalThis.confirm = vi.fn(() => true)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(catalogService.delete).toHaveBeenCalledWith(1)
    })
  })

  it('does not call delete when cancelled', async () => {
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)
    vi.mocked(catalogService.delete).mockResolvedValue(undefined)
    globalThis.confirm = vi.fn(() => false)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    expect(catalogService.delete).not.toHaveBeenCalled()
  })

  it('creates new test successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)
    vi.mocked(catalogService.create).mockResolvedValue({
      id: 3,
      code: 'RFT',
      name: 'Renal Function Test',
      description: 'Kidney panel',
      category: 'Chemistry',
      sample_type: 'Serum',
      price: 600,
      turnaround_time_hours: 24,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    const { container } = render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Test')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Test')).toBeInTheDocument()
    })

    const codeInput = container.querySelector('input[name="code"]')
    const nameInput = container.querySelector('input[name="name"]')
    const categoryInput = container.querySelector('input[name="category"]')
    const sampleTypeInput = container.querySelector('input[name="sample_type"]')
    const priceInput = container.querySelector('input[name="price"]')

    if (codeInput) await user.type(codeInput, 'RFT')
    if (nameInput) await user.type(nameInput, 'Renal Function Test')
    if (categoryInput) await user.type(categoryInput, 'Chemistry')
    if (sampleTypeInput) await user.type(sampleTypeInput, 'Serum')
    if (priceInput) {
      await user.clear(priceInput)
      await user.type(priceInput, '600')
    }

    const createButton = screen.getByRole('button', { name: /Create Test/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(catalogService.create).toHaveBeenCalled()
    })
  })

  it('shows validation error when price is zero or negative', async () => {
    const user = userEvent.setup()
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    const { container } = render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Test')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Test')).toBeInTheDocument()
    })

    const codeInput = container.querySelector('input[name="code"]')
    const nameInput = container.querySelector('input[name="name"]')
    const categoryInput = container.querySelector('input[name="category"]')
    const sampleTypeInput = container.querySelector('input[name="sample_type"]')
    const priceInput = container.querySelector('input[name="price"]')

    if (codeInput) await user.type(codeInput, 'RFT')
    if (nameInput) await user.type(nameInput, 'Renal Function Test')
    if (categoryInput) await user.type(categoryInput, 'Chemistry')
    if (sampleTypeInput) await user.type(sampleTypeInput, 'Serum')
    if (priceInput) {
      await user.clear(priceInput)
      await user.type(priceInput, '0')
    }

    const createButton = screen.getByRole('button', { name: /Create Test/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Price must be greater than 0/)
      ).toBeInTheDocument()
    })
  })

  it('updates existing test successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)
    vi.mocked(catalogService.update).mockResolvedValue({
      ...mockTests[0],
      price: 550,
    })

    const { container } = render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit Test')).toBeInTheDocument()
    })

    const priceInput = container.querySelector('input[name="price"]')
    if (priceInput) {
      await user.clear(priceInput)
      await user.type(priceInput, '550')
    }

    const updateButton = screen.getByRole('button', { name: /Update Test/i })
    await user.click(updateButton)

    await waitFor(() => {
      expect(catalogService.update).toHaveBeenCalledWith(1, expect.any(Object))
    })
  })

  it('closes modal when Cancel button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Test')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Test')).toBeInTheDocument()
    })

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByText('Add New Test')).not.toBeInTheDocument()
    })
  })

  it('displays error message when create fails', async () => {
    const user = userEvent.setup()
    vi.mocked(catalogService.getAll).mockResolvedValue(mockTests)
    vi.mocked(catalogService.create).mockRejectedValue(
      new Error('Test code already exists')
    )

    const { container } = render(
      <BrowserRouter>
        <TestCatalogPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('CBC')).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add Test')
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByText('Add New Test')).toBeInTheDocument()
    })

    const codeInput = container.querySelector('input[name="code"]')
    const nameInput = container.querySelector('input[name="name"]')
    const categoryInput = container.querySelector('input[name="category"]')
    const sampleTypeInput = container.querySelector('input[name="sample_type"]')
    const priceInput = container.querySelector('input[name="price"]')

    if (codeInput) await user.type(codeInput, 'CBC')
    if (nameInput) await user.type(nameInput, 'Complete Blood Count')
    if (categoryInput) await user.type(categoryInput, 'Hematology')
    if (sampleTypeInput) await user.type(sampleTypeInput, 'Blood')
    if (priceInput) {
      await user.clear(priceInput)
      await user.type(priceInput, '500')
    }

    const createButton = screen.getByRole('button', { name: /Create Test/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByText(/Test code already exists/)).toBeInTheDocument()
    })
  })
})
