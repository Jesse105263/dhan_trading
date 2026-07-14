import { fireEvent, render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { describe, expect, it } from 'vitest'

import { ApplicationProvider } from './ApplicationProvider'
import { statusMetadata, useApplication } from './application-context'
import { ErrorBoundary } from './ErrorBoundary'
import { LoadingBoundary } from './LoadingBoundary'
import { ThemeProvider } from './ThemeProvider'

function ShellActions() {
  const { openModal, openDrawer, pushToast } = useApplication()
  return (
    <>
      <button onClick={() => openModal('Modal title', 'Modal content')}>Open modal</button>
      <button onClick={() => openDrawer('Drawer title', 'Drawer content')}>Open drawer</button>
      <button onClick={() => pushToast('Saved locally')}>Push toast</button>
    </>
  )
}

describe('shell providers', () => {
  it('applies the fixed light theme without a theme switch', () => {
    render(<ThemeProvider>Theme content</ThemeProvider>)
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  })

  it('provides modal, drawer and toast hosts without business state', () => {
    render(
      <ApplicationProvider>
        <ShellActions />
      </ApplicationProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Open modal' }))
    expect(screen.getByRole('dialog', { name: 'Modal title' })).toHaveTextContent('Modal content')
    fireEvent.click(screen.getByRole('button', { name: 'Close Modal title' }))
    fireEvent.click(screen.getByRole('button', { name: 'Open drawer' }))
    expect(screen.getByRole('dialog', { name: 'Drawer title' })).toHaveTextContent('Drawer content')
    fireEvent.click(screen.getByRole('button', { name: 'Push toast' }))
    expect(screen.getByRole('status', { name: '' })).toHaveTextContent('Saved locally')
  })

  it('defines every approved placeholder status', () => {
    expect(Object.values(statusMetadata).map(({ label }) => label)).toEqual([
      'Backend unavailable',
      'Loading',
      'Offline',
      'Maintenance',
    ])
  })

  it('renders a loading boundary without mounting content', () => {
    render(
      <LoadingBoundary loading label="Loading workspace">
        <span>Workspace</span>
      </LoadingBoundary>,
    )
    expect(screen.getByRole('status')).toHaveTextContent('Loading workspace')
    expect(screen.queryByText('Workspace')).not.toBeInTheDocument()
  })
})

function ThrowingChild(): never {
  useEffect(() => undefined, [])
  throw new Error('test render failure')
}

describe('ErrorBoundary', () => {
  it('replaces a failed shell render with a safe fallback', () => {
    const originalError = console.error
    console.error = () => undefined
    try {
      render(
        <ErrorBoundary>
          <ThrowingChild />
        </ErrorBoundary>,
      )
      expect(
        screen.getByRole('heading', { name: 'The application shell could not be displayed' }),
      ).toBeInTheDocument()
    } finally {
      console.error = originalError
    }
  })
})
