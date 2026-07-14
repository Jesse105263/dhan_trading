import { createContext, useContext, type ReactNode } from 'react'

export type ApplicationStatus = 'backend-unavailable' | 'loading' | 'offline' | 'maintenance'

export const statusMetadata: Record<
  ApplicationStatus,
  { label: string; tone: 'neutral' | 'warning' | 'danger' | 'info' }
> = {
  'backend-unavailable': { label: 'Backend unavailable', tone: 'danger' },
  loading: { label: 'Loading', tone: 'info' },
  offline: { label: 'Offline', tone: 'warning' },
  maintenance: { label: 'Maintenance', tone: 'neutral' },
}

export interface ApplicationContextValue {
  status: ApplicationStatus
  setStatus: (status: ApplicationStatus) => void
  navigationOpen: boolean
  setNavigationOpen: (open: boolean) => void
  openModal: (title: string, content: ReactNode) => void
  openDrawer: (title: string, content: ReactNode) => void
  pushToast: (message: string) => void
}

export const ApplicationContext = createContext<ApplicationContextValue | null>(null)

export function useApplication(): ApplicationContextValue {
  const value = useContext(ApplicationContext)
  if (!value) throw new Error('useApplication must be used within ApplicationProvider.')
  return value
}
