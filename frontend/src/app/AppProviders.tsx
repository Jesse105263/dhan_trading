import type { ReactNode } from 'react'

import { ApplicationProvider, ErrorBoundary, ThemeProvider } from './providers'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ApplicationProvider>{children}</ApplicationProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}
