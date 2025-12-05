import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LabHomePage } from './LabHomePage'

describe('LabHomePage', () => {
  it('renders lab home title', () => {
    render(
      <BrowserRouter>
        <LabHomePage />
      </BrowserRouter>
    )

    expect(screen.getByText('Lab Home')).toBeInTheDocument()
  })

  it('displays lab action tiles', () => {
    render(
      <BrowserRouter>
        <LabHomePage />
      </BrowserRouter>
    )

    expect(screen.getByText('New Lab Slip')).toBeInTheDocument()
    expect(screen.getByText('Due Lab Slips')).toBeInTheDocument()
    expect(screen.getByText('Sample Collection')).toBeInTheDocument()
    expect(screen.getByText('Enter Results')).toBeInTheDocument()
    expect(screen.getByText('Verify Results')).toBeInTheDocument()
    expect(screen.getByText('Publish Results')).toBeInTheDocument()
    expect(screen.getByText('Manage Lab Tests')).toBeInTheDocument()
  })

  it('displays reports section', () => {
    render(
      <BrowserRouter>
        <LabHomePage />
      </BrowserRouter>
    )

    // Use getAllByText since "Reports" appears multiple times (section header and tile)
    const reportsElements = screen.getAllByText('Reports')
    expect(reportsElements.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Patient Records')).toBeInTheDocument()
    expect(screen.getByText('Dashboard Analytics')).toBeInTheDocument()
  })

  it('displays settings section', () => {
    render(
      <BrowserRouter>
        <LabHomePage />
      </BrowserRouter>
    )

    expect(screen.getByText('Settings & Admin')).toBeInTheDocument()
    expect(screen.getByText('Workflow Settings')).toBeInTheDocument()
    expect(screen.getByText('Role Permissions')).toBeInTheDocument()
    expect(screen.getByText('User Management')).toBeInTheDocument()
  })

  it('new lab slip tile links to correct route', () => {
    render(
      <BrowserRouter>
        <LabHomePage />
      </BrowserRouter>
    )

    const newLabSlipLink = screen.getByText('New Lab Slip').closest('a')
    expect(newLabSlipLink).toHaveAttribute('href', '/lab/new')
  })
})
