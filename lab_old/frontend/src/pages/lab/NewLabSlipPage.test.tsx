import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { NewLabSlipPage } from './NewLabSlipPage'
import { patientService } from '../../services/patients'
import { catalogService } from '../../services/catalog'

// Mock services
vi.mock('../../services/patients')
vi.mock('../../services/catalog')
vi.mock('../../services/orders')

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('NewLabSlipPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(patientService.search).mockResolvedValue([])
    vi.mocked(catalogService.search).mockResolvedValue([])
  })

  it('renders the new lab slip form', () => {
    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    expect(screen.getByText('New Lab Slip')).toBeInTheDocument()
    expect(screen.getByText('Patient Information')).toBeInTheDocument()
    expect(screen.getByText('Test Selection')).toBeInTheDocument()
    expect(screen.getByText('Billing & Report Details')).toBeInTheDocument()
  })

  it('displays all required patient fields', () => {
    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    expect(screen.getByPlaceholderText('12345-1234567-1')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('03001234567')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter full name')).toBeInTheDocument()
    expect(screen.getByText(/Gender/i)).toBeInTheDocument()
    expect(screen.getByText(/Date of Birth/i)).toBeInTheDocument()
  })

  it('validates required fields on submit', async () => {
    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    const saveButton = screen.getByRole('button', { name: /Save Only/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/Full name is required/i)).toBeInTheDocument()
      // CNIC is now optional, so we don't check for its validation
      expect(
        screen.getByText(/Valid phone number is required/i)
      ).toBeInTheDocument()
      // Age or DOB is required
      expect(
        screen.getByText(/Either date of birth or at least one age field is required/i)
      ).toBeInTheDocument()
    })
  })

  it('displays patient suggestions when searching', async () => {
    const mockPatients = [
      {
        id: 1,
        mrn: 'PAT-001',
        cnic: '12345-1234567-1',
        phone: '03001234567',
        full_name: 'John Doe',
        sex: 'M' as const,
        dob: '1990-01-01',
        age_years: 34,
        age_months: null,
        age_days: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(patientService.search).mockResolvedValue(mockPatients)

    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    const cnicInput = screen.getByPlaceholderText('12345-1234567-1')
    fireEvent.change(cnicInput, { target: { value: '12345' } })

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })
  })

  it('displays test suggestions when searching', async () => {
    const mockTests = [
      {
        id: 1,
        code: 'CBC',
        name: 'Complete Blood Count',
        description: '',
        category: 'Hematology',
        sample_type: 'Blood',
        price: 500,
        turnaround_time_hours: 24,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(catalogService.search).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    const testSearch = screen.getByPlaceholderText(
      /Search by test name or code/i
    )
    fireEvent.change(testSearch, { target: { value: 'CBC' } })

    await waitFor(() => {
      expect(screen.getByText('Complete Blood Count')).toBeInTheDocument()
    })
  })

  it('calculates bill amount correctly', async () => {
    const mockTests = [
      {
        id: 1,
        code: 'CBC',
        name: 'Complete Blood Count',
        description: '',
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
        description: '',
        category: 'Chemistry',
        sample_type: 'Blood',
        price: 800,
        turnaround_time_hours: 24,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(catalogService.search).mockResolvedValue(mockTests)

    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    // Add first test
    const testSearch = screen.getByPlaceholderText(
      /Search by test name or code/i
    )
    fireEvent.change(testSearch, { target: { value: 'test' } })

    await waitFor(() => {
      expect(screen.getByText('Complete Blood Count')).toBeInTheDocument()
    })

    const firstTestButton = screen.getByText('Complete Blood Count')
    fireEvent.click(firstTestButton)

    // Add second test
    fireEvent.change(testSearch, { target: { value: 'test' } })

    await waitFor(() => {
      expect(screen.getByText('Liver Function Test')).toBeInTheDocument()
    })

    const secondTestButton = screen.getByText('Liver Function Test')
    fireEvent.click(secondTestButton)

    // Check if bill amount is calculated correctly (500 + 800 = 1300)
    await waitFor(() => {
      const billText =
        screen.getByText(/Bill Amount:/i).nextSibling?.textContent
      expect(billText).toContain('1')
      expect(billText).toContain('300')
    })
  })

  it('shows action buttons', () => {
    render(
      <BrowserRouter>
        <NewLabSlipPage />
      </BrowserRouter>
    )

    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Save Only/i })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Save & Print/i })
    ).toBeInTheDocument()
  })
})
