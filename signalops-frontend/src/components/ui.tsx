import type { ReactNode } from 'react'
import type { FindingStatus, InvStatus } from '../types'

export function Card({ title, actions, children, className = '' }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-zinc-800 bg-zinc-900/60 print-plain ${className}`}>
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-zinc-800 px-4 py-2.5">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide text-zinc-400">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}

const tone = {
  green: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/30',
  amber: 'bg-amber-500/10 text-amber-300 ring-amber-500/30',
  red: 'bg-red-500/10 text-red-300 ring-red-500/30',
  indigo: 'bg-indigo-500/10 text-indigo-300 ring-indigo-500/30',
  zinc: 'bg-zinc-500/10 text-zinc-300 ring-zinc-500/30',
}
export type Tone = keyof typeof tone

export function Badge({ children, t = 'zinc', icon }: { children: ReactNode; t?: Tone; icon?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset ${tone[t]}`}>
      {icon && <span aria-hidden>{icon}</span>}{children}
    </span>
  )
}

// Status never by color alone: every badge has an icon + word.
const findingTone: Record<FindingStatus, [Tone, string]> = {
  confirmed: ['green', '✓'], likely: ['amber', '◐'], hypothesis: ['indigo', '?'], unknown: ['zinc', '∅'],
}
export const StatusBadge = ({ s }: { s: FindingStatus }) => <Badge t={findingTone[s][0]} icon={findingTone[s][1]}>{s}</Badge>

const invTone: Record<InvStatus, [Tone, string]> = {
  queued: ['zinc', '…'], investigating: ['indigo', '●'], partial: ['amber', '!'], awaiting_approval: ['amber', '⏸'],
  completed: ['green', '✓'], failed: ['red', '✕'], cancelled: ['zinc', '–'],
}
export const InvBadge = ({ s }: { s: InvStatus }) => <Badge t={invTone[s][0]} icon={invTone[s][1]}>{s.replace('_', ' ')}</Badge>

const sevTone: Record<string, Tone> = { critical: 'red', high: 'red', medium: 'amber', low: 'zinc', info: 'zinc', warning: 'amber' }
export const SeverityBadge = ({ s }: { s: string }) => <Badge t={sevTone[s] ?? 'zinc'} icon={s === 'critical' || s === 'high' ? '▲' : '•'}>{s}</Badge>

export const ServerBadge = ({ s }: { s: string }) =>
  <Badge t={s === 'orders' ? 'indigo' : 'zinc'} icon={s === 'orders' ? '◆' : '■'}>{s} MCP</Badge>

export function Stat({ label, value, sub, t }: { label: string; value: ReactNode; sub?: ReactNode; t?: 'red' | 'amber' }) {
  const color = t === 'red' ? 'text-red-300' : t === 'amber' ? 'text-amber-300' : 'text-zinc-50'
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-3 print-plain">
      <div className="text-xs font-medium text-zinc-400">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${color}`}>{value}</div>
      {sub && <div className="mt-1 text-[11px] leading-snug text-zinc-500">{sub}</div>}
    </div>
  )
}

export const Mono = ({ children }: { children: ReactNode }) => <span className="whitespace-nowrap font-mono text-[12px] text-zinc-300">{children}</span>

export const money = (n: number) => n.toLocaleString(undefined, { style: 'currency', currency: 'USD' })
export const time = (s: string | null | undefined) => (s ? s.replace('T', ' ').slice(0, 16) : '—')

export function ErrorNote({ children }: { children: ReactNode }) {
  return <div role="alert" className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">{children}</div>
}

export function Loading({ what }: { what: string }) {
  return <div className="animate-pulse text-sm text-zinc-500">Loading {what}…</div>
}
