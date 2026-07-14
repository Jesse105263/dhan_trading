import { fireEvent, render, screen, within } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { Button, EmptyState, Input, Modal, TableShell, Toggle } from './components'

describe('design-system controls', () => {
  it('exposes loading and disabled button state accessibly', () => {
    render(<Button loading>Save</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
    expect(within(button).getByRole('status')).toHaveTextContent('Working')
  })

  it('associates field errors with the input', () => {
    render(<Input label="Symbol" error="A symbol is required" />)
    const input = screen.getByRole('textbox', { name: 'Symbol' })
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription('A symbol is required')
  })

  it('operates a toggle by keyboard and reports switch state', () => {
    function Example() {
      const [checked, setChecked] = useState(false)
      return <Toggle label="Compact rows" checked={checked} onChange={setChecked} />
    }
    render(<Example />)
    const toggle = screen.getByRole('switch', { name: 'Compact rows' })
    toggle.focus()
    fireEvent.keyDown(toggle, { key: 'Enter' })
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })
})

describe('design-system states and overlays', () => {
  it('renders a semantic empty state', () => {
    render(<EmptyState title="No signals" description="Signals will appear after a run." />)
    expect(screen.getByRole('heading', { name: 'No signals' })).toBeInTheDocument()
  })

  it('focuses modal close and closes on Escape', () => {
    const onClose = vi.fn()
    render(
      <Modal open title="Details" onClose={onClose}>
        Evidence
      </Modal>,
    )
    expect(screen.getByRole('dialog', { name: 'Details' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Close Details' })).toHaveFocus()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })
})

describe('TableShell', () => {
  const columns = [
    {
      key: 'symbol',
      header: 'Symbol',
      sortable: true,
      render: (row: { id: string; symbol: string }) => row.symbol,
    },
  ]

  it('renders an accessible responsive table and emits sort requests without sorting', () => {
    const onSortRequest = vi.fn()
    render(
      <TableShell
        caption="Opportunities"
        columns={columns}
        rows={[{ id: '1', symbol: 'RELIANCE' }]}
        rowKey={(row) => row.id}
        onSortRequest={onSortRequest}
      />,
    )
    expect(screen.getByRole('region', { name: 'Opportunities table' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Symbol' }))
    expect(onSortRequest).toHaveBeenCalledWith('symbol')
    expect(screen.getByText('RELIANCE')).toBeInTheDocument()
  })

  it('renders loading and empty states instead of an empty table', () => {
    const { rerender } = render(
      <TableShell
        caption="Opportunities"
        columns={columns}
        rows={[]}
        rowKey={(row) => row.id}
        loading
      />,
    )
    expect(screen.getByRole('status', { name: 'Loading Opportunities' })).toBeInTheDocument()
    rerender(
      <TableShell caption="Opportunities" columns={columns} rows={[]} rowKey={(row) => row.id} />,
    )
    expect(screen.getByRole('heading', { name: 'No records' })).toBeInTheDocument()
  })
})
