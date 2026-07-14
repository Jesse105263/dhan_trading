import { type ReactNode, useEffect } from 'react'

import { ThemeContext, type Theme } from './theme-context'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme: Theme = 'light'

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>
}
