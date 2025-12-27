import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Health } from './Health'

describe('Health Component', () => {
  it('renders health status', () => {
    render(<Health />)

    const healthElement = screen.getByTestId('health-status')
    expect(healthElement).toBeInTheDocument()

    const heading = screen.getByText('System Health')
    expect(heading).toBeInTheDocument()

    const status = screen.getByText('Status: Healthy')
    expect(status).toBeInTheDocument()
  })
})
