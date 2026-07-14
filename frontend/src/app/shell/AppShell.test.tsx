import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AppProviders } from '../AppProviders'
import { navigationItems } from '../navigation'
import { NotFoundPage } from '../pages/NotFoundPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'
import { AppShell } from './AppShell'

function renderRoute(initialEntry = '/') {
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: <AppShell />,
        children: [
          { index: true, element: <PlaceholderPage {...navigationItems[0]!} /> },
          { path: 'signals', element: <PlaceholderPage {...navigationItems[4]!} /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  )
  render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
  )
}

describe('AppShell', () => {
  it('provides landmarks, skip navigation and all placeholder links', () => {
    renderRoute()
    expect(screen.getAllByRole('banner')).toHaveLength(2)
    expect(screen.getByRole('navigation', { name: 'Primary navigation' })).toBeInTheDocument()
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')
    expect(screen.getByRole('contentinfo', { name: 'Application status' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Skip to main content' })).toHaveAttribute(
      'href',
      '#main-content',
    )
    for (const item of navigationItems) {
      expect(screen.getByRole('link', { name: item.label })).toBeInTheDocument()
    }
  })

  it('renders placeholder content through nested routes', () => {
    renderRoute('/signals')
    expect(screen.getByRole('heading', { name: 'Signals', level: 1 })).toBeInTheDocument()
    expect(
      screen.getByText('A future workspace for signals and decision lineage.'),
    ).toBeInTheDocument()
  })

  it('opens and closes mobile navigation with an accessible control', () => {
    renderRoute()
    const control = screen.getByRole('button', { name: 'Open navigation' })
    fireEvent.click(control)
    expect(screen.getAllByRole('button', { name: 'Close navigation' })[0]).toHaveAttribute(
      'aria-expanded',
      'true',
    )
    fireEvent.click(screen.getAllByRole('button', { name: 'Close navigation' })[0]!)
    expect(screen.getByRole('button', { name: 'Open navigation' })).toHaveAttribute(
      'aria-expanded',
      'false',
    )
  })

  it('renders a not-found page within the shell', () => {
    renderRoute('/missing')
    expect(screen.getByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })

  it('shows an explicitly disconnected placeholder status', () => {
    renderRoute()
    expect(screen.getByText('Backend unavailable')).toBeInTheDocument()
    expect(screen.getByText(/not connected to the backend/u)).toBeInTheDocument()
  })
})
