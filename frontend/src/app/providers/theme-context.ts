import { createContext, useContext } from 'react'

export type Theme = 'light'

export const ThemeContext = createContext<Theme | null>(null)

export function useTheme(): Theme {
  const value = useContext(ThemeContext)
  if (!value) throw new Error('useTheme must be used within ThemeProvider.')
  return value
}
