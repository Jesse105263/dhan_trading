import {
  Activity,
  Bot,
  ChartNoAxesCombined,
  Gauge,
  Home,
  ListFilter,
  ScrollText,
  History,
  Target,
  CalendarClock,
  Search,
  Settings,
  WalletCards,
  type LucideIcon,
} from 'lucide-react'

export interface NavigationItem {
  path: string
  label: string
  description: string
  icon: LucideIcon
  end?: boolean
}

export const navigationItems: ReadonlyArray<NavigationItem> = [
  {
    path: '/',
    label: 'Home',
    description: 'Your private Version 2 workspace foundation.',
    icon: Home,
    end: true,
  },
  {
    path: '/market',
    label: 'Market Overview',
    description: 'A future overview of persisted market intelligence.',
    icon: Gauge,
  },
  {
    path: '/scanner',
    label: 'Scanner',
    description: 'A future workspace for persisted opportunity discovery.',
    icon: ListFilter,
  },
  {
    path: '/research',
    label: 'Symbol Research',
    description: 'A future workspace for persisted symbol and option-chain research.',
    icon: Search,
  },
  {
    path: '/trade-opportunities',
    label: 'Trade Opportunities',
    description: 'Deterministic evidence-backed opportunity assessments.',
    icon: Target,
  },
  {
    path: '/events',
    label: 'News & Events',
    description: 'Persisted, source-attributed market and company event context.',
    icon: CalendarClock,
  },
  {
    path: '/signals',
    label: 'Signals',
    description: 'A future workspace for signals and decision lineage.',
    icon: Activity,
  },
  {
    path: '/memory',
    label: 'Market Memory',
    description: 'Historical persisted features, snapshots, and comparisons.',
    icon: History,
  },
  {
    path: '/evaluation',
    label: 'Replay & Backtesting',
    description: 'A future workspace for persisted replay and backtest evidence.',
    icon: ChartNoAxesCombined,
  },
  {
    path: '/paper',
    label: 'Paper Portfolio',
    description: 'A future read-only view of isolated paper-trading records.',
    icon: WalletCards,
  },
  {
    path: '/operations',
    label: 'Operations',
    description: 'A future workspace for platform health and operational audit.',
    icon: ScrollText,
  },
  {
    path: '/copilot',
    label: 'AI Analyst',
    description: 'Grounded explanation and comparison of deterministic opportunities.',
    icon: Bot,
  },
  {
    path: '/settings',
    label: 'Settings',
    description: 'A future location for presentation preferences.',
    icon: Settings,
  },
]
