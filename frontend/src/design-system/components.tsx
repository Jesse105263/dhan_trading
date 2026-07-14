import { ArrowUpDown, CircleAlert, Inbox, X } from 'lucide-react'
import {
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TableHTMLAttributes,
  forwardRef,
  useEffect,
  useId,
  useRef,
} from 'react'

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'
type Size = 'sm' | 'md' | 'lg'

function classes(...values: Array<string | false | undefined>): string {
  return values.filter(Boolean).join(' ')
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'quiet' | 'danger'
  size?: Size
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading = false, disabled, className, children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={classes('ds-button', `ds-button--${variant}`, `ds-button--${size}`, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <Spinner label="Working" size="sm" /> : children}
    </button>
  )
})

export function Card({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <article className={classes('ds-card', className)} {...props} />
}

export function Panel({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={classes('ds-panel', className)} {...props} />
}

export function Divider({ className, ...props }: HTMLAttributes<HTMLHRElement>) {
  return <hr className={classes('ds-divider', className)} {...props} />
}

interface LabelProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone
}

export function Badge({ tone = 'neutral', className, ...props }: LabelProps) {
  return (
    <span className={classes('ds-label', 'ds-badge', `ds-tone--${tone}`, className)} {...props} />
  )
}

export function Tag({ tone = 'neutral', className, ...props }: LabelProps) {
  return (
    <span className={classes('ds-label', 'ds-tag', `ds-tone--${tone}`, className)} {...props} />
  )
}

export function StatusPill({ tone = 'neutral', className, children, ...props }: LabelProps) {
  return (
    <span className={classes('ds-label', 'ds-status', `ds-tone--${tone}`, className)} {...props}>
      <span className="ds-status__dot" aria-hidden="true" />
      {children}
    </span>
  )
}

interface FieldProps {
  label: string
  hint?: string
  error?: string
}

export function Input({
  label,
  hint,
  error,
  id: suppliedId,
  className,
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const generatedId = useId()
  const id = suppliedId ?? generatedId
  const descriptionId = hint || error ? `${id}-description` : undefined
  return (
    <div className="ds-field">
      <label className="ds-field__label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className={classes('ds-control', error && 'ds-control--error', className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={descriptionId}
        {...props}
      />
      {(error || hint) && (
        <span
          id={descriptionId}
          className={classes('ds-field__hint', error && 'ds-field__hint--error')}
        >
          {error ?? hint}
        </span>
      )}
    </div>
  )
}

export function Select({
  label,
  hint,
  error,
  id: suppliedId,
  className,
  children,
  ...props
}: FieldProps & SelectHTMLAttributes<HTMLSelectElement>) {
  const generatedId = useId()
  const id = suppliedId ?? generatedId
  const descriptionId = hint || error ? `${id}-description` : undefined
  return (
    <div className="ds-field">
      <label className="ds-field__label" htmlFor={id}>
        {label}
      </label>
      <select
        id={id}
        className={classes('ds-control', error && 'ds-control--error', className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={descriptionId}
        {...props}
      >
        {children}
      </select>
      {(error || hint) && (
        <span
          id={descriptionId}
          className={classes('ds-field__hint', error && 'ds-field__hint--error')}
        >
          {error ?? hint}
        </span>
      )}
    </div>
  )
}

export function Checkbox({
  label,
  className,
  ...props
}: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={classes('ds-check', className)}>
      <input type="checkbox" {...props} />
      <span>{label}</span>
    </label>
  )
}

export function Toggle({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className="ds-toggle"
      disabled={disabled}
      onClick={() => onChange(!checked)}
    >
      <span className="ds-toggle__track" aria-hidden="true">
        <span className="ds-toggle__thumb" />
      </span>
      <span>{label}</span>
    </button>
  )
}

export function Spinner({ label = 'Loading', size = 'md' }: { label?: string; size?: Size }) {
  return (
    <span className={classes('ds-spinner-wrap', `ds-spinner-wrap--${size}`)} role="status">
      <span className="ds-spinner" aria-hidden="true" />
      <span className="visually-hidden">{label}</span>
    </span>
  )
}

export function Skeleton({
  label = 'Loading content',
  lines = 3,
}: {
  label?: string
  lines?: number
}) {
  return (
    <div className="ds-skeleton" role="status" aria-label={label}>
      {Array.from({ length: lines }, (_, index) => (
        <span key={index} aria-hidden="true" />
      ))}
    </div>
  )
}

interface StateProps {
  title: string
  description: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: StateProps) {
  return <State icon={<Inbox />} title={title} description={description} action={action} />
}

export function ErrorState({ title, description, action }: StateProps) {
  return (
    <State icon={<CircleAlert />} title={title} description={description} action={action} danger />
  )
}

function State({
  icon,
  title,
  description,
  action,
  danger = false,
}: StateProps & { icon: ReactNode; danger?: boolean }) {
  return (
    <section className={classes('ds-state', danger && 'ds-state--danger')} aria-live="polite">
      <span className="ds-state__icon" aria-hidden="true">
        {icon}
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action && <div>{action}</div>}
    </section>
  )
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <header className="ds-page-header">
      <div>
        {eyebrow && <p className="ds-eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="cluster">{actions}</div>}
    </header>
  )
}

export function SectionHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <header className="ds-section-header">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="cluster">{actions}</div>}
    </header>
  )
}

