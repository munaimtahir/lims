import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Toast } from './Toast'

describe('Toast', () => {
  it('renders toast with success type', () => {
    const onClose = vi.fn()
    render(<Toast message="Success message" type="success" onClose={onClose} />)

    expect(screen.getByText('Success message')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders toast with error type', () => {
    const onClose = vi.fn()
    render(<Toast message="Error message" type="error" onClose={onClose} />)

    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('renders toast with info type', () => {
    const onClose = vi.fn()
    render(<Toast message="Info message" type="info" onClose={onClose} />)

    expect(screen.getByText('Info message')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(<Toast message="Test message" type="info" onClose={onClose} />)

    const closeButton = screen.getByLabelText('Close')
    closeButton.click()

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
