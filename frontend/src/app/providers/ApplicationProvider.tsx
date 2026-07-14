import { type ReactNode, useCallback, useMemo, useState } from 'react'

import { Drawer, Modal } from '../../design-system'
import { ApplicationContext, type ApplicationStatus } from './application-context'

interface OverlayState {
  title: string
  content: ReactNode
}

export interface ToastMessage {
  id: number
  message: string
}

export function ApplicationProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ApplicationStatus>('backend-unavailable')
  const [navigationOpen, setNavigationOpen] = useState(false)
  const [modal, setModal] = useState<OverlayState | null>(null)
  const [drawer, setDrawer] = useState<OverlayState | null>(null)
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const [, setNextToastId] = useState(1)

  const openModal = useCallback(
    (title: string, content: ReactNode) => setModal({ title, content }),
    [],
  )
  const openDrawer = useCallback(
    (title: string, content: ReactNode) => setDrawer({ title, content }),
    [],
  )
  const pushToast = useCallback((message: string) => {
    setNextToastId((id) => {
      setToasts((current) => [...current, { id, message }])
      return id + 1
    })
  }, [])

  const value = useMemo(
    () => ({
      status,
      setStatus,
      navigationOpen,
      setNavigationOpen,
      openModal,
      openDrawer,
      pushToast,
    }),
    [navigationOpen, openDrawer, openModal, pushToast, status],
  )

  return (
    <ApplicationContext.Provider value={value}>
      {children}
      <ToastHost toasts={toasts} />
      <Modal open={modal !== null} title={modal?.title ?? ''} onClose={() => setModal(null)}>
        {modal?.content}
      </Modal>
      <Drawer open={drawer !== null} title={drawer?.title ?? ''} onClose={() => setDrawer(null)}>
        {drawer?.content}
      </Drawer>
    </ApplicationContext.Provider>
  )
}

function ToastHost({ toasts }: { toasts: ReadonlyArray<ToastMessage> }) {
  return (
    <div className="shell-toast-host" aria-live="polite" aria-label="Notifications">
      {toasts.map((toast) => (
        <div key={toast.id} className="shell-toast" role="status">
          {toast.message}
        </div>
      ))}
    </div>
  )
}