export function Toolbar({
  label,
  className,
  ...props
}: { label: string } & HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="toolbar"
      aria-label={label}
      className={classes('ds-toolbar', className)}
      {...props}
    />
  )
}

interface OverlayProps {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
}

function Overlay({ open, title, children, onClose, drawer }: OverlayProps & { drawer: boolean }) {
  const titleId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!open) return
    closeRef.current?.focus()
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose, open])
  if (!open) return null
  return (
    <div className={classes('ds-overlay', drawer && 'ds-overlay--drawer')}>
      <section
        className={classes('ds-dialog', drawer && 'ds-drawer')}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <header>
          <h2 id={titleId}>{title}</h2>
          <Button
            ref={closeRef}
            variant="quiet"
            size="sm"
            aria-label={`Close ${title}`}
            onClick={onClose}
          >
            <X aria-hidden="true" />
          </Button>
        </header>
        <div className="ds-dialog__body">{children}</div>
      </section>
    </div>
  )
}

export function Modal(props: OverlayProps) {
  return <Overlay {...props} drawer={false} />
}

export function Drawer(props: OverlayProps) {
  return <Overlay {...props} drawer />
}

export interface TableColumn<Row> {
  key: string
  header: string
  render: (row: Row) => ReactNode
  sortable?: boolean
  align?: 'start' | 'end'
}

export interface TableShellProps<Row> extends Omit<
  TableHTMLAttributes<HTMLTableElement>,
  'children'
> {
  caption: string
  columns: ReadonlyArray<TableColumn<Row>>
  rows: ReadonlyArray<Row>
  rowKey: (row: Row) => string
  loading?: boolean
  emptyTitle?: string
  emptyDescription?: string
  onSortRequest?: (key: string) => void
}

export function TableShell<Row>({
  caption,
  columns,
  rows,
  rowKey,
  loading = false,
  emptyTitle = 'No records',
  emptyDescription = 'There is nothing to display yet.',
  onSortRequest,
  className,
  ...props
}: TableShellProps<Row>) {
  if (loading)
    return (
      <div className="ds-table-state">
        <Skeleton label={`Loading ${caption}`} lines={4} />
      </div>
    )
  if (rows.length === 0) return <EmptyState title={emptyTitle} description={emptyDescription} />
  return (
    <div className="ds-table-scroll" tabIndex={0} role="region" aria-label={`${caption} table`}>
      <table className={classes('ds-table', className)} {...props}>
        <caption className="visually-hidden">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={column.align === 'end' ? 'ds-table__number' : undefined}
              >
                {column.sortable ? (
                  <button
                    type="button"
                    className="ds-sort"
                    onClick={() => onSortRequest?.(column.key)}
                  >
                    {column.header}
                    <ArrowUpDown size={14} aria-hidden="true" />
                  </button>
                ) : (
                  column.header
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={column.align === 'end' ? 'ds-table__number' : undefined}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
