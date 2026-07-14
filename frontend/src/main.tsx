import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'

import { router } from './app/router'
import { AppProviders } from './app/AppProviders'
import './app/shell/shell.css'
import './styles.css'

const root = document.getElementById('root')

if (!root) {
  throw new Error('Frontend root element was not found.')
}

createRoot(root).render(
  <StrictMode>
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  </StrictMode>,
)
